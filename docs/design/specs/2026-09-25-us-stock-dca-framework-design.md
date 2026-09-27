# 美股定投框架设计文档

## 1. 项目概述

### 1.1 项目目标

开发一个基于 Binance 美股交易 API 的自动定投框架，支持多账户、多策略、自动执行和灵活通知。

### 1.2 核心功能

- 支持多个账户，使用 API key/secret key 操作 Binance 美股交易
- 支持三种定投策略：DCA、Drawdown、价值平均
- 支持买入和卖出操作（策略自动触发 + 手动干预）
- 一个账户可对同一标的或不同标的配置多个策略实例
- 完整的日志系统（本地文件日志）
- 企业微信通知（即时通知 + 定时汇总）
- SQLite 本地数据库记录所有操作
- 配置文件管理，敏感信息与业务配置分离

### 1.3 技术栈

- 语言：Python 3.9+
- 调度器：APScheduler
- 数据库：SQLite
- 行情数据：yFinance（历史日行情）+ Binance API（实时价格）
- 通知：企业微信 Webhook
- 部署：常驻进程，通过 PM2 管理

## 2. 架构设计

### 2.1 总体架构

采用分层模块架构：

```
├── core/                    # 核心业务层
│   ├── scheduler.py         # 调度器
│   ├── strategy_engine.py   # 策略引擎
│   ├── trade_executor.py    # 交易执行器
│   └── account_manager.py   # 账户管理器
├── strategies/              # 策略实现层
│   ├── base.py             # 策略基类
│   ├── dca.py              # DCA策略
│   ├── drawdown.py         # Drawdown策略
│   └── value_averaging.py  # 价值平均策略
├── integrations/           # 外部集成层
│   ├── binance_client.py   # Binance API客户端
│   ├── yfinance_client.py  # yFinance数据获取
│   └── wecom_notifier.py   # 企业微信通知
├── storage/                # 数据持久化层
│   ├── database.py         # SQLite操作
│   └── models.py           # 数据模型
├── config/                 # 配置管理层
│   ├── loader.py           # 配置加载器
│   └── validator.py        # 配置验证
├── utils/                  # 工具层
│   ├── logger.py           # 日志配置
│   ├── retry.py            # 重试机制
│   └── date_utils.py       # 日期工具
└── main.py                 # 程序入口
```

### 2.2 核心模块职责

**Scheduler（调度器）**
- 管理所有策略实例的执行时间
- 基于 APScheduler 实现智能调度（Cron 和 Interval 触发）
- 定期扫描手动交易配置文件
- 触发定时汇总通知
- 触发账户快照任务

**Strategy Engine（策略引擎）**
- 接收调度器的触发请求
- 同步 Binance 实际持仓（避免数据不一致）
- 获取市场数据（通过 MarketDataService，带缓存）
- 实例化策略类并执行计算
- 检查通用卖出规则（仅 DCA 和 Drawdown）
- 将交易信号传递给 TradeExecutor
- 记录策略执行记录到数据库（包含配置快照）

**Trade Executor（交易执行器）**
- 执行前检查账户余额（可配置：部分执行/全部跳过）
- 调用 Binance API 执行交易
- 实现重试机制（指数退避）
- 交易成功：记录到数据库，发送即时通知，更新持仓
- 交易失败：达上限后记录并发送告警通知
- 错误隔离：不影响其他策略执行

**Account Manager（账户管理器）**
- 加载所有账户配置（业务配置 + 敏感信息）
- 提供账户信息查询接口
- 定期更新账户快照到数据库
- 为汇总通知提供账户数据

### 2.3 数据流

```
定时策略执行流程：
Scheduler（触发） 
  → Strategy Engine（同步持仓 → 获取数据 → 执行策略 → 检查卖出规则）
  → Trade Executor（检查余额 → 执行交易 → 重试 → 记录）
  → WeComNotifier（即时通知）
  → Database（记录执行和交易）

手动交易流程：
Scheduler（扫描配置文件）
  → Trade Executor（执行交易）
  → 归档配置文件
  → WeComNotifier（通知）
  → Database（记录）
```

## 3. 策略设计

### 3.1 策略基类

```python
class BaseStrategy(ABC):
    @abstractmethod
    def calculate(self, account_config, strategy_config, market_data, position) -> TradeSignal:
        """
        计算交易信号
        
        参数:
            account_config: 账户配置
            strategy_config: 策略实例配置
            market_data: 市场数据（历史行情 + 实时价格）
            position: 当前持仓（从 Binance API 同步）
        
        返回:
            TradeSignal: 交易信号
                - action: BUY / SELL / HOLD
                - amount: 金额或数量
                - reason: 触发原因
        """
        pass
    
    @abstractmethod
    def get_required_data(self, strategy_config) -> DataRequirement:
        """
        声明策略所需的数据
        
        返回:
            DataRequirement: 数据需求（历史数据天数等）
        """
        pass
```

### 3.2 DCA 策略（固定金额定投）

**逻辑：**
- 在配置的时间点（如每月第1个交易日）买入固定金额
- 不考虑市场波动

**配置示例：**
```yaml
type: DCA
symbol: TQQQ
config:
  base_amount: 100  # 每次投入100 USDT
  frequency: monthly
  day_of_month: 1  # 每月1号（第1个交易日）
  sell_rules:  # 可选
    - type: profit_percentage
      threshold: 30
      sell_type: position_percentage
      sell_amount: 50
```

**数据需求：**
- 仅需实时价格（用于计算可买数量）

### 3.3 Drawdown 策略（回撤加仓）

**逻辑：**
- 计算当前价格相对于回看期内最高价的回撤幅度
- 根据回撤幅度调整定投金额：`实际投入 = 基础金额 × (1 + 回撤百分比)`
- 例如：基础100 USDT，回撤10%，则投入110 USDT

**配置示例：**
```yaml
type: Drawdown
symbol: TQQQ
config:
  base_amount: 100
  lookback_days: 250  # 回看250个交易日
  frequency: weekly
  day_of_week: 1  # 每周一
  sell_rules:  # 可选
    - type: profit_percentage
      threshold: 50
      sell_type: position_percentage
      sell_amount: 30
```

**数据需求：**
- N 天历史数据 + 实时价格

### 3.4 价值平均策略（纯粹版）

**逻辑：**
- 设定目标价值增长路径（如每月总市值增长1000 USDT）
- 每次执行：
  - 当前持仓市值 < 目标价值 → 买入补足差额
  - 当前持仓市值 > 目标价值 → 卖出超出部分
  - 当前持仓市值 = 目标价值 → 不操作

**配置示例：**
```yaml
type: ValueAveraging
symbol: SPY
config:
  target_growth_per_period: 1000  # 每期目标增长1000 USDT
  frequency: monthly
  start_date: "2026-01-01"  # 策略起始日期
  # 不支持额外的 sell_rules（卖出是核心逻辑）
```

**数据需求：**
- 历史数据（判断趋势）+ 实时价格 + 持仓数据

**重要：** 价值平均策略的卖出是其核心逻辑的一部分，不支持配置额外的通用卖出规则。

### 3.5 通用卖出规则

DCA 和 Drawdown 策略可以配置通用卖出规则，在策略自身逻辑之后检查。

**卖出规则类型：**

```yaml
sell_rules:
  - type: profit_percentage  # 盈利百分比触发
    threshold: 30  # 盈利30%
    sell_type: position_percentage  # 卖出类型
    sell_amount: 50  # 卖出50%
```

**sell_type 说明：**
- `position_percentage`：持仓数量的百分比
- `position_value`：持仓市值的金额
- `profit_value`：盈利部分的金额

**执行优先级：**
1. 先检查卖出规则是否触发
2. 如果触发，返回 SELL 信号
3. 如果未触发，执行策略的买入逻辑

## 4. 数据设计

### 4.1 配置文件设计

**设计原则：**
- 配置文件是唯一的配置源
- 敏感信息（API key）与业务配置分离
- 数据库只存储执行记录，不存储配置

**配置文件结构：**

```
configs/
├── system.yaml              # 系统配置
├── accounts/                # 账户配置目录
│   ├── alice.yaml
│   └── bob.yaml
└── manual_trades/           # 手动交易指令目录
    ├── 20260925_120000_alice_tqqq.yaml
    └── archive/             # 已执行归档

secrets/                     # 敏感信息目录（不进git）
├── alice.key
└── bob.key
```

**system.yaml：**
```yaml
system:
  timezone: "America/New_York"
  log_level: "INFO"

scheduler:
  check_interval: 60
  manual_trade_scan_interval: 60

database:
  path: "data/trading.db"

cache:
  realtime_price_ttl: 60
  history_data_clear_time: "16:30"

retry:
  api_call:
    max_attempts: 3
    interval_seconds: 5
    backoff: exponential
  data_fetch:
    max_attempts: 5
    interval_seconds: 10
    backoff: fixed
  trade_execution:
    max_attempts: 3
    interval_seconds: 10
    backoff: fixed

notifications:
  admin_webhook: "https://qyapi.weixin.qq.com/admin_webhook"
  summaries:
    daily:
      enabled: true
      time: "16:30"
      timezone: "America/New_York"
    weekly:
      enabled: true
      day_of_week: 0
      time: "09:00"
    monthly:
      enabled: false

snapshots:
  after_trade: true
  daily_close:
    enabled: true
    time: "16:30"
    timezone: "America/New_York"

balance_check:
  insufficient_action: "partial"  # partial / skip
```

**accounts/alice.yaml：**
```yaml
account:
  name: alice
  wecom_webhook: "https://qyapi.weixin.qq.com/alice_webhook"

strategies:
  - id: alice_tqqq_dca
    type: DCA
    symbol: TQQQ
    config:
      base_amount: 100
      frequency: monthly
      day_of_month: 1
      sell_rules:
        - type: profit_percentage
          threshold: 30
          sell_type: position_percentage
          sell_amount: 50
    status: active
  
  - id: alice_spy_drawdown
    type: Drawdown
    symbol: SPY
    config:
      base_amount: 200
      lookback_days: 250
      frequency: weekly
      day_of_week: 1
    status: active
```

**secrets/alice.key：**
```yaml
binance:
  api_key: "your_api_key_here"
  secret_key: "your_secret_key_here"
```

**manual_trades/20260925_120000_alice_tqqq.yaml：**
```yaml
trade:
  account: alice
  symbol: TQQQ
  action: SELL
  amount: 1000  # 金额（买入）或数量（卖出）
  reason: "市场贪婪，减仓"
  created_at: "2026-09-25T12:00:00"
```

### 4.2 数据库设计

**设计原则：**
- 只存储运行时产生的数据（交易、执行记录、快照）
- 不存储配置信息
- 所有时间字段使用 UTC 存储
- 通过 strategy_id 关联配置文件中的策略实例

**表 1: trades（交易记录）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| account_name | TEXT | 账户名称 |
| strategy_id | TEXT | 策略实例ID（可为空，手动交易时） |
| symbol | TEXT | 标的代码 |
| action | TEXT | BUY / SELL |
| quantity | REAL | 数量 |
| price | REAL | 成交价 |
| amount | REAL | 总金额 |
| fee | REAL | 手续费 |
| trigger_reason | TEXT | 触发原因：strategy_auto / manual / sell_rule |
| executed_at | TEXT | 执行时间（UTC） |
| created_at | TEXT | 创建时间（UTC） |

**表 2: strategy_executions（策略执行记录）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| strategy_id | TEXT | 策略实例ID |
| account_name | TEXT | 账户名称 |
| executed_at | TEXT | 执行时间（UTC） |
| market_data_snapshot | TEXT | 市场数据快照（JSON） |
| calculation_result | TEXT | 计算结果（JSON，包含配置快照） |
| signal | TEXT | BUY / SELL / HOLD |
| signal_amount | REAL | 信号金额/数量 |
| trade_id | INTEGER | 关联的交易ID（可为空） |
| status | TEXT | success / failed / skipped |
| error_message | TEXT | 错误信息 |
| created_at | TEXT | 创建时间（UTC） |

**calculation_result JSON 结构：**
```json
{
  "config_snapshot": {
    "strategy_type": "DCA",
    "base_amount": 100,
    "frequency": "monthly",
    "day_of_month": 1
  },
  "market_data": {
    "current_price": 45.32,
    "highest_price_250d": 52.10,
    "drawdown_percentage": 13.02
  },
  "calculation": {
    "target_amount": 113.02,
    "available_balance": 5000,
    "calculated_quantity": 2.49
  },
  "sell_rule_check": {
    "triggered": false,
    "rule": null
  }
}
```

**表 3: positions（持仓）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| account_name | TEXT | 账户名称 |
| symbol | TEXT | 标的代码 |
| quantity | REAL | 持仓数量 |
| avg_cost | REAL | 平均成本 |
| last_updated_at | TEXT | 最后更新时间（UTC） |
| created_at | TEXT | 创建时间（UTC） |

**唯一约束：** (account_name, symbol)

**表 4: account_snapshots（账户快照）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| account_name | TEXT | 账户名称 |
| total_balance | REAL | 总余额 |
| positions_snapshot | TEXT | 持仓详情（JSON） |
| snapshot_type | TEXT | after_trade / daily_close / weekly_summary / monthly_summary |
| snapshot_at | TEXT | 快照时间（UTC） |
| created_at | TEXT | 创建时间（UTC） |

**表 5: notifications（通知记录）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| notification_type | TEXT | trade / daily_summary / weekly_summary / alert |
| recipient | TEXT | 接收人标识 |
| content_summary | TEXT | 通知内容摘要 |
| status | TEXT | sent / failed |
| sent_at | TEXT | 发送时间（UTC） |
| error_message | TEXT | 错误信息 |
| created_at | TEXT | 创建时间（UTC） |

## 5. 市场数据管理

### 5.1 数据源

- **历史日行情**：yFinance（考虑除权除息调整）
- **实时价格**：Binance API（用于下单和实时报价）

### 5.2 缓存策略

**历史行情数据缓存：**
```python
缓存 key: f"{symbol}_{days}_{trading_day}"
缓存位置: 内存（dict）

更新机制:
- 缓存有效期：当天交易时间内有效
- 失效条件：日期变更（美国东部时间新的交易日）
- 清理机制：每天美国收盘后清空前一日缓存
```

**实时价格缓存：**
```python
缓存 key: f"{symbol}_realtime"
缓存位置: 内存

更新机制:
- 缓存有效期：1分钟（TTL）
- 超过1分钟自动失效，下次请求重新获取
```

### 5.3 MarketDataService

```python
class MarketDataService:
    def __init__(self, yfinance_client, binance_client):
        self.history_cache = {}
        self.realtime_cache = {}
        self.current_trading_day = None
    
    def get_market_data(self, symbol, days_required) -> MarketData:
        """
        获取市场数据
        - 检查缓存，命中则返回
        - 缓存未命中，从 yFinance 拉取并缓存
        - 日期变更时自动清空历史缓存
        """
        
    def get_realtime_price(self, symbol) -> float:
        """
        获取实时价格
        - 1分钟TTL缓存
        - 从 Binance API 获取
        """
```

## 6. 外部集成

### 6.1 Binance 客户端

```python
class BinanceClient:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=1200,
            max_requests_per_second=20
        )
    
    def get_realtime_price(self, symbol) -> float:
        """获取实时价格"""
    
    def get_account_balance(self) -> dict:
        """获取账户余额"""
    
    def get_position(self, symbol) -> dict:
        """获取持仓信息（数量、成本）"""
    
    def place_order(self, symbol, side, quantity) -> dict:
        """
        下单（市价单）
        side: BUY / SELL
        返回：订单信息（订单号、成交价、手续费等）
        """
    
    def _call_api(self, endpoint, params):
        """
        API调用封装
        - 限流检测和等待
        - 处理429（限流）响应
        - 解析 Retry-After 头
        """
```

**API 限流处理：**
- 维护请求计数器（滑动窗口）
- 接近阈值时自动延迟
- 收到429时解析Retry-After并等待
- 持续限流时发送告警

### 6.2 yFinance 客户端

```python
class YFinanceClient:
    def get_history_data(self, symbol, days) -> pd.DataFrame:
        """
        获取历史日行情数据
        返回：包含 Date, Open, High, Low, Close, Adj Close, Volume
        使用 Adj Close（考虑除权除息）
        """
    
    def is_trading_day(self, date) -> bool:
        """
        判断是否为美股交易日
        使用 pandas_market_calendars 库
        """
```

### 6.3 企业微信通知

```python
class WeComNotifier:
    def send_trade_notification(self, webhook_url, trade_info):
        """
        发送交易通知
        内容：策略名称、标的、数量、价格、金额、余额变化
        """
    
    def send_alert_notification(self, webhook_url, alert_info):
        """
        发送告警通知
        内容：错误类型、失败原因、重试次数
        """
    
    def send_summary_notification(self, webhook_url, summary_info):
        """
        发送汇总通知
        内容：时间范围、交易汇总、持仓情况、盈亏统计
        """
```

**通知内容示例：**

**交易通知：**
```
【交易通知 - alice】
策略：alice_tqqq_dca (DCA)
标的：TQQQ
操作：买入
数量：2.5股
价格：$45.20
金额：$113.00
手续费：$0.50
账户余额：$8,500.00 → $8,386.50
时间：2026-09-25 09:30:15
```

**账户汇总（每日）：**
```
【每日汇总 - alice】
时间范围：2026-09-24

📊 交易情况：
• TQQQ DCA策略：买入 2.5股，$112.50
• SPY Drawdown策略：买入 1.2股，$240.00

💰 账户状态：
• 总余额：$8,500.00
• 持仓市值：$6,200.00
• 可用余额：$2,300.00

📈 持仓情况：
• TQQQ：15.3股，成本$42.50，现价$45.20，盈亏+6.35%
• SPY：8.5股，成本$480.00，现价$490.00，盈亏+2.08%

✅ 今日盈亏：+$125.50 (+2.02%)
```

**系统汇总（管理员）：**
```
【系统每日汇总】
时间范围：2026-09-24

📊 执行统计：
• 策略执行：12次
• 成功交易：10笔
• 跳过执行：2次
• 失败：0次

💰 全局数据：
• 总交易金额：$2,450.00
• 活跃账户：3个
• 活跃策略：8个

⚠️ 异常情况：
• yFinance 数据获取失败：1次（已重试成功）
• API 调用限流：0次

🔄 系统状态：正常运行
```

## 7. 错误处理和重试机制

### 7.1 重试策略

**重试配置（system.yaml）：**
```yaml
retry:
  api_call:
    max_attempts: 3
    interval_seconds: 5
    backoff: exponential  # 指数退避
  data_fetch:
    max_attempts: 5
    interval_seconds: 10
    backoff: fixed  # 固定间隔
  trade_execution:
    max_attempts: 3
    interval_seconds: 10
    backoff: fixed
```

**重试装饰器：**
```python
@retry_with_config('api_call')
def call_binance_api(...):
    # API 调用逻辑
```

### 7.2 错误处理策略

**API 调用失败：**
- 自动重试，指数退避
- 达上限：记录错误日志 + 发送告警通知

**数据获取失败：**
- yFinance 失败：重试，失败后跳过本次策略执行，记录到 strategy_executions（status=skipped）
- Binance 实时价格失败：重试，失败后跳过

**交易执行失败：**
- 余额不足：
  - 根据配置选择：部分执行（按实际余额调整）或全部跳过
  - 记录日志 + 告警通知，不重试
- 网络错误/API错误：重试，达上限后记录并告警
- 不影响其他策略执行（异常捕获和隔离）

**持仓不一致：**
- 策略执行前同步 Binance 实际持仓
- 与本地 positions 表对比
- 如有差异：记录日志，以 API 数据为准更新，发送告警

### 7.3 异常恢复机制

**程序启动时：**
1. 检查 strategy_executions 表中 status='running' 的记录
2. 检查对应 trade 是否完成
3. 更新状态或发送告警
4. 检查手动交易配置中的 .processing 文件
5. 从 Binance API 同步最新交易记录和持仓
6. 发送系统恢复通知

## 8. 手动交易处理

### 8.1 配置文件格式

```yaml
# configs/manual_trades/20260925_120000_alice_tqqq.yaml
trade:
  account: alice
  symbol: TQQQ
  action: SELL  # BUY / SELL
  amount: 1000  # 金额（买入时）或数量（卖出时）
  reason: "市场贪婪，减仓"
  created_at: "2026-09-25T12:00:00"
```

### 8.2 处理流程

1. **Scheduler 定期扫描**（每分钟）`configs/manual_trades/` 目录
2. **发现新配置文件**：
   - 立即重命名（加 `.processing` 后缀，避免并发）
   - 验证配置合法性
   - 提取交易指令
3. **调用 Trade Executor 执行**
4. **执行后归档**：
   - 成功：移动到 `archive/` 并加 `executed_` 前缀 + 时间戳
   - 失败：重命名为 `.failed`
5. **记录到数据库**：
   - trades 表中 strategy_id 为空
   - trigger_reason 为 "manual"

### 8.3 并发安全

- 扫描时立即重命名文件（加 .processing 后缀）
- 使用文件锁机制避免并发扫描
- 执行完成后移动到归档目录

## 9. 定时任务和调度

### 9.1 Scheduler 职责

- 管理所有定时任务（基于 APScheduler）
- 策略执行任务（智能调度）
- 手动交易扫描任务
- 汇总通知任务
- 账户快照任务
- 持仓同步任务

### 9.2 智能调度

**问题：** 避免每天都触发策略但大部分时候返回 HOLD。

**解决方案：** Scheduler 根据策略配置计算下一个执行日期。

**示例：**
- DCA "每月第1个交易日"：计算下个月第1个交易日的日期，使用 Cron 触发器
- Drawdown "每周一"：使用 Cron 触发器 `0 9 * * 1`
- 价值平均 "每月1号"：使用 Cron 触发器 `0 9 1 * *`

**好处：**
- 减少无效执行
- strategy_executions 记录更有意义
- 降低系统负载

### 9.3 定时任务列表

| 任务 | 触发器 | 说明 |
|------|--------|------|
| 策略执行 | Cron/Interval | 根据策略配置动态创建 |
| 手动交易扫描 | Interval(60s) | 每分钟扫描一次 |
| 每日汇总通知 | Cron | 配置的时间（如16:30） |
| 每周汇总通知 | Cron | 配置的时间 |
| 每日账户快照 | Cron | 配置的时间（如16:30） |
| 持仓全量同步 | Cron | 每日一次，兜底机制 |

## 10. 程序启动流程

**main.py 启动逻辑：**

1. **加载系统配置**（system.yaml）
2. **初始化日志系统**（按日期轮转，级别可配置）
3. **初始化数据库**（建表、检查完整性）
4. **加载所有账户配置**：
   - 遍历 `configs/accounts/` 目录
   - 加载业务配置 + 敏感信息（`secrets/`）
   - 验证配置合法性（schema 验证）
   - 检查 strategy_id 唯一性
5. **初始化各模块**：
   - MarketDataService（带缓存）
   - BinanceClient（为每个账户创建实例）
   - YFinanceClient
   - WeComNotifier
   - Database
   - TradeExecutor
   - StrategyEngine
   - AccountManager
6. **异常恢复检查**：
   - 检查未完成的 strategy_executions
   - 检查 .processing 状态的手动交易文件
   - 同步所有账户的持仓
   - 发送系统恢复通知
7. **初始化 Scheduler**：
   - 为每个策略实例创建定时任务
   - 创建手动交易扫描任务
   - 创建汇总通知任务
   - 创建账户快照任务
8. **启动 Scheduler**（阻塞运行）
9. **信号处理**（Ctrl+C 优雅退出）

## 11. 关键设计决策

### 11.1 配置文件 vs 数据库

**决策：** 配置文件是唯一配置源，数据库只存执行记录。

**理由：**
- 单一数据源，避免不一致
- 配置文件更直观，易于编辑
- 不需要提供配置管理界面
- 配置变更可通过文件版本控制（Git）

**配置追溯：** strategy_executions 表的 calculation_result 中包含配置快照。

### 11.2 持仓同步机制

**决策：** 策略执行前同步 Binance 实际持仓，以 API 数据为准。

**理由：**
- 避免因漏记、外部交易导致的数据不一致
- 价值平均策略依赖准确的持仓数据
- 每日全量同步作为兜底

**流程：**
```python
actual_position = binance_client.get_position(symbol)
local_position = database.get_position(account, symbol)

if actual_position != local_position:
    logger.warning(f"持仓不一致: {symbol}")
    database.update_position(actual_position)
    notifier.send_alert("持仓差异", details)
```

### 11.3 卖出规则的优先级

**决策：** 
- 价值平均策略不支持额外卖出规则（卖出是核心逻辑）
- DCA 和 Drawdown 支持配置通用卖出规则

**执行顺序：**
1. 先检查通用卖出规则
2. 如果触发，返回 SELL 信号
3. 如果未触发，执行策略买入逻辑

### 11.4 API 限流处理

**决策：** 主动限流检测 + 429 响应处理。

**实现：**
- RateLimiter 维护请求计数器
- 接近阈值时延迟请求
- 收到429时解析Retry-After并等待
- 持续限流时暂停非紧急操作，发送告警

### 11.5 余额不足处理

**决策：** 可配置策略（partial / skip）。

**配置：**
```yaml
balance_check:
  insufficient_action: "partial"  # partial：部分执行 / skip：全部跳过
```

**行为：**
- `partial`：按实际余额调整交易金额
- `skip`：跳过本次交易，发送通知

### 11.6 智能调度 vs 每天触发

**决策：** 智能调度，只在需要执行的日期触发策略。

**理由：**
- 减少无效执行和数据库记录
- strategy_executions 记录更有意义
- 降低系统负载

## 12. 非功能需求

### 12.1 性能

- 市场数据缓存（历史数据当日有效，实时价格1分钟TTL）
- 策略并发执行（独立策略间不相互阻塞）
- API 限流控制，避免触发 Binance 限制

### 12.2 可靠性

- 完整的错误处理和重试机制
- 异常恢复机制（启动时检查未完成任务）
- 持仓同步机制（避免数据不一致）
- 手动交易的并发安全（文件锁和重命名）

### 12.3 可维护性

- 清晰的模块分层和职责划分
- 配置文件管理（易于编辑和版本控制）
- 完整的日志记录（按日期轮转）
- 数据库记录包含配置快照（可追溯）

### 12.4 可扩展性

- 策略基类设计，易于添加新策略
- 外部集成层抽象，易于替换数据源或通知渠道
- 通用卖出规则机制，支持多种触发条件

### 12.5 安全性

- 敏感信息与业务配置分离
- secrets/ 目录不进入 Git 仓库（.gitignore）
- API key 仅在内存中使用，不记录到日志

## 13. 部署和运维

### 13.1 部署方式

- 常驻进程运行
- 通过 PM2 管理（自动重启、日志管理）
- Python 虚拟环境隔离依赖

### 13.2 PM2 配置示例

```json
{
  "name": "us-stock-dca",
  "script": "main.py",
  "interpreter": "python",
  "cwd": "/path/to/us_stock_trading_binance",
  "instances": 1,
  "autorestart": true,
  "watch": false,
  "max_memory_restart": "500M",
  "env": {
    "PYTHONUNBUFFERED": "1"
  },
  "error_file": "logs/pm2-error.log",
  "out_file": "logs/pm2-out.log",
  "log_date_format": "YYYY-MM-DD HH:mm:ss Z"
}
```

### 13.3 监控和告警

- 企业微信告警（API 限流、交易失败、持仓不一致）
- 系统汇总通知（每日执行统计）
- 日志文件监控（ERROR 级别日志）

### 13.4 备份策略

- 配置文件：定期备份 configs/ 和 secrets/
- 数据库：每日备份 data/trading.db
- 日志文件：手动删除旧日志（不自动清理）

## 14. 依赖库

```
# 核心依赖
apscheduler>=3.10.0      # 任务调度
yfinance>=0.2.0          # 历史行情数据
pandas>=2.0.0            # 数据处理
requests>=2.31.0         # HTTP 请求
pyyaml>=6.0              # YAML 配置解析

# 日期处理
pytz>=2023.3             # 时区处理
pandas-market-calendars>=4.3.0  # 交易日历

# 数据库
sqlite3                  # Python 标准库

# 工具
python-dotenv>=1.0.0     # 环境变量管理（可选）
```

## 15. 目录结构

```
us_stock_trading_binance/
├── core/
│   ├── __init__.py
│   ├── scheduler.py
│   ├── strategy_engine.py
│   ├── trade_executor.py
│   └── account_manager.py
├── strategies/
│   ├── __init__.py
│   ├── base.py
│   ├── dca.py
│   ├── drawdown.py
│   └── value_averaging.py
├── integrations/
│   ├── __init__.py
│   ├── binance_client.py
│   ├── yfinance_client.py
│   └── wecom_notifier.py
├── storage/
│   ├── __init__.py
│   ├── database.py
│   └── models.py
├── config/
│   ├── __init__.py
│   ├── loader.py
│   └── validator.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── retry.py
│   ├── rate_limiter.py
│   └── date_utils.py
├── configs/
│   ├── system.yaml
│   ├── accounts/
│   │   ├── alice.yaml
│   │   └── bob.yaml
│   └── manual_trades/
│       └── archive/
├── secrets/
│   ├── .gitkeep
│   ├── alice.key
│   └── bob.key
├── logs/
│   └── .gitkeep
├── data/
│   └── .gitkeep
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-09-25-us-stock-dca-framework-design.md
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
└── pm2.config.json
```

## 16. .gitignore

```
# 敏感信息
secrets/
!secrets/.gitkeep

# 数据库
data/*.db
data/*.db-journal

# 日志
logs/*.log
logs/pm2-*.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# 手动交易归档（可选保留）
# configs/manual_trades/archive/
```

## 17. 未来扩展方向

### 17.1 短期扩展

- Web 管理界面（查看持仓、执行历史、手动触发）
- 更多策略类型（动量策略、均线策略等）
- 更多通知渠道（钉钉、Slack、邮件）
- 配置热加载（无需重启）

### 17.2 长期扩展

- 支持更多交易平台（Robinhood、IBKR等）
- 回测系统（基于历史数据测试策略）
- 策略优化（参数自动调优）
- 多资产组合管理
- 风险管理模块（最大回撤控制、止损等）

## 18. 总结

本设计文档描述了一个完整的美股定投框架，具备以下特点：

- **多账户多策略**：灵活配置，满足不同投资需求
- **三种核心策略**：DCA、Drawdown、价值平均，各有特色
- **自动化执行**：智能调度，减少无效操作
- **完整的错误处理**：重试机制、异常恢复、持仓同步
- **全面的通知系统**：即时通知 + 定时汇总
- **清晰的架构**：分层设计，易于维护和扩展
- **数据追溯性**：完整记录，包含配置快照

设计中解决了9个关键问题：
1. ✅ 卖出规则冲突
2. ✅ 持仓同步机制
3. ✅ 智能调度
4. ✅ 手动交易并发安全
5. ✅ API 限流处理
6. ✅ 余额不足处理
7. ✅ 卖出语义明确
8. ✅ 时区处理
9. ✅ 异常恢复机制

该框架已具备进入实施阶段的完整设计基础。
