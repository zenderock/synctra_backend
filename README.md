# Synctra Backend

Backend FastAPI modulaire pour la plateforme Synctra de gestion des liens dynamiques et analytics.

## 🚀 Fonctionnalités

- **Authentification JWT** avec rotation des tokens
- **Gestion des organisations** et utilisateurs avec avatars
- **Projets** avec clés API uniques
- **Liens dynamiques** avec détection de plateforme intelligente
- **Deferred Deep Linking** pour les applications mobiles
- **Analytics avancés** avec métriques et export CSV
- **Codes de parrainage** avec système de récompenses
- **Rate limiting** et sécurité renforcée
- **Cache Redis** pour les performances
- **API REST** complète avec documentation automatique

## 📦 Installation

### Avec Docker (Recommandé)

```bash
# Cloner le projet
git clone <repository-url>
cd synctra_backend

# Lancer avec Docker Compose
docker-compose up -d
```

### Installation manuelle

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations

# Lancer le serveur
uvicorn main:app --reload
```

## 🔧 Configuration

Copiez `.env.example` vers `.env` et configurez :

```bash
# Base de données PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/synctra

# Redis pour le cache
REDIS_URL=redis://localhost:6379

# Clé secrète pour JWT
SECRET_KEY=your-super-secret-key

# Domaine principal
DOMAIN=synctra.link
```

## 📚 API Documentation

Une fois le serveur lancé, accédez à :
- **Swagger UI** : http://localhost:8000/api/docs
- **ReDoc** : http://localhost:8000/api/redoc

## 🏗️ Architecture

```
app/
├── api/v1/endpoints/     # Endpoints API
├── core/                 # Configuration et utilitaires
├── models/              # Modèles SQLAlchemy
├── schemas/             # Schémas Pydantic
├── services/            # Logique métier
└── middleware/          # Middlewares personnalisés
```

## 🔐 Authentification

```python
# Inscription
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "Mon Entreprise"
}

# Connexion
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

## 🔗 Gestion des liens

```python
# Créer un lien dynamique
POST /api/v1/projects/{project_id}/links
{
  "original_url": "https://example.com/page",
  "title": "Mon lien",
  "android_package": "com.example.app",
  "ios_bundle_id": "com.example.app",
  "utm_source": "campaign"
}

# Redirection intelligente
GET /{short_code}
# Redirige automatiquement selon la plateforme détectée
```

## 📊 Analytics

```python
# Vue d'ensemble des analytics
GET /api/v1/projects/{project_id}/analytics/overview?days=30

# Analytics par lien
GET /api/v1/projects/{project_id}/analytics/links

# Export des données
GET /api/v1/projects/{project_id}/analytics/export?format=csv
```

## 🎯 Codes de parrainage

```python
# Créer un code de parrainage
POST /api/v1/projects/{project_id}/referrals
{
  "code": "WELCOME2024",
  "reward_type": "percentage",
  "reward_value": 10,
  "max_uses": 100
}

# Valider un code
POST /api/v1/projects/{project_id}/referrals/validate
{
  "code": "WELCOME2024"
}
```

## 🛡️ Sécurité

- **JWT** avec expiration courte et refresh tokens
- **Rate limiting** par IP et clé API
- **Validation stricte** des données d'entrée
- **Hash sécurisé** des mots de passe avec bcrypt
- **CORS** et **TrustedHost** configurés

## 🚀 Déploiement

### Production avec Docker

```bash
# Build de l'image
docker build -t synctra-backend .

# Lancement en production
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e SECRET_KEY=... \
  synctra-backend
```

### Variables d'environnement importantes

```bash
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ALLOWED_HOSTS=["yourdomain.com"]
```

## 📈 Performance

- **Cache Redis** pour les liens fréquemment accédés
- **Connection pooling** pour PostgreSQL
- **Rate limiting** intelligent
- **Pagination** optimisée
- **Index** sur les colonnes critiques

## 🧪 Tests

```bash
# Lancer les tests
pytest

# Avec couverture
pytest --cov=app
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.
