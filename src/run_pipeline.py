# src/run_pipeline.py
from data_processing import process_all_files
from vectorize_documents import LawChromaDB
from config import DATA_PROCESSED_DIR
import os


def run_full_pipeline():
    """运行完整的数据处理管道"""
    print("🚀 开始数据处理和向量化...")

    # 1. 处理原始数据（按条款切分）
    print("1. 处理原始Markdown文件（按条款切分）...")
    json_file = process_all_files()

    if not json_file:
        print("❌ 数据处理失败")
        return

    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"❌ JSON文件不存在: {json_file}")
        return

    # 2. 向量化文档
    print("\n2. 向量化文档...")
    law_db = LawChromaDB()
    law_db.create_collection("chinese_laws")

    # 检查集合是否已有数据
    has_data, message = law_db.check_collection_status()
    if has_data:
        print(f"📊 当前集合状态: {message}")
        user_input = input("🔄 集合已有数据，是否重新添加？(y/n): ")
        if user_input.lower() not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return
        else:
            # 清空现有集合
            law_db.clear_collection()
            law_db.create_collection("chinese_laws")

    # 询问批次大小
    try:
        batch_size = int(input("📦 请输入批次大小 (推荐 500-1000): ") or "500")
    except:
        batch_size = 500

    print(f"🔧 使用批次大小: {batch_size}")

    success = law_db.add_laws_from_json(
        f"{DATA_PROCESSED_DIR}/laws_processed.json",
        batch_size=batch_size
    )

    if success:
        # 3. 检查结果
        count = law_db.collection.count()
        print(f"\n✅ 数据处理和向量化完成！")
        print(f"📊 向量数据库中的条款数量: {count}")
    else:
        print("❌ 向量化失败")


if __name__ == "__main__":
    run_full_pipeline()