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
    "躯体化": [1, 4, 12, 27, 40, 42, 48, 49, 52, 53, 56, 58],
    "强迫症状": [3, 9, 10, 28, 38, 45, 46, 51, 55, 65],
    "人际关系敏感": [6, 21, 34, 36, 37, 41, 61, 69, 73],
    "抑郁": [5, 14, 15, 20, 22, 26, 29, 30, 31, 32, 54, 71, 79],
    "焦虑": [2, 17, 23, 33, 39, 57, 72, 78, 80, 86],
    "敌对": [11, 24, 63, 67, 74, 81],
    "恐怖": [13, 25, 47, 50, 70, 75, 82],
    "偏执": [8, 18, 43, 68, 76, 83],
    "精神病性": [7, 16, 35, 62, 77, 84, 85, 87, 88, 90],
    "其他": [19, 44, 59, 60, 64, 66, 89],
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
    "躯体化": [0.89, 1.85],
    "强迫症状": [1.04, 2.20],
    "人际关系敏感": [1.04, 2.26],
    "抑郁": [0.91, 2.09],
    "焦虑": [0.96, 1.82],
    "敌对": [0.91, 2.01],
    "恐怖": [0.82, 1.64],
    "偏执": [0.86, 2.00],
    "精神病性": [0.87, 1.71],
}

desc = {
    "躯体化": "总分范围在12～60分之间。\n得分在36分以上，表明个体在身体上有较明显的不适感，并常伴有头痛、肌肉酸痛等症状；\n得分在24分以下，说明躯体症状表现不明显。\n总的来说，得分越高，躯体不适感越强；得分越低，症状体验越不明显。",
    "强迫症状": "总分范围在10～50分之间。得分在30分以上，强迫症状较明显；得分在20分以下，强迫症状不明显。总的来说，得分越高，表明个体越难以摆脱一些无意义的行为、思想和冲动，并可能表现出一定的认知障碍行为；得分越低，表明个体在此类症状上表现不明显，没有出现明显的强迫行为。",
    "人际关系敏感": "总分范围在9～45分之间。得分在27分以上，表明个体在人际关系上较为敏感，人际交往中自卑感较强，并常伴有行为症状（如坐立不安、退缩等）；得分在18分以下，表明个体在人际关系上较为正常。总的来说，得分越高，个体在人际交往中表现的问题越多，自卑与自我中心越突出，并可能表现出消极的期待；得分越低，说明个体在人际关系中更为自信、应对自如，并抱有积极的期待。",
    "抑郁": "总分范围在13～65分之间。得分在39分以上，表明个体的抑郁程度较强，生活缺乏兴趣与活力，极端情况下可能会出现想死亡或自杀的念头；得分在26分以下，表明个体的抑郁程度较弱，生活态度积极乐观，充满活力，心境愉快。总的来说，得分越高，抑郁程度越明显；得分越低，抑郁程度越不明显。",
    "焦虑": "总分范围在10～50分之间。得分在30分以上，表明个体较易焦虑，常表现为烦躁、不安、神经过敏等，严重时可能出现惊恐发作；得分在20分以下，表明个体不易焦虑，心理状态较为安定。总的来说，得分越高，焦虑表现越明显；得分越低，越不易出现焦虑。",
    "敌对": "总分范围在6～30分之间。得分在18分以上，表明个体易表现出敌对的思想、情感和行为；得分在12分以下，表明个体较为友好，待人温和。总的来说，得分越高，个体越容易表现出敌对、好争论、脾气难以控制的倾向；得分越低，个体脾气越温和，待人友善，不喜欢争论，也不会出现破坏性行为。",
    "恐怖": "总分范围在7～35分之间。得分在21分以上，表明个体恐怖症状较为明显，常表现为社交恐惧、广场恐惧或人群恐惧；得分在14分以下，表明个体的恐怖症状不明显。总的来说，得分越高，个体越容易对某些场所或物体产生恐惧，并伴随明显的躯体症状；得分越低，说明个体不易产生恐惧心理，能较为正常地进行交往和活动。",
    "偏执": "总分范围在6～30分之间。得分在18分以上，表明个体的偏执症状较为明显，容易出现猜疑和敌对心理；得分在12分以下，表明个体的偏执症状不明显。总的来说，得分越高，个体越容易表现出偏执倾向，出现投射性思维或妄想；得分越低，思维越理性，不易走向极端。",
    "精神病性": "总分范围在10～50分之间。得分在30分以上，表明个体的精神病性症状较为明显；得分在20分以下，表明个体的精神病性症状不明显。总的来说，得分越高，表现出的精神病性症状和行为越多；得分越低，相关症状表现越少。",
    "其他": "包括睡眠、饮食等方面，作为附加项目或第十个因子进行处理，以使各因子分数之和等于总分。",
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
    overall_desc = (
        "在一些方面可能感受到一定的压力或不适"
        if (total_score > 160 or positive_count > 43)
        else "各方面心理状态较为健康，未见明显异常迹象"
    )

    avg_score = round(sum(answers) / len(answers), 2)

    index = min(int(avg_score - 1), 3)
    level = levels[index]

    overall_results = {
        "总分": {"A": total_score, "B": "90~450", "C": total_flag},
        "阳性项目数": {"A": positive_count, "B": "0~90", "C": positive_flag},
        "总症状指数": {"A": avg_score, "B": "1~5", "C": level},
    }

    # 2️⃣ 各因子统计
    factor_results = {}
    for name, idxs in FACTORS.items():
        vals = [answers[i - 1] for i in idxs]  # 转为0基索引
        total = sum(vals)
        avg = round(sum(vals) / len(vals), 2)
        if name == "其他":
            factor_results[name] = {
                "总分": total,
                "均分": avg,
                "判定": "-",
                "M±SD": "-",
            }
        else:
            # 获取对应因子的 M±SD 和范围
            msd_range = MSD2.get(name, [1, 2])
            min_val, max_val = msd_range

            # 判断因子的等级
            level = "正常"
            if avg >= min_val and avg <= max_val:
                level = "正常"
            elif avg > max_val and avg <= 3:
                level = "轻度"
            elif avg > 3 and avg <= 4:
                level = "中度"
            elif avg > 4 and avg <= 5:
                level = "重度"
            msd_value = MSD1.get(name, "-")
            factor_results[name] = {
                "总分": total,
                "均分": avg,
                "判定": level,
                "M±SD": msd_value,
            }

    return JSONResponse(
        content={
            "overall_flag": overall_flag,
            "overall_desc": overall_desc,
            "overall_results": overall_results,
            "factor_results": factor_results,
            "factor_desc": desc,
        }
    )
