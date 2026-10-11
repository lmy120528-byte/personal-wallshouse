#!/usr/bin/env python3
"""
本地 API 代理 —— 解决浏览器 CORS 跨域限制
将管理工具的请求转发到 DeepSeek API

用法：python3 proxy.py
默认端口 8081，管理工具会自动连接
"""

import http.server
import json
import urllib.request
import urllib.error
import os

PROXY_PORT = 8081
DEEPSEEK_API = 'https://api.deepseek.com/v1/chat/completions'

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        """路由：/analyze → DeepSeek，/deploy → 部署文章，/update-knowledge → 知识库导出，/git-pull → 本地同步"""
        if self.path == '/git-pull':
            self._handle_git_pull()
            return

        if self.path == '/deploy':
            self._handle_deploy()
            return

        if self.path == '/read-articles':
            self._handle_read_articles()
            return

        if self.path == '/update-knowledge':
            self._handle_update_knowledge()
            return

        if self.path != '/analyze':
            self.send_response(404)
            self._cors_headers()
            self.end_headers()
            return

        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            req_data = json.loads(body)

            api_key = req_data.pop('api_key', '') or os.environ.get('DEEPSEEK_API_KEY', '')
            if not api_key:
                self._error(400, '缺少 api_key（请在管理后台设置或配置环境变量 DEEPSEEK_API_KEY）')
                return

            # 转发到 DeepSeek
            http_req = urllib.request.Request(
                DEEPSEEK_API,
                data=json.dumps(req_data).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
            )

            with urllib.request.urlopen(http_req) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp_body)

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace')
            self._error(e.code, err_body[:500])
        except Exception as e:
            self._error(500, str(e))

    def _handle_git_pull(self):
        """执行 git pull 同步本地文件"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                self.send_response(200)
                self._cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'ok': True,
                    'output': output.strip()
                }).encode('utf-8'))
            else:
                self._error(500, output.strip())
        except Exception as e:
            self._error(500, str(e))

    def _handle_read_articles(self):
        """读取本地 articles-data.js 并返回解析后的文章列表"""
        import subprocess as sp
        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(project_dir, 'articles-data.js')

            if not os.path.exists(data_file):
                self.send_response(200)
                self._cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'articles': [], 'raw': ''}).encode('utf-8'))
                return

            with open(data_file, 'r', encoding='utf-8') as f:
                raw = f.read()

            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'raw': raw}).encode('utf-8'))

        except Exception as e:
            self._error(500, str(e))

    def _handle_deploy(self):
        """接收文章内容 → 写入文件 → git add/commit/push"""
        import subprocess as sp
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            req_data = json.loads(body)

            content = req_data.get('content', '')
            message = req_data.get('message', '更新文章')

            if not content:
                self._error(400, '缺少 content 字段')
                return

            project_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(project_dir, 'articles-data.js')

            # 写入文件
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # git add 所有变更（不漏任何文件）
            r1 = sp.run(['git', 'add', '.'],
                       capture_output=True, text=True, timeout=10, cwd=project_dir)
            if r1.returncode != 0:
                self._error(500, 'git add 失败: ' + (r1.stderr or r1.stdout))
                return

            # git status 检查是否有东西要提交
            r_status = sp.run(['git', 'status', '--porcelain'],
                            capture_output=True, text=True, timeout=10, cwd=project_dir)
            if not r_status.stdout.strip():
                # 没有变更，跳过 commit/push
                print('   ⚠️ 没有新变更，跳过 push')
                self.send_response(200)
                self._cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'ok': True,
                    'output': '没有新变更，已跳过',
                    'files': []
                }).encode('utf-8'))
                return

            # 列出本次提交的文件
            changed_files = [line[3:] for line in r_status.stdout.strip().split('\n') if line.strip()]
            print(f'   📦 将提交 {len(changed_files)} 个文件: {changed_files}')

            # git commit
            r2 = sp.run(['git', 'commit', '-m', message],
                       capture_output=True, text=True, timeout=10, cwd=project_dir)
            if r2.returncode != 0 and 'nothing to commit' not in r2.stdout + r2.stderr:
                self._error(500, 'git commit 失败: ' + (r2.stderr or r2.stdout))
                return

            # git push
            r3 = sp.run(['git', 'push', 'origin', 'main'],
                       capture_output=True, text=True, timeout=30, cwd=project_dir)
            if r3.returncode != 0:
                self._error(500, 'git push 失败: ' + (r3.stderr or r3.stdout))
                return

            print(f'   ✅ 推送成功 → GitHub（腾讯云服务器手动同步，已改为自动）')

            # 自动同步腾讯云服务器：文章数据 + 知识库 + 索引 + 热加载
            sync_result = self._sync_to_server(project_dir)

            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'ok': True,
                'output': (r2.stdout + r3.stdout).strip(),
                'server_sync': sync_result,
                'files': changed_files
            }).encode('utf-8'))

        except Exception as e:
            self._error(500, str(e))

    def _sync_to_server(self, project_dir):
        """推送后自动同步腾讯云服务器：articles-data.js + 知识库 + 索引 + 热加载。

        返回 {"ok": bool, "detail": str}；失败不阻断部署（页面提示，可手动喊 Claude 补同步）。
        """
        import subprocess as sp
        SERVER = 'agentuser@124.223.77.181'
        SITE_DIR = '/home/agentuser/personal-site'
        RAG_DIR = '/home/agentuser/personal-rag'
        # 防 macOS tar/scp 产生 ._ AppleDouble 垃圾文件
        env = dict(os.environ, COPYFILE_DISABLE='1')
        detail_parts = []

        def run_step(cmd, label, timeout=90):
            r = sp.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
            ok = r.returncode == 0
            err = (r.stderr or '').strip()
            detail_parts.append(f"{'✅' if ok else '❌'} {label}" + (f"（{err[:120]}）" if err else ""))
            return ok

        # ① 文章数据（线上文章列表）
        run_step(['scp', '-q', os.path.join(project_dir, 'articles-data.js'),
                  f'{SERVER}:{SITE_DIR}/'], '文章列表 articles-data.js')

        # ② 知识库文件（只传 .txt/.md，绝不整包传目录，防 ._ 垃圾文件）
        knowledge_dir = os.path.join(project_dir, 'rag-backend', 'knowledge')
        kb_files = [f for f in os.listdir(knowledge_dir)
                    if (f.endswith('.txt') or f.endswith('.md'))
                    and not f.startswith('.')]
        if kb_files:
            kb_paths = [os.path.join(knowledge_dir, f) for f in kb_files]
            run_step(['scp', '-q'] + kb_paths + [f'{SERVER}:{RAG_DIR}/knowledge/'],
                     f'知识库文件 {len(kb_files)} 个')
        else:
            detail_parts.append('⚠️ 知识库目录为空，跳过')

        # ③ 检索索引（embeddings.pkl）
        run_step(['scp', '-q', os.path.join(project_dir, 'rag-backend', 'embeddings.pkl'),
                  f'{SERVER}:{RAG_DIR}/'], '检索索引 embeddings.pkl')

        # ④ 服务器热加载索引（无需重启 systemd 服务）
        run_step(['ssh', '-o', 'ConnectTimeout=10', SERVER,
                  'curl -s -X POST http://127.0.0.1:8001/reload-index'],
                 '服务器索引热加载')

        detail = ' | '.join(detail_parts)
        ok = all('❌' not in p for p in detail_parts)
        if ok:
            print(f'   🚀 腾讯云服务器同步完成')
        else:
            print(f'   ⚠️ 服务器同步部分失败: {detail}')
        return {'ok': ok, 'detail': detail}

    def _handle_update_knowledge(self):
        """接收文章全文（已含 Markdown 格式）→ 写入 knowledge/ → 重建 TF-IDF 索引"""
        import subprocess as sp
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            req_data = json.loads(body)

            articles = req_data.get('articles', [])
            if not articles:
                self._error(400, '缺少 articles 字段')
                return

            project_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_dir = os.path.join(project_dir, 'rag-backend', 'knowledge')
            os.makedirs(knowledge_dir, exist_ok=True)

            written_files = []
            for a in articles:
                title = (a.get('title') or '无标题').strip()
                content = (a.get('content') or '').strip()
                if not content:
                    continue

                # 文件名：自动导入文章-{标题}.md（过滤非法字符）
                safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '：')
                filename = f'自动导入文章-{safe_title}.md'
                filepath = os.path.join(knowledge_dir, filename)

                # 组装 Markdown（内容已由前端转为 Markdown 格式）
                md_content = content
                if a.get('url'):
                    md_content += f'\n\n> 原文链接：{a["url"]}'
                if a.get('tags') and len(a.get('tags', [])) > 0:
                    md_content += f'\n> 标签：{"、".join(a["tags"])}'

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                written_files.append(filename)
                print(f'   📄 知识库写入: {filename} ({len(content)} 字)')

            if not written_files:
                self._error(400, '没有有效文章内容可写入')
                return

            if not written_files:
                self._error(400, '没有有效文章内容可写入')
                return

            # 重建 TF-IDF 索引
            print(f'   🔄 重建索引中...')
            ingest_py = os.path.join(project_dir, 'rag-backend', 'ingest.py')
            result = sp.run(
                ['python3', ingest_py],
                capture_output=True, text=True, timeout=60,
                cwd=os.path.join(project_dir, 'rag-backend')
            )
            if result.returncode != 0:
                print(f'   ⚠️ 索引重建失败: {result.stderr[:300]}')
                # 不阻断部署流程，文件已写入
            else:
                print(f'   ✅ 索引重建完成')

            # 通知 RAG 后端热重载索引
            reload_output = ''
            try:
                reload_req = urllib.request.Request(
                    'http://localhost:8000/reload-index',
                    data=b'{}',
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(reload_req, timeout=10) as resp:
                    reload_data = json.loads(resp.read())
                    reload_output = f', 热重载: {reload_data.get("chunks_before", "?")} → {reload_data.get("chunks_after", "?")} 切片'
                    print(f'   {reload_output}')
            except Exception as reload_err:
                reload_output = f', 热重载失败（后端可能未启动）: {reload_err}'
                print(f'   ⚠️ {reload_output}')

            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'ok': True,
                'files': written_files,
                'count': len(written_files),
                'index_output': (result.stdout + result.stderr).strip()[-500:] + reload_output
            }).encode('utf-8'))

        except Exception as e:
            self._error(500, str(e))

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _error(self, code, msg):
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        err = json.dumps({'error': msg}).encode('utf-8')
        self.wfile.write(err)

    def log_message(self, format, *args):
        print(f'[proxy] {args[0]}')

if __name__ == '__main__':
    print(f'代理已启动 → http://localhost:{PROXY_PORT}/analyze')
    print('管理工具会通过此代理调用 DeepSeek API')
    print('按 Ctrl+C 停止\n')
    http.server.HTTPServer(('', PROXY_PORT), ProxyHandler).serve_forever()
