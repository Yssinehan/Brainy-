# Web Development - Guide Complet

## C'est quoi le Web Development?

Le Web Development est la création de sites web et applications web. Il comprend:
- **Frontend** - Interface utilisateur (HTML, CSS, JavaScript)
- **Backend** - Logique serveur (Python, Node.js, Java)
- **Bases de données** - Stockage des données (SQL, NoSQL)

## HTML - Structure

HTML = HyperText Markup Language. C'est la structure d'une page web.

```html
<!DOCTYPE html>
<html>
<head>
    <title>Ma Page</title>
</head>
<body>
    <h1>Bienvenue</h1>
    <p>Ceci est un paragraphe.</p>
    <a href="https://example.com">Lien</a>
</body>
</html>
```

### Éléments communs:
- `<h1>` à `<h6>` - Titres
- `<p>` - Paragraphes
- `<a>` - Liens
- `<button>` - Boutons
- `<form>` - Formulaires
- `<div>` - Conteneurs

## CSS - Style

CSS = Cascading Style Sheets. Ça rend une page belle.

```css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: blue;
    font-size: 32px;
}

.button {
    background-color: green;
    color: white;
    padding: 10px 20px;
    border: none;
    cursor: pointer;
}
```

### Flexbox - Mise en page
```css
.container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}
```

## JavaScript - Interactivité

JavaScript rend une page interactive.

```javascript
// Sélectionner un élément
const button = document.getElementById("myButton");

// Ajouter un événement
button.addEventListener("click", function() {
    alert("Bouton cliqué!");
});

// Modifier le contenu
document.getElementById("title").textContent = "Nouveau Titre";
```

## Frameworks Frontend

- **React** - UI composants
- **Vue.js** - Simple et progressif
- **Angular** - Framework complet
- **Svelte** - Compilation du JS

## Frameworks Backend

- **Flask** (Python) - Micro-framework
- **Django** (Python) - Framework complet
- **Express** (Node.js) - Minimaliste
- **FastAPI** (Python) - Moderne, rapide

## Bases de Données

### SQL (Relationnel)
```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

SELECT * FROM users WHERE name = "Alice";
```

### NoSQL (Document)
```json
{
    "_id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "hobbies": ["lecture", "coding"]
}
```

## API REST

Une API REST permet à d'autres applications d'utiliser vos données.

```
GET /users           - Récupérer tous les utilisateurs
GET /users/1         - Récupérer utilisateur #1
POST /users          - Créer un utilisateur
PUT /users/1         - Modifier utilisateur #1
DELETE /users/1      - Supprimer utilisateur #1
```

## Déploiement

- **Vercel** - Frontend (React, Next.js)
- **Heroku** - Backend (Python, Node.js)
- **AWS** - Cloud complet
- **DigitalOcean** - VPS simple

## Bonnes Pratiques

1. Responsive design (mobile-friendly)
2. Sécurité (HTTPS, validation)
3. Performance (minification, cache)
4. Accessibilité (WCAG)
5. Testing (unit, integration)
