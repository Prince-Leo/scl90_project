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

MSD1 = {
    "躯体化": "1.37±0.48",
    "强迫症状": "1.62±0.58",
    "人际关系敏感": "1.65±0.61",
    "抑郁": "1.50±0.59",
    "焦虑": "1.39±0.43",
    "敌对": "1.46±0.55",
    "恐怖": "1.23±0.41",
    "偏执": "1.43±0.57",
    "精神病性": "1.29±0.42",
}

MSD2 = {
    "躯体化": "[0.89, 1.85]",
    "强迫症状": "[1.04, 2.20]",
    "人际关系敏感": "[1.04, 2.26]",
    "抑郁": "[0.91, 2.09]",
    "焦虑": "[0.96, 1.82]",
    "敌对": "[0.91, 2.01]",
    "恐怖": "[0.82, 1.64]",
    "偏执": "[0.86, 2.00]",
    "精神病性": "[0.87, 1.71]",
}


levels = ["正常", "轻度", "中度", "重度"]

@app.post("/api/scl90")
async def scl90_result(request: Request):
    data = await request.json()
    answers = data.get("filledAnswers", [])

    if len(answers) != 90:
        return {"error": "答案数量必须为90项"}

    # 1️⃣ 计算总分、阳性项目数及等级
    total_score = sum(answers)
    total_flag = "阳性" if (total_score > 160) else "正常"
    positive_count = sum(1 for x in answers if x >= 2)
    positive_flag = "阳性" if (positive_count > 43) else "正常"
    overall_flag = "阳性" if (total_score > 160 or positive_count > 43) else "正常"
    overall_desc = "在一些方面可能感受到一定的压力或不适" if (total_score > 160 or positive_count > 43) else "各方面心理状态较为健康，未见明显异常迹象"

    avg_score = round(sum(answers) / len(answers), 2)

    index = min(int(avg_score - 1), 3)
    level = levels[index]

    overall_results = {
        "总分": {"A": total_score, "B": "90~450", "C": total_flag},
        "阳性项目数": {"A": positive_count,"B": "0~90", "C": positive_flag},
        "总症状指数": {"A": avg_score, "B": "1~5", "C": level},
    }

    # 2️⃣ 各因子统计
    factor_results = {}
    for name, idxs in FACTORS.items():
        vals = [answers[i-1] for i in idxs]  # 转为0基索引
        total = sum(vals)
        avg = round(sum(vals) / len(vals), 2)
        if name == "其他":
            factor_results[其他] = {
            "总分": total,
            "均分": avg,
            "判定": "-",
            "M±SD": "-",
            }
            break
        level = "正常"
        msd_value = MSD1.get(name, "")
        factor_results[name] = {
            "总分": total,
            "均分": avg,
            "判定": level,
            "M±SD": msd_value,
        }

    return JSONResponse(content={
        "overall_flag": overall_flag,
        "overall_desc": overall_desc,
        "overall_results": overall_results,
        "factor_results": factor_results
        })
