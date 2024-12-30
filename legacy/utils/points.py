import os
import json
from datetime import datetime
import logging

class PointSystem:
    def __init__(self):
        self.points_dir = "points_records"
        self.points_file = os.path.join(self.points_dir, "points.json")
        
        # 确保目录存在
        if not os.path.exists(self.points_dir):
            os.makedirs(self.points_dir)
            
        # 确保文件存在
        if not os.path.exists(self.points_file):
            self._save_data({"users": {}})

    def add_points(self, uid: str, points: int, reason: str):
        """添加积分记录"""
        data = self._load_data()
        
        # 初始化用户数据
        if uid not in data["users"]:
            data["users"][uid] = {
                "total_points": 0,
                "records": []
            }
        
        # 添加新记录
        data["users"][uid]["records"].append({
            "time": int(datetime.now().timestamp()),
            "points": points,
            "reason": reason
        })
        
        # 更新总积分
        data["users"][uid]["total_points"] += points
        
        # 保存数据
        self._save_data(data)

    def get_user_points(self, uid: str) -> int:
        """获取用户总积分"""
        data = self._load_data()
        return data.get("users", {}).get(uid, {}).get("total_points", 0)

    def view_records(self, uid: str) -> list:
        """查看用户的积分记录"""
        data = self._load_data()
        user_data = data.get("users", {}).get(uid, {})
        return user_data.get("records", [])

    def get_leaderboard(self) -> list:
        """获取积分排行榜"""
        data = self._load_data()
        users = data.get("users", {})
        
        # 构建排行榜数据
        leaderboard = [
            {
                "uid": uid,
                "points": user_data["total_points"]
            }
            for uid, user_data in users.items()
        ]
        
        # 按积分降序排序
        leaderboard.sort(key=lambda x: x["points"], reverse=True)
        return leaderboard

    def _load_data(self) -> dict:
        """加载积分数据"""
        try:
            if os.path.exists(self.points_file):
                with open(self.points_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"users": {}}
        except Exception as e:
            logging.error(f"加载积分数据失败: {e}")
            return {"users": {}}

    def _save_data(self, data: dict):
        """保存积分数据"""
        try:
            with open(self.points_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存积分数据失败: {e}")