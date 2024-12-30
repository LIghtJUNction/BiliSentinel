B站黑名单管理系统
=================

模块说明
--------

AuthManager

~~~~~~~~~~
认证管理器，处理用户登录和凭证管理。

主要方法:
* ``authenticate()``: 处理登录认证流程

使用示例::

    from managers.auth_manager import AuthManager
  
    auth = AuthManager()
    credential, user_info = await auth.authenticate()

BlacklistManager
~~~~~~~~~~~~~~

黑名单管理器，处理用户拉黑和名单维护。

主要方法:

* ``get_user_details(uid)``: 获取用户详细信息
* ``mechanical_check(info)``: 机械规则检查
* ``process_blacklist_contribution()``: 处理黑名单贡献
* ``check_all()``: 审核模式
* ``blacklist_all(follower_count)``: 黑名单管理主菜单

使用示例::

from managers.blacklist_manager import BlacklistManager

manager = BlacklistManager(credential)
await manager.process_blacklist_contribution()
UserInfoManager

~~~~~~~~~~~~~
用户信息管理器，处理个人信息查询。

主要方法:
* ``show_info_submenu()``: 显示个人信息子菜单
* ``_get_info(info_type)``: 获取指定类型信息
* ``_format_info_table(info, title)``: 格式化信息表格

使用示例::

    from managers.user_info_manager import UserInfoManager
  
    manager = UserInfoManager(credential)
    await manager.show_info_submenu()

MenuHandlers
~~~~~~~~~~
菜单处理器，统一管理各个功能模块。

主要方法:
* ``handle_main_menu()``: 处理主菜单操作

使用示例::

    from managers.menu_handlers import MenuHandlers
  
    handlers = MenuHandlers(credential, follower_count)
    await handlers.handle_main_menu()

配置说明
--------

1. 凭证配置
~~~~~~~~~~~~
程序会自动管理凭证文件(credential.json)，首次使用需扫码登录。

2. 黑名单目录
~~~~~~~~~~~~
默认使用"blacklists"目录存储黑名单文件：
* SCP-0000.txt: 基础黑名单
* SCP-1989.txt: 机械判定黑名单
* SCP-3666.txt: 特殊黑名单

注意事项
--------
1. 请勿频繁操作以避免触发风控
2. 建议定期备份黑名单文件
3. 建议使用稳定的网络环境

常见问题
--------
Q: 提示"风控校验失败"
A: 等待几分钟后重试，避免频繁操作

Q: 凭证失效
A: 重新扫码登录即可

更新日志
--------
v1.0.0
* 初始版本发布
* 实现基础功能
~~~~~~~~~~~~~
