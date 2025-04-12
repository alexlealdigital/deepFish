from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS de forma simples

# Configuração do banco de dados
DATABASE = 'jogadas.db'

def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quantidade INTEGER DEFAULT 1,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/obter_jogadas', methods=['GET'])
def obter_jogadas():
    """Retorna o total acumulado de jogadas"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(quantidade) FROM jogadas')
    total = cursor.fetchone()[0] or 0
    conn.close()
    
    return jsonify({
        'status': 'sucesso',
        'total_jogadas': total
    })

@app.route('/incrementar_jogadas', methods=['POST'])
def incrementar_jogadas():
    """Registra uma nova jogada"""
    quantidade = request.json.get('quantidade', 1)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO jogadas (quantidade) VALUES (?)', (quantidade,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'status': 'sucesso',
        'mensagem': f'Adicionado {quantidade} jogada(s)'
    })

if __name__ == '__main__':
    init_db()  # Garante que o banco existe
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
