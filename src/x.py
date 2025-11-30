def parse_text(lis):
    res, t2, t3, now_article = [], '', '', ''

    def flush_article():
        if now_article:
            res.append(f'{t2}, {t3}, {now_article}' if t3 else f'{t2}, {now_article}')

    for i, line in enumerate(lis):
        if line.startswith('#'):
            flush_article()
            now_article = ''

            if line.startswith('###'):
                t3 = line[4:]
            else:
                t2, t3 = line[2:], ''
        else:
            if line.startswith('第'):
                flush_article()
                now_article = line
            else:
                now_article += line

        if i == len(lis) - 1:
            flush_article()

    return res

from config import DATA_DIR


# 测试函数
if __name__ == "__main__":
    with open(f'{DATA_DIR}/doc.md', 'r', encoding='utf-8') as file:
        content_list = file.read()
    content_list = [c.strip() for c in content_list.split('\n\n')]
    law_name, content_list = content_list[0], content_list[1:]
    parsed_results = parse_text(content_list)
    for item in parsed_results:
        print(item)