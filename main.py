#!/usr/bin/env python3
"""Render 入口：根目录启动，实际逻辑在 rag-backend/main.py"""
import subprocess, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "rag-backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "rag-backend"))
subprocess.run([sys.executable, "main.py"])
