from flask import Flask, jsonify

app = Flask(__name__)

# Variável global para armazenar as jogadas
jogadas = 0

@app.route('/incrementar_jogadas', methods=['POST'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET'])
def obter_jogadas():
    global jogadas
    return jsonify({"jogadas": jogadas})

# Adicione esta linha para o Gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
