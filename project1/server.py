# -*- coding: utf-8 -*-
"""
俄罗斯方块 - 后端服务器
使用 Python 标准库，无需安装任何依赖！
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ---- 配置 ----
PORT = int(os.environ.get("PORT", 5000))
SCORES_FILE = os.path.join(os.path.dirname(__file__), "scores.json")


def load_scores():
    """读取历史高分记录"""
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_scores(scores):
    """保存高分记录"""
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def get_top_scores(limit=10):
    """获取前 N 条最高分记录"""
    scores = load_scores()
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]


def add_score(name, score, level, lines):
    """添加一条新纪录"""
    scores = load_scores()
    scores.append({
        "name": name[:20] or "匿名玩家",
        "score": score,
        "level": level,
        "lines": lines,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    if len(scores) > 200:
        scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:200]
    save_scores(scores)


# ---- MIME 类型映射 ----
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class GameHandler(BaseHTTPRequestHandler):
    """处理 HTTP 请求"""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # ---- API: 获取排行榜 ----
        if path == "/api/rank":
            top = get_top_scores()
            self._send_json({"scores": top})
            return

        # ---- 静态文件 ----
        if path == "/" or path == "":
            path = "/index.html"

        # 映射到 templates 目录
        file_path = os.path.join(
            os.path.dirname(__file__),
            "templates",
            path.lstrip("/"),
        )

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "File not found")
            return

        ext = os.path.splitext(file_path)[1].lower()
        mime = MIME_TYPES.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except IOError:
            self.send_error(500, "Internal server error")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/rank":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            name = data.get("name", "匿名玩家")
            score = data.get("score", 0)
            level = data.get("level", 1)
            lines = data.get("lines", 0)
            add_score(name, score, level, lines)
            self._send_json({"status": "ok"})
            return

        self.send_error(404, "Not found")

    def _send_json(self, data):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        """自定义日志输出"""
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]} {args[2]}\n")


def main():
    server = HTTPServer(("127.0.0.1", PORT), GameHandler)
    print("=" * 50)
    print("  🎮 俄罗斯方块游戏已启动！")
    print(f"  🌐 打开浏览器访问: http://127.0.0.1:{PORT}")
    print("  ⌨  Ctrl+C 停止服务器")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        server.server_close()


if __name__ == "__main__":
    main()
