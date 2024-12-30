import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLACKLIST_DIR = os.path.join(BASE_DIR, "blacklists")
AUDIT_RECORDS_DIR = os.path.join(BASE_DIR, "audit_records")
POINTS_RECORDS_DIR = os.path.join(BASE_DIR, "points_records")

# API限流
MIN_INTERVAL = 1.0
MAX_INTERVAL = 3.0
MAX_RETRIES = 3

# SCP文件
SCP_TYPES = ['0000', '1989', '3666']
SCP_FILES = {
    "SCP-0000": "社区共建黑名单",
    "SCP-1989": "自动收容名单",
    "SCP-3666": "自动收容名单",
}

# 积分规则
POINT_RULES = {
    "AUDIT": {
        "KEEP": 2,     # 保留审核
        "REMOVE": 1    # 移除审核
    },
    "CONTRIBUTE": {
        "SCP_0000": 5,  # 贡献到社区黑名单
        "SCP_1989": 3,  # 贡献到机器黑名单
        "SCP_3666": 3   # 贡献到麦片黑名单
    }
}

# 机械判断规则
MECHANICAL_RULES = {
    "等级过低": lambda x: x.get("level", 0) <= 2,
    "无签名": lambda x: not x.get("sign", ""),
    "默认昵称": lambda x: x.get("name", "").startswith(("bili_", "用户")),
    "无关注": lambda x: x.get("following", 0) == 0,
    "极少粉丝": lambda x: x.get("follower", 0) <= 3,
    "关注粉丝比异常": lambda x: (
        x.get("following", 0) > 0 and 
        x.get("follower", 0) > 0 and
        (
            x.get("following", 0) / x.get("follower", 0) > 1000 or
            x.get("follower", 0) / x.get("following", 0) > 1000
        )
    )
}

# 黑名单限制
MAX_BLACKLIST_NORMAL = 1000  # 普通用户上限
MAX_BLACKLIST_VIP = 10000    # 大会员上限
FOLLOWER_THRESHOLD = 10000   # 粉丝数阈值

# 审核设置
AUDIT_PAGE_LIMIT = 5         # 每次审核页数限制
PBKDF2_ITERATIONS = 100000   # 密钥派生迭代次数
TIME_WINDOW = 86400         # 时间窗口(24小时)

# 安全相关
PROJECT_KEY = b"bilibili_blacklist_v1"  # 用于签名的项目密钥