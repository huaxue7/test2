# -*- coding: utf-8 -*-
"""
俄罗斯方块 - Vercel Serverless 入口
Flask 应用，部署到 Vercel 的 Python Serverless Functions
"""

import json
import os
import sys
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# ---- 分数存储（内存） ----
# Vercel 是无服务器环境，没有持久化磁盘。
# 成绩保存在内存中，冷启动后会重置。
# 前端 localStorage 会作为补充存储。
scores = []


def get_top_scores(limit=10):
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]


def add_score(name, score_val, level_val, lines_val):
    scores.append({
        "name": name[:20] or "匿名玩家",
        "score": score_val,
        "level": level_val,
        "lines": lines_val,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    if len(scores) > 200:
        scores.sort(key=lambda x: x["score"], reverse=True)
        scores[:]


# ---- 路由 ----

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/rank", methods=["GET"])
def rank_get():
    return jsonify({"scores": get_top_scores()})


@app.route("/api/rank", methods=["POST"])
def rank_post():
    data = request.get_json(silent=True) or {}
    add_score(
        name=data.get("name", "匿名玩家"),
        score_val=data.get("score", 0),
        level_val=data.get("level", 1),
        lines_val=data.get("lines", 0),
    )
    return jsonify({"status": "ok"})


# Vercel 需要导出 app 变量
# handler 是 Vercel Python Runtime 的约定名称
handler = app
