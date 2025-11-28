# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_RAW_DIR = DATA_DIR / 'raw'
DATA_PROCESSED_DIR = DATA_DIR / 'processed'
SRC_DIR = BASE_DIR / 'src'

# Gemini API 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ 请在 .env 文件中设置 GEMINI_API_KEY")

# ChromaDB 配置
CHROMA_DB_PATH = DATA_PROCESSED_DIR / "chroma_db"

# 确保目录存在
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)