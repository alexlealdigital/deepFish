import os
import sqlite3
import json
from threading import Lock
from flask import Flask, jsonify, request, send_from_directory  # Adicionei send_from_directory aqui
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

app = Flask(__name__)

# Configuração do CORS - Simplificada para desenvolvimento
CORS(app)

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
        print("⚠️ Firebase não inicializado - Variável FIREBASE_KEY não encontrada")
        return
    
    try:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://adsdados-default-rtdb.firebaseio.com/"
        })
        print("✅ Firebase inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")

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
            
            # Salva no Firebase (se configurado)
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
        'timestamp': datetime.now().isoformat(),
        'database': 'operacional' if os.path.exists(DATABASE) else 'não encontrado',
        'firebase': 'conectado' if firebase_admin._apps else 'não configurado'
    }), 200

# Rota raiz simplificada
@app.route('/')
def home():
    return jsonify({
        'status': 'servidor operacional',
        'api_endpoints': {
            'obter_jogadas': '/obter_jogadas [GET]',
            'incrementar_jogadas': '/incrementar_jogadas [POST]',
            'healthcheck': '/healthcheck [GET]'
        }
    })

if __name__ == "__main__":
    try:
        # Inicializa componentes
        init_db()
        init_firebase()
        
        # Configuração da porta
        port = int(os.environ.get("PORT", 10000))
        
        # Modo de execução
        if os.environ.get('FLASK_ENV') == 'production':
            print(f"🚀 Servidor iniciado em modo produção na porta {port}")
            from waitress import serve
            serve(app, host="0.0.0.0", port=port)
        else:
            print(f"🔧 Servidor iniciado em modo desenvolvimento na porta {port}")
            app.run(host="0.0.0.0", port=port, debug=True)
            
    except Exception as e:
        print(f"❌ Erro fatal na inicialização: {e}")
        exit(1)
