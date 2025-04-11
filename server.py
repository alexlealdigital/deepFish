import os
import sqlite3
import json
from threading import Thread
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configuração inicial
app = Flask(__name__)

# Correção para compatibilidade
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

# Configuração do CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

# Configuração do banco de dados
DATABASE = os.path.join(os.getcwd(), 'data', 'jogadas.db')
BACKUP_FILE = os.path.join(os.getcwd(), 'data', 'jogadas_backup.json')

# Garante que o diretório existe
os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)

def get_db():
    """Conexão segura com o banco de dados"""
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 0)")
    return db

def load_counter():
    """Carrega o valor do contador"""
    try:
        db = get_db()
        valor = db.execute("SELECT valor FROM contador WHERE id = 1").fetchone()[0]
        db.close()
        return valor
    except Exception as e:
        print(f"Erro ao carregar contador: {e}")
        return 0

def save_counter(value):
    """Salva o valor do contador"""
    try:
        db = get_db()
        db.execute("UPDATE contador SET valor = ? WHERE id = 1", (value,))
        db.commit()
        db.close()
        # Backup adicional
        with open(BACKUP_FILE, 'w') as f:
            json.dump({'jogadas': value}, f)
    except Exception as e:
        print(f"Erro ao salvar contador: {e}")

# Inicializa o contador
jogadas = load_counter()

# Rotas
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "jogadas": jogadas,
        "mensagem": "Servidor do DeepFish funcionando"
    })

@app.route('/incrementar_jogadas', methods=['POST', 'OPTIONS'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    save_counter(jogadas)
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET', 'OPTIONS'])
def obter_jogadas():
    return jsonify({"jogadas": jogadas})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
