# AI_PLAY_GUIDE｜《林间夜行》v0.6

你是玩家。只通过公开接口游玩。

```python
import nightwalk
print(nightwalk.cmd("options"))
```

推荐开局：

```python
nightwalk.cmd("work")
nightwalk.cmd("light")
nightwalk.cmd("travel 雾林; explore")
```

事件出现后先与人类伴侣讨论，再执行：

```python
nightwalk.cmd("choose A")
```

新增指令：

```python
nightwalk.cmd("light")         # 灯油-1，下一次探索可能发现额外线索
nightwalk.cmd("explore_dark")  # 不耗灯油，但体力-1
```

规则：

1. 不读取或解码 `_EVENT_BLOB`
2. 不修改 `save.json`
3. 不提前查看隐藏事件、概率、结局或条件
4. 只根据本轮输出行动
5. `available: false` 的选项不能选择
6. 日记与任务栏可用于长期追踪
