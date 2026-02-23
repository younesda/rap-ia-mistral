"""
RapGenius AI - Agent IA avec recherche web (DuckDuckGo) + Ollama
LangChain 1.x / LangGraph - create_agent API
Restricted to rap, hip-hop and their cultural influences only.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

app = Flask(__name__)
CORS(app)

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gpt-oss:120b-cloud')
print(f"[OK] Modele: {OLLAMA_MODEL} | URL: {OLLAMA_BASE_URL}")

# --- Chargement des prompts ---

def load_prompts():
    prompt_file = os.path.join(os.path.dirname(__file__), 'prompt.txt')
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            with open(prompt_file, 'r', encoding=encoding) as f:
                prompts = json.load(f)
            print(f"[OK] {len(prompts)} modes charges (encodage: {encoding})")
            return prompts
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    print("[ERREUR] Impossible de lire prompt.txt")
    exit(1)

MODES_PROMPTS = load_prompts()

# --- Outils & mémoire ---

search_tool = DuckDuckGoSearchRun(name="recherche_web")
tools = [search_tool]

# Mémoire partagée (LangGraph checkpointer)
# thread_id = f"{session_id}_{mode}" pour isoler chaque session/mode
memory = MemorySaver()

# Cache d'agents par mode (un agent par mode, mémoire partagée via thread_id)
agent_cache: dict = {}

TOPIC_GUARD = """\
RÈGLE ABSOLUE : Tu réponds UNIQUEMENT aux questions liées au rap, au hip-hop, \
et à leurs influences sur d'autres domaines (sport, football, basketball, \
mode, politique, langage, verlan, art, cinéma, gaming, entrepreneuriat, etc.). \
Pour toute autre question hors sujet, refuse poliment en une phrase et \
redirige vers ton domaine d'expertise.

Tu as accès à un outil de recherche web. Utilise-le pour toute information \
récente : nouveaux albums, actualités d'artistes, classements, événements, \
collaborations récentes, influences culturelles actuelles, etc.

Réponds toujours en français, de façon détaillée et structurée.\
"""

def get_agent(mode: str):
    """Retourne l'agent pour un mode donné (créé une seule fois)."""
    if mode not in agent_cache:
        mode_info = MODES_PROMPTS.get(mode, MODES_PROMPTS['general'])

        system_prompt = f"{TOPIC_GUARD}\n\n---\n\n{mode_info['system_prompt']}"

        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
            num_predict=2000,
        )

        agent_cache[mode] = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=memory,
        )
        print(f"[NEW] Agent cree pour le mode '{mode}'")

    return agent_cache[mode]

# --- Routes API ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'model': OLLAMA_MODEL,
        'ollama_url': OLLAMA_BASE_URL,
        'mode': 'agent',
        'tools': ['DuckDuckGoSearch'],
        'backend': 'Python + LangChain 1.x Agent + Ollama'
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

        user_message = next(
            (m['content'] for m in reversed(messages) if m.get('role') == 'user'),
            None
        )
        if not user_message:
            return jsonify({'error': 'Aucun message utilisateur trouvé'}), 400

        # thread_id unique par session + mode (mémoire isolée)
        thread_id = f"{session_id}_{mode}"
        print(f"\n[AGENT] Mode: {mode} | Thread: {thread_id}")
        print(f"[AGENT] Message: {user_message[:80]}...")

        agent = get_agent(mode)

        result = agent.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        response_text = result["messages"][-1].content
        print(f"[OK] Reponse: {len(response_text)} caracteres")

        return jsonify({
            'response': response_text,
            'mode': mode,
            'session_id': session_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """
    Avec MemorySaver, on ne peut pas supprimer un thread directement.
    Le frontend génère un nouveau session_id pour repartir de zéro.
    """
    return jsonify({'status': 'ok', 'message': 'Démarrez une nouvelle session côté client.'})

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
    print(f'\n{"="*55}')
    print(f'RapGenius AI — Agent IA sur http://localhost:{PORT}')
    print(f'Modele : {OLLAMA_MODEL} | Ollama : {OLLAMA_BASE_URL}')
    print(f'Outils : DuckDuckGo Search')
    print(f'Memoire: LangGraph MemorySaver (par thread_id)')
    print(f'Restriction : Rap & Hip-Hop uniquement')
    print(f'{"="*55}\n')
    app.run(host='0.0.0.0', port=PORT, debug=os.getenv('ENV') != 'production')
