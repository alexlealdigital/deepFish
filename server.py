import os
from dotenv import load_dotenv
import sqlite3
import requests
from threading import Thread
from flask import Flask, jsonify, request
from flask_cors import CORS

# Carrega variáveis de ambiente
load_dotenv()  # Para desenvolvimento local

app = Flask(__name__)

# Configuração robusta de CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configurações persistentes
DATABASE = '/var/lib/render/project/src/jogadas.db'  # Caminho persistente no Render
BACKUP_FILE = '/var/lib/render/project/src/jogadas_backup.json'

def get_db():
    """Conexão segura com o banco de dados SQLite"""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA journal_mode=WAL")  # Melhora concorrência
    db.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0,
            ultima_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 0)")
    return db

def load_counter():
    """Carrega o contador com fallback hierárquico"""
    try:
        # 1. Tenta SQLite primeiro
        db = get_db()
        valor = db.execute("SELECT valor FROM contador WHERE id = 1").fetchone()[0]
        db.close()
        
        # 2. Atualiza ambiente e backup
        os.environ['CONTADOR_JOGADAS'] = str(valor)
        with open(BACKUP_FILE, 'w') as f:
            json.dump({'jogadas': valor}, f)
            
        return valor
        
    except Exception as e:
        print(f"Erro SQLite, tentando fallback: {e}")
        
        try:
            # 3. Fallback para arquivo local
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE) as f:
                    return int(json.load(f)['jogadas'])
        except:
            # 4. Fallback final para variável de ambiente
            return int(os.getenv('CONTADOR_JOGADAS', '0'))

def save_counter(value):
    """Salva o contador em múltiplas camadas"""
    try:
        # 1. SQLite (camada principal)
        db = get_db()
        db.execute("UPDATE contador SET valor = ? WHERE id = 1", (value,))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Erro no SQLite: {e}")
    
    # 2. Variável de ambiente (sempre atualiza)
    os.environ['CONTADOR_JOGADAS'] = str(value)
    
    # 3. Backup local (sincrono)
    try:
        with open(BACKUP_FILE, 'w') as f:
            json.dump({'jogadas': value}, f)
    except Exception as e:
        print(f"Erro no backup local: {e}")

def async_backup(value):
    """Backup assíncrono para serviços externos"""
    try:
        if url := os.getenv('BACKUP_WEBHOOK'):
            requests.post(url, json={
                'jogadas': value,
                'service': 'deepfish'
            }, timeout=5)
    except:
        pass  # Falha não crítica

# Inicialização segura
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
jogadas = load_counter()

# Endpoints
@app.route('/')
def health_check():
    return jsonify({
        "status": "online",
        "jogadas": jogadas,
        "persistencia": "SQLite + Env Vars + Backup File"
    })

@app.route('/incrementar_jogadas', methods=['POST', 'OPTIONS'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    save_counter(jogadas)
    Thread(target=async_backup, args=(jogadas,)).start()
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET', 'OPTIONS'])
def obter_jogadas():
    return jsonify({"jogadas": jogadas})

@app.route('/debug', methods=['GET'])
def debug():
    db_val = sqlite3.connect(DATABASE).execute("SELECT valor FROM contador WHERE id = 1").fetchone()[0]
    return jsonify({
        "memoria": jogadas,
        "sqlite": db_val,
        "ambiente": os.getenv('CONTADOR_JOGADAS'),
        "backup_file": json.load(open(BACKUP_FILE)) if os.path.exists(BACKUP_FILE) else None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=True)
