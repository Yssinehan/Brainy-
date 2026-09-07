# Git & GitHub - Guide Complet

## Qu'est-ce que Git?

Git = Système de contrôle de version. Permet de:
- Tracker les changements du code
- Collaborer avec d'autres
- Revenir à des versions précédentes
- Créer des branches

## Qu'est-ce que GitHub?

GitHub = Plateforme cloud pour Git. Permet de:
- Héberger repositories
- Collaborer
- Issues & Pull Requests
- CI/CD
- Portfolio public

## Concepts clés

### Repository (Repo)
```
Dossier de projet avec historique Git
```

### Commit
```
Snapshot du code à un moment
Chaque commit a: ID, auteur, message, date
```

### Branch
```
Ligne de développement indépendante
Exemple: main, develop, feature-xyz
```

### Merge
```
Combiner deux branches
Peut avoir des conflits à résoudre
```

### Pull Request (PR)
```
Demande pour fusionner une branche
Permet review du code
```

## Installation et Configuration

```bash
# Installer Git
# Windows: https://git-scm.com/download/win

# Configuration globale
git config --global user.name "Ton Nom"
git config --global user.email "ton@email.com"

# Vérifier
git config --list
```

## Commandes de Base

### Démarrer un Repo

```bash
# Créer un nouveau repo
git init

# Cloner un repo existant
git clone https://github.com/user/repo.git
cd repo
```

### Vérifier le Statut

```bash
# Voir l'état des fichiers
git status

# Voir l'historique
git log
git log --oneline

# Différences
git diff
```

### Ajouter et Commiter

```bash
# Ajouter un fichier
git add fichier.py

# Ajouter tous les fichiers
git add .

# Commiter
git commit -m "Feature: Add login function"

# Commiter et ajouter (seulement tracked files)
git commit -am "Fix: bug in validation"
```

### Branches

```bash
# Voir les branches
git branch

# Créer une branche
git branch feature-new

# Changer de branche
git checkout feature-new

# Créer et changer (shortcut)
git checkout -b feature-new

# Supprimer branche
git branch -d feature-new
```

### Merge

```bash
# Se placer sur main
git checkout main

# Merger feature
git merge feature-new

# Si conflits, les résoudre manuellement
# Puis: git add . && git commit
```

### Travail Distant

```bash
# Voir remotes
git remote -v

# Ajouter remote
git remote add origin https://github.com/user/repo.git

# Push vers GitHub
git push origin main

# Pull depuis GitHub
git pull origin main

# Push une nouvelle branche
git push -u origin feature-new
```

## Workflow Typique

```bash
# 1. Cloner le repo
git clone https://github.com/user/repo.git
cd repo

# 2. Créer une branche
git checkout -b feature-login

# 3. Faire changements
# ... éditer fichiers ...

# 4. Vérifier changements
git status
git diff

# 5. Commiter
git add .
git commit -m "Add login functionality"

# 6. Push
git push -u origin feature-login

# 7. Ouvrir Pull Request sur GitHub
# (interface GitHub)

# 8. Merge après review
git checkout main
git pull origin main
git merge feature-login
git push origin main
```

## Bonnes Pratiques

### Messages de Commit

```
✅ BON:
- feat: add user authentication
- fix: resolve memory leak in parser
- docs: update API documentation
- refactor: simplify data processing

❌ MAUVAIS:
- fix stuff
- update
- changes
- asdf
```

### Commits

```
✅ Commits petits et focalisés
✅ Un feature = une branche
✅ Commiter souvent
✅ Tester avant push

❌ Commits énormes
❌ Code non testé
❌ Commits sur main
```

### Branches

```
Nommage:
- feature/user-auth
- fix/login-bug
- docs/readme-update
- refactor/data-processing
```

## GitHub Features

### Issues
```
- Tracker bugs
- Proposer features
- Discussions
```

### Pull Requests
```
- Code review
- Discussion
- CI/CD checks
- Merge quand approved
```

### Workflows (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python -m pytest
```

### Releases
```
- Tagging versions
- Release notes
- Artifacts
```

## Commandes Avancées

```bash
# Rebase (réecrire l'historique)
git rebase main

# Stash (temporairement sauver)
git stash
git stash pop

# Cherry-pick (copier un commit)
git cherry-pick abc123

# Reset (annuler commits)
git reset --soft HEAD~1  # Garder changements
git reset --hard HEAD~1  # Supprimer changements

# Revert (créer un commit opposé)
git revert abc123
```

## Tips

1. **Commit souvent** - Plus facile à reverter
2. **Sync régulièrement** avec main
3. **Faire des PRs** même seul (documentation)
4. **Code review** les PRs
5. **Tag les versions** importantes
6. **Utiliser `.gitignore`** pour secrets
7. **Branching strategy** (Git Flow)

## Plateformes Alternatives

- **GitLab** - GitHub alternatif
- **Gitea** - Self-hosted
- **Bitbucket** - Atlassian
