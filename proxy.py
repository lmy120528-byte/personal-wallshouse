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
        """路由：/analyze → DeepSeek，/deploy → 部署文章，/git-pull → 本地同步"""
        if self.path == '/git-pull':
            self._handle_git_pull()
            return

        if self.path == '/deploy':
            self._handle_deploy()
            return

        if self.path == '/read-articles':
            self._handle_read_articles()
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

            # git add
            r1 = sp.run(['git', 'add', 'articles-data.js'],
                       capture_output=True, text=True, timeout=10, cwd=project_dir)
            if r1.returncode != 0:
                self._error(500, 'git add 失败: ' + (r1.stderr or r1.stdout))
                return

            # git commit
            r2 = sp.run(['git', 'commit', '-m', message],
                       capture_output=True, text=True, timeout=10, cwd=project_dir)
            # commit 可能返回 "nothing to commit" 也算正常

            # git push
            r3 = sp.run(['git', 'push', 'origin', 'main'],
                       capture_output=True, text=True, timeout=30, cwd=project_dir)
            if r3.returncode != 0:
                self._error(500, 'git push 失败: ' + (r3.stderr or r3.stdout))
                return

            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'ok': True,
                'output': (r2.stdout + r3.stdout).strip()
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
