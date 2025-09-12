# Synctra SDK

[![pub package](https://img.shields.io/pub/v/synctra_sdk.svg)](https://pub.dev/packages/synctra_sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SDK Flutter professionnel pour la gestion des liens dynamiques, deferred deep linking et analytics. Alternative moderne et puissante à Firebase Dynamic Links.

## 🚀 Fonctionnalités

- **Liens dynamiques** : Création et gestion de liens courts intelligents
- **Deferred Deep Linking** : Redirection après installation d'application
- **Analytics avancés** : Tracking complet des interactions utilisateur
- **Codes de parrainage** : Système de référencement intégré
- **Détection d'installation** : Vérification automatique des apps installées
- **Multi-plateforme** : Support Android, iOS, Web, Desktop
- **Offline-first** : Fonctionnement hors ligne avec synchronisation
- **Production-ready** : Code optimisé pour la production

## 📦 Installation

Ajoutez Synctra SDK à votre `pubspec.yaml` :

```yaml
dependencies:
  synctra_sdk: ^1.0.0
```

Puis exécutez :

```bash
flutter pub get
```

## 🔧 Configuration

### 1. Initialisation du SDK

```dart
import 'package:synctra_sdk/synctra_sdk.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Configuration du SDK
  const config = SynctraConfig(
    apiKey: 'votre_cle_api_synctra',
    projectId: 'votre_project_id',
    baseUrl: 'https://api.synctra.link', // Optionnel
    enableAnalytics: true,
    enableDeepLinking: true,
    enableReferrals: true,
    debugMode: false, // true en développement
  );
  
  // Initialisation
  await SynctraSDK.initialize(config);
  
  runApp(MyApp());
}
```

### 2. Configuration Android

Ajoutez dans `android/app/src/main/AndroidManifest.xml` :

```xml
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleTop"
    android:theme="@style/LaunchTheme">
    
    <!-- Intent filter pour les liens personnalisés -->
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https"
              android:host="votre-domaine.com" />
    </intent-filter>
    
    <!-- Intent filter pour le scheme personnalisé -->
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="votre-app-scheme" />
    </intent-filter>
</activity>
```

### 3. Configuration iOS

Ajoutez dans `ios/Runner/Info.plist` :

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLName</key>
        <string>votre-domaine.com</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>https</string>
        </array>
    </dict>
    <dict>
        <key>CFBundleURLName</key>
        <string>votre-app-scheme</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>votre-app-scheme</string>
        </array>
    </dict>
</array>
```

## 💡 Utilisation

### Création de liens dynamiques

```dart
// Lien simple
final link = await SynctraSDK.instance.createLink(
  originalUrl: 'https://monapp.com/produit/123',
);

print('Lien court: ${link.shortUrl}');

// Lien avancé avec paramètres
final advancedLink = await SynctraSDK.instance.createLink(
  originalUrl: 'https://monapp.com/produit/123',
  parameters: {
    'productId': '123',
    'category': 'electronics',
    'utm_source': 'app',
  },
  fallbackUrl: 'https://monapp.com',
  iosAppStoreUrl: 'https://apps.apple.com/app/id123456789',
  androidPlayStoreUrl: 'https://play.google.com/store/apps/details?id=com.monapp',
  expiresAt: DateTime.now().add(Duration(days: 30)),
  campaignId: 'summer_2024',
);
```

### Gestion des liens entrants

```dart
class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  @override
  void initState() {
    super.initState();
    _initDeepLinks();
  }

  void _initDeepLinks() {
    // Écouter les liens entrants
    _linkStream = linkStream.listen((String link) {
      SynctraSDK.instance.handleIncomingLink(link);
    });
  }
}
```

### Deferred Deep Linking

```dart
// Attendre un lien différé après installation
final deferredLink = await SynctraSDK.instance.waitForDeferredLink(
  packageName: 'com.monapp.android',
  timeout: Duration(seconds: 30),
);

if (deferredLink != null) {
  // Traiter le lien différé
  final productId = deferredLink.parameters['productId'];
  Navigator.pushNamed(context, '/product/$productId');
}
```

### Analytics et tracking

```dart
// Tracking automatique (activé par défaut)
await SynctraSDK.instance.trackLinkClick('link_id_123');

// Tracking de conversion
await SynctraSDK.instance.trackConversion(
  'link_id_123',
  value: 29.99,
  currency: 'EUR',
  properties: {
    'product_name': 'Super Produit',
    'category': 'electronics',
  },
);

// Événement personnalisé
await SynctraSDK.instance.trackEvent(
  type: AnalyticsEventType.customEvent,
  linkId: 'link_id_123',
  properties: {
    'event_name': 'product_viewed',
    'product_id': '123',
  },
);
```

### Codes de parrainage

```dart
// Définir l'utilisateur actuel
await SynctraSDK.instance.setUserId('user_123');

// Créer un code de parrainage
final referralCode = await SynctraSDK.instance.createReferralCode(
  customCode: 'MONCODE123', // Optionnel
  maxUses: 10,
  rewardAmount: 5.0,
  rewardType: 'credit',
  expiresAt: DateTime.now().add(Duration(days: 30)),
);

// Valider un code de parrainage
final isValid = await SynctraSDK.instance.validateReferralCode('MONCODE123');

// Utiliser un code de parrainage
if (isValid) {
  final usedCode = await SynctraSDK.instance.useReferralCode('MONCODE123');
  print('Code utilisé avec succès: ${usedCode.rewardAmount}€');
}
```

### Détection d'installation d'app

```dart
// Vérifier si une app est installée
final isInstalled = await SynctraSDK.instance.isAppInstalled('com.example.app');

if (isInstalled) {
  // Ouvrir l'app avec des paramètres
  await SynctraSDK.instance.openApp(
    'com.example.app',
    parameters: {'page': 'product', 'id': '123'},
  );
} else {
  // Rediriger vers le store
  await SynctraSDK.instance.openAppStore(
    packageName: 'com.example.app',
    iosAppId: '123456789',
  );
}
```

## 🔒 Gestion des erreurs

```dart
try {
  final link = await SynctraSDK.instance.createLink(
    originalUrl: 'https://example.com',
  );
} on NetworkException catch (e) {
  // Erreur réseau
  print('Erreur réseau: ${e.message}');
} on ValidationException catch (e) {
  // Erreur de validation
  print('Erreur de validation: ${e.message} (Champ: ${e.field})');
} on ConfigurationException catch (e) {
  // Erreur de configuration
  print('Erreur de configuration: ${e.message}');
} catch (e) {
  // Autres erreurs
  print('Erreur inattendue: $e');
}
```

## 📊 Modèles de données

### DeepLink

```dart
class DeepLink {
  final String id;
  final String originalUrl;
  final String shortUrl;
  final Map<String, dynamic> parameters;
  final String? fallbackUrl;
  final String? iosAppStoreUrl;
  final String? androidPlayStoreUrl;
  final DateTime createdAt;
  final DateTime? expiresAt;
  final bool isActive;
  final String? campaignId;
  final String? referralCode;
  
  bool get isExpired;
  bool get isValid;
}
```

### ReferralCode

```dart
class ReferralCode {
  final String code;
  final String userId;
  final String? campaignId;
  final DateTime createdAt;
  final DateTime? expiresAt;
  final int maxUses;
  final int currentUses;
  final bool isActive;
  final double? rewardAmount;
  final String? rewardType;
  
  bool get isExpired;
  bool get hasReachedMaxUses;
  bool get isValid;
}
```

### AnalyticsEvent

```dart
enum AnalyticsEventType {
  linkCreated,
  linkClicked,
  linkOpened,
  appInstalled,
  appOpened,
  referralUsed,
  conversionCompleted,
  customEvent,
}

class AnalyticsEvent {
  final String id;
  final AnalyticsEventType type;
  final String linkId;
  final DateTime timestamp;
  final Map<String, dynamic> properties;
  final String? userId;
  final String? sessionId;
  final String? deviceId;
}
```

## 🧪 Tests

```dart
// Exécuter les tests
flutter test

// Tests avec couverture
flutter test --coverage
```

## 🔧 Configuration avancée

### Personnalisation du domaine

```dart
const config = SynctraConfig(
  apiKey: 'votre_cle_api',
  projectId: 'votre_project_id',
  customDomain: 'links.monapp.com',
  defaultParameters: {
    'utm_source': 'mobile_app',
    'utm_medium': 'deeplink',
  },
);
```

### Gestion offline

Le SDK fonctionne automatiquement hors ligne :
- Les événements analytics sont mis en cache
- Les liens sont synchronisés à la reconnexion
- Les données de parrainage sont sauvegardées localement

### Performance et optimisation

```dart
// Vider le cache analytics manuellement
await SynctraSDK.instance.flushAnalytics();

// Nettoyer les ressources
await SynctraSDK.instance.dispose();
```

## 📚 Exemples complets

Consultez le dossier `/example` pour des exemples d'implémentation complète :

- Application de e-commerce avec liens de produits
- Système de parrainage d'utilisateurs
- Tracking d'événements personnalisés
- Gestion des liens différés

## 🤝 Support et contribution

- **Documentation** : [docs.synctra.link](https://docs.synctra.link)
- **Issues** : [GitHub Issues](https://github.com/synctra/synctra_sdk/issues)
- **Discussions** : [GitHub Discussions](https://github.com/synctra/synctra_sdk/discussions)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🔄 Changelog

Consultez [CHANGELOG.md](CHANGELOG.md) pour l'historique des versions.

---

Développé avec ❤️ par l'équipe Synctra
