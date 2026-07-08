# -*- coding: utf-8 -*-
"""生成成果图与汇总表（读取 out/scc_national.csv, out/scc_provincial_ramsey.csv）。"""
import os, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['Microsoft YaHei']
plt.rcParams['axes.unicode_minus']=False

here=os.path.dirname(os.path.abspath(__file__)); od=os.path.join(here,'out')

def read_csv(p):
    with open(p,encoding='utf-8-sig') as f: return list(csv.reader(f))

nat=read_csv(os.path.join(od,'scc_national.csv'))
hdr=nat[0]; data=[[float(x) for x in r] for r in nat[1:]]
years=[int(r[0]) for r in data]
ram=[r[1] for r in data]; f25=[r[2] for r in data]; f30=[r[3] for r in data]
f45=[r[4] for r in data]; f50=[r[5] for r in data]

# 图1：全国 SCC 轨迹（动态 + 四档固定）
plt.figure(figsize=(8,5))
plt.plot(years,ram,'-o',lw=2,ms=4,color='#c0392b',label='动态 Ramsey (ρ=0.692%, η=1.07)')
plt.plot(years,f25,'--',color='#2980b9',label='固定 2.5%')
plt.plot(years,f30,'--',color='#27ae60',label='固定 3%')
plt.plot(years,f45,'--',color='#8e44ad',label='固定 4.5%')
plt.plot(years,f50,'--',color='#7f8c8d',label='固定 5%')
plt.xlabel('排放年份'); plt.ylabel('碳社会成本 SCC (CNY/tCO2, 2010价)')
plt.title('全国动态碳社会成本轨迹（SSP2-RCP6.0，标定至 Wang 2022: 2022=46.33 $/tC）')
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(os.path.join(od,'fig_scc_national_trajectory.png'),dpi=150)
plt.close()

# 图2：分省 SCC（2026 与 2050，动态）柱状对比
prov=read_csv(os.path.join(od,'scc_provincial_ramsey.csv'))
phdr=prov[0][1:]
def row_for(y):
    for r in prov[1:]:
        if int(r[0])==y: return [float(x) for x in r[1:]]
v2026=row_for(2026); v2050=row_for(2050)
order=sorted(range(len(phdr)),key=lambda i:v2050[i],reverse=True)
names=[phdr[i] for i in order]; a=[v2026[i] for i in order]; b=[v2050[i] for i in order]
import numpy as np
x=np.arange(len(names))
plt.figure(figsize=(13,5))
plt.bar(x-0.2,a,0.4,label='2026',color='#5dade2')
plt.bar(x+0.2,b,0.4,label='2050',color='#c0392b')
plt.xticks(x,names,rotation=60,ha='right',fontsize=8)
plt.ylabel('SCC (CNY/tCO2)'); plt.title('各省动态碳社会成本（SSP2-RCP6.0，动态折现）')
plt.legend(); plt.grid(axis='y',alpha=0.3); plt.tight_layout()
plt.savefig(os.path.join(od,'fig_scc_provincial.png'),dpi=150)
plt.close()

# 汇总 markdown 表（每5年）
lines=['# SCC 复现结果汇总（SSP2-RCP6.0，2010价）\n',
 '## 全国 SCC 轨迹 (CNY/tCO2)\n',
 '| 年份 | 动态Ramsey | 固定2.5% | 固定3% | 固定4.5% | 固定5% | 动态(≈$/tC) |',
 '|---|---|---|---|---|---|---|']
for r in data:
    if int(r[0])%5==0 or int(r[0]) in (2026,2050):
        lines.append(f"| {int(r[0])} | {r[1]:.1f} | {r[2]:.1f} | {r[3]:.1f} | {r[4]:.1f} | {r[5]:.1f} | {r[6]:.1f} |")
lines.append('\n## 各省 SCC（2026 / 2050，动态，CNY/tCO2）\n')
lines.append('| 省份 | 2026 | 2050 | | 省份 | 2026 | 2050 |')
lines.append('|---|---|---|---|---|---|---|')
half=(len(names)+1)//2
for i in range(half):
    L=f"| {names[i]} | {a[i]:.1f} | {b[i]:.1f} |"
    j=i+half
    R=f" {names[j]} | {a[j]:.1f} | {b[j]:.1f} |" if j<len(names) else "  |  |  |"
    lines.append(L+R)
open(os.path.join(od,'结果汇总.md'),'w',encoding='utf-8').write('\n'.join(lines))
print('[输出] out/fig_scc_national_trajectory.png, out/fig_scc_provincial.png, out/结果汇总.md')
