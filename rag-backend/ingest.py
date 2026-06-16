"""
ingest.py — 知识入库脚本（Embedding 语义版）

作用：读取 knowledge/ 目录下的所有 .txt / .md 文件，
     切分成小块 → Embedding 向量化 → 保存索引。

用法：python3 ingest.py
每次修改 knowledge/ 里的文件后，重新跑一次即可。
"""

import os
from retriever import Retriever

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 知识库入库（Embedding 语义检索）\n")

    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"⚠️  {KNOWLEDGE_DIR} 目录不存在")
        exit(1)

    r = Retriever()
    total = r.build(KNOWLEDGE_DIR)

    print(f"\n✅ 入库完成！共 {total} 个切片")
    print(f"   索引文件: {os.path.join(os.path.dirname(__file__), 'embeddings.pkl')}")
    print(f"   可以直接运行 main.py 开始聊天")
