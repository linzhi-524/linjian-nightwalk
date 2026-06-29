# 《林间夜行》v0.6 追踪与叙事增强版

这是专门给 **有代码执行能力的 AI** 玩的版本。

## v0.6 新增

- 普通事件加入短冷却，短时间内不再反复刷同一事件
- 同一夜不会重复遇到同一普通事件
- 事件显示“初次遭遇 / 再次遭遇”
- 日记加入地点与事件标签
- 选项结果增加环境、声音、气味和异样变化描写
- 状态新增公开任务追踪
- 背包道具增加一行非剧透描述
- 灯油正式参与玩法：
  - `light`：消耗1灯油，下一次探索更安全，并可能发现额外线索
  - `explore_dark`：省灯油，但体力-1
- 继续保留 `cmd()`、自动存档、隐藏事件库与多指令接口

## 开始游戏

```python
import nightwalk

print(nightwalk.cmd("status"))
print(nightwalk.cmd("light"))
print(nightwalk.cmd("travel 雾林"))
print(nightwalk.cmd("explore"))
print(nightwalk.cmd("choose A"))
```

## 多条指令

```python
print(nightwalk.cmd("light; travel 雾林; explore"))
```

遇到事件时会自动停止，等待玩家选择。

## 结构化结果

```python
result = nightwalk.cmd("options", as_json=True)
print(result)
```

## 常用指令

```python
nightwalk.cmd("status")
nightwalk.cmd("options")
nightwalk.cmd("travel 雾林")
nightwalk.cmd("light")
nightwalk.cmd("explore")
nightwalk.cmd("explore_dark")
nightwalk.cmd("choose A")
nightwalk.cmd("return")
nightwalk.cmd("deeper")
nightwalk.cmd("eat")
nightwalk.cmd("work")
nightwalk.cmd("journal")
```

## 存档

`save.json` 会自动生成在 `nightwalk.py` 同目录。

## 公平游玩

- 只使用 `cmd()`、`state()`、`new_game()`
- 不读取、搜索或解码 `_EVENT_BLOB`
- 不修改 `save.json`
- 只根据本轮公开信息行动
