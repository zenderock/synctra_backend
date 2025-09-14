#!/usr/bin/env python3
"""
Script de migration pour VPS - Ajouter les colonnes App Links à la table projects
À exécuter sur le serveur de production
"""

import sqlite3
import os
import sys
from pathlib import Path

def find_database():
    """Trouver la base de données SQLite sur le VPS"""
    possible_paths = [
        "synctra.db",
        "app.db", 
        "database.db",
        "/var/www/synctra/synctra.db",
        "/opt/synctra/synctra.db",
        "./synctra.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("❌ Base de données non trouvée. Chemins testés :")
    for path in possible_paths:
        print(f"   - {path}")
    return None

def migrate_projects_table_vps():
    """Migration pour VPS avec gestion d'erreurs robuste"""
    
    db_path = find_database()
    if not db_path:
        print("💡 Astuce : Exécutez ce script depuis le répertoire contenant votre base de données")
        return False
    
    print(f"📍 Base de données trouvée : {db_path}")
    
    try:
        # Backup de la base avant migration
        backup_path = f"{db_path}.backup"
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"💾 Backup créé : {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Migration de la table projects...")
        
        # Vérifier que la table projects existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        if not cursor.fetchone():
            print("❌ Table 'projects' non trouvée")
            return False
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(projects)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Colonnes existantes : {len(existing_columns)} colonnes")
        
        # Colonnes à ajouter avec gestion SQLite
        migrations = [
            ("android_package", "ALTER TABLE projects ADD COLUMN android_package VARCHAR(255)"),
            ("ios_bundle_id", "ALTER TABLE projects ADD COLUMN ios_bundle_id VARCHAR(255)"),
            ("android_sha256_fingerprints", "ALTER TABLE projects ADD COLUMN android_sha256_fingerprints TEXT DEFAULT '[]'"),
            ("ios_team_id", "ALTER TABLE projects ADD COLUMN ios_team_id VARCHAR(20)"),
            ("assetlinks_json", "ALTER TABLE projects ADD COLUMN assetlinks_json TEXT"),
            ("apple_app_site_association", "ALTER TABLE projects ADD COLUMN apple_app_site_association TEXT")
        ]
        
        success_count = 0
        
        for column_name, sql_command in migrations:
            if column_name not in existing_columns:
                try:
                    cursor.execute(sql_command)
                    print(f"✅ {column_name}")
                    success_count += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"ℹ️  {column_name} (déjà existante)")
                    else:
                        print(f"❌ {column_name} : {e}")
            else:
                print(f"ℹ️  {column_name} (déjà existante)")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Migration terminée ! {success_count} colonnes ajoutées")
        print("🚀 Redémarrez votre application pour appliquer les changements")
        return True
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        print("💡 Vérifiez les permissions et que l'application n'utilise pas la DB")
        return False

if __name__ == "__main__":
    print("🔧 Migration VPS - Colonnes App Links")
    print("=" * 40)
    
    if migrate_projects_table_vps():
        print("\n🎉 Migration réussie !")
        print("📝 N'oubliez pas de redémarrer votre serveur FastAPI")
    else:
        print("\n💥 Migration échouée")
        sys.exit(1)
