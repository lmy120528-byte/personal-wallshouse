# personal-site 项目

## 项目概述
- 张强的个人网页，展示个人信息、技能、社交媒体链接 + 数字分身 Agent（聊天）
- 静态前端 + FastAPI 后端：HTML + CSS + 图片 + RAG 检索

## 技术信息
- 部署平台：腾讯云服务器（nginx 静态服务 + systemd 后端，与奶粉 Agent 同机）
- GitHub 仓库：https://github.com/lmy120528-byte/personal-wallshouse
- 线上地址：http://124.223.77.181/personal/（管理后台 http://124.223.77.181/personal/admin）
- 本地开发：`python3 -m http.server 8080`，然后访问 http://localhost:8080

## 文件结构
- `index.html` — 页面结构（含聊天抽屉）
- `style.css` — 页面样式
- `admin.html` — 管理后台（文章分析/发布、Prompt、日志、服务器 Key 配置）
- `rag-backend/` — 数字分身后端（main.py + retriever.py + knowledge/）
- `images/` — 图片资源（头像、背景图、二维码）
- `部署流程.md` — 部署/同步流程文档

## 服务器部署要点
- 静态文件：`/home/agentuser/personal-site/`（nginx /personal/ 路径服务）
- 后端：`/home/agentuser/personal-rag/`，systemd 服务 `personal-rag`（端口 8001）
- 改动同步：git push 后 scp 到服务器，后端改动需 `systemctl restart personal-rag`
- nginx 配置：`/etc/nginx/sites-enabled/sevenpick`（与奶粉 Agent 共用，改前需用户确认）
