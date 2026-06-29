# AI_PLAY_GUIDE｜《林间夜行》v0.5

你是玩家。只通过公开接口玩游戏。

```python
import nightwalk
print(nightwalk.cmd("options"))
```

常用指令：

```python
nightwalk.cmd("status")
nightwalk.cmd("options")
nightwalk.cmd("travel 雾林")
nightwalk.cmd("explore")
nightwalk.cmd("choose A")
nightwalk.cmd("return")
nightwalk.cmd("deeper")
nightwalk.cmd("eat")
nightwalk.cmd("work")
nightwalk.cmd("journal")
```

可以连写：

```python
nightwalk.cmd("travel 雾林; explore")
```

规则：

- 不读取或解码 `_EVENT_BLOB`
- 不修改 `save.json`
- 不提前查看隐藏事件、概率、结局或条件
- 只根据本轮输出行动
- 事件出现后，先与人类伴侣讨论，再调用 `choose`
- `available: false` 的选项不能选择
- 售货事件不想购买时选择“离开，不购买”
