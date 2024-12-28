import requests

def get_user_info(uid, option):
    # 定义Bilibili用户信息API的基础URL
    api_url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
    stat_url = f"https://api.bilibili.com/x/relation/stat?vmid={uid}"
    
    try:
        # 获取用户基本信息
        info_response = requests.get(api_url)
        info_data = info_response.json()
        
        # 获取用户的关注和粉丝信息
        stat_response = requests.get(stat_url)
        stat_data = stat_response.json()
        
        if info_data["code"] != 0 or stat_data["code"] != 0:
            return "无法获取用户信息，可能UID不存在。"

        # 解析数据
        username = info_data["data"].get("name")
        level = info_data["data"].get("level")
        following = stat_data["data"].get("following")
        follower = stat_data["data"].get("follower")
        likes_url = f"https://api.bilibili.com/x/space/upstat?mid={uid}"
        likes_response = requests.get(likes_url)
        likes_data = likes_response.json()
        likes = likes_data["data"].get("likes") if likes_data["code"] == 0 else None

        # 根据选项构建结果
        result = {}
        if option & 1:  # 获取用户名
            result["用户名"] = username
        if option & 2:  # 获取用户等级
            result["等级"] = level
        if option & 4:  # 获取用户关注数
            result["关注数"] = following
        if option & 8:  # 获取用户粉丝数
            result["粉丝数"] = follower
        if option & 16:  # 获取用户获得赞数
            result["赞数"] = likes

        return result

    except Exception as e:
        return f"发生错误: {e}"
if __name__ == '__main__':
    # 示例调用
    uid = 646503378
    option = 1 + 2  # 获取用户名和等级
    print(get_user_info(uid, option))
