#!/usr/bin/env python3
"""Render 入口：启动 FastAPI 服务"""
import importlib.util, os, sys

# 加载 rag-backend/main.py 中的 app
backend_dir = os.path.join(os.path.dirname(__file__), "rag-backend")
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

spec = importlib.util.spec_from_file_location("backend", os.path.join(backend_dir, "main.py"))
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

import uvicorn
port = int(os.environ.get("PORT", 8000))
print(f"🚀 启动在端口 {port}")
uvicorn.run(backend.app, host="0.0.0.0", port=port)
