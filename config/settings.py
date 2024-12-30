from pathlib import Path
from typing import Dict, Any

# 基础配置
BASE_CONFIG: Dict[str, Any] = {
    "APP_NAME": "Bilibili Blacklist Manager",
    "VERSION": "2.0.0",
    
    # API设置
    "API_TIMEOUT": 30,
    "API_RETRY": 3,
    "API_DELAY": 1.0,
    
    # 存储设置
    "STORAGE_TYPE": "file",  # file/memory
    
    # 审核设置
    "AUDIT_BATCH_SIZE": 20,
    "POINTS_PER_AUDIT": 1,
    
    # UI设置
    "THEME": "default",
    "PAGE_SIZE": 20,
}

# 开发环境配置
DEV_CONFIG = {
    **BASE_CONFIG,
    "DEBUG": True,
    "LOG_LEVEL": "DEBUG",
}

# 生产环境配置
PROD_CONFIG = {
    **BASE_CONFIG,
    "DEBUG": False,
    "LOG_LEVEL": "INFO",
} 