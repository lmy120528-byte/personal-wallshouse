"""
retriever.py — 两阶段知识检索
Stage 1: Embedding 语义粗筛 Top-N（本地，快速）
Stage 2: DeepSeek Chat 精排 Top-K（语义理解，可选）
"""
import os
import re
import json
import pickle
import numpy as np
import urllib.request
import urllib.error
from sentence_transformers import SentenceTransformer

INDEX_FILE = os.path.join(os.path.dirname(__file__), "embeddings.pkl")
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Re-rank 用的 System Prompt
RERANK_PROMPT = """你是信息检索专家。根据用户问题，判断哪些候选文本片段最相关，按相关性从高到低排序。

规则：
1. 直接回答问题的 > 只是提到相关概念的
2. 包含具体事实/数据的 > 泛泛而谈的
3. 主题完全匹配的 > 部分相关的
4. 如果完全不相关，不要硬排

只返回排序后的序号（从最相关到最不相关），用逗号分隔，例如：3,1,5,2,4
不要返回任何其他文字。"""


class Retriever:
    def __init__(self):
        self._model = None
        self.embeddings = None   # numpy array (N, dim)
        self.chunks = []         # [{content, source, file}]

    @property
    def model(self):
        """懒加载 Embedding 模型（首次使用时下载缓存到本地）"""
        if self._model is None:
            print(f"   🤖 加载 Embedding 模型: {EMBEDDING_MODEL}")
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        return self._model

    # ============================================================
    # 索引构建 & 加载
    # ============================================================

    def build(self, knowledge_dir):
        """从 knowledge/ 目录读取文件 → 切片 → 向量化 → 保存索引"""
        files = []
        for fn in sorted(os.listdir(knowledge_dir)):
            if fn.startswith("."):
                continue
            if not (fn.endswith(".txt") or fn.endswith(".md")):
                continue
            fpath = os.path.join(knowledge_dir, fn)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            files.append({"file": fn, "content": content})
            print(f"   📄 {fn} ({len(content)} 字)")

        all_chunks = []
        for f in files:
            chunks = self._split(f["content"])
            for c in chunks:
                all_chunks.append({
                    "content": c["text"],
                    "source": c["source"],
                    "file": f["file"],
                })

        if not all_chunks:
            raise ValueError("知识库为空")

        texts = [c["content"] for c in all_chunks]
        print(f"   🤖 向量化 {len(texts)} 个切片（首次运行需下载模型，约 120MB）...")
        embeddings = self.model.encode(texts, show_progress_bar=True)

        self.embeddings = embeddings
        self.chunks = all_chunks

        with open(INDEX_FILE, "wb") as f:
            pickle.dump({"embeddings": embeddings, "chunks": all_chunks}, f)

        print(f"   ✅ 索引完成：{len(all_chunks)} 个切片，向量维度 {embeddings.shape[1]}")
        return len(all_chunks)

    def load(self):
        """加载已保存的索引（不加载模型，模型单独懒加载）"""
        if not os.path.exists(INDEX_FILE):
            raise FileNotFoundError("索引文件不存在，请先运行 ingest.py")
        with open(INDEX_FILE, "rb") as f:
            data = pickle.load(f)
        self.embeddings = data["embeddings"]
        self.chunks = data["chunks"]
        print(f"   ✅ 加载语义索引：{len(self.chunks)} 个切片")
        return len(self.chunks)

    # ============================================================
    # 检索
    # ============================================================

    def search(self, query, n=5, api_key=None, coarse_n=None):
        """
        两阶段检索：
        - Stage 1: Embedding 语义粗筛 coarse_n 个候选
        - Stage 2: DeepSeek 精排到 n 个（需要 api_key）

        无 api_key 时降级为纯语义检索 n 个。
        """
        if self.embeddings is None:
            return []

        # Stage 1: Embedding 语义检索
        fetch_n = coarse_n or max(n * 3, 15)
        query_vec = self.model.encode([query])[0]

        # 余弦相似度（sentence-transformers 默认已归一化，点积即可）
        scores = np.dot(self.embeddings, query_vec)
        top_idx = scores.argsort()[-fetch_n:][::-1]

        candidates = []
        for i in top_idx:
            if scores[i] > 0:
                candidates.append({
                    "index": len(candidates) + 1,
                    "content": self.chunks[i]["content"],
                    "source": self.chunks[i]["source"],
                    "file": self.chunks[i]["file"],
                    "score": float(scores[i]),
                })

        if not candidates:
            return []

        # Stage 2: DeepSeek Re-rank
        if api_key and len(candidates) > n:
            try:
                ranked_indices = self._rerank(query, candidates, api_key, n)
                candidates = [candidates[i - 1] for i in ranked_indices if 1 <= i <= len(candidates)]
            except Exception as e:
                print(f"   ⚠️ Re-rank 失败，降级语义检索: {e}")
                candidates = candidates[:n]

        # 返回统一格式: [(content, source, metadata), ...]
        results = []
        for c in candidates[:n]:
            results.append((c["content"], c["source"], {"file": c["file"], "score": c.get("score", 0)}))
        return results

    # ============================================================
    # DeepSeek 精排
    # ============================================================

    def _rerank(self, query, candidates, api_key, top_n):
        """调用 DeepSeek Chat API 对候选片段排序"""
        candidates_text = ""
        for c in candidates:
            content_preview = c["content"][:300].replace("\n", " ")
            candidates_text += f"[{c['index']}] 来源:{c['file']} | {c['source']}\n   {content_preview}...\n\n"

        user_prompt = f"用户问题：{query}\n\n候选文本片段：\n{candidates_text}\n请按相关性从高到低排序，返回序号。"

        req_body = {
            "model": "deepseek-chat",
            "temperature": 0,
            "max_tokens": 100,
            "messages": [
                {"role": "system", "content": RERANK_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        }

        req = urllib.request.Request(
            DEEPSEEK_API,
            data=json.dumps(req_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            answer = data["choices"][0]["message"]["content"].strip()

        # 解析排序结果: "3,1,5,2,4"
        indices = []
        for part in answer.replace("，", ",").split(","):
            part = part.strip()
            if part.isdigit():
                indices.append(int(part))

        if not indices:
            raise ValueError(f"无法解析排序结果: {answer}")

        return indices

    # ============================================================
    # 文本切片
    # ============================================================

    def _split(self, content, max_chars=1200, overlap=80):
        """按 ## 标题切片，过长再按段落细分"""
        heading_pattern = re.compile(r"^#{1,2}\s+.+$", re.MULTILINE)
        positions = [m.start() for m in heading_pattern.finditer(content)]

        if not positions:
            return [{"text": content.strip(), "source": "全文"}]

        raw = []
        for i, pos in enumerate(positions):
            start = pos
            end = positions[i+1] if i+1 < len(positions) else len(content)
            text = content[start:end].strip()
            if text:
                title_line = text.split("\n")[0].strip().lstrip("#").strip()
                raw.append({"text": text, "source": title_line})

        chunks = []
        for sec in raw:
            text, source = sec["text"], sec["source"]
            if len(text) <= max_chars:
                chunks.append({"text": text, "source": source})
            else:
                paras = text.split("\n\n")
                cur = ""
                for p in paras:
                    if len(cur) + len(p) <= max_chars:
                        cur += ("\n\n" if cur else "") + p
                    else:
                        if cur.strip():
                            chunks.append({"text": cur.strip(), "source": source})
                        cur = (cur[-overlap:] if len(cur) > overlap else cur) + "\n\n" + p
                if cur.strip():
                    chunks.append({"text": cur.strip(), "source": source})
        return chunks
