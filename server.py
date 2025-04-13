import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify
import os
import logging

# Configuração inicial
app = Flask(__name__)
app.logger.setLevel(logging.INFO)  # Habilita logs

# Variáveis críticas (valide no Render.com)
FIREBASE_CREDENTIALS = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT")
}

# Inicialização do Firebase (executada uma vez)
def init_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv("FIREBASE_DB_URL")
            })
            app.logger.info("✅ Firebase inicializado")
            return True
        except Exception as e:
            app.logger.error(f"🔥 ERRO Firebase: {str(e)}")
            return False
    return True

# Rotas
@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bem-vindo ao DeepFish!"})

@app.route('/incrementar', methods=['POST'])
def incrementar():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        ref = db.reference('contador')
        novo_valor = ref.transaction(lambda current: (current or 200) + 1)
        app.logger.info(f"➡️ Incrementado: {novo_valor}")
        return jsonify({"status": "success", "jogadas": novo_valor})
    except Exception as e:
        app.logger.error(f"🚨 Erro ao incrementar: {str(e)}")
        return jsonify({"status": "error"}), 500

@app.route('/status', methods=['GET'])
def get_status():
    try:
        # Conexão direta com o Firebase
        ref = db.reference('contador')
        current_value = ref.get() or 200  # Valor padrão se não existir
        return jsonify({
            "jogadas": current_value,
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Inicialização
if __name__ == '__main__':
    if init_firebase():
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:
        app.logger.critical("❌ Servidor não iniciado: Firebase falhou")
