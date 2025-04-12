import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# Configuração básica do Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração do Firebase
cred = credentials.Certificate(json.loads(os.environ['FIREBASE_KEY']))
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://adsdados-default-rtdb.firebaseio.com/'
})

# Configuração do SQLite
def get_db():
    conn = sqlite3.connect('jogadas.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializa o banco de dados
def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS jogadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quantidade INTEGER DEFAULT 1,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Rotas otimizadas
@app.route('/obter_jogadas', methods=['GET'])
def obter_jogadas():
    try:
        # Obtém do SQLite
        with get_db() as conn:
            total = conn.execute('SELECT SUM(quantidade) FROM jogadas').fetchone()[0] or 0
        
        # Obtém do Firebase (backup)
        firebase_total = db.reference('jogadas_total').get() or 0
        
        return jsonify({
            'status': 'sucesso',
            'sqlite_total': total,
            'firebase_total': firebase_total,
            'total_geral': total + firebase_total
        })
    
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/incrementar_jogadas', methods=['POST'])
def incrementar_jogadas():
    try:
        quantidade = request.json.get('quantidade', 1)
        
        # Salva no SQLite
        with get_db() as conn:
            conn.execute('INSERT INTO jogadas (quantidade) VALUES (?)', (quantidade,))
            conn.commit()
        
        # Atualiza no Firebase
        ref = db.reference('jogadas_total')
        ref.set((ref.get() or 0) + quantidade)
        
        return jsonify({
            'status': 'sucesso',
            'quantidade': quantidade,
            'mensagem': 'Jogada registrada em ambos os bancos'
        })
    
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'endpoints': {
            'GET /obter_jogadas': 'Retorna o total de jogadas',
            'POST /incrementar_jogadas': 'Registra nova jogada'
        }
    })

# Inicialização segura
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
