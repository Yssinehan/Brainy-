# 🧠 BRAINY - GUIDE COMPLET & FINAL

**Installation réussie!** ✅✅✅

Tout est prêt. Voici le guide complet pour utiliser BRAINY, ton second cerveau IA.

---

## 📋 TABLE DES MATIÈRES

1. [Ce que tu as accompli](#accomplissements)
2. [Comment utiliser BRAINY](#comment-utiliser)
3. [Structure du projet](#structure)
4. [Commandes complètes](#commandes)
5. [Cas d'usage réels](#cas-usage)
6. [Tips & Astuces](#tips)
7. [Documentation](#documentation)

---

## ✅ CE QUE TU AS ACCOMPLI {#accomplissements}

| Étape | Statut | Détails |
|-------|--------|---------|
| 1️⃣ Environnement virtuel + Dépendances | ✅ DONE | Python 3.12, venv, pip install |
| 2️⃣ Renommage (personal_llm → brainy) | ✅ DONE | Tous les fichiers renommés |
| 3️⃣ Tests de validation | ✅ DONE | **168/168 tests passent** |
| 4️⃣ Configuration Gemini API | ✅ DONE | API key setup, modèle gemini-3.5-flash-lite |
| 5️⃣ Tests finaux + Interface Web | ✅ DONE | CLI ✅ Web ✅ API ✅ |

---

## 🚀 COMMENT UTILISER BRAINY {#comment-utiliser}

### **MODE 1️⃣ - CLI (Ligne de Commande)**

La façon la plus simple pour tester rapidement.

#### Activation de l'environnement:

```powershell
cd "C:\Users\Elitebook\Desktop\Brainy Model"
& "venv\Scripts\Activate.ps1"
```

Tu dois voir `(venv)` au début du prompt ✅

#### Commandes disponibles:

```powershell
# 1. Ingérer des fichiers (mémoire)
python -m brainy.interfaces.cli ingest "chemin/fichier.md"
python -m brainy.interfaces.cli ingest "chemin/fichier.pdf"
python -m brainy.interfaces.cli ingest "dossier/*.md"  # Plusieurs fichiers

# 2. Rechercher dans la mémoire (sans IA)
python -m brainy.interfaces.cli recall "ma question?"
python -m brainy.interfaces.cli recall "topic" -k 10  # Top 10 résultats

# 3. Poser une question (avec réponse IA générée)
python -m brainy.interfaces.cli ask "Qu'ai-je dans ma mémoire?"
python -m brainy.interfaces.cli ask "Résume mes notes" --verify  # Multi-provider

# 4. Voix - Transcriber l'audio (local, gratuit)
python -m brainy.interfaces.cli transcribe "recording.wav"
python -m brainy.interfaces.cli ask-voice "recording.wav"
python -m brainy.interfaces.cli ask-voice "recording.wav" --speak  # Audio réponse

# 5. Vision - Décrire une image
python -m brainy.interfaces.cli describe-image "photo.jpg"
python -m brainy.interfaces.cli describe-image "screenshot.png"

# 6. Tendances - Topics tu lis plus
python -m brainy.interfaces.cli trends
python -m brainy.interfaces.cli trends --days 7

# 7. Revue - Résumé de ton activité
python -m brainy.interfaces.cli review --days 7
python -m brainy.interfaces.cli self-review --days 7

# 8. Agent autonome (avec permission)
python -m brainy.interfaces.cli agent "Fais quelquechose"
python -m brainy.interfaces.cli agent "Look up X" --allow-network

# 9. Infos
python -m brainy.interfaces.cli --version
python -m brainy.interfaces.cli --help
```

---

### **MODE 2️⃣ - WEB (Interface Streamlit)**

Interface graphique interactive dans le navigateur.

```powershell
# Depuis le dossier BRAINY avec (venv) activé
python -m streamlit run src/brainy/interfaces/app.py
```

✅ S'ouvre automatiquement à: **http://localhost:8501**

**Fonctionnalités:**
- 💬 Chat avec BRAINY
- 📝 Ingérer des fichiers
- 🔍 Rechercher dans la mémoire
- 📊 Voir les stats de mémoire
- 🎤 Voix intégrée
- 📸 Vision intégrée

**Arrêter:** `Ctrl+C` dans PowerShell

---

### **MODE 3️⃣ - API HTTP (FastAPI)**

Pour intégrations avec d'autres apps.

```powershell
# Démarrer le serveur
python -m uvicorn brainy.interfaces.api:app --reload
```

✅ API disponible à: **http://localhost:8000**
✅ Documentation interactive: **http://localhost:8000/docs**

**Endpoints:**
- `POST /ingest` - Ingérer du texte
- `GET /search` - Chercher dans la mémoire
- `POST /ask` - Poser une question
- `POST /remember` - Ajouter à la mémoire

**Arrêter:** `Ctrl+C` dans PowerShell

---

## 📂 STRUCTURE DE BRAINY {#structure}

```
C:\Users\Elitebook\Desktop\Brainy Model\
│
├── src/brainy/                      # 🧠 CODE PRINCIPAL
│   ├── interfaces/
│   │   ├── cli.py                  # Interface ligne de commande
│   │   ├── app.py                  # Interface Streamlit
│   │   └── api.py                  # API FastAPI
│   │
│   ├── core/
│   │   ├── memory.py               # Moteur mémoire (RAG)
│   │   ├── retrieval.py            # Récupération sémantique
│   │   ├── agent.py                # Agent autonome
│   │   └── router.py               # Routeur modèles IA
│   │
│   ├── integrations/               # Intégrations externes
│   ├── config.py                   # Configuration globale
│   ├── engine.py                   # Moteur principal
│   └── __init__.py
│
├── tests/                           # 🧪 TESTS (168/168 ✅)
│   ├── test_ingest.py
│   ├── test_agent.py
│   ├── test_api.py
│   └── ...
│
├── docs/                            # 📚 DOCUMENTATION
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── PRD.md
│   ├── TDD.md
│   └── DECISIONS/
│
├── data/                            # 💾 TA MÉMOIRE (auto-créée)
│   ├── brainy.db                   # Base données (SQLite)
│   ├── chroma/                     # Vecteurs (embeddings)
│   ├── workspace/                  # Fichiers temporaires
│   ├── voice/                      # Transcriptions audio
│   └── test.md                     # Fichier test
│
├── venv/                            # 🐍 ENVIRONNEMENT PYTHON
│   ├── Scripts/
│   │   └── Activate.ps1            # Activation (Windows)
│   └── Lib/site-packages/          # Dépendances
│
├── .env                             # 🔑 CONFIGURATION SECRETS
│   └── GEMINI_API_KEY=...
│
├── .env.example                     # Template .env
├── pyproject.toml                   # Config du projet
├── setup.py                         # Installation
├── requirements.txt                 # Dépendances
├── README.md                        # Docs (renommée)
└── LICENSE                          # MIT

```

---

## 🎯 COMMANDES COMPLÈTES {#commandes}

### **Ingestion (Ajouter à la mémoire)**

```powershell
# Fichier unique
python -m brainy.interfaces.cli ingest "C:\Mes Notes\note.md"

# Plusieurs fichiers
python -m brainy.interfaces.cli ingest "C:\Mes Notes\*.md"

# PDF
python -m brainy.interfaces.cli ingest "document.pdf"

# Image (OCR automatique)
python -m brainy.interfaces.cli ingest "screenshot.png"

# Tous les formats à la fois
python -m brainy.interfaces.cli ingest "dossier/*"
```

**Résultat:** Fichiers indexés dans `data/brainy.db` et vecteurs dans `data/chroma/`

---

### **Recherche (Recall - Pas d'IA)**

```powershell
# Recherche simple
python -m brainy.interfaces.cli recall "Python"

# Plus de résultats
python -m brainy.interfaces.cli recall "Python" -k 10

# Recherche avancée
python -m brainy.interfaces.cli recall "Comment faire X?" -k 5
```

**Résultat:** Top K résultats de la mémoire avec citations

---

### **Questions (Ask - Avec IA)**

```powershell
# Question simple
python -m brainy.interfaces.cli ask "Qui suis-je?"

# Question complexe
python -m brainy.interfaces.cli ask "Résume tout ce que je sais sur Python"

# Avec vérification multi-provider
python -m brainy.interfaces.cli ask "Ma question?" --verify

# Question avec contexte
python -m brainy.interfaces.cli ask "En fonction de mes notes, qu'est-ce que je dois faire?"
```

**Résultat:** 
- Réponse générée par Gemini
- Sources citées (fichiers d'origine)
- Basée sur ta mémoire

---

### **Voix (Speech)**

```powershell
# Transcriber un audio
python -m brainy.interfaces.cli transcribe "recording.wav"

# Poser une question par audio (local, gratuit)
python -m brainy.interfaces.cli ask-voice "recording.wav"

# Avec réponse audio (TTS)
python -m brainy.interfaces.cli ask-voice "recording.wav" --speak
```

**Avantages:**
- ✅ Local (pas d'API OpenAI)
- ✅ Gratuit
- ✅ Offline
- ✅ Faster-whisper (rapide)

---

### **Vision (Images)**

```powershell
# Décrire une image
python -m brainy.interfaces.cli describe-image "photo.jpg"

# OCR automatique lors de l'ingestion
python -m brainy.interfaces.cli ingest "screenshot.png"
```

---

### **Tendances & Review**

```powershell
# Topics que tu lis plus (derniers 7 jours vs avant)
python -m brainy.interfaces.cli trends --days 7

# Revue de la mémoire (résumé IA)
python -m brainy.interfaces.cli review --days 7

# Revue de l'activité du système (audit log, pas d'IA)
python -m brainy.interfaces.cli self-review --days 7
```

---

### **Agent (Autonome)**

```powershell
# Agent simple (lecture seule)
python -m brainy.interfaces.cli agent "Qu'est-ce que je dois faire?"

# Agent avec réseau (avec permission)
python -m brainy.interfaces.cli agent "Look up X on example.com" --allow-network

# Agent avancé (tous les outils)
python -m brainy.interfaces.cli agent "Task complexe" --allow-network
```

---

### **Gestion du Projet**

```powershell
# Vérifier la version
python -m brainy.interfaces.cli --version
# → BRAINY 1.0.0

# Aide
python -m brainy.interfaces.cli --help

# Lancer les tests
python -m pytest tests/ -q
# → 168 passed ✅

# Réinstaller après modifications
pip install -e .

# Réinitialiser la mémoire (⚠️ SUPPRIME TOUT)
rm -r data/
```

---

## 💡 CAS D'USAGE RÉELS {#cas-usage}

### **CAS 1: Gestionnaire de Notes Personnel**

```powershell
# Jour 1 - Ingère tes notes
python -m brainy.interfaces.cli ingest "C:\Mes Notes\*.md"
python -m brainy.interfaces.cli ingest "C:\Téléchargements\*.pdf"

# Jour 2 - Cherche une info
python -m brainy.interfaces.cli recall "Comment configurer Docker?"

# Jour 3 - Question complète
python -m brainy.interfaces.cli ask "Résume ce que j'ai appris sur Docker"
```

---

### **CAS 2: Assistant de Recherche**

```powershell
# Ingère articles/papiers de recherche
python -m brainy.interfaces.cli ingest "research_papers/*.pdf"

# Pose des questions complexes
python -m brainy.interfaces.cli ask "Quels sont les themes communs entre ces papiers?"

# Vérification
python -m brainy.interfaces.cli ask "Vérifie la conclusion" --verify
```

---

### **CAS 3: Journaling + Analyse**

```powershell
# Ingère tes journaux
python -m brainy.interfaces.cli ingest "journals/2024/*.md"

# Voix - Journalier vocal
python -m brainy.interfaces.cli ask-voice "daily_entry.wav" --speak

# Tendances
python -m brainy.interfaces.cli trends --days 30

# Revue de mois
python -m brainy.interfaces.cli review --days 30
```

---

### **CAS 4: Knowledge Base d'Équipe**

```powershell
# Setup: Ingère docs projet
python -m brainy.interfaces.cli ingest "project_docs/*.md"

# Onboarding: Nouveau membre pose questions
python -m brainy.interfaces.cli ask "Comment marche l'architecture?"

# Vérif: Multi-provider
python -m brainy.interfaces.cli ask "C'est correct?" --verify
```

---

### **CAS 5: Agent Autonome**

```powershell
# L'agent trouve l'info tout seul
python -m brainy.interfaces.cli agent "Fais un résumé de ce que j'ai lu cette semaine"

# Avec accès réseau
python -m brainy.interfaces.cli agent "Cherche la dernière news sur AI" --allow-network
```

---

## 🎯 TIPS & ASTUCES {#tips}

### **💡 Tip 1: Organisation des fichiers**

```powershell
# Crée une structure claire
C:\Users\Elitebook\Desktop\Brainy Model\data\
├── notes/
│   ├── python/
│   ├── ai/
│   └── personal/
├── articles/
├── pdfs/
└── projects/

# Ingère par dossier
python -m brainy.interfaces.cli ingest "data/notes/python/*.md"
```

---

### **💡 Tip 2: Mots-clés efficaces pour recall**

```powershell
# ✅ Bon
python -m brainy.interfaces.cli recall "Python decorators"

# ❌ Mauvais (trop vague)
python -m brainy.interfaces.cli recall "stuff"

# ✅ Très bon (avec contexte)
python -m brainy.interfaces.cli recall "How to implement caching in Python?"
```

---

### **💡 Tip 3: Combiner CLI et Web**

```powershell
# Terminal 1 - Lancer l'API
python -m uvicorn brainy.interfaces.api:app --reload

# Terminal 2 - Lancer la Web UI
python -m streamlit run src/brainy/interfaces/app.py

# Maintenant tu as les 3 modes en même temps!
```

---

### **💡 Tip 4: Automatiser l'ingest**

```powershell
# Ingère TOUT au démarrage
python -m brainy.interfaces.cli ingest "C:\Mes Documents\*"
python -m brainy.interfaces.cli ingest "C:\Téléchargements\*"
python -m brainy.interfaces.cli ingest "C:\Bureau\*"

# Puis utilise via Web UI
python -m streamlit run src/brainy/interfaces/app.py
```

---

### **💡 Tip 5: Vérification multi-provider**

```powershell
# Demande à Gemini + Ollama si configuré
python -m brainy.interfaces.cli ask "Question importante?" --verify

# Si les réponses diffèrent = tu le vois (flag)
```

---

### **💡 Tip 6: Exporter ta mémoire**

```powershell
# La base de données est dans:
C:\Users\Elitebook\Desktop\Brainy Model\data\brainy.db

# Les vecteurs sont dans:
C:\Users\Elitebook\Desktop\Brainy Model\data\chroma\

# Fais des backups! 💾
```

---

### **💡 Tip 7: Changer de modèle IA**

```powershell
# Fichier: src/brainy/config.py

# Actuellement: Gemini
gemini_model: str = "gemini-3.5-flash-lite"

# Tu peux passer à Ollama (local, gratuit, offline)
# Voir docs/ARCHITECTURE.md pour détails
```

---

## 📚 DOCUMENTATION {#documentation}

### **Fichiers importants dans `docs/`:**

1. **ARCHITECTURE.md** - Architecture complète du système
   - Diagrammes
   - Flux de données
   - Composants
   - Database schema

2. **ROADMAP.md** - Feuille de route future
   - v0.1 → v0.2 → v0.3 → v1.0 → v2.0 → v3.0
   - Features en cours
   - Features futures

3. **PRD.md** - Product Requirements Document
   - Vision
   - Cas d'usage
   - Features

4. **TDD.md** - Technical Design Document
   - Decisions techniques
   - Trade-offs
   - Justifications

5. **DECISIONS/** - Architecture Decision Records (ADRs)
   - ADR 0001-0006
   - Chaque decision documentée

---

## 🔧 COMMANDES DE MAINTENANCE {#maintenance}

### **Environnement:**

```powershell
# Activer venv
& "venv\Scripts\Activate.ps1"

# Désactiver venv
deactivate

# Réinstaller dépendances
pip install --force-reinstall -r requirements.txt

# Upgrade pip
python -m pip install --upgrade pip

# Voir dépendances installées
pip list
```

---

### **Tests & Qualité:**

```powershell
# Tous les tests
python -m pytest tests/ -q

# Tests spécifiques
python -m pytest tests/test_ingest.py -q
python -m pytest tests/test_agent.py -v

# Tests avec couverture
python -m pytest tests/ --cov=src/brainy

# Test un fichier
python -m pytest tests/test_api.py::test_function_name -v
```

---

### **Debugging:**

```powershell
# Voir les logs
python -m brainy.interfaces.cli recall "test" -v

# Mode debug
$env:DEBUG=1
python -m brainy.interfaces.cli ask "test"

# Réinitialiser settings
# Supprimer .env et relancer
```

---

## 🎓 PROCHAINES ÉTAPES {#prochaines-etapes}

### **Immédiat (aujourd'hui):**
- [ ] Ingère **5 fichiers importants** 📝
- [ ] Teste **recall** sur une info 🔍
- [ ] Teste **ask** avec une vraie question 💭
- [ ] Explore l'**interface Web** 🌐

### **Court terme (cette semaine):**
- [ ] Ingère **toutes tes notes** 📚
- [ ] Utilise **ask** quotidiennement 📅
- [ ] Explore **trends** de ta lecture 📊
- [ ] Essaye **voice** pour journalier 🎤

### **Moyen terme (ce mois):**
- [ ] Configure **Ollama** pour modèles locaux 🤖
- [ ] Intègre avec **Claude API** ou autre IA 🔌
- [ ] Exporte/Backup ta mémoire 💾
- [ ] Lis **docs/ARCHITECTURE.md** pour détails 📖

### **Long terme (futur):**
- [ ] Multi-device sync (v3) 📱💻
- [ ] SDK & Marketplace (v3)
- [ ] Voice cloning (v3)
- [ ] Contribuer au projet! 🚀

---

## ❓ FAQ

### **Q: Ça supprime mes fichiers si j'ingère?**
R: Non! L'ingest **copie** dans BRAINY, tes fichiers originaux restent intacts. ✅

### **Q: Ça consomme beaucoup d'espace?**
R: Non! Base de données SQLite + vecteurs Chroma = ~1-2GB max. 💾

### **Q: Je peux utiliser d'autres modèles IA?**
R: Oui! Ollama (local), Claude, OpenAI, etc. Vois config.py et docs. 🤖

### **Q: C'est vraiment gratuit?**
R: Oui! Gemini free tier suffit. Ingérer/Recall sont 100% locaux. ✅

### **Q: Ça fonctionne offline?**
R: Oui! Sauf pour `ask` qui needing IA provider. Ollama est offline. 🔌

### **Q: Je peux réinitialiser?**
R: Oui! `rm -r data/` supprime tout et relance. ⚠️

---

## 🎉 CONCLUSION

**Bravo!** 🎊 Tu as maintenant:

✅ **BRAINY** - Ton second cerveau IA
✅ **Mémoire privée** - Tes données sont à toi
✅ **Récupération sémantique** - Retrouve ce dont tu as besoin
✅ **Réponses IA** - Conversations intelligentes
✅ **Voix & Vision** - Multimodal (local + Gemini)
✅ **Agent autonome** - BRAINY qui pense tout seul
✅ **Interface complète** - CLI + Web + API

---

## 📞 BESOIN D'AIDE?

- Explore `docs/` pour + de détails
- Lis les **Architectural Decision Records** (ADRs)
- Regarde les **tests** pour des exemples d'usage
- Contribue au projet sur GitHub! 🚀

---

## 🚀 FIRST STEPS (Copie/Colle):

```powershell
# 1. Navigue vers BRAINY
cd "C:\Users\Elitebook\Desktop\Brainy Model"

# 2. Active l'environnement
& "venv\Scripts\Activate.ps1"

# 3. Lance l'interface Web
python -m streamlit run src/brainy/interfaces/app.py

# 4. Ingère un fichier
python -m brainy.interfaces.cli ingest "data/test.md"

# 5. Pose une question
python -m brainy.interfaces.cli ask "Qu'ai-je dans ma mémoire?"

# 🎉 Voilà!
```

---

**Bonne chance! Amuse-toi avec BRAINY!** 🧠✨

*Dernière mise à jour: Septembre 2026*
*Installation: ✅ Réussie*
*Tests: ✅ 168/168 passés*
*Status: 🟢 Prêt à utiliser*
