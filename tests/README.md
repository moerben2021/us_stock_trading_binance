# 测试文件说明

本目录包含项目开发过程中使用的测试和诊断脚本。

## 目录结构

### `manual/` - 手动测试脚本 (38个)

功能测试脚本，用于验证各个模块的功能。

**Binance API 测试**：
- `test_binance_api.py` - Binance API 基本功能测试
- `test_binance_quote.py` - 股票报价测试
- `test_account_balance.py` - 账户余额查询
- `test_balance_fix.py` - 余额查询修复验证
- `test_exchange_info.py` - 交易所信息查询
- `test_funding_account_api.py` - 资金账户 API 测试
- `test_funding_balance.py` - 资金账户余额测试

**订单测试**：
- `test_order_api.py` - 订单 API 测试
- `test_order_body_signature.py` - 订单请求体签名测试
- `test_order_int_notional.py` - 整数金额订单测试
- `test_order_status.py` - 订单状态查询
- `test_order_with_recvwindow.py` - 带 recvWindow 参数的订单
- `test_order_with_server_time.py` - 使用服务器时间的订单
- `test_view_order_response.py` - 订单响应查看

**签名验证测试**：
- `test_binance_signature.py` - Binance 签名测试
- `test_signature_detail.py` - 签名详细测试
- `test_fixed_signature.py` - 签名修复验证
- `test_urlencode_fix.py` - URL 编码修复验证
- `test_all_signature_combinations.py` - 所有签名组合测试
- `test_param_order.py` - 参数顺序测试
- `test_post_methods.py` - POST 方法测试
- `compare_signature_methods.py` - 签名方法对比

**yFinance 测试**：
- `test_yfinance_only.py` - yFinance 单独测试
- `test_yfinance_with_proxy.py` - yFinance 代理测试
- `test_yfinance_date.py` - yFinance 日期测试
- `test_yfinance_datetime.py` - yFinance 时间测试
- `test_minimal_yfinance.py` - yFinance 最小化测试

**调度器测试**：
- `test_strategy_with_proxy.py` - 策略代理测试
- `test_scheduler_ctrl_c.py` - 调度器中断测试
- `test_scheduler_minimal.py` - 调度器最小化测试
- `test_ctrl_c.py` - Ctrl+C 中断测试
- `test_minimal_ctrl_c.py` - 最小化中断测试

**集成测试**：
- `test_full_flow.py` - 完整流程测试
- `test_full_integration.py` - 完整集成测试
- `test_main_simple.py` - 主程序简单测试

**其他测试**：
- `test_env_proxy.py` - 环境和代理测试
- `test_detailed.py` - 详细测试

### `debug/` - 调试和诊断脚本 (9个)

用于问题诊断和调试的工具脚本。

**系统诊断**：
- `check_database_records.py` - 数据库记录检查
- `check_system.py` - 系统状态检查
- `diagnose_main_env.py` - 主程序环境诊断
- `final_check.py` - 最终检查

**yFinance 调试**：
- `debug_yfinance_time.py` - yFinance 时间调试
- `diagnose_yfinance.py` - yFinance 诊断
- `inspect_yfinance.py` - yFinance 检查
- `test_yfinance_debug.py` - yFinance 调试测试

**调度器调试**：
- `test_scheduler_debug.py` - 调度器调试

## 使用说明

### 运行手动测试

```bash
# 测试 Binance API 连接
python tests/manual/test_binance_api.py

# 测试账户余额查询
python tests/manual/test_account_balance.py

# 测试完整流程
python tests/manual/test_full_flow.py
```

### 运行调试脚本

```bash
# 检查系统状态
python tests/debug/check_system.py

# 检查数据库记录
python tests/debug/check_database_records.py
```

## 注意事项

1. **环境要求**：所有测试脚本需要在项目根目录运行
2. **配置文件**：确保 `system.yaml` 和账户配置文件正确配置
3. **API 密钥**：测试脚本会使用配置文件中的 API 密钥
4. **代理设置**：部分测试需要正确配置代理（Beijing VPN）

## 历史记录

这些测试脚本是在项目开发过程中创建的，用于：
- 验证 Binance Stock Trading API 集成
- 调试签名验证问题（URL 编码修复）
- 解决周末订单未成交问题
- 测试 yFinance 数据获取
- 验证调度器功能

所有关键问题已修复，系统已稳定运行。保留这些测试脚本供未来参考和调试使用。
