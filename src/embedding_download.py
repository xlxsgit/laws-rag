# py ./src/embedding_download.py
from sentence_transformers import SentenceTransformer, CrossEncoder
from config import embedding_model, embedding_DIR, reranker_name, reranker_DIR, HUGGINGFACE_HUB_TOKEN
import os
os.environ['HUGGINGFACE_HUB_TOKEN'] = HUGGINGFACE_HUB_TOKEN


# 创建本地目录
os.makedirs(embedding_DIR, exist_ok=True)
os.makedirs(reranker_DIR, exist_ok=True)

# 下载并保存
print("正在下载SentenceTransformer模型...")
model_st = SentenceTransformer(embedding_model)
model_st.save(embedding_DIR)

print("正在下载CrossEncoder模型...")
model_ce = CrossEncoder(embedding_model)
model_ce.save(reranker_DIR)

