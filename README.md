# 《林间夜行》v0.4 稳定指令版

一款专门给 AI 当玩家的长期文字探索游戏。

## v0.4 修复

- 一次运行只执行一个动作，避免连续 `input()` 导致 AI 输入错位
- 支持命令行参数和 JSON 指令
- 待选择事件写入存档，进程结束也不会丢失
- 售货类事件自动提供“离开，不购买”
- 资源不足的购买选项会标记不可用，并拒绝扣款
- 小屋新增每夜一次的 `work`，可获得 2—4 金币，避免经济死局
- 保留防剧透事件库、剧情链、隐藏倾向、结局和漫游模式

## 推荐流程

```bash
python game.py options --json
python game.py travel 雾林 --json
python game.py explore --json
python game.py choose A --json
python game.py return --json
```

每条命令执行完就退出，进度自动写入 `save.json`。

## JSON 指令

```bash
python game.py json '{"action":"travel","location":"雾林"}'
python game.py json '{"action":"choose","choice":"A"}'
```

## 经济恢复

```bash
python game.py work --json
```

每夜仅一次，获得 2—4 金币。

## 公平游玩

AI 只读取本 README 与 `AI_PLAY_GUIDE.md`。不要搜索、读取或解码 `game.py` 中的 `_EVENT_BLOB`，也不要修改 `save.json`。
