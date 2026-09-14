# Entraînement Darija (GPU cloud)

Le script `scripts/train_darija_lora.py` entraîne un adaptateur QLoRA à partir de
`docs/darija_marocaine_latin_10000.jsonl`. Le fichier contient actuellement 789
conversations au format `{"messages": [...]}`. Il n'entraîne pas les poids complets :
l'artefact final dépend donc toujours du modèle de base.

Le modèle choisi par défaut est `Qwen/Qwen2.5-3B-Instruct`, un modèle multilingue
accessible publiquement. Une instance Linux NVIDIA avec 8 Go de VRAM est le minimum
pratique ; 12 Go ou plus est préférable. Le script arrête l'exécution sans CUDA afin
d'éviter un entraînement CPU involontaire.

## Sur la machine GPU

1. Clonez le dépôt et copiez-y le dataset si nécessaire.
2. Installez Python 3.11 ou 3.12 et le pilote NVIDIA compatible CUDA.
3. Installez PyTorch correspondant à la version CUDA de la machine, puis les autres
   dépendances :

```bash
pip install --upgrade pip
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements-train.txt
python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
```

4. Lancez l'entraînement :

```bash
python scripts/train_darija_lora.py \
  --dataset docs/darija_marocaine_latin_10000.jsonl \
  --output-dir artifacts/darija-lora
```

Les sorties incluent `adapter_model.safetensors`, `adapter_config.json`, le tokenizer
et les deux derniers checkpoints. Ne publiez pas automatiquement l'adaptateur ou le
dataset si vous n'avez pas vérifié ses droits d'utilisation.

## Ajustements utiles

- Réduisez `--batch-size` à `1` en cas d'erreur mémoire ; conservez ou augmentez
  `--gradient-accumulation` pour garder une taille de lot effective suffisante.
- Réduisez `--max-seq-length` à `256` si la VRAM est limitée.
- Changez `--base-model` uniquement vers un modèle de type causal ayant un vrai chat
  template et dont la licence vous autorise l'usage prévu.

Le dépôt principal Brainy emploie aujourd'hui Ollama/Gemini. Pour utiliser l'adaptateur
entraîné, servez-le avec Transformers/vLLM ou fusionnez-le avec le modèle de base avant
une conversion GGUF/Ollama ; cette étape dépend du serveur d'inférence retenu.
