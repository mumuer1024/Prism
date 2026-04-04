# P3 阶段开发计划

> 创建时间：2026-04-04
> 开发阶段：P3（在线支付前置开发）
> 状态：✅ 已完成

---

## 📋 开发概览

| 任务 | 预估工时 | 状态 |
|:--|:--|:--|
| 支付订单数据库表 | 0.25 天 | ⏳ 待开始 |
| 支付服务抽象层 | 0.5 天 | ⏳ 待开始 |
| 支付 API 路由 | 0.5 天 | ⏳ 待开始 |
| 前端支付页面框架 | 0.25 天 | ⏳ 待开始 |
| 测试编写 | 0.25 天 | ⏳ 待开始 |

**总预估工时：1.75 天**

---

## 🎯 功能目标

### 开发定位

P3 阶段为**在线支付前置开发**，重点是预留接口框架，不直接上线。

### 核心目标

1. **数据库预留**：创建支付订单表，支持订单生命周期管理
2. **接口预留**：定义支付服务抽象接口，为微信/支付宝接入预留扩展点
3. **API 框架**：创建支付相关 API 端点，返回模拟数据
4. **前端占位**：创建支付页面框架，展示套餐选项

### 不包含

- 实际接入微信/支付宝 SDK
- 真实的支付回调处理
- 生产环境配置

---

## 🔧 技术方案

### 1. 数据库设计

#### 支付订单表 (payment_orders)

```sql
CREATE TABLE payment_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_no TEXT UNIQUE NOT NULL,        -- 订单号 (PRISM-YYYYMMDD-XXXXXX)
    amount INTEGER NOT NULL,              -- 金额（分）
    usage_count INTEGER NOT NULL,         -- 购买次数
    payment_method TEXT NOT NULL,         -- wechat / alipay
    status TEXT DEFAULT 'pending',        -- pending / paid / failed / cancelled / refunded

    -- 支付信息
    trade_no TEXT,                        -- 第三方交易号
    qr_code_url TEXT,                     -- 支付二维码链接
    paid_at DATETIME,                     -- 支付时间

    -- 回调信息
    callback_raw TEXT,                    -- 原始回调数据 (JSON)
    callback_at DATETIME,                 -- 回调时间

    -- 时间戳
    expires_at DATETIME,                  -- 订单过期时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_payment_orders_user ON payment_orders(user_id);
CREATE INDEX idx_payment_orders_status ON payment_orders(status);
CREATE INDEX idx_payment_orders_order_no ON payment_orders(order_no);
```

#### 套餐配置表 (payment_packages)

```sql
CREATE TABLE payment_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                   -- 套餐名称
    usage_count INTEGER NOT NULL,         -- 次数
    price INTEGER NOT NULL,               -- 价格（分）
    bonus_count INTEGER DEFAULT 0,        -- 赠送次数
    is_active BOOLEAN DEFAULT TRUE,       -- 是否上架
    sort_order INTEGER DEFAULT 0,         -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 支付服务抽象层

#### 目录结构

```
src/payment/
├── __init__.py
├── router.py           # API 路由
├── service.py          # 支付服务（订单管理）
├── schemas.py          # Pydantic 模型
├── base.py             # 支付渠道抽象基类
├── wechat.py           # 微信支付（预留接口）
├── alipay.py           # 支付宝支付（预留接口）
└── mock.py             # 模拟支付（开发测试用）
```

#### 支付渠道抽象基类

```python
# src/payment/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class PaymentResult:
    """支付结果"""
    success: bool
    order_no: str
    trade_no: Optional[str] = None
    qr_code_url: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class CallbackResult:
    """回调结果"""
    success: bool
    order_no: str
    trade_no: Optional[str] = None
    paid_at: Optional[datetime] = None
    raw_data: Optional[str] = None

class PaymentChannel(ABC):
    """支付渠道抽象基类"""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """渠道名称"""
        pass

    @abstractmethod
    async def create_payment(
        self,
        order_no: str,
        amount: int,
        description: str,
    ) -> PaymentResult:
        """
        创建支付订单

        Args:
            order_no: 商户订单号
            amount: 金额（分）
            description: 商品描述

        Returns:
            PaymentResult: 支付结果（包含二维码等）
        """
        pass

    @abstractmethod
    async def query_payment(self, order_no: str) -> PaymentResult:
        """
        查询支付状态

        Args:
            order_no: 商户订单号

        Returns:
            PaymentResult: 支付状态
        """
        pass

    @abstractmethod
    async def handle_callback(self, data: dict) -> CallbackResult:
        """
        处理支付回调

        Args:
            data: 回调数据

        Returns:
            CallbackResult: 回调处理结果
        """
        pass

    @abstractmethod
    async def close_payment(self, order_no: str) -> bool:
        """
        关闭支付订单

        Args:
            order_no: 商户订单号

        Returns:
            bool: 是否成功
        """
        pass
```

#### 模拟支付实现

```python
# src/payment/mock.py

class MockPaymentChannel(PaymentChannel):
    """模拟支付渠道（开发测试用）"""

    @property
    def channel_name(self) -> str:
        return "mock"

    async def create_payment(self, order_no: str, amount: int, description: str) -> PaymentResult:
        # 返回模拟的二维码链接
        return PaymentResult(
            success=True,
            order_no=order_no,
            qr_code_url=f"mock://pay/{order_no}",
        )

    async def query_payment(self, order_no: str) -> PaymentResult:
        # 返回模拟状态
        return PaymentResult(
            success=True,
            order_no=order_no,
        )

    async def handle_callback(self, data: dict) -> CallbackResult:
        # 模拟回调处理
        return CallbackResult(
            success=True,
            order_no=data.get("order_no", ""),
        )

    async def close_payment(self, order_no: str) -> bool:
        return True
```

### 3. API 端点设计

| 端点 | 方法 | 说明 | 状态 |
|:--|:--|:--|:--|
| `/api/payment/packages` | GET | 获取套餐列表 | 公开 |
| `/api/payment/create` | POST | 创建支付订单 | 需登录 |
| `/api/payment/{order_no}` | GET | 查询订单状态 | 需登录 |
| `/api/payment/orders` | GET | 获取用户订单列表 | 需登录 |
| `/api/payment/wechat/callback` | POST | 微信支付回调 | 内部 |
| `/api/payment/alipay/callback` | POST | 支付宝回调 | 内部 |
| `/api/payment/mock/pay` | POST | 模拟支付（开发用） | 需登录 |

### 4. 前端页面框架

#### 支付页面结构

```
ui/payment.html          # 支付页面
ui/static/payment.js     # 支付交互逻辑
```

#### 页面功能

- 套餐选择卡片
- 支付方式选择（微信/支付宝）
- 订单状态轮询
- 支付结果展示

---

## 📁 文件变更清单

| 文件 | 变更类型 | 说明 |
|:--|:--|:--|
| `src/database/models.py` | 修改 | 新增 PaymentOrder, PaymentPackage 模型 |
| `src/payment/__init__.py` | 新建 | 模块初始化 |
| `src/payment/base.py` | 新建 | 支付渠道抽象基类 |
| `src/payment/mock.py` | 新建 | 模拟支付实现 |
| `src/payment/wechat.py` | 新建 | 微信支付预留接口 |
| `src/payment/alipay.py` | 新建 | 支付宝预留接口 |
| `src/payment/schemas.py` | 新建 | Pydantic 模型 |
| `src/payment/service.py` | 新建 | 订单管理服务 |
| `src/payment/router.py` | 新建 | API 路由 |
| `server.py` | 修改 | 注册支付路由 |
| `ui/payment.html` | 新建 | 支付页面 |
| `ui/static/payment.js` | 新建 | 支付交互逻辑 |
| `ui/static/style.css` | 修改 | 支付页面样式 |
| `tests/test_payment.py` | 新建 | 支付模块测试 |

---

## 🧪 测试用例

### 后端测试

| 测试类 | 测试内容 |
|:--|:--|
| TestPaymentPackages | 套餐列表查询 |
| TestPaymentOrderCreate | 订单创建 |
| TestPaymentOrderQuery | 订单查询 |
| TestPaymentOrderList | 用户订单列表 |
| TestMockPayment | 模拟支付流程 |
| TestPaymentChannel | 支付渠道接口 |

---

## 📊 预期成果

| 成果 | 说明 |
|:--|:--|:--|
| 数据库表 | 支付订单表、套餐配置表 |
| 抽象接口 | 支付渠道基类，支持扩展 |
| API 端点 | 7 个支付相关端点 |
| 模拟支付 | 开发测试用的模拟支付渠道 |
| 前端页面 | 支付页面框架 |

---

## ⚠️ 注意事项

1. **安全性**：回调接口需要验签（预留接口）
2. **幂等性**：订单创建和回调处理需要幂等
3. **过期处理**：订单需要设置过期时间
4. **状态机**：订单状态变更需要严格校验

---

## ✅ 审核确认

请审核人员确认以下内容：

- [ ] 开发范围合理
- [ ] 接口设计完整
- [ ] 预留扩展点充足

**审核人**：________________
**审核日期**：________________