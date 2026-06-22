#!/usr/bin/env python3
"""元探案例库本地服务 · 替代 python3 -m http.server

功能:
  - 静态文件服务 (probe/ 根目录)
  - GET /open-file?run_id=<id>  → macOS open 直接打开 docx，零下载
  - GET /open-path?path=<rel>   → 打开任意相对路径文件

用法:
  cd ~/Downloads/metafoclaw/probe
  python3 hub/serve.py           # 默认 7890
  python3 hub/serve.py 8080      # 自定义端口

访问: http://localhost:7890/hub/probe-cases.html
"""
import http.server
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse

PORT    = int(sys.argv[1]) if len(sys.argv) > 1 else 7890
ROOT    = pathlib.Path(__file__).resolve().parent.parent   # probe/
CASES   = ROOT / "data" / "cases"


class ProbeHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── 自定义路由 ────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/open-file":
            run_id = (qs.get("run_id") or [""])[0]
            docx   = CASES / run_id / "report.docx"
            self._open_file(docx)
            return

        if parsed.path == "/open-path":
            rel  = (qs.get("path") or [""])[0]
            path = (ROOT / rel).resolve()
            # 安全检查：只允许 probe/ 目录内的文件
            if ROOT in path.parents:
                self._open_file(path)
            else:
                self._json(403, {"ok": False, "error": "path outside probe root"})
            return

        super().do_GET()

    # ── 工具方法 ─────────────────────────────────────────────────
    def _open_file(self, path: pathlib.Path):
        if not path.exists():
            self._json(404, {"ok": False, "error": f"file not found: {path.name}"})
            return
        # macOS: open 命令 → 用系统默认关联程序直接打开（Word/Pages）
        subprocess.Popen(["open", str(path)])
        self._json(200, {"ok": True, "opened": path.name})

    def _json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")  # 允许 JS fetch
        self.end_headers()
        self.wfile.write(body)

    # 静默日志（只打关键请求）
    def log_message(self, fmt, *args):
        msg = fmt % args
        if any(k in msg for k in ("/open-file", "/open-path", "404", "500")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/hub/probe-cases.html"
    print(f"\n✅  元探案例库服务已启动")
    print(f"   访问: {url}")
    print(f"   Word 直开端点: http://localhost:{PORT}/open-file?run_id=<run_id>")
    print(f"   Ctrl+C 停止\n")
    try:
        with http.server.ThreadingHTTPServer(("", PORT), ProbeHandler) as srv:
            srv.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
