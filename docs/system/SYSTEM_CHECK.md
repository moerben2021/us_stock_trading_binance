# 系统运行检查清单

## 启动前检查

### 1. 环境配置
- [x] Python 3.9+ 已安装
- [x] 所有依赖库已安装（yaml, requests, apscheduler, pandas, yfinance, pytz）
- [x] 代理服务正常运行（北京：OK云 port 7990；日本服务器：直连）

### 2. 配置文件
- [x] `system.yaml` - 系统配置（代理、时区、重试策略）
- [x] `configs/accounts/account1.yaml` - 账户配置（webhook、策略）
- [x] `secrets/account1.key` - API 密钥配置

### 3. API 密钥权限
- [x] Binance API Key 已配置
- [x] Binance Secret Key 已配置
- [x] API Key 有股票交易权限（Enable Stocks Trading）
- [x] 账户有足够 USDC 余额（当前 $312.24）

### 4. 企业微信通知
- [x] Webhook URL 已配置
- [x] 配置字段名正确（`wecom_webhook`）
- [x] 通知格式支持已成交/未成交状态

### 5. 策略配置
- [x] 6 个策略已配置（2个DCA、2个Drawdown、2个ValueAveraging）
- [x] 所有策略状态为 `active`
- [x] 定时任务使用美东时间（America/New_York）
- [x] 投资金额设置为 $6

## 核心功能验证

### 1. 签名验证 ✅
- [x] 使用 `urllib.parse.urlencode()` 生成签名
- [x] 资金账户查询成功
- [x] 下单接口返回订单ID（status: "S"）

### 2. 订单处理 ✅
- [x] 下单后自动查询订单详情
- [x] 获取真实成交数量（executedQty）
- [x] 未成交时（executedQty=0）不执行后续流程
- [x] 防止被 0 除错误

### 3. 通知系统 ✅
- [x] 已成交：发送交易通知（含成交信息）
- [x] 未成交：发送待成交通知（含订单ID和原因）
- [x] 通知格式统一（主体相同，状态不同）

### 4. 数据记录 ✅
- [x] 交易记录保存到数据库
- [x] 持仓信息自动更新
- [x] 策略执行记录保存

## 运行流程

### 启动系统
```bash
python main.py
```

### 预期行为

**周末/市场关闭时：**
1. 策略定时触发
2. 生成交易信号（BUY $6）
3. 提交订单到 Binance（获得订单ID）
4. 查询订单详情（executedQty = 0）
5. 发送企业微信通知（待成交状态）
6. 不更新持仓和余额

**市场开盘时：**
1. 策略定时触发
2. 生成交易信号（BUY $6）
3. 提交订单到 Binance（获得订单ID）
4. 查询订单详情（executedQty > 0）
5. 更新持仓和余额
6. 记录交易到数据库
7. 发送企业微信通知（已成交状态）

## 策略执行时间（美东时间）

| 策略 | 标的 | 类型 | 执行时间 |
|------|------|------|----------|
| dca_spy_monthly | SPY | DCA | 每天 10:32 |
| dca_qqq_weekly | QQQ | DCA | 每周三 10:00 |
| drawdown_spy | SPY | Drawdown | 每天 15:00 |
| drawdown_qqq | QQQ | Drawdown | 每天 15:30 |
| va_spy_monthly | SPY | ValueAveraging | 每月1号 10:00 |
| va_qqq_monthly | QQQ | ValueAveraging | 每月15号 10:00 |

**美股交易时间：** 周一至周五 9:30-16:00 ET

## 监控和日志

### 日志文件
- `logs/app.log` - 应用主日志
- 查看实时日志：`tail -f logs/app.log`

### 关键日志关键字
- `下单接口完整响应` - 查看下单返回的完整信息
- `订单详情` - 查看订单成交情况
- `企业微信通知发送成功` - 确认通知已发送
- `买入交易完成` - 确认交易执行完成
- `订单已提交但未成交` - 周末/市场关闭的预期行为

### 数据库查询
```sql
-- 查看最近的交易记录
SELECT * FROM trades ORDER BY executed_at DESC LIMIT 10;

-- 查看当前持仓
SELECT * FROM positions WHERE quantity > 0;

-- 查看策略执行记录
SELECT * FROM strategy_executions ORDER BY executed_at DESC LIMIT 10;
```

## 故障排查

### 问题：签名验证失败
- 检查：API Key 和 Secret Key 是否正确
- 检查：是否使用 `urlencode()` 生成签名
- 检查：时间同步是否正常

### 问题：通知不发送
- 检查：`wecom_webhook` 字段是否配置
- 检查：代码中读取字段名是否正确
- 检查：日志中是否有 "企业微信通知" 相关记录

### 问题：被 0 除错误
- 已修复：下单后查询订单详情
- 已修复：未成交时不执行持仓更新
- 已修复：_update_position 方法增加 quantity > 0 检查

## 下一步

**等待美股开盘（周一 9:30 ET）：**
1. 系统自动执行策略
2. 验证真实成交情况
3. 确认企业微信通知正常
4. 检查持仓和余额更新

**系统已就绪，可以运行！** 🚀
