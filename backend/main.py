from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# 允许跨域请求（前端 index.html 调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://survey.jakestar.cloud"],  # 生产环境建议指定你的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 因子对应题号
FACTOR_ITEMS = {
    "somatization": [1,4,12,27,40,42,48,49,52,53,56,58],
    "obsessive": [3,9,10,28,38,45,46,51,55,65],
    "interpersonal": [6,21,34,36,37,41,61,69,73],
    "depression": [5,14,15,20,22,26,29,30,31,32,54,71,79],
    "anxiety": [2,17,23,33,39,57,72,78,80,86],
    "hostility": [11,24,63,67,74,81],
    "phobic": [13,25,47,50,70,75,82],
    "paranoid": [8,18,43,68,76,83],
    "psychoticism": [7,16,35,62,77,84,85,87,88,90],
    "other": [19,44,59,60,64,66,89]
}

# 请求模型
class AnswerItem(BaseModel):
    idx: int
    var: int

class Answers(BaseModel):
    answers: List[AnswerItem]

# 工具函数：计算因子分数与阳性
def calculate_factors(answer_dict: Dict[int,int]):
    factor_scores = {}
    factor_positive_counts = {}
    factor_flags = {}

    for factor, items in FACTOR_ITEMS.items():
        scores = [answer_dict.get(i, 0) for i in items]
        avg_score = sum(scores) / len(items)
        positive_count = sum(1 for s in scores if s >= 2)
        # 因子阳性：平均分>2 或阳性项目数>2
        is_positive = avg_score > 2 or positive_count > 2

        factor_scores[factor] = avg_score
        factor_positive_counts[factor] = positive_count
        factor_flags[factor] = is_positive

    return factor_scores, factor_positive_counts, factor_flags

# 工具函数：生成文字说明
def generate_report(total_score, total_positive, factor_scores, factor_positive_counts, factor_flags):
    report = []

    # 总分和整体阳性项目
    report.append(f"总分：{total_score} 分")
    if total_score > 160 or total_positive > 43:
        report.append(f"提示：整体心理负担较重（总阳性项目数 {total_positive} 项）")
    else:
        report.append("整体心理状态良好，无明显心理问题")

    # 各因子说明
    for factor in FACTOR_ITEMS.keys():
        avg = factor_scores[factor]
        pos_count = factor_positive_counts[factor]
        flag = factor_flags[factor]
        status = "阳性" if flag else "正常"
        description = ""
        if factor == "somatization":
            description = "反映身体不适，如头痛、肌肉酸痛、心慌等。"
        elif factor == "obsessive":
            description = "包含反复思虑、检查、刻板行为等症状。"
        elif factor == "interpersonal":
            description = "在社交中产生不自在、自卑或被排斥感。"
        elif factor == "depression":
            description = "反映情绪低落、兴趣减退、自责等。"
        elif factor == "anxiety":
            description = "表现为紧张、恐惧、心慌等焦虑症状。"
        elif factor == "hostility":
            description = "包含愤怒、易激惹等表现。"
        elif factor == "phobic":
            description = "对特定情境或对象的恐惧。"
        elif factor == "paranoid":
            description = "表现为多疑、被害感等。"
        elif factor == "psychoticism":
            description = "包含孤僻、思维混乱、幻觉等精神病性症状。"
        elif factor == "other":
            description = "睡眠、饮食异常等生理功能问题。"

        report.append(f"{factor.capitalize()}：平均分 {avg:.2f}，阳性项目数 {pos_count}，判定 {status}。{description}")

    return "\n".join(report)

# FastAPI 路由
@app.post("/scl90/report")
def scl90_report(data: Answers):
    # 转换为题号→分数字典
    answer_dict = {item.idx: item.var for item in data.answers}

    # 计算总分与整体阳性项目数
    total_score = sum(answer_dict.values())
    total_positive = sum(1 for v in answer_dict.values() if v >= 2)

    # 计算因子
    factor_scores, factor_positive_counts, factor_flags = calculate_factors(answer_dict)

    # 生成文字报告
    report = generate_report(total_score, total_positive, factor_scores, factor_positive_counts, factor_flags)

    return {"report": report}