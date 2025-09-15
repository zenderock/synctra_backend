// Gestionnaire de redirection intelligente pour applications mobiles
class AppRedirectHandler {
    constructor(config) {
        this.config = config;
    }

    addLog(message, type = 'info') {
        // Utiliser la fonction addLog globale si elle existe
        if (typeof window.addLog === 'function') {
            window.addLog(message, type);
        } else {
            console.log(message);
        }
    }

    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/android/.test(userAgent)) return 'android';
        if (/iphone|ipad|ipod/.test(userAgent)) return 'ios';
        return 'desktop';
    }

    generateDeviceId() {
        const stored = localStorage.getItem('synctra_device_id');
        if (stored) return stored;
        
        const deviceId = 'web_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        localStorage.setItem('synctra_device_id', deviceId);
        return deviceId;
    }

    async handleAppRedirect(deeplink = '', linkData = {}) {
        const deviceType = this.getDeviceType();
        const fullDeeplink = this.config.customScheme + deeplink;
        
        this.addLog('🔍 handleAppRedirect appelé avec: ' + deeplink, 'info');
        this.addLog('📱 Device type: ' + deviceType, 'info');
        this.addLog('🔗 Full deeplink: ' + fullDeeplink, 'info');

        // ÉTAPE 2: Vérifier si les assetlinks sont configurés pour ce projet
        const hasAssetlinks = this.config.hasAssetlinks || this.config.hasAppleAssociation;
        this.addLog('🔗 ÉTAPE 2: Assetlinks configurés: ' + hasAssetlinks, 'info');
        this.addLog('📋 Android assetlinks: ' + this.config.hasAssetlinks + ', iOS association: ' + this.config.hasAppleAssociation, 'info');

        // ÉTAPE 3A: Si assetlinks configurés, utiliser getInstalledRelatedApps
        if (hasAssetlinks && 'getInstalledRelatedApps' in navigator) {
            this.addLog('🔍 ÉTAPE 3A: Utilisation getInstalledRelatedApps (assetlinks configurés)', 'info');
            try {
                const apps = await navigator.getInstalledRelatedApps();
                this.addLog('📱 Apps trouvées: ' + JSON.stringify(apps), 'info');
                const isAppInstalled = apps.some(app => 
                    (app.platform === 'play' && app.id === this.config.androidPackage) ||
                    (app.platform === 'itunes' && app.id === this.config.iosAppId)
                );
                
                if (isAppInstalled) {
                    this.addLog('✅ App détectée via getInstalledRelatedApps - ouverture directe', 'success');
                    window.location.href = fullDeeplink;
                    return true;
                } else {
                    this.addLog('❌ App non détectée via getInstalledRelatedApps', 'error');
                    this.addLog('🏪 ÉTAPE 4: Redirection vers le store', 'info');
                    await this.saveDeferredLink(linkData);
                    this.redirectToStore(deviceType);
                    return false;
                }
            } catch (error) {
                this.addLog('⚠️ getInstalledRelatedApps échoué: ' + error.message, 'warning');
                this.addLog('🔄 Fallback vers ÉTAPE 3B', 'info');
            }
        } else {
            this.addLog('🚀 ÉTAPE 3B: Utilisation directe de open-native-app (pas d\'assetlinks)', 'info');
        }

        // Utiliser open-native-app ou méthodes classiques
        if (deviceType === 'android') {
            this.addLog('🤖 Redirection vers handleAndroidRedirect', 'info');
            return this.handleAndroidRedirect(fullDeeplink, linkData);
        } else if (deviceType === 'ios') {
            this.addLog('🍎 Redirection vers handleIOSRedirect', 'info');
            return this.handleIOSRedirect(fullDeeplink, linkData);
        } else {
            this.addLog('💻 Desktop détecté - fallback URL', 'info');
            window.location.href = this.config.fallbackUrl;
            return false;
        }
    }

    redirectToStore(deviceType) {
     setTimeout(() => {
        if (deviceType === 'android' && this.config.androidPackage) {
            const playStoreUrl = `https://play.google.com/store/apps/details?id=${this.config.androidPackage}`;
            window.location.href = playStoreUrl;
        } else if (deviceType === 'ios' && this.config.iosAppId) {
            const appStoreUrl = `https://apps.apple.com/app/id${this.config.iosAppId}`;
            window.location.href = appStoreUrl;
        } else {
            window.location.href = this.config.fallbackUrl;
        }
     }, 15000);
    }

    async handleAndroidRedirect(deeplink, linkData) {
        this.addLog('🤖 ÉTAPE 3B: Android redirect avec open-native-app', 'info');
        this.addLog('🔗 Deeplink: ' + deeplink, 'info');
        this.addLog('📦 Package: ' + this.config.androidPackage, 'info');
        
        // Utiliser open-native-app pour une meilleure compatibilité
        if (typeof openApp !== 'undefined') {
            this.addLog('🚀 Tentative d\'ouverture avec open-native-app', 'info');
            
            return new Promise((resolve) => {
                openApp.open(
                    deeplink,
                    (code) => {
                        this.addLog('❌ App non installée ou refusée (code: ' + code + ')', 'error');
                        this.addLog('🏪 ÉTAPE 4: Redirection vers Play Store', 'info');
                        this.saveDeferredLink(linkData);
                        this.redirectToStore('android');
                        resolve(false);
                    },
                    () => {
                        this.addLog('❌ Erreur lors de l\'ouverture', 'error');
                        this.addLog('🏪 ÉTAPE 4: Redirection vers Play Store', 'info');
                        this.saveDeferredLink(linkData);
                        this.redirectToStore('android');
                        resolve(false);
                    },
                    3000 // Timeout de 3 secondes
                );
                
                // Si pas de callback d'erreur dans les 2 secondes, considérer comme succès
                setTimeout(() => {
                    this.addLog('✅ App probablement ouverte avec succès', 'success');
                    resolve(true);
                }, 2000);
            });
        }
        
        // Fallback vers l'ancienne méthode si open-native-app n'est pas disponible
        this.addLog('⚠️ open-native-app non disponible, fallback', 'warning');
        return this.tryCustomSchemeAndroid(deeplink);
    }

    // Nouvelle méthode pour Intent URLs
    tryIntentUrl(intentUrl) {
        return new Promise((resolve) => {
            let resolved = false;
            const startTime = Date.now();

            const handleSuccess = () => {
                if (!resolved && (Date.now() - startTime) < 1000) {
                    resolved = true;
                    resolve(true);
                }
            };

            // Écouter les événements de changement de visibilité
            document.addEventListener('visibilitychange', handleSuccess);
            window.addEventListener('blur', handleSuccess);
            window.addEventListener('pagehide', handleSuccess);

            // Timeout plus court pour Intent URLs
            setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    document.removeEventListener('visibilitychange', handleSuccess);
                    window.removeEventListener('blur', handleSuccess);
                    window.removeEventListener('pagehide', handleSuccess);
                    resolve(false);
                }
            }, 1500);

            // Tenter la redirection
            try {
                window.location.href = intentUrl;
            } catch (error) {
                if (!resolved) {
                    resolved = true;
                    resolve(false);
                }
            }
        });
    }

    // Méthode améliorée pour Android custom scheme
    tryCustomSchemeAndroid(deeplink) {
        return new Promise((resolve) => {
            let resolved = false;
            const startTime = Date.now();
            let blurDetected = false;

            const handleBlur = () => {
                blurDetected = true;
                setTimeout(() => {
                    if (!resolved && blurDetected) {
                        resolved = true;
                        cleanup();
                        resolve(true);
                    }
                }, 100);
            };

            const handleFocus = () => {
                if (blurDetected && !resolved) {
                    // L'utilisateur est revenu rapidement, l'app n'était pas installée
                    resolved = true;
                    cleanup();
                    resolve(false);
                }
            };

            const cleanup = () => {
                window.removeEventListener('blur', handleBlur);
                window.removeEventListener('focus', handleFocus);
                document.removeEventListener('visibilitychange', handleBlur);
            };

            // Écouter les événements
            window.addEventListener('blur', handleBlur);
            window.addEventListener('focus', handleFocus);
            document.addEventListener('visibilitychange', handleBlur);

            // Timeout
            setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    cleanup();
                    resolve(false);
                }
            }, this.config.timeout);

            // Créer un lien invisible et cliquer
            const link = document.createElement('a');
            link.href = deeplink;
            link.style.display = 'none';
            document.body.appendChild(link);
            
            setTimeout(() => {
                link.click();
                document.body.removeChild(link);
            }, 100);
        });
    }

    async handleIOSRedirect(deeplink, linkData) {
        this.addLog('🍎 ÉTAPE 3B: iOS redirect avec open-native-app', 'info');
        this.addLog('🔗 Deeplink: ' + deeplink, 'info');
        this.addLog('📱 App ID: ' + this.config.iosAppId, 'info');
        
        // Utiliser open-native-app pour iOS aussi
        if (typeof openApp !== 'undefined') {
            this.addLog('🚀 Tentative d\'ouverture avec open-native-app', 'info');
            
            return new Promise((resolve) => {
                openApp.open(
                    deeplink,
                    (code) => {
                        this.addLog('❌ App non installée ou refusée (code: ' + code + ')', 'error');
                        this.addLog('🏪 ÉTAPE 4: Redirection vers App Store', 'info');
                        this.saveDeferredLink(linkData);
                        this.redirectToStore('ios');
                        resolve(false);
                    },
                    () => {
                        this.addLog('❌ Erreur lors de l\'ouverture', 'error');
                        this.addLog('🏪 ÉTAPE 4: Redirection vers App Store', 'info');
                        this.saveDeferredLink(linkData);
                        this.redirectToStore('ios');
                        resolve(false);
                    },
                    3000 // Timeout de 3 secondes
                );
                
                // Si pas de callback d'erreur dans les 2 secondes, considérer comme succès
                setTimeout(() => {
                    this.addLog('✅ App probablement ouverte avec succès', 'success');
                    resolve(true);
                }, 2000);
            });
        }
        
        // Fallback vers l'ancienne méthode si open-native-app n'est pas disponible
        this.addLog('⚠️ open-native-app non disponible, fallback iOS', 'warning');
        return this.tryCustomScheme(deeplink);
    }

    tryCustomScheme(deeplink) {
        return new Promise((resolve) => {
            let resolved = false;
            const startTime = Date.now();

            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = deeplink;

            const handleEvent = () => {
                if (!resolved && (Date.now() - startTime) < this.config.timeout) {
                    resolved = true;
                    cleanup();
                    resolve(true);
                }
            };

            const cleanup = () => {
                if (iframe.parentNode) {
                    document.body.removeChild(iframe);
                }
                document.removeEventListener('visibilitychange', handleEvent);
                window.removeEventListener('blur', handleEvent);
                window.removeEventListener('pagehide', handleEvent);
            };

            document.addEventListener('visibilitychange', handleEvent);
            window.addEventListener('blur', handleEvent);
            window.addEventListener('pagehide', handleEvent);

            setTimeout(() => {
                if (!resolved) {
                    resolved = true;
                    cleanup();
                    resolve(false);
                }
            }, this.config.timeout);

            document.body.appendChild(iframe);

            setTimeout(() => {
                if (iframe.parentNode && !resolved) {
                    document.body.removeChild(iframe);
                }
            }, 100);
        });
    }

    async saveDeferredLink(linkData) {
        try {
            const deviceType = this.getDeviceType();
            const deviceId = this.generateDeviceId();
            
            const payload = {
                linkId: linkData.linkId,
                packageName: this.config.androidPackage || this.config.iosAppId,
                deviceId: deviceId,
                platform: deviceType,
                timestamp: new Date().toISOString(),
                parameters: linkData.parameters || {},
                originalUrl: linkData.originalUrl,
                metadata: {
                    userAgent: navigator.userAgent,
                    referrer: document.referrer,
                    currentUrl: window.location.href
                }
            };

            const response = await fetch(`${this.config.apiBaseUrl}/deferred-links`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.config.apiKey}`,
                    'X-Project-ID': this.config.projectId,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            sessionStorage.setItem('synctra_deferred_saved', JSON.stringify({
                deviceId: deviceId,
                linkId: linkData.linkId,
                timestamp: Date.now()
            }));

            return result;
        } catch (error) {
            console.error('Erreur lors de la sauvegarde des données différées:', error);
            
            sessionStorage.setItem('synctra_deferred_fallback', JSON.stringify({
                ...linkData,
                deviceId: this.generateDeviceId(),
                timestamp: Date.now(),
                error: error.message
            }));
            
            return null;
        }
    }

    async getDeferredLink() {
        try {
            const deviceType = this.getDeviceType();
            const deviceId = this.generateDeviceId();
            const packageName = this.config.androidPackage || this.config.iosAppId;

            const response = await fetch(
                `${this.config.apiBaseUrl}/deferred-links?packageName=${packageName}&deviceId=${deviceId}&platform=${deviceType}`,
                {
                    headers: {
                        'Authorization': `Bearer ${this.config.apiKey}`,
                        'X-Project-ID': this.config.projectId
                    }
                }
            );

            if (response.ok) {
                const result = await response.json();
                
                await this.cleanDeferredLink(packageName, deviceId);
                
                return result.data;
            }
            
            return null;
        } catch (error) {
            console.error('Erreur lors de la récupération des données différées:', error);
            
            const fallback = sessionStorage.getItem('synctra_deferred_fallback');
            if (fallback) {
                sessionStorage.removeItem('synctra_deferred_fallback');
                return JSON.parse(fallback);
            }
            
            return null;
        }
    }

    async cleanDeferredLink(packageName, deviceId) {
        try {
            await fetch(
                `${this.config.apiBaseUrl}/deferred-links?packageName=${packageName}&deviceId=${deviceId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${this.config.apiKey}`,
                        'X-Project-ID': this.config.projectId
                    }
                }
            );
            
            sessionStorage.removeItem('synctra_deferred_saved');
        } catch (error) {
            console.error('Erreur lors du nettoyage des données différées:', error);
        }
    }

    getLocalDeferred() {
        try {
            const data = sessionStorage.getItem('synctra_deferred_saved');
            if (data) {
                const parsed = JSON.parse(data);
                if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
                    return parsed;
                }
                sessionStorage.removeItem('synctra_deferred_saved');
            }
            return null;
        } catch (error) {
            console.error('Erreur lors de la récupération des données locales:', error);
            return null;
        }
    }
}

async function createSmartRedirect(linkConfig, linkData) {
    const handler = new AppRedirectHandler(linkConfig);
    
    try {
        const success = await handler.handleAppRedirect(linkData.deeplink, linkData);
        
        if (!success) {
            console.log('Application non installée, redirection vers le store');
        }
        
        return success;
    } catch (error) {
        console.error('Échec de la redirection:', error);
        window.location.href = linkConfig.fallbackUrl;
        return false;
    }
}

window.AppRedirectHandler = AppRedirectHandler;
window.createSmartRedirect = createSmartRedirect;
