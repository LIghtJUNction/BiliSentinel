# 项目重构计划

## 1. 目录结构重组

```
bilibili_blacklist/
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── auth.py            # 认证相关
│   ├── blacklist.py       # 黑名单核心
│   ├── audit.py          # 审核系统
│   └── points.py         # 积分系统
├── data/                  # 数据存储
│   ├── __init__.py 
│   ├── storage/          # 存储实现
│   └── models/           # 数据模型
├── ui/                    # 界面相关
│   ├── __init__.py
│   ├── menu.py           # 菜单系统
│   ├── display.py        # 显示组件
│   └── themes/           # 主题定义
├── utils/                 # 工具类
│   ├── __init__.py
│   ├── decorators.py     # 装饰器
│   ├── exceptions.py     # 异常定义
│   └── helpers.py        # 辅助函数
├── managers/             # 业务管理
│   ├── __init__.py
│   ├── base.py          # 管理器基类
│   └── handlers/        # 具体处理器
├── config/              # 配置文件
│   ├── __init__.py
│   └── settings.py      # 全局配置
└── tests/              # 测试用例
    ├── __init__.py
    └── test_*.py      # 测试文件
```

## 2. 核心模块重构

### 2.1 认证模块 (core/auth.py)
```python
class AuthService:
    """认证服务
    处理登录认证和凭证管理
    """
    
    def __init__(self):
        self.storage = CredentialStorage()
        
    async def login(self):
        """处理登录流程"""
        pass
        
    def save_credential(self):
        """保存凭证"""
        pass
```

### 2.2 黑名单模块 (core/blacklist.py)
```python
class BlacklistService:
    """黑名单服务
    处理黑名单的核心业务逻辑
    """
    
    def __init__(self):
        self.storage = BlacklistStorage()
        self.counter = SCPCounter()
        
    async def process_blacklist(self):
        """处理黑名单"""
        pass
```

### 2.3 审核模块 (core/audit.py)
```python
class AuditService:
    """审核服务
    处理审核相关的核心逻辑
    """
    
    def __init__(self):
        self.history = AuditHistory()
        self.points = PointSystem()
        
    async def audit_user(self):
        """审核用户"""
        pass
```

## 3. 数据层重构

### 3.1 存储接口 (data/storage/base.py)
```python
class BaseStorage(ABC):
    """存储基类"""
    
    @abstractmethod
    async def save(self, data: Any) -> bool:
        """保存数据"""
        pass
        
    @abstractmethod
    async def load(self) -> Any:
        """加载数据"""
        pass
```

### 3.2 数据模型 (data/models)
```python
@dataclass
class UserInfo:
    """用户信息模型"""
    uid: str
    name: str
    level: int
    
@dataclass 
class AuditRecord:
    """审核记录模型"""
    uid: str
    action: str
    timestamp: float
```

## 4. UI层重构

### 4.1 菜单系统 (ui/menu.py)
```python
class MenuSystem:
    """菜单系统"""
    
    def __init__(self):
        self.current = None
        self.history = []
        
    def show(self):
        """显示菜单"""
        pass
        
    def handle_input(self):
        """处理输入"""
        pass
```

### 4.2 显示组件 (ui/display.py)
```python
class DisplayManager:
    """显示管理器"""
    
    def show_table(self):
        """显示表格"""
        pass
        
    def show_progress(self):
        """显示进度"""
        pass
```

## 5. 重构步骤

1. 基础设施
   - [x] 创建新的目录结构
   - [x] 设置基础类
   - [x] 配置系统

2. 核心功能
   - [ ] 认证模块
   - [ ] 黑名单模块
   - [ ] 审核模块
   - [ ] 积分模块

3. 数据层
   - [ ] 存储接口
   - [ ] 数据模型
   - [ ] 文件操作

4. UI层
   - [ ] 菜单系统
   - [ ] 显示组件
   - [ ] 主题支持

5. 测试
   - [ ] 单元测试
   - [ ] 集成测试
   - [ ] UI测试

## 6. 注意事项

1. 代码规范
   - 使用类型注解
   - 添加文档字符串
   - 遵循PEP 8

2. 错误处理
   - 统一异常体系
   - 完善错误提示
   - 添加日志记录

3. 性能优化
   - 使用异步操作
   - 添加缓存机制
   - 优化文件操作 