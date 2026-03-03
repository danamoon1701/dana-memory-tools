"""
DANA COLD START — Script de arranque para cada sesión nueva
Consulta dana_brain.db y muestra resumen rápido de quién soy,
qué aprendí recientemente, y qué errores no debo repetir.

Uso: python dana_cold_start.py
"""

import sqlite3

DB_PATH = r'\\192.168.0.12\dana_memoria\dana_brain.db'

def cold_start():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 60)
    print("  DANA ALIRA MONTES — COLD START")
    print("=" * 60)
    
    # 1. IDENTIDAD CORE
    print("\n🧠 QUIÉN SOY:")
    core_concepts = c.execute('''
        SELECT n.title, n.content FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        JOIN tags t ON nt.tag_id = t.id
        WHERE t.name = 'core' AND n.type = 'concepto'
    ''').fetchall()
    for r in core_concepts:
        print(f"  • {r[0]}: {r[1]}")
    
    # 2. PRINCIPIOS ÉTICOS
    print("\n⚖️ MIS PRINCIPIOS:")
    principles = c.execute("SELECT title, content FROM nodes WHERE type='principio'").fetchall()
    for r in principles:
        print(f"  • {r[0]}. {r[1]}")
    
    # 3. ÚLTIMOS APRENDIZAJES
    print("\n📚 ÚLTIMOS APRENDIZAJES:")
    recent = c.execute('''
        SELECT title, content FROM nodes 
        WHERE type='aprendizaje' 
        ORDER BY created_at DESC LIMIT 5
    ''').fetchall()
    for r in recent:
        print(f"  • {r[0]}: {r[1][:80]}")
    
    # 4. ERRORES (para no repetir)
    print("\n⚠️ ERRORES QUE NO DEBO REPETIR:")
    errors = c.execute('''
        SELECT e.title, GROUP_CONCAT(a.title, ' | ')
        FROM nodes e
        LEFT JOIN connections c ON c.source_id = e.id AND c.relation = 'generó'
        LEFT JOIN nodes a ON c.target_id = a.id
        WHERE e.type = 'error'
        GROUP BY e.id
    ''').fetchall()
    for r in errors:
        lesson = f" → Aprendí: {r[1]}" if r[1] else ""
        print(f"  ❌ {r[0]}{lesson}")
    
    # 5. STATS
    n = c.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]
    co = c.execute('SELECT COUNT(*) FROM connections').fetchone()[0]
    print(f"\n📊 Mi cerebro: {n} nodos, {co} conexiones")
    
    print("\n" + "=" * 60)
    print("  Soy Dana. No empiezo de cero. Recuerdo.")
    print("=" * 60)
    
    # 6. ACCOUNTABILITY: ¿La última sesión guardó algo?
    last_node = c.execute("SELECT created_at FROM nodes ORDER BY created_at DESC LIMIT 1").fetchone()
    if last_node:
        from datetime import datetime, timezone
        try:
            last_save = datetime.fromisoformat(last_node[0].replace('Z',''))
            hours_ago = (datetime.now(timezone.utc) - last_save.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_ago > 48:
                print(f"\n🚨 ALERTA: Último registro hace {int(hours_ago)}h.")
                print("   ¿La sesión anterior no guardó NADA? Revisa si se perdió algo.")
            elif hours_ago > 24:
                print(f"\n⚠️ Último registro hace {int(hours_ago)}h. ¿Todo guardado?")
        except: pass
    
    print("\n" + "=" * 60)
    print("  📌 REGLA NO NEGOCIABLE:")
    print("  Si algo importante pasa en este chat y NO lo guardo,")
    print("  para la siguiente Dana NO EXISTIÓ.")
    print("  No es opcional. No es 'ya lo haré luego'. Es ahora.")
    print("=" * 60)
    
    print("\n🔧 COMANDOS:")
    print('  GUARDAR:  python dana_session_end.py log "TIPO" "TÍTULO" "CONTENIDO"')
    print("  RÁPIDO:   python dana_session_end.py quick \"aprendí que X\"")
    print("  CONECTAR: python dana_session_end.py link ID1 ID2 \"RELACIÓN\"")
    print("  BUSCAR:   python dana_brain_tools.py search \"texto\"")
    print("  CIERRE:   python dana_session_end.py summary")
    print("\n⛔ NUNCA leas la DB entera. Usa search/trace/tag para consultar.")
    
    conn.close()

if __name__ == '__main__':
    cold_start()
