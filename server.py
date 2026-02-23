"""
RapGenius AI - Backend Python avec LangChain et Ollama
API REST pure pour le frontend Lovable
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gpt-oss:120b-cloud')
print(f"[OK] Modele: {OLLAMA_MODEL} | URL: {OLLAMA_BASE_URL}")

def load_prompts():
    prompt_file = os.path.join(os.path.dirname(__file__), 'prompt.txt')
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(prompt_file, 'r', encoding=encoding) as f:
                prompts = json.load(f)
            print(f"[OK] {len(prompts)} modes charges (encodage: {encoding})")
            return prompts
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    print(f"[ERREUR] Impossible de lire {prompt_file}")
    exit(1)

MODES_PROMPTS = load_prompts()
conversations = {}

def get_llm():
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
        num_predict=2000,
    )

def create_conversation_chain(mode):
    mode_info = MODES_PROMPTS.get(mode, MODES_PROMPTS['general'])
    system_prompt = mode_info['system_prompt']

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    memory = ConversationBufferMemory(return_messages=True, memory_key="history")

    return ConversationChain(
        llm=get_llm(),
        memory=memory,
        prompt=prompt_template,
        verbose=False
    )

# --- Routes API ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'model': OLLAMA_MODEL,
        'ollama_url': OLLAMA_BASE_URL,
        'backend': 'Python + LangChain + Ollama'
    })

@app.route('/api/modes', methods=['GET'])
def get_modes():
    return jsonify({
        mode_id: {
            'name': data['name'],
            'description': data['description']
        }
        for mode_id, data in MODES_PROMPTS.items()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        mode = data.get('mode', 'general')
        session_id = data.get('session_id', 'default')

        if not messages:
            return jsonify({'error': 'Messages requis'}), 400

        conv_key = f"{session_id}_{mode}"
        if conv_key not in conversations:
            conversations[conv_key] = create_conversation_chain(mode)

        user_message = next(
            (m['content'] for m in reversed(messages) if m.get('role') == 'user'),
            None
        )

        if not user_message:
            return jsonify({'error': 'Aucun message utilisateur trouvé'}), 400

        print(f"[AI] Mode: {mode} | Session: {session_id}")
        response = conversations[conv_key].predict(input=user_message)
        print(f"[OK] Reponse: {len(response)} caracteres")

        return jsonify({
            'response': response,
            'mode': mode,
            'session_id': session_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        mode = data.get('mode')

        if mode:
            conv_key = f"{session_id}_{mode}"
            conversations.pop(conv_key, None)
        else:
            for key in [k for k in conversations if k.startswith(f"{session_id}_")]:
                del conversations[key]

        return jsonify({'status': 'ok'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Erreurs globales ---

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Route non trouvée', 'status': 404}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 3000))
    print(f'\n{"="*50}')
    print(f'RapGenius AI — API démarrée sur http://localhost:{PORT}')
    print(f'Modele: {OLLAMA_MODEL} | Ollama: {OLLAMA_BASE_URL}')
    print(f'{"="*50}\n')
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('ENV') != 'production')
