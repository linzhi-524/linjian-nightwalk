#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《林间夜行》v1.1 调查推理版

在 v0.8 的资源、存档和旧事件基础上，加入：
- 自动序章与章节开场
- 关键物品/返家/人物线/里程碑自动剧情
- inspect / use / follow / listen / combine 调查指令
- 自由调查、线索板、主动推理与小型谜题
- 自动随机事件与少量关键路线决定
- 三个普通结局与一个隐藏结局
"""

from __future__ import annotations
import base64
import gzip
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
SAVE_FILE = BASE / "save.json"
VERSION = "1.1"

INITIAL_STATE: dict[str, Any] = {
    "version": VERSION,
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
    "main_story_complete": False,
    "pending_event": None,
    "last_work_day": 0,
    "event_last_seen": {},
    "night_seen_events": [],
    "lamp_history": [],
    "last_lamp_refill_day": 0,
    "lamp_shop_price": 3,
    "rest_count": 0,
    # v1.0 narrative fields
    "prologue_complete": False,
    "chapter": 0,
    "visited_locations": [],
    "seen_auto_scenes": [],
    "auto_scene_last_seen": {},
    "completed_character_lines": [],
    "choice_events_this_night": 0,
    "shadow_home_pending": False,
    "final_mode": False,
    # v1.1 investigation / deduction fields
    "evidence": [],
    "board_pins": [],
    "board_links": [],
    "solved_deductions": [],
    "wrong_deductions": 0,
    "waited_scenes": [],
    "route_decisions": {},
    "max_field_actions": 8,
}

TITLE_RULES = {
    "勇敢": ("提灯者", 5),
    "谨慎": ("雾中归人", 5),
    "善意": ("林间守望者", 5),
    "贪心": ("拾荒之王", 5),
    "好奇": ("门后之眼", 5),
}

CHAPTERS = {
    0: ("序章", "提灯醒来"),
    1: ("第一章", "被拿走的名字"),
    2: ("第二章", "不存在的列车"),
    3: ("第三章", "影子先到终点"),
    4: ("第四章", "沉睡湖"),
    5: ("终章", "门与归途"),
}

STORY_EVENT_IDS = {
    "f_deer", "f_faceless", "f_door", "f_mark_reply", "f_deer_return",
    "f_name_found", "f_root_bargain", "s_clock", "s_ticket", "s_radio",
    "s_case", "s_oldman", "s_staff", "s_midnight", "s_radio_reply",
    "s_case_night", "s_final_ticket", "l_gate", "l_guard", "l_depth",
    "l_after"
}

ITEM_DESCRIPTIONS = {
    "旧提灯": "灯芯偶尔自行发亮，像在替某个看不见的人指路。",
    "折叠小刀": "刀刃不算锋利，但足以割断细绳和藤蔓。",
    "干面包": "硬得像木片，仍能在最糟的时候撑住一晚。",
    "空玻璃瓶": "瓶底有一圈洗不掉的灰白雾痕。",
    "空白车票": "没有始发站、终点和日期，纸面摸起来却有余温。",
    "半句纸条": "上面只有一句：别让列车抵达……",
    "白色字片": "薄得像一层脱落的树皮，上面浮着不完整的姓名。",
    "黑羽标记": "羽毛表面没有光泽，握久了会变得微温。",
    "旧怀表": "指针停在一个不存在的时刻。",
    "车票残角": "边缘焦黑，目的地一栏被撕掉了。",
    "拼合车票": "残角与空白票严丝合缝，背面显出一条水下铁轨。",
    "影子的行李牌": "写着你的名字，背面却登记着另一个抵达时间。",
    "生锈钥匙": "齿纹已经模糊，像是开过一扇不存在的门。",
    "守夜人的徽章": "背面刻着一句被磨平的话。",
    "湖边石片": "表面有水波一样的纹路，离开湖边也不会干。",
    "银色铃铛": "摇动时没有声音，却能让附近的雾散开一点。",
    "蓝火柴": "燃烧时不会发热，只会照出被隐藏的轮廓。",
}


EVIDENCE_DEFINITIONS: dict[str, dict[str, str]] = {
    "half_note": {"name": "半句纸条", "text": "纸条警告：别让列车抵达……，背面压着铁轨般的凹痕。"},
    "door_no_tracks": {"name": "门外没有脚印", "text": "敲门声真实存在，湿泥上却没有来去痕迹。"},
    "feather_to_forest": {"name": "指向雾林的黑羽", "text": "门槛上的黑羽朝向雾林，像一枚路标。"},
    "faceless_request": {"name": "无脸旅人的请求", "text": "旅人请求你把他从别人的记忆里找回来。"},
    "bark_missing_name": {"name": "树皮上的残缺姓名", "text": "雾林树皮上的姓名被整齐拿走了一部分。"},
    "root_train_truth": {"name": "倒生树根的证词", "text": "树根声称名字被一列没有终点的列车带走。"},
    "black_feather_station": {"name": "黑羽指向车站", "text": "黑羽标记与旧车站存在明确联系。"},
    "watch_0013": {"name": "零点十三分的怀表", "text": "旧怀表总会倒走并停在零点十三分。"},
    "timetable_names": {"name": "姓名时刻表", "text": "旧车站时刻表写的不是车次，而是一列列姓名。"},
    "broadcast_forgotten": {"name": "广播中的遗忘物", "text": "广播说：遗忘物不是失物，遗忘物是乘客。"},
    "hidden_platform_cargo": {"name": "隐藏站台的行李", "text": "列车车厢里装着姓名、笑声与旧照片，没有乘客。"},
    "ticket_water_track": {"name": "车票背面的水下铁轨", "text": "拼合车票显出一条经过雾林、车站与沉睡湖的线路。"},
    "shadow_checked_in": {"name": "影子已检票", "text": "时刻表显示你的影子比你更早检票。"},
    "staff_knows_feather": {"name": "站务员认识黑羽", "text": "站务员向黑羽标记行礼，显然认识它原来的主人。"},
    "deer_on_rails": {"name": "铁轨旁的白鹿", "text": "白鹿的蹄印让枕木浮出被遗忘的姓名。"},
    "shadow_route_lake": {"name": "影子的近路", "text": "影子走过不存在的近路，终点指向沉睡湖。"},
    "shadow_luggage_tag": {"name": "提前抵达的行李牌", "text": "行李牌写着你的名字，却登记为三年前已经抵达。"},
    "lake_child_tracks": {"name": "童年的湖岸脚印", "text": "湖岸最小的一双脚印属于你的童年，只向水中走去。"},
    "lake_station_sign": {"name": "湖底的林间小屋站牌", "text": "沉没站牌把林间小屋标成一座车站。"},
    "guardian_lamp_owner": {"name": "提灯原主人的决定", "text": "提灯属于第一个拒绝独自登车的人。"},
    "ticket_holder_decides": {"name": "由持票者决定的终点", "text": "拼合车票的终点不固定，而由持票者决定。"},
    "lamp_handover": {"name": "小屋钥匙的交接", "text": "提灯记忆中，上一任主人把小屋钥匙交给了你。"},
}

DEDUCTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "name_taken_by_train": {
        "title": "名字被列车带走",
        "aliases": ["名字被列车带走", "列车拿走了名字", "名字被车带走", "无脸旅人的名字在列车上"],
        "requires": ["faceless_request", "bark_missing_name", "root_train_truth"],
        "flag": "deduced_name_train",
        "scene": {"id": "deduce_name_train", "title": "推理成立·被拿走的名字", "text": "树皮缺口、无脸旅人的请求与倒生树根的证词终于扣在一起：名字并非自然遗失，而是被那趟列车作为『遗忘物』带走。"},
    },
    "train_carries_names": {
        "title": "列车运送名字和记忆",
        "aliases": ["列车运送名字和记忆", "列车的货物是名字和记忆", "列车运送遗忘物", "乘客其实是名字"],
        "requires": ["timetable_names", "broadcast_forgotten", "hidden_platform_cargo", "ticket_water_track"],
        "flag": "deduced_train_cargo",
        "scene": {"id": "deduce_train_cargo", "title": "推理成立·不存在的乘客", "text": "姓名时刻表、广播与行李车厢指向同一个答案：列车运送的不是人，而是被现实抛下的名字、记忆与存在过的证据。"},
    },
    "shadow_keeps_memories": {
        "title": "影子在替我保管记忆",
        "aliases": ["影子在替我保管记忆", "影子替我收集记忆", "影子先到终点是为了我", "影子不是冒名者"],
        "requires": ["shadow_checked_in", "staff_knows_feather", "deer_on_rails", "shadow_route_lake"],
        "flag": "deduced_shadow_guardian",
        "scene": {"id": "deduce_shadow_guardian", "title": "推理成立·先到终点的影子", "text": "影子并没有偷走你的位置。它提前检票、联系站务员，并沿白鹿留下的轨迹前往沉睡湖，是为了替尚未准备好的你保管被删除的过去。"},
    },
    "cottage_is_transfer": {
        "title": "林间小屋是中转站",
        "aliases": ["林间小屋是中转站", "小屋连接现实和遗忘", "小屋是一座车站", "小屋是入口"],
        "requires": ["lake_child_tracks", "lake_station_sign", "guardian_lamp_owner", "ticket_holder_decides", "lamp_handover"],
        "flag": "deduced_cottage_gate",
        "scene": {"id": "deduce_cottage_gate", "title": "推理成立·门与站台", "text": "小屋从来不只是避难所。它是一座藏在现实与遗忘之间的中转站，而提灯、钥匙与车票共同决定这扇门向哪一边开启。"},
    },
}

CONNECTION_HINTS: dict[frozenset[str], str] = {
    frozenset({"bark_missing_name", "root_train_truth"}): "树皮缺失的不是文字碎片，而是被列车带走的名字。",
    frozenset({"timetable_names", "broadcast_forgotten"}): "姓名就是时刻表上的『乘客』。",
    frozenset({"staff_knows_feather", "shadow_checked_in"}): "站务员认识的黑羽主人，很可能就是提前检票的影子。",
    frozenset({"lake_station_sign", "ticket_holder_decides"}): "当小屋成为站名，终点便不再是固定地点。",
}

PROLOGUE_SCENES = [
    {
        "id": "prologue_wake",
        "title": "序章·提灯醒来",
        "text": "你在林间小屋的木床上醒来。窗外没有天色，只有雾贴在玻璃上缓慢呼吸。桌上放着一盏旧提灯、一张空白车票，以及一张只写了半句的纸条。",
    },
    {
        "id": "prologue_note",
        "title": "半句纸条",
        "text": "纸条上写着：『别让列车抵达……』句子在这里断掉，墨迹却仍然潮湿。你翻过纸背，发现上面压着一道像铁轨又像缝合线的凹痕。",
    },
    {
        "id": "prologue_knock",
        "title": "门外三声",
        "text": "屋外响起三下敲门声。你提灯走到门边，敲门声停了。门外的湿泥平整得没有一枚脚印，只有一根黑羽贴在门槛上，羽尖朝向雾林。",
    },
]

LOCATION_SCENES = {
    "雾林": [
        {
            "id": "intro_forest",
            "title": "雾林·没有脸的人",
            "text": "第一次踏进雾林时，白鹿在两棵树之间回头看你。更深处站着一个没有脸的人，他用手指在自己本该有嘴的位置写下一个字：名。树根倒悬在雾中，像无数只伸向天空的手。",
        }
    ],
    "旧车站": [
        {
            "id": "intro_station",
            "title": "旧车站·错误的时间",
            "text": "站厅里的钟停在零点十三分，锈轨却仍在轻轻震动。广播报出一班不存在的列车，售票窗口后没有人，玻璃上却留着刚被擦过的指痕。",
        }
    ],
}

STATION_CHAPTER_SCENES = [
    {
        "id": "chapter2_station_open",
        "title": "第二章·不存在的列车",
        "text": "你再次站在旧车站里。空白车票在口袋中自行发热，停住的钟向后跳了一格。广播里有人用你的声音说：『请遗失物提前候车。』",
    }
]

LAKE_INTRO_SCENES = [
    {
        "id": "lake_intro_face",
        "title": "第四章·沉睡湖",
        "text": "湖面映出的不是你现在的脸。几段像被剪掉的过去依次浮起：一扇没有打开的门、一只握住你手腕的影子、一张被撕去姓名的合照。",
    },
    {
        "id": "lake_intro_lamp",
        "title": "提灯第一次熄灭",
        "text": "旧提灯没有风地熄灭了。灯芯冒出的白烟落向湖面，没有散去，反而组成一句倒写的话：『影子已经替你抵达。』",
    },
    {
        "id": "lake_intro_train",
        "title": "水下列车",
        "text": "湖底忽然亮起一排车窗。列车从水下无声驶过，车厢里坐满没有脸的乘客，每个人怀中都抱着一块写有名字的行李牌。",
    },
]

AMBIENT_SCENES = {
    "雾林": [
        {"id": "a_fog_bells", "title": "雾里的铃声", "text": "远处传来一串没有声源的铃响。白鹿从雾后穿过，鹿角上挂着一小片写有陌生姓氏的纸。你记下一处新线索。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
        {"id": "a_fog_breath", "title": "树洞的呼吸", "text": "一棵空心树随着你的呼吸一起收缩。你靠近时，它吐出一阵带着旧纸味的风，里面夹着一句：『名字不是丢的，是被带走的。』", "ops": [{"op": "trait", "key": "好奇", "amount": 1}]},
        {"id": "a_fog_lampmoth", "title": "灯蛾", "text": "一群灰白灯蛾围着提灯旋转，最后落成一枚指向旧车站的箭头。片刻后，它们又像灰烬一样散开。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
        {"id": "a_fog_bread", "title": "完好的纸包", "text": "你在树根间找到一份没有受潮的食物。纸包上写着明天的日期。", "ops": [{"op": "stat", "key": "food", "amount": 1}]},
    ],
    "旧车站": [
        {"id": "a_station_labels", "title": "姓名行李牌", "text": "行李转盘自行运转，一块块姓名牌从黑暗里滑出，又在你读清前翻到背面。你抢先记住了其中一个。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
        {"id": "a_station_window", "title": "空车经过", "text": "一列没有车头的空车从站外掠过。每扇窗里都映着不同年龄的你，只有最后一扇窗是空的。", "ops": [{"op": "trait", "key": "勇敢", "amount": 1}]},
        {"id": "a_station_coin", "title": "迟到的找零", "text": "售票机忽然吐出三枚旧金币，屏幕上显示：『记忆已退款。』", "ops": [{"op": "stat", "key": "coins", "amount": 3}]},
        {"id": "a_station_note", "title": "广播间隙", "text": "广播噪声短暂停止，一个孩子在里面念出半个名字。那半个名字和白色字片上的笔画相同。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
    ],
    "沉睡湖": [
        {"id": "a_lake_ripple", "title": "慢一拍的倒影", "text": "你已经停下，湖里的倒影却又向前走了一步。它回头望你，把手指放在唇前。", "ops": [{"op": "trait", "key": "谨慎", "amount": 1}]},
        {"id": "a_lake_ticket", "title": "漂来的票根", "text": "一张泡不烂的票根漂到岸边，上面盖着『未独自登车』的红章。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
        {"id": "a_lake_names", "title": "水下低语", "text": "湖底传来许多人同时念自己名字的声音。每念完一个，水面就亮起一颗很小的星。", "ops": [{"op": "stat", "key": "trust", "amount": 1}]},
    ],
}

HOME_SCENES = [
    {"id": "home_deer_window", "title": "窗外的白鹿", "text": "夜里，小屋窗外站着那只白鹿。它没有敲窗，只把额头贴在玻璃上。第二天，窗台多了一道由白色笔画组成的路。", "ops": [{"op": "stat", "key": "clues", "amount": 1}]},
    {"id": "home_three_knocks", "title": "又是三下", "text": "你刚放下背包，门外又响起三下敲门声。这一次，第三声来自屋内的衣柜。", "ops": [{"op": "trait", "key": "勇敢", "amount": 1}]},
    {"id": "home_lamp_trim", "title": "被修好的灯芯", "text": "你睡醒时，提灯的灯芯已经被人修剪整齐。桌面上留着一小圈湿脚印，却只从桌边走到墙里。", "ops": [{"op": "stat", "key": "lamp_oil", "amount": 1}]},
]

FINAL_CHOICE_EVENT = {
    "id": "final_choice",
    "location": "沉睡湖",
    "title": "最后一班列车",
    "text": "湖面裂开一条发光铁轨。列车停在岸边，车门内是全部被遗忘的名字和记忆。守夜人把旧提灯交回你手中，影子站在最后一节车厢旁，等待你作出唯一一次真正改变路线的决定。",
    "once": True,
    "choices": {
        "A": {"text": "让所有被遗忘的名字回到现实", "result": "你把车票撕成无数发光的碎片。每一片都带着一个名字穿过雾，回到现实中仍有人等待的位置。", "ops": [{"op": "ending", "ending": "归途结局"}]},
        "B": {"text": "留下，接替提灯原本的主人", "result": "你没有上车。旧提灯在掌心重新亮起，从此每个误入雾中的人都会先看见小屋窗口的光。", "ops": [{"op": "ending", "ending": "守夜结局"}]},
        "C": {"text": "独自登上不存在的列车", "result": "车门在身后合拢。全部记忆回到你身上，而现实里关于你的痕迹一件件变空。", "ops": [{"op": "ending", "ending": "终点结局"}]},
        "D": {"text": "拒绝独自登车，让小屋成为新的入口", "result": "你把脚留在岸上，也没有让列车空着离开。小屋的门在现实与遗忘之间同时打开，名字、记忆与仍愿意等待的人第一次可以双向来往。", "requires": {"flags_all": ["hidden_ready"]}, "blocked_text": "隐藏条件未满足：需要完成全部人物线、归还无脸旅人的名字并拼完整车票。", "ops": [{"op": "ending", "ending": "隐藏结局·林间入口"}]},
    },
}

_EVENT_BLOB = """ABzY8xqL!u0{`t@S#u&swtnwl(b2E=OxWG_Jos&9e#VU(1eQ>XXbE}%xv#Io5zs<x5{njugg^_DT4-UB8cB#n{Fj-^tg0vfg?mmWLI|pgrPw52M~9=k7BVZ($&=@NXZ!8d>(_67G1=^9tL4p4uit$4*SBxJ#cQTtOcsY7F8vq$>-Fp3*#F_Wc^V&^F-#ff=Gc?$>YR1T=&1jMymL=?V~_V7X2+bVenTi`$ZCZ|f=#zg|Kq6NmAxx8;TK9J5<Vy1l2F|j<8FAEWMY3*R>)yq-uo()LsIFSL_$JkpC*t0<NW;iQ&Y26^OOlE{V-j)`1dFOY#Na4?2@BG<85}&X0k8LvAZz1RK1XDUKp);5cZh$<KxOa{P)|Ff3b(~ccx~ImMPPd*V)~lZE$_o)c!k4zs26bpZo5wKYpup@8O$hY+rI0X>17=Q9R!!i8No<)-TZf60KP@eVN^1bSVBPd**}bSN8dH3-FDqPZ{T}3l^OD_o|OPe41FQiG|cR-@j3O@b_=~`2>f}Xzu(C<hV+Xy(;4>T>bA?UCgd;5_9esPfI{+q38rc!`_gbU#0sy5-gDQpmcr9_E-@%%-HBY`>_k6|K)8*steV164?36+h<AjS6WXr-+jE(^hIy}p(?oo`=oX*x#Ki*tRcVX)d7f8F6Q)zFhzoE5W0!LZQHt)ur1rUg`g@EQYPTTjHG;;E`{FoxY++xTWs<3olwfsa71+F#EhTZFR3j#JV2KG;?fD8U9dBYXLKn=f&sc5#B;2ANivb4(P7Rw|IuJI&-F(Qm^!_>>yH{UbH?|o)3VPRr>&n13l`82KA5K4pZmoKCj>m{uq~Jd&I)ANOQR_bR%oH*zZT547X5)Q6OLjx%$qH3_g*(f0nx2G(Bt19{?_=sH&)aSetJD)oU@x67eATI?`M%T?_M=M-L8e%te<++!brFxuN{+>ZQx1aZbdGBY1hU0b+T0e)d8LtlfcYQ8VHCRd-8^lzpg{`5;xNF;hyL}6-q}mm{JvCd=}w~be-qV!$~Jbw}s+z`xFMcnP#lk>HannpJ#s?$?P!A8;sKmBjX*uaF6Rhc)>|F-P9e{zgtis*bNq|#iXEOys=mfY<XX)9gV;Dco^oBQZ7mZ>q0f$!p{mvqJNb{R_Shz?j|QmtN%e$<wHa0d{1=W)W5RiQRe?aXm_ei*aI_;LOqiTXQZ|`I;H$?+7#lVD(VK>0JYfZzYJ=+e7Fn3Yr?hg@4MB)zkilw)~SW7Du!e=Am#j=@?6~$Pqs+TqkWvwjT_(y{^a9vR$dkFt90KhW%GK(Qs)z-d8C0Wd#H^V?4~K3$uVk0Pr+DIA?-l*FNe)!>Q(=8u7N&<!ZTU}6^!n$w(DPTk?!9Kl_DHg<meQPeP9(hvPk#_Y<zjGEY)^MVy^|*=}`-#E1RU^q+gHWm$Z&dc+8gvxkmPurC1oWn-^tE4jiA;MsI|opYFy<_=pr;v>XRI($ES>xbXpWR<orWfbLz#Lqhhh!bg4cZggkz4?lKNn~-_EC32Lgn>?wI==Y9SZEBg!5RbOe%GGXkb+H@;k)t7O-~p-T1z|&-XCMUiNScv?L}(kImc&q5Tw4^^Z|KH7Nu=viytu3i7_Hw3#f;>NBV-$1Meqm@ggZHLrCSTIndYs(m^4hurs)pHSmht0-<-tXvm4Oeq+m^|f5sD&^2ty?b1cfxEGHOL+WcckfWDQ6x0*`B418ygN&}yt<c^bI9(Y8G9E+~=cD;f4gLLx_eP~4|+4m4%T=cj_R|Z~z=h252EbyNa%4MM%<v*xLhlnJ^LJFos5_wIt`yO=&P?F14l8@8G841T|H4F3NfXTR!oK8SatGh{u?32Afo4ok>PV_Fe(60?gJ{R42{=87if^c|&sB!;_;M)#*;5Tmvhy9-~6JJ^UQr14T>W&sy0<5`-II;$6;{c_4cJ;$mIaVMWS*dU$lrjny&R&9qK_Uc*XB*6+KPqv$Tm!=xapwJ7kW|9mp7h1V&0`W-5i=mNZi%yksC6+R9oO{W&+J#f=L#!YR%~byeqRGTEFICUb&_47zTr7>l$G)BfM@nGLj#`q+6+t&<OHC}1Mbyt(16BH;3OeC_v0mlV$ec&B9VR1u*kso+v6e)O3n#or*P+!7pp=s2!v2ue40p${uQZOhCgIIh*&4+8Hc(cD@{OY)@m`?9fn`bcC*838!@IdJbA0F9!{G~wjRZ;lsYFnd7&CcKXX1T-_;a!Lv|gN$E6xPFR#0VVp6Q^!&|WZ<ZZW9TSfIS;ip?6x^<6&wp0=?%es|B;=iJs89pG5u9EDc8iVmU(i<N+x>Su_8r+FmcX(;28iPhik+ufA@t58_;e$4sXkd$k_hGS#&p9wZ96fZ>y<^Tt^7gH~b*ZH>Eqf65W-Nhb$=wauzhWpau7r^3fJxh!ZU|U78-C!*Yp2tr)8Wy(&7m&Wi$OWL4+PO5g-}b<6_<3I1T}Y}l~>#sy~@&$R_k0}rZ#b|k?JMFG5G?mDk-q+y0lp3@ji(4B+}f%hAXh}Jb+b?Z5;?u|FTdiB1oLaPz+VE>B$q%EuSoj?BW;rm!+lX^NCwUk>K7VzC0orekV<wAshoAR9uohYm@Ci?KX(<o41n^LP~OLaPDz8l6;m{2oD^@3M(Fj?H13R24=2$B<gcLPm=F^ypg0d5G6~;-_zYVw;xqCe~>@P6ur*!&_)tIrs)ImYd}u9rL^;<*~8D}co+AJVk*RGqfI&K@H446@pxJc1O4C%2fBx>U_}!!ypo@50ID<|?S@&a-C>?HO<Gv#kSs$UOxvSABf4@3p|R*=g-B1HW5e#!+y+ftfc{OFQt0nzk;^(180q9Q$?dg_+^V|pkw3ff&x#j=^A59!aqJZ6?Ik&Kj}7GMc^^-pyLBTC79R1HFpNZ-4DeWf6AX1=6_5{NB`TL!CI1!bz@^%Y3i#+Ow)jU6+KGUUxLk*A;7XCBAk7?-V(}T8VhwsJ;}Z3_;C4)+ElJ>2>r{T%_NN-BOmil?y;no8Iae<3mU6fB^0R`W$Ni<H4U*mBm>4{X_R3C8C~u-?b7z<5DC+S@WHv}?Lklno9plz4dH(H8kfTc}Qf;J0{@a-x8UQ<EwoDr=#`%$-u$@BDd-T1=!@_+{EN=tFr0ZLuc*d7bRcT^OL9%{1xlIyzSbP$W!Qww7gSxyaJ6${!8MJ#EI1(?uj5qM9zTenPCdCq#KOX`!$Q#>IF2`8{6l6Fsxf@c9Vg@bGtsI+${K;muyjR|XJ=n?P4V9+LYhpR6z1!%OUoLOKZsTd!I&&7arCR;KFxX5p3-<o8_`VNHZU2weYU@3-9(87>Fk?(jEUlpF155k8By%M1+`u2yN)l;!ODJaeD`*`?LSPy;yn+1a)0gPgoFxJ#X!F!s*Z^+9_;f3W3aH-;;zB+QAqIH2NtXP>4~Wy5TZO!(VNDD<3{G|O{e;1_Wcl@Ibb#d+I;Nqt2C1>QLh2moEPXxzMPBxXX<!HRC|)6AOy)+XxT4l1^bsQoU8STXaMgukfCpGe**po~YV0?f1RXXcdsh%5Vs3pJz2a_tcztN{7bTow-e~*qVzNZEaU1+pkUt;ie(lGvzYCTD+9ywm*^J--!Rf^Tr+MQ^8pF^gaui3%mXTCCSdq6^V0W{6DsfW$!c`u9WmIUujrdX~Ce`jV_B*+c@eoj&y(UXvg;IzQj-jaxPkCWLkLCtIZO$-jwm9@_9$lgQ>tATd-%%Q1SrIsHqgTXRCWm?AO6W9s^a=sC*(SX{1o1FY>pdg4mkpa-BZ7)8bWys_lT;eE4AZ(I+^qtJnz&s>*bVkYd!EW*!TIKq-b^AyK46gPk>7fRmsre>&E#0HS$a+NW8qAs5|wUq?SdPGJB_Y_snZDBYE*0jB?xmvk4n@XMqTN44@A5kB>r|!j)%1Zud<7995hGjgC#+-ezKINU;SdDqK6k}O~yIH%)*>Pl=)K)i)2@DK!$=2+;0c$WOwv+3<$LYp<EtdDgX(efiM=TVc-iynl-d!c#Oe*C>@dqG<Zwy-9vWT0mt6E6$4BsPxwmNQ(#@~0R8$dWMz=V#Bw7;Unf@&48R<f{Cf;N>`?$RZDj_w$#k#s?<r8-E&`j+AVedY5P7gjh(Cx~ao!TS&$b`{y@yiqL4?u~M}f7mD6#AV1(hxzGvwdX4(|^KfzWv(caf6EzD~N{7mq4Kz&KPTXdO?_dw3b4Mha}596U^JC`$If7BGN(8f(#v#e>mxY;pgm30FOZS`y)E&OB<8u(8ot&N&HhfmKF#3PLG6M0X>v;4#7=>kp=nj-H)X{hvW{EDHifOzhFjVMhZ1p2X8XS3m=tI~*=|QP#L?z%E=Xz!Qx*8pmc5zwKlazkM@_;LLzeOl9Y1lkxsa0mD_rX;s8~cSo?zYIPWXHrn1B&Al2SjVyG=Q%~xxJu0NmHF0APo~-AeAC!4wNK35(v`JV6L>@IHJN<O|RF8XLC5zA%&l6WWklFNU@}9@9@rjU#kNP5w*$w?<R!n98c3?lRSrXzIcpnrf$gXRCm!6VuETM=qs#eTIAcbuIz`7(@K$Ckn35FE$tqGN*KarzBsg9POn5IrC(ZutWWaBjcnZ|B}Vo*%w;Z%EpF-@w{UX}N|5%_k)6guaWB|VLuNYyXm`L>e9<w`IF=?3czfGm&Q$ZLBF&=Y%~9G$>j{>pdX{q)^;C|^(3<TamA4&u+Gjz}P_2X@LY(r5uE5i6)0TrfqSc;*t_H`49bmH`KBlq;zi-%eT-qYj*(Wz}&KYJp0jThROE^&9@=u#@cS!wfR14a7;uatw4a0L=7ErH-a-aG0k)G*#H^S~y_AcoynNHnQSzT0D!9@Sy@I!>-puK}uOHR_DrLhW^0{YHO<=UJjU4_OV_LD77%&u^utOQ~&wTsMbVj8cK>(rP>YytCw}=2Y2BnX&QKN8#Q_btE~F14+KC`v8ER!xXE!64g(L{VcIF{=542}o3}4I>t+z;V1^|cY^nyLrrHobBfh*?_Hng=_+s#=LMU`>AN|7YE_|Mx+{e}v@b^#(Tet8)>ANkGP3e#ZAY+;bZ-ub<;LKMgp4PBfTro&8TcEC>MH)YmUF$DOt?#Bb3nSa!*GUOa>QEwpGfX$t!hkJhR}8%f2P-rg8nU9&G}7Q?g=WJD&dj{rMWYrl2_KV8<c~_6(-qk}k>>8W7ANpzN68F5uF7thH%`r(EvDY(9YW@Tv{X2SgOw&q3X(2SBHL*ci@{B-O|_M#v155BP4k8SI9)u7itAD|^#!hAMZ27vc<~BIAezzRtrG6?%>({X@x6N}Rpr+z<Zy?+;-^y`mxl1JlZNnaNDi*1uOFD$f`x6NIFRJW?n%<dF5{xgkDaLU<B-Z$JzaoF$(#JA)&^|b&_MIIJ#0fwf$$R4^)5DJ+Zv4ih_D%_&DMSt;vi;Xu4U*37Q!NTHTb)N--KPqqG_8M*^95hVS(v^#UK_h<i3(7{gfa0dP-?6eU)RGmg%%=6}iuHavMAM@Yvsxn2aMg&;Fs&))BKQwU>z9<xk@A?pqbg7Z?(>QxNx#fmad1PNb#UwoZIO(@)KK(_pmNKbdT!Z;drrktvo>#Bzp2F0_0Ckqha>Rqu?JT^1{>MP(%TCrdBqAB_v(_l_JpoU_{dKn}TWB>GS3@{XMHkR!KRMOPF%`-l)q*&@mx_7;MNxiBmLd?PPbdC6Cli;)%GnbRCR<Uh$HVIK1e{HJ8y)e#8ih9-PIbvmVk^l+`r#xMg9ce0tLtnV%6|9vKsL|uLtv!u37qXjYI;q22ft3=Em;KQpdKc5Bbz9^A0+OX!aW$*t}yU09oR^+wIj(b|Hm8t)p3!_O&*Z*6``gaWV`k_&ZYvMb?{LpPjm>*t#cR20-eNyI&yuQd=Gyi`txN#D-p8^L1wMT(eGc$d-ZtML&im29r{unrb(@w#4`*5p)w2Q}>*Dq8(@Ge%{51;YwAZQYnJz^!P#~206{;2fCL8>B``CWRQ6+?M=OO8jdlNd}kJjB}J=ILpZ#qe>?=$NtE=EqrYS>1=+XOo&{r+d#O!RpARQ~<^Kv#JmJfs=&$6RC8Lc{Ua2OG7S48Zw7vO-kpob5Xio)eM}w!hNNCZ#=j7#IY3Hw;QI6_CEYa@`j5S+vn~=F?*@xEI$$BS-1rzu~6Bk$z$xAaG!1DR}ZeP3iYpRL?pmussE5v?sV?pkyKF`ZIvuu`GS|65z03-;e%Z#hJy+nsRp5^^-wFTX(p3WD+_Uwos?Y0Qj$U$nI20Aoh3kAjjcG=g5`t7`pIILvYCvI1=~cG$a-OQeNb-g?2?db#62(s$wc58CgDm9=e;61kGSvpGu8IM6U8uPogPv48Frpz#|)Np+1c&fitp+3*aYNqdB~A952qy`csMIQYaK+s-yorO>)iCbv5#OpnsAaxh)3AU(HcEkQV8I8x>zC7LLKtHy%Nh|?2(3*0{kTCB6kHH`h~oGhKY*F2yWs^oVZnM6x1h@y^^kPQR4x<_1-CzmdB&IcEVr3c?RX+C$D;Hz0o}|1an^t#UStm=(E~9(FkiJ;WHlD_P`%i@qB;iUY5p4Zw8#_%cAlyByaspqa{mYgQ9ym5U8j6da%ArvjML&qEAyS+D%hd%d`Rh)pMz-Z=ZWOVL$TvXA@W$y^CugCn=o>)gX<zSTVDrlv-AR=Gb)%lV<pvP_7E)py<A##Zz&SRp3mf$jXv#PiQypP8j@|wcQ;XoYSF&B`?~g-8%(i!dTul@#Q(S+etlIG;IuBQznoh2JEHmn3h%#k?{wm+RjVs5^Oijo2M=8!QNx-f}kiQIO5qZHygRESPYmYeDEhRrUV;>`SGmxBRWk^mU#_RIpNipw@UJ!M%touxP&I{(?r@9;_|z^VRwBZ*Lj_ptX-jPYRQ%QZK?-ywqz8I!Fi(cje5!lB+?D-i&t;tAz9scuTVgaq8PP$jMy_MMy=)%<abp+t$RpItdvN8wRs%s+id<}Rd}nb7RbaE?^xOZ?U{=M;t94?&uwOh(U+`gb$a$#b$~~tYE&xLl;bR@7NeYZc7@u3TC_9`96z9gXP98a${+E9GVS4@y%ro`<r1}bb0caDn}|mX`a@8=XeiV)(hJCp{fCByOtOn~D<|b$+M(ACpBQf-PVRkhZX*X=tPZ{W!w4&p@%=PoGn*{aqk)5o&r3Hm;>I;CMLI;kSIeXn<vngjtd0(9VeRHQu-V7ZzoTFA+!FEMYfTu$x%*VI8?I;!k!2~`iUo<AodONO9>K1o1iZ_^X6|inDGlDUpg!fk*GBU}?4hg<Db}Bftb+8GclV{z1x7WMjxbc>;zB6;o2yFd;pUzcC;fa}?|k+it5lAsiRB0iRC2=zy+Fl)stGl?s`Fh5q``f*1|SfE(-4?c%KN%O<*+OnYm7jz{9^Ke-ffP*H^LYTLF%N?h$Q->@3BW=K4Z2R=lU+?!@UqKCf1`8(4=pI%*G%k9(t+ieCQQ!UW;PigD&De$;u}6MOsS#PL`1Fu1up&HD2>1;GDp`HN93V)&XK~mk|SbTJELw=xwgJl312bT+Q+c+sd4*{ki1RV0$*frr_H|jBbnNZSFW!jpbwU07$dP+}=Ih(1FXL*Rmh1-PB!!lECF8)pS%3bypS*-JAq-hWAE?S_taHMpKFsx!Y7}^Y=s-CXp2yyCLCKaS>aJ;9JQQ33^!<RBQ+cKceRl2&KUmXqihZ&$7-!+}x+JeHzX4N)SRdB;_(gbAQhnKbY9s8mu2pmdWi9-xXrL<P*zLSZ3Z*T?^U*O2a{aRg~`UP@p^{;-WI)j+0>iPbI1c+-(FlRz2W)1G_%cd;wNj)uQ2Bjo~W@7OTU=&$!zN_YuJ?&;e*^I0-w7yal6ex_6mJvOb#Fk(^6H`9dM!e&-&WO2Qr}W=Y_bH&(*76Khy~27QFy5?6w;qv%ypAABK{H(AYy5G!o30y?%TBQQ55?_okOy>(R>j6K#~36ltJb9z|AWSKTw6y#w2dSl(h@;bS6s`p@$?(bo4{3+~Cz+Qrhu@(ISl7xQ<Lx~<27~2W1R<V9(&CAb$_Ff)3dRsg!G;hVs<(ig{efa_np6fh`tRj_bL#+Nfcs;PSFADo|E%_2l3*`{a9Els3jlBUnIt?5RnW3s{vU8(XhGH+l#Q4mSkG>p(<RW<&$!xJK#eD=HeR;YYlVgR)(BuiS_gl0I#SRdRZ5{;T6I$2h^iQvUY@fKMz??RHbj<dpB$84TG1eu&g1}^Vc|01~Ns+}c-P(gcy!km<t&m8OzpF<>tR~3PF-<smcWSM@%Z$s%y6LQ;3J069ZrD~18(7vnG=X_^!{u+;8G*0vk-zy%PXuPu@=LW1R2eGgv{)31n__fjka7~n1EI&qBiW=z(F}f<-1~rU>IMPm=ZQ3|DQM}uzSM9R7Y0V`psU5LX9_<oF@Lqb#Jr(w$-}=0<;UF~Hh9PvrCNfY7w~YspY*`|Ypiu2sYY?UVvw)9mOh^M)Vbhfi{w1Svn|zjfX5M&iygyHjZGha*GV6LH#B|xc|g0WqP{DMZJcqKY<);<E+FofVKXWj_hleXJ=>$aPLq3l3xiT5l!F)yx0y$U^5&~lyW{Gvo-9)qu*hems)eutfuZSkT&ithvIv~t`fMFdv;LFOGHtRM<_Dc%rBzRkYa+ZP5#6`}iKLxig`ntdj{8y>Mw*b0Yx1@aq15YJovZU_?WU^L^qy}47R%=Zb+S47sFgsq12`k(!w~C!zDn|OnmChA4&@CD-sfeOhn$<zR28$nbz!>0h}Z2P_~wmfi^1-&+I}@mS?52_nH()!r!L@L;Us?lKO9v>YAM7300"""


def clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def load_events() -> list[dict[str, Any]]:
    raw = gzip.decompress(base64.b85decode(_EVENT_BLOB.encode("ascii"))).decode("utf-8")
    events = json.loads(raw)["events"]
    for event in events:
        if event.get("id") not in {"f_stall", "s_ticket", "s_machine"}:
            continue
        choices = event.setdefault("choices", {})
        if not any("离开" in c.get("text", "") or "不买" in c.get("text", "") or "什么都不" in c.get("text", "") for c in choices.values()):
            for key in ("D", "E", "F"):
                if key not in choices:
                    choices[key] = {"text": "离开，不购买", "result": "你收好金币，离开了这里。", "ops": []}
                    break
    events.append(clone(FINAL_CHOICE_EVENT))
    return events


def infer_chapter(state: dict[str, Any]) -> int:
    flags = state.get("flags", {})
    if state.get("main_story_complete"):
        return 5
    if "沉睡湖" in state.get("unlocked_locations", []) or state.get("night_keys", 0) >= 3:
        return 4
    if flags.get("shadow_truth"):
        return 4
    if flags.get("station_truth_complete") or flags.get("hidden_platform"):
        return 3
    if any(x in state.get("inventory", []) for x in ("白色字片", "黑羽标记", "旧怀表")):
        return 1
    return 1



def load_state() -> dict[str, Any]:
    if SAVE_FILE.exists():
        try:
            state = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = clone(INITIAL_STATE)
    else:
        state = clone(INITIAL_STATE)
    old_had_progress = bool(state.get("journal") or state.get("day", 1) > 1 or state.get("night_keys", 0) or state.get("seen_once_events"))
    previous_version = str(state.get("version", "0.8"))
    for key, value in INITIAL_STATE.items():
        state.setdefault(key, clone(value))
    if "prologue_complete" not in state or previous_version != VERSION:
        state["prologue_complete"] = bool(state.get("prologue_complete", old_had_progress))
    if not state.get("chapter"):
        state["chapter"] = infer_chapter(state) if state["prologue_complete"] else 0
    state["version"] = VERSION
    state.pop("pending_return_prompt", None)
    flags = state.setdefault("flags", {})
    state.setdefault("completed_character_lines", [])

    # v0.8 / v1.0 存档迁移：保留已经完成的物品、章节与调查进度。
    inventory = set(state.get("inventory", []))
    migration_flags = {
        "white_fragment_obtained": "白色字片" in inventory or bool(flags.get("white_fragment_found")),
        "black_feather_obtained": "黑羽标记" in inventory,
        "watch_obtained": "旧怀表" in inventory,
        "ticket_corner_obtained": "车票残角" in inventory or bool(flags.get("ticket_complete")),
    }
    for key, value in migration_flags.items():
        if value:
            flags[key] = True

    solved = state.setdefault("solved_deductions", [])
    if state.get("chapter", 0) >= 2 or flags.get("chapter1_complete"):
        if "name_taken_by_train" not in solved:
            solved.append("name_taken_by_train")
        flags["deduced_name_train"] = True
    if state.get("chapter", 0) >= 3 or flags.get("station_truth_complete"):
        if "train_carries_names" not in solved:
            solved.append("train_carries_names")
        flags["deduced_train_cargo"] = True
    if state.get("chapter", 0) >= 4 or flags.get("shadow_truth"):
        if "shadow_keeps_memories" not in solved:
            solved.append("shadow_keeps_memories")
        flags["deduced_shadow_guardian"] = True

    evidence = state.setdefault("evidence", [])
    evidence_migrations = {
        "half_note": "半句纸条" in inventory,
        "faceless_request": bool(flags.get("find_name")),
        "bark_missing_name": bool(flags.get("white_fragment_revealed") or flags.get("white_fragment_found") or flags.get("white_fragment_obtained")),
        "root_train_truth": bool(flags.get("root_truth")),
        "black_feather_station": bool(flags.get("black_feather_obtained")),
        "watch_0013": bool(flags.get("watch_obtained") or flags.get("station_watch_used")),
        "timetable_names": bool(flags.get("station_timetable")),
        "broadcast_forgotten": bool(flags.get("station_broadcast")),
        "hidden_platform_cargo": bool(flags.get("hidden_platform")),
        "ticket_water_track": bool(flags.get("ticket_complete")),
        "shadow_checked_in": bool(flags.get("station_timetable")),
        "staff_knows_feather": bool(flags.get("station_recognized_feather")),
        "deer_on_rails": bool(flags.get("deer_tracks_seen")),
        "shadow_route_lake": bool(flags.get("shadow_followed")),
        "lake_child_tracks": bool(flags.get("lake_shore")),
        "lake_station_sign": bool(flags.get("lake_sign")),
        "guardian_lamp_owner": bool(flags.get("lake_guard")),
        "ticket_holder_decides": bool(flags.get("lake_ticket")),
        "lamp_handover": bool(flags.get("lake_lamp_memory")),
    }
    for evidence_id, present in evidence_migrations.items():
        if present and evidence_id not in evidence:
            evidence.append(evidence_id)
    return state

def save_state(state: dict[str, Any]) -> None:
    SAVE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def add_journal(state: dict[str, Any], text: str) -> None:
    state.setdefault("journal", []).append({"day": state["day"], "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": text})
    state["journal"] = state["journal"][-250:]


def has_item(state: dict[str, Any], item: str) -> bool:
    return item in state.get("inventory", [])


def add_item(state: dict[str, Any], item: str) -> bool:
    if item not in state["inventory"]:
        state["inventory"].append(item)
        return True
    return False


def remove_item(state: dict[str, Any], item: str) -> bool:
    if item in state["inventory"]:
        state["inventory"].remove(item)
        return True
    return False


def add_character_line(state: dict[str, Any], name: str) -> None:
    if name not in state["completed_character_lines"]:
        state["completed_character_lines"].append(name)


def clamp(state: dict[str, Any]) -> None:
    state["hp"] = max(0, min(state["max_hp"], state["hp"]))
    for key in ("lamp_oil", "food", "coins", "clues", "trust"):
        state[key] = max(0, state[key])
    state["night_keys"] = max(0, min(3, state["night_keys"]))


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
    for trait, minimum in req.get("traits_min", {}).items():
        if state["traits"].get(trait, 0) < minimum:
            return False
    if state["night_keys"] < req.get("night_keys_min", 0):
        return False
    if req.get("main_story_complete") is not None and state["main_story_complete"] != req["main_story_complete"]:
        return False
    return True


def apply_ops(state: dict[str, Any], ops: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for op in ops:
        kind = op.get("op")
        if kind == "stat":
            key, amount = op["key"], int(op.get("amount", 0))
            state[key] = state.get(key, 0) + amount
            messages.append(op.get("text", f"{key}{amount:+d}"))
        elif kind == "trait":
            key, amount = op["key"], int(op.get("amount", 1))
            state["traits"][key] = state["traits"].get(key, 0) + amount
            messages.append(op.get("text", f"{key}+{amount}"))
        elif kind == "item_add":
            if add_item(state, op["item"]):
                messages.append(op.get("text", f"获得：{op['item']}"))
        elif kind == "item_remove":
            if remove_item(state, op["item"]):
                messages.append(op.get("text", f"失去：{op['item']}"))
        elif kind == "flag":
            state["flags"][op["key"]] = op.get("value", True)
            if op.get("text"):
                messages.append(op["text"])
        elif kind == "unlock":
            loc = op["location"]
            if loc not in state["unlocked_locations"]:
                state["unlocked_locations"].append(loc)
                messages.append(op.get("text", f"解锁地点：{loc}"))
        elif kind == "key":
            state["night_keys"] += int(op.get("amount", 1))
            messages.append(op.get("text", "获得夜钥匙×1"))
        elif kind == "chance":
            roll, total, chosen = random.random(), 0.0, None
            for branch in op.get("branches", []):
                total += float(branch.get("p", 0))
                if roll <= total:
                    chosen = branch
                    break
            chosen = chosen or op.get("branches", [{}])[-1]
            if chosen.get("text"):
                messages.append(chosen["text"])
            messages.extend(apply_ops(state, chosen.get("ops", [])))
        elif kind == "conditional":
            branch = op.get("then", []) if check_requirements(state, op.get("requires")) else op.get("else", [])
            messages.extend(apply_ops(state, branch))
        elif kind == "heal_full":
            state["hp"] = state["max_hp"]
            messages.append(op.get("text", "体力完全恢复"))
        elif kind == "ending":
            ending = op["ending"]
            if ending not in state["completed_endings"]:
                state["completed_endings"].append(ending)
            state["main_story_complete"] = True
            state["chapter"] = 5
            state["final_mode"] = False
            messages.append(op.get("text", f"达成结局：{ending}"))
    clamp(state)
    for title in apply_titles(state):
        messages.append(f"新称号：{title}")
    return [m for m in messages if m]


def scene_payload(scene: dict[str, Any]) -> dict[str, Any]:
    return {"id": scene["id"], "title": scene["title"], "text": scene["text"]}


def play_scenes(state: dict[str, Any], scenes: list[dict[str, Any]], *, mark_seen: bool = True) -> list[dict[str, Any]]:
    played = []
    for scene in scenes:
        if mark_seen and scene["id"] in state["seen_auto_scenes"]:
            continue
        effects = apply_ops(state, scene.get("ops", []))
        if mark_seen:
            state["seen_auto_scenes"].append(scene["id"])
        state["auto_scene_last_seen"][scene["id"]] = state["day"]
        text = scene["text"] + (("\n" + "；".join(effects)) if effects else "")
        add_journal(state, f"[自动剧情｜{scene['title']}] {text}")
        played.append({"id": scene["id"], "title": scene["title"], "text": text})
    return played



def run_prologue(state: dict[str, Any]) -> dict[str, Any]:
    add_item(state, "空白车票")
    add_item(state, "半句纸条")
    state["prologue_complete"] = True
    state["chapter"] = 1
    state["flags"]["prologue_knock"] = True
    record_evidence(state, "half_note")
    scenes = play_scenes(state, PROLOGUE_SCENES)
    save_state(state)
    return {"ok": True, "message": "序章自动播放完毕。自由行动已经开放；开场现场可以继续 inspect、open 或 wait。", "scenes": scenes, "state": state_summary(state), "next": "先查看 options，调查小屋，再决定前往雾林或旧车站。"}

def item_reaction(item: str) -> dict[str, Any] | None:
    mapping = {
        "白色字片": {"id": "item_white_fragment", "title": "白色字片", "text": "字片落进掌心时，附近树皮上的文字同时少了一笔。无脸旅人远远抬起头，像是听见了自己的名字。"},
        "黑羽标记": {"id": "item_black_feather", "title": "黑羽标记", "text": "黑羽在掌心变暖。你的影子朝旧车站方向偏了一下，哪怕提灯就在正前方。"},
        "旧怀表": {"id": "item_watch", "title": "停住的怀表", "text": "怀表指针先倒走十三秒，又停在零点十三分。远处传来一声列车汽笛，雾林里的树根同时绷紧。"},
        "车票残角": {"id": "item_ticket_corner", "title": "车票残角", "text": "残角靠近空白车票时，两个断面像伤口一样微微发热。"},
        "拼合车票": {"id": "item_ticket_whole", "title": "拼合车票", "text": "两张车票拼合后，票面浮出一条经过雾林、旧车站和沉睡湖的线路。终点栏仍然空着。"},
    }
    return mapping.get(item)



def chapter_objective(state: dict[str, Any]) -> str:
    flags, inv, chapter = state["flags"], set(state["inventory"]), state["chapter"]
    solved = set(state.get("solved_deductions", []))
    if chapter == 1:
        tasks = []
        if not flags.get("find_name"): tasks.append("inspect 无脸旅人")
        if not flags.get("white_fragment_obtained"): tasks.append("follow 白鹿 → inspect 树皮 → take 白色字片")
        if not flags.get("black_feather_obtained"): tasks.append("follow 乌鸦")
        if not flags.get("watch_obtained"): tasks.append("listen 倒生树根")
        if "name_taken_by_train" not in solved: tasks.append("board / connect / deduce 名字被列车带走")
        return "雾林调查：" + ("；".join(tasks) if tasks else "镜中梦即将触发")
    if chapter == 2:
        tasks = []
        if not flags.get("station_timetable"): tasks.append("inspect 时刻表")
        if not flags.get("station_broadcast"): tasks.append("listen 广播")
        if not flags.get("ticket_corner_obtained"): tasks.append("inspect 售票窗口 → take 车票残角")
        if not flags.get("hidden_platform"): tasks.append("use 空白车票")
        if not flags.get("station_watch_used"): tasks.append("adjust 旧怀表 00:13")
        if not flags.get("ticket_complete"): tasks.append("combine 车票残角 空白车票")
        if "train_carries_names" not in solved: tasks.append("deduce 列车运送名字和记忆")
        return "旧车站调查：" + ("；".join(tasks) if tasks else "等待列车真相显形")
    if chapter == 3:
        tasks = []
        if not flags.get("station_recognized_feather"): tasks.append("在旧车站 use 黑羽标记")
        if not flags.get("deer_tracks_seen"): tasks.append("在旧车站 follow 白鹿")
        if not flags.get("shadow_followed"): tasks.append("follow 影子")
        if not flags.get("shadow_decision"): tasks.append("trust 影子 或 confront 影子")
        if "shadow_keeps_memories" not in solved: tasks.append("deduce 影子在替我保管记忆")
        return "追查先到终点的影子：" + ("；".join(tasks) if tasks else "第三把夜钥匙正在回应")
    if chapter == 4:
        tasks = []
        if not flags.get("lake_shore"): tasks.append("inspect 湖岸")
        if not flags.get("lake_guard"): tasks.append("listen 守夜人")
        if not flags.get("lake_sign"): tasks.append("inspect 湖底站牌")
        if not flags.get("lake_ticket"): tasks.append("use 拼合车票")
        if not flags.get("lake_lamp_memory"): tasks.append("use 旧提灯")
        if "cottage_is_transfer" not in solved: tasks.append("deduce 林间小屋是中转站")
        return "沉睡湖终局调查：" + ("；".join(tasks) if tasks else "最后一班列车即将抵达")
    if chapter == 5:
        return "主线已经结束，可继续漫游和收集其他结局。"
    return "让提灯照亮第一步。"

def quest_snapshot(state: dict[str, Any]) -> list[dict[str, Any]]:
    chapter_name = "·".join(CHAPTERS.get(state["chapter"], ("未知", "未知")))
    quests = [{"id": "main", "name": chapter_name, "description": "调查林间小屋、雾林、旧车站与沉睡湖之间的联系。", "progress": chapter_objective(state), "complete": state["main_story_complete"]}]
    if state["flags"].get("find_name") or state["flags"].get("name_quest_done"):
        quests.append({"id": "lost_name", "name": "失落的名字", "description": "帮助无脸旅人找回名字。", "progress": "名字已经归还" if state["flags"].get("name_quest_done") else "找到白色字片后，在雾林 give 白色字片 无脸旅人", "complete": bool(state["flags"].get("name_quest_done"))})
    return quests


def hidden_ready(state: dict[str, Any]) -> bool:
    required = {"无脸旅人", "白鹿", "站务员", "影子", "守夜人"}
    return required.issubset(set(state["completed_character_lines"])) and state["flags"].get("name_quest_done") and state["flags"].get("ticket_complete")



def process_milestones(state: dict[str, Any]) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    flags = state["flags"]
    solved = set(state.get("solved_deductions", []))
    if hidden_ready(state):
        flags["hidden_ready"] = True

    chapter1_items = all(flags.get(k) for k in ("white_fragment_obtained", "black_feather_obtained", "watch_obtained"))
    if state["chapter"] == 1 and not flags.get("chapter1_complete") and chapter1_items and "name_taken_by_train" in solved:
        flags["chapter1_complete"] = True
        state["chapter"] = 2
        state["night_keys"] = max(state["night_keys"], 1)
        state["location"] = "林间小屋"
        state["run_events"] = 0
        scenes.extend([
            {"id": "chapter1_dream_mirror", "title": "镜中梦", "text": "你没有记得自己是怎样回到小屋的。镜子里站着一个和你一模一样的人，它没有影子，手腕上却缠着旧车站的检票带。"},
            {"id": "chapter1_dream_items", "title": "三件物品", "text": "白色字片曾留下的笔画浮上镜面，黑羽自行竖起，旧怀表开始倒走。镜中人把第一把夜钥匙放在桌上，用口型说：『下一站不是给活人准备的。』"},
            {"id": "chapter1_to_station", "title": "第二章开启", "text": "空白车票上浮出『零点十三分』。旧车站的方向传来一声很远的汽笛。"},
        ])

    station_actions = all(flags.get(k) for k in ("station_timetable", "station_broadcast", "hidden_platform", "station_watch_used", "ticket_complete"))
    if state["chapter"] == 2 and station_actions and "train_carries_names" in solved and not flags.get("station_truth_complete"):
        flags["station_truth_complete"] = True
        state["chapter"] = 3
        state["night_keys"] = max(state["night_keys"], 2)
        state["shadow_home_pending"] = True
        scenes.extend([
            {"id": "chapter2_cargo", "title": "列车的货物", "text": "你亲手串起的证据让站厅发生变化：所有站名同时变成姓名。广播承认，这趟列车运送的从来不是乘客，而是被世界遗忘的名字与记忆。"},
            {"id": "chapter2_shadow_window", "title": "先到一步的人", "text": "列车开过时，你在最后一扇窗里看见自己的影子。它胸前挂着第二把夜钥匙，比你先一步抵达了终点。"},
        ])

    chapter3_actions = all(flags.get(k) for k in ("station_recognized_feather", "deer_tracks_seen", "shadow_followed", "shadow_decision"))
    if state["chapter"] == 3 and chapter3_actions and "shadow_keeps_memories" in solved and not flags.get("shadow_truth"):
        flags["shadow_truth"] = True
        state["chapter"] = 4
        state["night_keys"] = 3
        add_character_line(state, "影子")
        if "沉睡湖" not in state["unlocked_locations"]:
            state["unlocked_locations"].append("沉睡湖")
        tone = "它接受了你的信任" if flags.get("shadow_trusted") else "它接受了你的质问，也终于把真相交还给你"
        scenes.extend([
            {"id": "chapter3_truth", "title": "影子先到终点", "text": f"白鹿踏过铁轨，站务员向黑羽行礼。你的影子终于停下，{tone}：它一直替你收集那些被删除的过去，只因真正的你还没有准备好记起。"},
            {"id": "chapter3_third_key", "title": "第三把夜钥匙", "text": "影子把第三把夜钥匙按进你的掌心。三把钥匙同时指向同一个地方——沉睡湖。"},
        ])

    lake_actions = all(flags.get(k) for k in ("lake_shore", "lake_guard", "lake_sign", "lake_ticket", "lake_lamp_memory"))
    if state["chapter"] == 4 and lake_actions and "cottage_is_transfer" in solved and not state["final_mode"]:
        if hidden_ready(state):
            flags["hidden_ready"] = True
        state["final_mode"] = True
        state["pending_event"] = "final_choice"
        scenes.extend([
            {"id": "chapter4_deleted_past", "title": "被删除的过去", "text": "沉入湖底的站牌翻到正面，上面写着你的名字。你终于明白：林间小屋不是避难所，而是有人为了让你有机会重新选择而留下的中转站。"},
            {"id": "chapter4_last_train", "title": "最后一班列车", "text": "水下列车驶上湖面。普通事件的声音全部停止，终局开始连续推进。"},
        ])
    clamp(state)
    return play_scenes(state, scenes)

def homecoming_scenes(state: dict[str, Any]) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    if state.get("shadow_home_pending"):
        state["shadow_home_pending"] = False
        add_item(state, "影子的行李牌")
        scenes.extend([
            {"id": "chapter3_home_shadow", "title": "影子回到小屋", "text": "你推门时，背包里的物品已经按另一种顺序摆在桌上。影子坐在床沿替你擦拭旧怀表，却没有在地板上留下轮廓。"},
            {"id": "chapter3_unknown_item", "title": "从未得到过的物品", "text": "影子离开后，桌上多出一块你从未取得过的行李牌。正面写着你的名字，背面写着：『已于三年前抵达。』\n获得：影子的行李牌"},
        ])
    elif state["flags"].pop("faceless_followup_pending", False):
        scenes.append({"id": "followup_faceless", "title": "名字归来以后", "text": "无脸旅人第一次以完整的面容来敲门。他没有请求帮助，只把一张写着自己名字的便签贴在小屋墙上：『以后有人忘记我，这里仍会记得。』"})
    elif state["flags"].pop("deer_followup_pending", False):
        scenes.append({"id": "followup_deer", "title": "白鹿留下的路", "text": "白鹿在窗外停了一夜。天亮前，它用鹿角在雾中划出一条不会消失的路，终点正对沉睡湖。"})
    elif state["flags"].pop("staff_followup_pending", False):
        scenes.append({"id": "followup_staff", "title": "站务员来访", "text": "站务员没有敲门。他把检票钳放在门槛上，夹出一张小票：『影子并非冒名者，它在替你保管终点。』"})
    elif random.random() < 0.55:
        available = [s for s in HOME_SCENES if state["day"] - state["auto_scene_last_seen"].get(s["id"], -99) >= 3]
        if available:
            scenes.append(random.choice(available))
    return play_scenes(state, scenes, mark_seen=False)


def first_visit_scenes(state: dict[str, Any], location: str) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    if location not in state["visited_locations"]:
        state["visited_locations"].append(location)
        scenes.extend(LOCATION_SCENES.get(location, []))
    if location == "旧车站" and state["chapter"] >= 2 and "chapter2_station_open" not in state["seen_auto_scenes"]:
        scenes.extend(STATION_CHAPTER_SCENES)
    if location == "沉睡湖" and state["chapter"] >= 4 and "lake_intro_face" not in state["seen_auto_scenes"]:
        state["flags"].pop("lamp_lit", None)
        state["flags"]["lamp_extinguished_at_lake"] = True
        scenes.extend(LAKE_INTRO_SCENES)
    return play_scenes(state, scenes)



def normalize_phrase(text: str) -> str:
    table = str.maketrans("", "", " \t\r\n，。！？、：；（）()【】[]‘’“”\"'·-—_+")
    return text.lower().translate(table)


def record_evidence(state: dict[str, Any], evidence_id: str) -> str | None:
    if evidence_id not in EVIDENCE_DEFINITIONS:
        return None
    if evidence_id in state.setdefault("evidence", []):
        return None
    state["evidence"].append(evidence_id)
    info = EVIDENCE_DEFINITIONS[evidence_id]
    add_journal(state, f"[新线索｜{info['name']}] {info['text']}")
    return f"新线索：{info['name']}"


def evidence_id_from_text(state: dict[str, Any], text: str) -> str | None:
    needle = normalize_phrase(text)
    for evidence_id in state.get("evidence", []):
        info = EVIDENCE_DEFINITIONS.get(evidence_id, {})
        if needle in {normalize_phrase(evidence_id), normalize_phrase(info.get("name", ""))}:
            return evidence_id
    return None


def board_payload(state: dict[str, Any]) -> dict[str, Any]:
    evidence = []
    for evidence_id in state.get("evidence", []):
        info = EVIDENCE_DEFINITIONS.get(evidence_id, {"name": evidence_id, "text": ""})
        evidence.append({"id": evidence_id, "name": info["name"], "text": info["text"], "pinned": evidence_id in state.get("board_pins", [])})
    deductions = []
    found = set(state.get("evidence", []))
    solved = set(state.get("solved_deductions", []))
    for deduction_id, definition in DEDUCTION_DEFINITIONS.items():
        required = set(definition["requires"])
        visible = bool(required & found) or deduction_id in solved
        if not visible:
            continue
        deductions.append({
            "id": deduction_id,
            "title": definition["title"] if deduction_id in solved or len(required & found) >= 2 else "尚未成形的推理",
            "progress": f"{len(required & found)}/{len(required)}",
            "solved": deduction_id in solved,
        })
    links = []
    for link in state.get("board_links", []):
        a, b = link
        links.append({"a": EVIDENCE_DEFINITIONS.get(a, {"name": a})["name"], "b": EVIDENCE_DEFINITIONS.get(b, {"name": b})["name"]})
    return {"evidence": evidence, "links": links, "deductions": deductions}


def pin_evidence(state: dict[str, Any], text: str) -> str:
    evidence_id = evidence_id_from_text(state, text)
    if not evidence_id:
        return "这条线索尚未发现，或名称无法对应。先用 board 查看已有线索。"
    pins = state.setdefault("board_pins", [])
    if evidence_id in pins:
        return f"“{EVIDENCE_DEFINITIONS[evidence_id]['name']}”已经钉在线索板上。"
    pins.append(evidence_id)
    return f"你把“{EVIDENCE_DEFINITIONS[evidence_id]['name']}”钉在线索板上。"


def connect_evidence(state: dict[str, Any], left: str, right: str) -> tuple[str, list[dict[str, Any]]]:
    a, b = evidence_id_from_text(state, left), evidence_id_from_text(state, right)
    if not a or not b:
        return "至少有一条线索尚未发现。先用 board 查看可连接内容。", []
    if a == b:
        return "同一条线索无法与自己连接。", []
    pair = tuple(sorted((a, b)))
    links = state.setdefault("board_links", [])
    if list(pair) in links or pair in [tuple(x) for x in links]:
        return "这两条线索已经连接过。", []
    links.append(list(pair))
    state["clues"] += 1
    hint = CONNECTION_HINTS.get(frozenset({a, b}))
    message = f"你用红线连接了“{EVIDENCE_DEFINITIONS[a]['name']}”和“{EVIDENCE_DEFINITIONS[b]['name']}”。线索+1。"
    scenes = []
    if hint:
        scenes.append({"id": f"link_{a}_{b}", "title": "线索之间", "text": hint})
    return message, scenes


def find_deduction(text: str) -> str | None:
    needle = normalize_phrase(text)
    for deduction_id, definition in DEDUCTION_DEFINITIONS.items():
        options = [definition["title"], deduction_id, *definition.get("aliases", [])]
        if needle in {normalize_phrase(x) for x in options}:
            return deduction_id
    return None


def solve_deduction(state: dict[str, Any], text: str) -> tuple[str, list[dict[str, Any]]]:
    deduction_id = find_deduction(text)
    if not deduction_id:
        state["wrong_deductions"] = state.get("wrong_deductions", 0) + 1
        return "这个推理暂时无法成立。线索板没有出现能支撑它的完整链条。", []
    definition = DEDUCTION_DEFINITIONS[deduction_id]
    if deduction_id in state.get("solved_deductions", []):
        return f"推理“{definition['title']}”已经成立。", []
    found = set(state.get("evidence", []))
    missing = [EVIDENCE_DEFINITIONS[x]["name"] for x in definition["requires"] if x not in found]
    if missing:
        return f"证据还不够。至少还缺少{len(missing)}类关键痕迹；继续调查现场或连接已有线索。", []
    state.setdefault("solved_deductions", []).append(deduction_id)
    state["flags"][definition["flag"]] = True
    state["clues"] += 1
    return f"推理成立：{definition['title']}。线索+1。", [definition["scene"]]



def available_investigations(state: dict[str, Any]) -> dict[str, list[str]]:
    loc, flags, inv, ch = state["location"], state["flags"], set(state["inventory"]), state["chapter"]
    result: dict[str, list[str]] = {"inspect": [], "open": [], "take": [], "use": [], "follow": [], "listen": [], "wait": [], "adjust": [], "combine": [], "ask": [], "give": [], "trust/confront": []}
    if loc == "林间小屋":
        result["inspect"] = ["镜子", "半句纸条"]
        if not flags.get("door_opened"): result["open"].append("门")
        result["wait"].append("敲门声")
        if ch == 3 and not flags.get("shadow_followed"): result["follow"].append("影子")
    elif loc == "雾林":
        if not flags.get("find_name"): result["inspect"].append("无脸旅人")
        elif not flags.get("name_quest_done"): result["ask"].append("无脸旅人 名字")
        if not flags.get("deer_guidance"): result["follow"].append("白鹿")
        if flags.get("deer_guidance") and not flags.get("white_fragment_revealed"): result["inspect"].append("树皮")
        if flags.get("white_fragment_revealed") and not flags.get("white_fragment_obtained"): result["take"].append("白色字片")
        if not flags.get("black_feather_obtained"): result["follow"].append("乌鸦")
        if not flags.get("root_truth"): result["listen"].append("倒生树根")
        if "白色字片" in inv and flags.get("find_name") and flags.get("root_truth") and not flags.get("name_quest_done"): result["give"].append("白色字片 无脸旅人")
        if ch == 3 and not flags.get("shadow_followed"): result["follow"].append("影子")
        result["wait"].append("雾散开")
    elif loc == "旧车站":
        if not flags.get("station_timetable"): result["inspect"].append("时刻表")
        if not flags.get("ticket_corner_revealed") and not flags.get("ticket_complete"): result["inspect"].append("售票窗口")
        if flags.get("ticket_corner_revealed") and not flags.get("ticket_corner_obtained"): result["take"].append("车票残角")
        if not flags.get("station_broadcast"): result["listen"].append("广播")
        if "空白车票" in inv and flags.get("station_timetable") and flags.get("station_broadcast") and not flags.get("hidden_platform"): result["use"].append("空白车票")
        if "旧怀表" in inv and flags.get("hidden_platform") and not flags.get("station_watch_used"): result["adjust"].append("旧怀表 00:13")
        if "车票残角" in inv and "空白车票" in inv and not flags.get("ticket_complete"): result["combine"].append("车票残角 + 空白车票")
        if ch == 3:
            if "黑羽标记" in inv and not flags.get("station_recognized_feather"): result["use"].append("黑羽标记")
            if not flags.get("deer_tracks_seen"): result["follow"].append("白鹿")
            if flags.get("station_recognized_feather") and "站务员" not in state["completed_character_lines"]: result["listen"].append("站务员")
            if not flags.get("shadow_followed"): result["follow"].append("影子")
            if flags.get("shadow_followed") and not flags.get("shadow_decision"): result["trust/confront"] = ["trust 影子", "confront 影子"]
        result["wait"].append("下一班列车")
    elif loc == "沉睡湖":
        if not flags.get("lake_shore"): result["inspect"].append("湖岸")
        if not flags.get("lake_sign"): result["inspect"].append("湖底站牌")
        if not flags.get("lake_guard"): result["listen"].append("守夜人")
        if "拼合车票" in inv and not flags.get("lake_ticket"): result["use"].append("拼合车票")
        if "旧提灯" in inv and not flags.get("lake_lamp_memory"): result["use"].append("旧提灯")
        result["wait"].append("水下列车")
    result["board"] = ["board", "pin <线索>", "connect <线索1> | <线索2>", "deduce <推理>"]
    return {k: v for k, v in result.items() if v}


def action_scene(state: dict[str, Any], action: str, target: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    loc, flags = state["location"], state["flags"]
    scenes: list[dict[str, Any]] = []
    effects: list[str] = []
    target = target.strip()

    def gain_item(item: str, flag: str | None = None) -> None:
        if add_item(state, item):
            effects.append(f"获得：{item}")
        if flag:
            flags[flag] = True
        reaction = item_reaction(item)
        if reaction:
            scenes.append(reaction)

    def clue(evidence_id: str) -> None:
        msg = record_evidence(state, evidence_id)
        if msg:
            effects.append(msg)

    if action == "inspect":
        if loc == "林间小屋" and target == "镜子":
            flags["mirror_inspected"] = True
            return "镜中的你慢了半拍。你转身后，它仍然面对镜外。", scenes, effects
        if loc == "林间小屋" and target == "半句纸条":
            clue("half_note")
            return "你用提灯烘热纸条，断句后显出很淡的两个字：『独自』。", scenes, effects
        if loc == "雾林" and target == "无脸旅人":
            flags["find_name"] = True
            clue("faceless_request")
            return "无脸旅人把掌心按在胸口。他无法发声，只在雾上写下：『请把我从别人的记忆里找回来。』人物线“失落的名字”开启。", scenes, effects
        if loc == "雾林" and target == "树皮" and flags.get("deer_guidance") and not flags.get("white_fragment_revealed"):
            flags["white_fragment_revealed"] = True
            clue("bark_missing_name")
            return "白鹿停在一棵被剥去姓名的树前。你在树皮夹层看见一枚白色字片，但它还被细根牢牢缠住。现在可以 take 白色字片。", scenes, effects
        if loc == "旧车站" and target == "时刻表":
            flags["station_timetable"] = True
            clue("timetable_names"); clue("shadow_checked_in")
            return "时刻表没有列车编号，只有一列列姓名。零点十三分那一行写着你的名字，状态是『影子已检票』。", scenes, effects
        if loc == "旧车站" and target == "售票窗口":
            flags["ticket_corner_revealed"] = True
            return "你照亮窗口下方的缝，里面卡着一张焦黑票角。现在可以 take 车票残角。", scenes, effects
        if loc == "沉睡湖" and target == "湖岸":
            flags["lake_shore"] = True
            clue("lake_child_tracks")
            return "湖岸泥里排列着许多向水中走去的脚印，却没有一枚返回。最小的一双属于你的童年。", scenes, effects
        if loc == "沉睡湖" and target == "湖底站牌":
            flags["lake_sign"] = True
            clue("lake_station_sign")
            return "你把沉入浅水的站牌翻正。站名是『林间小屋』，下一站写着『仍有人记得你』。", scenes, effects

    if action == "open":
        if loc == "林间小屋" and target == "门":
            flags["door_opened"] = True
            clue("door_no_tracks"); clue("feather_to_forest")
            return "你拉开门。门外的湿泥平整得没有脚印，门槛上的黑羽却缓慢转向雾林。", scenes, effects

    if action == "take":
        if loc == "雾林" and target == "白色字片" and flags.get("white_fragment_revealed") and not flags.get("white_fragment_obtained"):
            state["hp"] -= 1
            gain_item("白色字片", "white_fragment_obtained")
            return "你用折叠小刀割断细根，取下白色字片。根须在手背留下一道冰凉划痕，体力-1。", scenes, effects
        if loc == "旧车站" and target == "车票残角" and flags.get("ticket_corner_revealed") and not flags.get("ticket_corner_obtained"):
            gain_item("车票残角", "ticket_corner_obtained")
            return "你从缝里取出焦黑票角。它与空白车票的缺口完全吻合。", scenes, effects

    if action == "follow":
        if loc == "雾林" and target == "白鹿":
            state["hp"] -= 1
            flags["deer_guidance"] = True
            return "白鹿带你穿过一段会改变方向的雾路。你跟得很吃力，体力-1，最后停在刻满残缺姓名的树前。", scenes, effects
        if loc == "雾林" and target == "乌鸦":
            gain_item("黑羽标记", "black_feather_obtained")
            clue("black_feather_station")
            return "乌鸦没有逃，它沿着树冠带你找到一处黑羽组成的标记。你取下一根，所有羽毛同时指向旧车站。", scenes, effects
        if target == "影子" and state["chapter"] == 3 and loc in {"雾林", "旧车站", "林间小屋"}:
            state["hp"] -= 1
            flags["shadow_followed"] = True
            clue("shadow_route_lake")
            return "你没有踩自己的脚步，而是跟着影子走。它带你经过一条现实里不存在的近路，终点正是沉睡湖的旧岸。体力-1。接下来可以 trust 影子 或 confront 影子。", scenes, effects
        if loc == "旧车站" and target == "白鹿" and state["chapter"] == 3:
            flags["deer_tracks_seen"] = True
            add_character_line(state, "白鹿")
            flags["deer_followup_pending"] = True
            clue("deer_on_rails")
            return "白鹿从铁轨另一侧走来，蹄印每落下一次，枕木上就浮出一个被遗忘的名字。人物线“白鹿”完成。", scenes, effects

    if action == "listen":
        if loc == "雾林" and target == "倒生树根":
            flags["root_truth"] = True
            gain_item("旧怀表", "watch_obtained")
            clue("root_train_truth"); clue("watch_0013")
            return "你把耳朵贴上倒生树根。根须说：名字被一列没有终点的车拿走了，而拿票的人有你的影子。树洞里同时掉出一枚旧怀表。", scenes, effects
        if loc == "旧车站" and target == "广播":
            flags["station_broadcast"] = True
            clue("broadcast_forgotten")
            return "你没有关掉广播。噪声下藏着一句循环低语：『遗忘物不是失物，遗忘物是乘客。』", scenes, effects
        if loc == "旧车站" and target == "站务员" and state["chapter"] == 3 and flags.get("station_recognized_feather"):
            add_character_line(state, "站务员")
            flags["staff_followup_pending"] = True
            return "站务员承认自己曾替黑羽的主人检票。那个人不是你，却与你共用一张影子。人物线“站务员”完成。", scenes, effects
        if loc == "沉睡湖" and target == "守夜人":
            flags["lake_guard"] = True
            add_character_line(state, "守夜人")
            gain_item("守夜人的徽章")
            clue("guardian_lamp_owner")
            return "守夜人说，提灯原本属于第一个拒绝独自上车的人。他把徽章交给你，并请你不要替任何人决定该被遗忘。人物线“守夜人”完成。", scenes, effects

    if action == "wait":
        key = f"{loc}:{target}"
        if key in state.setdefault("waited_scenes", []):
            return "你又等了一会儿，但现场没有出现新的变化。", scenes, effects
        state["waited_scenes"].append(key)
        if loc == "林间小屋" and target == "敲门声":
            clue("door_no_tracks")
            return "你没有立刻开门。第三下敲击过后，声音从门外移动到衣柜里，又回到门槛。", scenes, effects
        if loc == "雾林":
            state["clues"] += 1
            return "你站着不动，等雾自己改变。几条原本不存在的路径短暂重叠，线索+1。", scenes, effects
        if loc == "旧车站":
            state["clues"] += 1
            return "你等到钟的秒针倒走十三格。空轨上传来一班列车经过后的余震，线索+1。", scenes, effects
        if loc == "沉睡湖":
            state["trust"] += 1
            return "你等到水下列车完整经过，没有伸手阻拦。湖面因此记住了你的耐心，信任+1。", scenes, effects

    if action == "ask":
        if loc == "雾林" and target in {"无脸旅人 名字", "无脸旅人"} and flags.get("find_name"):
            return "无脸旅人无法说出名字，只在雾里画出一节车厢、一根黑羽和停在零点十三分的钟。", scenes, effects

    if action == "give":
        if loc == "雾林" and target in {"白色字片 无脸旅人", "白色字片 给 无脸旅人"} and has_item(state, "白色字片") and flags.get("find_name") and flags.get("root_truth"):
            flags["name_quest_done"] = True
            add_character_line(state, "无脸旅人")
            flags["faceless_followup_pending"] = True
            remove_item(state, "白色字片")
            state["trust"] += 2
            return "你把白色字片交给无脸旅人。残缺笔画自行补全，他第一次拥有了脸，也第一次叫出你的名字。人物线“无脸旅人”完成，信任+2。", scenes, effects

    if action == "use":
        if loc == "雾林" and target == "白色字片":
            return "这枚字片属于一个正在等待名字的人。可以执行 give 白色字片 无脸旅人。", scenes, effects
        if loc == "旧车站" and target == "空白车票" and has_item(state, target) and flags.get("station_timetable") and flags.get("station_broadcast"):
            flags["hidden_platform"] = True
            clue("hidden_platform_cargo")
            scenes.extend([
                {"id": "hidden_platform_open", "title": "隐藏站台", "text": "空白车票贴上检票口，墙面像一层旧漆向两侧剥开。后面不是房间，而是一座从时刻表里被删掉的站台。"},
                {"id": "train_arrival_auto", "title": "列车进站", "text": "没有汽笛，没有风。列车像一段被遗忘的句子滑入站台。车窗里没有乘客，只有一排排装着姓名、笑声和旧照片的行李。"},
            ])
            return "隐藏站台已经开放。列车进站场景自动播放。", scenes, effects
        if loc == "旧车站" and target == "旧怀表" and has_item(state, target) and flags.get("hidden_platform"):
            return "怀表指针可以被拨动。根据已有痕迹，尝试执行 adjust 旧怀表 <时间>。", scenes, effects
        if loc == "旧车站" and target == "黑羽标记" and has_item(state, target) and state["chapter"] == 3:
            flags["station_recognized_feather"] = True
            clue("staff_knows_feather")
            return "站务员看见黑羽后第一次抬头。他把检票钳放在胸前，像向一个早已离开的同事致意。现在可以 listen 站务员。", scenes, effects
        if loc == "沉睡湖" and target == "拼合车票" and has_item(state, target):
            flags["lake_ticket"] = True
            clue("ticket_holder_decides")
            return "拼合车票接触湖水后，终点栏终于显字：『由持票者决定。』车背面同时出现四种不同的撕票方式。", scenes, effects
        if loc == "沉睡湖" and target == "旧提灯" and has_item(state, target):
            flags["lake_lamp_memory"] = True
            clue("lamp_handover")
            return "你把熄灭的提灯浸入湖水。灯没有亮，玻璃里却映出提灯上一任主人把小屋钥匙交给你的画面。", scenes, effects

    if action == "adjust":
        parts = target.split()
        if loc == "旧车站" and parts and parts[0] in {"旧怀表", "怀表"} and has_item(state, "旧怀表") and flags.get("hidden_platform"):
            value = parts[-1].replace("：", ":") if len(parts) > 1 else ""
            if value in {"00:13", "0:13", "零点十三分"}:
                flags["station_watch_used"] = True
                clue("watch_0013")
                return "你把怀表拨到00:13。指针开始倒走，列车里的每件行李同时退回到被遗忘前一秒；最后一节车厢里，你的影子正在藏起一块行李牌。", scenes, effects
            state["hp"] -= 1
            return "时间不对。怀表猛地震动，错误时刻从指缝割过，体力-1。时刻表和序章纸条里也许藏着正确数字。", scenes, effects

    if action == "combine":
        normalized = {x.strip() for x in target.replace("＋", "+").split("+") if x.strip()}
        if normalized == {"车票残角", "空白车票"} and has_item(state, "车票残角") and has_item(state, "空白车票"):
            remove_item(state, "车票残角")
            remove_item(state, "空白车票")
            gain_item("拼合车票")
            flags["ticket_complete"] = True
            clue("ticket_water_track")
            return "两张票在你指间自行缝合。针脚不是线，而是一段段被剪掉的记忆。", scenes, effects

    if action == "trust" and target == "影子" and state["chapter"] == 3 and flags.get("shadow_followed"):
        flags["shadow_decision"] = "trust"
        flags["shadow_trusted"] = True
        state["trust"] += 2
        state["traits"]["善意"] += 1
        return "你放下提灯，让影子先碰到你的手。它没有夺走身体，只把一段你承受不了的记忆轻轻放回掌心。信任+2，善意+1。", scenes, effects

    if action == "confront" and target == "影子" and state["chapter"] == 3 and flags.get("shadow_followed"):
        flags["shadow_decision"] = "confront"
        flags["shadow_confronted"] = True
        state["traits"]["勇敢"] += 1
        state["clues"] += 1
        return "你挡在影子面前，要求它停止替你决定。它第一次正面看你，并把隐藏的路线全部画在地上。勇敢+1，线索+1。", scenes, effects

    return f"当前无法对“{target}”执行 {action}。先用 options 查看这里可调查的对象。", scenes, effects

def item_description(item: str) -> str:
    return ITEM_DESCRIPTIONS.get(item, "用途尚未确认。")


def visible_inventory(state: dict[str, Any]) -> list[dict[str, str]]:
    return [{"name": item, "description": item_description(item)} for item in state.get("inventory", [])]



def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    chapter_label = "·".join(CHAPTERS.get(state["chapter"], ("未知", "未知")))
    return {
        "version": state["version"], "day": state["day"], "location": state["location"],
        "chapter": state["chapter"], "chapter_label": chapter_label,
        "hp": state["hp"], "max_hp": state["max_hp"], "lamp_oil": state["lamp_oil"],
        "food": state["food"], "coins": state["coins"], "clues": state["clues"],
        "trust": state["trust"], "night_keys": state["night_keys"],
        "inventory": visible_inventory(state), "traits": state["traits"], "titles": state["titles"],
        "unlocked_locations": state["unlocked_locations"], "completed_endings": state["completed_endings"],
        "character_lines": state["completed_character_lines"], "run_events": state["run_events"],
        "quests": quest_snapshot(state), "investigations": available_investigations(state),
        "board": board_payload(state), "solved_deductions": state.get("solved_deductions", []),
        "recommendation": chapter_objective(state),
    }

def required_resources(ops: list[dict[str, Any]]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for op in ops:
        if op.get("op") == "stat" and op.get("key") in {"coins", "clues", "food", "lamp_oil"} and int(op.get("amount", 0)) < 0:
            costs[op["key"]] = costs.get(op["key"], 0) - int(op["amount"])
    return costs


def choice_block_reason(state: dict[str, Any], choice: dict[str, Any]) -> str | None:
    if not check_requirements(state, choice.get("requires")):
        return choice.get("blocked_text", "当前条件不足。")
    labels = {"coins": "金币", "clues": "线索", "food": "食物", "lamp_oil": "灯油"}
    for key, amount in required_resources(choice.get("ops", [])).items():
        if state.get(key, 0) < amount:
            return f"{labels[key]}不足：需要{amount}，当前{state.get(key, 0)}。"
    return None


def event_by_id(events: list[dict[str, Any]], event_id: str | None) -> dict[str, Any] | None:
    return next((event for event in events if event.get("id") == event_id), None) if event_id else None


def event_payload(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    choices = []
    for key, choice in event.get("choices", {}).items():
        blocked = choice_block_reason(state, choice)
        choices.append({"key": key, "text": choice["text"], "available": blocked is None, "blocked_reason": blocked})
    return {"id": event["id"], "title": event["title"], "text": event["text"], "first_time": event["id"] not in state["event_last_seen"], "choices": choices}


def available_legacy_events(state: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for event in events:
        if event["id"] == "final_choice" or event["id"] in STORY_EVENT_IDS:
            continue
        if event.get("location") != state["location"]:
            continue
        if event.get("once") and event["id"] in state["seen_once_events"]:
            continue
        if not check_requirements(state, event.get("requires")):
            continue
        last = state["event_last_seen"].get(event["id"], -99)
        cooldown = int(event.get("cooldown", 4))
        if state["day"] - last < cooldown or event["id"] in state["night_seen_events"]:
            continue
        result.append(event)
    return result


def choose_ambient(state: dict[str, Any]) -> dict[str, Any] | None:
    pool = []
    for scene in AMBIENT_SCENES.get(state["location"], []):
        last = state["auto_scene_last_seen"].get(scene["id"], -99)
        if state["day"] - last >= 2:
            pool.append(scene)
    return random.choice(pool) if pool else None


def auto_resolve_legacy_event(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    preferred = {
        "f_call": "B", "f_crow": "C", "f_tree": "B", "f_fire": "A",
        "f_stall": "C", "f_pool": "B", "f_shadow": "A",
        "s_train": "B", "s_machine": "D", "s_lost": "B", "s_bench": "C",
    }
    key = preferred.get(event["id"])
    if key not in event.get("choices", {}) or choice_block_reason(state, event["choices"][key]):
        key = next((k for k, c in event.get("choices", {}).items() if choice_block_reason(state, c) is None), None)
    if key is None:
        return {"id": "legacy_" + event["id"], "title": event["title"], "text": event["text"]}
    result, messages = resolve_choice(state, event, key)
    mark_event_seen(state, event)
    text = event["text"] + "\n" + result
    if messages:
        text += "\n" + "；".join(messages)
    add_journal(state, f"[自动插曲｜{event['title']}] {result}")
    return {"id": "legacy_" + event["id"], "title": event["title"], "text": text}


def mark_event_seen(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["event_last_seen"][event["id"]] = state["day"]
    if event["id"] not in state["night_seen_events"]:
        state["night_seen_events"].append(event["id"])


def resolve_choice(state: dict[str, Any], event: dict[str, Any], key: str) -> tuple[str, list[str]]:
    choice = event["choices"][key]
    messages = apply_ops(state, choice.get("ops", []))
    if event.get("once") and event["id"] not in state["seen_once_events"]:
        state["seen_once_events"].append(event["id"])
    return choice.get("result", "事情暂时告一段落。"), messages


def reset_night(state: dict[str, Any]) -> None:
    state["run_events"] = 0
    state["choice_events_this_night"] = 0
    state["night_seen_events"] = []
    state["flags"].pop("lamp_lit", None)
    state["flags"].pop("dark_mode", None)


def return_home(state: dict[str, Any], old: str, *, automatic: bool = False) -> tuple[str, list[dict[str, Any]]]:
    state["location"] = "林间小屋"
    state["day"] += 1
    reset_night(state)
    add_journal(state, f"从{old}返回林间小屋。")
    scenes = homecoming_scenes(state)
    text = "这一夜的探索已经足够。提灯自行转暗，把你送回林间小屋。" if automatic else "你回到了林间小屋，新的一夜开始了。"
    return text, scenes



def finish_field_action(state: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    if state["location"] == "林间小屋" or state["final_mode"] or state.get("pending_event"):
        return None, []
    state["run_events"] += 1
    limit = max(5, int(state.get("max_field_actions", 8)))
    if state["run_events"] >= limit:
        old = state["location"]
        return return_home(state, old, automatic=True)
    return None, []

def ending_scenes(ending: str) -> list[dict[str, Any]]:
    mapping = {
        "归途结局": [{"id": "end_return", "title": "归途", "text": "清晨第一次真正照进雾林。被归还的名字在现实里重新被人叫起，你带着已经熄灭的提灯离开小屋，门在身后安静合上。"}],
        "守夜结局": [{"id": "end_watch", "title": "守夜", "text": "你留在小屋。此后每当雾里有人迷路，窗边便会亮起一盏灯，而你会在第三下敲门前替他们打开门。"}],
        "终点结局": [{"id": "end_terminal", "title": "终点", "text": "你在列车上找回全部记忆。现实却失去你的姓名、照片和声音，只剩林间小屋偶尔梦见一位曾经住过的人。"}],
        "隐藏结局·林间入口": [{"id": "end_hidden", "title": "隐藏结局·林间入口", "text": "小屋没有关闭。它同时出现在现实和遗忘之地，成为一扇可以往返的门。无脸旅人、白鹿、站务员、守夜人与影子都在第一夜回来，帮你把长桌搬到窗边。"}],
    }
    return mapping.get(ending, [])



def state_options(state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    pending = event_by_id(events, state.get("pending_event"))
    if pending:
        return {"ok": True, "message": "当前来到真正需要决定路线的节点。", "event": event_payload(state, pending), "state": state_summary(state)}
    actions: dict[str, Any] = {"status": True, "journal": True, "story": True, "board": True, "pin": True, "connect": True, "deduce": True, "save": True}
    if state["location"] == "林间小屋":
        actions.update({"travel": state["unlocked_locations"], "eat": state["food"] > 0, "rest": True, "work": state.get("last_work_day", 0) != state["day"], "refill_lamp": state["day"] - state.get("last_lamp_refill_day", 0) >= 3, "buy_lamp": state["coins"] >= state.get("lamp_shop_price", 3)})
    else:
        actions.update({"light": state["lamp_oil"] > 0, "explore": True, "explore_dark": True, "return": True})
    actions.update(available_investigations(state))
    return {"ok": True, "message": "自动剧情已经留下可操作现场。你可以自由调查、使用物品、等待变化或在线索板上推理。", "actions": actions, "state": state_summary(state)}


def command_help() -> dict[str, Any]:
    return {"message": "《林间夜行》v1.1 指令。自动剧情负责制造现场，玩家通过调查、物品、推理与少量关键决定推动故事。", "commands": [
        'cmd("options")                         # 查看当前位置的可操作现场',
        'cmd("travel 雾林")                     # 前往地点，首次进入自动播放章节场景',
        'cmd("inspect 树皮") / cmd("open 门")    # 观察或打开现场对象',
        'cmd("take 白色字片")                    # 取得已经发现的物品',
        'cmd("use 空白车票") / cmd("give 白色字片 无脸旅人")',
        'cmd("follow 白鹿") / cmd("listen 广播") / cmd("wait 下一班列车")',
        'cmd("adjust 旧怀表 00:13")              # 小型谜题：调整物品',
        'cmd("combine 车票残角 空白车票")         # 拼合物品',
        'cmd("board")                            # 查看证据、连接与推理进度',
        'cmd("pin 半句纸条")',
        'cmd("connect 姓名时刻表 | 广播中的遗忘物")',
        'cmd("deduce 列车运送名字和记忆")',
        'cmd("trust 影子") / cmd("confront 影子") # 真正有意义的路线态度',
        'cmd("light; explore")                   # 普通随机插曲自动播放',
        'cmd("choose A")                         # 只在最终路线节点使用',
        'cmd("return") / cmd("story") / cmd("status") / cmd("journal")',
        'new_game("RESET")                       # 重置并自动播放序章',
    ]}


def perform_action(state: dict[str, Any], events: list[dict[str, Any]], action: str, args: list[str]) -> dict[str, Any]:
    action = action.lower().strip()
    if state["hp"] <= 0:
        old = state["location"]
        state["hp"] = max(4, state["max_hp"] // 2)
        message, scenes = return_home(state, old, automatic=True)
        save_state(state)
        return {"ok": True, "message": "体力耗尽。" + message, "scenes": scenes, "state": state_summary(state)}
    if action in {"help", "-h", "--help"}:
        return {"ok": True, **command_help(), "state": state_summary(state)}
    if action in {"status", "story"}:
        return {"ok": True, "message": chapter_objective(state), "state": state_summary(state)}
    if action == "options":
        return state_options(state, events)
    if action == "board":
        return {"ok": True, "message": "线索板", "board": board_payload(state), "state": state_summary(state)}
    if action == "pin":
        if not args:
            return {"ok": False, "message": "请提供要钉在线索板上的线索名称。", "state": state_summary(state)}
        message = pin_evidence(state, " ".join(args)); save_state(state)
        return {"ok": True, "message": message, "board": board_payload(state), "state": state_summary(state)}
    if action == "connect":
        raw = " ".join(args)
        if "|" in raw:
            left, right = [x.strip() for x in raw.split("|", 1)]
        elif "+" in raw:
            left, right = [x.strip() for x in raw.split("+", 1)]
        elif len(args) >= 2:
            # 尝试在每个切分点找到两个已知线索名
            left = right = ""
            for i in range(1, len(args)):
                a, b = " ".join(args[:i]), " ".join(args[i:])
                if evidence_id_from_text(state, a) and evidence_id_from_text(state, b):
                    left, right = a, b; break
            if not left:
                return {"ok": False, "message": "请用 connect 线索1 | 线索2。", "state": state_summary(state)}
        else:
            return {"ok": False, "message": "请用 connect 线索1 | 线索2。", "state": state_summary(state)}
        message, raw_scenes = connect_evidence(state, left, right)
        scenes = play_scenes(state, raw_scenes)
        save_state(state)
        return {"ok": True, "message": message, "scenes": scenes, "board": board_payload(state), "state": state_summary(state)}
    if action == "deduce":
        if not args:
            return {"ok": False, "message": "请输入要验证的推理。", "state": state_summary(state)}
        message, raw_scenes = solve_deduction(state, " ".join(args))
        scenes = play_scenes(state, raw_scenes)
        scenes.extend(process_milestones(state))
        save_state(state)
        payload = {"ok": True, "message": message, "scenes": scenes, "board": board_payload(state), "state": state_summary(state), "next": chapter_objective(state)}
        if state.get("pending_event"):
            payload["event"] = event_payload(state, event_by_id(events, state["pending_event"]))
        return payload

    pending = event_by_id(events, state.get("pending_event"))
    if pending and action != "choose":
        return {"ok": False, "message": "请先处理当前关键节点。", "event": event_payload(state, pending), "state": state_summary(state)}

    if action == "travel":
        if state["location"] != "林间小屋":
            return {"ok": False, "message": "必须先返回林间小屋。", "state": state_summary(state)}
        loc = " ".join(args)
        if not loc or loc not in state["unlocked_locations"] or loc == "林间小屋":
            return {"ok": False, "message": f"地点未解锁：{loc or '未提供'}", "state": state_summary(state)}
        state["location"] = loc
        state["run_events"] = 0
        scenes = first_visit_scenes(state, loc)
        add_journal(state, f"从林间小屋进入{loc}。")
        save_state(state)
        return {"ok": True, "message": f"你进入了{loc}。" + ("章节场景自动播放。" if scenes else ""), "scenes": scenes, "state": state_summary(state), "next": chapter_objective(state)}

    investigation_actions = {"inspect", "open", "take", "use", "follow", "listen", "wait", "adjust", "combine", "ask", "give", "trust", "confront"}
    if action in investigation_actions:
        if not args:
            return {"ok": False, "message": f"请提供对象，例如 {action} 时刻表。", "state": state_summary(state)}
        target = " ".join(args)
        if action == "combine" and "+" not in target and len(args) >= 2:
            target = " + ".join(args)
        before = set(state["inventory"])
        action_location = state["location"]
        message, raw_scenes, effects = action_scene(state, action, target)
        if message.startswith("当前无法"):
            save_state(state)
            return {"ok": False, "message": message, "state": state_summary(state)}
        gained = set(state["inventory"]) - before
        scenes = play_scenes(state, raw_scenes)
        for item in gained:
            reaction = item_reaction(item)
            if reaction and reaction["id"] not in {s["id"] for s in scenes}:
                scenes.extend(play_scenes(state, [reaction]))
        scenes.extend(process_milestones(state))
        auto_message, home_scenes = finish_field_action(state)
        scenes.extend(home_scenes)
        add_journal(state, f"[{action_location}｜{action} {target}] {message}")
        save_state(state)
        payload = {"ok": True, "message": message + ((" " + "；".join(effects)) if effects else ""), "scenes": scenes, "state": state_summary(state), "next": chapter_objective(state)}
        if auto_message:
            payload["message"] += "\n" + auto_message
        if state.get("pending_event"):
            payload["event"] = event_payload(state, event_by_id(events, state["pending_event"]))
        return payload

    if action == "light":
        if state["location"] == "林间小屋":
            return {"ok": False, "message": "先 travel 到探索地点。", "state": state_summary(state)}
        if state["flags"].get("lamp_lit"):
            return {"ok": True, "message": "提灯已经点亮。", "state": state_summary(state)}
        if state["lamp_oil"] <= 0:
            return {"ok": False, "message": "灯油不足。可回小屋补给或使用 explore_dark。", "state": state_summary(state)}
        state["lamp_oil"] -= 1
        state["flags"]["lamp_lit"] = True
        state["lamp_history"].append({"day": state["day"], "action": "light"})
        save_state(state)
        return {"ok": True, "message": "你点亮旧提灯。下一次 explore 会更安全。", "state": state_summary(state)}

    if action == "explore_dark":
        if state["location"] == "林间小屋":
            return {"ok": False, "message": "先前往探索地点。", "state": state_summary(state)}
        state["hp"] -= 1
        state["flags"]["dark_mode"] = True
        state["lamp_history"].append({"day": state["day"], "action": "dark"})
        if state["hp"] <= 0:
            return perform_action(state, events, "status", [])
        return perform_action(state, events, "explore", [])

    if action == "explore":
        if state["location"] == "林间小屋":
            return {"ok": False, "message": "请先 travel 到地点。", "state": state_summary(state)}
        if state["final_mode"]:
            return {"ok": False, "message": "普通事件池已经关闭。最后一班列车正在等待决定。", "event": event_payload(state, event_by_id(events, "final_choice")), "state": state_summary(state)}
        lamp_lit = bool(state["flags"].pop("lamp_lit", False))
        dark_mode = bool(state["flags"].pop("dark_mode", False))
        if not lamp_lit and not dark_mode:
            return {"ok": False, "message": "前方太暗。先 light，或用 explore_dark。", "state": state_summary(state)}
        if lamp_lit and random.random() < 0.35:
            state["clues"] += 1
            add_journal(state, f"[{state['location']}｜提灯细节] 额外线索+1。")
        legacy_pool = available_legacy_events(state, events)
        ambient = choose_ambient(state)
        scenes: list[dict[str, Any]] = []
        if legacy_pool and (ambient is None or random.random() < 0.35):
            event = random.choices(legacy_pool, weights=[float(e.get("weight", 1)) for e in legacy_pool], k=1)[0]
            before = set(state["inventory"])
            scenes.append(auto_resolve_legacy_event(state, event))
            for item in set(state["inventory"]) - before:
                reaction = item_reaction(item)
                if reaction:
                    scenes.extend(play_scenes(state, [reaction]))
            scenes.extend(process_milestones(state))
        elif ambient:
            scenes.extend(play_scenes(state, [ambient], mark_seen=False))
        if scenes:
            auto_message, home_scenes = finish_field_action(state)
            scenes.extend(home_scenes)
            save_state(state)
            return {"ok": True, "message": "发生了一段无需选择的夜行插曲。现场随后留下了新的可调查痕迹。" + (("\n" + auto_message) if auto_message else ""), "scenes": scenes, "state": state_summary(state), "next": chapter_objective(state)}
        auto_message, home_scenes = finish_field_action(state)
        save_state(state)
        return {"ok": True, "message": "这一带暂时没有新的痕迹。" + (("\n" + auto_message) if auto_message else ""), "scenes": home_scenes, "state": state_summary(state)}

    if action == "choose":
        event = event_by_id(events, state.get("pending_event"))
        if not event:
            return {"ok": False, "message": "当前没有待选择事件。", "state": state_summary(state)}
        if not args or args[0].upper() not in event["choices"]:
            return {"ok": False, "message": "请提供有效选项字母。", "event": event_payload(state, event), "state": state_summary(state)}
        key = args[0].upper()
        choice = event["choices"][key]
        blocked = choice_block_reason(state, choice)
        if blocked:
            return {"ok": False, "message": blocked, "event": event_payload(state, event), "state": state_summary(state)}
        before = set(state["inventory"])
        result, messages = resolve_choice(state, event, key)
        mark_event_seen(state, event)
        state["pending_event"] = None
        state["choice_events_this_night"] += 1
        gained = set(state["inventory"]) - before
        scenes: list[dict[str, Any]] = []
        for item in gained:
            reaction = item_reaction(item)
            if reaction:
                scenes.extend(play_scenes(state, [reaction]))
        scenes.extend(process_milestones(state))
        if event["id"] == "final_choice" and state["completed_endings"]:
            ending = state["completed_endings"][-1]
            scenes.extend(play_scenes(state, ending_scenes(ending)))
        add_journal(state, f"[{event['title']}] 选择{key}：{result}")
        save_state(state)
        return {"ok": True, "message": result + ((" " + "；".join(messages)) if messages else ""), "scenes": scenes, "state": state_summary(state), "next": chapter_objective(state)}

    if action == "return":
        if state["location"] == "林间小屋":
            return {"ok": True, "message": "你已经在林间小屋。", "state": state_summary(state)}
        old = state["location"]
        message, scenes = return_home(state, old)
        scenes.extend(process_milestones(state))
        save_state(state)
        return {"ok": True, "message": message, "scenes": scenes, "state": state_summary(state), "next": chapter_objective(state)}

    if action == "eat":
        if state["location"] != "林间小屋": return {"ok": False, "message": "只能在林间小屋吃东西。", "state": state_summary(state)}
        if state["food"] <= 0: return {"ok": False, "message": "没有食物了。", "state": state_summary(state)}
        state["food"] -= 1; state["hp"] += 3; clamp(state); save_state(state)
        return {"ok": True, "message": "你吃下一份食物，体力+3。", "state": state_summary(state)}
    if action == "work":
        if state["location"] != "林间小屋": return {"ok": False, "message": "只能在小屋整理旧物。", "state": state_summary(state)}
        if state["last_work_day"] == state["day"]: return {"ok": False, "message": "今晚已经整理过旧物。", "state": state_summary(state)}
        earned = random.randint(2, 4); state["coins"] += earned; state["last_work_day"] = state["day"]
        add_journal(state, f"整理旧物，金币+{earned}。"); save_state(state)
        return {"ok": True, "message": f"你整理旧物，金币+{earned}。", "state": state_summary(state)}
    if action == "rest":
        if state["location"] != "林间小屋": return {"ok": False, "message": "只能在林间小屋休息。", "state": state_summary(state)}
        state["day"] += 1; state["rest_count"] += 1; state["hp"] = min(state["max_hp"], state["hp"] + 2); reset_night(state)
        scenes = homecoming_scenes(state); save_state(state)
        return {"ok": True, "message": "你睡到下一夜，体力+2。", "scenes": scenes, "state": state_summary(state)}
    if action == "refill_lamp":
        if state["location"] != "林间小屋": return {"ok": False, "message": "只能在小屋领取灯油。", "state": state_summary(state)}
        if state["day"] - state["last_lamp_refill_day"] < 3: return {"ok": False, "message": "补给还没有准备好。", "state": state_summary(state)}
        state["lamp_oil"] += 1; state["last_lamp_refill_day"] = state["day"]; save_state(state)
        return {"ok": True, "message": "你在柜底找到一小瓶灯油。灯油+1。", "state": state_summary(state)}
    if action == "buy_lamp":
        if state["location"] != "林间小屋": return {"ok": False, "message": "请先回小屋。", "state": state_summary(state)}
        price = state["lamp_shop_price"]
        if state["coins"] < price: return {"ok": False, "message": f"金币不足，需要{price}。", "state": state_summary(state)}
        state["coins"] -= price; state["lamp_oil"] += 1; save_state(state)
        return {"ok": True, "message": f"花费{price}金币购买灯油+1。", "state": state_summary(state)}
    if action == "journal": return {"ok": True, "message": "最近10条夜行日记", "journal": state["journal"][-10:], "state": state_summary(state)}
    if action == "save": save_state(state); return {"ok": True, "message": "已保存。", "state": state_summary(state)}
    if action == "reset":
        if not args or args[0] != "RESET": return {"ok": False, "message": "重置需执行 reset RESET。", "state": state_summary(state)}
        state.clear(); state.update(clone(INITIAL_STATE)); save_state(state); return run_prologue(state)
    return {"ok": False, "message": f"未知动作：{action}", **command_help(), "state": state_summary(state)}


def _human_text(payload: dict[str, Any]) -> str:
    lines: list[str] = [payload.get("message", "")]
    if payload.get("scenes"):
        for scene in payload["scenes"]:
            lines.append(f"\n【{scene['title']}】\n{scene['text']}")
    if payload.get("event"):
        event = payload["event"]
        lines.append(f"\n【{event['title']}】\n{event['text']}")
        for choice in event["choices"]:
            suffix = "" if choice["available"] else f" [不可用：{choice['blocked_reason']}]"
            lines.append(f"{choice['key']}. {choice['text']}{suffix}")
    if payload.get("board"):
        board = payload["board"]
        lines.append("\n【线索板】")
        if board.get("evidence"):
            for item in board["evidence"]:
                mark = "📌" if item.get("pinned") else "·"
                lines.append(f"{mark} {item['name']}：{item['text']}")
        else:
            lines.append("尚未记录线索。")
        for link in board.get("links", []):
            lines.append(f"↔ {link['a']} ⇄ {link['b']}")
        for theory in board.get("deductions", []):
            status = "已成立" if theory["solved"] else f"证据{theory['progress']}"
            lines.append(f"◇ {theory['title']}（{status}）")
    if payload.get("actions"):
        lines.append("可执行：" + json.dumps(payload["actions"], ensure_ascii=False))
    if payload.get("commands"):
        lines.append("完整指令：")
        lines.extend(f"- {command}" for command in payload["commands"])
    if payload.get("journal"):
        lines.extend(f"第{item['day']}夜：{item['text']}" for item in payload["journal"])
    if payload.get("state"):
        s = payload["state"]
        lines.append(f"\n{s['chapter_label']}｜第{s['day']}夜｜{s['location']}｜体力{s['hp']}/{s['max_hp']}｜金币{s['coins']}｜线索{s['clues']}｜灯油{s['lamp_oil']}｜夜钥匙{s['night_keys']}/3")
        if s.get("recommendation"):
            lines.append("当前目标：" + s["recommendation"])
        if s.get("investigations"):
            pretty = "；".join(f"{k}: {', '.join(v)}" for k, v in s["investigations"].items())
            lines.append("可调查：" + pretty)
    if payload.get("next"):
        lines.append(payload["next"])
    return "\n".join(x for x in lines if x is not None)

def _parse_one(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split()
    return (parts[0], parts[1:]) if parts else ("help", [])


def cmd(command: str, *, as_json: bool = False) -> str | dict[str, Any]:
    events = load_events()
    state = load_state()
    if not state.get("prologue_complete"):
        payload = run_prologue(state)
        return payload if as_json else _human_text(payload)
    commands = [part.strip() for part in command.split(";") if part.strip()] or ["help"]
    results: list[dict[str, Any]] = []
    for raw in commands:
        action, args = _parse_one(raw)
        payload = perform_action(state, events, action, args)
        results.append(payload)
        if not payload.get("ok") or payload.get("event") or payload.get("scenes"):
            break
    if as_json:
        return {"ok": all(x.get("ok") for x in results), "results": results, "state": state_summary(state)}
    blocks = []
    for i, payload in enumerate(results, 1):
        prefix = f"--- 指令{i} ---\n" if len(results) > 1 else ""
        blocks.append(prefix + _human_text(payload))
    return "\n\n".join(blocks)


def new_game(confirm: str = "") -> str:
    if confirm != "RESET":
        return '重置被拒绝。请调用 new_game("RESET")。'
    state = clone(INITIAL_STATE)
    save_state(state)
    return _human_text(run_prologue(state))


def state() -> dict[str, Any]:
    return state_summary(load_state())


__all__ = ["cmd", "new_game", "state"]

if __name__ == "__main__":
    import sys
    raw = " ".join(sys.argv[1:]).strip() or "help"
    print(cmd(raw))
