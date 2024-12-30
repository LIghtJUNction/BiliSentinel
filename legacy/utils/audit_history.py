import json
import logging
import os
import hashlib
import hmac
from datetime import datetime
from .constants import AUDIT_RECORDS_DIR, PBKDF2_ITERATIONS

class AuditHistory:
    VERSION = 1

    def __init__(self, credential, uid):
        self.credential = credential
        self.uid = uid
        self.history_dir = AUDIT_RECORDS_DIR
        self.history = {}
        self._ensure_dirs()
        self._load_history()

    def _ensure_dirs(self):
        """确保必要的目录存在"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

    def _calculate_signature(self, data: dict) -> str:
        """计算记录的签名
        使用公开的项目密钥，任何人都可以验证，但不能伪造
        """
        # 项目公共密钥，可以放在代码中
        PROJECT_KEY = b"bilibili_blacklist_v1"
        
        # 计算签名
        message = json.dumps(data, sort_keys=True).encode()
        return hmac.new(PROJECT_KEY, message, hashlib.sha256).hexdigest()

    def _verify_signature(self, data: dict, signature: str) -> bool:
        """验证记录签名"""
        expected = self._calculate_signature(data)
        return hmac.compare_digest(signature, expected)

    def get_history_file(self) -> str:
        """获取历史记录文件路径"""
        return os.path.join(self.history_dir, f"{self.uid}.audit")

    def record_audit(self, scp_type: str, target_uid: str, action: str):
        """记录审核操作"""
        if scp_type not in self.history:
            self.history[scp_type] = {}

        record = {
            "action": action,
            "time": datetime.now().timestamp(),
            "uid": self.uid,  # 记录审核者ID
            "version": self.VERSION
        }

        # 计算签名
        record["signature"] = self._calculate_signature(record)
        
        self.history[scp_type][target_uid] = record
        self._save_history()

    def has_audited(self, user_uid: str, scp_type: str, target_uid: str) -> bool:
        """检查是否已审核过"""
        scp_key = f"SCP-{scp_type}"
        if target_uid not in self.history.get(scp_key, {}):
            return False
            
        # 验证记录完整性
        record = self.history[scp_key][target_uid]
        if not self._verify_signature(record, record.get("signature", "")):
            logging.warning(f"发现被篡改的审核记录: {scp_type}/{target_uid}")
            return False
            
        return True

    def _load_history(self):
        """加载审核历史"""
        try:
            history_file = self.get_history_file()
            if not os.path.exists(history_file):
                return

            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 验证所有记录
            valid_records = {}
            for scp_type, records in data.items():
                valid_records[scp_type] = {}
                for uid, record in records.items():
                    if self._verify_signature(record, record.get("signature", "")):
                        valid_records[scp_type][uid] = record
                    else:
                        logging.warning(f"忽略被篡改的记录: {scp_type}/{uid}")
                        
            self.history = valid_records
                
        except Exception as e:
            logging.error(f"加载审核历史失败: {e}")
            self.history = {}

    def _save_history(self):
        """保存审核历史"""
        try:
            history_file = self.get_history_file()
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logging.error(f"保存审核历史失败: {e}")

    def get_audited_uids(self, scp_type: str) -> set:
        """获取已审核过的UID集合
        
        Args:
            scp_type: SCP类型 (0000/1989/3666)
            
        Returns:
            set: 已审核的UID集合
        """
        scp_key = f"SCP-{scp_type}"
        if scp_key not in self.history:
            return set()
            
        # 返回经过验证的记录的UID集合
        valid_uids = set()
        for uid, record in self.history[scp_key].items():
            if self._verify_signature(record, record.get("signature", "")):
                valid_uids.add(uid)
            else:
                logging.warning(f"忽略被篡改的记录: {scp_type}/{uid}")
                
        return valid_uids

    def add_record(self, scp_type: str, target_uid: str, keep: bool):
        """添加审核记录
        
        Args:
            scp_type: SCP类型 (0000/1989/3666)
            target_uid: 目标用户UID
            keep: True表示保留，False表示移除
        """
        action = "KEEP" if keep else "REMOVE"
        self.record_audit(scp_type, target_uid, action)
