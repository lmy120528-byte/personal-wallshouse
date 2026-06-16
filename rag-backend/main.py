"""
main.py — 数字分身聊天服务

作用：启动一个 API 服务，接收用户的聊天请求，
     从知识库检索相关内容 → 组装提示词 → 调用 DeepSeek → 返回回答。

用法：python3 main.py
     服务启动在 http://localhost:8000
     聊天接口：POST /chat（一次性返回）
     流式接口：POST /chat/stream（逐字输出）
"""

import os
import json
import ssl
import http.client
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urlparse
from retriever import Retriever
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# ============================================================
# 配置
# ============================================================
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
MAX_RETRIEVED = 8      # 每次最多检索几条知识
MAX_HISTORY = 6         # 对话历史最多保留几轮（单数会取整）
LOG_FILE = os.path.join(os.path.dirname(__file__), "chat_logs.jsonl")  # 对话日志
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 从环境变量读取，不给前端暴露

# ============================================================
# System Prompt —— Agent 人格定义
# ============================================================
# ---- System Prompt 管理 ----
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "system_prompt.txt")

def load_system_prompt():
    """从文件读取 System Prompt，文件不存在则返回默认值"""
    try:
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return content
    except Exception as e:
        print(f"[prompt] 读取失败: {e}")
    return "你是张强的数字分身。基于知识库内容回答问题。如果知识库中没有相关信息，坦诚说明。"

def save_system_prompt(text):
    """保存 System Prompt 到文件"""
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(text.strip())

# 启动时打印 Prompt 前 80 字
_prompt = load_system_prompt()
print(f"📝 System Prompt: {_prompt[:80]}...")

# ---- 对话日志 ----
def log_conversation(ip, session_id, question, answer, sources):
    """将一轮对话追加写入 JSONL 日志文件（一行一条 JSON）"""
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "session": session_id,
        "question": question,
        "answer": answer,
        "sources": sources
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[log error] {e}")


# ============================================================
# 初始化：TF-IDF 轻量检索
# ============================================================
from retriever import Retriever

retriever = Retriever()
print("📦 加载知识索引...")
try:
    retriever.load()
except Exception:
    print("   ⚠️  索引不存在，自动构建中...")
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "ingest.py")],
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    if result.returncode == 0:
        retriever.load()
    else:
        print(f"   ❌ 自动构建失败: {result.stderr[:200]}")

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(title="张强数字分身 API", version="0.1")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 对话历史（服务重启会清空，生产环境可换 Redis）
chat_histories: dict[str, list] = {}


# ---- 请求/响应模型 ----
class ChatRequest(BaseModel):
    message: str                     # 用户消息
    session_id: str = "default"      # 会话 ID（用于区分不同用户）


class ChatResponse(BaseModel):
    answer: str                      # Agent 回答
    sources: list[str] = []          # 引用了哪些知识来源


# ---- 核心：检索知识 ----
def search_knowledge(query: str, n: int = MAX_RETRIEVED, api_key: str = None):
    """两阶段检索：TF-IDF 粗筛 + DeepSeek 精排，返回 [(文本, 来源, 元数据), ...]"""
    return retriever.search(query, n=n, api_key=api_key)


# ---- 核心：生成回答 ----
def generate_answer(question: str, knowledge: list, history: list, api_key: str):
    """
    组装 Prompt → 调用 DeepSeek → 返回回答。
    """

    # 组装知识上下文（简洁格式，避免模型复述标记）
    knowledge_text = ""
    for i, item in enumerate(knowledge):
        text, source = item[0], item[1]
        knowledge_text += f"\n[参考{i+1} · {source}]\n{text}\n"

    # 组装对话历史
    history_text = ""
    for h in history:
        history_text += f"\n用户：{h['user']}\n张强：{h['agent']}\n"

    # ⚠️ 合并为一条 System 消息，避免多条 System 消息权重不确定
    system_content = load_system_prompt()
    system_content += "\n\n【知识库 — 严格基于以下内容回答。未提及的信息一律视为不存在。禁止编造。】"
    system_content += "\n⚠️ 禁止在回答中输出\"[参考N]\"等标记、禁止逐字复述知识片段原文。这些内容仅供你理解背景。"
    system_content += "\n\n【回答前自检】在回答工作经历类问题前，先在心里默念一遍你待过的所有公司：①北京瑞金麟 ②山东云医康 ③百度健康 ④GEO创业。然后在回答中逐一提到这四家公司，缺一不可。\n"
    system_content += knowledge_text

    if history_text:
        system_content += f"\n\n【对话历史 — 用于理解上下文和追问】\n{history_text}"

    # 构造消息 — 只有一条 System 消息
    # 工作经历类问题：用户消息前置公司列表，强制逐家枚举
    user_message = question
    career_kw = ['经验', '经历', '工作', '职业', '公司', '简历', '履历', '项目经历']
    if any(kw in question for kw in career_kw):
        user_message = '回答要求：逐一列出你工作过的全部4家公司（①北京瑞金麟 ②山东云医康 ③百度健康 ④GEO创业），然后展开。不得跳过、合并或省略任何一家。\n\n用户问题：' + question

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]

    # 调用 DeepSeek API
    req_body = {
        "model": "deepseek-v4-pro",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1200,
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
    }

    req = urllib.request.Request(
        DEEPSEEK_API,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            message = data["choices"][0]["message"]
            # 只取 content，reasoning_content（思考过程）不展示给用户
            answer = message.get("content", "")
            return answer
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return f"[API 错误 {e.code}] {err_body[:300]}"
    except Exception as e:
        return f"[请求失败] {str(e)}"


# ---- API 端点 ----
@app.get("/")
def root():
    return {"ok": True, "status": "张强数字分身运行中", "chunks": len(retriever.chunks) if retriever.chunks else 0}


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    """聊天接口：接收问题，返回回答"""

    if not DEEPSEEK_KEY:
        return ChatResponse(answer="服务未配置 API Key，请联系站长。")

    if not retriever.chunks:
        return ChatResponse(answer="知识库为空，请先运行 ingest.py 导入知识")

    knowledge = search_knowledge(req.message, api_key=DEEPSEEK_KEY)
    session = req.session_id
    if session not in chat_histories:
        chat_histories[session] = []
    history = chat_histories[session]

    answer = generate_answer(req.message, knowledge, history, DEEPSEEK_KEY)

    history.append({"user": req.message, "agent": answer})
    if len(history) > MAX_HISTORY:
        history.pop(0)

    sources = [item[2].get("file", item[1]) for item in knowledge]

    # 记录日志
    client_ip = request.client.host if request.client else "unknown"
    log_conversation(client_ip, session, req.message, answer, sources)

    return ChatResponse(answer=answer, sources=sources)


# ---- 流式生成器 ----
def stream_deepseek(messages, api_key):
    """
    调用 DeepSeek 流式 API，逐块 yield 内容。
    DeepSeek 返回的是 SSE 格式：
      data: {"choices":[{"delta":{"content":"你好"}}]}
      data: [DONE]
    """
    parsed = urlparse(DEEPSEEK_API)
    conn = http.client.HTTPSConnection(
        parsed.netloc,
        context=ssl.create_default_context(),
        timeout=60
    )

    body = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1200,
        "stream": True,
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
    })

    try:
        conn.request("POST", parsed.path, body=body.encode("utf-8"), headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })

        resp = conn.getresponse()

        # 检查 HTTP 状态码，非 200 时读取错误信息并抛出
        if resp.status != 200:
            err_body = resp.read().decode("utf-8", errors="replace")
            raise Exception(f"DeepSeek API 返回 {resp.status}: {err_body[:300]}")

        # 逐行读取 SSE 流
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:]  # 去掉 "data: " 前缀
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
                delta = obj["choices"][0].get("delta", {})
                # 推理过程（思考链）
                reasoning = delta.get("reasoning_content", "")
                if reasoning:
                    yield ("reasoning", reasoning)
                # 最终回答
                content = delta.get("content", "")
                if content:
                    yield ("content", content)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    except Exception as e:
        # 将异常作为错误事件 yield 出去，前端可以展示
        yield ("error", str(e))
    finally:
        conn.close()


@app.post("/chat/stream")
def chat_stream(req: ChatRequest, request: Request):
    """流式聊天接口：逐字返回回答"""

    if not DEEPSEEK_KEY:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': '服务未配置 API Key，请联系站长。'}, ensure_ascii=False)}\n\n"]),
            media_type="text/event-stream"
        )

    if not retriever.chunks:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': '知识库为空，请先运行 ingest.py'}, ensure_ascii=False)}\n\n"]),
            media_type="text/event-stream"
        )

    knowledge = search_knowledge(req.message, api_key=DEEPSEEK_KEY)
    client_ip = request.client.host if request.client else "unknown"

    # 组装 Prompt（合并为一条 System 消息，避免多条 System 消息权重不确定）
    knowledge_text = ""
    for i, item in enumerate(knowledge):
        text, source = item[0], item[1]
        knowledge_text += f"\n[参考{i+1} · {source}]\n{text}\n"

    # 对话历史
    session = req.session_id
    if session not in chat_histories:
        chat_histories[session] = []
    history = chat_histories[session]

    history_text = ""
    for h in history:
        history_text += f"\n用户：{h['user']}\n张强：{h['agent']}\n"

    # 合并为一条 System 消息
    system_content = load_system_prompt()
    system_content += "\n\n【知识库 — 严格基于以下内容回答。未提及的信息一律视为不存在。禁止编造。】"
    system_content += "\n⚠️ 禁止在回答中输出\"[参考N]\"等标记、禁止逐字复述知识片段原文。这些内容仅供你理解背景。"
    system_content += "\n\n【回答前自检】在回答工作经历类问题前，先在心里默念一遍你待过的所有公司：①北京瑞金麟 ②山东云医康 ③百度健康 ④GEO创业。然后在回答中逐一提到这四家公司，缺一不可。\n"
    system_content += knowledge_text

    if history_text:
        system_content += f"\n\n【对话历史 — 用于理解上下文和追问】\n{history_text}"

    # 工作经历类问题：用户消息前置公司列表，强制逐家枚举
    user_message = req.message
    career_kw = ['经验', '经历', '工作', '职业', '公司', '简历', '履历', '项目经历']
    if any(kw in req.message for kw in career_kw):
        user_message = '回答要求：逐一列出你工作过的全部4家公司（①北京瑞金麟 ②山东云医康 ③百度健康 ④GEO创业），然后展开。不得跳过、合并或省略任何一家。\n\n用户问题：' + req.message

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]

    # 整理来源
    sources = [item[2].get("file", item[1]) for item in knowledge]

    # 流式生成
    def generate():
        full_answer = ""

        # 先发送来源信息
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

        try:
            for chunk_type, chunk_text in stream_deepseek(messages, DEEPSEEK_KEY):
                if chunk_type == "error":
                    # 流式调用出错，直接返回错误
                    yield f"data: {json.dumps({'type': 'error', 'error': chunk_text}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                if chunk_type == "content":
                    full_answer += chunk_text
                yield f"data: {json.dumps({'type': chunk_type, 'content': chunk_text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

        # 保存对话历史
        if full_answer.strip():
            history.append({"user": req.message, "agent": full_answer.strip()})
            if len(history) > MAX_HISTORY:
                history.pop(0)
            # 记录日志
            log_conversation(client_ip, req.session_id, req.message, full_answer.strip(), sources)

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---- System Prompt 管理 ----
class PromptUpdate(BaseModel):
    content: str

@app.get("/system-prompt")
def get_prompt():
    """获取当前 System Prompt"""
    return {"content": load_system_prompt()}

@app.post("/system-prompt")
def update_prompt(req: PromptUpdate):
    """更新 System Prompt（动态生效，无需重启）"""
    save_system_prompt(req.content)
    return {"ok": True, "length": len(req.content)}


# ---- 索引热重载 ----
@app.post("/reload-index")
def reload_index():
    """热重载 TF-IDF 索引（知识库更新后调用，无需重启服务）"""
    try:
        before = len(retriever.chunks) if retriever.chunks else 0
        retriever.load()
        after = len(retriever.chunks)
        print(f"   🔄 索引热重载: {before} → {after} 个切片")
        return {"ok": True, "chunks_before": before, "chunks_after": after}
    except Exception as e:
        print(f"   ❌ 索引重载失败: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---- 日志查看 ----
@app.get("/chat/logs")
def view_logs(limit: int = 50):
    """查看最近的对话日志"""
    logs = []
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        # 返回最近的 N 条（倒序）
        return JSONResponse({"total": len(logs), "logs": logs[-limit:][::-1]})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("\n" + "=" * 60)
    print("🏠 张强数字分身 API 启动")
    print(f"   地址: http://0.0.0.0:{port}")
    print(f"   文档: http://0.0.0.0:{port}/docs")
    print(f"   聊天: POST http://0.0.0.0:{port}/chat")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
