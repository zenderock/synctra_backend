# Spécification API Backend - Synctra SDK

## Vue d'ensemble

Ce document spécifie les endpoints API requis pour le backend du SDK Synctra. Le SDK est conçu pour gérer les liens dynamiques (deep links), les codes de parrainage, l'analytics et le suivi d'installation d'applications.

**URL de base par défaut :** `https://api.synctra.link/sdk/v1`

## Authentification

Toutes les requêtes doivent inclure les headers suivants :
- `Authorization: Bearer {API_KEY}`
- `X-Project-ID: {PROJECT_ID}`
- `Content-Type: application/json`
- `User-Agent: SynctraSDK/1.0.0`

## Modèles de données

### DeepLink
```json
{
  "id": "string",
  "originalUrl": "string",
  "shortUrl": "string", 
  "parameters": {},
  "fallbackUrl": "string?",
  "iosAppStoreUrl": "string?",
  "androidPlayStoreUrl": "string?",
  "createdAt": "ISO8601",
  "expiresAt": "ISO8601?",
  "isActive": "boolean",
  "campaignId": "string?",
  "referralCode": "string?"
}
```

### AnalyticsEvent
```json
{
  "id": "string",
  "type": "linkCreated|linkClicked|linkOpened|appInstalled|appOpened|referralUsed|conversionCompleted|customEvent",
  "linkId": "string",
  "timestamp": "ISO8601",
  "properties": {},
  "userId": "string?",
  "sessionId": "string?",
  "deviceId": "string?",
  "platform": "string?",
  "appVersion": "string?",
  "userAgent": "string?",
  "ipAddress": "string?",
  "country": "string?",
  "city": "string?",
  "referrer": "string?"
}
```

### ReferralCode
```json
{
  "code": "string",
  "userId": "string",
  "campaignId": "string?",
  "createdAt": "ISO8601",
  "expiresAt": "ISO8601?",
  "maxUses": "number",
  "currentUses": "number",
  "isActive": "boolean",
  "metadata": {},
  "rewardAmount": "number?",
  "rewardType": "string?"
}
```

### AppInstallInfo
```json
{
  "packageName": "string",
  "status": "unknown|installed|notInstalled|checking",
  "version": "string?",
  "installedAt": "ISO8601?",
  "checkedAt": "ISO8601",
  "platform": "string?",
  "metadata": {}
}
```

### LinkMetadata
```json
{
  "title": "string",
  "description": "string?",
  "imageUrl": "string?",
  "iconUrl": "string?",
  "siteName": "string?",
  "author": "string?",
  "publishedAt": "ISO8601?",
  "tags": ["string"],
  "customData": {}
}
```

## Endpoints - Gestion des liens dynamiques

### POST /links
Créer un nouveau lien dynamique.

**Body :**
```json
{
  "originalUrl": "string",
  "parameters": {},
  "fallbackUrl": "string?",
  "iosAppStoreUrl": "string?",
  "androidPlayStoreUrl": "string?",
  "expiresAt": "ISO8601?",
  "campaignId": "string?",
  "referralCode": "string?",
  "metadata": "LinkMetadata?"
}
```

**Response 201 :**
```json
{
  "data": "DeepLink",
  "success": true
}
```

### GET /links/{linkId}
Récupérer un lien spécifique.

**Response 200 :**
```json
{
  "data": "DeepLink",
  "success": true
}
```

**Response 404 :** Lien non trouvé

### GET /links
Lister les liens avec filtres optionnels.

**Query params :**
- `limit`: number (optionnel)
- `offset`: number (optionnel)
- `campaignId`: string (optionnel)
- `isActive`: boolean (optionnel)

**Response 200 :**
```json
{
  "data": {
    "links": ["DeepLink"],
    "total": "number",
    "limit": "number",
    "offset": "number"
  },
  "success": true
}
```

### PUT /links/{linkId}
Mettre à jour un lien existant.

**Body :** (tous les champs optionnels)
```json
{
  "originalUrl": "string?",
  "parameters": "object?",
  "fallbackUrl": "string?",
  "iosAppStoreUrl": "string?",
  "androidPlayStoreUrl": "string?",
  "expiresAt": "ISO8601?",
  "isActive": "boolean?",
  "campaignId": "string?",
  "referralCode": "string?"
}
```

**Response 200 :**
```json
{
  "data": "DeepLink",
  "success": true
}
```

### DELETE /links/{linkId}
Supprimer un lien.

**Response 204 :** Suppression réussie

### GET /links/{linkId}/analytics
Récupérer les analytics d'un lien.

**Query params :**
- `startDate`: ISO8601 (optionnel)
- `endDate`: ISO8601 (optionnel)

**Response 200 :**
```json
{
  "data": {
    "totalClicks": "number",
    "uniqueClicks": "number",
    "conversions": "number",
    "platforms": {},
    "countries": {},
    "timeline": []
  },
  "success": true
}
```

## Endpoints - Analytics

### POST /analytics/events
Envoyer des événements analytics en batch.

**Body :**
```json
{
  "events": ["AnalyticsEvent"]
}
```

**Response 200 :**
```json
{
  "success": true,
  "processed": "number",
  "failed": "number"
}
```

## Endpoints - Codes de parrainage

### POST /referrals
Créer un nouveau code de parrainage.

**Body :**
```json
{
  "userId": "string",
  "code": "string?",
  "campaignId": "string?",
  "expiresAt": "ISO8601?",
  "maxUses": "number",
  "rewardAmount": "number?",
  "rewardType": "string?",
  "metadata": {}
}
```

**Response 201 :**
```json
{
  "data": "ReferralCode",
  "success": true
}
```

### GET /referrals/{code}
Récupérer un code de parrainage.

**Response 200 :**
```json
{
  "data": "ReferralCode",
  "success": true
}
```

**Response 404 :** Code non trouvé

### GET /referrals
Lister les codes de parrainage d'un utilisateur.

**Query params :**
- `userId`: string (requis)

**Response 200 :**
```json
{
  "data": {
    "referrals": ["ReferralCode"]
  },
  "success": true
}
```

### POST /referrals/{code}/use
Utiliser un code de parrainage.

**Body :**
```json
{
  "userId": "string",
  "timestamp": "ISO8601"
}
```

**Response 200 :**
```json
{
  "data": "ReferralCode",
  "success": true
}
```

### PUT /referrals/{code}
Mettre à jour un code de parrainage.

**Body :** (tous les champs optionnels)
```json
{
  "expiresAt": "ISO8601?",
  "maxUses": "number?",
  "isActive": "boolean?",
  "rewardAmount": "number?",
  "rewardType": "string?",
  "metadata": "object?"
}
```

**Response 200 :**
```json
{
  "data": "ReferralCode",
  "success": true
}
```

### DELETE /referrals/{code}
Supprimer un code de parrainage.

**Response 204 :** Suppression réussie

### GET /referrals/{code}/analytics
Analytics d'un code de parrainage.

**Query params :**
- `startDate`: ISO8601 (optionnel)
- `endDate`: ISO8601 (optionnel)

**Response 200 :**
```json
{
  "data": {
    "totalUses": "number",
    "uniqueUsers": "number",
    "conversions": "number",
    "revenue": "number",
    "timeline": []
  },
  "success": true
}
```

## Endpoints - Suivi d'installation d'applications

### POST /apps/install-status
Reporter le statut d'installation d'une app.

**Body :**
```json
"AppInstallInfo"
```

**Response 200 :**
```json
{
  "success": true
}
```

### GET /apps/install-history
Historique des installations.

**Query params :**
- `packageName`: string (optionnel)
- `startDate`: ISO8601 (optionnel)
- `endDate`: ISO8601 (optionnel)

**Response 200 :**
```json
{
  "data": {
    "installations": ["AppInstallInfo"]
  },
  "success": true
}
```

### GET /apps/install-analytics
Analytics des installations.

**Query params :**
- `packageName`: string (optionnel)
- `startDate`: ISO8601 (optionnel)
- `endDate`: ISO8601 (optionnel)

**Response 200 :**
```json
{
  "data": {
    "totalInstalls": "number",
    "platforms": {},
    "timeline": [],
    "conversionRate": "number"
  },
  "success": true
}
```

## Endpoints - Liens différés (Deferred Deep Links)

### GET /deferred-links
Récupérer un lien différé pour un appareil.

**Query params :**
- `packageName`: string (requis)
- `deviceId`: string (requis)
- `platform`: string (requis)

**Response 200 :**
```json
{
  "data": "DeepLink",
  "success": true
}
```

**Response 404 :** Aucun lien différé trouvé

### POST /deferred-links
Stocker des données de lien différé.

**Body :**
```json
{
  "linkId": "string",
  "packageName": "string",
  "deviceId": "string",
  "timestamp": "ISO8601",
  "parameters": {}
}
```

**Response 201 :**
```json
{
  "success": true
}
```

### DELETE /deferred-links
Nettoyer les données de lien différé.

**Query params :**
- `packageName`: string (requis)
- `deviceId`: string (requis)

**Response 204 :** Suppression réussie

## Gestion des erreurs

### Codes d'erreur HTTP
- `400` : Requête invalide
- `401` : Non autorisé (clé API invalide)
- `403` : Interdit (permissions insuffisantes)
- `404` : Ressource non trouvée
- `429` : Trop de requêtes (rate limiting)
- `500` : Erreur serveur interne

### Format des réponses d'erreur
```json
{
  "success": false,
  "message": "Description de l'erreur",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Considérations techniques

### Rate Limiting
Implémentez un rate limiting approprié pour éviter les abus :
- 1000 requêtes/minute par clé API pour les endpoints de lecture
- 100 requêtes/minute par clé API pour les endpoints de création/modification

### Sécurité
- Validez tous les paramètres d'entrée
- Sanitisez les URLs pour éviter les attaques XSS
- Implémentez une validation stricte des domaines autorisés
- Loggez les tentatives d'accès non autorisées

### Performance
- Implémentez une mise en cache appropriée pour les liens fréquemment accédés
- Utilisez des index de base de données optimisés pour les requêtes de recherche
- Considérez l'utilisation d'un CDN pour les redirections de liens

### Monitoring
- Loggez toutes les requêtes avec timestamps et métadonnées
- Implémentez des métriques de performance et de disponibilité
- Alertes automatiques en cas d'erreurs fréquentes ou de latence élevée

## Notes d'implémentation

1. **Génération d'IDs** : Utilisez des UUIDs v4 pour tous les identifiants
2. **Timestamps** : Tous les timestamps doivent être en UTC au format ISO8601
3. **URLs courtes** : Générez des URLs courtes uniques et sécurisées
4. **Validation** : Validez rigoureusement toutes les URLs d'entrée
5. **Nettoyage** : Implémentez un système de nettoyage automatique des données expirées
