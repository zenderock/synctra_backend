#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes App Links à la table projects
"""

import sqlite3
import os
from pathlib import Path

def migrate_projects_table():
    """Ajouter les colonnes manquantes à la table projects"""
    
    # Chemin vers la base de données
    db_path = Path(__file__).parent / "synctra.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée : {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔄 Début de la migration de la table projects...")
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(projects)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Colonnes existantes : {existing_columns}")
        
        # Colonnes à ajouter
        new_columns = [
            ("android_package", "VARCHAR(255)"),
            ("ios_bundle_id", "VARCHAR(255)"),
            ("android_sha256_fingerprints", "JSON DEFAULT '[]'"),
            ("ios_team_id", "VARCHAR(20)"),
            ("assetlinks_json", "JSON"),
            ("apple_app_site_association", "JSON")
        ]
        
        # Ajouter chaque colonne si elle n'existe pas
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                    print(f"✅ Colonne ajoutée : {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erreur lors de l'ajout de {column_name} : {e}")
            else:
                print(f"ℹ️  Colonne déjà existante : {column_name}")
        
        conn.commit()
        
        # Vérifier les colonnes après migration
        cursor.execute("PRAGMA table_info(projects)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📊 Colonnes finales : {final_columns}")
        
        conn.close()
        print("✅ Migration terminée avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        return False

if __name__ == "__main__":
    migrate_projects_table()
