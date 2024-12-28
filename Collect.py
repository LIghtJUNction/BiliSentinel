import requests

def extract_bilibili_data(uid, param_sum):
    """
    从 Bilibili API 获取指定用户信息，根据参数和返回对应字段。
    
    参数:
        uid: int - 用户 ID
        param_sum: int - 需要获取的字段和，按位表示字段选择。
        
    返回:
        list - 按 param_sum 指定的字段顺序返回对应数据。
    """
    # 数据字段与对应参数的映射
    param_mapping = {
        1: "name",
        2: "sex",
        4: "face",
        8: "sign",
        16: "level",
        32: "coins",
        64: "birthday",
        128: "school",
        256: "fans_badge",
        512: "live_room",
        1024: "vip",
    }

    # API URL
    api_url = f"https://api.bilibili.com/x/space/acc/info?mid={uid}"
    
    try:
        # 请求 API
        response = requests.get(api_url)
        response.raise_for_status()
        api_response = response.json()
        
        # 检查 API 返回状态
        if api_response.get("code") != 0:
            return {"错误": f"API 返回异常，code: {api_response.get('code')}"}

        # 获取用户数据
        data = api_response.get("data", {})
        
        # 提取需要的数据
        result = []
        for key, field in param_mapping.items():
            if param_sum & key:  # 检查对应位是否为1
                value = data.get(field, None)
                # 如果是嵌套字段（如 school 和 live_room），需要额外处理
                if isinstance(value, dict):
                    result.append(value.get("name", None) if field == "school" else value)
                else:
                    result.append(value)
        
        return result
    
    except requests.RequestException as e:
        return {"错误": f"网络请求失败: {e}"}
    except ValueError as e:
        return {"错误": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"错误": f"未知错误: {e}"}


if __name__ == "__main__":
    # 示例调用
    uid = 646503378
    param_sum = 3  # 1 (name) + 2 (sex)
    result = extract_bilibili_data(uid, param_sum)
    print(result)
