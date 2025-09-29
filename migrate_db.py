#!/usr/bin/env python3
"""
Script para ejecutar migraciones en Railway Production
"""
import os
from sqlalchemy import create_engine
from src.models.database import Base

def load_env():
    """Carga variables de entorno"""
    # En Railway, las variables ya están disponibles automáticamente
    pass

def migrate_database():
    """Crea todas las tablas"""
    load_env()
    
    # Railway proporciona DATABASE_URL automáticamente
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL no encontrada")
        print("Asegúrate de que PostgreSQL esté configurado en Railway")
        return False
    
    print(f"🔗 Conectando a: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        engine = create_engine(database_url)
        
        # Crear todas las tablas
        print("📊 Creando tablas de la base de datos...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Migración completada exitosamente!")
        print("📋 Tablas creadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
