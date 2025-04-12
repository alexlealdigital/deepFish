import os
import sqlite3
from threading import Lock
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Configuração do CORS (básica)
CORS(app)

# Configuração do banco de dados SQLite
DATABASE = os.path.join(os.getcwd(), 'jogadas.db')
counter_lock = Lock()

def init_db():
    """Inicializa o banco de dados do contador"""
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 0)")
    conn.commit()
    conn.close()

def get_count():
    """Obtém o valor atual do contador"""
    with counter_lock:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador WHERE id = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count

def increment_count():
    """Incrementa e retorna o novo valor"""
    with counter_lock:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
        cursor.execute("SELECT valor FROM contador WHERE id = 1")
        new_count = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return new_count

# Inicializa o banco de dados
init_db()

# Rotas da API
@app.route("/")
def home():
    return jsonify({"status": "online", "jogadas": get_count()})

@app.route("/incrementar_jogadas", methods=["POST"])
def incrementar_jogadas():
    return jsonify({"jogadas": increment_count()})

@app.route("/obter_jogadas", methods=["GET"])
def obter_jogadas():
    return jsonify({"jogadas": get_count()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
