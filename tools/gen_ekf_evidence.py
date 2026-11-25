"""Generate chapter 27 FigureSpec sources from the executable evidence."""
from pathlib import Path
import json
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bms-book/code'))
from ekf_covariance_evidence import innovation_allocations  # noqa: E402


def node(id,label,x,y,width=180,height=84,fill='#E6F0EF',stroke='#176B73'):
    return dict(id=id,label=label,x=x,y=y,width=width,height=height,shape='rounded',fill=fill,stroke=stroke,text_color='#293B3A',font_size=23)
def label(text,x,y,size=23,color='#293B3A'):
    return dict(text=text,x=x,y=y,font_size=size,color=color,anchor='start')
def edge(a,b):return {'from':a,'to':b,'color':'#176B73','thickness':2}
def spec(title,description,nodes,edges,labels,height=650):
    return dict(title=title,description=description,canvas={'width':960,'height':height},style={'font_family':'Noto Sans CJK SC, Microsoft YaHei, sans-serif','font_size':23,'bg_color':'#FFFDF5'},nodes=nodes,edges=edges,labels=labels)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "bms-book/assets/specs")
    OUT = parser.parse_args().out
    OUT.mkdir(parents=True, exist_ok=True)
    s=spec('电流怎样间接影响 EKF 的协方差','固定的线性模型可以预先递推协方差。本书EKF先用电流预测SOC，再在该SOC计算OCV斜率，因此C、K和更新后的P随工作点变化。当前电压更新状态后，会影响下一拍的线性化点。',[
        node('fixed','预先给定\nA、C、Q、R 与 P₀',180,210,265),
        node('recur','递推 P 与 K',500,210,210),
        node('offline','可预先计算\n同一更新时序',795,210,245),
        node('current','这一拍电流 I',135,445),
        node('state','预测 SOC',365,445),
        node('slope','工作点斜率 C',595,445),
        node('cov','这一拍 K 与 P⁺',825,445),
    ], [edge('fixed','recur'),edge('recur','offline'),edge('current','state'),edge('state','slope'),edge('slope','cov')],[
        label('P 的公式没写电流，轨迹也可能改变',36,49,31),
        label('先分清：矩阵序列预先固定，还是跟着估计状态更新。',36,92),
        label('固定线性模型：读数改变状态，不改变这套 P 递推',36,147,24),
        label('本书 EKF：C 在预测 SOC 处重新求值',36,348,24),
        label('电压 z 改变本拍更新状态 → 下一拍工作点 → 下一拍 C 与 P。',36,548,23),
        label('改变激励可能改变信息条件；不保证误差或协方差一定更小。',36,598,23),
    ])
    (OUT/'ekf-state-dependency.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    t=innovation_allocations()[1]
    s=spec('一条新息怎样分到两个状态','本书第1拍：SOC对线性化端电压的贡献为88.26%，极化项为负27.04%，合计61.22%。分项可能相互抵消，不能把SOC分项当成整体信任概率；C乘K只是局部线性化解释。',[
        node('innov',f'第 1 拍新息\n{t["residual_mv"]:+.3f} mV',480,180,380),
        node('soc',f'SOC 电压分项\nC₀K₀ = {t["soc_share"]*100:.2f}%',250,350,370,110),
        node('rc',f'极化电压分项\nK₁ = {t["urc_share"]*100:.2f}%',710,350,370,110,'#F6F0E1','#926717'),
        node('sum',f'线性化总贡献 C·K\n{t["total_share"]*100:.2f}%',480,505,520,95),
    ], [edge('innov','soc'),edge('innov','rc'),edge('soc','sum'),edge('rc','sum')],[
        label('88% 和 61%，为什么都算对了？',36,49,31),
        label('一条电压证据，两个相关状态；先说清你在算哪个分项。',36,92),
        label('正负分项可以抵消。它们不是两个独立概率，也不是精度。',36,607,23),
        label('只在当前 C 的线性化模型内解释；实际 OCV 曲线仍是非线性的。',36,647,22),
    ],height=690)
    (OUT/'ekf-innovation-allocation.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == "__main__":
    main()
