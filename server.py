from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Configuração do CORS para permitir seu domínio do Netlify e outros possíveis
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://relaxed-cat-5cf3a5.netlify.app/",
            "https://*.netlify.app",
            "http://localhost:*"  # Para desenvolvimento local
        ]
    }
})

jogadas = 0

@app.route('/')
def home():
    return jsonify({"status": "online"})

@app.route('/incrementar_jogadas', methods=['POST', 'OPTIONS'])
def incrementar_jogadas():
    global jogadas
    jogadas += 1
    return jsonify({"jogadas": jogadas})

@app.route('/obter_jogadas', methods=['GET', 'OPTIONS'])
def obter_jogadas():
    global jogadas
    return jsonify({"jogadas": jogadas})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
