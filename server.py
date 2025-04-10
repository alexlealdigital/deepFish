import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Configuração do CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ]
    }
})

# Configuração do banco de dados
DATABASE = '/var/lib/render/project/src/jogadas.db'  # Path persistente no Render

def get_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Garante que existe exatamente um registro
    db.execute("""
        INSERT OR IGNORE INTO contador (id, valor) 
        VALUES (1, 0)
    """)
    return db

def load_counter():
    try:
        db = get_db()
        valor = db.execute("SELECT valor FROM contador WHERE id = 1").fetchone()[0]
        db.close()
        return valor
    except Exception as e:
        print(f"Erro ao ler contador: {e}")
        return 0

def save_counter(value):
    try:
        db = get_db()
        db.execute("UPDATE contador SET valor = ? WHERE id = 1", (value,))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Erro ao salvar contador: {e}")

# Carrega o valor inicial
jogadas = load_counter()

@app.route('/')
def home():
    return jsonify({"status": "online", "jogadas": jogadas})

@app.route('/incrementar_jogadas', methods=['POST', 'OPTIONS'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    save_counter(jogadas)
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET', 'OPTIONS'])
def obter_jogadas():
    global jogadas
    return jsonify({"jogadas": jogadas})

if __name__ == '__main__':
    # Garante que o diretório do banco de dados existe
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    app.run(host='0.0.0.0', port=10000)
