import json
import os
import logging
from typing import Dict

class AuditCounter:
    def __init__(self, blacklist_dir: str):
        self.blacklist_dir = blacklist_dir
        self.counters = {}  # SCP计数
        self.user_audits = {}  # 用户审核记录 {user_uid: {scp_type: set(audited_uids)}}
        self._load_counters()
        
    def _load_counters(self):
        """加载计数器和审核记录"""
        counter_file = os.path.join(self.blacklist_dir, "audit_counters.json")
        try:
            if os.path.exists(counter_file):
                with open(counter_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.counters = data.get("counters", {})
                    
                    # 将list转回set
                    raw_audits = data.get("user_audits", {})
                    self.user_audits = {
                        user_id: {
                            scp_type: set(uids)
                            for scp_type, uids in scp_types.items()
                        }
                        for user_id, scp_types in raw_audits.items()
                    }
            else:
                self.counters = {}
                self.user_audits = {}
                self._save_counters()
                
        except Exception as e:
            logging.error(f"加载计数器失败: {e}")
            self.counters = {}
            self.user_audits = {}

    def _save_counters(self):
        """保存计数器和审核记录"""
        counter_file = os.path.join(self.blacklist_dir, "audit_counters.json")
        try:
            # 将所有set转换为list再保存
            serializable_audits = {}
            for user_id, scp_types in self.user_audits.items():
                serializable_audits[user_id] = {
                    scp_type: list(uids) 
                    for scp_type, uids in scp_types.items()
                }
                
            data = {
                "counters": self.counters,
                "user_audits": serializable_audits
            }
            
            with open(counter_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存计数器失败: {e}")

    def increment(self, scp_type: str, uid: str, user_uid: str):
        """增加审核计数并记录用户审核"""
        try:
            uid = str(uid)
            user_key = str(user_uid)
            scp_key = f"SCP-{scp_type}"
            
            # 更新计数
            if scp_key not in self.counters:
                self.counters[scp_key] = {}
            if uid not in self.counters[scp_key]:
                self.counters[scp_key][uid] = 0
            self.counters[scp_key][uid] += 1
            
            # 记录用户审核
            if user_key not in self.user_audits:
                self.user_audits[user_key] = {}
            if scp_key not in self.user_audits[user_key]:
                self.user_audits[user_key][scp_key] = set()
            self.user_audits[user_key][scp_key].add(uid)
            
            self._save_counters()
            return True
        except Exception as e:
            logging.error(f"增加计数失败: {e}")
            return False
    
    def get_least_audited(self, scp_type: str, user_uid: str) -> str:
        """获取用户未审核过的、审核次数最少的UID"""
        user_key = str(user_uid)
        scp_key = f"SCP-{scp_type}"
        
        # 初始化用户的审核记录
        if user_key not in self.user_audits:
            self.user_audits[user_key] = {}
        if scp_key not in self.user_audits[user_key]:
            self.user_audits[user_key][scp_key] = set()
            
        # 获取文件中的所有UID
        filepath = os.path.join(self.blacklist_dir, f"SCP-{scp_type}.txt")
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, "r", encoding="utf-8") as f:
            all_uids = {line.strip() for line in f if line.strip()}
            
        # 获取用户未审核的UID
        unaudited_uids = all_uids - set(self.user_audits[user_key][scp_key])
        if not unaudited_uids:
            return None
            
        # 从未审核的UID中找出审核次数最少的
        counter = self.counters.get(scp_key, {})
        return min(unaudited_uids, key=lambda x: counter.get(x, 0))