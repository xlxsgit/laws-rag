# py: /src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Define base directories
ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"

# embedding model and vector DB configurations
embedding_model = 'BAAI/bge-small-zh-v1.5'
embedding_DIR = ROOT_DIR / 'data' / embedding_model.split('/')[-1]

reranker_name = 'BAAI/bge-reranker-base'
reranker_DIR = ROOT_DIR / 'data' / reranker_name.split('/')[-1]

VECTOR_DB_DIR = ROOT_DIR / "data/vector_db"

# Load environment variables from .env file
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
HUGGINGFACE_HUB_TOKEN = os.getenv("HUGGINGFACE_HUB_TOKEN")