@app.route('/ranking', methods=['GET'])
def get_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500
    try:
        ranking_data = get_current_ranking()
        
        # Formatação para o Unity - mantendo sua lógica original mas adaptando o formato
        formatted_ranking = {
            "topPlayers": [
                {"playerName": entry.get('name', 'Anônimo'), "score": entry['score']}
                for entry in ranking_data
            ]
        }
        
        return jsonify(formatted_ranking)
    except Exception as e:
        app.logger.error(f"🔥 Erro ao obter ranking: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/ranking', methods=['POST'])
def submit_ranking():
    if not init_firebase():
        return jsonify({"status": "error", "message": "Firebase offline"}), 500
    try:
        data = request.get_json()  # Alterado para get_json() para melhor compatibilidade
        name = data.get('name')    # Alterado para 'name' (padrão do Unity)
        score = int(data.get('score', 0))  # Alterado para 'score'

        if name and isinstance(score, int):
            if update_ranking(name, score):
                app.logger.info(f"🏆 Ranking atualizado com: {name} - {score}")
                return jsonify({
                    "status": "success", 
                    "message": "Ranking atualizado",
                    "playerName": name,
                    "score": score
                })
            else:
                app.logger.info(f"🏅 Pontuação não entrou no ranking: {name} - {score}")
                return jsonify({
                    "status": "info", 
                    "message": "Pontuação não é alta o suficiente para o ranking",
                    "minimumScore": min(e['score'] for e in get_current_ranking())
                })
        else:
            return jsonify({
                "status": "error", 
                "message": "Parâmetros 'name' e 'score' são necessários"
            }), 400
    except Exception as e:
        app.logger.error(f"🚨 Erro ao enviar ranking: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
