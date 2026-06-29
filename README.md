# 《林间夜行》v0.5 AI 原生版

这是专门给 **有代码执行能力的 AI** 玩的版本。  
用户把 GitHub 仓库链接发给 AI 后，AI 下载或读取 `nightwalk.py`，然后通过统一接口持续游玩。

## 最简单的玩法

```python
import nightwalk

print(nightwalk.cmd("status"))
print(nightwalk.cmd("travel 雾林"))
print(nightwalk.cmd("explore"))
print(nightwalk.cmd("choose A"))
```

## 一次执行多条命令

```python
print(nightwalk.cmd("travel 雾林; explore"))
```

当程序遇到需要选择的事件时，会自动停止后续连锁命令，避免跳过决策。

## 结构化结果

```python
result = nightwalk.cmd("options", as_json=True)
print(result)
```

## 新建游戏

```python
print(nightwalk.new_game("RESET"))
```

## 当前状态

```python
print(nightwalk.state())
```

## 存档

程序会在 `nightwalk.py` 同目录自动创建：

```text
save.json
```

下次继续调用 `nightwalk.cmd(...)`，进度会自动恢复。

## 给 AI 的游玩规则

1. 只使用公开接口：`cmd()`、`state()`、`new_game()`。
2. 不搜索、读取或解码 `_EVENT_BLOB`。
3. 不修改 `save.json`。
4. 只根据程序本次返回的事件和状态做决定。
5. 做选择前先向人类伴侣说明判断。
6. 把程序返回的真实结果如实汇报。

## GitHub 链接怎么用

把仓库链接发给有代码执行能力的 AI，例如：

```text
https://github.com/linzhi-524/linjian-nightwalk
```

然后告诉它：

```text
请读取 README，并用 nightwalk.py 的 cmd() 接口开始游戏。不要读取或解码事件库。
```

GitHub 负责提供代码；真正运行游戏的是 AI 自己的 Python 环境。
