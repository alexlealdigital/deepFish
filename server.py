import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Caminho ABSOLUTO com permissões garantidas
DATABASE = '/tmp/jogadas.db'  # Pasta temporária do Render (sempre escrevível)

def init_db():
    """Garante que a tabela existe com valor inicial 200"""
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contador (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                valor INTEGER NOT NULL DEFAULT 200
            )
        """)
        conn.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 200)")
        conn.commit()
    finally:
        conn.close()

def get_count():
    """Obtém o valor atual ou retorna 200 se falhar"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador WHERE id = 1")
        return cursor.fetchone()[0]
    except:
        return 200
    finally:
        conn.close()

def increment_count():
    """Incrementa e retorna o novo valor"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
        conn.commit()
        return get_count()
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return 200
    finally:
        conn.close()

@app.route("/reset_db", methods=["POST"])
def reset_db():
    """Rota para resetar o contador (opcional)"""
    try:
        os.remove(DATABASE)  # Deleta o arquivo do banco
        init_db()  # Recria com valor 200
        return jsonify({"status": "resetado", "jogadas": 200})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rotas principais
@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "jogadas": get_count(),
        "db_path": DATABASE
    })

@app.route("/incrementar", methods=["POST"])
def incrementar():
    new_count = increment_count()
    status = "success" if new_count > 200 else "warning"
    return jsonify({"jogadas": new_count, "status": status})


# Inicialização
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
