import json
import os
from collections import defaultdict
from typing import Dict

class SCPCounter:
    def __init__(self, blacklist_dir: str):
        self.blacklist_dir = blacklist_dir
        self.counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._load_counters()
    
    def _load_counters(self):
        """加载计数器"""
        counter_file = os.path.join(self.blacklist_dir, "counters.json")
        if os.path.exists(counter_file):
            with open(counter_file, "r", encoding="utf-8") as f:
                self.counters = defaultdict(lambda: defaultdict(int), json.load(f))
    
    def _save_counters(self):
        """保存计数器"""
        counter_file = os.path.join(self.blacklist_dir, "counters.json")
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump(self.counters, f, indent=2)
    
    def increment(self, scp_type: str, uid: str):
        """增加计数"""
        self.counters[f"SCP-{scp_type}"][uid] += 1
        self._save_counters()
        self._reorder_file(scp_type)
    
    def remove(self, scp_type: str, uid: str):
        """移除计数"""
        if uid in self.counters[f"SCP-{scp_type}"]:
            del self.counters[f"SCP-{scp_type}"][uid]
            self._save_counters()
            self._reorder_file(scp_type)
    
    def _reorder_file(self, scp_type: str):
        """重新排序文件内容"""
        filepath = os.path.join(self.blacklist_dir, f"SCP-{scp_type}.txt")
        if not os.path.exists(filepath):
            return
            
        # 读取所有UID
        uids = set()
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                uid = line.strip()
                if uid:
                    uids.add(uid)
        
        # 按计数排序
        counter = self.counters[f"SCP-{scp_type}"]
        sorted_uids = sorted(
            uids,
            key=lambda x: (-counter.get(x, 0), x)  # 计数降序，UID升序
        )
        
        # 重写文件
        with open(filepath, "w", encoding="utf-8") as f:
            for uid in sorted_uids:
                f.write(f"{uid}\n")