from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import os
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "cambia_esta_clave_por_algo_tuyo"

DATABASE = "tienda.db"

# Configuracion Cloudinary
cloudinary.config(
    cloud_name="dbyqlyzkn",
    api_key="323887487553112",
    api_secret=os.environ.get("CLOUDINARY_SECRET")
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            imagen TEXT,
            descripcion TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT")
        conn.commit()
    except:
        pass
    conn.commit()
    conn.close()


init_db()


# 🏠 TIENDA VISUAL
@app.route("/")
def home():
    conn = get_db()
    productos = conn.execute("SELECT * FROM productos ORDER BY id DESC").fetchall()
    conn.close()
    carrito_count = len(session.get("carrito", []))
    return render_template("index.html", productos=productos, carrito_count=carrito_count)


# ➕ CREAR PRODUCTO
@app.route("/crear", methods=["POST"])
def crear():
    nombre = request.form.get("nombre", "").strip()
    precio = request.form.get("precio", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    imagen = request.files.get("imagen")
    imagen_url = None

    if imagen and imagen.filename and allowed_file(imagen.filename):
        resultado = cloudinary.uploader.upload(imagen)
        imagen_url = resultado["secure_url"]

    conn = get_db()
    conn.execute(
        "INSERT INTO productos (nombre, precio, imagen, descripcion) VALUES (?, ?, ?, ?)",
        (nombre, float(precio), imagen_url, descripcion)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# ❌ ELIMINAR PRODUCTO
@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


# 🔍 DETALLE DEL PRODUCTO
@app.route("/producto/<int:id>")
def detalle_producto(id):
    conn = get_db()
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (id,)).fetchone()
    conn.close()
    carrito_count = len(session.get("carrito", []))
    return render_template("detalle.html", producto=producto, carrito_count=carrito_count)


# =========================
# 🛒 CARRITO DE COMPRAS
# =========================

@app.route("/agregar_carrito/<int:id>")
def agregar_carrito(id):
    carrito = session.get("carrito", [])
    carrito.append(id)
    session["carrito"] = carrito
    session.modified = True
    return redirect(url_for("home"))


@app.route("/carrito")
def ver_carrito():
    carrito_ids = session.get("carrito", [])
    conn = get_db()
    productos = []
    total = 0.0
    for pid in carrito_ids:
        p = conn.execute("SELECT * FROM productos WHERE id = ?", (pid,)).fetchone()
        if p:
            productos.append(p)
            total += float(p["precio"])
    conn.close()
    return render_template("carrito.html", productos=productos, total=total)


@app.route("/quitar_carrito/<int:id>")
def quitar_carrito(id):
    carrito = session.get("carrito", [])
    if id in carrito:
        carrito.remove(id)
    session["carrito"] = carrito
    session.modified = True
    return redirect(url_for("ver_carrito"))


@app.route("/vaciar_carrito")
def vaciar_carrito():
    session["carrito"] = []
    session.modified = True
    return redirect(url_for("ver_carrito"))


# 🧩 API JSON
@app.route("/items", methods=["GET"])
def get_items():
    conn = get_db()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return jsonify([dict(p) for p in productos])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
