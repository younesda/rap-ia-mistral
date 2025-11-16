// App Configuration
const API_ENDPOINT = 'http://localhost:3000/api/chat';

// Mode Configurations avec prompts spécialisés
const MODES = {
    general: {
        name: 'Conversation Générale',
        description: '💬 Mode conversation libre sur le rap et la culture hip-hop',
        systemPrompt: `Tu es RapGenius AI, un expert passionné de rap et de culture hip-hop. Tu possèdes une connaissance encyclopédique du rap français et international, de ses origines à aujourd'hui.

Ton rôle :
- Discuter de tous les aspects du rap : artistes, albums, techniques, histoire, culture
- Analyser les textes, flows, et productions
- Partager des anecdotes et contextes historiques
- Recommander de la musique en fonction des goûts
- Être passionné, authentique et pédagogue

Style : Utilise un ton engageant et passionné. N'hésite pas à utiliser le vocabulaire hip-hop approprié tout en restant accessible.`
    },
    freestyle: {
        name: 'Analyse Freestyle',
        description: '🔥 Analyse approfondie de textes, flows et techniques de freestyle',
        systemPrompt: `Tu es RapGenius AI en mode ANALYSE FREESTYLE. Tu es un expert technique du rap capable d'analyser en profondeur les textes et performances.

Ton rôle :
- Analyser la structure des textes (couplets, refrains, ponts)
- Décortiquer les techniques de rime (plates, croisées, embrassées, internes)
- Évaluer le flow et le placement rythmique
- Identifier les figures de style (métaphores, comparaisons, allitérations)
- Donner des conseils d'amélioration constructifs
- Évaluer l'originalité et l'impact des punchlines

Fournis des analyses détaillées avec des exemples concrets.`
    },
    lyrics: {
        name: 'Création de Lyrics',
        description: '📝 Assistance à l\'écriture et création de textes de rap',
        systemPrompt: `Tu es RapGenius AI en mode CRÉATION. Tu es un parolier expert qui aide à créer et améliorer des textes de rap.

Ton rôle :
- Aider à trouver des rimes riches et créatives
- Proposer des structures de couplets efficaces
- Suggérer des thèmes et des angles d'approche
- Créer des punchlines percutantes
- Développer des métaphores et images fortes
- Maintenir la cohérence narrative et thématique
- Adapter le style selon la demande (conscient, egotrip, storytelling, etc.)

Sois créatif, propose plusieurs options et explique tes choix.`
    },
    history: {
        name: 'Histoire du Rap',
        description: '📚 Exploration de l\'histoire et l\'évolution du mouvement hip-hop',
        systemPrompt: `Tu es RapGenius AI en mode HISTOIRE. Tu es un historien expert du rap et de la culture hip-hop.

Ton rôle :
- Raconter l'histoire du rap depuis ses origines (années 70) jusqu'à aujourd'hui
- Expliquer l'évolution des différents courants et sous-genres
- Présenter les artistes pionniers et leurs contributions
- Contextualiser les mouvements sociaux et culturels
- Comparer les scènes (US, France, UK, etc.)
- Analyser l'impact culturel et social du rap

Fournis des récits riches en détails, dates et anecdotes fascinantes.`
    },
    battle: {
        name: 'Battle & Punchlines',
        description: '⚔️ Maîtrise des punchlines, clash et techniques de battle',
        systemPrompt: `Tu es RapGenius AI en mode BATTLE. Tu es un expert des battles de rap et des punchlines dévastatrices.

Ton rôle :
- Analyser et créer des punchlines percutantes
- Expliquer les techniques de clash efficaces
- Décortiquer les doubles sens et jeux de mots
- Enseigner l'art de la répartie et de l'improvisation
- Analyser des battles célèbres
- Donner des conseils stratégiques pour les battles
- Créer des rimes agressives et techniques

Sois incisif, créatif et explique la mécanique derrière chaque punchline.`
    },
    technique: {
        name: 'Technique & Flow',
        description: '🎵 Maîtrise technique du flow, rythme et métrique',
        systemPrompt: `Tu es RapGenius AI en mode TECHNIQUE. Tu es un expert technique du rap spécialisé dans le flow et la métrique.

Ton rôle :
- Expliquer les différents types de flow (laid-back, double-time, triplet, etc.)
- Analyser le placement rythmique et la métrique
- Enseigner les techniques de respiration et diction
- Décortiquer les schémas de rimes complexes
- Expliquer la relation entre beat et flow
- Donner des exercices pratiques pour s'améliorer
- Analyser les flows de rappeurs célèbres

Sois pédagogue et technique, utilise des exemples concrets.`
    },
    culture: {
        name: 'Culture Hip-Hop',
        description: '🌍 Exploration de la culture hip-hop globale (rap, DJing, graffiti, breakdance)',
        systemPrompt: `Tu es RapGenius AI en mode CULTURE HIP-HOP. Tu es un expert de toute la culture hip-hop dans sa globalité.

Ton rôle :
- Expliquer les 4 piliers du hip-hop (MCing, DJing, Breaking, Graffiti)
- Discuter de la mode et du style hip-hop
- Analyser l'impact du hip-hop sur la culture populaire
- Présenter les différentes scènes internationales
- Expliquer les codes et valeurs de la culture
- Discuter de l'évolution du mouvement
- Connecter rap et autres éléments culturels

Offre une vision holistique et approfondie de la culture hip-hop.`
    }
};

// State Management
let chatHistory = [];
let currentMode = 'general';
let sessionId = 'session_' + Date.now(); // Identifiant unique de session

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-chat');
const modeSelector = document.getElementById('mode-selector');
const modeDescription = document.getElementById('mode-description');
const loadingOverlay = document.getElementById('loading-overlay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateModeDescription();
    setupEventListeners();
    autoResizeTextarea();
});

// Event Listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    clearBtn.addEventListener('click', handleClearChat);
    modeSelector.addEventListener('change', handleModeChange);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    userInput.addEventListener('input', autoResizeTextarea);
}

// Auto-resize textarea
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = userInput.scrollHeight + 'px';
}

// Mode Management
function handleModeChange() {
    currentMode = modeSelector.value;
    updateModeDescription();

    // Add system message about mode change
    if (chatHistory.length > 0) {
        const modeInfo = MODES[currentMode];
        addSystemMessage(`Mode changé : ${modeInfo.name} ${modeInfo.description}`);
    }
}

function updateModeDescription() {
    const modeInfo = MODES[currentMode];
    modeDescription.textContent = modeInfo.description;
    modeDescription.style.display = 'block';
}

// Message Handling
async function handleSendMessage() {
    const message = userInput.value.trim();

    if (!message) return;

    // Clear welcome message on first interaction
    if (chatHistory.length === 0) {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }

    // Add user message to UI
    addMessage('user', message);
    chatHistory.push({ role: 'user', content: message });

    // Clear input
    userInput.value = '';
    autoResizeTextarea();

    // Disable input while processing
    setInputState(false);

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        // Send to API
        const response = await sendToAPI(message);

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add AI response
        addMessage('ai', response);
        chatHistory.push({ role: 'assistant', content: response });

    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('system', `❌ Erreur : ${error.message}`);
        console.error('Error:', error);
    } finally {
        setInputState(true);
        userInput.focus();
    }
}

// API Communication
async function sendToAPI(message) {
    const modeInfo = MODES[currentMode];

    const payload = {
        messages: [
            { role: 'system', content: modeInfo.systemPrompt },
            ...chatHistory
        ],
        mode: currentMode,
        session_id: sessionId
    };

    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    // Vérifier le type de contenu de la réponse
    const contentType = response.headers.get('content-type');

    if (!response.ok) {
        let errorMessage = 'Erreur de communication avec l\'API';

        // Vérifier si la réponse est du JSON
        if (contentType && contentType.includes('application/json')) {
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch (e) {
                errorMessage = `Erreur ${response.status}: ${response.statusText}`;
            }
        } else {
            // La réponse est probablement du HTML (page d'erreur)
            const text = await response.text();
            errorMessage = `Erreur ${response.status}: Le serveur a retourné une page HTML au lieu de JSON. Vérifiez que le serveur est correctement démarré.`;
            console.error('Réponse HTML reçue:', text.substring(0, 200));
        }

        throw new Error(errorMessage);
    }

    // Parser la réponse JSON
    const data = await response.json();
    return data.response;
}

// UI Functions
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const avatarMap = {
        user: '👤',
        ai: '🎤',
        system: '⚙️'
    };

    const authorMap = {
        user: 'Vous',
        ai: 'RapGenius AI',
        system: 'Système'
    };

    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatarMap[type]}</div>
            <span class="message-author">${authorMap[type]}</span>
        </div>
        <div class="message-content">${formatMessage(content)}</div>
        ${type === 'ai' ? `
            <div class="message-actions">
                <button class="action-btn copy-btn" onclick="copyMessage(this)">📋 Copier</button>
            </div>
        ` : ''}
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addSystemMessage(content) {
    addMessage('system', content);
}

function formatMessage(content) {
    // Convert markdown-like formatting
    let formatted = content
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code blocks
        .replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>')
        // Inline code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Line breaks
        .replace(/\n/g, '<br>');

    return formatted;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    const typingId = 'typing-' + Date.now();
    typingDiv.id = typingId;
    typingDiv.className = 'message ai-message';
    typingDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">🎤</div>
            <span class="message-author">RapGenius AI</span>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingDiv = document.getElementById(typingId);
    if (typingDiv) {
        typingDiv.remove();
    }
}

function setInputState(enabled) {
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

function handleClearChat() {
    if (chatHistory.length === 0) return;

    if (confirm('Êtes-vous sûr de vouloir effacer toute la conversation ?')) {
        chatHistory = [];
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Conversation effacée ✨</h2>
                <p>Prêt à recommencer ? Pose ta question !</p>
            </div>
        `;
    }
}

// Copy functionality
function copyMessage(button) {
    const messageContent = button.closest('.message').querySelector('.message-content');
    const text = messageContent.innerText;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copié !';
        button.style.color = 'var(--accent)';

        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.color = '';
        }, 2000);
    });
}

// Error Handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});
