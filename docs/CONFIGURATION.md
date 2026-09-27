# 配置指南

本文档说明如何配置系统和账户。

## 快速开始

### 1. 系统配置

复制示例配置并修改：

```bash
# 复制系统配置模板（在项目根目录）
cp system.yaml.example system.yaml

# 编辑配置文件
nano system.yaml  # 或使用你喜欢的编辑器
```

**需要修改的内容**：

- `notifications.admin_webhook` - 替换为你的企业微信 Webhook URL
- `system.proxy.enabled` - 根据网络环境设置（需要代理设为 `true`）
- `system.proxy.http/https` - 如果使用代理，填写代理地址

### 2. 账户配置

```bash
# 复制账户配置模板
cp configs/accounts/account1.yaml.example configs/accounts/account1.yaml

# 编辑账户配置
nano configs/accounts/account1.yaml
```

**需要修改的内容**：

- `account.name` - 账户名称（对应密钥文件名）
- `account.wecom_webhook` - 账户级别的企业微信 Webhook URL
- `strategies` - 根据需要调整策略配置

### 3. API 密钥配置

创建密钥文件（与账户名对应）：

```bash
# 创建密钥目录（如果不存在）
mkdir -p secrets

# 创建密钥文件
nano secrets/account1.key
```

**密钥文件格式** (`secrets/account1.key`)：

```yaml
binance:
  api_key: "YOUR_BINANCE_API_KEY"
  secret_key: "YOUR_BINANCE_SECRET_KEY"
```

⚠️ **安全提醒**：
- `secrets/` 目录已在 `.gitignore` 中排除
- 密钥文件**永远不会**被提交到 Git
- 请妥善保管你的 API 密钥

## 配置文件说明

### system.yaml

系统级配置，包括：
- 时区设置
- 日志级别
- 代理配置
- 调度器参数
- 数据库路径
- 缓存设置
- 重试策略
- 通知配置（日报/周报/月报）
- 快照配置
- 余额检查策略

### configs/accounts/*.yaml

账户级配置，每个账户一个文件：
- 账户基本信息
- 企业微信通知地址（账户级别）
- 交易策略列表
  - DCA（定期定额）
  - Drawdown（回撤加仓）
  - ValueAveraging（价值平均）

### secrets/*.key

API 密钥文件（YAML 格式）：
- Binance API Key
- Binance Secret Key

## 获取 API 密钥

### Binance Stock Trading API

1. 登录 Binance 账户
2. 访问 API 管理页面
3. 创建新的 API Key
4. **重要**：确保开启 **Stock Trading** 权限
5. 记录 API Key 和 Secret Key
6. 设置 IP 白名单（推荐）

### 企业微信 Webhook

1. 登录企业微信管理后台
2. 创建群机器人
3. 获取 Webhook URL（格式：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...`）
4. 复制完整 URL 到配置文件

## 配置示例

### 简单配置（单策略）

**system.yaml**:
```yaml
system:
  timezone: "America/New_York"
  log_level: "INFO"
  proxy:
    enabled: false

notifications:
  admin_webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
```

**configs/accounts/account1.yaml**:
```yaml
account:
  name: "account1"
  wecom_webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
  initial_balance: 10000.0

strategies:
  - id: "dca_spy_monthly"
    type: "DCA"
    symbol: "SPY"
    status: "active"
    schedule: "0 10 1 * *"  # 每月 1 号上午 10:00（美东时间）
    config:
      base_amount: 100.0  # 每次投资 100 美元
```

### 高级配置（多策略）

参考 `configs/accounts/account1.yaml.example` 中的完整示例。

## 验证配置

运行系统检查脚本：

```bash
python tests/debug/check_system.py
```

检查内容：
- ✅ 配置文件格式
- ✅ API 密钥有效性
- ✅ 网络连接（代理）
- ✅ Binance API 权限
- ✅ 企业微信 Webhook 可用性
- ✅ 数据库连接

## 常见问题

### 1. API 签名错误

**现象**：`Signature for this request is not valid`

**解决**：
- 检查 API Key 和 Secret Key 是否正确
- 确认 API Key 开启了 Stock Trading 权限
- 检查系统时间是否同步（时间差不能超过 5 秒）

### 2. 代理连接失败

**现象**：`ProxyError` 或超时

**解决**：
- 确认代理服务正在运行
- 检查代理地址和端口是否正确
- 如果不需要代理，设置 `system.proxy.enabled: false`

### 3. Webhook 通知失败

**现象**：没有收到企业微信通知

**解决**：
- 检查 Webhook URL 是否正确
- 确认企业微信机器人未被禁用
- 查看日志文件 `logs/app.log` 了解详细错误

## 安全建议

1. ✅ **永远不要**将密钥文件提交到 Git
2. ✅ **定期轮换** API Key
3. ✅ **启用 IP 白名单**限制 API Key 访问
4. ✅ **使用最小权限**原则，只开启必需的 API 权限
5. ✅ **备份配置文件**到安全位置
6. ✅ **监控 API 使用**情况，及时发现异常

## 更多帮助

- 查看 [README.md](../README.md) 了解系统功能
- 查看 [SYSTEM_CHECK.md](docs/system/SYSTEM_CHECK.md) 了解系统检查清单
- 查看 [工作日志](docs/work_logs/) 了解开发历史
