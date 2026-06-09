"""
retriever.py — 轻量级知识检索（TF-IDF）
不用任何 AI 模型，纯 CPU，内存占用 < 50MB
"""
import os
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

INDEX_FILE = os.path.join(os.path.dirname(__file__), "tfidf_index.pkl")

class Retriever:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.chunks = []       # [{content, source, file}]

    def build(self, knowledge_dir):
        """从 knowledge/ 目录构建 TF-IDF 索引"""
        files = []
        for fn in sorted(os.listdir(knowledge_dir)):
            if fn.startswith("."): continue
            if not (fn.endswith(".txt") or fn.endswith(".md")): continue
            fpath = os.path.join(knowledge_dir, fn)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            files.append({"file": fn, "content": content})
            print(f"   📄 {fn} ({len(content)} 字)")

        all_chunks = []
        for f in files:
            chunks = self._split(f["content"])
            for c in chunks:
                all_chunks.append({"content": c["text"], "source": c["source"], "file": f["file"]})

        if not all_chunks:
            raise ValueError("知识库为空")

        texts = [c["content"] for c in all_chunks]
        # char 级别 1-3 gram 适合中文，max_features 控制内存
        self.vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(1, 3), max_features=5000
        )
        self.matrix = self.vectorizer.fit_transform(texts)
        self.chunks = all_chunks

        # 持久化
        with open(INDEX_FILE, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "matrix": self.matrix, "chunks": self.chunks}, f)

        print(f"   ✅ 索引 {len(all_chunks)} 个切片，词汇量 {len(self.vectorizer.vocabulary_)}")
        return len(all_chunks)

    def load(self):
        """加载已保存的索引"""
        if not os.path.exists(INDEX_FILE):
            raise FileNotFoundError("索引文件不存在，请先运行 ingest.py")
        with open(INDEX_FILE, "rb") as f:
            data = pickle.load(f)
        self.vectorizer = data["vectorizer"]
        self.matrix = data["matrix"]
        self.chunks = data["chunks"]
        print(f"   ✅ 加载索引：{len(self.chunks)} 个切片")
        return len(self.chunks)

    def search(self, query, n=5):
        """搜索最相关的 n 个切片"""
        if self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        top_idx = scores.argsort()[-n:][::-1]
        results = []
        for i in top_idx:
            if scores[i] > 0:
                results.append((self.chunks[i]["content"], self.chunks[i]["source"]))
        return results

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
