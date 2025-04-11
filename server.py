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

app = Flask(__name__)

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

# ... (restante do seu código atual)

if __name__ == "__main__":
    try:
        init_firebase()
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        exit(1)
