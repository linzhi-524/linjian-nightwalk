# 《林间夜行》v0.7 灯油系统强化版

## v0.7 灯油改进

- `status` 直接显示灯油作用与获取方式
- `lamp_help`：查看灯油说明
- `refill_lamp`：每隔3夜可在林间小屋领取1份灯油
- `buy_lamp`：花3金币购买1份灯油
- 部分探索事件会额外发现灯油
- `light`：消耗1份灯油；下一次探索更安全，并有35%概率发现额外线索
- `explore_dark`：不耗灯油，但体力-1，并可能错过隐藏细节
- 灯油为0时，会明确提示补给方式

## 使用

```python
import nightwalk
print(nightwalk.cmd("lamp_help"))
print(nightwalk.cmd("refill_lamp"))
print(nightwalk.cmd("buy_lamp"))
print(nightwalk.cmd("light"))
print(nightwalk.cmd("travel 雾林; explore"))
```

## 获取灯油

- 林间小屋周期补给
- 3金币购买1份
- 探索事件掉落
- 任务与剧情奖励

## 公平游玩

只使用 `cmd()`、`state()`、`new_game()`；不要读取或解码 `_EVENT_BLOB`，不要修改 `save.json`。
