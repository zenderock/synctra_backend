# Spécifications Backend - Synctra

## Vue d'ensemble

Synctra est une plateforme SAAS pour la gestion des deeplinks et analytics. Cette documentation détaille les spécifications techniques pour l'équipe de développement backend.

## Architecture générale

### Stack technologique recommandé
- **API**: Node.js/Express ou Python/FastAPI
- **Base de données**: PostgreSQL (principal) + Redis (cache/sessions)
- **Authentification**: JWT + OAuth2
- **File d'attente**: Redis/Bull ou RabbitMQ
- **Stockage**: AWS S3 ou équivalent
- **Monitoring**: Prometheus + Grafana

## Modèles de données

### 1. Organisation
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255),
    plan_type VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);
```

### 2. Utilisateur
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) DEFAULT 'member',
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### 3. Projet
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(100) UNIQUE NOT NULL, -- Format: nom_projet_2024
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES organizations(id),
    api_key VARCHAR(255) UNIQUE NOT NULL, -- Format: sk_live_xxxx
    custom_domain VARCHAR(255),
    status VARCHAR(50) DEFAULT 'development',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_project_org (organization_id),
    INDEX idx_project_api_key (api_key)
);
```

### 4. Lien dynamique
```sql
CREATE TABLE dynamic_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    short_code VARCHAR(20) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    title VARCHAR(255),
    description TEXT,
    
    -- Configuration deeplink
    android_package VARCHAR(255),
    android_fallback_url TEXT,
    ios_bundle_id VARCHAR(255),
    ios_fallback_url TEXT,
    desktop_fallback_url TEXT,
    
    -- Paramètres UTM
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_term VARCHAR(100),
    utm_content VARCHAR(100),
    
    -- Métadonnées
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_link_project (project_id),
    INDEX idx_link_short_code (short_code),
    INDEX idx_link_created_by (created_by)
);
```

### 5. Analytics des clics
```sql
CREATE TABLE link_clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID REFERENCES dynamic_links(id),
    
    -- Informations utilisateur
    ip_address INET,
    user_agent TEXT,
    referer TEXT,
    
    -- Géolocalisation
    country VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    
    -- Détection de plateforme
    platform VARCHAR(50), -- android, ios, web, desktop
    device_type VARCHAR(50), -- mobile, tablet, desktop
    browser VARCHAR(100),
    os VARCHAR(100),
    
    -- Tracking de conversion
    converted BOOLEAN DEFAULT false,
    conversion_value DECIMAL(10,2),
    
    clicked_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_click_link (link_id),
    INDEX idx_click_date (clicked_at),
    INDEX idx_click_platform (platform)
);
```

### 6. Codes de parrainage
```sql
CREATE TABLE referral_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id), -- Créateur du code
    
    -- Configuration
    reward_type VARCHAR(50), -- percentage, fixed_amount, custom
    reward_value DECIMAL(10,2),
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_referral_project (project_id),
    INDEX idx_referral_code (code)
);
```

## APIs REST

### Authentification

#### POST /api/auth/register
```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "John",
  "lastName": "Doe",
  "organizationName": "Mon Entreprise"
}
```

#### POST /api/auth/login
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### POST /api/auth/refresh
```json
{
  "refreshToken": "jwt_refresh_token"
}
```

### Gestion des projets

#### GET /api/projects
Récupère tous les projets de l'organisation

#### POST /api/projects
```json
{
  "name": "Mon Projet",
  "description": "Description du projet",
  "customDomain": "links.mondomaine.com",
  "settings": {
    "enableAnalytics": true,
    "enableDeepLinking": true,
    "enableReferrals": true
  }
}
```

#### GET /api/projects/:projectId
Récupère les détails d'un projet

#### PUT /api/projects/:projectId
Met à jour un projet

#### DELETE /api/projects/:projectId
Supprime un projet

### Gestion des liens

#### GET /api/projects/:projectId/links
Récupère tous les liens d'un projet

#### POST /api/projects/:projectId/links
```json
{
  "originalUrl": "https://example.com/page",
  "title": "Titre du lien",
  "description": "Description",
  "androidPackage": "com.example.app",
  "androidFallbackUrl": "https://play.google.com/store/apps/details?id=com.example.app",
  "iosBundleId": "com.example.app",
  "iosFallbackUrl": "https://apps.apple.com/app/id123456789",
  "utmSource": "campaign",
  "utmMedium": "social",
  "utmCampaign": "launch",
  "expiresAt": "2024-12-31T23:59:59Z"
}
```

#### GET /api/projects/:projectId/links/:linkId
Récupère les détails d'un lien

#### PUT /api/projects/:projectId/links/:linkId
Met à jour un lien

#### DELETE /api/projects/:projectId/links/:linkId
Supprime un lien

### Redirection des liens

#### GET /:shortCode
Endpoint de redirection principal
- Détecte la plateforme (User-Agent)
- Enregistre le clic dans les analytics
- Redirige vers l'URL appropriée

### Analytics

#### GET /api/projects/:projectId/analytics/overview
```json
{
  "totalClicks": 1250,
  "totalLinks": 45,
  "conversionRate": 12.5,
  "topCountries": [...],
  "topPlatforms": [...],
  "clicksOverTime": [...]
}
```

#### GET /api/projects/:projectId/analytics/links
Analytics détaillées par lien

#### GET /api/projects/:projectId/analytics/export
Export des données analytics (CSV/JSON)

### Codes de parrainage

#### GET /api/projects/:projectId/referrals
Récupère tous les codes de parrainage

#### POST /api/projects/:projectId/referrals
```json
{
  "code": "WELCOME2024",
  "rewardType": "percentage",
  "rewardValue": 10,
  "maxUses": 100,
  "expiresAt": "2024-12-31T23:59:59Z"
}
```

## Fonctionnalités spéciales

### 1. Deferred Deep Linking
- Détection si l'app est installée via User-Agent
- Si non installée : redirection vers store + cookie de tracking
- Après installation : récupération du contexte via API

### 2. Détection de plateforme intelligente
```javascript
// Exemple de logique de détection
const detectPlatform = (userAgent) => {
  if (/Android/i.test(userAgent)) return 'android';
  if (/iPhone|iPad/i.test(userAgent)) return 'ios';
  if (/Windows NT/i.test(userAgent)) return 'windows';
  if (/Macintosh/i.test(userAgent)) return 'macos';
  return 'web';
};
```

### 3. Système de cache
- Redis pour les liens fréquemment accédés
- TTL de 1 heure pour les métadonnées de liens
- Cache des analytics avec TTL de 15 minutes

### 4. Rate limiting
- 1000 requêtes/heure par API key
- 10 requêtes/seconde pour les redirections
- Limitation par IP pour éviter les abus

## Sécurité

### 1. Authentification
- JWT avec expiration courte (15 min)
- Refresh tokens avec rotation
- Hash des mots de passe avec bcrypt (rounds: 12)

### 2. Validation des données
- Validation stricte des URLs
- Sanitisation des paramètres UTM
- Validation des domaines personnalisés

### 3. Protection CSRF
- Tokens CSRF pour les opérations sensibles
- Validation de l'origine des requêtes

## Monitoring et observabilité

### 1. Métriques à surveiller
- Latence des redirections (< 100ms)
- Taux d'erreur des APIs (< 1%)
- Utilisation de la base de données
- Taux de cache hit/miss

### 2. Logs structurés
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "link_clicked",
  "linkId": "uuid",
  "projectId": "uuid",
  "platform": "android",
  "country": "FR",
  "responseTime": 45
}
```

### 3. Alertes
- Pic de trafic inhabituel
- Erreurs 5xx > 1%
- Latence > 200ms
- Espace disque < 20%

## Déploiement

### 1. Variables d'environnement
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/synctra
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
DOMAIN=synctra-admin.vercel.app
```

### 2. Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### 3. Base de données
- Migrations avec Prisma ou TypeORM
- Backup quotidien automatique
- Réplication read-only pour les analytics

## Performance

### 1. Optimisations base de données
- Index sur les colonnes fréquemment requêtées
- Partitioning des tables d'analytics par date
- Connection pooling (max 20 connexions)

### 2. CDN
- Cache des assets statiques
- Géo-distribution des redirections
- TTL de 1 an pour les ressources statiques

### 3. Pagination
- Limite de 50 éléments par page par défaut
- Cursor-based pagination pour les grandes collections

## Tests

### 1. Tests unitaires
- Couverture > 80%
- Tests des fonctions critiques (redirections, analytics)

### 2. Tests d'intégration
- Tests des APIs complètes
- Tests de la logique de redirection

### 3. Tests de charge
- 1000 redirections/seconde
- 100 créations de liens/minute

---

## Contact

Pour toute question technique, contactez l'équipe frontend ou consultez la documentation API interactive à l'adresse : `https://synctra-admin.vercel.app/api/docs`
