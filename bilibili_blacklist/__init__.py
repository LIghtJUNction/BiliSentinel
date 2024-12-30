from typing import Optional
import logging
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = ROOT_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
BLACKLIST_DIR = DATA_DIR / "blacklists"
AUDIT_DIR = DATA_DIR / "audit_records"

# 确保目录存在
for directory in [DATA_DIR, STORAGE_DIR, BLACKLIST_DIR, AUDIT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT_DIR / "app.log", encoding="utf-8")
    ]
) 