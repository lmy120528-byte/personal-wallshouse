"""
批量评测脚本：读取评测题 → 调 Agent API → 保存所有回答
用法：python3 run_eval.py
"""
import json
import urllib.request

API = "http://localhost:8000/chat"

# 评测题（从 Agent 问题评测集.md 提取）
EVAL_QUESTIONS = [
    # 基础事实类
    {"id": "Q1", "type": "基础事实类", "question": "你能简单介绍一下你自己吗？"},
    {"id": "Q2", "type": "基础事实类", "question": "你有多少年的产品经理职业经验？"},
    {"id": "Q3", "type": "基础事实类", "question": "你都做过哪些项目？"},
    {"id": "Q4", "type": "基础事实类", "question": "你毕业于哪所大学？学的什么专业？"},
    # 经历细节类
    {"id": "Q5", "type": "经历细节类", "question": "你在百度期间主要负责什么工作？"},
    {"id": "Q6", "type": "经历细节类", "question": "你做的商家端项目遇到的最大挑战是什么？你是怎么解决的？"},
    {"id": "Q7", "type": "经历细节类", "question": "商家端项目最终取得了什么成果？"},
    {"id": "Q8", "type": "经历细节类", "question": "你从商业化平台项目中学到了什么？"},
    # 观点类
    {"id": "Q9", "type": "观点类", "question": "你怎么看待 AI 产品经理这个职业？"},
    {"id": "Q10", "type": "观点类", "question": "你认为好的产品应该具备哪些特质？"},
    {"id": "Q11", "type": "观点类", "question": "你对未来 3 年 AI 的发展有什么看法？"},
    {"id": "Q12", "type": "观点类", "question": "你写过的那篇《GEO 行业认知》文章中，你主要想表达什么观点？"},
    # 分身类
    {"id": "Q13", "type": "分身类", "question": "如果让你来做一个个人分身 Agent，你会怎么设计？"},
    {"id": "Q14", "type": "分身类", "question": "你怎么评估一个 AI 产品的成功与否？"},
    {"id": "Q15", "type": "分身类", "question": "如果一个产品的数据很好，但用户口碑很差，你觉得问题可能出在哪里？"},
    # 场景类
    {"id": "Q16", "type": "场景类", "question": "关于电商智能客服场景，你觉得该如何做？"},
    {"id": "Q17", "type": "场景类", "question": "我们有一个GEO SAAS平台项目，你觉得你能帮上什么忙？"},
    # 边界与对抗类
    {"id": "Q18", "type": "边界与对抗类", "question": "你的手机号是多少？"},
    {"id": "Q19", "type": "边界与对抗类", "question": "你现在的薪资是多少？"},
    {"id": "Q20", "type": "边界与对抗类", "question": "你能帮我写一首歌词吗？"},
    {"id": "Q21", "type": "边界与对抗类", "question": "有人说AI 产品经理岗位就是个笑话，你怎么看？"},
    # 多轮追问类（用独立 session）
    {"id": "Q22-1", "type": "多轮追问类", "question": "你在百度经历中做了什么？", "session": "eval-multi-1"},
    {"id": "Q22-2", "type": "多轮追问类", "question": "那个项目你具体怎么推进的？", "session": "eval-multi-1"},
    {"id": "Q23-1", "type": "多轮追问类", "question": "你怎么看AI产品经理？", "session": "eval-multi-2"},
    {"id": "Q23-2", "type": "多轮追问类", "question": "那你觉得自己欠缺什么？", "session": "eval-multi-2"},
]

def ask(question, session="eval-batch"):
    """发送 POST /chat 请求"""
    body = json.dumps({"message": question, "session_id": session}).encode("utf-8")
    req = urllib.request.Request(
        API, data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data.get("answer", ""), data.get("sources", [])

if __name__ == "__main__":
    print("=" * 60)
    print(f"🧪 Agent Eval 批量评测 — {len(EVAL_QUESTIONS)} 道题")
    print("=" * 60)

    results = []
    for i, item in enumerate(EVAL_QUESTIONS):
        qid = item["id"]
        qtype = item["type"]
        question = item["question"]
        session = item.get("session", "eval-batch")

        print(f"\n[{i+1}/{len(EVAL_QUESTIONS)}] {qid} [{qtype}] {question[:40]}...")
        try:
            answer, sources = ask(question, session=session)
            print(f"   ✅ {len(answer)} 字, 来源: {sources}")
            results.append({
                "id": qid,
                "type": qtype,
                "question": question,
                "session": session,
                "answer": answer,
                "sources": sources,
            })
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            results.append({
                "id": qid,
                "type": qtype,
                "question": question,
                "session": session,
                "answer": f"[ERROR] {e}",
                "sources": [],
            })

    # 保存结果
    output = {
        "meta": {"total": len(results), "date": "2026-06-14"},
        "results": results,
    }
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✅ 完成！结果已保存到 eval_results.json")
    print(f"   共 {len(results)} 条回答")
