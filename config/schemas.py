"""配置 schema 定义"""

SYSTEM_CONFIG_SCHEMA = {
    "system": {
        "timezone": str,
        "log_level": str
    },
    "scheduler": {
        "check_interval": int,
        "manual_trade_scan_interval": int
    },
    "database": {
        "path": str
    },
    "cache": {
        "realtime_price_ttl": int,
        "history_data_clear_time": str
    },
    "retry": {
        "api_call": {
            "max_attempts": int,
            "interval_seconds": int,
            "backoff": str
        },
        "data_fetch": {
            "max_attempts": int,
            "interval_seconds": int,
            "backoff": str
        },
        "trade_execution": {
            "max_attempts": int,
            "interval_seconds": int,
            "backoff": str
        }
    },
    "notifications": {
        "admin_webhook": str,
        "summaries": dict
    },
    "snapshots": {
        "after_trade": bool,
        "daily_close": dict
    },
    "balance_check": {
        "insufficient_action": str
    }
}

ACCOUNT_CONFIG_SCHEMA = {
    "account": {
        "name": str,
        "wecom_webhook": str
    },
    "strategies": list
}

STRATEGY_CONFIG_SCHEMA = {
    "id": str,
    "type": str,  # DCA / Drawdown / ValueAveraging
    "symbol": str,
    "config": dict,
    "status": str  # active / paused
}
