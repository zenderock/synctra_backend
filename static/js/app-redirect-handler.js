// Gestionnaire de redirection intelligente pour applications mobiles
class AppRedirectHandler {
    constructor(config) {
        this.config = {
            customScheme: config.customScheme,
            androidPackage: config.androidPackage,
            iosAppId: config.iosAppId,
            fallbackUrl: config.fallbackUrl,
            timeout: config.timeout || 3000,
            apiKey: config.apiKey,
            projectId: config.projectId,
            apiBaseUrl: config.apiBaseUrl || '/sdk/v1'
        };
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

        if (deviceType === 'android') {
            return this.handleAndroidRedirect(fullDeeplink, linkData);
        } else if (deviceType === 'ios') {
            return this.handleIOSRedirect(fullDeeplink, linkData);
        } else {
            window.location.href = this.config.fallbackUrl;
            return false;
        }
    }

    async handleAndroidRedirect(deeplink, linkData) {
        const isInstalled = await this.tryCustomScheme(deeplink);
        
        if (!isInstalled) {
            await this.saveDeferredLink(linkData);
            
            if (this.config.androidPackage) {
                const playStoreUrl = `https://play.google.com/store/apps/details?id=${this.config.androidPackage}`;
                window.location.href = playStoreUrl;
            } else {
                window.location.href = this.config.fallbackUrl;
            }
        }
        
        return isInstalled;
    }

    async handleIOSRedirect(deeplink, linkData) {
        const isInstalled = await this.tryCustomScheme(deeplink);
        
        if (!isInstalled) {
            await this.saveDeferredLink(linkData);
            
            const appStoreUrl = this.config.iosAppId ? 
                `https://apps.apple.com/app/id${this.config.iosAppId}` : 
                this.config.fallbackUrl;
            
            setTimeout(() => {
                window.location.href = appStoreUrl;
            }, 100);
        }
        
        return isInstalled;
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
