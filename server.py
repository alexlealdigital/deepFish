import firebase_admin
from firebase_admin import credentials, db
import os

# Configuração Firebase
cred = credentials.Certificate({
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT")
})

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://deepfish-counter.firebaseio.com/' # Substitua pelo seu URL
})

@app.route('/incrementar', methods=['POST'])
def incrementar():
    try:
        ref = db.reference('contador')
        novo_valor = ref.transaction(lambda current: (current or 200) + 1)
        return jsonify({"status": "success", "jogadas": novo_valor})
    except Exception as e:
        return jsonify({"status": "error", "erro": str(e)}), 500
