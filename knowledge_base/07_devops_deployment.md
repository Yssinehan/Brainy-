# DevOps & Deployment

## Qu'est-ce que DevOps?

DevOps = Développement + Opérations
- Automation
- CI/CD (Continuous Integration/Deployment)
- Infrastructure as Code
- Monitoring

## Docker - Conteneurisation

Docker = Packager une app avec toutes ses dépendances dans un conteneur.

### Pourquoi Docker?

```
Problème: "Ça marche sur mon PC, pas en production"
Solution: Docker empaque tout dans une image
```

### Dockerfile

```dockerfile
FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### Docker Commands

```bash
# Créer une image
docker build -t myapp:1.0 .

# Lancer un conteneur
docker run -p 8000:8000 myapp:1.0

# Lister images
docker images

# Lister conteneurs
docker ps

# Arrêter
docker stop container_id

# Logs
docker logs container_id
```

## Docker Compose

Orchestrer plusieurs conteneurs.

```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Démarrer tous les services
docker-compose up

# Arrêter
docker-compose down
```

## CI/CD - Automatisation

### GitHub Actions

```yaml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: python -m pytest
      
      - name: Build Docker image
        run: docker build -t myapp:latest .
      
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: |
          docker push myapp:latest
          # Deploy commands
```

## Infrastructure as Code

### Terraform (exemple)

```hcl
provider "aws" {
  region = "eu-west-1"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  
  tags = {
    Name = "web-server"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}
```

## Déploiement Platforms

### Vercel (Frontend)

```bash
# Installation
npm i -g vercel

# Déployer
vercel
```

- Gratuit pour hobby projects
- Preview deployments sur PR
- Serverless functions
- Optimal pour Next.js, React

### Heroku (Backend)

```bash
heroku login
heroku create myapp
git push heroku main
heroku logs --tail
```

- Simple pour débuter
- Très cher maintenant
- Alternative: Railway, Render

### AWS (Cloud complet)

```
Services:
- EC2 - Serveurs
- RDS - Bases de données
- S3 - Stockage
- Lambda - Serverless
- CloudFront - CDN
```

### DigitalOcean (VPS simple)

```bash
# Créer un VPS (Droplet)
# Via interface web

# SSH
ssh root@your_ip

# Installer app
sudo apt update
sudo apt install python3-pip
pip install -r requirements.txt

# Démarrer avec systemd ou supervisord
```

## Monitoring & Logging

### Monitoring

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@request_duration.time()
def handler():
    request_count.inc()
    # ...
```

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Application started")
logger.error("Error occurred")
```

Services:
- **Datadog** - Monitoring complet
- **New Relic** - APM
- **ELK Stack** - Centralisé
- **CloudWatch** - AWS native

## Scaling

### Horizontal Scaling
```
Ajouter plus de serveurs
- Load balancer
- Database replication
- Cache (Redis)
```

### Vertical Scaling
```
Ajouter plus de ressources à un serveur
- Plus CPU
- Plus RAM
- Plus disque
```

## Bonnes Pratiques

1. **Infrastructure as Code** - Versioner config
2. **Automatiser tout** - Tests, déploiement
3. **Monitoring** - Alertes
4. **Logs centralisés** - Facile à debug
5. **Backups** - Régulier
6. **Secrets management** - Pas en code!
7. **Blue-Green deployment** - Zéro downtime
8. **Canary releases** - Progressive rollout

## Commandes Utiles

```bash
# Voir services
systemctl status

# Redémarrer app
systemctl restart myapp

# Logs
journalctl -u myapp -f

# Disk usage
df -h

# CPU/Memory
top
htop

# Network
netstat -tuln
ss -tuln
```
