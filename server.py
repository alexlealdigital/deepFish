import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Configuração do CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ]
    }
})

# Arquivo para persistência (na pasta do servidor)
COUNTER_FILE = "jogadas_counter.txt"

def load_counter():
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"Erro ao ler contador: {e}")
    return 0  # Valor padrão se o arquivo não existir

def save_counter(value):
    try:
        with open(COUNTER_FILE, 'w') as f:
            f.write(str(value))
    except Exception as e:
        print(f"Erro ao salvar contador: {e}")

# Carrega o valor inicial
jogadas = load_counter()

@app.route('/')
def home():
    return jsonify({"status": "online", "jogadas": jogadas})

@app.route('/incrementar_jogadas', methods=['POST', 'OPTIONS'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    save_counter(jogadas)  # Salva o novo valor
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET', 'OPTIONS'])
def obter_jogadas():
    global jogadas
    return jsonify({"jogadas": jogadas})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
