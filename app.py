from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
import secrets

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "orders.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            district TEXT NOT NULL,
            address TEXT NOT NULL,
            postal_code TEXT,
            note TEXT,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Yeni Sipariş',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(BASE_DIR, filename)


@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Geçersiz sipariş."
        }), 400

    required = [
        "first_name",
        "last_name",
        "phone",
        "city",
        "district",
        "address",
        "items",
        "total"
    ]

    for field in required:

        if not data.get(field):

            return jsonify({
                "success": False,
                "message": "Eksik bilgi: " + field
            }), 400


    order_number = (
        "VS-" +
        str(datetime.now().year) +
        "-" +
        secrets.token_hex(3).upper()
    )


    conn = get_db()

    conn.execute("""
        INSERT INTO orders (
            order_number,
            first_name,
            last_name,
            phone,
            city,
            district,
            address,
            postal_code,
            note,
            items,
            total,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        order_number,

        data["first_name"],
        data["last_name"],
        data["phone"],

        data["city"],
        data["district"],
        data["address"],

        data.get("postal_code", ""),

        data.get("note", ""),

        str(data["items"]),

        float(data["total"]),

        "Yeni Sipariş",

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))


    conn.commit()
    conn.close()


    return jsonify({
        "success": True,
        "order_number": order_number
    })


@app.route("/api/orders", methods=["GET"])
def get_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(order)
        for order in orders
    ])


@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def change_status(order_id):

    data = request.get_json()

    status = data.get("status")


    allowed_statuses = [
        "Yeni Sipariş",
        "Hazırlanıyor",
        "Kargoya Verildi",
        "Teslim Edildi",
        "İptal Edildi"
    ]


    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Geçersiz sipariş durumu."
        }), 400


    conn = get_db()

    conn.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (
        status,
        order_id
    ))

    conn.commit()
    conn.close()


    return jsonify({
        "success": True
    })


if __name__ == "__main__":

    init_db()

    print()
    print("====================================")
    print("       VOLSTRA ORDER SYSTEM")
    print("====================================")
    print("Site : http://127.0.0.1:5000")
    print("Admin: http://127.0.0.1:5000/admin.html")
    print("====================================")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )