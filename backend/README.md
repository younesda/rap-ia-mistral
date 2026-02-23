# RapGenius AI — Backend

API REST Python propulsée par Flask, LangChain 1.x, LangGraph et Ollama.

## Stack

| Composant | Rôle |
|-----------|------|
| Flask | Serveur HTTP |
| LangChain 1.x | Orchestration de l'agent |
| LangGraph MemorySaver | Mémoire de conversation par session |
| ChatOllama | Inférence locale via Ollama |
| DuckDuckGoSearchRun | Recherche web sans clé API |

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` en `.env` et renseigner les valeurs :

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:120b-cloud
PORT=3000
ENV=development
```

## Lancement

```bash
python server.py
```

## Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/health` | Statut du serveur et du modèle |
| GET | `/api/modes` | Liste des 7 modes disponibles |
| POST | `/api/chat` | Envoyer un message à l'agent |
| POST | `/api/clear` | Réinitialiser une session |

### POST `/api/chat`

**Corps de la requête :**
```json
{
  "messages": [{ "role": "user", "content": "..." }],
  "mode": "general",
  "session_id": "session_1234567890"
}
```

**Réponse :**
```json
{
  "response": "...",
  "mode": "general",
  "session_id": "session_1234567890"
}
```

## Modes disponibles

| ID | Nom |
|----|-----|
| `general` | Conversation Générale |
| `freestyle` | Analyse Freestyle |
| `lyrics` | Création de Lyrics |
| `history` | Histoire du Rap |
| `battle` | Battle & Punchlines |
| `technique` | Technique & Flow |
| `culture` | Culture Hip-Hop |

## Architecture agent

L'agent est construit avec `create_agent` (LangChain 1.x / LangGraph) :

1. Le message utilisateur est reçu par Flask
2. Le mode est déterminé côté frontend via détection par mots-clés
3. L'agent est invoqué avec le `thread_id` `{session_id}_{mode}`
4. L'agent décide seul s'il doit faire une recherche web ou répondre de mémoire
5. `MemorySaver` conserve l'historique par `thread_id` en RAM

## Prompts

Les system prompts sont définis dans `prompt.txt` (JSON). Chaque mode possède :
- `name` : nom affiché
- `description` : description courte
- `system_prompt` : instructions détaillées pour le LLM

Le `TOPIC_GUARD` (défini dans `server.py`) est ajouté en tête de chaque system prompt pour imposer la restriction thématique rap/hip-hop.
