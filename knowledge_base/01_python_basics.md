# Python Basics - Guide Complet

## Qu'est-ce que Python?

Python est un langage de programmation interprété, haut niveau, dynamique. Créé en 1989 par Guido van Rossum, il est connu pour sa syntaxe simple et lisible.

### Avantages de Python:
- Syntaxe facile à apprendre
- Communauté très grande
- Librairies puissantes (NumPy, Pandas, TensorFlow)
- Utilisé en Data Science, AI, Web Development

## Variables et Types

```python
# Entiers
age = 25
nombre = 1000

# Strings (texte)
nom = "Alice"
message = "Bonjour le monde"

# Booléens
actif = True
inactif = False

# Listes
fruits = ["pomme", "banane", "orange"]
nombres = [1, 2, 3, 4, 5]

# Dictionnaires
personne = {
    "nom": "Alice",
    "age": 25,
    "ville": "Paris"
}
```

## Fonctions

```python
def saluer(nom):
    """Cette fonction salue quelqu'un"""
    return f"Bonjour {nom}!"

result = saluer("Alice")
print(result)  # Bonjour Alice!
```

## Boucles

### Boucle For
```python
for fruit in ["pomme", "banane", "orange"]:
    print(f"J'aime la {fruit}")
```

### Boucle While
```python
compteur = 0
while compteur < 5:
    print(compteur)
    compteur += 1
```

## Conditions

```python
age = 18

if age >= 18:
    print("Vous êtes majeur")
elif age >= 13:
    print("Vous êtes adolescent")
else:
    print("Vous êtes enfant")
```

## Listes et Compréhensions

```python
# Compréhension de liste
carrés = [x**2 for x in range(1, 6)]
# Résultat: [1, 4, 9, 16, 25]

# Filtrer
pairs = [x for x in range(10) if x % 2 == 0]
# Résultat: [0, 2, 4, 6, 8]
```

## Modules Courants

- `os` - Opérations système
- `sys` - Paramètres système
- `json` - Traiter JSON
- `requests` - Requêtes HTTP
- `datetime` - Dates et heures

## Bonnes Pratiques

1. **Utiliser des noms explicites** pour variables
2. **Commenter le code complexe**
3. **Respecter PEP 8** (guide de style)
4. **Tester votre code**
5. **Utiliser des fonctions** pour réutiliser du code

## Conseils d'apprentissage

- Pratiquez régulièrement
- Lisez le code des autres
- Participez à la communauté
- Faites de petits projets
- Utilisez Python pour des vrais problèmes
