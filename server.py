import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite todas as origens (ajuste depois)

# Configuração à prova de erros para o Render
def get_db_path():
    """Define o caminho absoluto garantido para o arquivo SQLite"""
    # Tenta primeiro a pasta persistente do Render
    render_path = '/var/lib/render/jogadas.db'
    if os.path.exists('/var/lib/render'):
        return render_path
    
    # Se não existir, usa o diretório atual (para desenvolvimento local)
    return os.path.join(os.getcwd(), 'jogadas.db')

DATABASE = get_db_path()

def init_db():
    """Inicialização robusta do banco de dados"""
    try:
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contador (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                valor INTEGER NOT NULL DEFAULT 200
            )
        """)
        
        # Insere o valor inicial apenas se a tabela estiver vazia
        cursor.execute("INSERT OR IGNORE INTO contador (id, valor) VALUES (1, 200)")
        conn.commit()
        
    except Exception as e:
        print(f"ERRO NA INICIALIZAÇÃO: {str(e)}")
        raise
    finally:
        conn.close()

def get_count():
    """Obtém o contador com tratamento de erros"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM contador WHERE id = 1")
        return cursor.fetchone()[0]
    except Exception as e:
        print(f"ERRO AO LER CONTADOR: {str(e)}")
        return 200  # Valor padrão se falhar
    finally:
        conn.close()

def increment_count():
    """Incrementa o contador com transação segura"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE contador SET valor = valor + 1 WHERE id = 1")
        conn.commit()
        return get_count()
    except Exception as e:
        print(f"ERRO AO INCREMENTAR: {str(e)}")
        return get_count()  # Tenta retornar o valor atual mesmo se falhar
    finally:
        conn.close()

# Rotas
@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "jogadas": get_count(),
        "db_path": DATABASE  # Para debug
    })

@app.route("/incrementar", methods=["POST"])
def incrementar():
    return jsonify({
        "jogadas": increment_count(),
        "db_path": DATABASE  # Para debug
    })

# Inicialização segura
if __name__ == "__main__":
    print(f"🚀 Iniciando servidor com banco em: {DATABASE}")
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
