from pathlib import Path
import sqlite3
from flask import Flask, jsonify, render_template

DB = Path(__file__).resolve().parent / "data" / "orders.sqlite3"
app = Flask(__name__)

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/orders")
def orders():
    try:
        with connect() as con:
            return jsonify([dict(row) for row in con.execute("SELECT * FROM orders ORDER BY id")])
    except sqlite3.Error:
        return jsonify(error="No se pudieron cargar los pedidos."), 500

SHIP_REJECTIONS = {
    "enviado": "El pedido ya está enviado.",
    "cancelado": "Un pedido cancelado no puede enviarse.",
}

@app.post("/api/orders/<int:order_id>/ship")
def ship(order_id):
    try:
        with connect() as con:
            # The status check lives in the UPDATE itself so it is atomic:
            # only a pending order can ever become shipped.
            shipped = con.execute(
                "UPDATE orders SET status = 'enviado' WHERE id = ? AND status = 'pendiente'",
                (order_id,),
            ).rowcount
            row = con.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return jsonify(error="Pedido no encontrado."), 404
        if not shipped:
            return jsonify(error=SHIP_REJECTIONS[row["status"]]), 409
        return jsonify(dict(row))
    except sqlite3.Error:
        return jsonify(error="No se pudo actualizar el pedido."), 500

if __name__ == "__main__":
    app.run(debug=True)
