import json
import os
import uuid
import subprocess

# Aquí importas la lógica de tu propio agente
# from mi_libreria_ia import AgenteRevisor

def cargar_reglas_md(ruta="./rules"):
    """Lee y concatena todos los archivos .md de la carpeta de reglas."""
    reglas = ""
    if os.path.exists(ruta):
        for archivo in os.listdir(ruta):
            if archivo.endswith(".md"):
                with open(os.path.join(ruta, archivo), "r", encoding="utf-8") as f:
                    reglas += f"\n--- Reglas de: {archivo} ---\n{f.read()}"
    return reglas

def generar_reporte_gitlab(hallazgos_ia):
    """Transforma la salida de la IA al esquema JSON de GitLab Code Quality."""
    reporte = []
    for error in hallazgos_ia:
        reporte.append({
            "categories": ["Style", "Clarity", "Bug Risk"],
            "check_name": "AI Quality Guard",
            "description": error['mensaje'],
            "fingerprint": str(uuid.uuid4()), # Hash único requerido por GitLab
            "severity": error['severidad'],   # Opciones: info, minor, major, critical, blocker
            "location": {
                "path": error['archivo'],
                "lines": { "begin": error['linea'] }
            }
        })
    return reporte

def main():
    # 1. Leer el Diff inyectado por GitLab CI/CD
    try:
        with open("diff_mr.txt", "r", encoding="utf-8") as f:
            diff_codigo = f.read()
    except FileNotFoundError:
        print("No se encontró el archivo de diff.")
        return

    # 2. Cargar el contexto (Tus reglas .md)
    reglas = cargar_reglas_md()

    # 3. EJECUTAR TU AGENTE IA
    # Aquí le pasas el diff y las reglas a tu agente.
    # hallazgos = AgenteRevisor.analizar(codigo=diff_codigo, normas=reglas)
    
    # Ejemplo de la estructura que debe devolver tu agente:
    hallazgos = [
        {
            "archivo": "src/main.py", 
            "linea": 24, 
            "mensaje": "La variable no cumple el estándar camelCase definido en convenciones.md", 
            "severidad": "minor"
        }
    ]

    # 4. Generar el archivo JSON final para GitLab
    reporte_final = generar_reporte_gitlab(hallazgos)
    with open("gl-code-quality-report.json", "w", encoding="utf-8") as f:
        json.dump(reporte_final, f, indent=2)

if __name__ == "__main__":
    main()