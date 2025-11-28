# src/check_data.py
import json
from collections import Counter
from config import DATA_PROCESSED_DIR


def check_data_consistency():
    """检查数据一致性"""
    json_file = DATA_PROCESSED_DIR / "laws_processed.json"

    print(f"📁 检查数据文件: {json_file}")

    if not json_file.exists():
        print("❌ JSON文件不存在")
        return

    # 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 JSON文件总记录数: {len(data)}")

    # 检查内容重复
    content_counter = Counter([item['content'] for item in data])
    duplicates = {k: v for k, v in content_counter.items() if v > 1}

    print(f"🔄 重复内容数量: {len(duplicates)}")
    if duplicates:
        print("重复内容示例:")
        for content, count in list(duplicates.items())[:3]:
            print(f"  ×{count}: {content[:50]}...")

    # 检查空内容
    empty_content = len([d for d in data if not d.get('content', '').strip()])
    print(f"📭 空内容记录: {empty_content}")

    # 检查法律分布
    law_counter = Counter([item['law'] for item in data])
    print(f"📚 涉及法律数量: {len(law_counter)}")
    print("法律分布前5:")
    for law, count in law_counter.most_common(5):
        print(f"  《{law}》: {count} 条")

    # 检查章节标题和条款
    chapter_titles = len([d for d in data if d.get('is_chapter_title', False)])
    actual_articles = len([d for d in data if d.get('article_number', 0) > 0])
    print(f"📑 章节标题: {chapter_titles}")
    print(f"⚖️ 实际条款: {actual_articles}")


if __name__ == "__main__":
    check_data_consistency()