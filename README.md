# RapGenius AI

Assistant IA spécialisé dans le rap et la culture hip-hop, propulsé par Ollama en local.

## Structure

```
rap-ai-mistral/
├── backend/          # API Python (Flask + LangChain + Ollama)
│   ├── server.py
│   ├── prompt.txt
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
└── frontend/         # Interface React + TypeScript + Tailwind
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## Prérequis

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installé et lancé en local

## Démarrage rapide

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # puis renseigner OLLAMA_MODEL
python server.py
# API disponible sur http://localhost:3000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# App disponible sur http://localhost:8080
```

## Fonctionnalités

- 7 modes spécialisés : conversation générale, analyse freestyle, création de lyrics, histoire du rap, battle & punchlines, technique & flow, culture hip-hop
- Détection automatique du mode selon le message
- Recherche web en temps réel via DuckDuckGo
- Mémoire de conversation par session
- Restriction thématique : rap et influences hip-hop uniquement
