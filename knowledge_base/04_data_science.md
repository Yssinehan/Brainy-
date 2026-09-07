# Data Science - Guide Complet

## Qu'est-ce que la Data Science?

Data Science = Extraction d'insights à partir de données. C'est l'intersection de:
- Statistiques
- Programmation
- Mathématiques
- Domaine métier

## Cycle d'un projet Data Science

### 1. Définir la Question
```
Qu'est-ce qu'on veut prédire/comprendre?
Exemples:
- Quels clients vont partir?
- Comment prédire les ventes?
- Quel est le sentiment des clients?
```

### 2. Collecte des Données
```
Où trouver les données?
- Bases de données
- APIs
- Web scraping
- Fichiers CSV/Excel
- Capteurs
```

### 3. Nettoyage (Data Cleaning)
```
Préparer les données:
- Supprimer valeurs manquantes
- Corriger les erreurs
- Standardiser formats
- Supprimer duplicatas
```

### 4. Exploration (EDA - Exploratory Data Analysis)
```
Comprendre les données:
- Statistiques descriptives
- Visualisations
- Corrélations
- Patterns
```

### 5. Feature Engineering
```
Créer nouvelles variables utiles:
- Transformer données
- Combiner features
- Normaliser/Standardiser
```

### 6. Modélisation
```
Entraîner un modèle:
- Choisir algorithme
- Split train/test
- Entraîner
- Hyperparameters tuning
```

### 7. Évaluation
```
Mesurer la performance:
- Accuracy, Precision, Recall
- MAE, RMSE (régression)
- ROC-AUC
- Validation croisée
```

### 8. Déploiement
```
Mettre en production:
- API FastAPI
- Pipeline automatique
- Monitoring
- Maintenance
```

## Outils populaires

### Langage
- **Python** - Standard dans l'industrie
- **R** - Statistiques, visualisations
- **SQL** - Requêter bases de données

### Librairies Python

```python
import pandas as pd          # Dataframes
import numpy as np           # Mathématiques
import matplotlib.pyplot as plt  # Visualisations
import seaborn as sns        # Visualisations belles
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import tensorflow as tf      # Deep Learning
```

### Exemple d'Analyse

```python
import pandas as pd

# Charger données
df = pd.read_csv('customers.csv')

# Statistiques
print(df.describe())
print(df.info())

# Filtrer
high_value = df[df['spending'] > 1000]

# Grouper
by_region = df.groupby('region')['spending'].mean()

# Visualiser
import matplotlib.pyplot as plt
df['age'].hist()
plt.show()
```

## Algos de Classification

**Quand on veut prédire une catégorie**

```
Exemples: Spam/Pas spam, Churn/Stay, 0/1
```

- **Logistic Regression** - Simple, rapide
- **Decision Trees** - Interprétable
- **Random Forest** - Robuste
- **SVM** - Puissant
- **Neural Networks** - Flexible

## Algos de Régression

**Quand on veut prédire un nombre**

```
Exemples: Prix, Température, Ventes
```

- **Linear Regression** - Simple
- **Ridge/Lasso** - Régularisé
- **Random Forest Regressor** - Robuste
- **Gradient Boosting** - Puissant

## Clustering

**Quand on veut grouper les données**

```
Exemples: Segments clients, Taxonomies
```

- **K-Means** - Rapide, simple
- **Hierarchical** - Dendrogramme
- **DBSCAN** - Formes complexes
- **Gaussian Mixture** - Probabiliste

## Métriques

### Classification
- **Accuracy** - % correct
- **Precision** - % positifs vrais
- **Recall** - % positifs trouvés
- **F1-Score** - Moyenne harmonique
- **ROC-AUC** - Courbe ROC

### Régression
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **R²** - Coefficient de détermination

## Bases de Données pour Data Science

### SQL
```sql
SELECT customer_id, SUM(amount) as total_spent
FROM orders
WHERE order_date > '2024-01-01'
GROUP BY customer_id
HAVING SUM(amount) > 1000
ORDER BY total_spent DESC;
```

### NoSQL
```python
# MongoDB
collection.find({'age': {'$gt': 25}})
```

## Bonnes Pratiques

1. **Comprendre le problème métier** avant les données
2. **Valider sur données indépendantes** (test set)
3. **Vérifier les biais** dans les données
4. **Documenter tout** - Processus, décisions
5. **Automatiser** le pipeline
6. **Monitorer** en production
7. **Communiquer** les résultats clairement

## Métiers Data Science

- **Data Scientist** - Modélisation
- **Data Analyst** - Analyse, visualisations
- **Data Engineer** - Pipelines, infrastructure
- **ML Engineer** - Production de modèles
- **Analytics Engineer** - Données + business

## Ressources d'Apprentissage

- **Kaggle** - Compétitions, datasets
- **DataCamp** - Cours interactifs
- **Andrew Ng** - Cours ML classique
- **Fast.ai** - Deep Learning accessible
- **Papers** - arXiv.org
