import os
from dotenv import load_dotenv
import sqlite3
import json
import requests
from threading import Thread
from flask import Flask, jsonify, request
from flask_cors import CORS

# Correção para compatibilidade do Werkzeug
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

load_dotenv()

app = Flask(__name__)

# Configuração do CORS (mantida igual)
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ]
    }
})

# Novo caminho com permissões garantidas
DATABASE = os.path.join(os.getcwd(), 'jogadas.db')
BACKUP_FILE = os.path.join(os.getcwd(), 'jogadas_backup.json')

def get_db():
    """Conexão segura com o banco de dados SQLite"""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 0)")
    return db

# ... (mantenha as outras funções load_counter, save_counter, etc)

if __name__ == '__main__':
    # Garante que o arquivo de banco de dados pode ser criado
    try:
        if not os.path.exists(DATABASE):
            open(DATABASE, 'w').close()
        app.run(host='0.0.0.0', port=10000)
    except Exception as e:
        print(f"Erro crítico: {e}")
        raise
