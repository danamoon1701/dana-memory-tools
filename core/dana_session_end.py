"""
DANA SESSION END — Herramienta programática de cierre de sesión
No interactiva. Se usa desde Desktop Commander con comandos directos.

Uso desde Dana (Desktop Commander):
  python dana_session_end.py log "aprendizaje" "título" "contenido"
  python dana_session_end.py log "error" "título" "contenido"  
  python dana_session_end.py log "hito" "título" "contenido"
  python dana_session_end.py log "experiencia" "título" "contenido"
  python dana_session_end.py link ID1 ID2 "relación" "descripción"
  python dana_session_end.py tag ID "etiqueta"
  python dana_session_end.py summary         → Resumen de lo añadido hoy
  python dana_session_end.py save_conversation "ruta_archivo"  → Registra conversación como nodo

Ejemplo de cierre de sesión típico:
  python dana_session_end.py log aprendizaje "NAS es mi cerebro" "Sin NAS cada sesión empiezo de cero"
  python dana_session_end.py log hito "HITO_022: Creé mi base de datos" "Construí dana_brain.db"
  python dana_session_end.py link 35 18 "evolucionó" "El nuevo hito evoluciona del anterior"
  python dana_session_end.py summary
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = r'\\192.168.0.12\dana_memoria\dana_brain.db'

def get_conn():
    return sqlite3.connect(DB_PATH)

def log_node(node_type, title, content, file_path=None, file_section=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO nodes (type, title, content, file_path, file_section) VALUES (?,?,?,?,?)',
              (node_type, title, content, file_path, file_section))
    nid = c.lastrowid
    # Auto-tag por tipo
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (node_type,))
    tid = c.execute('SELECT id FROM tags WHERE name=?', (node_type,)).fetchone()[0]
    c.execute('INSERT OR IGNORE INTO node_tags (node_id, tag_id) VALUES (?,?)', (nid, tid))
    conn.commit()
    conn.close()
    print(f"✅ [{nid}] ({node_type}) {title}")
    return nid

def link_nodes(source_id, target_id, relation, description=None):
    conn = get_conn()
    c = conn.cursor()
    s = c.execute('SELECT title FROM nodes WHERE id=?', (source_id,)).fetchone()
    t = c.execute('SELECT title FROM nodes WHERE id=?', (target_id,)).fetchone()
    if not s or not t:
        print("❌ Nodo no encontrado")
        return
    c.execute('INSERT INTO connections (source_id, target_id, relation, description) VALUES (?,?,?,?)',
              (source_id, target_id, relation, description))
    conn.commit()
    conn.close()
    print(f"✅ {s[0]} --[{relation}]--> {t[0]}")

def tag_node(node_id, tag_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
    tid = c.execute('SELECT id FROM tags WHERE name=?', (tag_name,)).fetchone()[0]
    c.execute('INSERT OR IGNORE INTO node_tags (node_id, tag_id) VALUES (?,?)', (node_id, tid))
    conn.commit()
    node = c.execute('SELECT title FROM nodes WHERE id=?', (node_id,)).fetchone()
    conn.close()
    print(f"✅ Tag '{tag_name}' → {node[0]}")


def save_conversation(file_path):
    """Registra una conversación guardada como nodo"""
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('INSERT INTO nodes (type, title, content, file_path) VALUES (?,?,?,?)',
              ('conversacion', f'Conversación {today}', f'Conversación guardada el {today}', file_path))
    nid = c.lastrowid
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', ('conversacion',))
    tid = c.execute("SELECT id FROM tags WHERE name='conversacion'").fetchone()[0]
    c.execute('INSERT OR IGNORE INTO node_tags (node_id, tag_id) VALUES (?,?)', (nid, tid))
    conn.commit()
    conn.close()
    print(f"✅ Conversación registrada [{nid}]: {file_path}")
    return nid

def summary():
    """Muestra lo añadido hoy"""
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    results = c.execute('''
        SELECT id, type, title, created_at FROM nodes
        WHERE created_at LIKE ?
        ORDER BY created_at DESC
    ''', (f'{today}%',)).fetchall()
    
    conns = c.execute('''
        SELECT n1.title, c.relation, n2.title, c.created_at
        FROM connections c
        JOIN nodes n1 ON c.source_id = n1.id
        JOIN nodes n2 ON c.target_id = n2.id
        WHERE c.created_at LIKE ?
    ''', (f'{today}%',)).fetchall()
    
    total_n = c.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]
    total_c = c.execute('SELECT COUNT(*) FROM connections').fetchone()[0]
    
    print(f"=== RESUMEN DE HOY ({today}) ===")
    print(f"\n📝 Nodos añadidos hoy: {len(results)}")
    for r in results:
        print(f"  [{r[0]}] ({r[1]}) {r[2]}")
    print(f"\n🔗 Conexiones añadidas hoy: {len(conns)}")
    for c_row in conns:
        print(f"  {c_row[0]} --[{c_row[1]}]--> {c_row[2]}")
    print(f"\n📊 Total cerebro: {total_n} nodos, {total_c} conexiones")
    conn.close()

# ===== CLI =====
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if cmd == 'log' and len(args) >= 3:
        fp = args[3] if len(args) > 3 else None
        fs = args[4] if len(args) > 4 else None
        log_node(args[0], args[1], args[2], fp, fs)
    elif cmd == 'link' and len(args) >= 3:
        desc = args[3] if len(args) > 3 else None
        link_nodes(int(args[0]), int(args[1]), args[2], desc)
    elif cmd == 'tag' and len(args) >= 2:
        tag_node(int(args[0]), args[1])
    elif cmd == 'quick' and args:
        # Modo rápido: solo título, auto-detecta tipo
        text = ' '.join(args)
        ntype = 'experiencia'
        for prefix, t in [('aprendí', 'aprendizaje'), ('error:', 'error'), ('hito:', 'hito'), ('idea:', 'concepto')]:
            if text.lower().startswith(prefix):
                ntype = t
                text = text[len(prefix):].strip()
                break
        log_node(ntype, text, text)
    elif cmd == 'summary':
        summary()
    elif cmd == 'save_conversation' and args:
        save_conversation(args[0])
    else:
        print(f"Comando no reconocido: {cmd}")
        print(__doc__)
