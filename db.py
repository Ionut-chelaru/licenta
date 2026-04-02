import sqlite3
from datetime import datetime
import json

DB_NAME = "licenta.db"

def init_db():
    """Inițializează baza de date și creează tabelele necesare."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabel Sesiuni
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            data TEXT NOT NULL,
            exercitiu TEXT NOT NULL,
            repetari INTEGER NOT NULL,
            scor INTEGER NOT NULL,
            feedback TEXT NOT NULL
        )
    """)
    
    # Tabel Utilizatori
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def adauga_utilizator(username, password):
    """Înregistrează un utilizator nou."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO utilizatori (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verifica_utilizator(username, password):
    """Verifică dacă credențialele sunt corecte."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilizatori WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def salveaza_sesiune(exercitiu, repetari, scor, feedback_lista):
    """Salvează o nouă sesiune de analiză în baza de date."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    data_acum = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_json = json.dumps(feedback_lista)
    
    cursor.execute("""
        INSERT INTO sesiuni (data, exercitiu, repetari, scor, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (data_acum, exercitiu, repetari, scor, feedback_json))
    
    conn.commit()
    conn.close()

def obtine_istoric(limit=10):
    """Returnează ultimele sesiuni din baza de date."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite accesarea coloanelor prin nume
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sesiuni ORDER BY data DESC LIMIT ?", (limit,))
    randuri = cursor.fetchall()
    
    istoric = []
    for r in randuri:
        sesiune = dict(r)
        sesiune['feedback'] = json.loads(sesiune['feedback'])
        istoric.append(sesiune)
        
    conn.close()
    return istoric

if __name__ == "__main__":
    init_db()
    print("Baza de date a fost inițializată cu succes!")
