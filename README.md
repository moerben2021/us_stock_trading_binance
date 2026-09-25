# 美股定投框架

完全自动化的美股定期定额投资（DCA）和策略交易框架，支持多账户、多策略、企业微信通知和详细的交易记录。

## 主要特性

✅ **多账户多策略** - 同时管理多个交易账户和投资策略  
✅ **三大策略** - DCA 定期定额、Drawdown 低位补仓、ValueAveraging 价值平均  
✅ **自动执行** - 按时间表自动执行交易，无需手动操作  
✅ **手动介入** - 支持手动交易配置和快速执行  
✅ **企业微信通知** - 实时交易通知和定期报表  
✅ **完整日志** - 详细的交易记录和操作日志  
✅ **余额检查** - 自动检查余额，防止交易失败  
✅ **API 限流** - 智能 API 请求管理和重试机制  
✅ **异常恢复** - 自动处理错误和异常情况  

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

#### 系统配置 (system.yaml)

```bash
cp configs/system.yaml.example configs/system.yaml
```

编辑 `configs/system.yaml`，配置以下项：
- `timezone`: 时区（默认美东）
- `log_level`: 日志级别
- `scheduler.check_interval`: 检查间隔（秒）
- `notifications.admin_webhook`: 管理员 Webhook URL
- 其他系统参数

#### 账户配置 (account.yaml)

```bash
cp configs/accounts/example.yaml configs/accounts/my_account.yaml
```

编辑 `configs/accounts/my_account.yaml`，配置：
- 账户名称和企业微信 Webhook
- 投资策略（名称、类型、参数）
- 各策略的状态（active/paused）

#### 密钥配置 (secrets.key)

```bash
cp secrets/example.key secrets/binance.key
```

编辑 `secrets/binance.key`，填入：
- `binance.api_key`: 你的 Binance API Key
- `binance.secret_key`: 你的 Binance Secret Key

### 3. 运行框架

#### 直接运行

```bash
python main.py
```

#### 使用 PM2 运行

```bash
pm2 start pm2.config.json
pm2 logs us-stock-dca
```

## 投资策略详解

### DCA（定期定额）策略

定期以固定金额购买美股，不受价格波动影响，长期分散风险。

**配置示例：**

```yaml
- name: "TQQQ Monthly DCA"
  strategy_type: "DCA"
  symbol: "TQQQ"
  status: "active"
  parameters:
    amount: 500
    interval: "monthly"
    day_of_month: 15
    time: "10:00"
  sell_rules:
    - condition: "profit_percent"
      value: 20
      action: "sell_all"
```

**参数说明：**
- `amount`: 每次投资金额
- `interval`: 投资频率（daily/weekly/monthly）
- `day_of_month`: 每月投资日期
- `time`: 投资时间（24小时制）
- `sell_rules`: 卖出规则（获利目标、止损点）

### Drawdown（低位补仓）策略

在股价下跌时自动补仓，摊低平均成本。

**配置示例：**

```yaml
- name: "SPY Weekly Drawdown"
  strategy_type: "Drawdown"
  symbol: "SPY"
  status: "active"
  parameters:
    base_amount: 1000
    check_interval: "weekly"
    day_of_week: "Monday"
    time: "09:30"
    drawdown_threshold: 5
    max_buys_per_week: 2
```

**参数说明：**
- `base_amount`: 基础投资金额
- `check_interval`: 检查频率
- `drawdown_threshold`: 下跌幅度阈值（%）
- `max_buys_per_week`: 每周最多补仓次数

### ValueAveraging（价值平均）策略

根据目标价值路径动态调整持仓，定期买卖以保持目标增长路径。

**配置示例：**

```yaml
- name: "QQQ Value Averaging"
  strategy_type: "ValueAveraging"
  symbol: "QQQ"
  status: "active"
  parameters:
    target_value_path: 10000
    monthly_increment: 500
    rebalance_interval: "monthly"
    sell_threshold: 15
```

**参数说明：**
- `target_value_path`: 目标总价值
- `monthly_increment`: 每月增长目标
- `rebalance_interval`: 重新平衡频率
- `sell_threshold`: 卖出阈值（%）

## 手动交易

### 手动交易配置

在 `configs/accounts/` 目录中的账户配置文件中添加手动交易指令：

```yaml
manual_trades:
  - symbol: "AAPL"
    action: "buy"
    amount: 100
    status: "pending"
    executed_at: null
```

### 支持的操作

- `buy`: 购买指定数量的股票
- `sell`: 卖出指定数量的股票
- `sell_all`: 卖出全部持仓

## 目录结构

```
us_stock_trading_binance/
├── configs/                    # 配置文件目录
│   ├── system.yaml            # 系统配置
│   └── accounts/              # 账户配置
│       ├── my_account.yaml
│       └── example.yaml
├── secrets/                    # 密钥文件（在 .gitignore 中）
│   ├── binance.key
│   └── example.key
├── logs/                       # 日志目录
│   ├── trading.log
│   ├── pm2-out.log
│   └── pm2-error.log
├── data/                       # 数据目录
│   └── trading.db             # SQLite 数据库
├── src/                        # 源代码
│   ├── strategies/            # 投资策略实现
│   ├── core/                  # 核心模块
│   └── utils/                 # 工具函数
├── main.py                    # 主入口
├── requirements.txt           # 依赖列表
├── pm2.config.json           # PM2 配置
├── README.md                 # 本文件
└── LICENSE                   # MIT 许可证
```

## 重要说明

### 安全性

- 不要将 `secrets/` 目录提交到版本控制系统
- 定期更新 Binance API 密钥
- 使用 IP 白名单保护 API 密钥
- 定期检查交易日志，确保没有异常操作

### 测试环境

强烈建议在沙箱或测试环境中先测试策略：
- 使用较小的投资金额
- 在工作时间内监控运行
- 验证所有配置和通知正常工作

### 余额检查

确保 Binance 账户有足够的 USDT 或 USD 余额：
- DCA 策略：至少 1.5 倍的月投资额
- Drawdown 策略：至少 2 倍的基础投资额
- 预留 5% 作为缓冲

### 交易时间

美股交易时间（美东时区）：
- 常规交易：09:30 - 16:00
- 盘前交易：04:00 - 09:30
- 盘后交易：16:00 - 20:00

建议在常规交易时间内执行交易。

### 日志监控

定期检查日志文件以监控框架运行状态：

```bash
# 查看最近日志
tail -f logs/trading.log

# 查看 PM2 日志
pm2 logs us-stock-dca
```

## 许可证

MIT License - 详见 LICENSE 文件
