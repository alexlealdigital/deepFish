import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
import os
import logging
from flask_cors import CORS # Importe o CORS

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO E LOGGING ---
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# --- CONFIGURAÇÃO COMPLETA DE CORS (APENAS UMA VEZ!) ---
# A melhor forma é usar a extensão Flask-CORS logo após criar a instância do Flask.
# O 'origins=["*"]' é para permitir de qualquer origem. Para produção, é melhor
# especificar 'origins=["https://adorable-snickerdoodle-92c29c.netlify.app"]'
# ou listar todas as origens permitidas.
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"], # Permite todas as origens para /api/
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"], # Garante que Content-Type é permitido
        "supports_credentials": True,
        "max_age": 86400 # Cache preflight requests por 24 horas
    },
    r"/status": {
        "origins": ["*"], # Permite todas as origens para /status
        "methods": ["GET", "OPTIONS"]
    },
    r"/incrementar": {
        "origins": ["*"], # Permite todas as origens para /incrementar
        "methods": ["POST", "OPTIONS"]
    }
})

# --- REMOVA ESSE BLOCO, ELE ESTÁ CAUSANDO DUPLICAÇÃO E SOBREPOSIÇÃO ---
# app = Flask(__name__) # ISSO REINICIALIZA O APP!
# CORS(app, resources={r"/api/*": {"origins": "*"}}) # ISSO REINICIALIZA O CORS!

# --- REMOVA ESTE DECORADOR @app.after_request, o Flask-CORS já faz isso de forma mais robusta ---
# @app.after_request
# def add_cors_headers(response):
#     response.headers.add('Access-Control-Allow-Origin', 'https://adorable-snickerdoodle-92c29c.netlify.app')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
#     return response

# Credenciais do Firebase (mantenha suas configurações originais)
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

# ================= ROTAS CONTADOR =================
@app.route('/incrementar', methods=['POST', 'OPTIONS']) # Adicione OPTIONS para o preflight
def incrementar():
    if request.method == 'OPTIONS':
        # As requisições OPTIONS são tratadas automaticamente pelo Flask-CORS
        # mas ter o método aqui garante que o Flask "reconheça" a rota para OPTIONS.
        return '', 200

    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        ref = db.reference('contador')
        # Garante que 'current' não é None antes de adicionar.
        # Use um valor inicial se 'current' for None.
        novo_valor = ref.transaction(lambda current: (current if current is not None else 200) + 1)
        app.logger.info(f"➡️ Incrementado: {novo_valor}")
        return jsonify({"status": "success", "jogadas": novo_valor})
    except Exception as e:
        app.logger.error(f"🚨 Erro ao incrementar: {str(e)}")
        return jsonify({"status": "error"}), 500

@app.route('/status', methods=['GET', 'OPTIONS']) # Adicione OPTIONS para o preflight
def get_status():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        if not init_firebase():
            return jsonify({"status": "error", "message": "Firebase offline"}), 500
        ref = db.reference('contador')
        current_value = ref.get() or 200
        return jsonify({"jogadas": current_value, "status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ================= ROTAS RANKING =================
@app.route('/api/ranking', methods=['GET', 'POST', 'OPTIONS']) # Adicione OPTIONS para o preflight
def handle_ranking():
    if request.method == 'OPTIONS':
        # As requisições OPTIONS são tratadas automaticamente pelo Flask-CORS
        return '', 200

    if request.method == 'GET':
        if not init_firebase():
            return jsonify({"status": "error", "message": "Firebase offline"}), 500
        try:
            ref = db.reference('ranking')
            scores = ref.order_by_child('score').limit_to_last(3).get() or {}

            # Converter para lista ordenada
            ranked_list = [
                {"playerName": value.get('name', 'Anônimo'), "score": value['score']}
                for key, value in scores.items()
            ]
            ranked_list.sort(key=lambda x: x['score'], reverse=True)

            return jsonify({"topPlayers": ranked_list})
        except Exception as e:
            app.logger.error(f"🔥 Erro ao buscar ranking: {str(e)}")
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        app.logger.info(f"Dados recebidos (POST): {request.data}")
        if not init_firebase():
            return jsonify({"error": "Firebase offline"}), 500

        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            score = int(data.get('score', 0))

            ref = db.reference('ranking')

            # 1. Busca os 3 melhores scores (ordenados por score crescente)
            top_scores = ref.order_by_child('score').limit_to_last(3).get() or {}

            # 2. Se já tem 3 registros, pega o menor score
            min_score = min([v['score'] for v in top_scores.values()]) if len(top_scores) >= 3 else 0

            # 3. Lógica de substituição
            if len(top_scores) < 3 or score > min_score:
                if len(top_scores) >= 3:
                    # Encontra e remove o registro com menor score
                    for key, value in top_scores.items():
                        if value['score'] == min_score:
                            ref.child(key).delete()
                            break

                # Adiciona o novo registro
                new_entry = ref.push({
                    "name": name,
                    "score": score
                })

                return jsonify({
                    "success": True,
                    "message": "Ranking atualizado!",
                    "action": "substituiu" if len(top_scores) >= 3 else "adicionou"
                })

            return jsonify({
                "success": False,
                "message": f"Pontuação muito baixa. Mínimo para Top 3: {min_score + 1}"
            })

        except Exception as e:
            app.logger.error(f"Erro ao adicionar ao ranking: {str(e)}")
            return jsonify({"error": str(e)}), 500

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
