import os
import sqlite3
import json
import requests
from threading import Thread, Lock
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# Configuração inicial
app = Flask(__name__)

# Correção para compatibilidade
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

# Configuração do CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://deepfishgame.netlify.app",
            "https://*.netlify.app",
            "http://localhost:*"
        ],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

# ======================================
# SEÇÃO 1: CONFIGURAÇÃO DO CONTADOR DE JOGADAS
# ======================================

# Configuração persistente no Render
DATABASE = os.path.join(os.getcwd(), 'data', 'jogadas.db')
BACKUP_FILE = os.path.join(os.getcwd(), 'data', 'jogadas_backup.json')
counter_lock = Lock()

# Garante que o diretório existe
os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)

def init_counter_db():
    """Inicializa o banco de dados do contador com valor do environment"""
    initial_value = int(os.environ.get('jogadas', 0))
    
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor INTEGER NOT NULL DEFAULT ?,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """, (initial_value,))
    
    conn.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, ?)", (initial_value,))
    conn.commit()
    conn.close()

def get_count():
    """Obtém o valor atual do contador"""
    with counter_lock:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT valor FROM contador WHERE id = 1")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"Erro ao ler contador: {e}")
            return int(os.environ.get('jogadas', 0))
        finally:
            conn.close()

def increment_count():
    """Incrementa e retorna o novo valor"""
    with counter_lock:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
            cursor.execute("SELECT valor FROM contador WHERE id = 1")
            new_value = cursor.fetchone()[0]
            conn.commit()
            
            # Atualiza backup
            with open(BACKUP_FILE, 'w') as f:
                json.dump({'jogadas': new_value}, f)
                
            return new_value
        except Exception as e:
            print(f"Erro ao incrementar contador: {e}")
            return int(os.environ.get('jogadas', 0))
        finally:
            conn.close()

# ======================================
# SEÇÃO 2: CONFIGURAÇÃO DO FIREBASE (ANÚNCIOS)
# ======================================

FIREBASE_CODES_URL = "https://adsdados-default-rtdb.firebaseio.com/codes.json"
IMGUR_CLIENT_ID = "8823fb7cd2338d3"
IMGUR_UPLOAD_URL = "https://api.imgur.com/3/upload"

# Configuração do Firebase
firebase_key_json = os.environ.get("FIREBASE_KEY")
if firebase_key_json:
    cred_dict = json.loads(firebase_key_json)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://adsdados-default-rtdb.firebaseio.com/"
    })
else:
    print("❌ ERRO: Variável FIREBASE_KEY não encontrada.")
    exit(1)

# ======================================
# FUNÇÕES AUXILIARES (ANÚNCIOS)
# ======================================

def load_ads():
    """Carrega anúncios do Firebase"""
    ref = db.reference("ads")
    ads = ref.get()
    return list(ads.values()) if ads else []

def validate_code(code):
    """Valida códigos de pagamento"""
    try:
        response = requests.get(FIREBASE_CODES_URL)
        if response.status_code != 200:
            return False

        codes = response.json() or {}
        
        for code_id, code_data in codes.items():
            if isinstance(code_data, dict) and code_data.get("code") == str(code):
                if code_data.get("valid", False):
                    updates = {
                        "valid": False,
                        "used_at": datetime.now().isoformat(),
                        "used_by": "server_validation"
                    }
                    
                    patch_response = requests.patch(
                        f"https://adsdados-default-rtdb.firebaseio.com/codes/{code_id}.json",
                        json=updates
                    )
                    
                    return patch_response.status_code in [200, 204]
                return False
        return False
    except Exception as e:
        print(f"Erro na validação: {str(e)}")
        return False

def upload_to_imgur(image_url):
    """Faz upload de imagens para o Imgur"""
    try:
        with open(image_url, "rb") as image_file:
            headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
            files = {"image": image_file}
            response = requests.post(IMGUR_UPLOAD_URL, headers=headers, files=files)
            return response.json()["data"]["link"] if response.status_code == 200 else None
    except Exception as e:
        print(f"❌ Erro ao enviar imagem: {e}")
        return None

# ======================================
# ROTAS DO SISTEMA
# ======================================

# Inicialização do contador
init_counter_db()

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "jogadas": get_count(),
        "message": "API DeepFish operacional",
        "services": ["anuncios", "contador"]
    })

# Rotas do Contador
@app.route("/incrementar_jogadas", methods=["POST"])
def incrementar_jogadas():
    new_count = increment_count()
    return jsonify({
        "status": "success",
        "jogadas": new_count
    })

@app.route("/obter_jogadas", methods=["GET"])
def obter_jogadas():
    return jsonify({
        "jogadas": get_count()
    })

# Rotas de Anúncios
@app.route("/ads", methods=["GET"])
def get_ads():
    ads = load_ads()
    return jsonify(ads)

@app.route("/ads", methods=["POST"])
def add_ad():
    try:
        data = request.get_json()
        if not all(k in data for k in ["image", "link", "description", "code"]):
            return jsonify({"error": "Todos os campos são obrigatórios"}), 400

        if not validate_code(data["code"]):
            return jsonify({"error": "Código inválido ou já utilizado"}), 400

        uploaded_image_url = upload_to_imgur(data["image"])
        if not uploaded_image_url:
            return jsonify({"error": "Falha ao fazer upload da imagem"}), 500

        ref = db.reference("ads")
        new_ad_ref = ref.push({
            "image": uploaded_image_url,
            "link": data["link"],
            "description": data["description"]
        })

        return jsonify({"message": "Anúncio salvo com sucesso!", "id": new_ad_ref.key}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_codes", methods=["POST"])
def add_codes():
    try:
        data = request.get_json()
        if not isinstance(data.get("codes"), list):
            return jsonify({"error": "Formato inválido. Deve ser uma lista de códigos."}), 400

        ref = db.reference("codes")
        for code in data["codes"]:
            ref.push({"code": str(code), "valid": True})

        return jsonify({"message": "Códigos adicionados com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
