# src/project_lawsrag/config.py

from pathlib import Path

# ------------------------------
# 自动定位项目根目录
# ------------------------------
# 结构是: src/project_lawsrag/config.py
# 因此向上两级就是项目根目录
ROOT = Path(__file__).resolve().parents[2]

# ------------------------------
# 数据目录
# ------------------------------
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"

# ------------------------------
# 输出目录
# ------------------------------
OUTPUT_DIR = ROOT / "output"
FIG_DIR = OUTPUT_DIR / "figures"
MODEL_DIR = OUTPUT_DIR / "models"
TABLE_DIR = OUTPUT_DIR / "tables"

# ------------------------------
# 保证目录存在
# ------------------------------
for d in [
    DATA_DIR, RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR,
    OUTPUT_DIR, FIG_DIR, MODEL_DIR, TABLE_DIR
]:
    d.mkdir(parents=True, exist_ok=True)
