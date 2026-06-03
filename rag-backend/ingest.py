"""
ingest.py — 知识入库脚本

作用：读取 knowledge/ 目录下的所有 .txt / .md 文件，
     切分成小块 → 向量化 → 存入 Chroma 向量数据库。

用法：python3 ingest.py
每次修改 knowledge/ 里的文件后，重新跑一次即可。
"""

import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================================
# 配置
# ============================================================
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")  # 知识库文件目录
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")   # 向量数据库存储位置
COLLECTION_NAME = "zhangqiang"                                        # 集合名称（相当于"库名"）
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"                            # 中文嵌入模型

# ============================================================
# 第一步：加载嵌入模型
# ============================================================
print("📦 加载嵌入模型...")
print(f"   模型: {EMBEDDING_MODEL}")
print("   （首次运行会自动下载，约 100MB，之后直接用本地缓存）")
model = SentenceTransformer(EMBEDDING_MODEL)
print("   ✅ 模型就绪\n")


# ============================================================
# 第二步：读取所有知识库文件
# ============================================================
def load_knowledge_files(directory):
    """
    扫描 knowledge/ 目录，读取所有 .txt 和 .md 文件。
    返回：[{ "file": "文件名", "content": "全文内容" }, ...]
    """
    files = []
    for filename in sorted(os.listdir(directory)):
        # 跳过隐藏文件（如 .DS_Store）
        if filename.startswith("."):
            continue
        # 只读 .txt 和 .md
        if not (filename.endswith(".txt") or filename.endswith(".md")):
            continue

        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        files.append({"file": filename, "content": content})
        print(f"📄 读取: {filename} ({len(content)} 字)")

    return files


# ============================================================
# 第三步：切片 —— 按 ## 标题切分
# ============================================================
def split_by_headings(content, max_chunk_size=1500, overlap=100):
    """
    把一篇长文章切成多个小块（chunk）。

    策略：
    1. 优先按 ## 二级标题切 —— 每个标题段落是一个独立切片
    2. 如果某个切片太长（超过 max_chunk_size），递归按段落切
    3. 相邻切片之间有 overlap 字的重叠，防止信息在边界丢失
    """

    # ---- 3a. 尝试按 ## 标题切分 ----
    # 正则匹配：以 ## 开头的行
    heading_pattern = re.compile(r"^#{1,2}\s+.+$", re.MULTILINE)

    # 找到所有标题的位置
    heading_positions = []
    for match in heading_pattern.finditer(content):
        heading_positions.append(match.start())

    # 如果没有任何标题，整篇当作一个切片
    if not heading_positions:
        return [{"content": content.strip(), "source": "无标题"}]

    # 按标题边界切分
    raw_sections = []
    for i, pos in enumerate(heading_positions):
        # 确定当前段的起始位置
        start = pos
        # 确定当前段的结束位置（下一个标题之前，或文章末尾）
        end = heading_positions[i + 1] if i + 1 < len(heading_positions) else len(content)
        section_text = content[start:end].strip()
        if section_text:
            # 提取标题作为来源标记
            title_line = section_text.split("\n")[0].strip().lstrip("#").strip()
            raw_sections.append({"content": section_text, "source": title_line})

    # ---- 3b. 处理过长切片 ----
    chunks = []
    for section in raw_sections:
        text = section["content"]
        source = section["source"]

        # 如果这个段落不超过上限，直接作为一个切片
        if len(text) <= max_chunk_size:
            chunks.append({"content": text, "source": source})
            continue

        # 太长的话，按两个换行（段落边界）细分
        paragraphs = text.split("\n\n")
        current_chunk = ""
        for para in paragraphs:
            # 加上这一段后会不会超长？
            if len(current_chunk) + len(para) <= max_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                # 保存当前切片
                if current_chunk.strip():
                    chunks.append({"content": current_chunk.strip(), "source": source})
                # 开始新切片，带上 overlap
                # overlap: 从前一个切片末尾取 overlap 个字拼到开头
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para

        # 最后一个切片
        if current_chunk.strip():
            chunks.append({"content": current_chunk.strip(), "source": source})

    return chunks


# ============================================================
# 第四步：把切片存入 Chroma
# ============================================================
def store_chunks(chunks, file_name):
    """
    把切片列表：向量化 → 存入 Chroma。
    每个切片有：唯一 ID、文本内容、元信息（来源文件、来源标题）
    """

    # 4a. 连接 Chroma 数据库
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 4b. 准备数据
    ids = []          # 唯一标识
    texts = []        # 文本内容
    metadatas = []    # 元信息

    for i, chunk in enumerate(chunks):
        # ID 格式：文件名_序号，确保唯一
        chunk_id = f"{file_name}_{i}"
        ids.append(chunk_id)
        texts.append(chunk["content"])
        metadatas.append({
            "file": file_name,
            "source": chunk["source"]
        })

    # 4c. 向量化 + 写入（Chroma 自动调用 embedding 模型）
    print(f"   🔄 向量化 {len(chunks)} 个切片...")
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"   ✅ 已存入 {len(chunks)} 个切片")
    return len(chunks)


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 知识库入库\n")

    # 读文件
    files = load_knowledge_files(KNOWLEDGE_DIR)
    if not files:
        print("⚠️  knowledge/ 目录下没有 .txt 或 .md 文件，请先放入内容")
        exit(1)

    # 先清空旧数据（避免重复）
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("\n🗑️  已清空旧数据\n")
    except Exception:
        pass  # 第一次运行没有旧数据，忽略

    # 逐文件处理
    total_chunks = 0
    for f in files:
        print(f"🔪 切片: {f['file']}")
        chunks = split_by_headings(f["content"], max_chunk_size=1200, overlap=80)

        # 打印切片概览
        for i, c in enumerate(chunks):
            print(f"     切片 {i+1}: 「{c['source'][:40]}」({len(c['content'])} 字)")

        count = store_chunks(chunks, f["file"])
        total_chunks += count
        print()

    # 验证
    collection = client.get_collection(name=COLLECTION_NAME)
    print("=" * 60)
    print(f"✅ 入库完成！共 {total_chunks} 个切片，来自 {len(files)} 个文件")
    print(f"   向量数据库位置: {CHROMA_DIR}")
    print(f"   可以直接运行 main.py 开始聊天")
