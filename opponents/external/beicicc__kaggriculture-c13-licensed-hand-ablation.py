"""Schema-safe Ray Kretzschmar c14 policy with finite public-behavior patches.

Source: raykkretzschmar, "Kaggriculture: Findings from Zero to Top Meta"
https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta

The embedded source is the notebook's exact 15,962-byte ``main.py`` payload
(SHA-256 ``569cf2d20e3b37c3805c2a4ca7c4e5728eaa85df85c78392cdc3df77c5ddc17b``).
Its own provenance identifies the replay schedule as senkin13 submission
55186674 / public replay 89546258 seat 0, with Ray Kretzschmar's observation-
driven terminal harvest, drop, and sell controller.  No authorship claim is
made over that underlying work.

The Kaggle Code page identifies the Rayk/Senkin source as Apache-2.0.  This
modified version retains its observation-driven terminal controller and adds
48 explicit actor patches at 46 steps.  The finite patches were independently
measured from the public behavior in episode 89660976 (Milkomeda, seat 0):
https://www.kaggle.com/competitions/kaggriculture/episodes/89660976
They are public behavioral evidence only; this file does not claim or reproduce
Milkomeda's private source.  Relative to the licensed Rayk tape, the patches
change 4 farmer, 10 hands, and 34 market components over the executable 719-step
prefix, including removal of six replay-specific extra HIRE orders.

Modification notice: the final wrapper also clips or pads taped hand actions
with PASS to match the live hand count.  Rayk's adaptive terminal harvest,
drop, and sell controller remains active, so fresh terminal behavior can differ
from the fixed public episode while the finite prefix tape stays auditable.

C13-C is a five-coordinate ablation: it removes the Milkomeda-derived hands
patches at steps 211--215 and restores the licensed Rayk hand actions there.
The route was also observed across eight public Ueddy episodes, used only as
behavioral evidence; no Ueddy private source or authorship is claimed.
"""
import base64
import copy
import json
import zlib

_TRACE = json.loads(zlib.decompress(base64.b85decode(
    'c-rk<+io0La{L!Q_k;Svi~PosdNsmwC4rK*u^teE0lbC*WBoApo8f=AR%}*RS4Kug<~hYCIeKgG(sk~Y87Ct0m;XKc_uqd1$KQWH`<GwNK3#wQe0H}u`;XuL>)-zS+Yi2d{Ks#<|L5QT=iBFB&VGJ>yZ!dt(TAVD{_WT65AXkSeRH-rd-HL3wpc#=`15xA_S+Btvc38E;cRg+`SI@O?e&-ak3Vm3ZVo?M-rfD*V%(;mzP`VC`|G!sefj$RsYBy_IooYNfBD{y4<B#8{CswI+}wXY?$hnZw_o3UnLIJk{{6q5Ph0ir{hL33{WSWoQM2}~S&Tp3H&tlh%4^rO0XNrgw)@{6J$*V}om%nv=k4|rYRAJs9R73En9m=-?jLQNHTj9qs`X*=Caw6>KWFRc$;T74Iv$7Z^?u=?0hzAHh0~g)uy}`748u2W<C|+UL;D^0@IhM9lV?7B8C;Rymd%GR!@fk%79P129(lYzzm4?um+h_aKy~z2_@Ht3$^8W2;UCVC!*XqD+A?09qX&@*fybIYK$BMNyNmY7cudhm?VHOQveFx}A8xolhp8Ao$g6T?_v0F@h7X5-IcmdxlF*E}bHoQ^+U@<o!eww6_0cEwv|h&}Y{zx-Vf+|<(5Aaw8N12XmHKCga+p3ilJ}q3bO~c<&kOn<fnC`oR^(v|m@yn4Ob7G0hZ|uO4~t?LyJ-WR(bReiUKHT)<y#==6<@8BuGpX0lUZM<(g=g)X?o5!BZ;@9CN4}MAHJ=4oDJRs`~f^<9Cq28k2g2lH(!4J)Ashu`<wUwdbA``LI1k7P2m0H2l?uYyErPr@Mx_m_C9>((7NG(0--~$<M@%2lUI$QGokX^+mD|Lj~FI;)M6V9fK7HdaUZ@MoyO_>V3|3C!K2Nu>Q9zB?Y?hPGy8C)@=i|PGktoA9&LLt+NXu?kpQpQyUJ9x^<lq-aaLqI0e)GZqbbk@dvJK7^z85vhoEh)C(uq*=1A$p;d|}xo@O7~*IDHe!{~GwCi^8#-!Dg%)98EQyzjb)nQ}Pm;6fvC;N!;|lsL>7ma16E@<~Lh8jSO@0#*uk^@v!(d?;X7@aScP^7v>-F+e7$1YK!OA%_o-1#m&4Kgx&uqqTSJOOSxvbg`)SkTKa2<hXZ-uy=Sk3K=Kwt5n!~XgTN~xbP{gLi7l`^z<j#xOe#9L&|BtmplNzf)n=>Qk3Vdl_wfTvS7PU6gf;*HJo>*Eqw6gD`&_fPVt0C4PVVhIbEy@TC_PiV)~@x&_#R)@Iph=_^Pf6OJ$L1J}P!XQ}B*MpKPR6fidTcNEyu5E5P=_*!=ByE+D0MaxWkrr4VMKgDfBgE2MWo%5Dl0y&w@O3(sgoI&0*qk6tnI?E8RZ<OySftGgco=^rT|1vu-8V$^2>lOD!w5BYBXILIlb49*^(b_<RZ{jAW~lF;eT*SCL-KF53=32{V+S<Ko#zTsG7=K4B5C%n!Llsb)>6^2GW{R%<I!_yBx8XD)0#pf@#*Snv#x3_<@3}Ky)3WKP9Q%6s5B69GDZhPIh$S1L(Jzyi~+#+R6!0|VY7Q*(k$Dj*W29M00@0<21(K$kfC6Bc~0V9zcQ@h-GewDeCvN1eG-$C{jX55Uh;eMa}(E5b7POz)`KAj*Lfu)pzc(zI@%cVN*kGkbLQr9~15Y|f<N<BFdArf*u1#GvE+H1ZLdOcGJZC~I0sk@1g+KS{#^IIFMVJ|z)WLiGhx<dMRI2Wh-N`xG0Ld(Vm9F%(j$ue<{YMF=&Sr_5#9QmQGi#*Hl#euy$cv!SdY}u)cQ_}k)V0FtK0}(R_#mgNF4>%h_j|E6a`pP7eHZ{ION;u4Aipkk}Q9(nS9#<CZN`|$f)Mbz`kSjXS<18U%)j~+2EeRppUd-APK4>Pcu!X(nCk<bmm^6IZ3UWi;v;>FFB~WWZPBU3fHS!JOaPV?&1(N}On25wHX#mr;kE0*ZS>B#L?-DQ|JJY0$6qSZs0AmaDiiRr{axidOgN`Gz7{N!#`4xpan+&5yR|a9;8}^nADD5nf#Ot^$AliDgk<w@~SvKV-O#nQ6Jbagz_%FH4E&}P03+maC2#_c6WWv4x*#)!(Y4-r3#F<IMQU^4%l1i%1^sa;3{EOTguuupkKL}<m%8p2?6*B`8AFS-*UNoEPu=GsA0I3T>z>_U;C;4QJM3Mpq!w0NeL~LE+_zNG%zPbMJwntFUU`QcEJkK&%kb-f1r@hJA)0Hk2L>ynAsq<zQISOq|!sWNNJ&TCxFv%MRsd4NzNtxnylq&O<$tt4$7k@8#Z)I#fKwbbz!0w;*PEQCMh%KI4!lJMY7L*||A;8pMgqjVU1we%#RaK^Tl!sR{dwfj!Q4#?H$O`u*$x-QH7Q;|@kgw#2%a5Qhm3E^2y%oscJ;qHU9nqv?Sb5fwEVa&*Kv07hB(g_~U7XM^l!GYnHlNdAc$fqu*^I5?+gDB`D3ytU|JtOL4N$eFx<r0@*VU<sL<5s+plBfYlp5N1va8oZR}Nyft|d|FjI&4X8Rc)Q4ml~L!K$9)UGmdfvN^oaDwkDq{`sH*d4Kcg{gRqJBZUNIeD$OBjNrIqE|QB76!Tk?F!H!VAdI;ljr}z<=t>JW3c&lrj~Eeef;Nyvw_No(E79bL^t1vhf&Q><B`%B9Kbv3Jg~TN5_Iy-t;3WzyiR_Oqd0jYTLYHET4rEcmTU(hVJ<OeO_B>(6VR^D-3NG1$Z8sP8=ox}1)Nwrq#yyD%xBw<eH=1D(U_paMQNt)359WkZ%LFnJy!#lx)a-=m0$E9kQZUvM>D8|7@b!IQHP}<i+n7O9?J$EEfQCL{Fz@iADHo(eTf?X>YA`=MO!6AFoUUlQ14)3nh}aew2AQmG_kvVuuL$MRA*9#0Q>|x}_5&XhEl>?etZ3jUP6JO-W^-od)WZjBOOQ5}5kTxuCWlgPHbJZr?cD-rRwy`f^biVoFylM{_Y&?jATZGh`B+|dLKEzoYP<gHhypm_FswjSP5Sp=^7;`_jS(S<@&@1!4Y~!s%|Q5VH}J2!!8n}!?D2ck4i@uV=Lgfq+Y@#2fQMW=`P*FW2Gm}bA?y5)`@gKK>1^^h-ibKKe*6BNgGg057#g;bM{AZ51_kEDdF6zCU<FSKy86S+AX+$O3GAj5HMCR=&?__(u$%+a6j1#libF|+(sEyJhZ;4V!4e?bJRWq-bfjtEd5mvEvf~CO5Xt&=F<a)0+d)-!Y30nM%D|$-*i$V_H1q;pKc<c+f>4^P@;9vQ3fk_l>`ZL~Y)U7OXphO;o?&t^9t7ox*@g}W2!T3-JN9-43}JVn!=+GBAzBZKa?arVrd%F+bdZ;95!gU0isBh8X*Q$Z=@{0=i}Mee3?UR7u~&nlYY3pBWbI1sujy6x4p27Y7TjqN%lL-p&U4;G;Aq1(R?iaKSgxKrxH0}A%ZN*p_NqTECFIzoCCfU4r4bd#EIbg#L>+@fBT@vp6`Zl;28eMCA0qzAj&pHl2S2s~YeAB3=)8{n6fBh$Wyd~}edtpHE`Kt39|<<ZT!RWiGF-Jn7{`zzqJ~CMq>xYbvyaq$QSsihd*e7~ZPKTM_5wRpn(##9S<)b}M1qR=u>~vomqgiRja$zf7#TVQz#LOnRb)FMz{hhX^oh}0inppP`{j%SKvYa79(%9oi<Ael*{iHFw!LKKL(RD7Lu(iGf-=Ud28(Rn*X*!GX~`FI-AvPQ8DU<DHlmtR^oY=B62_xj7^6uKGWM2vTqm3w_#Vy_^qutBhoI~<L4CO<J53uqP`Cl{LUpF!+R4jb-z6CtQ53+u+L*5>)5YaPOYX_XykNkE4RQpKmYT9gBai=8Gvnl;9P-snqM9~LX8lYsndgGPfG_&KY*!t6yLu!jrbsQ}L7()AE2rk+ogllViTFEhA6LBDUI6T|6Z<0sbgq2?gy0E60n~L-mcqarh#aWC+H=uYR>h9W7!P-s%t#d4F*bhJ8i*5!zGyndm2syR;vmEreq_B**xinW3n`T-m25NEj9Uy+_X@@|mgN+bWzFOt;5wJwmoq;}hj|eWwC1}IfLGMw+@3;hyaQ05iI_EpN1K4h<GssX(c?_!A`V$2N;@l5ijF`clw<X-dO?a7oDms*oWc@Qoh~vYA+|56jef|aOw%u*IIdl02ogVz?z#DFmZ1U9#YJciLrDqjq@vs%ZB`jL+9aG}Dx1Wj3THblG>QRwt>}XWO48;L&`B(`*Vb}gHbW-uy8dZJVil{=#iLsQR=IF`ZCSU~mwnX-;+cjUN>;g<8{yF}o>?XyWRUYyaFXpUqCzJIe)J~WH77)l6f(%-KI83p(QHnl*V@u7J)69Ys;(piz!`p`5UJ!s!@ZnSaZ164m8z+N6Ni{D#C&wy4G_&oK#iT27LHN)QYF+3O7@91g{T~1xpAe`;J(cns{=5Yc8`#}8B%3xmh;qd6m~>|N~l7Ekq2BoO|gV8A-LNymz+sxgf=Nr|4O(|WLgdP{x$-d-BnM9@vy9de8^#CS>-_D3c@ZS=U_ZC(^{)b*+%kV<`7CT4?rwq6|h_$Kbtz%m4pjp90<$qP+>(aPt2JIt=s%6sW~q1xtJ-E{jp!x+@&-DI{`^XCN&SaG@djd0DvC;{^G8!Hg>~Yshv*3Swc;0XZnEKa(PDWl04wOY-aZdUZobIh8=3A*J!@(hey%5N~Wh|ogqAn)TZ6y^6bnESJRnP7ZR6*C8r`5dGqp{-{OYbk6E??t+Vb!AFt;3uqgme&k}Ev9b8@-wzLV>&?NYNJhZ9gUsC{^9IxU=#!9H91|hF@g-ojbS$psJ3XniciA;mCaYWKkDz9D&*JX(n1jd<7OYUH5t~9z%II9DW0J}qH%nC3(8DMQ0qdElR05}K;m+VG4et#EUUunb!wPD(=1m;ZXT>N_~y^~!<31~z4UF^cSg0qF~=f#z_LYY%G19@8KYIKC%CmfrEeS>J#pn-(QQOZv<?i+j2VyDB?PuDbutRmLs%r;oC66xOi6Wp>(QmeqZn<1;zjJ3YWsoW6!G7$ktFhrk<ZXx>j;Fo6KCY+Np*F@|jEEtebv(_y_<!CiI(BZ9ht(a7r(!=;CoL7`l{~haq%wflnOOc69XK;YWhBd6HO+!D{jo3W~7};$%Mcbmz$-cm{yOdsM=c*1gk$o9_BECT6Kf~Hh>0P_ZV4dh>B&Z)1<&pQKMq(<%Y0V%NFVaz=WWCZrmkEQc21)2%I*n-AdR~%J0*$C(XXXvkaUQqt-lZu&1;;12Dzl}qx_UojsIMS8;C4v57H?MuFA5!{WH`d)0<TE`kG44_`E^NL6_@u}_PCx|YbWuxz#s>1jt8;V9II>*izSPSAiKaM&6PbkW^<E9frifWV(9>V=amR)0R~97Is?qWCAi)6+~51?Quxx13RjuS03OYPKcgxiMX@N<2!7S-{=q+4JV`g&@>W*5lp195>bFW96A;974OBMG*^2^CF|^!`u_&UATbIU5PW$jMw1Pp3cMN}yYBt2=VJWK|fxQ!nVZ7-Wfdudt<GRi2DoRKrT|X*I9!0!8qW!X>Dt;{L4(iGVWMdCHqA9@qU7ZupF-vD@B$;}bAkM{B?tCXMfM_70SqxFqcXy(#c4Q>~BW?c0Bg64`YE#Ose<<Zzlya-bRLTL5u6}H$LJ4awlv^~dT&KOk5EOV#r^IFo<*b>|BTHYBljKc@nWOcXK=w?oatrVby-MDxGRsQ3-1eP)=t`7;#KLdv%gfeTI1?-nrZ5>}h*9^R3dGVt+=*r$_!+5~m`HF^Zx1HByiycfH{BQSxxkpjQKnt-;2fd(0!NghDGlz}fWUgwXcrS7^$`rvg<zq0loL6q=KH?uV^2-<2BmHCl}Sy<>Hq*_7jiK={NZlv?=zp?!C)Yp(1!<rC5;@?Dn@n)6g+!`Mz?rLK(zteEMo<TXcoXpt6H}nObB;nqQD^S7=X;!`8UoxFH>XAFhg#(1paIyIhuerxuwp5`v3r!OadopNiM{VIlywUOMz08Yn#R8z$OsLs}fBuG0Po{hpcW;Q2gxwcwWe5m6IQ>e!ws+_<a_BMGJH1&=I#NSQ+WbbhUuo-D!atn$<m~jZqI6MyIpcn>xjIQl$8YYX!&Vlm#Jn?GX?dR#%<)80`wSQ$=8g$-`v%l~bgyrJlm7RGHN&F<$c7XLslsI40}|0Lc;!R_jz%a%~c$h;_%6LSMu-ph#(3ns?*t6y-$??^z8g0r==c2-6H&qN;VQ-8w^qW&>0{=NN@EZkl;5&7^+hRnfVLSLzf>RKQ~j!5~NW>wt@;+~U?T$kXP8nuAk;YSE%E%OV1t8KoiQx^J|%jCsib?5-vHI*BLYWO}Qh3!{*6`#yG^nvn%9uQK9K3sLgEi0B(cNpfSFek=2fD!w3OXfuRI^3}oi?|H2Hxf=ca__pSh@}={BJeitg;JE=bbh);nGI~gM3KMBhGs3@NyaU!4%20A3?y5DLkV!I)4i`4k1E}V}eX3J&O_Tkg6c@`*TdStYTYr_Qi?a3lJTRa`EytFVT&WVeAoS3Z6iL8@B1~crl(^EZz#lb16QjaWnVoQ*SaL2hhD$uUq!;xx96a6$fTUGvKIFTj%1YZf$M%{kc{Y^Ht^&mv#vWxTm4>~F2T-L??3`lvvXat==Mk0a15P=&=qh)h4xr;5kM30DBHIWbE@Zt*QQ{G66DW`s1F@mTbHbWF&I}23MVopVEc(t6@y-kcO7X1265&i<X%BGoy43KOcQmu5B2_JdB@*9q<?e>;s$ef)AVSlMq=_D5M=SfPY1=ZL*a3TFnlsUVMz04;nNY}r`=N0jbSLiCVb+K?*sHAPz%yvTw~BpDzIr1ckDh!Vd&G{RqANhGK6lOBpQiR|(MYNI!2^1cb<0{<KVj;ulrnpY;wwOaA*jpKB>6yqIzcX&pXj5Jt2BOw3>@_nRzX@mywnCzk*smc5qP9qXNR(rJKvF6c_$MhiSCmUd9XlrCUaQ8?13g@%(}_}N!{#+7Sm8FR%iw@++T;H5)ua4dCdfnHVwlg@UBDpNLW4a={)d9zx7rRw?wM?(FbFTe;tTfXf{Ufsc-@#mk-ofRhnkILaEa3G-5DTtNP?^?py;CCf8!gaRfa0Sz}b}31oMxda=GBA15c^(M_&U7fQ=}S=l|UU`0a)-vjC+z!@i^kTGnfuh9_%tJ5vv6(aNmq@jhJdG$`o)QI^?2OeaEP&M987c=mDB9P{?4;TZI-lyS(L&_k_bc?4*@u`3>z3NtRN8*`CKHZIP^16q)sXn!fqv&MKd*Srx3$wN%HivdXk$Y_J7KdUmy5DZV%TG9gJg)Z*^YOJa!IW*Tdu%a67d*O=OSO)-;BS)GkvjUs6I3f5Pw&SiM~*&>DMWh_Y1ueybtWK~_dXy2D}hAqm89GBE*Q6-9R}!Xq#4@AP+$YL#~qS2+o4SHb02j`-Q{~4uV92#bs<&h<{XB@BJc!uRMu|t)`<Xe9Fht!F3Qrf>zTAL0<c85IKo?kEvRLH$9b#F>JV?1B(<7e-a3O6h<Zng!qEn1-KY{Y4Mbw2Z5PK+GU~Nd3(8$%kQVbsW`IVVM<|>gCJLhiMn^cqrRvXsacM1=09|=~QU%rehl1)P3M$P}?gc8SM5U?1==BXdFMAGx>4F6ygum5Gnc^~9wLJ8E7Nu3f>~||wIqIgo;y4pPFc=1fbJX4z%h9MRm9I)wqWV_BT4##nT9he>*tiFVTQ@hnPFV|is+ftgGFNo*_bGJ68g4%fv1{Q@MCnc80(nCUMlB2xN3aEwv-O1bPy|!t8=|8+#saxWf}+45;iJrhOs0oZ?yj7oOLC3A=y+oeCpBCmW=2L}EkgxudHV`sFTnU56Ch{4E2hSzmA(p1t}jJhfnsjT+U2Gs(t6kCg-kA!;4&PmN?GM-8DmYd%fd-9u)I?{)X5S$j<zU*-s(2M3<Pn2UJ$-d#6ZGj5^3QCIA~eG^j;{u$QHRZZvC#F7@ulL9pO9)7v?n3Gg8<=mX5`FE>0(DTFp(NVQSDii{^PSW&|>8N2lVWfN^sgB25b10i$RBO~ZX22hvG_m*T~lB<P+I!4XMAEXrgRrgBu9E<~Z@7Xt`*s3~I!p-#Txr1iiN1uwEkJyHuwXOt7fM~Pt^p=3>Zmz7xj0WFACPTM8inZBD9_VF&Jsy#d06}N6tT->QY5rjf<R*ntBJ;3k$d$<D2PH90xpw+61V^z2nU}6t8C*zaF2B+MB*<8yd@~<!xi<_BJyJo8!Yo&mKF$*Xw4<4w6MAk#{*!!O9l~qVSJ&x2;*&}mp{d8PGHe({ix>)EcNPKi6Id=zcl-%S-i~nC%{HxpLFd9j$$n;RG*uu`eop6>0=|bdFMMrk$E7_R1DPh1BQrc+zY-^EA?PIoM6yr)`GLzhR;oSJ4BEBbsX3l3<H~q0HeIICQFT`3#E$i)L8-km$0?j;ynp2reL)}e>U3Q<!orZx&L<yxArBa+}N>B|1W}J30r{;|9N{&6RRXk6a8;hdwZ5_5*m&(|%lJTr&IIY9ov33@SK%Di1d|kXHC7AaV3JKK+C$<BccrN0XsOx5xX?1XNdU<y^#(6}uvoSW!hh={ln)xfoDe*Vr0zQ#55s!0bc*Q84$x5|6j?sT<-s!k`)Js;e4GfowmpDg;&0UPWZToRCQG0|_XC20L;CY_bYzPY_aBbik(mo9i^-?5fELe`amxSc1k#n;UtwK4N$b_`W>+Qu|LW?N+=ET$wKva<mt0!9?1|&=d$ndM7)l*4R(MLXzT(eqg#m154F-{scndL!2=|KPK7kaSWvD{0I&o&PNwd#&QwTi$t{Y79xCf?g+=i)RnFc7sAoOSHKJO>?Em1U!IGE_*W$!P~&*htA)YLz$9!*U(6xC*UgZeS#>(pSplh1Fgv)ldrmJu3fjjQR<auqnBtFmD}sz}dAuk6o!OTz0Qz733sn17CxcFpYJ+!jZ62sO?LTS5pY5S5=g)QoNOh+w|t0-tgCLgWP@RX%`|&OHwV_P;m_;YN3#Zqej~lEJ81>M*)rslR@`Tnv3ly>x$)>^d4Nih8Oy{(7ZBfs>*0D_V^8pl{5UV(^P_m3Ez2kT1qcmr9yY3ad0>Wt0bBPc&c<QTgXeQ+$<)_?%H0p7hYo=WI&q=$x^ZLI0g9UTjC)=m^U_xOuW)=6scosm8p|XiiSr8=;0*RI_b~gy4D%*wH@2CM~p?Kc9*f&(x)`hTRJ(^C7*|vM2VM~H+(v;OFay*yFi%_zEFYk(ytk9tKNU@WhdY5<w|)UEQ5)Pbz;Y^Q@uEB@;SbI0kpOyH>7w<8pPm#N*+_oydZIPH5cf}OQ=OuFI8aDpU%eMl0^6-Fw{<jD>8sFR3L>O7IPF)!O@RWWG{kRT1}%jnR@k>$OS@(h=0eBxPX>ZMH0b+QL2!MG@LpyDgqIK$2_BpFy<QgstVzBmC~$a%;plvyc+2>bW71&Xqrj%2^#eVyskpXIS@ni&V_QvoXc%<M39*nUR5oK|0CugbJ4NLitec;X{^->>LJupI;2dYxM*9C*iw6SA^4SeTOhgXjia_cC$Cm#L#utl>!vmIYMC;;C(}c8d78z<lo`bOqj~P>U<Wu>MeFu5F}FZr^8nZ`h%*XQj)lDuCSqZGNxwK}p8>e6-gSYwHYX8eZ)qU=qxMB8kwI<MC3L)XDN@JtfD=J0^0~54RqdJYU=smvwX`f;@1ErqIPO+m@Sh)6Ui}oKB1HYjwqKIR#8YDMi3l5`42NX5j3+=JM=Ko!q~^xX887jY7MjO&7Y8hWw+WCa@jW7ZxDLhghHrm(`BTaZN==d%0Wx_hRVa_d0sw~#2RT=sib*N$2V8ZXI|WCR2XWfYmF6SVn0Sz-5Z{*aX2Pu~oQK`i>L*zZBS6eM7sZowpai^?3SD<ne}cUcG6VK=pxP=U6rod@Mg8`I89A$f2V9Y*JHiwKZO_h#catp#ADZK6?GusX$j*zZ57mM;+jsAP2dJc619E;*_{riTQA?GmQb$Uo1}lX?nojMOAS!Ar2p9Y3Q8Ey{t}dt@#nNz5(Mwf|Dogk*si#yYP^TS{GPzLpykAvKQq7pS2DY0e>Wa*-K)!6D7``GH=~85|S+Iy=)l+MC#-Qp8620Q;?WlU+tCuF+{G(LwQ)QcTP^+H3Y_lVwDv6E=Z*xhj24i5|;kRxZ#JfjH-6Yv(v7TlQ#><%|kO+^<Rik6E6EY&xRi=m6Dc>qaO?FZej_52v?d*yq<0tkHIfuaCY<;wZc4dQ!VU~A}@3N-G?E@)B%sf_Qh{2HsRWz+{qvvXAv*2`X&?dz3ev(HG2U0Hr0H{XKXkF!8hYM*kyN})qv;skpTBW~LnPiL?0hlsq34sI)&5jVGtP<{voW3U&6pRh-W%n(CLAE1h<M>e1`h;E?j!yKdh&0CMgCiMP%fDvnRSb4S^hlaqOA>TesWLvT)@?#nP5frB8Y}=Jx!K?UTVJ7^!ZYGEbiqxEi;slsHSXfN-7|pJ#bt9Uc4y*H)@geIcuU^rfY#WtFKG(jB{R8i7yQH?XID)WtJhtipH6B<f6QLL1kRN|)|;oMW>j<yLhSRJGRXE=@AC4*EGufGB(khJ;%mLwR)q1=<gz~xnTnEl)FO60%LgWG&H&I6me6XkqFYxg2<9OsEc9(HK1r);EA_J-#nLvZ>Fr!RkRhWbnv}a)`;fg-zKK*+Mt|8@zHymh28MY&2L_UKV%><)XitDxRbo`^w)3F5JIQ%3K;j%La7igheVWS3Ti{s7iq|n}g6{d)?kX54MF`@fa2&b|_$6p#N3=!cMz3VYP0P7ibq)AkbZa8naIZ>?F;eQyLN4}Kl4Budo*0lGoI^@W$gd<K6&*^jQW=}8*31m~h*bQ0l=f)D2BKWhOuO=|;lJ`LR);W)vh>AFEM&5Az4UEU)^kB7ttHXDR;}km7r+t!lxawf;6YFdFpxQvG->VK3&VSEsS^-(b?SGa=_G~X>JGV<e7U{A!a1~R(GBX|(4db?2o3M`MNqE+S)_F=GyY5#WMW0wy9|AX{6lHHm8uL?LDD)CUWM=q7-PAjOjnzB@OZI4Pv9W4>zI1;tuI^VA`GTuE1CH=yFC>Y04YN=I$5-Snqt*ULe&daNT?580&$>XH*<>{sr~D@ueg?p1{xWU{qtHL7!-75Lnx)HHia<ROpzc*i9Ym&O|>co&n}`C_R2&!H2@phs4ZDLii{dT10Zm3Gc?fg5!1(w3mTC~HYmqeD=nI5Yf6S+eEUmcqw(dq0$l-kgMoWl%2Q#SH_<kV=^Y-txI70GuvK8)0yE0MO^fBU$ITBPJkiu%WKeMpr&nKohKlh02)~ks2ERq(x<pEifYeE%9ax&5R{Z>MEHagu05Y$)M6?fMnVrQigGxmSET7{M_Q~K%Bn*xBXE6;Qp{*);d}yR_bTzj$yLbOZ^o;@fN?N3`Y@EGon*)2=u|;|V+{zK^(_^fy`@<)H^ZcG|AEZ2ba<7pR{XblDw6u|2xp*IvSL`jVD}1O;USSx-ff-NU>v-~_G`=d{rg1`LEN`ygY;7&8@z~<OAipRU0!ej4^l$T5itk>U?m^!reE5(ac%@*tIFzf(Q1<A<d@Vknj=TQ{t1_&S'
)).decode("utf-8"))

_SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")


def _terminal_liquidation(action, obs, step):
    """Replay-derived safety net: leave no sellable shed inventory at season end."""
    if step < 680:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    market = action.setdefault("market", [])
    already = {
        order[1]
        for order in market
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"
    }
    for item in _SELLABLE:
        qty = int(shed.get(item, 0) or 0)
        if qty > 0 and item not in already and len(market) < 10:
            market.append(["SELL", item, qty])


def _shed_access(size):
    half = size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _move_toward(pos, target, tiles):
    x, y = pos
    tx, ty = target
    choices = []
    if tx < x:
        choices.append(("WEST", (x - 1, y)))
    if tx > x:
        choices.append(("EAST", (x + 1, y)))
    if ty < y:
        choices.append(("NORTH", (x, y - 1)))
    if ty > y:
        choices.append(("SOUTH", (x, y + 1)))
    size = len(tiles)
    for op, (nx, ny) in choices:
        if 0 <= nx < size and 0 <= ny < size and tiles[ny][nx] != "LOCKED":
            return [op]
    return ["PASS"]


def _terminal_action(obs):
    """Observation-driven final-eight-turn harvest/drop/sell controller."""
    player = int(obs.get("player", 0) or 0)
    farm = (obs.get("farms") or [])[player]
    private = obs.get("private") or {}
    tiles = farm.get("tiles") or []
    size = len(tiles)
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands") or [])]
    inventories = list(private.get("inventories") or [])
    inventories.extend({} for _ in range(len(positions) - len(inventories)))
    sheds = set(_shed_access(size))

    available = {
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0
    }
    actions = []
    pending = {}
    for pos_raw, inventory in zip(positions, inventories):
        pos = tuple(pos_raw)
        inventory = inventory or {}
        load = sum(max(0, int(v or 0)) for v in inventory.values())
        x, y = pos
        tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else None
        if load > 0 and pos in sheds:
            action = ["DROP"]
            for item, count in inventory.items():
                if item in _SELLABLE:
                    pending[item] = pending.get(item, 0) + max(0, int(count or 0))
        elif isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
            action = ["HARVEST"]
            available.discard(pos)
        elif load > 0:
            target = min(sheds, key=lambda q: abs(q[0] - x) + abs(q[1] - y))
            action = _move_toward(pos, target, tiles)
        elif available:
            target = min(available, key=lambda q: (abs(q[0] - x) + abs(q[1] - y), q[1], q[0]))
            available.discard(target)
            action = _move_toward(pos, target, tiles)
        elif isinstance(tile, dict) and tile.get("fertilizer_available", False):
            action = ["COLLECT_FERTILIZER"]
        else:
            action = ["PASS"]
        actions.append(action)

    shed = dict(private.get("shed") or {})
    for item, count in pending.items():
        shed[item] = int(shed.get(item, 0) or 0) + count
    prices = ((obs.get("market") or {}).get("prices") or {})
    sells = [
        (int(shed.get(item, 0) or 0) * int(prices.get(item, 1) or 1), item, int(shed.get(item, 0) or 0))
        for item in _SELLABLE
    ]
    sells = [row for row in sells if row[2] > 0]
    sells.sort(reverse=True)
    market = [["SELL", item, qty] for _, item, qty in sells[:10]]
    if int(obs.get("hour", 0) or 0) <= 1:
        already = int(farm.get("hires_today", 0) or 0)
        for _ in range(min(10 - len(market), max(0, 8 - already))):
            market.append(["HIRE"])
    return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}


def _source_agent(obs, config=None):
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    if step >= 712:
        return _terminal_action(obs)
    action = copy.deepcopy(_TRACE[step])
    _terminal_liquidation(action, obs, step)
    return action


TRACE_ACTIONS = _TRACE

_PUBLIC_EPISODE_PATCHES = {
    26: {"market": [["BUY_PRODUCT", "WHEAT", 3]]},
    50: {"market": [["SELL", "WHEAT", 2], ["BUY_PRODUCT", "WHEAT", 1], ["HIRE"]]},
    74: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["HIRE"]]},
    126: {"market": []},
    211: {"hands": [["SOUTH"], ["SOUTH"], ["SOUTH"], ["DIG"], ["SOUTH"], ["CARE"], ["SOUTH"], ["PASS"], ["NORTH"], ["SOUTH"]]},
    212: {"hands": [["SOUTH"], ["SOUTH"], ["EAST"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["WEST"], ["SOUTH"], ["PASS"], ["PLACE", "SHEEP"], ["EAST"]]},
    213: {"hands": [["SOUTH"], ["SOUTH"], ["EAST"], ["WATER"], ["EAST"], ["PASS"], ["EAST"], ["PASS"], ["CARE"], ["EAST"]]},
    214: {"hands": [["EAST"], ["SOUTH"], ["EAST"], ["NORTH"], ["EAST"], ["PASS"], ["EAST"], ["PASS"], ["EAST"], ["EAST"]]},
    215: {"hands": [["EAST"], ["EAST"], ["DROP"], ["PLANT", "STRAWBERRY"], ["EAST"], ["PASS"], ["EAST"], ["PASS"], ["PLANT", "STRAWBERRY"], ["EAST"]]},
    260: {"farmer": ["DIG"]},
    261: {"farmer": ["BUILD_PASTURE"]},
    262: {
        "farmer": ["NORTH"],
        "hands": [["PLANT", "STRAWBERRY"], ["WEST"], ["NORTH"], ["PASS"], ["EAST"], ["SOUTH"], ["BUILD_PASTURE"], ["PASS"], ["SOUTH"], ["DROP"], ["PLANT", "WHEAT"], ["WATER"]],
    },
    263: {
        "farmer": ["PLANT", "STRAWBERRY"],
        "hands": [["WATER"], ["FEED"], ["WATER"], ["PICKUP", "COW", 1], ["WATER"], ["SOUTH"], ["PASS"], ["PASS"], ["SOUTH"], ["PASS"], ["WATER"], ["SOUTH"]],
    },
    299: {"market": [["SELL", "MILK", 3]]},
    300: {"market": [["SELL", "WHEAT", 20], ["SELL", "MILK", 6]]},
    321: {"market": [["BUY_PRODUCT", "WHEAT", 2], ["SELL", "MILK", 3]]},
    333: {"hands": [["SOUTH"], ["SOUTH"], ["DIG"], ["EAST"], ["SOUTH"], ["WEST"], ["WATER"], ["EAST"], ["PASS"], ["PLANT", "STRAWBERRY"], ["WEST"], ["PLANT", "STRAWBERRY"]]},
    334: {"hands": [["PLANT", "STRAWBERRY"], ["PLANT", "MELON"], ["PLANT", "MELON"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WATER"], ["PASS"], ["WATER"], ["WATER"], ["WATER"]]},
    335: {"hands": [["WATER"], ["WATER"], ["WATER"], ["EAST"], ["EAST"], ["EAST"], ["WATER"], ["SOUTH"], ["PASS"], ["NORTH"], ["SOUTH"], ["SOUTH"]]},
    361: {"market": [["BUY_PRODUCT", "WHEAT", 14], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "MELON", 6]]},
    370: {"market": [["BUY_PRODUCT", "WHEAT", 3], ["SELL", "WHEAT", 1], ["SELL", "STRAWBERRY", 4]]},
    373: {"market": [["BUY_PRODUCT", "WHEAT", 2], ["SELL", "WOOL", 4]]},
    384: {"market": [["SELL", "FERTILIZER", 10], ["SELL", "WOOL", 4], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "WOOL", 4], ["SELL", "MILK", 6]]},
    385: {"market": [["BUY_PRODUCT", "WHEAT", 12], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "WHEAT", 22], ["SELL", "MILK", 6]]},
    445: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["SELL", "WOOL", 4]]},
    489: {"market": [["SELL", "FERTILIZER", 3], ["SELL", "STRAWBERRY", 4]]},
    490: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["SELL", "STRAWBERRY", 8]]},
    496: {"market": [["SELL", "WOOL", 3]]},
    502: {"market": [["SELL", "WOOL", 2]]},
    505: {"market": [["BUY_PRODUCT", "WHEAT", 12], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "STRAWBERRY", 12]]},
    519: {"market": [["SELL", "MILK", 3]]},
    520: {"market": [["SELL", "MILK", 3]]},
    543: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["SELL", "MILK", 11]]},
    566: {"market": [["SELL", "WOOL", 4], ["SELL", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 1], ["SELL", "FERTILIZER", 6], ["SELL", "MILK", 3]]},
    567: {"market": [["SELL", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 1], ["SELL", "STRAWBERRY", 2]]},
    577: {"market": [["SELL", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 11], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "STRAWBERRY", 28]]},
    586: {"market": [["BUY_PRODUCT", "WHEAT", 2], ["SELL", "MELON", 6]]},
    620: {"market": [["SELL", "MILK", 1]]},
    621: {"market": [["SELL", "MILK", 1]]},
    627: {"market": [["BUY_PRODUCT", "WHEAT", 12], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "MILK", 15]]},
    644: {"market": [["SELL", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 3], ["SELL", "STRAWBERRY", 2], ["SELL", "MILK", 3]]},
    649: {"market": [["SELL", "WHEAT", 3], ["BUY_PRODUCT", "WHEAT", 9], ["HIRE"], ["HIRE"], ["HIRE"], ["SELL", "MELON", 17]]},
    659: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["SELL", "MILK", 2]]},
    683: {"market": [["BUY_PRODUCT", "WHEAT", 1], ["SELL", "MILK", 2]]},
    698: {"market": [["SELL", "MILK", 8]]},
    707: {"market": [["SELL", "MILK", 1]]},
}

for _step in (211, 212, 213, 214, 215):
    del _PUBLIC_EPISODE_PATCHES[_step]
del _step


def agent(obs, config=None):
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    action = _source_agent(obs, config)
    for actor, value in _PUBLIC_EPISODE_PATCHES.get(step, {}).items():
        action[actor] = copy.deepcopy(value)
    player = int(obs.get("player", 0) or 0)
    expected = len(obs["farms"][player].get("hands", []))
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = hands[:expected]
    return action
