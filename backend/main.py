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

# 题库
QUESTIONS = [
    "头痛",
    "神经过敏，心中不踏实",
    "头脑中有不必要的想法或字句盘旋",
    "头昏或昏倒",
    "对异性的兴趣减弱",
    "对旁人责备求全",
    "感到别人能控制你的思想",
    "责怪别人制造麻烦",
    "忘性大",
    "担心自己的服饰整齐或仪表的端正",
    "容易烦恼和激动",
    "胸痛",
    "害怕空旷的场所或街道",
    "感到自己的精力下降，活动减弱",
    "想结束自己的生命",
    "听到旁人听不到的声音",
    "发抖",
    "感到大多数人都不可信任",
    "胃口不好",
    "容易哭泣",
    "同异性相处时感到害羞不自在",
    "感到受骗，中了圈套或有人想抓住你",
    "无缘无故地突然感到害怕",
    "自己不能控制的大发脾气",
    "怕单独出门",
    "经常责怪自己",
    "腰痛",
    "感到难以完成任务",
    "感到孤独",
    "感到苦闷",
    "过分担忧",
    "对事物不感兴趣",
    "感到害怕",
    "你的感情容易受到伤害",
    "旁人能知道你的私下的想法",
    "感到别人不理解你、不同情你",
    "感到别人对你不友好、不喜欢你",
    "做事必须做得很慢以保证做得正确",
    "心跳得很厉害",
    "恶心或胃部不舒服",
    "感到比不上他人",
    "肌肉酸痛",
    "感到有人在监视你、谈论你",
    "难以入睡",
    "做事必须反复检查",
    "难以做出决定",
    "怕乘电车、公共汽车、地铁或火车",
    "呼吸有困难",
    "一阵阵发冷或发热",
    "因为感到害怕而避开某些东西、场合或活动",
    "脑子变空了",
    "身体发麻或刺痛",
    "喉咙有梗塞感",
    "感到前途没有希望",
    "不能集中注意",
    "感到身体的某一部分软弱无力",
    "感到紧张或容易紧张",
    "感到手或脚发重",
    "想到死亡的事",
    "吃得太多",
    "当别人看着您或谈论您时感到不自在",
    "有一些不属于您自己的想法",
    "有想打人或伤害他人的冲动",
    "早醒",
    "必须反复洗手、点数",
    "睡得不稳不深",
    "有想摔坏或破坏东西的想法",
    "有一些别人没有的想法",
    "对别人小心谨慎",
    "在公共场所感到不自在",
    "感到任何事情都很困难",
    "一阵阵恐惧或惊恐",
    "感到公共场合吃东西很不舒服",
    "经常与人争论",
    "单独一人时神经很紧张",
    "别人对你的成绩没有作出恰当的评价",
    "即使和别人在一起也感到孤单",
    "感到坐立不安心神不定",
    "感到自己没有什么价值",
    "感到熟悉的东西变成陌生或不像是真的",
    "大叫或摔东西",
    "害怕会在公共场合昏倒",
    "感到别人想占你的便宜",
    "为一些有关性的想法而很苦恼",
    "你认为应该因为自己的过错而受到惩罚",
    "感到要很快把事情做完",
    "感到自己的身体有严重问题",
    "从未感到和其他人很亲近",
    "感到自己有罪",
    "感到自己的脑子有毛病"
]

OPTIONS = [
    {"label": "A", "text": "没有", "val": 1},
    {"label": "B", "text": "很轻", "val": 2},
    {"label": "C", "text": "中等", "val": 3},
    {"label": "D", "text": "偏重", "val": 4},
    {"label": "E", "text": "严重", "val": 5},
]

@app.get("/api/questions")
async def get_questions():
    return {"questions": QUESTIONS}

@app.get("/api/options")
async def get_options():
    return {"options": OPTIONS}

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

@app.post("/api/scl90")
async def scl90_result(request: Request):
    data = await request.json()
    answers = data.get("filledAnswers", [])

    if len(answers) != 90:
        return {"error": "答案数量必须为90项"}

    # 1️⃣ 计算总分与阳性项目数
    total_score = sum(answers)
    positive_count = sum(1 for x in answers if x >= 2)

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
   🧠 SCL-90 量表测评结果报告
=======================

【总体情况】
- 总分：{total_score} 分（{'阳性' if total_score > 160 else '正常'}）
- 阳性项目数：{positive_count} 项（{'阳性' if positive_count > 43 else '正常'}）
- 整体结论：{overall_flag}

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
   - 本结果仅供自测参考，若症状持续或影响日常生活，请寻求专业心理咨询或临床帮助。
"""

    return JSONResponse(content={
        "total_score": total_score,
        "positive_count": positive_count,
        "overall_flag": overall_flag,
        "factors": factor_results,
        "summary": summary.strip()
    })
