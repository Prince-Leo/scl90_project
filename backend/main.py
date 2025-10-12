from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# 允许跨域访问（前端可以直接请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["survey.jakestar.cloud"],  # 生产环境建议改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各因子题号（从1开始计数）
FACTORS = {
    "躯体化": [1,4,12,27,40,42,48,49,52,53,56,58],
    "强迫症状": [3,9,10,28,38,45,46,51,55,65],
    "人际关系敏感": [6,21,34,36,37,41,61,69,73],
    "抑郁": [5,14,15,20,22,26,29,30,31,32,54,71,79],
    "焦虑": [2,17,23,33,39,57,72,78,80,86],
    "敌对": [11,24,63,67,74,81],
    "恐怖": [13,25,47,50,70,75,82],
    "偏执": [8,18,43,68,76,83],
    "精神病性": [7,16,35,62,77,84,85,87,88,90],
    "其他": [19,44,59,60,64,66,89],
}

levels = ["无抑郁", "轻度抑郁", "中度抑郁", "重度抑郁"]

@app.post("/api/scl90")
async def scl90_result(request: Request):
    data = await request.json()
    answers = data.get("filledAnswers", [])

    if len(answers) != 90:
        return {"error": "答案数量必须为90项"}

    # 1️⃣ 计算总分与阳性项目数及等级
    total_score = sum(answers)
    total_flag = '阳性' if total_score > 160 else '正常'
    positive_count = sum(1 for x in answers if x >= 2)
    positive_flag = '阳性' if positive_count > 43 else '正常'
    avg_score = round(sum(answers) / len(answers), 2)
    index = min(int(avg_score - 1), 3)
    level = levels[index]

    # 2️⃣ 各因子统计
    factor_results = {}
    for name, idxs in FACTORS.items():
        vals = [answers[i-1] for i in idxs]  # 转为0基索引
        avg = round(sum(vals) / len(vals), 2)
        pos = sum(1 for v in vals if v >= 2)
        flag = "阳性" if (avg > 2 or pos > 2) else "正常"
        factor_results[name] = {
            "平均分": avg,
            "阳性项目数": pos,
            "判定": flag,
        }

    # 3️⃣ 总体判定
    overall_flag = "阳性" if (total_score > 160 or positive_count > 43) else "正常"

    header = "【各因子分析】\n"
    lines = []

    # 控制列宽，名称对齐，平均分右对齐
    for k, v in factor_results.items():
        lines.append(
            f"    {k.ljust(8, '　')} 平均分：{str(v['平均分']).ljust(5)}"
            f"阳性项目：{str(v['阳性项目数']).ljust(3)} 判定：{v['判定']}"
        )


    # 4️⃣ 生成文字描述
    summary = f"""
=======================
      SCL-90 量表测评结果报告
=======================

【总体情况】
- 总分：{total_score} 分（{total_flag}）
- 阳性项目数：{positive_count} 项（{positive_flag}）
- 整体结论：{overall_flag}
- 整体平均分：{avg_score}
- 抑郁程度：{level}

--------------------------------
{header}{chr(10).join(lines)}

--------------------------------
【结果说明】
1️⃣ 总体判定依据：
   - 总分 > 160 分，或阳性项目数 > 43 项 → 可能存在总体心理问题；
   - 若满足任一条件，则建议进一步心理评估。

2️⃣ 因子阳性判定依据：
   - 因子平均分 > 2 分，或该因子内阳性项目数 > 2 项 → 视为该因子阳性；
   - 因子阳性说明该维度存在一定心理压力或障碍倾向。

3️⃣ 结果解读提示：
   - 若多个因子阳性，说明心理问题可能涉及多个方面；
   - 若单一因子阳性，可针对该领域（如焦虑、抑郁等）进行重点关注；
"""

    return JSONResponse(content={
        "total_score": total_score,
        "total_flag": total_flag,
        "positive_count": positive_count,
        "positive_flag": positive_flag,
        "overall_flag": overall_flag,
        "avg_score": avg_score,
        "level":level,
        "factor_results": factor_results,
        "summary": summary.strip()
    })
