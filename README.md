# 林间夜行 v1.1：调查推理版

一款面向 AI 玩家或命令行玩家的长期文字探索游戏。玩家在林间小屋醒来，通过自由调查、使用物品、跟踪、倾听、拼合、线索板与主动推理，逐步解开雾林、旧车站、影子和沉睡湖之间的秘密。

## 这一版改了什么

- 自动剧情负责制造现场，不再频繁弹出 A/B/C。
- 玩家通过 `inspect`、`open`、`take`、`use`、`give`、`follow`、`listen`、`wait`、`adjust`、`combine` 主动推动调查。
- 新增线索板：`board`、`pin`、`connect`、`deduce`。
- 四个章节的关键里程碑必须由玩家完成证据链和推理后触发。
- 新增怀表时间谜题、物品取得步骤、路线态度决定和资源风险。
- 普通随机事件自动结算，但会留下可以继续调查的痕迹。
- 仅真正改变路线的终局保留 A/B/C/D 选择。
- 支持 v0.8 / v1.0 存档迁移。

## 运行要求

- Python 3.10+
- 无第三方依赖

## 快速开始

```python
import nightwalk

print(nightwalk.cmd("options"))
print(nightwalk.cmd("open 门"))
print(nightwalk.cmd("travel 雾林"))
print(nightwalk.cmd("inspect 无脸旅人"))
```

第一次调用 `cmd()` 时会自动播放序章。存档会写入同目录的 `save.json`。

也可以直接在命令行运行：

```bash
python nightwalk.py options
python nightwalk.py "travel 雾林"
python nightwalk.py "inspect 无脸旅人"
```

## 主要指令

```text
options                         查看当前可操作现场
status / story                  查看状态和章节目标
travel 雾林                     前往地点
inspect 树皮                    调查对象
open 门                         打开对象
take 白色字片                   取得物品
use 空白车票                    使用物品
give 白色字片 无脸旅人          交付物品
follow 白鹿                     跟踪角色
listen 广播                     倾听
wait 下一班列车                 等待现场变化
adjust 旧怀表 00:13             调整物品 / 解谜
combine 车票残角 空白车票       拼合物品
board                           查看线索板
pin 半句纸条                    固定线索
connect 姓名时刻表 | 广播中的遗忘物
                                连接两条证据
deduce 列车运送名字和记忆       主动提出推理
trust 影子 / confront 影子      关键态度决定
light; explore                  点灯并触发随机夜行插曲
return                          返回小屋
journal                         查看日记
save                            手动保存
```

## 核心循环

```text
自动剧情出现
→ 玩家观察现场
→ 选择调查动作
→ 获得物品或线索
→ 在线索板连接证据并主动推理
→ 自动剧情反馈与章节推进
→ 决定下一处地点或是否继续探索
```

设计比例约为：20% 自动剧情、60% 调查操作、20% 关键决定。

## 结局

- 归途结局
- 守夜结局
- 终点结局
- 隐藏结局：林间入口

隐藏结局需要完成全部主要人物线、归还无脸旅人的名字、拼完整车票，并在终局拒绝独自登车。

## 测试

```bash
python -m unittest discover -s tests -v
```

## 存档

`save.json` 会在运行后自动生成，已加入 `.gitignore`，不会被默认提交到仓库。
