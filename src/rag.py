# py: /src/rag.py
from typing import List, Dict, Any
from config import MODELSCOPE_API_KEY, embedding_DIR, reranker_DIR, VECTOR_DB_DIR
from openai import OpenAI
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb


class LawRAGSystem:
    def __init__(self):
        self.embedding_model = SentenceTransformer(str(embedding_DIR))

        self.client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        self.collection = self.client.get_collection("laws_collection")

        self.llm = OpenAI(
            api_key=MODELSCOPE_API_KEY,
            base_url="https://api-inference.modelscope.cn/v1/"
        )

        self._reranker = None
        self.history = []

    @property
    def reranker(self):
        if self._reranker is None:
            self._reranker = CrossEncoder(str(reranker_DIR))
        return self._reranker

    def embed(self, text: str):
        return self.embedding_model.encode(text, normalize_embeddings=True).tolist()

    def retrieve(self, query: str, k=10):
        emb = self.embed(query)
        result = self.collection.query(query_embeddings=[emb], n_results=k)
        return result["documents"][0]

    def rerank(self, query: str, docs: List[str], k=5):
        pairs = [(query, d) for d in docs]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [d for d, _ in ranked[:k]]

    def answer(self, query: str):
        retrieved = self.retrieve(query)
        reranked = self.rerank(query, retrieved)

        context = "\n\n".join(reranked)

        messages = [
            {"role": "system",
             "content": f"请基于以下法律条文回答问题，不得编造：\n\n{context}"},
            {"role": "user", "content": query}
        ]

        resp = self.llm.chat.completions.create(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            messages=messages
        )

        answer = resp.choices[0].message.content
        self.history.append((query, answer))

        return answer, reranked

    def show_history(self):
        if not self.history:
            print("📝 暂无对话历史。")
            return
        print("\n📖 对话历史：")
        print("-" * 100)
        for i, (q, a) in enumerate(self.history, 1):
            print(f"\n第 {i} 轮对话：")
            print(f"💭 用户：{q}")
            print(f"⏳ 回答：{a}")
        print("-" * 100)

    def clear(self):
        self.history.clear()
        print("🗑️  对话历史已清空。")


def interactive_dialogue():
    print("=" * 100)
    print("✨ 法律智能问答系统")
    print("使用说明：")
    print("  • 输入 'quit' 或 'exit' 退出系统")
    print("  • 输入 'clear' 清空对话历史")
    print("  • 输入 'history' 查看对话历史")
    print("=" * 100)

    rag = LawRAGSystem()

    while True:
        try:
            print("-" * 100)
            q = input("💭 用户：").strip()

            if q.lower() in ["quit", "exit"]:
                print("\n👋 感谢使用，再见！")
                break
            if q.lower() == "clear":
                rag.clear()
                continue
            if q.lower() == "history":
                rag.show_history()
                continue
            if not q:
                print("⚠️  请输入有效的问题。")
                continue

            answer, ref = rag.answer(q)

            print("-" * 100)
            print("⏳ 回答：")
            print(answer)

            print("-" * 30)
            print("📚 参考法律条文：")
            for i, c in enumerate(ref, 1):
                print(f"{i}. {c}")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断操作，感谢使用！")
            break
        except Exception as e:
            print(f"\n❌ 系统出现错误：{e}")
            print("请重新尝试或联系技术支持。")


if __name__ == "__main__":
    interactive_dialogue()