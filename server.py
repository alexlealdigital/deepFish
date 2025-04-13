import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify
import os

# 1. Inicialização do Flask
app = Flask(__name__)

# 2. Configuração do Firebase
def init_firebase():
    try:
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
            'databaseURL': os.getenv("FIREBASE_DB_URL")  # Ex: "https://SEU_PROJETO.firebaseio.com"
        })
        
        print("🔥 Firebase inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {str(e)}")
        raise

# 3. Rotas
@app.route('/incrementar', methods=['POST'])
def incrementar():
    try:
        ref = db.reference('contador')
        novo_valor = ref.transaction(lambda current: (current or 200) + 1)
        return jsonify({
            "status": "success",
            "jogadas": novo_valor,
            "message": "Incrementado via Firebase"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    try:
        ref = db.reference('contador')
        valor = ref.get() or 200
        return jsonify({
            "status": "online",
            "jogadas": valor,
            "db": "Firebase Realtime"
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# 4. Inicialização
if __name__ == '__main__':
    init_firebase()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
