import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify
import os

# 1. Cria a instância do Flask PRIMEIRO
app = Flask(__name__)

# 2. Configuração do Firebase
def init_firebase():
    try:
        if firebase_admin._apps:
            return True  # Já inicializado
            
        # Valida variáveis críticas
        required_env_vars = [
            'FIREBASE_DB_URL', 
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY'
        ]
        
        missing = [var for var in required_env_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Variáveis faltando: {missing}")

        # Configura credenciais
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

        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv("FIREBASE_DB_URL")
        })
        return True
        
    except Exception as e:
        app.logger.error(f"🔥 ERRO Firebase: {str(e)}")
        return False

# 3. Rotas (só depois de criar o 'app')
@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bem-vindo ao DeepFish!"})

@app.route('/incrementar', methods=['POST'])
def incrementar():
    if not init_firebase():
        return jsonify({"status": "error"}), 500
        
    try:
        ref = db.reference('contador')
        novo_valor = ref.transaction(lambda current: (current or 200) + 1)
        return jsonify({"status": "success", "jogadas": novo_valor})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# 4. Inicialização segura
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
