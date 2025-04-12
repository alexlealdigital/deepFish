import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Caminho definitivo para o SQLite no Render
DATABASE = '/opt/render/project/src/jogadas.db'

def init_db():
    """Inicialização à prova de falhas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Criação robusta da tabela
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contador (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                valor INTEGER NOT NULL DEFAULT 200
            )
        """)
        
        # Inserção condicional
        cursor.execute("""
            INSERT OR IGNORE INTO contador (id, valor)
            SELECT 1, 200
            WHERE NOT EXISTS (SELECT 1 FROM contador WHERE id = 1)
        """)
        
        conn.commit()
    except Exception as e:
        print(f"⚠️ ERRO NA INICIALIZAÇÃO: {str(e)}")
    finally:
        conn.close()

def get_count():
    """Consulta com fallback seguro"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador WHERE id = 1")
        return cursor.fetchone()[0]
    except:
        return 200  # Valor padrão garantido
    finally:
        conn.close()

def increment_count():
    """Incremento atômico e seguro"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
        conn.commit()
        return get_count()
    except Exception as e:
        print(f"⚠️ ERRO AO INCREMENTAR: {str(e)}")
        return get_count()  # Fallback
    finally:
        conn.close()

# Rotas otimizadas
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
    return jsonify({
        "status": "success" if new_count > 200 else "warning",
        "jogadas": new_count
    })

# Inicialização
if __name__ == "__main__":
    print(f"🔧 Caminho do banco de dados: {DATABASE}")
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
