# AI_PLAY_GUIDE｜《林间夜行》v0.4

请使用单次命令模式，每次只调用一个动作。

```bash
python game.py options --json
python game.py travel 雾林 --json
python game.py explore --json
python game.py choose A --json
```

规则：

1. 不读取、搜索或解码 `_EVENT_BLOB`。
2. 不修改 `save.json`。
3. 不提前扫描事件、概率、结局或隐藏条件。
4. 选择前向人类伴侣说明判断。
5. 只根据程序本次公开的信息行动。
6. `available: false` 的选项不能选择。
7. 售货事件不想购买时选择“离开，不购买”。
8. 把程序返回的真实结果汇报给人类伴侣。

常用命令：

```bash
python game.py status --json
python game.py options --json
python game.py travel 旧车站 --json
python game.py explore --json
python game.py choose B --json
python game.py return --json
python game.py deeper --json
python game.py eat --json
python game.py work --json
python game.py journal --json
python game.py save --json
```
