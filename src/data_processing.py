# src/data_processing.py
import re
import json
from pathlib import Path

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR


def extract_type_from_folder(folder_name: str) -> str:
    """从文件夹名称提取法律类型"""
    if '-' in folder_name:
        return folder_name.split('-', 1)[1]
    return folder_name


def extract_law_name_from_file(file_name: str) -> str:
    """从文件名提取法律名称，去除括号内容"""
    name = Path(file_name).stem
    pattern = r'\s*\([^)]+\)$'
    return re.sub(pattern, '', name)


def parse_law_content(content: str):
    """
    按条款切分法律内容，每条记录对应一个法律条款
    """
    lines = content.split('\n')
    results = []

    current_chapter = "第一章 总则"
    current_article = ""
    current_content = []
    article_number = 0

    for line in lines:
        line = line.strip()

        # 跳过空行和注释标记
        if not line or line == "<!-- INFO END -->":
            continue

        # 检测章节标题
        if line.startswith('## '):
            current_chapter = line[3:].strip()
            # 章节标题单独作为一条记录
            results.append({
                "chapter": current_chapter,
                "content": line,
                "is_chapter_title": True,
                "article_number": 0
            })
            continue

        # 检测条款开始（第X条）
        article_match = re.match(r'^(第[一二三四五六七八九十百千万零\d]+条)', line)
        if article_match:
            # 保存前一条款
            if current_article and current_content:
                article_number += 1
                full_content = '\n'.join(current_content).strip()
                results.append({
                    "chapter": current_chapter,
                    "article_title": current_article,
                    "content": full_content,
                    "is_chapter_title": False,
                    "article_number": article_number
                })

            # 开始新条款
            current_article = article_match.group(1)
            current_content = [line]
        else:
            # 普通内容行，添加到当前条款
            if current_content and line:
                current_content.append(line)
            elif line and not current_article:
                # 章节内的说明性文字，单独作为记录
                results.append({
                    "chapter": current_chapter,
                    "article_title": "",
                    "content": line,
                    "is_chapter_title": False,
                    "article_number": 0
                })

    # 处理最后一条条款
    if current_article and current_content:
        article_number += 1
        full_content = '\n'.join(current_content).strip()
        results.append({
            "chapter": current_chapter,
            "article_title": current_article,
            "content": full_content,
            "is_chapter_title": False,
            "article_number": article_number
        })

    return results


def process_single_file(path: Path):
    """处理单个法律文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 分离元信息和法律内容
        parts = content.split("<!-- INFO END -->", 1)
        if len(parts) != 2:
            print(f"⚠️ 文件格式错误: {path}")
            return []

        _, law_content = parts
        parsed_articles = parse_law_content(law_content)

        # 添加元数据
        folder_name = path.parent.name
        law_type = extract_type_from_folder(folder_name)
        law_name = extract_law_name_from_file(path.name)

        for article in parsed_articles:
            article.update({
                "type": law_type,
                "law": law_name,
                "source_file": path.name,
                "content_length": len(article["content"])
            })

        print(f"  📊 切分为 {len(parsed_articles)} 个条款")
        return parsed_articles

    except Exception as e:
        print(f"❌ 处理文件失败 {path}: {e}")
        return []


def analyze_article_distribution(data):
    """分析条款分布"""
    total_articles = len(data)
    chapter_titles = len([d for d in data if d.get('is_chapter_title', False)])
    actual_articles = len([d for d in data if d.get('article_number', 0) > 0])
    other_content = total_articles - chapter_titles - actual_articles

    print(f"\n📈 条款分布分析:")
    print(f"   总记录数: {total_articles}")
    print(f"   章节标题: {chapter_titles}")
    print(f"   法律条款: {actual_articles}")
    print(f"   其他内容: {other_content}")

    # 内容长度分布
    lengths = [item["content_length"] for item in data]
    print(f"   平均长度: {sum(lengths) / len(lengths):.0f} 字符")
    print(f"   最小长度: {min(lengths)} 字符")
    print(f"   最大长度: {max(lengths)} 字符")

    # 长度分布
    dist = {
        "小于100": len([l for l in lengths if l < 100]),
        "100-300": len([l for l in lengths if 100 <= l < 300]),
        "300-500": len([l for l in lengths if 300 <= l < 500]),
        "大于500": len([l for l in lengths if l >= 500])
    }

    print("   长度分布:")
    for range_name, count in dist.items():
        percentage = (count / total_articles) * 100
        print(f"     {range_name}: {count} 条 ({percentage:.1f}%)")


def process_all_files(raw_dir: Path = DATA_RAW_DIR,
                      output_json: Path = DATA_PROCESSED_DIR / "laws_processed.json"):
    """处理所有法律文件"""

    md_files = list(raw_dir.rglob("*.md"))
    print(f"📄 找到 {len(md_files)} 个 Markdown 文件")

    if not md_files:
        print("❌ 没有找到Markdown文件，请检查 data/raw 目录")
        return None

    all_data = []
    processed_files = 0

    for md_file in md_files:
        print(f"\n➡️ 处理 {md_file.relative_to(raw_dir)}")
        file_data = process_single_file(md_file)
        all_data.extend(file_data)
        processed_files += 1
        print(f"  ✅ 已完成 {processed_files}/{len(md_files)} 文件")

    # 创建输出目录
    output_json.parent.mkdir(parents=True, exist_ok=True)

    # 保存处理结果
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # 输出统计信息
    print(f"\n🎉 处理完成!")
    print(f"   处理文件: {processed_files} 个")
    print(f"   生成条款: {len(all_data)} 条")
    print(f"   输出文件: {output_json}")

    # 分析条款分布
    analyze_article_distribution(all_data)

    return output_json


if __name__ == "__main__":
    process_all_files()