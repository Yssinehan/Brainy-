# Databases - SQL vs NoSQL

## Types de Bases de Données

### Relationnel (SQL)
```
Structure: Tables avec lignes et colonnes
Exemples: PostgreSQL, MySQL, SQL Server, SQLite
Quand l'utiliser: Données structurées, relations
```

### Document (NoSQL)
```
Structure: Documents JSON
Exemples: MongoDB, Firebase, CouchDB
Quand l'utiliser: Données flexibles, scalabilité
```

### Key-Value
```
Exemples: Redis, Memcached
Quand l'utiliser: Cache, sessions, données rapides
```

### Graphe
```
Exemples: Neo4j
Quand l'utiliser: Réseaux sociaux, recommandations
```

## SQL - Langage Relationnel

### Créer une Table

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Select - Lire

```sql
-- Tous les utilisateurs
SELECT * FROM users;

-- Colonnes spécifiques
SELECT name, email FROM users;

-- Avec condition
SELECT * FROM users WHERE age > 18;

-- Ordre
SELECT * FROM users ORDER BY age DESC;

-- Limite
SELECT * FROM users LIMIT 10;
```

### Insert - Créer

```sql
INSERT INTO users (name, email, age)
VALUES ('Alice', 'alice@example.com', 25);

-- Plusieurs lignes
INSERT INTO users (name, email, age) VALUES
('Alice', 'alice@example.com', 25),
('Bob', 'bob@example.com', 30);
```

### Update - Modifier

```sql
UPDATE users
SET age = 26
WHERE name = 'Alice';
```

### Delete - Supprimer

```sql
DELETE FROM users
WHERE id = 1;
```

### Joins - Combiner Tables

```sql
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Inner Join
SELECT users.name, orders.amount
FROM users
INNER JOIN orders ON users.id = orders.user_id;

-- Left Join (tous users, orders si existe)
SELECT users.name, orders.amount
FROM users
LEFT JOIN orders ON users.id = orders.user_id;
```

### Agrégations

```sql
-- Count
SELECT COUNT(*) FROM users;

-- Sum
SELECT SUM(amount) FROM orders;

-- Average
SELECT AVG(age) FROM users;

-- Group By
SELECT age, COUNT(*) FROM users GROUP BY age;

-- Having (filter groups)
SELECT age, COUNT(*) as count
FROM users
GROUP BY age
HAVING COUNT(*) > 5;
```

## MongoDB - NoSQL

### Créer et Insérer

```javascript
// Créer collection et insérer
db.users.insertOne({
    name: "Alice",
    email: "alice@example.com",
    age: 25,
    hobbies: ["lecture", "coding"],
    address: {
        street: "123 Main St",
        city: "Paris"
    }
});

// Plusieurs documents
db.users.insertMany([
    { name: "Alice", age: 25 },
    { name: "Bob", age: 30 }
]);
```

### Lire

```javascript
// Tous
db.users.find();

// Avec condition
db.users.find({ age: { $gt: 25 } });

// Un seul
db.users.findOne({ name: "Alice" });

// Projection (colonnes)
db.users.find({}, { name: 1, age: 1 });
```

### Modifier

```javascript
// Update un
db.users.updateOne(
    { name: "Alice" },
    { $set: { age: 26 } }
);

// Update plusieurs
db.users.updateMany(
    { age: { $lt: 25 } },
    { $set: { verified: true } }
);
```

### Supprimer

```javascript
db.users.deleteOne({ name: "Alice" });
db.users.deleteMany({ age: { $lt: 18 } });
```

## Concepts Clés

### ACID (SQL)
- **Atomicity** - Tout ou rien
- **Consistency** - Données valides
- **Isolation** - Transactions indépendantes
- **Durability** - Données persistentes

### CAP Theorem (NoSQL)
```
Impossible d'avoir les 3:
- Consistency (cohérence)
- Availability (disponibilité)
- Partition tolerance (résilience)
```

## Indexing

```sql
-- Créer un index (SQL)
CREATE INDEX idx_email ON users(email);

-- Utilisation
SELECT * FROM users WHERE email = 'alice@example.com';
```

```javascript
// MongoDB
db.users.createIndex({ email: 1 });
```

## ORM - Object-Relational Mapping

**Python (SQLAlchemy)**
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Create
user = User(name="Alice", email="alice@example.com")
session.add(user)
session.commit()

# Read
users = session.query(User).filter(User.age > 18).all()

# Update
user.age = 26
session.commit()

# Delete
session.delete(user)
session.commit()
```

## Bonnes Pratiques

1. **Indexer les colonnes** frequently queried
2. **Normaliser** les données (SQL)
3. **Dénormaliser** quand besoin de performance
4. **Backups réguliers**
5. **Versionner migrations**
6. **Monitorer queries lentes**
7. **Security**: Prepared statements contre SQL injection
