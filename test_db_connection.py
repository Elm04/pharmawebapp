import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
import time

# Configuration distante Render.com
REMOTE_DB_URI = "postgresql://pharmadatabase_user:WQSRXZWsY2KYpxQAdmqENzqcvRrzpX7K@dpg-d1lerhje5dus73fkkk6g-a.oregon-postgres.render.com/pharmadatabase"

def parse_db_uri(db_uri):
    """Extrait les paramètres de connexion depuis l'URI"""
    parsed = urlparse(db_uri)
    return {
        "host": parsed.hostname,
        "database": parsed.path[1:],  # Supprime le slash initial
        "user": parsed.username,
        "password": parsed.password,
        "port": parsed.port or 5432
    }

def test_remote_connection(max_retries=3, retry_delay=2):
    """Teste la connexion au serveur distant avec reprise automatique"""
    db_config = parse_db_uri(REMOTE_DB_URI)
    
    print(f"\n🔍 Test de connexion au serveur distant: {db_config['host']}")
    print("="*50)
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔹 Tentative {attempt}/{max_retries}...")
            
            conn = psycopg2.connect(
                host=db_config["host"],
                database=db_config["database"],
                user=db_config["user"],
                password=db_config["password"],
                port=db_config["port"],
                connect_timeout=5  # Timeout de 5 secondes
            )
            
            with conn.cursor() as cursor:
                # Test 1: Version de PostgreSQL
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                
                # Test 2: Liste des tables (pour vérifier si la structure existe)
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Test 3: Temps de réponse
                start_time = time.time()
                cursor.execute("SELECT 1")
                latency = (time.time() - start_time) * 1000  # en ms
                
            print("\n✅ Connexion réussie!")
            print(f"📌 Version: {version.split(',')[0]}")
            print(f"📊 Tables existantes: {', '.join(tables) if tables else 'Aucune'}")
            print(f"⏱ Latence: {latency:.2f} ms")
            print(f"🔗 Host: {db_config['host']}")
            print(f"📁 Database: {db_config['database']}")
            print(f"👤 User: {db_config['user']}")
            
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Erreur de connexion: {str(e).split('(')[0]}")
            if attempt < max_retries:
                print(f"⏳ Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
            continue
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    print("\n💥 Échec après plusieurs tentatives. Vérifiez:")
    print("- Que l'URI de connexion est correcte")
    print("- Que le serveur est accessible depuis votre réseau")
    print("- Que les identifiants sont valides")
    print("- Que la base existe (CREATE DATABASE si nécessaire)")
    return False

def check_database_operations():
    """Vérifie les opérations CRUD de base"""
    db_config = parse_db_uri(REMOTE_DB_URI)
    
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test de création de table temporaire
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                message TEXT
            )
        """)
        
        # Test d'insertion
        cursor.execute("""
            INSERT INTO test_connection (timestamp, message)
            VALUES (NOW(), %s)
            RETURNING id
        """, ("Test de connexion réussi",))
        row_id = cursor.fetchone()[0]
        
        # Test de lecture
        cursor.execute("SELECT message FROM test_connection WHERE id = %s", (row_id,))
        message = cursor.fetchone()[0]
        
        # Nettoyage
        cursor.execute("DROP TABLE IF EXISTS test_connection")
        
        print(f"\n🔧 Tests CRUD réussis (ID: {row_id}, Message: '{message}')")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des opérations de base: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Test complet de connexion PostgreSQL distante ===")
    
    if test_remote_connection():
        print("\n🔍 Vérification des opérations de base...")
        check_database_operations()