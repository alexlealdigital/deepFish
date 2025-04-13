import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify
import os
from datetime import datetime

def init_firebase():
    try:
        # 1. Verifica se já está inicializado
        if firebase_admin._apps:
            return True
            
        # 2. Validação EXTRA das variáveis
        required_vars = [
            'FIREBASE_TYPE', 'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL', 'FIREBASE_DB_URL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Variáveis faltando: {missing_vars}")

        # 3. Configuração robusta
        cred = credentials.Certificate({
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT")
        })

        # 4. Inicialização com tratamento de URL
        firebase_url = os.getenv("FIREBASE_DB_URL").strip()
        if not firebase_url.startswith('https://'):
            firebase_url = f"https://{firebase_url}"
            
        firebase_admin.initialize_app(cred, {
            'databaseURL': firebase_url,
            'projectId': os.getenv("FIREBASE_PROJECT_ID")
        })
        
        print("🔥 Firebase inicializado! URL:", firebase_url)
        return True
        
    except Exception as e:
        print("❌ ERRO FATAL no Firebase:", str(e))
        return False

# 3. Rotas Essenciais
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "DeepFish Counter",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/incrementar (POST)", "/status (GET)"]
    })

@app.route('/incrementar', methods=['POST'])
def incrementar():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase não inicializado"}), 500
    
    try:
        ref = db.reference('contador')
        novo_valor = ref.transaction(lambda current: (current or 200) + 1)
        return jsonify({
            "status": "success",
            "jogadas": novo_valor,
            "server": "firebase"
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    if not init_firebase():
        return jsonify({"status": "offline"}), 500
    
    try:
        valor = db.reference('contador').get() or 200
        return jsonify({
            "status": "online",
            "jogadas": valor,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/debug_firebase')
def debug_firebase():
    try:
        ref = db.reference('contador')
        ref.set(200)  # Reseta para teste
        valor = ref.get()
        return jsonify({
            "success": True,
            "firebase_value": valor,
            "env_keys": list(os.environ.keys())  # Mostra variáveis carregadas
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expected_db_url": os.getenv("FIREBASE_DB_URL")
        }), 500

# 4. Inicialização
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
