# src/project_lawsrag/utils/data_processing.py

import re
import json
from pathlib import Path

from project_lawsrag.config import RAW_DIR, PROCESSED_DIR


def extract_type_from_folder(folder_name: str) -> str:
    if '-' in folder_name:
        return folder_name.split('-', 1)[1]
    return folder_name


def extract_law_name_from_file(file_name: str) -> str:
    name = Path(file_name).stem
    pattern = r'\s*\([^)]+\)$'
    return re.sub(pattern, '', name)


def parse_law_content(content: str):
    lines = content.split('\n')
    results = []

    current_chapter = "第一章 总则"
    current_article = ""
    current_content = []

    for line in lines:
        line = line.strip()

        if line.startswith('## '):
            if current_article and current_content:
                results.append({
                    "chapter": current_chapter,
                    "content": "\n".join(current_content).strip()
                })
            current_chapter = line[3:].strip()
            current_article = ""
            current_content = []

        elif re.match(r'^第[一二三四五六七八九十百千万零\d]+条', line):
            if current_article and current_content:
                results.append({
                    "chapter": current_chapter,
                    "content": "\n".join(current_content).strip()
                })
            current_article = line
            current_content = [line]

        elif current_article and line:
            current_content.append(line)

    if current_article and current_content:
        results.append({
            "chapter": current_chapter,
            "content": "\n".join(current_content).strip()
        })

    return results


def process_single_file(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split("<!-- INFO END -->", 1)
    if len(parts) != 2:
        print(f"⚠️ 文件格式错误: {path}")
        return []

    _, law_content = parts
    parsed_items = parse_law_content(law_content)

    folder_name = path.parent.name
    law_type = extract_type_from_folder(folder_name)
    law_name = extract_law_name_from_file(path.name)

    for item in parsed_items:
        item["type"] = law_type
        item["law"] = law_name

    return parsed_items


def process_all_files(raw_dir: Path = RAW_DIR,
                      output_json: Path = PROCESSED_DIR / "laws.json"):

    md_files = list(raw_dir.rglob("*.md"))
    print(f"📄 找到 {len(md_files)} 个 Markdown 文件")

    all_data = []

    for md in md_files:
        print(f"➡️ 处理 {md}")
        all_data.extend(process_single_file(md))

    output_json.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 完成：{len(all_data)} 条记录")
    print(f"📁 输出：{output_json.resolve()}")


if __name__ == "__main__":
    process_all_files()
