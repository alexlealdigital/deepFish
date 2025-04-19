import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
import os
import logging

# ================= CONFIGURAÇÃO INICIAL =================
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Credenciais do Firebase (Mantenha suas configurações)
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

# ================= INICIALIZAÇÃO FIREBASE =================
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

# ================= ROTAS CONTADOR (Mantenha suas rotas) =================
@app.route('/incrementar', methods=['POST'])
def incrementar():
    # ... (seu código) ...

@app.route('/status', methods=['GET'])
def get_status():
    # ... (seu código) ...

# ================= ROTAS RANKING (MODIFICADO PARA LISTA) =================
@app.route('/ranking.json', methods=['GET'])
def get_ranking_direct_list():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        ref = db.reference('ranking')
        top_scores_dict = ref.order_by_child('score').limit_to_last(3).get() or {}
        # Converter o dicionário para uma lista de objetos
        top_scores_list = []
        for key, value in top_scores_dict.items():
            top_scores_list.append({"name": value.get("name"), "score": value.get("score")})
        # Inverter a lista para ter os maiores scores primeiro
        top_scores_list.reverse()
        return jsonify(top_scores_list)
    except Exception as e:
        app.logger.error(f"🔥 Erro ao buscar ranking: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ranking', methods=['POST'])
def add_to_ranking():
    # ... (seu código) ...

# ================= ROTAS AUXILIARES (Mantenha suas rotas) =================
@app.route('/')
def home():
    # ... (seu código) ...

@app.route('/health', methods=['GET'])
def health_check():
    # ... (seu código) ...

# ================= INICIALIZAÇÃO =================
if __name__ == '__main__':
    if init_firebase():
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:
        app.logger.critical("❌ Servidor não iniciado: Firebase falhou")
