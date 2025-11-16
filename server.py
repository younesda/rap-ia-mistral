"""
RapGenius AI - Backend Python avec LangChain et Mistral AI
Serveur Flask pour l'IA spécialisée en rap et culture hip-hop
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from langchain_mistralai import ChatMistralAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import json

# Charger les variables d'environnement
load_dotenv()

# Configuration
app = Flask(__name__, static_folder='.')
CORS(app)

# Verifier la cle API
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
if not MISTRAL_API_KEY:
    print("[ERREUR] MISTRAL_API_KEY n'est pas definie dans le fichier .env")
    print("[INFO] Creez un fichier .env avec votre cle API Mistral:")
    print("   MISTRAL_API_KEY=votre_cle_ici")
    exit(1)

# Configuration Mistral
MISTRAL_MODEL = os.getenv('MISTRAL_MODEL', 'mistral-large-latest')
print(f"[OK] Cle API Mistral chargee")
print(f"[INFO] Modele utilise: {MISTRAL_MODEL}")

def load_prompts():
    """Charger les prompts depuis le fichier prompt.txt"""
    prompt_file = os.path.join(os.path.dirname(__file__), 'prompt.txt')

    try:
        # Essayer différents encodages pour supporter Windows et Unix
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        prompts = None
        used_encoding = None

        for encoding in encodings:
            try:
                with open(prompt_file, 'r', encoding=encoding) as f:
                    prompts = json.load(f)
                used_encoding = encoding
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

        if prompts is None:
            raise ValueError("Impossible de lire le fichier avec les encodages supportes")

        print(f"[OK] Prompts charges depuis {prompt_file} (encodage: {used_encoding})")
        print(f"[INFO] {len(prompts)} modes disponibles")
        return prompts

    except FileNotFoundError:
        print(f"[ERREUR] Fichier {prompt_file} non trouve!")
        print("[INFO] Creation d'un fichier prompt.txt par defaut...")
        # Créer un fichier de prompts par défaut
        default_prompts = {
            'general': {
                'name': 'Conversation Generale',
                'description': 'Mode conversation libre sur le rap et la culture hip-hop',
                'system_prompt': 'Tu es RapGenius AI, un expert passionne de rap et de culture hip-hop.'
            }
        }
        with open(prompt_file, 'w', encoding='utf-8') as f:
            json.dump(default_prompts, f, indent=2, ensure_ascii=False)
        return default_prompts
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ERREUR] Erreur lors du chargement de prompt.txt: {str(e)}")
        exit(1)

# Charger les prompts spécialisés pour chaque mode
MODES_PROMPTS = load_prompts()

# Stockage des conversations par session (en mémoire)
conversations = {}

def get_llm():
    """Initialise et retourne le modèle Mistral via LangChain"""
    return ChatMistralAI(
        model=MISTRAL_MODEL,
        mistral_api_key=MISTRAL_API_KEY,
        temperature=0.7,
        max_tokens=2000,
        top_p=0.95
    )

def create_conversation_chain(mode):
    """Crée une chaîne de conversation LangChain pour un mode spécifique"""

    # Récupérer le prompt système pour le mode
    mode_info = MODES_PROMPTS.get(mode, MODES_PROMPTS['general'])
    system_prompt = mode_info['system_prompt']

    # Créer le template de prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # Initialiser le LLM
    llm = get_llm()

    # Créer la mémoire de conversation
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="history"
    )

    # Créer la chaîne de conversation
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt_template,
        verbose=False
    )

    return conversation

def convert_messages_to_langchain(messages):
    """Convertir les messages du format frontend au format LangChain"""
    langchain_messages = []

    for msg in messages:
        role = msg.get('role')
        content = msg.get('content')

        if role == 'system':
            langchain_messages.append(SystemMessage(content=content))
        elif role == 'user':
            langchain_messages.append(HumanMessage(content=content))
        elif role == 'assistant':
            langchain_messages.append(AIMessage(content=content))

    return langchain_messages

@app.route('/')
def index():
    """Servir la page principale"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Servir les fichiers statiques"""
    return send_from_directory('.', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'ok',
        'model': MISTRAL_MODEL,
        'langchain': True,
        'backend': 'Python + LangChain'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal pour les conversations"""
    try:
        data = request.json
        messages = data.get('messages', [])
        mode = data.get('mode', 'general')
        session_id = data.get('session_id', 'default')

        if not messages:
            return jsonify({'error': 'Messages requis'}), 400

        print(f"\n[REQUEST] Nouvelle requete en mode: {mode}")
        print(f"[INFO] Nombre de messages: {len(messages)}")
        print(f"[INFO] Session ID: {session_id}")

        # Créer ou récupérer la conversation pour cette session et ce mode
        conv_key = f"{session_id}_{mode}"

        if conv_key not in conversations:
            print(f"[NEW] Creation d'une nouvelle conversation pour {conv_key}")
            conversations[conv_key] = create_conversation_chain(mode)

        conversation = conversations[conv_key]

        # Extraire le dernier message utilisateur
        user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_message = msg.get('content')
                break

        if not user_message:
            return jsonify({'error': 'Aucun message utilisateur trouvé'}), 400

        # Generer la reponse avec LangChain
        print(f"[AI] Generation de la reponse...")
        response = conversation.predict(input=user_message)

        print(f"[OK] Reponse generee avec succes")
        print(f"[INFO] Longueur de la reponse: {len(response)} caracteres")

        return jsonify({
            'response': response,
            'mode': mode,
            'session_id': session_id,
            'backend': 'Python + LangChain'
        })

    except Exception as e:
        print(f"[ERROR] Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """Effacer une conversation spécifique"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        mode = data.get('mode')

        if mode:
            conv_key = f"{session_id}_{mode}"
            if conv_key in conversations:
                del conversations[conv_key]
                print(f"[CLEAR] Conversation {conv_key} effacee")
        else:
            # Effacer toutes les conversations de cette session
            keys_to_delete = [k for k in conversations.keys() if k.startswith(f"{session_id}_")]
            for key in keys_to_delete:
                del conversations[key]
            print(f"[CLEAR] Toutes les conversations de la session {session_id} effacees")

        return jsonify({'status': 'ok', 'message': 'Conversation effacée'})

    except Exception as e:
        print(f"[ERROR] Erreur lors de l'effacement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/modes', methods=['GET'])
def get_modes():
    """Retourner la liste des modes disponibles"""
    modes_info = {}
    for mode_id, mode_data in MODES_PROMPTS.items():
        modes_info[mode_id] = {
            'name': mode_data['name'],
            'description': mode_data['description']
        }
    return jsonify(modes_info)

# Gestionnaires d'erreur globaux pour toujours retourner du JSON
@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return jsonify({
        'error': 'Route non trouvée',
        'status': 404
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Gestionnaire d'erreur 405"""
    return jsonify({
        'error': 'Méthode non autorisée',
        'status': 405
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    print(f"[ERROR 500] Erreur interne: {str(error)}")
    import traceback
    traceback.print_exc()
    return jsonify({
        'error': 'Erreur interne du serveur',
        'details': str(error),
        'status': 500
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Gestionnaire d'exception générique pour toutes les erreurs non gérées"""
    print(f"[ERROR] Exception non gérée: {str(error)}")
    import traceback
    traceback.print_exc()

    # Retourner toujours du JSON, jamais du HTML
    return jsonify({
        'error': 'Une erreur est survenue',
        'details': str(error),
        'type': type(error).__name__,
        'status': 500
    }), 500

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 3000))

    print('\n' + '=' * 60)
    print('RapGenius AI - Serveur Python + LangChain demarre!')
    print('=' * 60)
    print(f'Application disponible sur: http://localhost:{PORT}')
    print(f'Modele Mistral: {MISTRAL_MODEL}')
    print(f'Backend: Python + LangChain + Mistral AI')
    print(f'Environnement: {os.getenv("ENV", "development")}')
    print('=' * 60)
    print(f'\nOuvrez votre navigateur et allez sur http://localhost:{PORT}')
    print('Pret a parler de rap!\n')

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=os.getenv('ENV') != 'production'
    )
