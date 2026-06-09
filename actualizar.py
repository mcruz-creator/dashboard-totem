"""
actualizar.py
─────────────
Flujo completo en un solo comando:
  1. Procesa los XLS nuevos de /nuevos
  2. Regenera el dashboard.html
  3. Sube el HTML a GitHub Pages

Uso:
  python actualizar.py
"""

import os, sys, json, base64, subprocess, urllib.request, urllib.error
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG    = os.path.join(BASE_DIR, "config.json")
HTML_FILE = os.path.join(BASE_DIR, "dashboard.html")

# ── Colores para la consola ───────────────────────────────────────────────────
OK   = "\033[92m✔\033[0m"
ERR  = "\033[91m✘\033[0m"
INFO = "\033[94m→\033[0m"
WARN = "\033[93m⚠\033[0m"

def paso(n, desc):
    print(f"\n\033[1m[{n}/3] {desc}\033[0m")

# ── 1. Procesar XLS ───────────────────────────────────────────────────────────
def procesar():
    paso(1, "Procesando archivos nuevos...")
    nuevos_dir = os.path.join(BASE_DIR, "nuevos")
    archivos = [f for f in os.listdir(nuevos_dir) if f.lower().endswith((".xls", ".xlsx"))]
    if not archivos:
        print(f"  {WARN}  No hay archivos en /nuevos. Continuando con datos existentes.")
        return False   # no hubo nuevos, pero seguimos igual

    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "procesar.py")],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"  {ERR}  Error al procesar:\n{result.stderr}")
        sys.exit(1)
    return True

# ── 2. Generar HTML ───────────────────────────────────────────────────────────
def generar():
    paso(2, "Generando dashboard.html...")
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "generar_html.py")],
        cwd=BASE_DIR, capture_output=True, text=True
    )
    print(f"  {OK}  {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"  {ERR}  Error al generar:\n{result.stderr}")
        sys.exit(1)

# ── 3. Subir a GitHub ─────────────────────────────────────────────────────────
def subir_github():
    paso(3, "Subiendo a GitHub Pages...")

    with open(CONFIG) as f:
        cfg = json.load(f)

    token  = cfg["github_token"]
    owner  = cfg["github_owner"]
    repo   = cfg["github_repo"]
    branch = cfg["github_branch"]
    path   = cfg["github_file"]
    url    = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/vnd.github+json",
        "User-Agent":    "python",
    }

    # Obtener SHA del archivo actual (necesario para actualizar)
    sha = None
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            sha = json.load(r).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  {ERR}  Error consultando SHA: {e.code}")
            sys.exit(1)
        # 404 = archivo no existe aún, lo creamos

    # Leer y encodear el HTML
    with open(HTML_FILE, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "message": f"Dashboard actualizado · {fecha}",
        "content": content_b64,
        "branch":  branch,
    }
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            json.load(r)
        pages_url = f"https://{owner}.github.io/{repo}/"
        print(f"  {OK}  Publicado en: {pages_url}")
        print(f"\n  \033[1m🔗 {pages_url}\033[0m\n")
    except urllib.error.HTTPError as e:
        print(f"  {ERR}  Error subiendo: {e.code}\n{e.read().decode()[:400]}")
        sys.exit(1)

# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n\033[1m══ Actualización Dashboard Tótem ══\033[0m")
    procesar()
    generar()
    subir_github()
    print(f"{OK}  ¡Todo listo!\n")
