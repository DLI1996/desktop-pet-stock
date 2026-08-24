# CONNECTOR.md — 行情连接记录

## 实际使用的连接器 / Skill

**名称**：`a-stock-realtime`（千问办公内置 Skill，数据源为新浪财经接口）

**Skill 脚本位置**：`/Users/mac/.qwenworkcn/skills/a-stock-realtime/scripts/analyze.py`

**调用方式**（桌面程序无法直接调用千问办公 Skill，采用文件桥接）：

```bash
uv run /Users/mac/.qwenworkcn/skills/a-stock-realtime/scripts/analyze.py 600519 --json
```

实际返回结构（2026-08-20 21:46 实测）：

```json
[
  {
    "code": "sh000001",
    "name": "平安银行",
    "realtime": {
      "code": "000001",
      "name": "平安银行",
      "price": 11.4,
      "open": 11.2,
      "pre_close": 11.27,
      "high": 11.4,
      "low": 11.19,
      "volume": 1183578,
      "amount": 1338932697.29,
      "change_amt": 0.13,
      "change_pct": 1.15,
      "turnover": null
    },
    "updated_at": "2026-08-20T21:46:52.135738"
  }
]
```

注意：该 Skill 会把 `sh000001` 前缀剥离并按深市个股解析（返回平安银行），
**仅适合 6 位个股代码**；指数需走下面的新浪直连接口。

## 桥接层（Skill → 桌宠）

启动顺序：

1. 千问办公中运行 `python tools/quote_bridge.py <6位代码>`
   （内部调用上述 Skill 命令，解析 `realtime` 字段，规范化市场前缀）
2. 桥接脚本把结果写入项目根目录 `quote.json`：

```json
{
  "symbol": "sh600519",
  "name": "贵州茅台",
  "price": 1291.5,
  "change": -16.38,
  "change_percent": -1.25,
  "timestamp": "2026-08-20 21:47:45",
  "source": "a-stock-realtime Skill"
}
```

3. 桌宠每次轮询时优先读取 `quote.json`（`SkillBridgeProvider`，超过 120 秒视为过期）。

桥接实测（600519）：✅ 成功写入并被 `SkillBridgeProvider` 正确读取。

## 备用数据源（默认关闭）

**名称**：`SinaHttpProvider`（新浪财经公开行情接口 `hq.sinajs.cn`，延迟约 3 秒）

- 启用方式：在 `config.json` 中显式设置 `"enable_http_fallback": true`
- 触发条件：已启用，且 `quote.json` 不存在 / 过期 / symbol 不匹配，或桥接读取异常
- 请求头：`Referer: https://finance.sina.com.cn`
- 接口实测（2026-08-20 21:28）：`sh000001` 返回上证指数 3903.7210 +0.24%
- 界面数据源标注：`新浪财经接口(hq.sinajs.cn)`（如实标注，不冒充 Skill）
- 隐私说明：启用后会向新浪发送所查看的标的，并暴露客户端 IP

## 统一接口

`StockDataProvider.get_quote(symbol) -> QuoteResult`：

```json
{
  "symbol": "sh000001",
  "name": "上证指数",
  "price": 3903.721,
  "change": 9.2986,
  "change_percent": 0.2388,
  "timestamp": "2026-08-20 15:35:32",
  "source": "新浪财经接口(hq.sinajs.cn)",
  "is_realtime": false,
  "market_open": false,
  "ok": true
}
```

所有请求后台线程执行，超时 8 秒；失败保留最后一次成功数据并在卡片显示「行情连接暂时走丢了」。非交易时段 `is_realtime=false`，徽标显示「已收盘 / 午间休市」。

## 容错实测结果

| 场景 | 结果 |
|------|------|
| 正常获取（收盘后） | ✅ 返回收盘数据，标注非实时 |
| 无效代码（sz999999） | ✅ 返回「接口返回空数据」，UI 显示连接走丢 |
| 模拟断网 | ✅ 保留旧数据，不崩溃 |
| 桥接文件过期/不匹配 | 默认不联网；显式启用后降级新浪直连 |
