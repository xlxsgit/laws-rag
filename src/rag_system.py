# src/rag_system.py
import google.generativeai as genai
from config import GEMINI_API_KEY, CHROMA_DB_PATH
from vectorize_documents import LawChromaDB
from typing import List, Dict
import sys
import textwrap


class LawRAGSystem:
    def __init__(self, chroma_db_path=CHROMA_DB_PATH):
        # 检查API密钥
        if not GEMINI_API_KEY:
            raise ValueError("❌ Gemini API密钥未设置，请检查 .env 文件")

        # 初始化向量数据库
        print("🔧 初始化向量数据库...")
        self.vector_db = LawChromaDB(str(chroma_db_path))
        self.vector_db.create_collection("chinese_laws")

        # 检查集合状态
        has_data, message = self.vector_db.check_collection_status()
        print(f"📊 {message}")

        if not has_data:
            print("❌ 向量数据库为空！请先运行数据处理管道")
            print("💡 运行: python src/run_pipeline.py")
            sys.exit(1)

        # 配置Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        print("✅ RAG系统初始化完成 - 使用Gemini 2.0 Flash")

    def search_relevant_laws(self, query: str, n_results: int = 5) -> List[Dict]:
        """搜索相关的法律条文"""
        try:
            results = self.vector_db.search_similar_laws(query, n_results)
            return results
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []

    def format_context(self, search_results: List[Dict]) -> str:
        """格式化检索到的上下文"""
        if not search_results:
            return "未找到相关的法律条文。"

        context_parts = []
        for i, result in enumerate(search_results, 1):
            similarity = 1 - result['distance']
            context_parts.append(
                f"【相关条文 {i} - 相似度 {similarity:.3f}】\n"
                f"法律名称: {result['metadata']['law']}\n"
                f"章节: {result['metadata']['chapter']}\n"
                f"内容: {result['content']}\n"
                f"{'-' * 50}"
            )
        return "\n".join(context_parts)

    def build_prompt(self, query: str, context: str, search_results: List[Dict]) -> str:
        """构建提示词"""
        # 分析问题类型
        question_type = self.analyze_question_type(query)

        base_prompt = f"""你是一个专业的法律AI助手，请基于以下相关法律条文并结合你的法律知识来回答用户的问题。

相关法律条文：
{context}

用户问题：{query}

请按照以下要求回答：
1. 首先理解用户问题的意图：{question_type}
2. 如果检索到的条文相关，请基于这些条文进行解释和说明
3. 如果条文不相关或不足以完整回答问题，请结合你的法律知识进行补充
4. 对于概念性问题，请先给出定义，再引用相关条文
5. 对于具体案例咨询，请分析相关法律规定
6. 回答要专业、准确、易懂，避免过于技术化的表述
7. 适当举例说明，帮助用户理解

请基于以上要求，给出专业且有用的回答："""

        return base_prompt

    def analyze_question_type(self, query: str) -> str:
        """分析问题类型"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['是什么', '什么是', '定义', '概念', '介绍']):
            return "概念解释型问题"
        elif any(word in query_lower for word in ['怎么办', '如何处理', '怎么解决', '步骤', '程序']):
            return "操作指导型问题"
        elif any(word in query_lower for word in ['权利', '义务', '责任', '应当', '必须']):
            return "权利义务型问题"
        elif any(word in query_lower for word in ['案例', '例子', '举例', '实际情况']):
            return "案例咨询型问题"
        elif any(word in query_lower for word in ['区别', '不同', '对比']):
            return "比较分析型问题"
        else:
            return "一般咨询型问题"

    def format_answer_with_wrap(self, text: str, width: int = 80) -> str:
        """格式化文本，自动换行"""
        wrapped_lines = []
        for line in text.split('\n'):
            if len(line) <= width:
                wrapped_lines.append(line)
            else:
                wrapped_lines.extend(textwrap.wrap(line, width=width))
        return '\n'.join(wrapped_lines)

    def print_section_header(self, title: str):
        """打印章节标题"""
        print(f"\n{'━' * 60}")
        print(f"📖 {title}")
        print(f"{'━' * 60}")

    def print_law_reference(self, source: Dict, index: int):
        """打印法律引用详情"""
        law_name = source['law']
        chapter = source['chapter']
        article_title = source.get('article_title', '')
        relevance = source['relevance_score']
        content = source['content']

        print(f"\n🔍 引用 {index}：《{law_name}》")
        print(f"   📍 章节：{chapter}")
        if article_title:
            print(f"   📑 条款：{article_title}")
        print(f"   ⭐ 相关度：{relevance:.3f}")
        print(f"   📝 具体内容：")

        # 格式化内容，添加缩进
        formatted_content = textwrap.fill(content, width=70, subsequent_indent='   ')
        print(f"   {formatted_content}")

    def ask_question(self, query: str, n_results: int = 8) -> Dict:
        """提问并获取回答"""
        try:
            print(f"🔍 检索相关法律条文: '{query}'")
            search_results = self.search_relevant_laws(query, n_results)

            context = self.format_context(search_results)
            prompt = self.build_prompt(query, context, search_results)

            print("🤖 生成回答...")
            response = self.model.generate_content(prompt)

            # 构建结果
            result = {
                "answer": response.text,
                "sources": [
                    {
                        "law": result['metadata']['law'],
                        "chapter": result['metadata']['chapter'],
                        "type": result['metadata']['type'],
                        "content": result['content'],  # 显示完整内容
                        "relevance_score": round(1 - result['distance'], 3)
                    }
                    for result in search_results
                ] if search_results else [],
                "has_relevant_laws": len(search_results) > 0,
                "query": query
            }

            return result

        except Exception as e:
            return {
                "answer": f"处理问题时出现错误：{str(e)}",
                "sources": [],
                "has_relevant_laws": False,
                "error": str(e)
            }

    def chat_loop(self):
        """交互式聊天循环"""
        print("\n" + "=" * 70)
        print("🎯 法律智能问答系统")
        print("💎 基于检索增强生成 (RAG) + Gemini 2.0 Flash")
        print("=" * 70)
        print("💡 您可以询问：")
        print("   • 法律概念解释（如：什么是正当防卫？）")
        print("   • 权利义务咨询（如：劳动者有哪些权利？）")
        print("   • 法律程序指导（如：如何申请行政复议？）")
        print("   • 具体法律规定（如：关于劳动合同解除的规定？）")
        print("💡 输入 '退出' 或 'quit' 结束对话")
        print("=" * 70)

        while True:
            try:
                query = input("\n💬 请输入您的法律问题： ").strip()

                if query.lower() in ['退出', 'quit', 'exit']:
                    print("\n👋 感谢使用！再见！")
                    break

                if not query:
                    print("⚠️ 请输入问题")
                    continue

                # 获取回答
                result = self.ask_question(query)

                # 显示回答部分
                self.print_section_header("AI 回答")
                formatted_answer = self.format_answer_with_wrap(result["answer"])
                print(formatted_answer)

                # 显示引用部分
                if result["has_relevant_laws"]:
                    self.print_section_header("📚 相关法律条文")
                    print(f"共找到 {len(result['sources'])} 条相关条文：")

                    # 按相关度排序并显示
                    sorted_sources = sorted(result['sources'],
                                            key=lambda x: x['relevance_score'],
                                            reverse=True)

                    for i, source in enumerate(sorted_sources, 1):
                        if source['relevance_score'] > 0.1:  # 显示所有相关度>0.1的条文
                            self.print_law_reference(source, i)
                        if i >= 5:  # 最多显示5条
                            remaining = len(sorted_sources) - 5
                            if remaining > 0:
                                print(f"\n📋 还有 {remaining} 条相关条文未显示...")
                            break
                else:
                    self.print_section_header("💡 提示")
                    print("未找到高度相关的法律条文，以上回答基于AI的法律知识库")

                print("\n" + "=" * 70)

            except KeyboardInterrupt:
                print("\n👋 感谢使用！再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误：{e}")


if __name__ == "__main__":
    rag_system = LawRAGSystem()
    rag_system.chat_loop()