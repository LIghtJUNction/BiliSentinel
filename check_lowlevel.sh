#!/bin/bash

# 输入的 UID 区间
start_uid=$1
end_uid=$2

# Lowlevel名单文件
lowlevel_file="Lowlevel.txt"

# 检查 Lowlevel.txt 是否存在，不存在则创建并设置可写权限
if [ ! -f "$lowlevel_file" ]; then
    touch "$lowlevel_file"
    chmod 666 "$lowlevel_file"  # 设置文件为可写
fi

# 遍历 UID 区间
for ((uid=$start_uid; uid<$end_uid; uid++))
do
    # 提取用户数据
    user_data=$(python3 -c "
import sys
from Collect import extract_bilibili_data
uid = $uid
user_info = extract_bilibili_data(uid, 24)
if user_info:
    print(user_info)
else:
    print('None')
")

    # 检查提取的数据是否为空
    if [[ "$user_data" != "None" ]]; then
        # 解析出用户的等级和简介
        level=$(echo $user_data | cut -d',' -f1 | tr -d '[] "')
        sign=$(echo $user_data | cut -d',' -f4 | tr -d '[] "')

        # 如果等级 <= 1 且简介为空，则写入 Lowlevel.txt 文件
        if [ "$level" -le 1 ] && [ -z "$sign" ]; then
            echo "UID: $uid" >> $lowlevel_file
        fi
    fi
done

echo "处理完成，符合条件的 UID 已写入 $lowlevel_file 文件"
