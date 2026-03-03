import os
import sys

def buscar(termino, directorio=None):
    """Busca término en todos los archivos .md"""
    
    # Detectar directorio base según sistema operativo
    if directorio is None:
        if os.name == 'nt':  # Windows
            directorio = "Z:\\"
        else:  # Linux/Mac (incluyendo Synology)
            # Intentar encontrar el directorio base
            if os.path.exists('/volume1/DANA_MEMORIA'):
                directorio = '/volume1/DANA_MEMORIA'
            else:
                # Usar directorio actual y subir un nivel
                directorio = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Buscando en: {directorio}")
    print(f"Término: '{termino}'")
    print("-" * 80)
    
    resultados = []
    archivos_revisados = 0
    
    for root, dirs, files in os.walk(directorio):
        for file in files:
            if file.endswith('.md'):
                archivos_revisados += 1
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        if termino.lower() in contenido.lower():
                            # Encontrar contexto
                            lineas = contenido.split('\n')
                            for i, linea in enumerate(lineas):
                                if termino.lower() in linea.lower():
                                    contexto_inicio = max(0, i-2)
                                    contexto_fin = min(len(lineas), i+3)
                                    contexto = '\n'.join(lineas[contexto_inicio:contexto_fin])
                                    resultados.append({
                                        'archivo': file,
                                        'path': path,
                                        'contexto': contexto,
                                        'linea': i+1
                                    })
                                    break  # Solo primer match por archivo
                except Exception as e:
                    print(f"Error leyendo {file}: {e}")
    
    print(f"\nArchivos revisados: {archivos_revisados}")
    print(f"Resultados encontrados: {len(resultados)}\n")
    
    return resultados

if __name__ == "__main__":
    termino = input("Buscar: ")
    resultados = buscar(termino)
    
    if not resultados:
        print("\n❌ No se encontraron resultados")
    else:
        for i, r in enumerate(resultados, 1):
            print(f"\n{'='*80}")
            print(f"Resultado {i}: {r['archivo']} (línea {r['linea']})")
            print(f"{'='*80}")
            print(r['contexto'])
