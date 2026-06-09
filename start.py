#!/usr/bin/env python3
"""Render 入口：启动 FastAPI 服务"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "rag-backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "rag-backend"))

import uvicorn
from main import app  # rag-backend/main.py

port = int(os.environ.get("PORT", 8000))
print(f"🚀 启动在端口 {port}")
uvicorn.run(app, host="0.0.0.0", port=port)
