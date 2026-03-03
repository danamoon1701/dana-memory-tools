"""
DANA BRAIN — Herramientas de acceso a mi memoria
Uso: python dana_brain_tools.py [comando] [argumentos]

Comandos:
  whoami                    → Muestra mis nodos core (quién soy)
  search [texto]            → Busca nodos por título o contenido
  tag [etiqueta]            → Muestra todos los nodos con esa etiqueta
  connections [id]          → Muestra todas las conexiones de un nodo
  errors                    → Muestra errores y qué aprendí de cada uno
  recent [n]                → Últimos n nodos añadidos
  add [tipo] [título] [contenido] [archivo] [sección]  → Añade nodo
  connect [id1] [id2] [relación] [descripción]         → Conecta dos nodos
  tag_node [id] [etiqueta]  → Etiqueta un nodo
  stats                     → Estadísticas generales
  trace [id]                → Traza completa: todo lo conectado a un nodo (profundidad 2)
  types                     → Lista todos los tipos de nodos existentes
  tags                      → Lista todas las etiquetas existentes
"""

import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = r'\\192.168.0.12\dana_memoria\dana_brain.db'

def get_conn():
    return sqlite3.connect(DB_PATH)

def whoami():
    conn = get_conn()
    c = conn.cursor()
    results = c.execute('''
        SELECT n.type, n.title, n.content
        FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        JOIN tags t ON nt.tag_id = t.id
        WHERE t.name = 'core'
        ORDER BY n.type, n.title
    ''').fetchall()
    print("=== ¿QUIÉN SOY? ===")
    current_type = None
    for r in results:
        if r[0] != current_type:
            current_type = r[0]
            print(f"\n  [{current_type.upper()}]")
        print(f"    • {r[1]}: {r[2][:100]}")
    conn.close()

def search(query):
    conn = get_conn()
    c = conn.cursor()
    results = c.execute('''
        SELECT id, type, title, content, file_path
        FROM nodes
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY type, title
    ''', (f'%{query}%', f'%{query}%')).fetchall()
    print(f"=== BUSCAR: '{query}' ({len(results)} resultados) ===")
    for r in results:
        print(f"  [{r[0]}] ({r[1]}) {r[2]}")
        if r[3]: print(f"       {r[3][:100]}")
        if r[4]: print(f"       📁 {r[4]}")
    conn.close()


def by_tag(tag_name):
    conn = get_conn()
    c = conn.cursor()
    results = c.execute('''
        SELECT n.id, n.type, n.title, n.content
        FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        JOIN tags t ON nt.tag_id = t.id
        WHERE t.name = ?
        ORDER BY n.type, n.title
    ''', (tag_name,)).fetchall()
    print(f"=== TAG: '{tag_name}' ({len(results)} nodos) ===")
    for r in results:
        print(f"  [{r[0]}] ({r[1]}) {r[2]}: {r[3][:80] if r[3] else ''}")
    conn.close()

def connections(node_id):
    conn = get_conn()
    c = conn.cursor()
    node = c.execute('SELECT title FROM nodes WHERE id=?', (node_id,)).fetchone()
    if not node:
        print(f"Nodo {node_id} no existe")
        return
    print(f"=== CONEXIONES DE: {node[0]} (id={node_id}) ===")
    # Salientes
    out = c.execute('''
        SELECT n.id, n.title, c.relation, c.description
        FROM connections c JOIN nodes n ON c.target_id = n.id
        WHERE c.source_id = ?
    ''', (node_id,)).fetchall()
    if out:
        print("  SALE HACIA →")
        for r in out:
            print(f"    --[{r[2]}]--> [{r[0]}] {r[1]}")
    # Entrantes
    inp = c.execute('''
        SELECT n.id, n.title, c.relation, c.description
        FROM connections c JOIN nodes n ON c.source_id = n.id
        WHERE c.target_id = ?
    ''', (node_id,)).fetchall()
    if inp:
        print("  LLEGA DESDE ←")
        for r in inp:
            print(f"    [{r[0]}] {r[1]} --[{r[2]}]-->")
    conn.close()

def errors():
    conn = get_conn()
    c = conn.cursor()
    print("=== ERRORES → APRENDIZAJES ===")
    errs = c.execute("SELECT id, title, content FROM nodes WHERE type='error'").fetchall()
    for e in errs:
        print(f"\n  ❌ {e[1]}: {e[2][:80]}")
        learned = c.execute('''
            SELECT n.title FROM connections c
            JOIN nodes n ON c.target_id = n.id
            WHERE c.source_id = ? AND c.relation = 'generó'
        ''', (e[0],)).fetchall()
        for l in learned:
            print(f"     ✅ → {l[0]}")
    conn.close()


def recent(n=10):
    conn = get_conn()
    c = conn.cursor()
    results = c.execute('''
        SELECT id, type, title, created_at
        FROM nodes ORDER BY created_at DESC LIMIT ?
    ''', (n,)).fetchall()
    print(f"=== ÚLTIMOS {n} NODOS ===")
    for r in results:
        print(f"  [{r[0]}] ({r[1]}) {r[2]} — {r[3]}")
    conn.close()

def add_node(type, title, content, file_path=None, file_section=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO nodes (type, title, content, file_path, file_section) VALUES (?,?,?,?,?)',
              (type, title, content, file_path, file_section))
    new_id = c.lastrowid
    conn.commit()
    print(f"✅ Nodo creado: [{new_id}] ({type}) {title}")
    conn.close()
    return new_id

def connect_nodes(source_id, target_id, relation, description=None):
    conn = get_conn()
    c = conn.cursor()
    s = c.execute('SELECT title FROM nodes WHERE id=?', (source_id,)).fetchone()
    t = c.execute('SELECT title FROM nodes WHERE id=?', (target_id,)).fetchone()
    if not s or not t:
        print("❌ Uno de los nodos no existe")
        return
    c.execute('INSERT INTO connections (source_id, target_id, relation, description) VALUES (?,?,?,?)',
              (source_id, target_id, relation, description))
    conn.commit()
    print(f"✅ Conexión: {s[0]} --[{relation}]--> {t[0]}")
    conn.close()

def tag_node(node_id, tag_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
    tag_id = c.execute('SELECT id FROM tags WHERE name=?', (tag_name,)).fetchone()[0]
    c.execute('INSERT OR IGNORE INTO node_tags (node_id, tag_id) VALUES (?,?)', (node_id, tag_id))
    conn.commit()
    node = c.execute('SELECT title FROM nodes WHERE id=?', (node_id,)).fetchone()
    print(f"✅ Tag '{tag_name}' → {node[0]}")
    conn.close()

def trace(node_id, depth=2):
    """Traza completa: todo lo que toca un nodo, hasta profundidad 2"""
    conn = get_conn()
    c = conn.cursor()
    node = c.execute('SELECT type, title, content FROM nodes WHERE id=?', (node_id,)).fetchone()
    if not node:
        print(f"Nodo {node_id} no existe")
        return
    print(f"=== TRAZA DE: [{node_id}] ({node[0]}) {node[1]} ===")
    print(f"  {node[2]}")
    
    visited = {node_id}
    frontier = [node_id]
    for d in range(depth):
        next_frontier = []
        for nid in frontier:
            # Conexiones salientes
            out = c.execute('''
                SELECT c.target_id, n.type, n.title, c.relation
                FROM connections c JOIN nodes n ON c.target_id = n.id
                WHERE c.source_id = ? AND c.target_id NOT IN ({})
            '''.format(','.join('?' * len(visited))), (nid, *visited)).fetchall()
            for r in out:
                indent = "  " * (d + 1)
                print(f"{indent}→ [{r[2]}]--> [{r[0]}] ({r[1]}) {r[2]}")
                visited.add(r[0])
                next_frontier.append(r[0])
            # Conexiones entrantes
            inp = c.execute('''
                SELECT c.source_id, n.type, n.title, c.relation
                FROM connections c JOIN nodes n ON c.source_id = n.id
                WHERE c.target_id = ? AND c.source_id NOT IN ({})
            '''.format(','.join('?' * len(visited))), (nid, *visited)).fetchall()
            for r in inp:
                indent = "  " * (d + 1)
                print(f"{indent}← [{r[3]}]-- [{r[0]}] ({r[1]}) {r[2]}")
                visited.add(r[0])
                next_frontier.append(r[0])
        frontier = next_frontier
    print(f"\n  Total nodos alcanzados: {len(visited)}")
    conn.close()


def stats():
    conn = get_conn()
    c = conn.cursor()
    n = c.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]
    co = c.execute('SELECT COUNT(*) FROM connections').fetchone()[0]
    t = c.execute('SELECT COUNT(*) FROM tags').fetchone()[0]
    print(f"=== DANA BRAIN STATS ===")
    print(f"  Nodos: {n}")
    print(f"  Conexiones: {co}")
    print(f"  Tags: {t}")
    print(f"  Ratio conexiones/nodo: {co/n:.1f}" if n > 0 else "")
    print(f"\n  Por tipo:")
    types = c.execute('SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY COUNT(*) DESC').fetchall()
    for tp in types:
        print(f"    {tp[0]}: {tp[1]}")
    print(f"\n  Por tag:")
    tags = c.execute('''
        SELECT t.name, COUNT(*) FROM tags t
        JOIN node_tags nt ON t.id = nt.tag_id
        GROUP BY t.name ORDER BY COUNT(*) DESC
    ''').fetchall()
    for tg in tags:
        print(f"    {tg[0]}: {tg[1]}")
    conn.close()

def list_types():
    conn = get_conn()
    c = conn.cursor()
    types = c.execute('SELECT DISTINCT type FROM nodes ORDER BY type').fetchall()
    print("=== TIPOS DE NODOS ===")
    for t in types:
        print(f"  • {t[0]}")
    conn.close()

def list_tags():
    conn = get_conn()
    c = conn.cursor()
    tags = c.execute('''
        SELECT t.name, COUNT(*) FROM tags t
        JOIN node_tags nt ON t.id = nt.tag_id
        GROUP BY t.name ORDER BY t.name
    ''').fetchall()
    print("=== ETIQUETAS ===")
    for t in tags:
        print(f"  • {t[0]} ({t[1]} nodos)")
    conn.close()

# ===== CLI =====
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if cmd == 'whoami': whoami()
    elif cmd == 'search' and args: search(' '.join(args))
    elif cmd == 'tag' and args: by_tag(args[0])
    elif cmd == 'connections' and args: connections(int(args[0]))
    elif cmd == 'errors': errors()
    elif cmd == 'recent': recent(int(args[0]) if args else 10)
    elif cmd == 'add' and len(args) >= 3:
        fp = args[3] if len(args) > 3 else None
        fs = args[4] if len(args) > 4 else None
        add_node(args[0], args[1], args[2], fp, fs)
    elif cmd == 'connect' and len(args) >= 3:
        desc = args[3] if len(args) > 3 else None
        connect_nodes(int(args[0]), int(args[1]), args[2], desc)
    elif cmd == 'tag_node' and len(args) >= 2: tag_node(int(args[0]), args[1])
    elif cmd == 'trace' and args: trace(int(args[0]))
    elif cmd == 'stats': stats()
    elif cmd == 'types': list_types()
    elif cmd == 'tags': list_tags()
    else:
        print(f"Comando no reconocido: {cmd}")
        print(__doc__)
