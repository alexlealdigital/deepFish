import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite todas as origens (ajuste depois)

# Caminho ABSOLUTO para o banco de dados (crucial no Render)
DATABASE = '/var/lib/render/jogadas.db'  # Pasta persistente do Render!

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 200  # Valor inicial fixo
        )
    """)
    conn.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 200)")
    conn.commit()
    conn.close()

def get_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM contador WHERE id = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def increment_count():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
    conn.commit()
    new_count = get_count()  # Lê o novo valor
    conn.close()
    return new_count

# Rotas
@app.route("/")
def home():
    return jsonify({"jogadas": get_count()})

@app.route("/incrementar", methods=["POST"])
def incrementar():
    return jsonify({"jogadas": increment_count()})

# Inicialização
if __name__ == "__main__":
    init_db()  # Só executa na primeira vez
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
