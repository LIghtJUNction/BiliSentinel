from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class UserInfo:
    """用户信息"""
    uid: str
    name: str
    level: int
    follower: int
    following: int
    sign: str = ""
    
@dataclass
class BlacklistEntry:
    """黑名单条目"""
    uid: str
    reason: str
    timestamp: float
    contributor: str
    scp_type: str
    
@dataclass
class AuditRecord:
    """审核记录"""
    uid: str
    action: str  # KEEP/REMOVE
    auditor: str
    timestamp: float
    reason: str = ""
    
@dataclass
class PointRecord:
    """积分记录"""
    uid: str
    points: int
    reason: str
    timestamp: float 