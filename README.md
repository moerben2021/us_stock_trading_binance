# 美股定投框架

基于 Binance 美股交易 API 的自动定投框架。

## 特性

- 支持多账户、多策略
- 三种定投策略：DCA、Drawdown、价值平均
- 自动执行和手动干预
- 企业微信通知
- 完整的日志和数据记录

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置文件模板到 `configs/`
2. 创建 `secrets/` 目录并添加 API key
3. 修改 `configs/system.yaml` 中的系统配置

## 运行

```bash
python main.py
```

## 文档

- [设计文档](docs/superpowers/specs/2026-09-25-us-stock-dca-framework-design.md)
- [实施计划](docs/superpowers/plans/2026-09-25-us-stock-dca-framework.md)
