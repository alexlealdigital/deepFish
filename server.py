import os
from dotenv import load_dotenv
import sqlite3
load_dotenv()  # Para desenvolvimento local
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
        # Tenta SQLite primeiro
        db = get_db()
        valor = db.execute("SELECT valor FROM contador WHERE id = 1").fetchone()[0]
        db.close()
        
        # Atualiza a variável de ambiente para sincronização
        os.environ['CONTADOR_JOGADAS'] = str(valor)
        return valor
    except Exception as e:
        print(f"Erro SQLite, usando fallback: {e}")
        return int(os.getenv('CONTADOR_JOGADAS', '0'))

def save_counter(value):
    try:
        # Salva em SQLite
        db = get_db()
        db.execute("UPDATE contador SET valor = ? WHERE id = 1", (value,))
        db.commit()
        db.close()
        
        # Atualiza variável de ambiente
        os.environ['CONTADOR_JOGADAS'] = str(value)
    except Exception as e:
        print(f"Erro ao salvar no SQLite: {e}")
        os.environ['CONTADOR_JOGADAS'] = str(value)

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

@app.route('/backup_jogadas', methods=['GET'])
def backup_jogadas():
    try:
        with open('jogadas_backup.txt', 'w') as f:
            f.write(str(load_counter()))
        return jsonify({"status": "backup success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Garante que o diretório do banco de dados existe
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    app.run(host='0.0.0.0', port=10000)
