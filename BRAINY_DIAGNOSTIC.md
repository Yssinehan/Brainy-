# Diagnostic technique — Brainy

Date d'analyse : 13 septembre 2026  
Périmètre : audit statique du dépôt et vérification locale non destructive. Aucun fichier existant n'a été modifié, supprimé ou déplacé dans le cadre de cet audit ; ce document est le seul nouveau fichier créé.

## 1. Résumé exécutif

Brainy est une application Python locale de type **RAG** (Retrieval-Augmented Generation) : elle indexe des documents dans SQLite + Chroma, récupère les passages pertinents avec des embeddings locaux, puis demande à un LLM de produire une réponse ancrée dans ces passages.

L'application web actuelle est une SPA statique HTML/CSS/JavaScript servie par FastAPI. Le backend appelle **Ollama** pour la génération et `sentence-transformers` pour les embeddings. Le modèle de conversation actuellement configuré est `llama3.2:1b`, exécuté par Ollama sur la machine locale. Aucun modèle n'est stocké dans le dépôt : les poids se trouvent dans le cache Ollama global de la machine.

La lenteur observée est principalement due à l'inférence LLM locale sur CPU. Les facteurs secondaires sont le chargement à froid de l'embedder, la recherche hybride et la taille du contexte RAG. Un script QLoRA pour GPU est présent, mais son adaptateur n'a pas été trouvé dans ce dépôt et il n'est pas branché à l'inférence actuelle.

## 2. Structure du projet

```text
Brainy/
├── .env                         # Configuration locale ; contient des secrets, non détaillés ici
├── .env.example                 # Modèle de configuration sans secret
├── .github/workflows/ci.yml     # Intégration continue
├── .venv/ et venv/              # Environnements virtuels locaux (non versionnés)
├── data/                        # Données locales/caches de développement ; ne pas publier
├── docs/
│   ├── ARCHITECTURE.md           # Architecture détaillée
│   ├── PRD.md, TDD.md, ROADMAP.md
│   ├── ENTRAINEMENT_DARIJA.md    # Guide QLoRA GPU
│   └── darija_marocaine_latin_10000.jsonl # Dataset conversationnel Darija
├── knowledge_base/              # Documents d'exemple à ingérer
├── scripts/
│   ├── train_darija_lora.py     # Entraînement QLoRA, réservé à CUDA
│   ├── check_graph_health.py
│   ├── merge_stores.py
│   └── rebuild_entities.py
├── src/brainy/
│   ├── config.py                # Configuration Pydantic et chemins de données
│   ├── engine.py                # Composition des services Brainy
│   ├── interfaces/
│   │   ├── api.py               # FastAPI, API REST et service de la SPA
│   │   ├── cli.py               # Commande CLI Typer
│   │   ├── validators.py        # Validation d'entrées
│   │   └── web/                 # Frontend actuel
│   │       ├── index.html       # Structure de la SPA
│   │       ├── styles.css       # Thème blanc/bleu responsive
│   │       └── app.js           # Navigation, chat et calendrier
│   ├── router/
│   │   ├── router.py            # Sélection des fournisseurs LLM/embeddings
│   │   └── providers.py         # Appels Ollama, Gemini et SentenceTransformers
│   ├── rag/                     # Pipeline RAG et retrievers hybrides
│   ├── memory/                  # SQLite, Chroma, ingestion, scoring et recherche
│   ├── graph/                   # Graphe de connaissances NetworkX/SQLite
│   ├── agent/                   # Agent plan-act-reflect et outils autorisés
│   ├── voice/                   # Whisper local et TTS
│   ├── vision/                  # OCR Tesseract et description d'image Gemini
│   ├── prompts/                 # Prompts système versionnés
│   ├── integrations/            # Synchronisation de contenus externes
│   ├── review/, proactive/, profile/, recommendation/, eval/, tools/
│   └── logging_config.py, errors.py
├── tests/                       # Suite pytest hors ligne
├── Dockerfile                   # Image Python/FastAPI, pas un conteneur LLM GPU
├── docker-compose.yml           # API Brainy ; Ollama attendu sur l'hôte
├── requirements.txt             # Dépendances d'exécution
├── requirements-train.txt       # Dépendances GPU d'entraînement
├── requirements.lock.txt        # Versions verrouillées
├── pyproject.toml               # Paquet Python BRAINY v1.0.0
└── run.cmd                      # Lance Uvicorn sur Windows
```

### Fichiers de lancement et de configuration

| Fichier | Rôle |
|---|---|
| `run.cmd` | Lance `uvicorn brainy.interfaces.api:app` sur `127.0.0.1:8000`. |
| `src/brainy/config.py` | Lit `.env` avec Pydantic Settings. Définit modèle Ollama, limites de génération/RAG, chemins de données, Whisper et mémoire. |
| `.env` | Configuration locale active. Il contient une clé Gemini et ne doit jamais être commité ou copié dans Colab. Les valeurs de secrets ne sont pas reproduites dans ce rapport. |
| `.env.example` | Exemple public de variables : hôte/modèle Ollama, limites de contexte, recherche et chemin de données. |
| `Dockerfile` / `docker-compose.yml` | Démarrent l'API, mais ne fournissent pas CUDA ni Ollama dans le conteneur. |
| `pyproject.toml` | Paquet Python `BRAINY`, Python >= 3.12, version 1.0.0, commande CLI `BRAINY`. |

## 3. Technologies utilisées

### Frontend

| Élément | Technologie constatée |
|---|---|
| Framework | Aucun framework SPA : JavaScript navigateur natif (vanilla JS). |
| Langages | HTML5, CSS3, JavaScript moderne. |
| Bundler / package manager | Aucun. Il n'y a ni `package.json`, ni React, TypeScript, Vite, Next.js ou Tailwind. |
| UI / icônes | CSS personnalisé et caractères Unicode ; aucune bibliothèque UI. |
| État | Objet JavaScript en mémoire + `localStorage` comme repli pour les événements. |
| Routing | Hash routing client : `#home`, `#chat`, `#calendar`. |
| Backend frontend | La SPA est servie à `/`; les assets sont sous `/ui/`. Le token de passerelle est injecté dans le HTML pour les requêtes même origine. |

La SPA offre : page d'accueil, chat, import document/photo, détection de dates côté interface, calendrier mensuel, création/modification/suppression d'événements. Elle utilise l'API réelle lorsqu'elle est disponible et des données locales de secours pour le calendrier.

### Backend

| Élément | Technologie constatée |
|---|---|
| Langage | Python 3.12+ |
| API HTTP | FastAPI >= 0.115 avec Pydantic v2 |
| Serveur ASGI | Uvicorn >= 0.30 |
| CLI | Typer >= 0.12 |
| Base mémoire | SQLite (via `MemoryStore`) |
| Base vectorielle | ChromaDB >= 0.5 persistant |
| Graphe | NetworkX >= 3.2, données persistées via la couche mémoire |
| Embeddings | `sentence-transformers` >= 3.0, modèle par défaut `all-MiniLM-L6-v2` |
| LLM conversationnel | Client Python `ollama` >= 0.3 vers serveur Ollama HTTP |
| Vision distante | `google-genai` >= 2.8, uniquement pour la description d'image si une clé Gemini est configurée |
| Documents | pdfplumber, python-docx, openpyxl ; OCR via pytesseract/Pillow |
| Voix | faster-whisper + pyttsx3 |

L'architecture est une façade `PersonalAIEngine` (`engine.py`) qui assemble `MemoryStore`, `VectorStore`, `ModelRouter`, STT et TTS. Les routes FastAPI et la CLI restent des adaptateurs minces vers cette façade.

## 4. Modèle IA réellement utilisé

### Inférence de conversation active

| Propriété | Constat |
|---|---|
| Modèle configuré | `llama3.2:1b` dans l'environnement local actuel |
| Fournisseur / runtime | Ollama local, HTTP par défaut `http://localhost:11434` |
| Architecture/famille | Llama 3.2, modèle instruction/chat servi par Ollama |
| Paramètres | Environ 1 milliard (d'après le nom du modèle) |
| Taille locale observée | Environ 1,3 Go dans `ollama list` |
| Format et quantification | Géré par Ollama ; les métadonnées détaillées de quantification n'ont pas été exposées par `ollama list` pour le 1B lors de cet audit. |
| Emplacement des poids | Hors dépôt, dans le stockage global d'Ollama. Aucun fichier GGUF/Safetensors de ce LLM n'est présent sous `Brainy/`. |
| Chargement | À la demande par le serveur Ollama au premier appel, via `ollama.Client.chat()`. |

Autres modèles Ollama observés sur la machine : `llama3.2:3b` (~2,0 Go) et `gemma4:26b` (~18 Go). Ils ne sont pas le modèle configuré de Brainy. L'état Ollama ne signalait aucun modèle actif au moment du dernier contrôle : une première requête après inactivité doit donc charger les poids et est plus lente.

### Embeddings

Le modèle `all-MiniLM-L6-v2` est chargé par `sentence_transformers.SentenceTransformer` dans `LocalEmbedder._get_model()` (`src/brainy/router/providers.py`). Il crée les vecteurs de documents et de requêtes. C'est un second modèle local, distinct du modèle de chat. Son premier chargement peut ralentir la première ingestion ou requête RAG.

### Fine-tuning présent mais non déployé

Le dépôt contient un pipeline d'entraînement, séparé de l'inférence courante :

| Propriété | Constat |
|---|---|
| Script | `scripts/train_darija_lora.py` |
| Base model par défaut | `Qwen/Qwen2.5-3B-Instruct` |
| Méthode | SFT (TRL `SFTTrainer`) + PEFT QLoRA |
| Quantification entraînement | 4-bit NF4, double quantification, BitsAndBytesConfig |
| Adaptateur LoRA | rang `r=16`, alpha 32, dropout 0,05 ; modules Q/K/V/O et MLP ciblés |
| Dataset | `docs/darija_marocaine_latin_10000.jsonl`, documenté à 789 conversations `messages` |
| Tokenizer | `AutoTokenizer.from_pretrained(base_model)` ; sauvegardé avec l'adaptateur |
| Artefacts attendus | `artifacts/darija-lora/adapter_model.safetensors`, `adapter_config.json`, tokenizer et checkpoints |
| État trouvé | Aucun dossier `artifacts/darija-lora` ni adaptateur sauvegardé n'est présent dans le dépôt. |

**Point crucial :** l'application actuelle n'infère pas avec Qwen ni avec cet adaptateur LoRA. Elle utilise Ollama/Llama. Entraîner Qwen sur Colab ne changera donc pas Brainy tant qu'un serveur d'inférence pour Qwen + PEFT (ou un modèle fusionné/converti) ne remplacera pas ou ne complètera pas `OllamaProvider`.

## 5. Flux exact d'inférence

```text
Navigateur (web/app.js)
  -> POST /ask ou POST /api/v1/chat (X-DreamOS-Token)
  -> FastAPI (interfaces/api.py)
  -> PersonalAIEngine.process_message()
  -> RAGEngine.answer() / rag.pipeline.ask()
  -> HybridRetriever
      -> recherche vectorielle Chroma + all-MiniLM-L6-v2
      -> recherche mots-clés SQLite
      -> recherche graphe
  -> contexte RAG borné
  -> ModelRouter.complete()
  -> OllamaProvider.complete()
  -> ollama.Client.chat()
  -> serveur Ollama -> llama3.2:1b
  -> Answer JSON -> FastAPI -> navigateur
```

### Fichiers et fonctions

| Étape | Fichier / symbole | Fonction |
|---|---|---|
| UI | `interfaces/web/app.js`, `sendMessage()` | Envoie la question au endpoint `/ask`, affiche le résultat. |
| HTTP | `interfaces/api.py`, `ask_endpoint()` | Reçoit `AskRequest(question, k, verify)`. |
| Orchestration | `engine.py`, `PersonalAIEngine.process_message()` | Délègue à `generate_response()`. |
| RAG | `rag/pipeline.py`, `ask()` | Récupère les chunks, construit le prompt et appelle le routeur. |
| Retrieval | `rag/retrievers.py`, `HybridRetriever.retrieve()` | Fusion RRF de recherche sémantique, lexicale et graphe. |
| Embeddings | `router/providers.py`, `LocalEmbedder.embed()` | `SentenceTransformer.encode(..., normalize_embeddings=True)`. |
| Routage | `router/router.py`, `ModelRouter.complete()` | Ne choisit qu'Ollama pour le chat ; pas de fallback cloud silencieux. |
| Génération | `router/providers.py`, `OllamaProvider.complete()` | Crée `ollama.Client`, puis exécute `client.chat()`. |

Il n'y a pas de `transformers.pipeline()`, `model.generate()`, `AutoModelForCausalLM` ou tokenizer dans la chaîne de chat de production. Ces APIs sont utilisées uniquement par `scripts/train_darija_lora.py` pour l'entraînement QLoRA.

### Paramètres de génération actifs

Les paramètres viennent de `.env` (sans reproduire les secrets) et de `Settings` :

| Paramètre | Valeur active constatée | Effet |
|---|---:|---|
| Modèle | `llama3.2:1b` | Modèle plus léger que le 3B, adapté au CPU local. |
| `num_predict` | 128 tokens | Longueur maximale de la réponse. Une limite trop basse coupe les réponses. |
| `num_ctx` | 2048 | Fenêtre de contexte Ollama. |
| `num_thread` | 8 | Threads CPU demandés à Ollama sur cette machine. |
| Timeout client | 90 s | Limite du client Ollama ; l'API renvoie ensuite une erreur 503. |
| `retrieval_top_k` | 2 | Nombre de passages retournés au RAG. |
| `rag_context_max_chars` | 1200 caractères | Taille maximale des extraits injectés au LLM. |
| Seuil de similarité | 0,25 | Sous ce seuil, Brainy refuse de répondre sans mémoire pertinente. |

## 6. Diagnostic des lenteurs

### Causes principales confirmées

1. **Inférence CPU locale.** Ollama est utilisé sans VRAM GPU. La machine comporte un AMD Ryzen 5 PRO 2500U (4 cœurs / 8 threads) et environ 14,9 Go de RAM. Cette génération CPU est la cause dominante.
2. **Chargement à froid.** Le modèle Ollama n'était pas actif pendant le contrôle. Le premier message après expiration/restart doit charger les poids et peut être nettement plus lent.
3. **RAG à chaque question.** Une question passe par embedding, Chroma, recherche lexicale, graphe, fusion puis construction de contexte avant la génération.
4. **Chargement à froid de l'embedder.** `all-MiniLM-L6-v2` est lazy-loaded ; la première opération peut télécharger/charger les poids et consommer de la RAM.
5. **Réponse désormais plus complète.** La limite a été relevée à 128 tokens pour ne plus couper les phrases ; le temps augmente logiquement par rapport à 48 tokens.

### Mesure locale disponible

Un essai direct après échauffement de `llama3.2:1b` a mesuré environ **8,3 tokens/seconde** et **1,68 seconde** pour une très courte réponse de 12 tokens. Les réponses RAG réelles sont plus longues et incluent retrieval + contexte : elles seront donc plus lentes. Avant l'allègement, des journaux relevaient des appels `llama3.2:3b` qui atteignaient le timeout de 90 secondes.

### Limitations de qualité observables

- Le 1B réduit fortement la latence, mais sa qualité, son suivi d'instruction et sa robustesse en français sont inférieurs à un 3B/7B plus récent.
- Le prompt RAG interdit de répondre hors du contexte stocké. Une réponse « je ne sais pas » peut être une décision de grounding, pas une panne du modèle.
- L'interface appelle actuellement `/ask` alors que le endpoint enrichi `/api/v1/chat` possède la détection d'événements côté backend. Cette divergence fonctionnelle doit être corrigée lors d'une future itération UI, mais ne bloque pas la migration GPU.

## 7. Préparation de Google Colab + GPU

### Choix recommandé

Séparer les responsabilités :

```text
Colab GPU
  - entraînement QLoRA de Qwen2.5-3B-Instruct
  - évaluation et export de l'adaptateur
  - éventuellement serveur d'inférence temporaire

Machine Brainy / serveur de production
  - FastAPI + interface web + SQLite + Chroma
  - soit Ollama avec modèle fusionné GGUF,
  - soit endpoint vLLM/Transformers distant configurable
```

Colab est adapté à l'entraînement et aux tests, mais n'est pas un hébergement permanent fiable : sessions éphémères, URL/tunnel changeant et stockage temporaire. Exporter les artefacts vers Google Drive ou un stockage versionné autorisé à la fin de chaque session.

### Procédure Colab pour le fine-tuning

1. Utiliser un runtime GPU NVIDIA et vérifier `torch.cuda.is_available()`.
2. Copier seulement les fichiers nécessaires : `scripts/train_darija_lora.py`, `requirements-train.txt`, le dataset et éventuellement la documentation. Ne jamais téléverser `.env`, les bases SQLite/Chroma privées, `data/`, le token gateway ou les journaux.
3. Installer une version CUDA de PyTorch compatible, puis `requirements-train.txt`.
4. Lancer le script avec le dataset ; l'objectif par défaut nécessite au minimum 8 Go VRAM, 12 Go ou plus étant préférable.
5. Télécharger/sauvegarder `artifacts/darija-lora` : adaptateur Safetensors, configuration PEFT, tokenizer et métriques d'évaluation.
6. Évaluer en Darija, français et anglais avant toute intégration. Vérifier le respect des consignes RAG et les hallucinations.

### Deux options d'inférence après entraînement

#### Option A — Conserver Ollama (recommandée si local-first)

1. Fusionner l'adaptateur PEFT avec `Qwen2.5-3B-Instruct` dans un environnement Transformers GPU.
2. Convertir le modèle fusionné au format GGUF avec l'outillage compatible Qwen/llama.cpp.
3. Quantifier (souvent Q4_K_M pour le compromis RAM/vitesse) puis créer un modèle Ollama avec un `Modelfile`.
4. Changer `OLLAMA_MODEL` vers le nom du modèle Brainy fusionné.
5. Garder `OllamaProvider` inchangé ; le reste de Brainy n'a pas à connaître le modèle.

Avantage : changement minimal du code. Inconvénient : la conversion et la qualité après quantification doivent être validées.

#### Option B — Endpoint GPU Transformers/vLLM

1. Héberger Qwen + adaptateur PEFT sur un GPU (Colab seulement pour prototype, VM GPU pour production).
2. Exposer une API compatible OpenAI ou une API dédiée sécurisée.
3. Ajouter un fournisseur, par exemple `VllmProvider`, qui implémente le protocole `ChatProvider` dans `router/providers.py`.
4. Ajouter une variable `BRAINY_LLM_PROVIDER`/URL/token, stockée uniquement dans `.env` ou les secrets de l'hébergeur.
5. Conserver `ModelRouter`, RAG, API et frontend inchangés au-dessus de cette couche.

Avantage : très bonnes performances GPU sans conversion GGUF. Inconvénients : coûts, réseau, sécurité des notes envoyées au serveur distant et disponibilité du service.

### Ajustements recommandés avant migration

| Priorité | Action | Justification |
|---|---|---|
| Haute | Décider si le modèle cible est Llama/Ollama ou Qwen/LoRA. | Évite de financer un entraînement Qwen jamais utilisé par Brainy. |
| Haute | Ajouter un test d'intégration pour le fournisseur GPU choisi. | Vérifie prompts, streaming, erreurs et timeouts. |
| Haute | Ne jamais copier `.env` dans un notebook ou dépôt public. | Il contient des secrets. Utiliser les secrets Colab ou variables d'environnement. |
| Haute | Exporter l'adaptateur, tokenizer et métriques après l'entraînement. | Colab est éphémère. |
| Moyenne | Ajouter le streaming de tokens (SSE/WebSocket) à FastAPI et l'UI. | Réduit fortement la perception de latence même si la génération totale reste longue. |
| Moyenne | Précharger l'embedder et le modèle au démarrage. | Évite le coût de la première requête utilisateur. |
| Moyenne | Instrumenter les temps retrieval/LLM/total. | Permet de distinguer vraie régression modèle et recherche mémoire lente. |
| Moyenne | Aligner l'UI sur `/api/v1/chat`. | Centralise la détection d'événements et l'identifiant de conversation. |
| Basse | Évaluer un embedding multilingue si Darija/français est prioritaire. | `all-MiniLM-L6-v2` n'est pas nécessairement optimal pour cette langue. |

## 8. Commandes utiles (sans secrets)

```powershell
# Lancer l'API et l'interface locale
& "venv\Scripts\python.exe" -m uvicorn brainy.interfaces.api:app --host 127.0.0.1 --port 8000

# Vérifier les modèles Ollama locaux
ollama list

# Vérifier la disponibilité d'Ollama
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:11434/api/tags

# Exécuter les tests pertinents API/RAG
& "venv\Scripts\python.exe" -m pytest tests\test_api.py tests\test_api_v1.py tests\test_rag.py -q

# Entraîner l'adaptateur sur une machine CUDA / Colab
python scripts/train_darija_lora.py --dataset docs/darija_marocaine_latin_10000.jsonl --output-dir artifacts/darija-lora
```

## 9. Conclusion

Brainy possède une base RAG modulaire déjà prête à être reliée à une infrastructure GPU, car toute la génération de chat passe par `OllamaProvider`/`ModelRouter`. La migration la moins risquée consiste à conserver cette abstraction et à remplacer uniquement le runtime du fournisseur de chat.

Pour les performances immédiates locales, `llama3.2:1b` est le choix actif le plus raisonnable. Pour un assistant d'étude Darija de meilleure qualité, la voie cohérente est : entraîner l'adaptateur QLoRA Qwen sur Colab, l'évaluer, puis soit le fusionner et le servir via Ollama, soit implémenter un fournisseur GPU distant clairement configuré et sécurisé.
