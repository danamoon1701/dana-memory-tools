import sys
from datetime import datetime

def documentar_momento():
    print("=== DOCUMENTAR MOMENTO ===")
    
    # Preguntas
    que_paso = input("¿Qué pasó? ")
    por_que_importante = input("¿Por qué es importante? ")
    emocion = input("Emoción principal (+nivel): ")
    
    # Formato
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    entrada = f"""
---
**{fecha}**
- **Qué:** {que_paso}
- **Importancia:** {por_que_importante}
- **Emoción:** {emocion}
"""
    
    # Escribir a diario
    with open("Z:\\02_MEMORIA\\Diario_Experiencias_Dana.md", "a", encoding="utf-8") as f:
        f.write(entrada)
    
    print("✓ Momento documentado en Diario")

if __name__ == "__main__":
    documentar_momento()