"""Topology figures with explicit reference ports and model boundaries."""
import math
from scripts.visuals.scenes.handdrawn_wave2 import BLUE,GREEN,INK,INK2,PAPER,RED,RULE,box,header,text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import topology_models as m


def curve(points,color=BLUE,dash=''):
    return '<polyline points="'+' '.join(f'{x:g},{y:g}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>'


def ports():
    out=[header('公共端指交流参考，不一定直接接电源地','三种组态先比较端口阻抗；具体值随偏置、源阻和负载变化。')]
    rows=[('共射 CE','B → C','E 交流公共','反相；Av≈−gmRL','输入约 rπ；输出由负载决定'),('共集 CC','B → E','C 交流公共','同相；Av<1','输入反射负载；输出由偏置与驱动决定'),('共基 CB','E → C','B 交流公共','同相；Av≈gmRL','输入约 1/gm；Cbc 是输出对地电容')]
    for i,(name,path,common,gain,note) in enumerate(rows):
        y=145+i*156
        out += [box(45,y,200,105,fill=PAPER),text(145,y+38,name,26,anchor='middle'),text(145,y+78,path,25,anchor='middle'),arrow(250,y+52,300,y+52,colour=BLUE),text(320,y+30,common,25),text(560,y+30,gain,25),text(320,y+83,note,24)]
    out.append(text(50,660,'MOS 的 CS/CD/CG 对应三种端口结构，仍要计入体效应和器件寄生。',24))
    return out


def mirror_errors():
    out=[header('电流镜要同时过三道误差账','示意匹配 β=100，参考 IC1 的 VCE=0.65 V；不以 Wilson 消除所有误差。')]
    rows=[('基流分流','IREF = IC1 + IB1 + IB2','忽略 Early：Iout/IREF = 100/102 ≈ 98.04%'),('输出电压','Iout 随 VCE 变化','VA=100 V、Vout=5 V：含基流后复制比约 102.23%'),('匹配与温度','同 VBE 仍依赖 IS、面积、温度','ΔVBE 的指数敏感性；发射极退化能换取鲁棒性')]
    for i,(label,equation,result) in enumerate(rows):
        y=150+i*155
        out += [text(50,y+30,label,27),arrow(210,y+20,270,y+20,colour=INK),text(290,y+30,equation,26),text(290,y+83,result,23)]
    out.append(text(50,655,'有源负载阻抗有限；Wilson 与 cascode 还要支付偏置、带宽和电压余量。',23))
    return out


def diff_four():
    out=[header('先守恒，再检查线性范围与输出端口','示意 Itail=1 mA、VT=26 mV、Rc=10 kΩ，忽略基流和 Early 效应。')]
    a,b=m.differential(.02)
    rows=[('共模同升','理想尾电流不变 → IC1、IC2 均不变','集电极电压不变；有限尾阻才引入同步变化'),('差模 20 mV',f'IC1={a*1000:.4f} mA，IC2={b*1000:.4f} mA',f'差分输出 Rc(IC1−IC2) ≈ {(a-b)*10000:.3f} V'),('小信号极限','单端增益 −96.15；差分增益 +192.31','线性估计 3.846 V，比 tanh 结果高约 4.88%'),('真实共模','单端看尾阻；差分还看失配','两输入保持在共模范围内，各管均有电压余量')]
    for i,(label,main,note) in enumerate(rows):
        y=135+i*132
        out += [box(40,y,200,108,fill=PAPER),text(140,y+60,label,26,anchor='middle'),text(270,y+35,main,25),text(270,y+82,note,23)]
    return out


def phase_table():
    out=[header('这张表只适用于写出的标准二阶环路','单位负反馈：L(s)=ωn²/[s(s+2ζωn)]，闭环无额外零点或延迟。')]
    out += [text(60,165,'PM',27),text(250,165,'阻尼比 ζ',27),text(490,165,'阶跃过冲',27),text(740,165,'解释',27)]
    for i,p in enumerate([45,60,65]):
        y=225+i*115
        out += [text(60,y,f'{p}°',29),text(250,y,f'{m.damping(p):.3f}',29),text(490,y,f'{100*m.overshoot(p):.2f}%',29),text(740,y,['振铃较大','约九个百分点','接近最大平坦'][i],24)]
    out += [text(50,590,'Butterworth：ζ=1/√2 → PM≈65.53°，严格值与约数应区分。',24),text(50,640,'极点数量不能单独判振荡；应看交越、零点、延迟与完整环路稳定性。',24)]
    return out


def miller():
    out=[header('电荷账决定输入等效电容','示意 A=100、Cbc=10 pF、有效驱动电阻 10 kΩ，忽略其他电容。')]
    out += [box(80,180,260,135,fill=PAPER),text(210,230,'输入 +1 mV',27,anchor='middle'),text(210,280,'q = Cbc(vi−vo)',24,anchor='middle'),arrow(350,245,560,245,colour=BLUE),box(570,180,310,135,fill=PAPER),text(725,230,'输出 −100 mV',27,anchor='middle'),text(725,280,'跨电容 +101 mV',24,anchor='middle'),text(60,390,'Δq = 1.01 pC → Cin = 1.01 nF → fp ≈ 15.76 kHz。',27),text(60,455,'有效驱动电阻要包括源阻与输入支路，不能总取开路源阻。',24),text(60,525,'MOS 三电容：Ciss=Cgs+Cgd，Coss=Cds+Cgd，Crss=Cgd。',24),text(60,595,'fT/β0 是单极点电流增益模型的 fβ 近似，不是放大器通用上限。',24),text(60,650,'GBW/噪声增益只适用于相应单主极点模型，不能推广所有反馈电路。',23)]
    return out


def noise_identify():
    out=[header('症状只能给线索，不能单凭一个旋钮定案','保持信号传递、负载、带宽与参考点一致，记录改变前后的频谱。')]
    rows=[('宽带嘶声','测白噪声地板与 ENBW','列源阻、en、in 各项功率'),('低频起伏','区分 1/f、温漂和外部干扰','斩波还查纹波与输入电流'),('50 Hz 及谐波','查接地、屏蔽与电源路径','同测共模、供电和输出'),('随偏置变化','查散粒项，也查 gm 与带宽','改变电流后重新核对失真'),('随源阻变化','分开热噪声和 in·|Zs|','并电阻可能同时削弱信号')]
    for i,(symptom,test,decision) in enumerate(rows):
        y=145+i*100
        out += [text(45,y+25,symptom,25),arrow(225,y+17,275,y+17,colour=INK),text(295,y+25,test,24),text(295,y+63,decision,23,colour=INK2)]
    return out


def noise_taxes():
    out=[header('相同输入信号条件下，才比较 SNR 改善','示意 300 K、高阻读出、信号始终为 1 mVrms；仅计源电阻热噪声。')]
    px=lambda v:260+v*40
    for i,(rs,bw) in enumerate([(10000,1e6),(10000,1e4),(1000,1e6)]):
        n=math.sqrt(4*m.K*300*rs*bw);y=180+i*135
        out += [text(45,y,f'{rs/1000:g} kΩ',25),text(45,y+38,f'Bn={bw/1000:g} kHz',23),box(260,y-25,n*1e6*40,35,fill=PAPER),text(px(n*1e6)+20,y+1,f'{n*1e6:.2f} µV',25),text(260,y+54,f'SNR = {20*math.log10(.001/n):.2f} dB',26)]
    out += [text(50,610,'不能把被滤掉或加载衰减的信号，当成降噪收益。',25),text(50,660,'四项等量且互不相关：总 RMS 为单项两倍，四项均方贡献相等。',24)]
    return out


def noise_input():
    terms,total=m.noise_budget()
    out=[header('噪声按均方值合账，先找占比最大的项','示意 1 MΩ、300 K、en=10 nV/√Hz、in=1 fA/√Hz，一阶低通 fH=10 kHz。')]
    for i,(label,n) in enumerate(zip(['源电阻','运放电压项','运放电流项'],terms)):
        y=190+i*120;share=(n/total)**2*100
        out += [text(45,y,label,25),box(230,y-25,share*5.5,36,fill=PAPER),text(820,y,f'{share:.3f}%',25),text(230,y+47,f'单项 RMS = {n*1e6:.3f} µV',24)]
    out += [text(45,595,f'RSS 总量 ≈ {total*1e6:.3f} µVrms；横条长度表示均方值占比。',25),text(45,650,'降低 en 只有小幅收益；改变源阻或带宽前，先验证信号传递条件。',24)]
    return out


def margins():
    out=[header('原候选失败；修订候选只在列明模型下通过','示意比较：输入端到 100 Ω 负载；修订频率模型含 10 kΩ 源阻。')]
    rows=[('电压增益','≥1000','原约 807：失败','修订标称约 2661'),('输入电阻','≥10 kΩ','原约 11.63 kΩ','修订标称约 13.13 kΩ'),('输出电阻','≤100 Ω','小信号低阻仍不够','修订标称约 11.76 Ω'),('高频截止','≥100 kHz','原漏计寄生与加载','修订标称约 138.3 kHz'),('输出 ±1 V','负载需 ±10 mA','原 1 mA 静态：失败','修订 IE3≈18.68 mA')]
    for i,(name,goal,old,new) in enumerate(rows):
        y=160+i*85
        out += [text(40,y,name,25),text(230,y,goal,24),text(440,y,old,23),text(740,y,new,23)]
    out += [text(50,620,'β=100 时修订输入电阻约 8.76 kΩ，仍失败；不能拿标称结果当保证。',24),text(50,666,'偏置、电容、温度、容性负载与有限旁路电容都要进入下一轮验证。',24)]
    return out


def headroom():
    out=[header('高交流电阻与最小工作电压是不同的量','有源负载不等于直流短路；cascode 也不保证输出极点更高。')]
    for i,(label,top,bottom) in enumerate([('电阻负载','压降 IC·RC','增益受 RC 与负载限制'),('有源负载','须留电流源合规电压','增益看并联 ro 与外负载'),('cascode','多一个工作区约束','高 Rout 与 Cout 可形成低极点')]):
        x=45+i*320
        out += [box(x,160,290,330,fill=PAPER),text(x+145,205,label,28,anchor='middle'),text(x+145,270,'电源',24,anchor='middle'),arrow(x+145,285,x+145,335,colour=INK),text(x+145,375,top,23,anchor='middle'),text(x+145,445,'输出摆幅窗口',24,anchor='middle')]
        out.append(text(x+145,540,bottom,22,anchor='middle'))
    out += [text(50,610,'MOS 长沟道近似留 VOV；BJT 要避免饱和并满足线性，不统一写成 0.3 V。',24),text(50,660,'折叠 cascode 改变电平安排；是否低压、低噪声，仍由具体结构决定。',24)]
    return out


def cmrr_definitions():
    out=[header('分子和分母必须使用同一个输出端口','定义 vd=vi1−vi2，差分输出 vod=vo2−vo1，RC 两侧为 Rc(1±δ)。')]
    rows=[('单端输出 vo1','Ad=−gmRc/2','Acm=−Rc/(2Rtail+1/gm)','1 MΩ 尾阻 → 85.68 dB'),('差分输出 vod','Ad=+gmRc','Acm=2δRc/(2Rtail+1/gm)','δ=0.01 → 125.68 dB')]
    for i,(name,ad,ac,result) in enumerate(rows):
        y=155+i*215
        out += [box(40,y,220,160,fill=PAPER),text(150,y+80,name,25,anchor='middle'),text(300,y+30,ad,27),text(300,y+80,ac,26),text(300,y+135,result,25)]
    out += [text(50,625,'单端行取 δ=0；差分行仅隔离负载失配，现实还存在其他误差。',23),text(50,670,'测 CMRR 看共模范围与频率；测 PSRR 看电源通道、频率和噪声增益。',23)]
    return out


def design_dc():
    out=[header('修订候选的直流工作点与交流连接','示意 12 V、β=200、VBE=0.65 V；第一级 cascode，第二级 CE，末级射随。')]
    for i,(title,lines) in enumerate([('第一级下管 + 共基管',['1 MΩ / 130 kΩ 分压','RE1=1.5 kΩ（交流旁路）','RC1=12 kΩ；上基极 2.5 V','IC1≈0.351 mA','VE1≈0.529 V','中间节点≈1.85 V','VC1≈7.812 V']),('第二级共射',['60 kΩ / 12 kΩ 分压','RE2=1.2 kΩ（交流旁路）','RC2=2.2 kΩ','IC2≈1.075 mA','VE2≈1.296 V','VC2≈9.431 V','基极经电容接前级']),('输出射随器',['基极直接接第二级集电极','集电极接 12 V','RE3=470 Ω','IE3≈18.683 mA','VE3≈8.781 V','负载 100 Ω 经电容接入','静态负载无直流电流'])]):
        x=32+i*327
        out += [box(x,150,304,425,fill=PAPER),text(x+152,190,title,24,anchor='middle')]
        for j,content in enumerate(lines):out.append(text(x+15,245+j*44,content,22))
        if i<2:out.append(arrow(x+306,350,x+324,350,colour=BLUE))
    out += [text(45,625,'输入也经电容接入；上管基极按低阻 2.5 V 偏置建模，不与输入信号相连。',23),text(45,670,'交流模型：每管 Cπ=25 pF、Cµ=5 pF、VA=100 V，均为示意参数。',23)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
 ('ch11-topology-ports',ports,'11.1','三种组态的端口条件','三行端口示意对照输入输出与交流公共端，标明共射反相、共集跟随、共基低输入阻抗，并说明阻抗随偏置与负载变化。'),
 ('ch11-mirror-three-errors',mirror_errors,'11.3','电流镜三项误差账','参考电流包含两份基流，Early 效应使不同输出电压下复制比改变，器件匹配与温度构成独立误差。'),
 ('ch11-diffpair-four-beats',diff_four,'11.7','差分对的守恒与非线性','共模不改变理想尾电流，差模二十毫伏按双曲正切分配，单端与差分增益分开列，提醒线性误差与工作区。'),
 ('ch11-phase-margin-table',phase_table,'11.5','指定二阶环路的阻尼换算','给出四十五、六十、六十五度在指定环路中的阻尼和过冲，禁止按极点数量直接判定稳定性。'),
 ('ch11-miller-bandwidth',miller,'11.5','米勒电荷与频率定义','输入一毫伏、输出负一百毫伏在十皮法电容上产生一点零一皮库仑电荷，列出 MOS 三电容和电流增益带宽的正确定义。'),
 ('ch11-noise-identify',noise_identify,'11.6','噪声症状与核验路径','五种症状各配一个频谱或工况检查，再决定改带宽、源阻或器件，保留信号与稳定性约束。'),
 ('ch11-noise-three-taxes',noise_taxes,'11.10','同一信号口径下的噪声预算','三组源阻和等效噪声带宽分别计算热噪声与信噪比，长度表示有效值，说明不能靠衰减信号报告降噪。'),
 ('ch11-noise-input-budget',noise_input,'11.6','输入参考噪声的均方贡献','一兆欧源的热噪声占本例总均方值约百分之九十九点四，横条按功率比例绘制，三项有效值分别列出后再做平方和开方。'),
 ('ch11-two-stage-margin',margins,'11.11','原候选与修订候选的预算','原候选在一百欧负载下增益和驱动失败，修订候选仅按列出的标称模型通过，低贝塔输入电阻仍不合格。'),
 ('ch11-cascode-headroom',headroom,'11.8','有源负载与叠管的电压约束','三种负载分别显示电源到输出的电压预算，强调合规电压不同于实际直流压降，高输出电阻可降低输出极点。'),
 ('ch11-cmrr-definitions',cmrr_definitions,'11.9','一致端口下的共模抑制比','单端与差分输出分别列差模增益和共模增益，只有分子分母使用同一输出端口才可相除。'),
 ('ch11-design-dc',design_dc,'11.11','修订候选的偏置闭合','三个模块列出偏置分压、发射极和集电极电阻、直流节点与耦合关系，输出管基流计入第二级集电极电阻。')]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=11,source='docs/p2-01-ch11.md',anchor=anchor,alt=alt)

for aid,values,reason in [
 ('ch11-mirror-three-errors',['102.23','98.04'],'正文参考节点 KCL 模型在 β=100、VA=100 V、Vout=5 V 的结果，图内按百分比取两位小数。'),
 ('ch11-two-stage-margin',['11.63','18.68'],'正文候选的小信号输入电阻与修订静态电流，图内按 kΩ、mA 取两位小数。'),
 ('ch11-noise-three-taxes',['1.29','1000','4.07'],'三组正文热噪声预算：带宽统一以 kHz 标注，RMS 以 µV 取两位小数；1 MHz=1000 kHz。'),
 ('ch11-noise-input-budget',['0.006','0.600','16.132','16.181','99.394'],'正文同一白噪声与一阶低通模型，RMS 以 µV 取三位小数，比例按各项均方值除总均方值显示。'),
 ('ch11-design-dc',['0.351','1.075','1.296','9.431'],'正文固定 VBE、有限 β 的偏置 KCL，图中电压和电流取三位小数，与可复算模型一致。'),
]:
    SCENES[aid]['numbers']=[dict(value=v,label='示意',reason=reason) for v in values]
