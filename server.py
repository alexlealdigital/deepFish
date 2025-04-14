import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
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

# Função para obter o ranking atual (mantém apenas os 3 maiores)
def get_current_ranking():
    ref = db.reference('ranking')
    # Ordena por pontuação decrescente e pega os 3 primeiros
    ranking = ref.order_by_child('score').limit_to_last(3).get() or {}
    # Converter para lista e ordenar para garantir a ordem decrescente
    ranked_list = sorted(ranking.values(), key=lambda x: x['score'], reverse=True)
    return ranked_list

# Função para tentar adicionar uma nova pontuação ao ranking
def update_ranking(name, score):
    ranking_ref = db.reference('ranking')
    current_ranking = get_current_ranking()

    if len(current_ranking) < 3:
        ranking_ref.push({'name': name, 'score': score})
        return True
    else:
        lowest_score_entry = min(current_ranking, key=lambda x: x['score'])
        if score > lowest_score_entry['score']:
            # Encontrar a chave do nó a ser removido (se existir)
            ranking_snapshot = db.reference('ranking').order_by_child('score').limit_to_first(1).get()
            if ranking_snapshot:
                key_to_remove = list(ranking_snapshot.keys())[0]
                ranking_ref.child(key_to_remove).delete()
                ranking_ref.push({'name': name, 'score': score})
                return True
        return False

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
        if not init_firebase():
            return jsonify({"status": "error", "message": "Firebase offline"}), 500
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

@app.route('/ranking', methods=['GET'])
def get_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500
    try:
        ranking_data = get_current_ranking()
        return jsonify(ranking_data)
    except Exception as e:
        app.logger.error(f"🔥 Erro ao obter ranking: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/ranking', methods=['POST'])
def submit_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500
    try:
        data = request.form
        name = data.get('nome')
        score = int(data.get('pontuacao'))

        if name and isinstance(score, int):
            if update_ranking(name, score):
                app.logger.info(f"🏆 Ranking atualizado com: {name} - {score}")
                return jsonify({"status": "success", "message": "Ranking atualizado"})
            else:
                app.logger.info(f"🏅 Pontuação não entrou no ranking: {name} - {score}")
                return jsonify({"status": "info", "message": "Pontuação não é alta o suficiente para o ranking"})
        else:
            return jsonify({"status": "error", "message": "Parâmetros 'nome' e 'pontuacao' são necessários"}), 400
    except Exception as e:
        app.logger.error(f"🚨 Erro ao enviar ranking: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Inicialização
if __name__ == '__main__':
    if init_firebase():
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    else:
        app.logger.critical("❌ Servidor não iniciado: Firebase falhou")
