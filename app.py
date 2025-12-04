from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "cafe_management.db"

# ===== DB接続用の関数 =====
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # カラム名で取り出せるように
    return conn

# ===== TOPページ =====
@app.route("/")
def index():
    return render_template("index.html")

# ===== 商品登録フォーム =====
@app.route("/items/new", methods=["GET", "POST"])
def add_item():
    conn = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        unit = request.form["unit"]
        category_id = request.form["category_id"]
        alert_threshold = request.form["alert_threshold"]
        note = request.form["note"]

        conn.execute("""
            INSERT INTO items (name, unit, category_id, alert_threshold, note)
            VALUES (?, ?, ?, ?, ?)
        """, (name, unit, category_id, alert_threshold, note))
        conn.commit()
        conn.close()

        return redirect(url_for("item_list"))

    categories = conn.execute("SELECT id, name FROM categories").fetchall()
    conn.close()

    return render_template("add_item.html", categories=categories)

# ===== 商品一覧ページ =====
@app.route("/items")
def item_list():
    conn = get_db_connection()

    # 商品一覧（カテゴリ名つき）
    items = conn.execute("""
        SELECT items.id,
               items.name,
               items.unit,
               categories.name AS category_name,
               items.alert_threshold,
               items.note
        FROM items
        JOIN categories ON items.category_id = categories.id
        ORDER BY items.id ASC
    """).fetchall()

    # 在庫計算（stock_logsのSUM(change)で現在の在庫数を取得）
    stock_dict = {}
    for item in items:
        stock = conn.execute("""
            SELECT IFNULL(SUM(change), 0)
            FROM stock_logs
            WHERE item_id = ?
        """, (item["id"],)).fetchone()[0]
        stock_dict[item["id"]] = stock

    conn.close()
    return render_template("item_list.html", items=items, stock_dict=stock_dict)

# ===== 入出庫登録ページ =====
@app.route("/stock", methods=["GET", "POST"])
def stock():
    conn = get_db_connection()

    if request.method == "POST":
        item_id = request.form["item_id"]
        quantity = int(request.form["quantity"])
        memo = request.form["memo"]
        action = request.form["action"]

        change_value = quantity if action == "in" else -quantity

        conn.execute("""
            INSERT INTO stock_logs (item_id, user_id, change, timestamp, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, 1, change_value, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), memo))

        conn.commit()
        conn.close()

        return redirect(url_for("stock"))

    items = conn.execute("SELECT id, name FROM items").fetchall()
    conn.close()

    return render_template("stock.html", items=items)

# ===== 入出庫一覧ページ =====
@app.route("/stock/list")
def stock_list():
    conn = get_db_connection()
    logs = conn.execute("""
        SELECT sl.id,
               sl.timestamp,
               sl.change,
               sl.memo,
               i.name AS item_name,
               u.username AS user_name
        FROM stock_logs sl
        JOIN items i ON sl.item_id = i.id
        JOIN users u ON sl.user_id = u.id
        ORDER BY sl.timestamp DESC
    """).fetchall()
    conn.close()

    return render_template("stock_list.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
