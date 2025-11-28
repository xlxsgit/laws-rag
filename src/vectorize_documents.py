# src/vectorize_documents.py
import chromadb
import json
import uuid
from typing import List, Dict
from config import DATA_PROCESSED_DIR
import os


class LawChromaDB:
    def __init__(self, persist_directory=None):
        if persist_directory is None:
            persist_directory = DATA_PROCESSED_DIR / "chroma_db"

        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)

        print(f"📁 ChromaDB路径: {persist_directory}")
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = None

    def create_collection(self, collection_name="chinese_laws"):
        """创建或获取集合"""
        try:
            # 先尝试获取，如果不存在再创建
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ 加载现有集合 '{collection_name}'")
        except:
            # 集合不存在，创建新集合
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "中国法律条文向量数据库"}
            )
            print(f"✅ 创建新集合 '{collection_name}'")

    def add_laws_from_json(self, json_file_path: str, batch_size: int = 1000):
        """从 JSON 文件分批添加法律数据"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                laws_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ JSON文件不存在: {json_file_path}")
            return False
        except Exception as e:
            print(f"❌ 读取JSON文件失败: {e}")
            return False

        if not laws_data:
            print("❌ JSON文件为空")
            return False

        print(f"📥 开始处理 {len(laws_data)} 条法律条款...")
        print(f"📦 批次大小: {batch_size} 条")

        total_added = 0
        batch_count = 0

        # 分批处理
        for i in range(0, len(laws_data), batch_size):
            batch = laws_data[i:i + batch_size]
            batch_count += 1

            documents = []
            metadatas = []
            ids = []

            for law in batch:
                # 跳过空内容
                if not law.get('content', '').strip():
                    continue

                documents.append(law['content'])
                metadatas.append({
                    'chapter': law.get('chapter', ''),
                    'type': law.get('type', ''),
                    'law': law.get('law', ''),
                    'article_title': law.get('article_title', ''),
                    'article_number': law.get('article_number', 0),
                    'is_chapter_title': law.get('is_chapter_title', False),
                    'source_file': law.get('source_file', ''),
                    'content_length': law.get('content_length', 0)
                })
                ids.append(str(uuid.uuid4()))

            if not documents:
                print(f"  批次 {batch_count} 没有有效数据，跳过")
                continue

            print(f"📤 正在添加批次 {batch_count} ({len(documents)} 条)...")

            try:
                # 批量添加到集合
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                total_added += len(documents)
                print(f"  ✅ 批次 {batch_count} 添加成功，累计 {total_added} 条")

            except Exception as e:
                print(f"  ❌ 批次 {batch_count} 添加失败: {e}")
                # 可以继续处理下一批，或者根据需求决定是否停止
                continue

        print(f"🎉 所有批次处理完成！")
        print(f"📊 成功添加 {total_added} 条法律条文到数据库")
        print(f"📦 总共处理 {batch_count} 个批次")

        return total_added > 0

    def search_similar_laws(self, query: str, n_results: int = 5) -> List[Dict]:
        """搜索相似的法律条文"""
        if not self.collection:
            raise ValueError("请先创建集合并添加数据")

        # 检查集合是否为空
        count = self.collection.count()
        if count == 0:
            print("⚠️ 集合为空，无法搜索")
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, count)  # 避免请求超过实际数量
        )

        formatted_results = []

        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'id': results['ids'][0][i]
                })

        return formatted_results

    def get_collection_info(self):
        """获取集合信息"""
        if not self.collection:
            return "集合未创建"

        count = self.collection.count()
        return f"集合中共有 {count} 条法律条文"

    def check_collection_status(self):
        """检查集合状态"""
        if not self.collection:
            return False, "集合未创建"

        count = self.collection.count()
        return count > 0, f"集合中有 {count} 条记录"

    def clear_collection(self):
        """清空集合"""
        if self.collection:
            try:
                self.client.delete_collection("chinese_laws")
                print("🗑️ 集合已清空")
                self.collection = None
            except Exception as e:
                print(f"❌ 清空集合失败: {e}")


if __name__ == "__main__":
    law_db = LawChromaDB()
    law_db.create_collection("chinese_laws")

    # 检查状态
    has_data, message = law_db.check_collection_status()
    print(f"集合状态: {message}")

    if not has_data:
        print("正在添加数据...")
        law_db.add_laws_from_json(f"{DATA_PROCESSED_DIR}/laws_processed.json")
        has_data, message = law_db.check_collection_status()
        print(f"添加后状态: {message}")