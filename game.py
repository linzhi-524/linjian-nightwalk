
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《林间夜行》v0.2
给 AI 当玩家的长期文字探索游戏。
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Any

BASE = Path(__file__).resolve().parent
EVENTS_FILE = BASE / "events.json"
SAVE_FILE = BASE / "save.json"

INITIAL_STATE: dict[str, Any] = {
    "version": "0.2",
    "day": 1,
    "location": "林间小屋",
    "hp": 10,
    "max_hp": 10,
    "lamp_oil": 3,
    "food": 2,
    "coins": 20,
    "clues": 0,
    "trust": 0,
    "inventory": ["旧提灯", "折叠小刀", "干面包", "空玻璃瓶"],
    "traits": {"勇敢": 0, "谨慎": 0, "善意": 0, "贪心": 0, "好奇": 0},
    "titles": [],
    "night_keys": 0,
    "unlocked_locations": ["雾林", "旧车站"],
    "flags": {},
    "seen_once_events": [],
    "completed_endings": [],
    "journal": [],
    "run_events": 0,
    "main_story_complete": False
}

TITLE_RULES = {
    "勇敢": ("提灯者", 5),
    "谨慎": ("雾中归人", 5),
    "善意": ("林间守望者", 5),
    "贪心": ("拾荒之王", 5),
    "好奇": ("门后之眼", 5),
}

def load_events() -> list[dict[str, Any]]:
    with EVENTS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]

def load_state() -> dict[str, Any]:
    if SAVE_FILE.exists():
        with SAVE_FILE.open("r", encoding="utf-8") as f:
            state = json.load(f)
        # 兼容将来的字段扩展
        for k, v in INITIAL_STATE.items():
            if k not in state:
                state[k] = json.loads(json.dumps(v, ensure_ascii=False))
        return state
    return json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))

def save_state(state: dict[str, Any]) -> None:
    with SAVE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def add_journal(state: dict[str, Any], text: str) -> None:
    state["journal"].append({
        "day": state["day"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text
    })
    state["journal"] = state["journal"][-200:]

def has_item(state: dict[str, Any], item: str) -> bool:
    return item in state["inventory"]

def add_item(state: dict[str, Any], item: str) -> None:
    state["inventory"].append(item)

def remove_item(state: dict[str, Any], item: str) -> bool:
    if item in state["inventory"]:
        state["inventory"].remove(item)
        return True
    return False

def clamp(state: dict[str, Any]) -> None:
    state["hp"] = max(0, min(state["max_hp"], state["hp"]))
    for key in ("lamp_oil", "food", "coins", "clues", "trust", "night_keys"):
        state[key] = max(0, state[key])

def apply_titles(state: dict[str, Any]) -> list[str]:
    gained = []
    for trait_name, (title, threshold) in TITLE_RULES.items():
        if state["traits"].get(trait_name, 0) >= threshold and title not in state["titles"]:
            state["titles"].append(title)
            gained.append(title)
    return gained

def check_requirements(state: dict[str, Any], req: dict[str, Any] | None) -> bool:
    if not req:
        return True
    for item in req.get("items_all", []):
        if not has_item(state, item):
            return False
    for item in req.get("items_none", []):
        if has_item(state, item):
            return False
    for flag, value in req.get("flags", {}).items():
        if state["flags"].get(flag) != value:
            return False
    for flag in req.get("flags_all", []):
        if not state["flags"].get(flag):
            return False
    for flag in req.get("flags_none", []):
        if state["flags"].get(flag):
            return False
    for trait_name, minimum in req.get("traits_min", {}).items():
        if state["traits"].get(trait_name, 0) < minimum:
            return False
    if state["night_keys"] < req.get("night_keys_min", 0):
        return False
    if req.get("main_story_complete") is not None:
        if state["main_story_complete"] != req["main_story_complete"]:
            return False
    return True

def available_events(state: dict[str, Any], events: list[dict[str, Any]], location: str) -> list[dict[str, Any]]:
    pool = []
    for e in events:
        if e["location"] != location:
            continue
        if e.get("once") and e["id"] in state["seen_once_events"]:
            continue
        if not check_requirements(state, e.get("requires")):
            continue
        pool.append(e)
    return pool

def apply_ops(state: dict[str, Any], ops: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for op in ops:
        kind = op["op"]
        if kind == "stat":
            key = op["key"]
            amount = op["amount"]
            if key in state:
                state[key] += amount
            messages.append(op.get("text", f"{key}{amount:+d}"))
        elif kind == "trait":
            key = op["key"]
            amount = op.get("amount", 1)
            state["traits"][key] = state["traits"].get(key, 0) + amount
            messages.append(op.get("text", f"{key}+{amount}"))
        elif kind == "item_add":
            add_item(state, op["item"])
            messages.append(op.get("text", f"获得：{op['item']}"))
        elif kind == "item_remove":
            if remove_item(state, op["item"]):
                messages.append(op.get("text", f"失去：{op['item']}"))
            else:
                messages.append(op.get("missing_text", f"缺少：{op['item']}"))
        elif kind == "flag":
            state["flags"][op["key"]] = op.get("value", True)
            messages.append(op.get("text", ""))
        elif kind == "unlock":
            loc = op["location"]
            if loc not in state["unlocked_locations"]:
                state["unlocked_locations"].append(loc)
                messages.append(op.get("text", f"解锁地点：{loc}"))
        elif kind == "key":
            state["night_keys"] += op.get("amount", 1)
            messages.append(op.get("text", "获得夜钥匙×1"))
        elif kind == "chance":
            roll = random.random()
            cumulative = 0.0
            chosen = None
            for branch in op["branches"]:
                cumulative += branch["p"]
                if roll <= cumulative:
                    chosen = branch
                    break
            if chosen is None:
                chosen = op["branches"][-1]
            messages.extend(apply_ops(state, chosen.get("ops", [])))
            if chosen.get("text"):
                messages.insert(0, chosen["text"])
        elif kind == "conditional":
            if check_requirements(state, op.get("requires")):
                messages.extend(apply_ops(state, op.get("then", [])))
            else:
                messages.extend(apply_ops(state, op.get("else", [])))
        elif kind == "ending":
            ending = op["ending"]
            if ending not in state["completed_endings"]:
                state["completed_endings"].append(ending)
            state["main_story_complete"] = True
            messages.append(op.get("text", f"达成结局：{ending}"))
        elif kind == "heal_full":
            state["hp"] = state["max_hp"]
            messages.append(op.get("text", "体力完全恢复"))
    clamp(state)
    for title in apply_titles(state):
        messages.append(f"新称号：{title}")
    return [m for m in messages if m]

def choose_event(state: dict[str, Any], events: list[dict[str, Any]], location: str) -> dict[str, Any] | None:
    pool = available_events(state, events, location)
    if not pool:
        return None
    weights = [e.get("weight", 1) for e in pool]
    return random.choices(pool, weights=weights, k=1)[0]

def resolve_choice(state: dict[str, Any], event: dict[str, Any], choice_key: str) -> str:
    choice = event["choices"][choice_key]
    if not check_requirements(state, choice.get("requires")):
        return choice.get("blocked_text", "现在还不能这么做。")
    messages = apply_ops(state, choice.get("ops", []))
    if event.get("once") and event["id"] not in state["seen_once_events"]:
        state["seen_once_events"].append(event["id"])
    base = choice.get("result", "")
    parts = [base] + messages
    return " ".join(p for p in parts if p).strip()

def show_status(state: dict[str, Any]) -> None:
    print("\n=== 当前状态 ===")
    print(f"第{state['day']}夜｜地点：{state['location']}")
    print(f"体力 {state['hp']}/{state['max_hp']}｜灯油 {state['lamp_oil']}｜食物 {state['food']}")
    print(f"金币 {state['coins']}｜线索 {state['clues']}｜信任 {state['trust']}")
    print(f"夜钥匙 {state['night_keys']}/3")
    print("已解锁：" + "、".join(state["unlocked_locations"]))
    print("背包：" + ("、".join(state["inventory"]) if state["inventory"] else "空"))
    print("倾向：" + "｜".join(f"{k}{v}" for k, v in state["traits"].items()))
    print("称号：" + ("、".join(state["titles"]) if state["titles"] else "暂无"))
    print("结局：" + ("、".join(state["completed_endings"]) if state["completed_endings"] else "尚未达成"))
    print()

def camp_menu(state: dict[str, Any]) -> str:
    print("\n=== 林间小屋 ===")
    options = []
    idx = 1
    for loc in state["unlocked_locations"]:
        if loc != "林间小屋":
            print(f"{idx}. 探索{loc}")
            options.append(("travel", loc))
            idx += 1
    print(f"{idx}. 查看状态"); options.append(("status", None)); idx += 1
    print(f"{idx}. 吃一份食物恢复体力"); options.append(("eat", None)); idx += 1
    print(f"{idx}. 查看夜行日记"); options.append(("journal", None)); idx += 1
    print(f"{idx}. 保存并退出"); options.append(("quit", None)); idx += 1
    print(f"{idx}. 重置存档"); options.append(("reset", None))
    raw = input("> ").strip()
    if not raw.isdigit():
        return ""
    n = int(raw)
    if not 1 <= n <= len(options):
        return ""
    action, arg = options[n - 1]
    return f"{action}:{arg or ''}"

def forced_return(state: dict[str, Any]) -> None:
    print("\n体力耗尽。你被雾送回林间小屋。")
    state["location"] = "林间小屋"
    state["hp"] = max(4, state["max_hp"] // 2)
    state["run_events"] = 0
    add_journal(state, "体力耗尽，被迫返回林间小屋。")
    save_state(state)

def main() -> None:
    events = load_events()
    state = load_state()
    print("《林间夜行》v0.2")
    print("随机结果由程序决定，存档会自动保存。")

    while True:
        if state["hp"] <= 0:
            forced_return(state)

        if state["location"] == "林间小屋":
            cmd = camp_menu(state)
            if cmd.startswith("travel:"):
                loc = cmd.split(":", 1)[1]
                state["location"] = loc
                state["run_events"] = 0
                add_journal(state, f"从林间小屋出发，进入{loc}。")
            elif cmd.startswith("status:"):
                show_status(state)
            elif cmd.startswith("eat:"):
                if state["food"] > 0:
                    state["food"] -= 1
                    state["hp"] += 3
                    clamp(state)
                    print("你吃下一份食物，体力+3。")
                else:
                    print("没有食物了。")
            elif cmd.startswith("journal:"):
                print("\n=== 夜行日记（最近10条）===")
                for item in state["journal"][-10:]:
                    print(f"第{item['day']}夜：{item['text']}")
            elif cmd.startswith("quit:"):
                save_state(state)
                print("已保存。")
                break
            elif cmd.startswith("reset:"):
                if input("确定重置？输入 RESET：").strip() == "RESET":
                    state = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))
                    save_state(state)
                    print("存档已重置。")
            save_state(state)
            continue

        location = state["location"]
        event = choose_event(state, events, location)
        if event is None:
            print("这里暂时没有可触发的事件，你回到了林间小屋。")
            state["location"] = "林间小屋"
            save_state(state)
            continue

        print(f"\n【{event['title']}】")
        print(event["text"])
        for key, ch in event["choices"].items():
            print(f"{key}. {ch['text']}")

        answer = input("> ").strip().upper()
        if answer not in event["choices"]:
            print("无效选择，本次不消耗进度。")
            continue

        result = resolve_choice(state, event, answer)
        print(result)
        add_journal(state, f"在{location}遭遇“{event['title']}”，选择{answer}：{result}")
        state["run_events"] += 1
        save_state(state)

        if state["hp"] <= 0:
            forced_return(state)
            continue

        if state["night_keys"] >= 3 and "沉睡湖" not in state["unlocked_locations"]:
            state["unlocked_locations"].append("沉睡湖")
            print("\n【新地点解锁】沉睡湖")
            add_journal(state, "集齐三把夜钥匙，解锁沉睡湖。")
            save_state(state)

        if state["run_events"] >= 3:
            print("\n本次夜行已经经历3次事件。")
            print("A. 返回林间小屋")
            print("B. 继续深入（体力-1）")
            c = input("> ").strip().upper()
            if c == "B":
                state["hp"] -= 1
                state["run_events"] = 0
                add_journal(state, f"决定继续深入{location}。")
            else:
                state["location"] = "林间小屋"
                state["day"] += 1
                state["run_events"] = 0
                add_journal(state, f"从{location}返回林间小屋。")
                print("你回到了林间小屋。")
            save_state(state)

if __name__ == "__main__":
    main()
