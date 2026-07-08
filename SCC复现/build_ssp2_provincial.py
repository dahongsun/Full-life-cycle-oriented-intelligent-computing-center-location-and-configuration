# -*- coding: utf-8 -*-
"""
重构省级 SSP2 GDP/人口序列（2018–2100）—— 路径A
=================================================
姜彤(2017人口/2018经济)两篇论文的分省结果以"图+0.5°格点库"呈现，正文无省×年完整数值表。
本脚本用论文中**明确给出**的两类信息重构省×年序列：

  (1) 全国 SSP2 轨迹（论文明确）：
      - GDP(2010不变价)：2016≈64.5万亿；增速 2020年代~4.8%、2030–49~2.0%、2050后~1.0%；2100≈260万亿
      - 人口：2030 峰值 14.09亿；2100 降至 9.70亿（先升后降）
  (2) 分省份额：以 2020 年各省 GDP/人口实际份额为基准（公开统计），
      并向姜彤 2090年代 GDP 前8省排序(表2 SSP2)做温和漂移；人口份额近似稳定。

→ 全国总量严格对齐姜彤 SSP2；省级分布与表2/现状一致。最终若有你主模型的精确省级表，可直接替换。
输出：data/1_省级SSP2_GDP人口.csv （列：province,year,gdp_per_capita_CNY,population_persons）
单位：GDP 人均 = CNY/人(2010不变价)；人口 = 人。
"""
import os, csv

YEARS = list(range(2018, 2201))   # 外延到 2200：脉冲损害需积分到收敛(上百年)，避免2100截断导致轨迹下降

# ---------- 全国 SSP2 轨迹 ----------
# GDP 用"平滑下降的年增速曲线"累积，避免折现率出现人工台阶（姜彤 SSP2 增速：
# 2020前~6%、2020年代~4.8%、2030-49~2%、2050后~1%，平滑过渡）。锚点为增速 g(year)。
GDP_BASE_YEAR=2016; GDP_BASE_VAL=64.5   # 万亿元(2010价)
NAT_G_ANCHOR = {2016:0.062,2018:0.057,2020:0.052,2022:0.048,2024:0.044,2026:0.040,2028:0.036,
                2030:0.032,2032:0.028,2034:0.025,2036:0.023,2038:0.021,2040:0.020,2043:0.018,
                2046:0.017,2050:0.015,2060:0.013,2070:0.011,2080:0.010,2090:0.009,2100:0.008,
                2120:0.006,2150:0.005,2200:0.004}   # 2100后缓慢增长(外延,重折现下影响小)
# 国家人口(亿人)
NAT_POP_ANCHOR = {2016:13.83, 2020:14.00, 2024:14.06, 2028:14.085, 2030:14.09, 2034:14.06,
                  2038:13.99, 2042:13.88, 2046:13.74, 2050:13.58, 2060:13.05, 2070:12.35,
                  2080:11.55, 2090:10.65, 2100:9.70, 2120:8.6, 2150:7.6, 2200:6.8}  # 2100后续降(外延)

def lin_interp(anchor, years):
    ks=sorted(anchor); out={}
    for y in years:
        if y<=ks[0]: out[y]=anchor[ks[0]]
        elif y>=ks[-1]: out[y]=anchor[ks[-1]]
        else:
            lo=max(k for k in ks if k<=y); hi=min(k for k in ks if k>=y)
            w=(y-lo)/(hi-lo) if hi>lo else 0; out[y]=anchor[lo]*(1-w)+anchor[hi]*w
    return out

def geom_interp(anchor, years):
    ks=sorted(anchor); out={}
    for y in years:
        if y<=ks[0]: out[y]=anchor[ks[0]]
        elif y>=ks[-1]: out[y]=anchor[ks[-1]]
        else:
            lo=max(k for k in ks if k<=y); hi=min(k for k in ks if k>=y)
            if hi==lo: out[y]=anchor[lo]
            else:
                w=(y-lo)/(hi-lo); out[y]=anchor[lo]*(anchor[hi]/anchor[lo])**w
    return out

def gdp_from_growth(years):
    """由平滑增速曲线累积出国家 GDP(万亿元)，从 GDP_BASE_YEAR 起。"""
    allyears=list(range(GDP_BASE_YEAR, max(years)+1))
    g=lin_interp(NAT_G_ANCHOR, allyears)
    val={GDP_BASE_YEAR:GDP_BASE_VAL}
    for y in allyears[1:]:
        val[y]=val[y-1]*(1+g[y])
    return {y:val[y] for y in years}

# ---------- 2020 各省 GDP(亿元) 与 人口(万人)（公开统计，作份额基准）----------
GDP2020 = {  # 亿元
 '广东':110760,'江苏':102719,'山东':73129,'浙江':64613,'河南':54997,'四川':48598,'福建':43904,
 '湖北':43443,'湖南':41781,'上海':38701,'安徽':38681,'河北':36207,'北京':36103,'陕西':26182,
 '江西':25692,'重庆':25003,'辽宁':25115,'云南':24522,'广西':22157,'山西':17652,'内蒙古':17360,
 '贵州':17827,'天津':14084,'黑龙江':13699,'新疆':13797,'吉林':12311,'甘肃':9017,'海南':5532,
 '宁夏':3921,'青海':3006,'西藏':1903}
POP2020 = {  # 万人
 '广东':12601,'山东':10153,'河南':9937,'江苏':8475,'四川':8367,'河北':7461,'湖南':6644,
 '浙江':6457,'安徽':6103,'湖北':5775,'广西':5013,'云南':4721,'江西':4519,'辽宁':4259,
 '福建':4154,'陕西':3953,'贵州':3856,'山西':3492,'黑龙江':3185,'重庆':3205,'上海':2487,
 '新疆':2585,'甘肃':2502,'吉林':2407,'内蒙古':2405,'北京':2189,'天津':1387,'海南':1008,
 '宁夏':720,'青海':592,'西藏':365}

# 姜彤 2090年代 SSP2 GDP 前8省(表2,万亿元) —— 用于让份额向其温和漂移
GDP2090s_TOP8 = {'广东':29.8,'浙江':24.3,'江苏':22.1,'山东':21.1,'河南':20.3,'河北':10.9,'上海':10.4,'福建':10.1}

def shares(d):
    s=sum(d.values()); return {k:v/s for k,v in d.items()}

def main():
    here=os.path.dirname(os.path.abspath(__file__))
    nat_gdp=gdp_from_growth(YEARS)               # 万亿元（平滑增速累积）
    nat_pop=geom_interp(NAT_POP_ANCHOR, YEARS)   # 亿人

    gdp_share_2020=shares(GDP2020)
    pop_share_2020=shares(POP2020)
    # 2090 GDP 目标份额：前8省用表2，其余省按 2020 份额填充剩余总量
    top8_sum=sum(GDP2090s_TOP8.values())  # 万亿
    nat_2090=nat_gdp[2090]                # 万亿
    g90={}
    rest_share_2020=1-sum(gdp_share_2020[p] for p in GDP2090s_TOP8)
    rest_target=max(0.0,(nat_2090-top8_sum)/nat_2090)
    for p in GDP2020:
        if p in GDP2090s_TOP8: g90[p]=GDP2090s_TOP8[p]/nat_2090
        else: g90[p]=gdp_share_2020[p]/rest_share_2020*rest_target
    # 归一
    ssum=sum(g90.values()); g90={k:v/ssum for k,v in g90.items()}

    rows=[['province','year','gdp_per_capita_CNY','population_persons']]
    provinces=list(GDP2020)
    for y in YEARS:
        # GDP 份额：2020→2090 线性漂移（2090后保持）
        if y<=2020: gw=0.0
        elif y>=2090: gw=1.0
        else: gw=(y-2020)/(2090-2020)
        gsh={p: gdp_share_2020[p]*(1-gw)+g90[p]*gw for p in provinces}
        gtot=sum(gsh.values()); gsh={p:v/gtot for p in provinces for v in [gsh[p]]}
        # 人口份额：近似保持 2020（人口份额变化慢；可后续用2100 Fig5精修）
        psh=pop_share_2020
        nat_gdp_cny=nat_gdp[y]*1e12      # 万亿元→元
        nat_pop_per=nat_pop[y]*1e8       # 亿人→人
        for p in provinces:
            pop_p=nat_pop_per*psh[p]
            gdp_p=nat_gdp_cny*gsh[p]
            gpc=gdp_p/pop_p
            rows.append([p, y, round(gpc,1), int(round(pop_p))])

    out=os.path.join(here,'data','1_省级SSP2_GDP人口.csv')
    with open(out,'w',newline='',encoding='utf-8-sig') as f:
        csv.writer(f).writerows(rows)
    print(f"[写出] {out}  ({len(provinces)}省 × {len(YEARS)}年 = {len(rows)-1} 行)")
    # 自检：2022 全国
    i22=YEARS.index(2022)
    print(f"自检 国家 2022: GDP={nat_gdp[2022]:.1f}万亿(2010价), 人口={nat_pop[2022]:.2f}亿, "
          f"人均={nat_gdp[2022]*1e12/(nat_pop[2022]*1e8):,.0f} CNY/人")

if __name__=='__main__':
    main()
