import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
import os
import logging

# ================= CONFIGURAÇÃO INICIAL =================
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Credenciais do Firebase (Render Environment Variables)
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

# ================= FIREBASE INIT =================
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

# ================= ROTAS CONTADOR DE JOGADAS =================
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
        if not init_firebase():
            return jsonify({"status": "error", "message": "Firebase offline"}), 500
        ref = db.reference('contador')
        current_value = ref.get() or 200
        return jsonify({"jogadas": current_value, "status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ================= ROTAS RANKING =================
@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        ref = db.reference('ranking')
        scores = ref.order_by_child('score').limit_to_last(3).get() or {}
        ranked_players = []
        for key, data in scores.items():
            ranked_players.append({"playerName": data.get('name', 'Anônimo'), "score": data['score']})
        ranked = sorted(ranked_players, key=lambda x: x['score'], reverse=True)
        return jsonify({"topPlayers": ranked})
    except Exception as e:
        app.logger.error(f"🔥 Erro ao buscar ranking: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ranking', methods=['POST'])
def add_to_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        # Força o parsing como JSON independente do Content-Type
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 415
            
        data = request.get_json(force=True)  # force=True para casos onde o header pode estar mal configurado
        app.logger.info(f"Dados brutos recebidos: {request.data}")
        app.logger.info(f"Dados parseados: {data}")

        if not data:
            return jsonify({"error": "Corpo da requisição vazio ou inválido"}), 400

        name = data.get('name')
        score = data.get('score')

        # Restante da lógica permanece igual...
# ================= ROTAS AUXILIARES =================
@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Bem-vindo ao DeepFish!"})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# ================= INICIALIZAÇÃO =================
if __name__ == '__main__':
    if init_firebase():
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:
        app.logger.critical("❌ Servidor não iniciado: Firebase falhou")
