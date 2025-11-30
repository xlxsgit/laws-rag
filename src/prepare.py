# py: /src/prepare.py
from typing import List, Tuple
from config import DATA_DIR, embedding_DIR, VECTOR_DB_DIR
from sentence_transformers import SentenceTransformer
import chromadb
import os
import re


def parse_text(file_path: str) -> List[Tuple[str, str]]:
    """
    解析法律文档，返回 (元数据, 纯净内容)
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    if not paragraphs:
        return []

    law_name = paragraphs[0]
    paragraphs = paragraphs[1:]

    results = []
    current_chapter = ""
    current_section = ""
    current_article = ""

    def flush_article():
        nonlocal current_article
        if current_article.strip():
            metadata = ", ".join(filter(None, [current_chapter, current_section]))
            results.append((metadata, current_article.strip()))
            current_article = ""

    for line in paragraphs:
        line = line.strip()
        if not line:
            continue

        if line.startswith('## '):
            flush_article()
            current_chapter = line[3:].strip()
            current_section = ""
        elif line.startswith('### '):
            flush_article()
            current_section = line[4:].strip()
        elif re.match(r'^第[\u4e00-\u9fa5\d]+条', line):
            flush_article()
            current_article = line
        else:
            current_article += " " + line

    flush_article()
    return results


def create_chunk_with_context(metadata: str, content: str) -> str:
    return f"{metadata} | {content}" if metadata else content


def embed_chunk(chunk: str, embedding_model: SentenceTransformer):
    return embedding_model.encode(chunk, normalize_embeddings=True).tolist()


def save_embeddings(chunks, embeddings, collection):
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[emb],
            metadatas=[{"chunk_id": i}],
            ids=[f"chunk_{i}"]
        )


def main():
    print("开始处理法律文档...")

    parsed = parse_text(f'{DATA_DIR}/doc.md')
    print(f"解析到 {len(parsed)} 个条文")

    chunks = [
        create_chunk_with_context(metadata, content)
        for metadata, content in parsed
    ]

    print("加载 embedding 模型...")
    model = SentenceTransformer(str(embedding_DIR))

    print("生成向量...")
    embeddings = [embed_chunk(c, model) for c in chunks]

    print("初始化 ChromaDB...")
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)

    try:
        client.delete_collection("laws_collection")
    except:
        pass

    collection = client.get_or_create_collection("laws_collection")

    print("写入向量数据库...")
    save_embeddings(chunks, embeddings, collection)

    print("🎉 完成！向量数据库已生成。")


if __name__ == "__main__":
    main()
