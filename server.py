import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
import os
import logging

# ================= CONFIGURAÇÃO INICIAL =================
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

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

# ================= ROTAS CONTADOR (mantidas originais) =================
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

# ================= ROTAS RANKING (ajustadas para sua estrutura) =================
@app.route('/api/ranking', methods=['GET'])
def get_ranking():
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

@app.route('/api/ranking', methods=['POST'])
def add_to_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500

    try:
        # Verifica explicitamente o Content-Type
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 415
            
        # Força o parsing mesmo se o header estiver mal formatado
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "Dados JSON inválidos ou mal formatados"}), 400

        app.logger.info(f"Dados recebidos: {data}")  # Log para debug

        name = data.get('name', '').strip()
        try:
            score = int(data.get('score', 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Pontuação deve ser um número inteiro"}), 400

        if not name:
            return jsonify({"error": "Nome é obrigatório"}), 400

        ref = db.reference('ranking')
        top_scores = ref.order_by_child('score').limit_to_last(3).get() or {}
        min_score = min([v['score'] for v in top_scores.values()]) if top_scores else 0

        if len(top_scores) < 3 or score > min_score:
            new_entry = ref.push({"name": name, "score": score})
            return jsonify({
                "success": True,
                "message": "Ranking atualizado!",
                "position": "Top 3" if len(top_scores) < 3 else f"Posição {len(top_scores)}"
            })

        return jsonify({
            "success": False,
            "message": f"Pontuação mínima para o Top 3: {min_score + 1}",
            "currentTop3": [
                {"name": v['name'], "score": v['score']} 
                for v in top_scores.values()
            ]
        })

    except Exception as e:
        app.logger.error(f"ERRO CRÍTICO: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
        
# ================= ROTAS AUXILIARES (mantidas originais) =================
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
