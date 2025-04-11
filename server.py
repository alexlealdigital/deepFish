import os
import sqlite3
import json
from threading import Lock
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime


try:
    import requests
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Execute: pip install -r requirements.txt")
    exit(1)

app = Flask(__name__, static_folder='../frontend/build')

# Configuração do CORS
CORS(app, resources={
    r"/*": {
        "origins": ["https://deepfishgame.netlify.app", "https://*.netlify.app", "http://localhost:*"],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

# Configurações de caminho
DATA_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE = os.path.join(DATA_DIR, 'jogadas.db')
BACKUP_FILE = os.path.join(DATA_DIR, 'jogadas_backup.json')

# Lock para operações thread-safe
db_lock = Lock()

# Inicialização do banco de dados SQLite
def init_db():
    with db_lock:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jogadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quantidade INTEGER NOT NULL,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

# Inicialização do Firebase
def init_firebase():
    firebase_key_json = os.environ.get("FIREBASE_KEY")
    if not firebase_key_json:
        raise ValueError("Variável FIREBASE_KEY não encontrada")
    
    cred_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://adsdados-default-rtdb.firebaseio.com/"
    })

# Rotas da API
@app.route('/obter_jogadas', methods=['GET'])
def obter_jogadas():
    try:
        with db_lock:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(quantidade) FROM jogadas')
            total = cursor.fetchone()[0] or 0
            conn.close()
            
            return jsonify({
                'status': 'sucesso',
                'total_jogadas': total,
                'timestamp': datetime.now().isoformat()
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500

@app.route('/incrementar_jogadas', methods=['POST'])
def incrementar_jogadas():
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 1)
        
        with db_lock:
            # Salva no SQLite
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO jogadas (quantidade) VALUES (?)', (quantidade,))
            conn.commit()
            conn.close()
            
            # Salva no Firebase (opcional)
            if firebase_admin._apps:
                ref = db.reference('jogadas')
                ref.push({
                    'quantidade': quantidade,
                    'timestamp': datetime.now().isoformat()
                })
            
            return jsonify({
                'status': 'sucesso',
                'quantidade_adicionada': quantidade
            }), 200
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def serve_frontend():
    """Rota principal para servir o frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve arquivos estáticos"""
    return send_from_directory(app.static_folder, path)

# ... (rotas anteriores permanecem iguais)

if __name__ == "__main__":
    try:
        init_db()
        init_firebase()
        port = int(os.environ.get("PORT", 10000))
        
        # Configuração para produção
        if os.environ.get('FLASK_ENV') == 'production':
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        else:
            app.run(host="0.0.0.0", port=port, debug=True)
            
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        exit(1)
