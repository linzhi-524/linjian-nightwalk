
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《林间夜行》v0.6 追踪与叙事增强版
给 AI 当玩家的长期文字探索游戏。
"""

from __future__ import annotations
import json
import random
import gzip
import base64
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

BASE = Path(__file__).resolve().parent
SAVE_FILE = BASE / "save.json"

INITIAL_STATE: dict[str, Any] = {
    "version": "0.6",
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
    "pending_return_prompt": False,
    "last_work_day": 0,
    "event_last_seen": {},
    "night_seen_events": [],
    "quests": {},
    "item_notes_seen": [],
    "lamp_history": []
}

TITLE_RULES = {
    "勇敢": ("提灯者", 5),
    "谨慎": ("雾中归人", 5),
    "善意": ("林间守望者", 5),
    "贪心": ("拾荒之王", 5),
    "好奇": ("门后之眼", 5),
}


ITEM_DESCRIPTIONS = {
    "旧提灯": "灯芯偶尔自行发亮，像在替某个看不见的人指路。",
    "折叠小刀": "刀刃不算锋利，但足以割断细绳和藤蔓。",
    "干面包": "硬得像木片，仍能在最糟的时候撑住一晚。",
    "空玻璃瓶": "瓶底有一圈洗不掉的灰白雾痕。",
    "生锈钥匙": "齿纹已经模糊，像是开过一扇不存在的门。",
    "黑羽标记": "羽毛表面没有光泽，握久了会变得微温。",
    "旧怀表": "指针停在一个不存在的时刻。",
    "车票残角": "边缘焦黑，目的地一栏被撕掉了。",
    "守夜人的徽章": "背面刻着一句被磨平的话。",
    "湖边石片": "表面有水波一样的纹路，离开湖边也不会干。",
    "银色铃铛": "摇动时没有声音，却能让附近的雾散开一点。",
    "蓝火柴": "燃烧时不会发热，只会照出被隐藏的轮廓。"
}

QUEST_DEFINITIONS = {
    "lost_name": {
        "name": "失落的名字",
        "description": "寻找与一个被遗忘名字有关的物品。",
        "progress_text": "尚未找到与名字有关的物品"
    },
    "night_keys": {
        "name": "三把夜钥匙",
        "description": "收集三把夜钥匙，找到通往沉睡湖的路。",
        "progress_text": "夜钥匙 {night_keys}/3"
    },
    "station_truth": {
        "name": "旧车站的真相",
        "description": "拼合旧车站留下的线索。",
        "progress_text": "线索 {clues}/5"
    }
}

# 事件库经过压缩编码，目的是减少 AI 玩家在运行前无意中看到剧透。
# 这不是安全加密；有意解码仍然做得到。请遵守 AI_PLAY_GUIDE.md 的公平游玩规则。
_EVENT_BLOB = """ABzY8xqL!u0{`t@S#u&swtnwl(b2E=OxWG_Jos&9e#VU(1eQ>XXbE}%xv#Io5zs<x5{njugg^_DT4-UB8cB#n{Fj-^tg0vfg?mmWLI|pgrPw52M~9=k7BVZ($&=@NXZ!8d>(_67G1=^9tL4p4uit$4*SBxJ#cQTtOcsY7F8vq$>-Fp3*#F_Wc^V&^F-#ff=Gc?$>YR1T=&1jMymL=?V~_V7X2+bVenTi`$ZCZ|f=#zg|Kq6NmAxx8;TK9J5<Vy1l2F|j<8FAEWMY3*R>)yq-uo()LsIFSL_$JkpC*t0<NW;iQ&Y26^OOlE{V-j)`1dFOY#Na4?2@BG<85}&X0k8LvAZz1RK1XDUKp);5cZh$<KxOa{P)|Ff3b(~ccx~ImMPPd*V)~lZE$_o)c!k4zs26bpZo5wKYpup@8O$hY+rI0X>17=Q9R!!i8No<)-TZf60KP@eVN^1bSVBPd**}bSN8dH3-FDqPZ{T}3l^OD_o|OPe41FQiG|cR-@j3O@b_=~`2>f}Xzu(C<hV+Xy(;4>T>bA?UCgd;5_9esPfI{+q38rc!`_gbU#0sy5-gDQpmcr9_E-@%%-HBY`>_k6|K)8*steV164?36+h<AjS6WXr-+jE(^hIy}p(?oo`=oX*x#Ki*tRcVX)d7f8F6Q)zFhzoE5W0!LZQHt)ur1rUg`g@EQYPTTjHG;;E`{FoxY++xTWs<3olwfsa71+F#EhTZFR3j#JV2KG;?fD8U9dBYXLKn=f&sc5#B;2ANivb4(P7Rw|IuJI&-F(Qm^!_>>yH{UbH?|o)3VPRr>&n13l`82KA5K4pZmoKCj>m{uq~Jd&I)ANOQR_bR%oH*zZT547X5)Q6OLjx%$qH3_g*(f0nx2G(Bt19{?_=sH&)aSetJD)oU@x67eATI?`M%T?_M=M-L8e%te<++!brFxuN{+>ZQx1aZbdGBY1hU0b+T0e)d8LtlfcYQ8VHCRd-8^lzpg{`5;xNF;hyL}6-q}mm{JvCd=}w~be-qV!$~Jbw}s+z`xFMcnP#lk>HannpJ#s?$?P!A8;sKmBjX*uaF6Rhc)>|F-P9e{zgtis*bNq|#iXEOys=mfY<XX)9gV;Dco^oBQZ7mZ>q0f$!p{mvqJNb{R_Shz?j|QmtN%e$<wHa0d{1=W)W5RiQRe?aXm_ei*aI_;LOqiTXQZ|`I;H$?+7#lVD(VK>0JYfZzYJ=+e7Fn3Yr?hg@4MB)zkilw)~SW7Du!e=Am#j=@?6~$Pqs+TqkWvwjT_(y{^a9vR$dkFt90KhW%GK(Qs)z-d8C0Wd#H^V?4~K3$uVk0Pr+DIA?-l*FNe)!>Q(=8u7N&<!ZTU}6^!n$w(DPTk?!9Kl_DHg<meQPeP9(hvPk#_Y<zjGEY)^MVy^|*=}`-#E1RU^q+gHWm$Z&dc+8gvxkmPurC1oWn-^tE4jiA;MsI|opYFy<_=pr;v>XRI($ES>xbXpWR<orWfbLz#Lqhhh!bg4cZggkz4?lKNn~-_EC32Lgn>?wI==Y9SZEBg!5RbOe%GGXkb+H@;k)t7O-~p-T1z|&-XCMUiNScv?L}(kImc&q5Tw4^^Z|KH7Nu=viytu3i7_Hw3#f;>NBV-$1Meqm@ggZHLrCSTIndYs(m^4hurs)pHSmht0-<-tXvm4Oeq+m^|f5sD&^2ty?b1cfxEGHOL+WcckfWDQ6x0*`B418ygN&}yt<c^bI9(Y8G9E+~=cD;f4gLLx_eP~4|+4m4%T=cj_R|Z~z=h252EbyNa%4MM%<v*xLhlnJ^LJFos5_wIt`yO=&P?F14l8@8G841T|H4F3NfXTR!oK8SatGh{u?32Afo4ok>PV_Fe(60?gJ{R42{=87if^c|&sB!;_;M)#*;5Tmvhy9-~6JJ^UQr14T>W&sy0<5`-II;$6;{c_4cJ;$mIaVMWS*dU$lrjny&R&9qK_Uc*XB*6+KPqv$Tm!=xapwJ7kW|9mp7h1V&0`W-5i=mNZi%yksC6+R9oO{W&+J#f=L#!YR%~byeqRGTEFICUb&_47zTr7>l$G)BfM@nGLj#`q+6+t&<OHC}1Mbyt(16BH;3OeC_v0mlV$ec&B9VR1u*kso+v6e)O3n#or*P+!7pp=s2!v2ue40p${uQZOhCgIIh*&4+8Hc(cD@{OY)@m`?9fn`bcC*838!@IdJbA0F9!{G~wjRZ;lsYFnd7&CcKXX1T-_;a!Lv|gN$E6xPFR#0VVp6Q^!&|WZ<ZZW9TSfIS;ip?6x^<6&wp0=?%es|B;=iJs89pG5u9EDc8iVmU(i<N+x>Su_8r+FmcX(;28iPhik+ufA@t58_;e$4sXkd$k_hGS#&p9wZ96fZ>y<^Tt^7gH~b*ZH>Eqf65W-Nhb$=wauzhWpau7r^3fJxh!ZU|U78-C!*Yp2tr)8Wy(&7m&Wi$OWL4+PO5g-}b<6_<3I1T}Y}l~>#sy~@&$R_k0}rZ#b|k?JMFG5G?mDk-q+y0lp3@ji(4B+}f%hAXh}Jb+b?Z5;?u|FTdiB1oLaPz+VE>B$q%EuSoj?BW;rm!+lX^NCwUk>K7VzC0orekV<wAshoAR9uohYm@Ci?KX(<o41n^LP~OLaPDz8l6;m{2oD^@3M(Fj?H13R24=2$B<gcLPm=F^ypg0d5G6~;-_zYVw;xqCe~>@P6ur*!&_)tIrs)ImYd}u9rL^;<*~8D}co+AJVk*RGqfI&K@H446@pxJc1O4C%2fBx>U_}!!ypo@50ID<|?S@&a-C>?HO<Gv#kSs$UOxvSABf4@3p|R*=g-B1HW5e#!+y+ftfc{OFQt0nzk;^(180q9Q$?dg_+^V|pkw3ff&x#j=^A59!aqJZ6?Ik&Kj}7GMc^^-pyLBTC79R1HFpNZ-4DeWf6AX1=6_5{NB`TL!CI1!bz@^%Y3i#+Ow)jU6+KGUUxLk*A;7XCBAk7?-V(}T8VhwsJ;}Z3_;C4)+ElJ>2>r{T%_NN-BOmil?y;no8Iae<3mU6fB^0R`W$Ni<H4U*mBm>4{X_R3C8C~u-?b7z<5DC+S@WHv}?Lklno9plz4dH(H8kfTc}Qf;J0{@a-x8UQ<EwoDr=#`%$-u$@BDd-T1=!@_+{EN=tFr0ZLuc*d7bRcT^OL9%{1xlIyzSbP$W!Qww7gSxyaJ6${!8MJ#EI1(?uj5qM9zTenPCdCq#KOX`!$Q#>IF2`8{6l6Fsxf@c9Vg@bGtsI+${K;muyjR|XJ=n?P4V9+LYhpR6z1!%OUoLOKZsTd!I&&7arCR;KFxX5p3-<o8_`VNHZU2weYU@3-9(87>Fk?(jEUlpF155k8By%M1+`u2yN)l;!ODJaeD`*`?LSPy;yn+1a)0gPgoFxJ#X!F!s*Z^+9_;f3W3aH-;;zB+QAqIH2NtXP>4~Wy5TZO!(VNDD<3{G|O{e;1_Wcl@Ibb#d+I;Nqt2C1>QLh2moEPXxzMPBxXX<!HRC|)6AOy)+XxT4l1^bsQoU8STXaMgukfCpGe**po~YV0?f1RXXcdsh%5Vs3pJz2a_tcztN{7bTow-e~*qVzNZEaU1+pkUt;ie(lGvzYCTD+9ywm*^J--!Rf^Tr+MQ^8pF^gaui3%mXTCCSdq6^V0W{6DsfW$!c`u9WmIUujrdX~Ce`jV_B*+c@eoj&y(UXvg;IzQj-jaxPkCWLkLCtIZO$-jwm9@_9$lgQ>tATd-%%Q1SrIsHqgTXRCWm?AO6W9s^a=sC*(SX{1o1FY>pdg4mkpa-BZ7)8bWys_lT;eE4AZ(I+^qtJnz&s>*bVkYd!EW*!TIKq-b^AyK46gPk>7fRmsre>&E#0HS$a+NW8qAs5|wUq?SdPGJB_Y_snZDBYE*0jB?xmvk4n@XMqTN44@A5kB>r|!j)%1Zud<7995hGjgC#+-ezKINU;SdDqK6k}O~yIH%)*>Pl=)K)i)2@DK!$=2+;0c$WOwv+3<$LYp<EtdDgX(efiM=TVc-iynl-d!c#Oe*C>@dqG<Zwy-9vWT0mt6E6$4BsPxwmNQ(#@~0R8$dWMz=V#Bw7;Unf@&48R<f{Cf;N>`?$RZDj_w$#k#s?<r8-E&`j+AVedY5P7gjh(Cx~ao!TS&$b`{y@yiqL4?u~M}f7mD6#AV1(hxzGvwdX4(|^KfzWv(caf6EzD~N{7mq4Kz&KPTXdO?_dw3b4Mha}596U^JC`$If7BGN(8f(#v#e>mxY;pgm30FOZS`y)E&OB<8u(8ot&N&HhfmKF#3PLG6M0X>v;4#7=>kp=nj-H)X{hvW{EDHifOzhFjVMhZ1p2X8XS3m=tI~*=|QP#L?z%E=Xz!Qx*8pmc5zwKlazkM@_;LLzeOl9Y1lkxsa0mD_rX;s8~cSo?zYIPWXHrn1B&Al2SjVyG=Q%~xxJu0NmHF0APo~-AeAC!4wNK35(v`JV6L>@IHJN<O|RF8XLC5zA%&l6WWklFNU@}9@9@rjU#kNP5w*$w?<R!n98c3?lRSrXzIcpnrf$gXRCm!6VuETM=qs#eTIAcbuIz`7(@K$Ckn35FE$tqGN*KarzBsg9POn5IrC(ZutWWaBjcnZ|B}Vo*%w;Z%EpF-@w{UX}N|5%_k)6guaWB|VLuNYyXm`L>e9<w`IF=?3czfGm&Q$ZLBF&=Y%~9G$>j{>pdX{q)^;C|^(3<TamA4&u+Gjz}P_2X@LY(r5uE5i6)0TrfqSc;*t_H`49bmH`KBlq;zi-%eT-qYj*(Wz}&KYJp0jThROE^&9@=u#@cS!wfR14a7;uatw4a0L=7ErH-a-aG0k)G*#H^S~y_AcoynNHnQSzT0D!9@Sy@I!>-puK}uOHR_DrLhW^0{YHO<=UJjU4_OV_LD77%&u^utOQ~&wTsMbVj8cK>(rP>YytCw}=2Y2BnX&QKN8#Q_btE~F14+KC`v8ER!xXE!64g(L{VcIF{=542}o3}4I>t+z;V1^|cY^nyLrrHobBfh*?_Hng=_+s#=LMU`>AN|7YE_|Mx+{e}v@b^#(Tet8)>ANkGP3e#ZAY+;bZ-ub<;LKMgp4PBfTro&8TcEC>MH)YmUF$DOt?#Bb3nSa!*GUOa>QEwpGfX$t!hkJhR}8%f2P-rg8nU9&G}7Q?g=WJD&dj{rMWYrl2_KV8<c~_6(-qk}k>>8W7ANpzN68F5uF7thH%`r(EvDY(9YW@Tv{X2SgOw&q3X(2SBHL*ci@{B-O|_M#v155BP4k8SI9)u7itAD|^#!hAMZ27vc<~BIAezzRtrG6?%>({X@x6N}Rpr+z<Zy?+;-^y`mxl1JlZNnaNDi*1uOFD$f`x6NIFRJW?n%<dF5{xgkDaLU<B-Z$JzaoF$(#JA)&^|b&_MIIJ#0fwf$$R4^)5DJ+Zv4ih_D%_&DMSt;vi;Xu4U*37Q!NTHTb)N--KPqqG_8M*^95hVS(v^#UK_h<i3(7{gfa0dP-?6eU)RGmg%%=6}iuHavMAM@Yvsxn2aMg&;Fs&))BKQwU>z9<xk@A?pqbg7Z?(>QxNx#fmad1PNb#UwoZIO(@)KK(_pmNKbdT!Z;drrktvo>#Bzp2F0_0Ckqha>Rqu?JT^1{>MP(%TCrdBqAB_v(_l_JpoU_{dKn}TWB>GS3@{XMHkR!KRMOPF%`-l)q*&@mx_7;MNxiBmLd?PPbdC6Cli;)%GnbRCR<Uh$HVIK1e{HJ8y)e#8ih9-PIbvmVk^l+`r#xMg9ce0tLtnV%6|9vKsL|uLtv!u37qXjYI;q22ft3=Em;KQpdKc5Bbz9^A0+OX!aW$*t}yU09oR^+wIj(b|Hm8t)p3!_O&*Z*6``gaWV`k_&ZYvMb?{LpPjm>*t#cR20-eNyI&yuQd=Gyi`txN#D-p8^L1wMT(eGc$d-ZtML&im29r{unrb(@w#4`*5p)w2Q}>*Dq8(@Ge%{51;YwAZQYnJz^!P#~206{;2fCL8>B``CWRQ6+?M=OO8jdlNd}kJjB}J=ILpZ#qe>?=$NtE=EqrYS>1=+XOo&{r+d#O!RpARQ~<^Kv#JmJfs=&$6RC8Lc{Ua2OG7S48Zw7vO-kpob5Xio)eM}w!hNNCZ#=j7#IY3Hw;QI6_CEYa@`j5S+vn~=F?*@xEI$$BS-1rzu~6Bk$z$xAaG!1DR}ZeP3iYpRL?pmussE5v?sV?pkyKF`ZIvuu`GS|65z03-;e%Z#hJy+nsRp5^^-wFTX(p3WD+_Uwos?Y0Qj$U$nI20Aoh3kAjjcG=g5`t7`pIILvYCvI1=~cG$a-OQeNb-g?2?db#62(s$wc58CgDm9=e;61kGSvpGu8IM6U8uPogPv48Frpz#|)Np+1c&fitp+3*aYNqdB~A952qy`csMIQYaK+s-yorO>)iCbv5#OpnsAaxh)3AU(HcEkQV8I8x>zC7LLKtHy%Nh|?2(3*0{kTCB6kHH`h~oGhKY*F2yWs^oVZnM6x1h@y^^kPQR4x<_1-CzmdB&IcEVr3c?RX+C$D;Hz0o}|1an^t#UStm=(E~9(FkiJ;WHlD_P`%i@qB;iUY5p4Zw8#_%cAlyByaspqa{mYgQ9ym5U8j6da%ArvjML&qEAyS+D%hd%d`Rh)pMz-Z=ZWOVL$TvXA@W$y^CugCn=o>)gX<zSTVDrlv-AR=Gb)%lV<pvP_7E)py<A##Zz&SRp3mf$jXv#PiQypP8j@|wcQ;XoYSF&B`?~g-8%(i!dTul@#Q(S+etlIG;IuBQznoh2JEHmn3h%#k?{wm+RjVs5^Oijo2M=8!QNx-f}kiQIO5qZHygRESPYmYeDEhRrUV;>`SGmxBRWk^mU#_RIpNipw@UJ!M%touxP&I{(?r@9;_|z^VRwBZ*Lj_ptX-jPYRQ%QZK?-ywqz8I!Fi(cje5!lB+?D-i&t;tAz9scuTVgaq8PP$jMy_MMy=)%<abp+t$RpItdvN8wRs%s+id<}Rd}nb7RbaE?^xOZ?U{=M;t94?&uwOh(U+`gb$a$#b$~~tYE&xLl;bR@7NeYZc7@u3TC_9`96z9gXP98a${+E9GVS4@y%ro`<r1}bb0caDn}|mX`a@8=XeiV)(hJCp{fCByOtOn~D<|b$+M(ACpBQf-PVRkhZX*X=tPZ{W!w4&p@%=PoGn*{aqk)5o&r3Hm;>I;CMLI;kSIeXn<vngjtd0(9VeRHQu-V7ZzoTFA+!FEMYfTu$x%*VI8?I;!k!2~`iUo<AodONO9>K1o1iZ_^X6|inDGlDUpg!fk*GBU}?4hg<Db}Bftb+8GclV{z1x7WMjxbc>;zB6;o2yFd;pUzcC;fa}?|k+it5lAsiRB0iRC2=zy+Fl)stGl?s`Fh5q``f*1|SfE(-4?c%KN%O<*+OnYm7jz{9^Ke-ffP*H^LYTLF%N?h$Q->@3BW=K4Z2R=lU+?!@UqKCf1`8(4=pI%*G%k9(t+ieCQQ!UW;PigD&De$;u}6MOsS#PL`1Fu1up&HD2>1;GDp`HN93V)&XK~mk|SbTJELw=xwgJl312bT+Q+c+sd4*{ki1RV0$*frr_H|jBbnNZSFW!jpbwU07$dP+}=Ih(1FXL*Rmh1-PB!!lECF8)pS%3bypS*-JAq-hWAE?S_taHMpKFsx!Y7}^Y=s-CXp2yyCLCKaS>aJ;9JQQ33^!<RBQ+cKceRl2&KUmXqihZ&$7-!+}x+JeHzX4N)SRdB;_(gbAQhnKbY9s8mu2pmdWi9-xXrL<P*zLSZ3Z*T?^U*O2a{aRg~`UP@p^{;-WI)j+0>iPbI1c+-(FlRz2W)1G_%cd;wNj)uQ2Bjo~W@7OTU=&$!zN_YuJ?&;e*^I0-w7yal6ex_6mJvOb#Fk(^6H`9dM!e&-&WO2Qr}W=Y_bH&(*76Khy~27QFy5?6w;qv%ypAABK{H(AYy5G!o30y?%TBQQ55?_okOy>(R>j6K#~36ltJb9z|AWSKTw6y#w2dSl(h@;bS6s`p@$?(bo4{3+~Cz+Qrhu@(ISl7xQ<Lx~<27~2W1R<V9(&CAb$_Ff)3dRsg!G;hVs<(ig{efa_np6fh`tRj_bL#+Nfcs;PSFADo|E%_2l3*`{a9Els3jlBUnIt?5RnW3s{vU8(XhGH+l#Q4mSkG>p(<RW<&$!xJK#eD=HeR;YYlVgR)(BuiS_gl0I#SRdRZ5{;T6I$2h^iQvUY@fKMz??RHbj<dpB$84TG1eu&g1}^Vc|01~Ns+}c-P(gcy!km<t&m8OzpF<>tR~3PF-<smcWSM@%Z$s%y6LQ;3J069ZrD~18(7vnG=X_^!{u+;8G*0vk-zy%PXuPu@=LW1R2eGgv{)31n__fjka7~n1EI&qBiW=z(F}f<-1~rU>IMPm=ZQ3|DQM}uzSM9R7Y0V`psU5LX9_<oF@Lqb#Jr(w$-}=0<;UF~Hh9PvrCNfY7w~YspY*`|Ypiu2sYY?UVvw)9mOh^M)Vbhfi{w1Svn|zjfX5M&iygyHjZGha*GV6LH#B|xc|g0WqP{DMZJcqKY<);<E+FofVKXWj_hleXJ=>$aPLq3l3xiT5l!F)yx0y$U^5&~lyW{Gvo-9)qu*hems)eutfuZSkT&ithvIv~t`fMFdv;LFOGHtRM<_Dc%rBzRkYa+ZP5#6`}iKLxig`ntdj{8y>Mw*b0Yx1@aq15YJovZU_?WU^L^qy}47R%=Zb+S47sFgsq12`k(!w~C!zDn|OnmChA4&@CD-sfeOhn$<zR28$nbz!>0h}Z2P_~wmfi^1-&+I}@mS?52_nH()!r!L@L;Us?lKO9v>YAM7300"""

def load_events() -> list[dict[str, Any]]:
    raw = gzip.decompress(base64.b85decode(_EVENT_BLOB.encode("ascii"))).decode("utf-8")
    data = json.loads(raw)
    events = data["events"]
    merchant_words = ("售货", "贩卖", "商店", "摊", "窗口")
    for event in events:
        is_merchant = any(word in event.get("title", "") for word in merchant_words)
        has_cost = any(
            any(op.get("op") == "stat" and op.get("amount", 0) < 0
                and op.get("key") in ("coins", "clues", "food", "lamp_oil")
                for op in choice.get("ops", []))
            for choice in event.get("choices", {}).values()
        )
        if is_merchant or has_cost:
            choices = event.setdefault("choices", {})
            if not any("离开" in c.get("text", "") or "不买" in c.get("text", "")
                       or "什么都不" in c.get("text", "") for c in choices.values()):
                for key in ("D", "E", "F"):
                    if key not in choices:
                        choices[key] = {
                            "text": "离开，不购买",
                            "result": "你收好金币，离开了这里。",
                            "ops": []
                        }
                        break
    return events

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



def is_first_time(state: dict[str, Any], event_id: str) -> bool:
    return event_id not in state.get("event_last_seen", {})

def event_cooldown_ready(state: dict[str, Any], event: dict[str, Any]) -> bool:
    event_id = event["id"]
    if event_id in state.get("night_seen_events", []):
        return False
    last_seen = state.get("event_last_seen", {}).get(event_id)
    cooldown = int(event.get("cooldown", 3))
    if last_seen is None:
        return True
    return (state["day"] - last_seen) >= cooldown

def mark_event_seen(state: dict[str, Any], event: dict[str, Any]) -> None:
    event_id = event["id"]
    state.setdefault("event_last_seen", {})[event_id] = state["day"]
    if event_id not in state.setdefault("night_seen_events", []):
        state["night_seen_events"].append(event_id)

def item_description(item: str) -> str:
    return ITEM_DESCRIPTIONS.get(item, "用途尚未确认。")

def visible_inventory(state: dict[str, Any]) -> list[dict[str, str]]:
    return [{"name": item, "description": item_description(item)}
            for item in state.get("inventory", [])]

def quest_snapshot(state: dict[str, Any]) -> list[dict[str, Any]]:
    quests = []
    # Always-visible long-term quests
    quests.append({
        "id": "night_keys",
        "name": QUEST_DEFINITIONS["night_keys"]["name"],
        "description": QUEST_DEFINITIONS["night_keys"]["description"],
        "progress": f"{state.get('night_keys', 0)}/3",
        "complete": state.get("night_keys", 0) >= 3
    })
    quests.append({
        "id": "station_truth",
        "name": QUEST_DEFINITIONS["station_truth"]["name"],
        "description": QUEST_DEFINITIONS["station_truth"]["description"],
        "progress": f"{min(state.get('clues', 0), 5)}/5",
        "complete": state.get("clues", 0) >= 5
    })
    # Unlock the name quest once the player has a relevant item/flag.
    name_items = {"旧怀表", "车票残角", "守夜人的徽章"}
    if any(x in state.get("inventory", []) for x in name_items) or state.get("flags", {}).get("name_thread"):
        found = [x for x in state.get("inventory", []) if x in name_items]
        quests.append({
            "id": "lost_name",
            "name": QUEST_DEFINITIONS["lost_name"]["name"],
            "description": QUEST_DEFINITIONS["lost_name"]["description"],
            "progress": "已找到：" + ("、".join(found) if found else "相关痕迹"),
            "complete": len(found) >= 2
        })
    return quests

def result_narration(event: dict[str, Any], choice: dict[str, Any], state: dict[str, Any]) -> str:
    base = choice.get("result", "事情暂时告一段落。")
    sensory = {
        "雾林": [
            "湿冷的气味贴在衣袖上，远处枝叶轻轻摩擦，像有人在跟着你。",
            "雾在脚边缓慢合拢，刚才留下的痕迹很快就被吞没。",
            "树皮上传来细微震动，随后一切重新安静下来。"
        ],
        "旧车站": [
            "铁轨深处传来一声很远的金属回响，空气里浮着旧机油和雨水的味道。",
            "候车厅的玻璃轻轻发颤，仿佛有一班不存在的列车刚刚驶过。",
            "墙上的时刻表翻动了一页，却没有风。"
        ],
        "沉睡湖": [
            "湖面荡开一圈极慢的波纹，月光被切成细碎的银片。",
            "岸边水草贴住靴边，冰凉得像一只试探的手。",
            "湖心传来一声闷响，像有什么东西在水下翻了个身。"
        ]
    }
    extra = random.choice(sensory.get(event.get("location"), [
        "四周短暂安静下来，但那种被注视的感觉没有消失。",
        "你听见自己的呼吸声比平时更清楚。",
        "某种难以解释的变化留在了周围。"
    ]))
    return f"{base} {extra}"

def required_resources(ops: list[dict[str, Any]]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for op in ops:
        if op.get("op") == "stat" and op.get("key") in ("coins", "clues", "food", "lamp_oil"):
            amount = int(op.get("amount", 0))
            if amount < 0:
                key = op["key"]
                costs[key] = costs.get(key, 0) + (-amount)
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
    if not event_id:
        return None
    return next((e for e in events if e.get("id") == event_id), None)

def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": state["version"], "day": state["day"], "location": state["location"],
        "hp": state["hp"], "max_hp": state["max_hp"], "lamp_oil": state["lamp_oil"],
        "food": state["food"], "coins": state["coins"], "clues": state["clues"],
        "trust": state["trust"], "night_keys": state["night_keys"],
        "inventory": visible_inventory(state), "traits": state["traits"],
        "titles": state["titles"], "unlocked_locations": state["unlocked_locations"],
        "completed_endings": state["completed_endings"], "run_events": state["run_events"],
        "quests": quest_snapshot(state)
    }

def resolve_choice(state: dict[str, Any], event: dict[str, Any], choice_key: str) -> str:
    choice = event["choices"][choice_key]
    blocked = choice_block_reason(state, choice)
    if blocked:
        return blocked
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


def forced_return(state: dict[str, Any]) -> str:
    state["location"] = "林间小屋"
    state["hp"] = max(4, state["max_hp"] // 2)
    state["run_events"] = 0
    state["pending_event"] = None
    state["pending_return_prompt"] = False
    add_journal(state, "体力耗尽，被迫返回林间小屋。")
    save_state(state)
    return "体力耗尽。你被雾送回林间小屋，体力恢复到可行动状态。"

def event_payload(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    choices = []
    for key, choice in event["choices"].items():
        blocked = choice_block_reason(state, choice)
        choices.append({"key": key, "text": choice["text"], "available": blocked is None,
                        "blocked_reason": blocked})
    return {"id": event["id"], "title": event["title"], "text": event["text"],
            "first_time": is_first_time(state, event["id"]), "choices": choices}

def state_options(state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    pending = event_by_id(events, state.get("pending_event"))
    if pending:
        return {"ok": True, "message": "请先处理当前事件。",
                "event": event_payload(state, pending), "state": state_summary(state)}
    if state.get("pending_return_prompt"):
        return {"ok": True, "message": "本次夜行已经经历3次事件。",
                "choices": [{"action": "return", "text": "返回林间小屋"},
                            {"action": "deeper", "text": "继续深入（体力-1）"}],
                "state": state_summary(state)}
    if state["location"] == "林间小屋":
        return {"ok": True, "message": "林间小屋可执行动作",
                "actions": {"travel": state["unlocked_locations"],
                            "eat": state["food"] > 0,
                            "light_lamp": state["lamp_oil"] > 0,
                            "work": state.get("last_work_day", 0) != state["day"],
                            "status": True, "journal": True, "save": True},
                "state": state_summary(state)}
    return {"ok": True, "message": f"你正在{state['location']}，可执行 explore。",
            "actions": {"explore": True, "explore_dark": True, "return": True}, "state": state_summary(state)}

def command_help() -> dict[str, Any]:
    return {"message": "每次运行只执行一个动作，避免多轮 input() 造成输入错位。",
            "commands": ["python game.py status", "python game.py options",
                         "python game.py travel 雾林", "python game.py explore",
                         "python game.py choose A", "python game.py return",
                         "python game.py deeper", "python game.py light",
                         "python game.py explore_dark",
                         "python game.py eat",
                         "python game.py work", "python game.py journal",
                         "python game.py save", "python game.py reset RESET",
                         "python game.py json '{\"action\":\"status\"}'",
                         "任意命令末尾加 --json"]}

def perform_action(state: dict[str, Any], events: list[dict[str, Any]],
                   action: str, args: list[str]) -> dict[str, Any]:
    action = action.lower().strip()
    if state["hp"] <= 0:
        return {"ok": True, "message": forced_return(state), "state": state_summary(state)}
    if action in ("help", "-h", "--help"):
        return {"ok": True, **command_help(), "state": state_summary(state)}
    if action == "status":
        return {"ok": True, "message": "当前状态", "state": state_summary(state)}
    if action == "options":
        return state_options(state, events)
    if action == "travel":
        if state["location"] != "林间小屋":
            return {"ok": False, "message": "必须先返回林间小屋。", "state": state_summary(state)}
        if not args:
            return {"ok": False, "message": "请提供地点名称。", "state": state_summary(state)}
        loc = " ".join(args)
        if loc not in state["unlocked_locations"] or loc == "林间小屋":
            return {"ok": False, "message": f"地点未解锁：{loc}", "state": state_summary(state)}
        state["location"], state["run_events"] = loc, 0
        state["pending_event"], state["pending_return_prompt"] = None, False
        add_journal(state, f"从林间小屋出发，进入{loc}。")
        save_state(state)
        return {"ok": True, "message": f"你进入了{loc}。下一步执行 explore。",
                "state": state_summary(state)}
    if action == "explore":
        if state["location"] == "林间小屋":
            return {"ok": False, "message": "请先 travel 到已解锁地点。", "state": state_summary(state)}
        if state.get("pending_return_prompt"):
            return {"ok": False, "message": "请先执行 return 或 deeper。", "state": state_summary(state)}
        pending = event_by_id(events, state.get("pending_event"))
        if pending:
            return {"ok": False, "message": "已有待处理事件，请执行 choose。",
                    "event": event_payload(state, pending), "state": state_summary(state)}
        event = choose_event(state, events, state["location"])
        lamp_lit = bool(state.get("flags", {}).pop("lamp_lit", False))
        if event is None:
            state["location"] = "林间小屋"
            save_state(state)
            return {"ok": True, "message": "这里暂时没有可触发事件，你回到了林间小屋。",
                    "state": state_summary(state)}
        state["pending_event"] = event["id"]
        if lamp_lit and random.random() < 0.35:
            state["clues"] += 1
            add_journal(state, f"[{state['location']}｜提灯细节] 灯光照出额外痕迹，线索+1。")
        save_state(state)
        message = "遭遇事件（提灯照亮了更多细节）" if lamp_lit else "遭遇事件"
        return {"ok": True, "message": message, "event": event_payload(state, event),
                "state": state_summary(state)}
    if action == "choose":
        event = event_by_id(events, state.get("pending_event"))
        if not event:
            return {"ok": False, "message": "当前没有待选择事件，请先 explore。",
                    "state": state_summary(state)}
        if not args:
            return {"ok": False, "message": "请提供选项字母，如 choose A。",
                    "event": event_payload(state, event), "state": state_summary(state)}
        choice_key = args[0].upper()
        if choice_key not in event["choices"]:
            return {"ok": False, "message": "无效选项，本次不消耗进度。",
                    "event": event_payload(state, event), "state": state_summary(state)}
        choice = event["choices"][choice_key]
        blocked = choice_block_reason(state, choice)
        if blocked:
            return {"ok": False, "message": blocked, "event": event_payload(state, event),
                    "state": state_summary(state)}
        location = state["location"]
        result = resolve_choice(state, event, choice_key)
        result = result_narration(event, choice, state)
        mark_event_seen(state, event)
        add_journal(state, f"[{location}｜{event['title']}] 选择{choice_key}：{result}")
        state["pending_event"] = None
        state["run_events"] += 1
        unlocked = None
        if state["night_keys"] >= 3 and "沉睡湖" not in state["unlocked_locations"]:
            state["unlocked_locations"].append("沉睡湖")
            unlocked = "沉睡湖"
            add_journal(state, "集齐三把夜钥匙，解锁沉睡湖。")
        if state["hp"] <= 0:
            forced = forced_return(state)
            return {"ok": True, "message": result, "forced_return": forced,
                    "state": state_summary(state)}
        if state["run_events"] >= 3:
            state["pending_return_prompt"] = True
        save_state(state)
        payload = {"ok": True, "message": result, "event_title": event["title"],
                   "choice": choice_key, "state": state_summary(state),
                   "next": "执行 return 返回小屋，或 deeper 继续深入。"
                           if state.get("pending_return_prompt") else "执行 explore 继续探索。"}
        if unlocked:
            payload["unlocked"] = unlocked
        return payload
    if action == "return":
        if state.get("pending_event"):
            return {"ok": False, "message": "请先处理当前事件。", "state": state_summary(state)}
        if state["location"] == "林间小屋":
            return {"ok": True, "message": "你已经在林间小屋。", "state": state_summary(state)}
        old = state["location"]
        state["location"], state["day"], state["run_events"] = "林间小屋", state["day"] + 1, 0
        state["pending_return_prompt"] = False
        state["night_seen_events"] = []
        add_journal(state, f"从{old}返回林间小屋。")
        save_state(state)
        return {"ok": True, "message": "你回到了林间小屋，新的一夜开始了。",
                "state": state_summary(state)}
    if action == "deeper":
        if not state.get("pending_return_prompt"):
            return {"ok": False, "message": "当前无需决定是否深入。", "state": state_summary(state)}
        state["hp"] -= 1
        state["run_events"], state["pending_return_prompt"] = 0, False
        add_journal(state, f"决定继续深入{state['location']}。")
        message = forced_return(state) if state["hp"] <= 0 else "你继续深入，体力-1。下一步执行 explore。"
        save_state(state)
        return {"ok": True, "message": message, "state": state_summary(state)}

    if action == "light":
        if state["lamp_oil"] <= 0:
            return {"ok": False, "message": "灯油不足。", "state": state_summary(state)}
        state["lamp_oil"] -= 1
        state.setdefault("flags", {})["lamp_lit"] = True
        state.setdefault("lamp_history", []).append({"day": state["day"], "action": "light"})
        save_state(state)
        return {"ok": True, "message": "你点亮旧提灯。下一次探索将更安全，并可能看见额外细节。",
                "state": state_summary(state)}
    if action == "explore_dark":
        if state["location"] == "林间小屋":
            return {"ok": False, "message": "请先前往探索地点。", "state": state_summary(state)}
        state.setdefault("flags", {})["lamp_lit"] = False
        state.hp -= 1
        state.setdefault("lamp_history", []).append({"day": state["day"], "action": "dark"})
        add_journal(state, f"[{state['location']}｜无灯探索] 为节省灯油摸黑前进，体力-1。")
        if state["hp"] <= 0:
            message = forced_return(state)
            return {"ok": True, "message": message, "state": state_summary(state)}
        save_state(state)
        return perform_action(state, events, "explore", [])
    if action == "eat":
        if state["location"] != "林间小屋":
            return {"ok": False, "message": "只能在林间小屋吃东西休整。", "state": state_summary(state)}
        if state["food"] <= 0:
            return {"ok": False, "message": "没有食物了。", "state": state_summary(state)}
        state["food"] -= 1
        state["hp"] += 3
        clamp(state)
        save_state(state)
        return {"ok": True, "message": "你吃下一份食物，体力+3。", "state": state_summary(state)}
    if action == "work":
        if state["location"] != "林间小屋":
            return {"ok": False, "message": "只能在林间小屋整理旧物。", "state": state_summary(state)}
        if state.get("last_work_day", 0) == state["day"]:
            return {"ok": False, "message": "今晚已经整理过旧物了。", "state": state_summary(state)}
        earned = random.randint(2, 4)
        state["coins"] += earned
        state["last_work_day"] = state["day"]
        add_journal(state, f"在小屋附近整理旧物，获得{earned}金币。")
        save_state(state)
        return {"ok": True, "message": f"你整理并卖掉一些旧物，金币+{earned}。",
                "state": state_summary(state)}
    if action == "journal":
        return {"ok": True, "message": "最近10条夜行日记",
                "journal": state["journal"][-10:], "state": state_summary(state)}
    if action == "save":
        save_state(state)
        return {"ok": True, "message": "已保存。", "state": state_summary(state)}
    if action == "reset":
        if not args or args[0] != "RESET":
            return {"ok": False, "message": "重置需执行：python game.py reset RESET",
                    "state": state_summary(state)}
        fresh = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))
        state.clear()
        state.update(fresh)
        save_state(state)
        return {"ok": True, "message": "存档已重置。", "state": state_summary(state)}
    return {"ok": False, "message": f"未知动作：{action}", **command_help(),
            "state": state_summary(state)}


def _human_text(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(payload.get("message", ""))
    if "event" in payload:
        event = payload["event"]
        marker = "【初次遭遇】" if event.get("first_time") else "【再次遭遇】"
        lines.append(f"\n{marker}【{event['title']}】")
        lines.append(event["text"])
        for choice in event["choices"]:
            suffix = "" if choice["available"] else f" [不可用：{choice['blocked_reason']}]"
            lines.append(f"{choice['key']}. {choice['text']}{suffix}")
    if "choices" in payload:
        for choice in payload["choices"]:
            lines.append(f"- {choice['action']}: {choice['text']}")
    if "actions" in payload:
        lines.append("可执行：" + json.dumps(payload["actions"], ensure_ascii=False))
    if "journal" in payload:
        for item in payload["journal"]:
            lines.append(f"第{item['day']}夜：{item['text']}")
    if "state" in payload:
        s = payload["state"]
        lines.append(
            f"\n第{s['day']}夜｜{s['location']}｜体力{s['hp']}/{s['max_hp']}｜"
            f"金币{s['coins']}｜线索{s['clues']}｜灯油{s['lamp_oil']}｜食物{s['food']}"
        )
        if s.get("quests"):
            lines.append("当前任务：")
            for q in s["quests"]:
                status = "已完成" if q["complete"] else q["progress"]
                lines.append(f"- {q['name']}：{status}")
        if s.get("inventory"):
            lines.append("背包：")
            for item in s["inventory"]:
                lines.append(f"- {item['name']}：{item['description']}")
    if payload.get("next"):
        lines.append(payload["next"])
    if payload.get("unlocked"):
        lines.append(f"【新地点解锁】{payload['unlocked']}")
    return "\n".join(x for x in lines if x is not None)

def _parse_one(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split()
    if not parts:
        return "help", []
    return parts[0], parts[1:]

def cmd(command: str, *, as_json: bool = False) -> str | dict[str, Any]:
    """
    Execute one or more semicolon-separated game commands.

    Examples:
        cmd("status")
        cmd("light; travel 雾林; explore")
        cmd("choose A")
        cmd("options", as_json=True)

    Every command automatically reads and writes save.json beside this module.
    """
    events = load_events()
    state = load_state()
    results: list[dict[str, Any]] = []

    commands = [part.strip() for part in command.split(";") if part.strip()]
    if not commands:
        commands = ["help"]

    for raw in commands:
        action, args = _parse_one(raw)
        payload = perform_action(state, events, action, args)
        results.append(payload)

        # Stop chained execution when a choice/event requires a deliberate follow-up.
        if not payload.get("ok", False):
            break
        if payload.get("event") and action.lower() != "choose":
            break
        if state.get("pending_return_prompt"):
            break

    if as_json:
        return {
            "ok": all(item.get("ok", False) for item in results),
            "results": results,
            "state": state_summary(state),
        }

    blocks = []
    for i, payload in enumerate(results, 1):
        prefix = f"--- 指令{i} ---\n" if len(results) > 1 else ""
        blocks.append(prefix + _human_text(payload))
    return "\n\n".join(blocks)

def new_game(confirm: str = "") -> str:
    """
    Reset the current save. Pass confirm="RESET" to avoid accidental deletion.
    """
    if confirm != "RESET":
        return '重置被拒绝。请调用 new_game("RESET")。'
    state = json.loads(json.dumps(INITIAL_STATE, ensure_ascii=False))
    save_state(state)
    return "新游戏已创建。"

def state() -> dict[str, Any]:
    """Return the current public save state."""
    return state_summary(load_state())

__all__ = ["cmd", "new_game", "state"]

if __name__ == "__main__":
    import sys
    raw = " ".join(sys.argv[1:]).strip() or "help"
    print(cmd(raw))
