
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《林间夜行》v0.3 防剧透测试版
给 AI 当玩家的长期文字探索游戏。
"""

from __future__ import annotations
import json
import random
import gzip
import base64
from pathlib import Path
from datetime import datetime
from typing import Any

BASE = Path(__file__).resolve().parent
SAVE_FILE = BASE / "save.json"

INITIAL_STATE: dict[str, Any] = {
    "version": "0.3",
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

# 事件库经过压缩编码，目的是减少 AI 玩家在运行前无意中看到剧透。
# 这不是安全加密；有意解码仍然做得到。请遵守 AI_PLAY_GUIDE.md 的公平游玩规则。
_EVENT_BLOB = """ABzY8xqL!u0{`t@S#u&swtnwl(b2E=OxWG_Jos&9e#VU(1eQ>XXbE}%xv#Io5zs<x5{njugg^_DT4-UB8cB#n{Fj-^tg0vfg?mmWLI|pgrPw52M~9=k7BVZ($&=@NXZ!8d>(_67G1=^9tL4p4uit$4*SBxJ#cQTtOcsY7F8vq$>-Fp3*#F_Wc^V&^F-#ff=Gc?$>YR1T=&1jMymL=?V~_V7X2+bVenTi`$ZCZ|f=#zg|Kq6NmAxx8;TK9J5<Vy1l2F|j<8FAEWMY3*R>)yq-uo()LsIFSL_$JkpC*t0<NW;iQ&Y26^OOlE{V-j)`1dFOY#Na4?2@BG<85}&X0k8LvAZz1RK1XDUKp);5cZh$<KxOa{P)|Ff3b(~ccx~ImMPPd*V)~lZE$_o)c!k4zs26bpZo5wKYpup@8O$hY+rI0X>17=Q9R!!i8No<)-TZf60KP@eVN^1bSVBPd**}bSN8dH3-FDqPZ{T}3l^OD_o|OPe41FQiG|cR-@j3O@b_=~`2>f}Xzu(C<hV+Xy(;4>T>bA?UCgd;5_9esPfI{+q38rc!`_gbU#0sy5-gDQpmcr9_E-@%%-HBY`>_k6|K)8*steV164?36+h<AjS6WXr-+jE(^hIy}p(?oo`=oX*x#Ki*tRcVX)d7f8F6Q)zFhzoE5W0!LZQHt)ur1rUg`g@EQYPTTjHG;;E`{FoxY++xTWs<3olwfsa71+F#EhTZFR3j#JV2KG;?fD8U9dBYXLKn=f&sc5#B;2ANivb4(P7Rw|IuJI&-F(Qm^!_>>yH{UbH?|o)3VPRr>&n13l`82KA5K4pZmoKCj>m{uq~Jd&I)ANOQR_bR%oH*zZT547X5)Q6OLjx%$qH3_g*(f0nx2G(Bt19{?_=sH&)aSetJD)oU@x67eATI?`M%T?_M=M-L8e%te<++!brFxuN{+>ZQx1aZbdGBY1hU0b+T0e)d8LtlfcYQ8VHCRd-8^lzpg{`5;xNF;hyL}6-q}mm{JvCd=}w~be-qV!$~Jbw}s+z`xFMcnP#lk>HannpJ#s?$?P!A8;sKmBjX*uaF6Rhc)>|F-P9e{zgtis*bNq|#iXEOys=mfY<XX)9gV;Dco^oBQZ7mZ>q0f$!p{mvqJNb{R_Shz?j|QmtN%e$<wHa0d{1=W)W5RiQRe?aXm_ei*aI_;LOqiTXQZ|`I;H$?+7#lVD(VK>0JYfZzYJ=+e7Fn3Yr?hg@4MB)zkilw)~SW7Du!e=Am#j=@?6~$Pqs+TqkWvwjT_(y{^a9vR$dkFt90KhW%GK(Qs)z-d8C0Wd#H^V?4~K3$uVk0Pr+DIA?-l*FNe)!>Q(=8u7N&<!ZTU}6^!n$w(DPTk?!9Kl_DHg<meQPeP9(hvPk#_Y<zjGEY)^MVy^|*=}`-#E1RU^q+gHWm$Z&dc+8gvxkmPurC1oWn-^tE4jiA;MsI|opYFy<_=pr;v>XRI($ES>xbXpWR<orWfbLz#Lqhhh!bg4cZggkz4?lKNn~-_EC32Lgn>?wI==Y9SZEBg!5RbOe%GGXkb+H@;k)t7O-~p-T1z|&-XCMUiNScv?L}(kImc&q5Tw4^^Z|KH7Nu=viytu3i7_Hw3#f;>NBV-$1Meqm@ggZHLrCSTIndYs(m^4hurs)pHSmht0-<-tXvm4Oeq+m^|f5sD&^2ty?b1cfxEGHOL+WcckfWDQ6x0*`B418ygN&}yt<c^bI9(Y8G9E+~=cD;f4gLLx_eP~4|+4m4%T=cj_R|Z~z=h252EbyNa%4MM%<v*xLhlnJ^LJFos5_wIt`yO=&P?F14l8@8G841T|H4F3NfXTR!oK8SatGh{u?32Afo4ok>PV_Fe(60?gJ{R42{=87if^c|&sB!;_;M)#*;5Tmvhy9-~6JJ^UQr14T>W&sy0<5`-II;$6;{c_4cJ;$mIaVMWS*dU$lrjny&R&9qK_Uc*XB*6+KPqv$Tm!=xapwJ7kW|9mp7h1V&0`W-5i=mNZi%yksC6+R9oO{W&+J#f=L#!YR%~byeqRGTEFICUb&_47zTr7>l$G)BfM@nGLj#`q+6+t&<OHC}1Mbyt(16BH;3OeC_v0mlV$ec&B9VR1u*kso+v6e)O3n#or*P+!7pp=s2!v2ue40p${uQZOhCgIIh*&4+8Hc(cD@{OY)@m`?9fn`bcC*838!@IdJbA0F9!{G~wjRZ;lsYFnd7&CcKXX1T-_;a!Lv|gN$E6xPFR#0VVp6Q^!&|WZ<ZZW9TSfIS;ip?6x^<6&wp0=?%es|B;=iJs89pG5u9EDc8iVmU(i<N+x>Su_8r+FmcX(;28iPhik+ufA@t58_;e$4sXkd$k_hGS#&p9wZ96fZ>y<^Tt^7gH~b*ZH>Eqf65W-Nhb$=wauzhWpau7r^3fJxh!ZU|U78-C!*Yp2tr)8Wy(&7m&Wi$OWL4+PO5g-}b<6_<3I1T}Y}l~>#sy~@&$R_k0}rZ#b|k?JMFG5G?mDk-q+y0lp3@ji(4B+}f%hAXh}Jb+b?Z5;?u|FTdiB1oLaPz+VE>B$q%EuSoj?BW;rm!+lX^NCwUk>K7VzC0orekV<wAshoAR9uohYm@Ci?KX(<o41n^LP~OLaPDz8l6;m{2oD^@3M(Fj?H13R24=2$B<gcLPm=F^ypg0d5G6~;-_zYVw;xqCe~>@P6ur*!&_)tIrs)ImYd}u9rL^;<*~8D}co+AJVk*RGqfI&K@H446@pxJc1O4C%2fBx>U_}!!ypo@50ID<|?S@&a-C>?HO<Gv#kSs$UOxvSABf4@3p|R*=g-B1HW5e#!+y+ftfc{OFQt0nzk;^(180q9Q$?dg_+^V|pkw3ff&x#j=^A59!aqJZ6?Ik&Kj}7GMc^^-pyLBTC79R1HFpNZ-4DeWf6AX1=6_5{NB`TL!CI1!bz@^%Y3i#+Ow)jU6+KGUUxLk*A;7XCBAk7?-V(}T8VhwsJ;}Z3_;C4)+ElJ>2>r{T%_NN-BOmil?y;no8Iae<3mU6fB^0R`W$Ni<H4U*mBm>4{X_R3C8C~u-?b7z<5DC+S@WHv}?Lklno9plz4dH(H8kfTc}Qf;J0{@a-x8UQ<EwoDr=#`%$-u$@BDd-T1=!@_+{EN=tFr0ZLuc*d7bRcT^OL9%{1xlIyzSbP$W!Qww7gSxyaJ6${!8MJ#EI1(?uj5qM9zTenPCdCq#KOX`!$Q#>IF2`8{6l6Fsxf@c9Vg@bGtsI+${K;muyjR|XJ=n?P4V9+LYhpR6z1!%OUoLOKZsTd!I&&7arCR;KFxX5p3-<o8_`VNHZU2weYU@3-9(87>Fk?(jEUlpF155k8By%M1+`u2yN)l;!ODJaeD`*`?LSPy;yn+1a)0gPgoFxJ#X!F!s*Z^+9_;f3W3aH-;;zB+QAqIH2NtXP>4~Wy5TZO!(VNDD<3{G|O{e;1_Wcl@Ibb#d+I;Nqt2C1>QLh2moEPXxzMPBxXX<!HRC|)6AOy)+XxT4l1^bsQoU8STXaMgukfCpGe**po~YV0?f1RXXcdsh%5Vs3pJz2a_tcztN{7bTow-e~*qVzNZEaU1+pkUt;ie(lGvzYCTD+9ywm*^J--!Rf^Tr+MQ^8pF^gaui3%mXTCCSdq6^V0W{6DsfW$!c`u9WmIUujrdX~Ce`jV_B*+c@eoj&y(UXvg;IzQj-jaxPkCWLkLCtIZO$-jwm9@_9$lgQ>tATd-%%Q1SrIsHqgTXRCWm?AO6W9s^a=sC*(SX{1o1FY>pdg4mkpa-BZ7)8bWys_lT;eE4AZ(I+^qtJnz&s>*bVkYd!EW*!TIKq-b^AyK46gPk>7fRmsre>&E#0HS$a+NW8qAs5|wUq?SdPGJB_Y_snZDBYE*0jB?xmvk4n@XMqTN44@A5kB>r|!j)%1Zud<7995hGjgC#+-ezKINU;SdDqK6k}O~yIH%)*>Pl=)K)i)2@DK!$=2+;0c$WOwv+3<$LYp<EtdDgX(efiM=TVc-iynl-d!c#Oe*C>@dqG<Zwy-9vWT0mt6E6$4BsPxwmNQ(#@~0R8$dWMz=V#Bw7;Unf@&48R<f{Cf;N>`?$RZDj_w$#k#s?<r8-E&`j+AVedY5P7gjh(Cx~ao!TS&$b`{y@yiqL4?u~M}f7mD6#AV1(hxzGvwdX4(|^KfzWv(caf6EzD~N{7mq4Kz&KPTXdO?_dw3b4Mha}596U^JC`$If7BGN(8f(#v#e>mxY;pgm30FOZS`y)E&OB<8u(8ot&N&HhfmKF#3PLG6M0X>v;4#7=>kp=nj-H)X{hvW{EDHifOzhFjVMhZ1p2X8XS3m=tI~*=|QP#L?z%E=Xz!Qx*8pmc5zwKlazkM@_;LLzeOl9Y1lkxsa0mD_rX;s8~cSo?zYIPWXHrn1B&Al2SjVyG=Q%~xxJu0NmHF0APo~-AeAC!4wNK35(v`JV6L>@IHJN<O|RF8XLC5zA%&l6WWklFNU@}9@9@rjU#kNP5w*$w?<R!n98c3?lRSrXzIcpnrf$gXRCm!6VuETM=qs#eTIAcbuIz`7(@K$Ckn35FE$tqGN*KarzBsg9POn5IrC(ZutWWaBjcnZ|B}Vo*%w;Z%EpF-@w{UX}N|5%_k)6guaWB|VLuNYyXm`L>e9<w`IF=?3czfGm&Q$ZLBF&=Y%~9G$>j{>pdX{q)^;C|^(3<TamA4&u+Gjz}P_2X@LY(r5uE5i6)0TrfqSc;*t_H`49bmH`KBlq;zi-%eT-qYj*(Wz}&KYJp0jThROE^&9@=u#@cS!wfR14a7;uatw4a0L=7ErH-a-aG0k)G*#H^S~y_AcoynNHnQSzT0D!9@Sy@I!>-puK}uOHR_DrLhW^0{YHO<=UJjU4_OV_LD77%&u^utOQ~&wTsMbVj8cK>(rP>YytCw}=2Y2BnX&QKN8#Q_btE~F14+KC`v8ER!xXE!64g(L{VcIF{=542}o3}4I>t+z;V1^|cY^nyLrrHobBfh*?_Hng=_+s#=LMU`>AN|7YE_|Mx+{e}v@b^#(Tet8)>ANkGP3e#ZAY+;bZ-ub<;LKMgp4PBfTro&8TcEC>MH)YmUF$DOt?#Bb3nSa!*GUOa>QEwpGfX$t!hkJhR}8%f2P-rg8nU9&G}7Q?g=WJD&dj{rMWYrl2_KV8<c~_6(-qk}k>>8W7ANpzN68F5uF7thH%`r(EvDY(9YW@Tv{X2SgOw&q3X(2SBHL*ci@{B-O|_M#v155BP4k8SI9)u7itAD|^#!hAMZ27vc<~BIAezzRtrG6?%>({X@x6N}Rpr+z<Zy?+;-^y`mxl1JlZNnaNDi*1uOFD$f`x6NIFRJW?n%<dF5{xgkDaLU<B-Z$JzaoF$(#JA)&^|b&_MIIJ#0fwf$$R4^)5DJ+Zv4ih_D%_&DMSt;vi;Xu4U*37Q!NTHTb)N--KPqqG_8M*^95hVS(v^#UK_h<i3(7{gfa0dP-?6eU)RGmg%%=6}iuHavMAM@Yvsxn2aMg&;Fs&))BKQwU>z9<xk@A?pqbg7Z?(>QxNx#fmad1PNb#UwoZIO(@)KK(_pmNKbdT!Z;drrktvo>#Bzp2F0_0Ckqha>Rqu?JT^1{>MP(%TCrdBqAB_v(_l_JpoU_{dKn}TWB>GS3@{XMHkR!KRMOPF%`-l)q*&@mx_7;MNxiBmLd?PPbdC6Cli;)%GnbRCR<Uh$HVIK1e{HJ8y)e#8ih9-PIbvmVk^l+`r#xMg9ce0tLtnV%6|9vKsL|uLtv!u37qXjYI;q22ft3=Em;KQpdKc5Bbz9^A0+OX!aW$*t}yU09oR^+wIj(b|Hm8t)p3!_O&*Z*6``gaWV`k_&ZYvMb?{LpPjm>*t#cR20-eNyI&yuQd=Gyi`txN#D-p8^L1wMT(eGc$d-ZtML&im29r{unrb(@w#4`*5p)w2Q}>*Dq8(@Ge%{51;YwAZQYnJz^!P#~206{;2fCL8>B``CWRQ6+?M=OO8jdlNd}kJjB}J=ILpZ#qe>?=$NtE=EqrYS>1=+XOo&{r+d#O!RpARQ~<^Kv#JmJfs=&$6RC8Lc{Ua2OG7S48Zw7vO-kpob5Xio)eM}w!hNNCZ#=j7#IY3Hw;QI6_CEYa@`j5S+vn~=F?*@xEI$$BS-1rzu~6Bk$z$xAaG!1DR}ZeP3iYpRL?pmussE5v?sV?pkyKF`ZIvuu`GS|65z03-;e%Z#hJy+nsRp5^^-wFTX(p3WD+_Uwos?Y0Qj$U$nI20Aoh3kAjjcG=g5`t7`pIILvYCvI1=~cG$a-OQeNb-g?2?db#62(s$wc58CgDm9=e;61kGSvpGu8IM6U8uPogPv48Frpz#|)Np+1c&fitp+3*aYNqdB~A952qy`csMIQYaK+s-yorO>)iCbv5#OpnsAaxh)3AU(HcEkQV8I8x>zC7LLKtHy%Nh|?2(3*0{kTCB6kHH`h~oGhKY*F2yWs^oVZnM6x1h@y^^kPQR4x<_1-CzmdB&IcEVr3c?RX+C$D;Hz0o}|1an^t#UStm=(E~9(FkiJ;WHlD_P`%i@qB;iUY5p4Zw8#_%cAlyByaspqa{mYgQ9ym5U8j6da%ArvjML&qEAyS+D%hd%d`Rh)pMz-Z=ZWOVL$TvXA@W$y^CugCn=o>)gX<zSTVDrlv-AR=Gb)%lV<pvP_7E)py<A##Zz&SRp3mf$jXv#PiQypP8j@|wcQ;XoYSF&B`?~g-8%(i!dTul@#Q(S+etlIG;IuBQznoh2JEHmn3h%#k?{wm+RjVs5^Oijo2M=8!QNx-f}kiQIO5qZHygRESPYmYeDEhRrUV;>`SGmxBRWk^mU#_RIpNipw@UJ!M%touxP&I{(?r@9;_|z^VRwBZ*Lj_ptX-jPYRQ%QZK?-ywqz8I!Fi(cje5!lB+?D-i&t;tAz9scuTVgaq8PP$jMy_MMy=)%<abp+t$RpItdvN8wRs%s+id<}Rd}nb7RbaE?^xOZ?U{=M;t94?&uwOh(U+`gb$a$#b$~~tYE&xLl;bR@7NeYZc7@u3TC_9`96z9gXP98a${+E9GVS4@y%ro`<r1}bb0caDn}|mX`a@8=XeiV)(hJCp{fCByOtOn~D<|b$+M(ACpBQf-PVRkhZX*X=tPZ{W!w4&p@%=PoGn*{aqk)5o&r3Hm;>I;CMLI;kSIeXn<vngjtd0(9VeRHQu-V7ZzoTFA+!FEMYfTu$x%*VI8?I;!k!2~`iUo<AodONO9>K1o1iZ_^X6|inDGlDUpg!fk*GBU}?4hg<Db}Bftb+8GclV{z1x7WMjxbc>;zB6;o2yFd;pUzcC;fa}?|k+it5lAsiRB0iRC2=zy+Fl)stGl?s`Fh5q``f*1|SfE(-4?c%KN%O<*+OnYm7jz{9^Ke-ffP*H^LYTLF%N?h$Q->@3BW=K4Z2R=lU+?!@UqKCf1`8(4=pI%*G%k9(t+ieCQQ!UW;PigD&De$;u}6MOsS#PL`1Fu1up&HD2>1;GDp`HN93V)&XK~mk|SbTJELw=xwgJl312bT+Q+c+sd4*{ki1RV0$*frr_H|jBbnNZSFW!jpbwU07$dP+}=Ih(1FXL*Rmh1-PB!!lECF8)pS%3bypS*-JAq-hWAE?S_taHMpKFsx!Y7}^Y=s-CXp2yyCLCKaS>aJ;9JQQ33^!<RBQ+cKceRl2&KUmXqihZ&$7-!+}x+JeHzX4N)SRdB;_(gbAQhnKbY9s8mu2pmdWi9-xXrL<P*zLSZ3Z*T?^U*O2a{aRg~`UP@p^{;-WI)j+0>iPbI1c+-(FlRz2W)1G_%cd;wNj)uQ2Bjo~W@7OTU=&$!zN_YuJ?&;e*^I0-w7yal6ex_6mJvOb#Fk(^6H`9dM!e&-&WO2Qr}W=Y_bH&(*76Khy~27QFy5?6w;qv%ypAABK{H(AYy5G!o30y?%TBQQ55?_okOy>(R>j6K#~36ltJb9z|AWSKTw6y#w2dSl(h@;bS6s`p@$?(bo4{3+~Cz+Qrhu@(ISl7xQ<Lx~<27~2W1R<V9(&CAb$_Ff)3dRsg!G;hVs<(ig{efa_np6fh`tRj_bL#+Nfcs;PSFADo|E%_2l3*`{a9Els3jlBUnIt?5RnW3s{vU8(XhGH+l#Q4mSkG>p(<RW<&$!xJK#eD=HeR;YYlVgR)(BuiS_gl0I#SRdRZ5{;T6I$2h^iQvUY@fKMz??RHbj<dpB$84TG1eu&g1}^Vc|01~Ns+}c-P(gcy!km<t&m8OzpF<>tR~3PF-<smcWSM@%Z$s%y6LQ;3J069ZrD~18(7vnG=X_^!{u+;8G*0vk-zy%PXuPu@=LW1R2eGgv{)31n__fjka7~n1EI&qBiW=z(F}f<-1~rU>IMPm=ZQ3|DQM}uzSM9R7Y0V`psU5LX9_<oF@Lqb#Jr(w$-}=0<;UF~Hh9PvrCNfY7w~YspY*`|Ypiu2sYY?UVvw)9mOh^M)Vbhfi{w1Svn|zjfX5M&iygyHjZGha*GV6LH#B|xc|g0WqP{DMZJcqKY<);<E+FofVKXWj_hleXJ=>$aPLq3l3xiT5l!F)yx0y$U^5&~lyW{Gvo-9)qu*hems)eutfuZSkT&ithvIv~t`fMFdv;LFOGHtRM<_Dc%rBzRkYa+ZP5#6`}iKLxig`ntdj{8y>Mw*b0Yx1@aq15YJovZU_?WU^L^qy}47R%=Zb+S47sFgsq12`k(!w~C!zDn|OnmChA4&@CD-sfeOhn$<zR28$nbz!>0h}Z2P_~wmfi^1-&+I}@mS?52_nH()!r!L@L;Us?lKO9v>YAM7300"""

def load_events() -> list[dict[str, Any]]:
    raw = gzip.decompress(base64.b85decode(_EVENT_BLOB.encode("ascii"))).decode("utf-8")
    data = json.loads(raw)
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
    print("《林间夜行》v0.3 防剧透测试版")
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
