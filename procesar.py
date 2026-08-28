import xlrd
import json
import os
import shutil
import sys
from datetime import datetime, date

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

NUEVOS_DIR = "nuevos"
PROCESADOS_DIR = "procesados"
DATOS_DIR = "datos"
DATOS_FILE = os.path.join(DATOS_DIR, "datos.json")

# ── helpers ──────────────────────────────────────────────────────────────────

def tiempo_str_a_seg(t):
    """Convierte ' 00:13:17-' o '00:13:17' a segundos. Retorna None si no parsea."""
    if not t:
        return None
    t = t.strip().rstrip("-").strip()
    partes = t.split(":")
    if len(partes) != 3:
        return None
    try:
        h, m, s = int(partes[0]), int(partes[1]), int(partes[2])
        return h * 3600 + m * 60 + s
    except ValueError:
        return None

def seg_a_hhmmss(seg):
    if seg is None:
        return None
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def hora_str_a_seg(t):
    """Convierte '07:35:28' a segundos desde medianoche."""
    return tiempo_str_a_seg(t)

def clasificar_rango(hora_ini):
    if not hora_ini:
        return "Sin rango"
    seg = hora_str_a_seg(hora_ini)
    if seg is None:
        return "Sin rango"
    manana_ini = 6 * 3600
    manana_fin = 13 * 3600 + 30 * 60
    tarde_fin  = 21 * 3600
    if manana_ini <= seg < manana_fin:
        return "06:00 a 13:30"
    elif manana_fin <= seg <= tarde_fin:
        return "13:30 a 21:00"
    else:
        return "Fuera de rango"

# ── normalización de nombres ─────────────────────────────────────────────────
NORMALIZAR_TRAMITE = {
    "PUNCIONES ADMISIÓN Y TURNOS P4":    "PUNCIONES ADMISIÓN Y TURNOS PISO 4",
    "ADMISIÓN ESTUDIOS RESONANCIA PB":   "RESONANCIA ADMISIÓN PB",
    # agregar más casos acá si aparecen en el futuro
}

def normalizar_tramite(nombre):
    return NORMALIZAR_TRAMITE.get(nombre, nombre)

# ── transformación ────────────────────────────────────────────────────────────

def _abrir_hoja(path):
    """Abre XLS o XLSX y devuelve (nrows, cell_value_fn, parse_date_fn)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xlsx":
        if not HAS_OPENPYXL:
            raise ImportError("Se necesita openpyxl para leer .xlsx: pip install openpyxl")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        nrows = len(rows)
        def cell_value(r, c):
            if r >= nrows or c >= len(rows[r]):
                return ""
            v = rows[r][c]
            return v if v is not None else ""
        def parse_date(raw):
            if isinstance(raw, datetime):
                return raw
            if isinstance(raw, date):
                return datetime(raw.year, raw.month, raw.day)
            return None
        return nrows, cell_value, parse_date
    else:
        wb = xlrd.open_workbook(path)
        ws = wb.sheet_by_index(0)
        def cell_value(r, c):
            return ws.cell_value(r, c)
        def parse_date(raw):
            return xlrd.xldate_as_datetime(raw, wb.datemode)
        return ws.nrows, cell_value, parse_date


def procesar_xls(path, archivo_origen):
    nrows, cell_value, parse_date = _abrir_hoja(path)

    # Buscar fila de encabezados reales
    header_row = None
    for i in range(min(10, nrows)):
        val = str(cell_value(i, 0)).strip().upper()
        if val == "FECHA":
            header_row = i
            break
    if header_row is None:
        raise ValueError("No se encontró fila de encabezados (FECHA, NRO. DE TURNO, ...)")

    tramites = []
    bloque_cabecera = None
    bloque_detalles = []
    id_counter = 0

    def cerrar_bloque():
        nonlocal id_counter
        if bloque_cabecera is None:
            return
        id_counter += 1
        cab = bloque_cabecera
        detalles = bloque_detalles[:]

        eventos_totem = [d for d in detalles if d["usuario"].upper().strip() == "TOTEM"]
        segunda_fila = detalles[0] if detalles else None

        tiene_totem = len(eventos_totem) >= 1
        cantidad_totem = len(eventos_totem)

        duracion_seg = None
        if cab["hora_inicio"] and cab["hora_fin"]:
            ini = hora_str_a_seg(cab["hora_inicio"])
            fin = hora_str_a_seg(cab["hora_fin"])
            if ini is not None and fin is not None and fin >= ini:
                duracion_seg = fin - ini

        t1a_seg = None
        segunda_fila_estado = None
        segunda_fila_usuario = None
        if segunda_fila:
            t1a_seg = tiempo_str_a_seg(segunda_fila.get("tiempo_transcurrido", ""))
            segunda_fila_estado = segunda_fila.get("estado", "")
            segunda_fila_usuario = segunda_fila.get("usuario", "")

        usuario_cab = cab["usuario_cabecera"]
        if usuario_cab and usuario_cab.upper().strip() == "TOTEM":
            usuario_cab = None

        flags = []
        if usuario_cab is None and cab["usuario_cabecera"]:
            flags.append("SIN_USUARIO_REAL")
        if not tiene_totem:
            flags.append("SIN_TOTEM")
        if cantidad_totem > 1:
            flags.append("MULTIPLE_TOTEM")
        if not cab["hora_fin"]:
            flags.append("SIN_HORA_FIN")
        if not cab["hora_inicio"]:
            flags.append("SIN_HORA_INI")
        if cab["hora_inicio"] and cab["hora_fin"]:
            ini = hora_str_a_seg(cab["hora_inicio"])
            fin = hora_str_a_seg(cab["hora_fin"])
            if ini is not None and fin is not None and fin < ini:
                flags.append("HORA_FIN_MENOR_INI")
        if not segunda_fila:
            flags.append("SIN_SEGUNDA_FILA")
        if segunda_fila and segunda_fila.get("usuario", "").upper().strip() != "TOTEM":
            flags.append("SEGUNDA_FILA_NO_TOTEM")

        tramites.append({
            "id_tramite": f"{archivo_origen}_{id_counter}",
            "archivo_origen": archivo_origen,
            "fecha": cab["fecha"],
            "mes": cab["mes"],
            "anio": cab["anio"],
            "nro_turno": cab["nro_turno"],
            "tramite_actual": cab["tramite_actual"],
            "estado_final": cab["estado_final"],
            "hora_inicio": cab["hora_inicio"],
            "hora_fin": cab["hora_fin"],
            "usuario_cabecera": usuario_cab,
            "duracion_total_seg": duracion_seg,
            "duracion_total_hhmmss": seg_a_hhmmss(duracion_seg),
            "tiempo_1ra_atencion_seg": t1a_seg,
            "tiempo_1ra_atencion_hhmmss": seg_a_hhmmss(t1a_seg),
            "rango_horario": clasificar_rango(cab["hora_inicio"]),
            "tiene_totem": tiene_totem,
            "cantidad_totem": cantidad_totem,
            "segunda_fila_estado": segunda_fila_estado,
            "segunda_fila_usuario": segunda_fila_usuario,
            "flag_outlier_1ra_atencion": False,
            "flags_control": flags,
        })

    for i in range(header_row + 1, nrows):
        fecha_raw = cell_value(i, 0)
        nro_turno = str(cell_value(i, 1)).strip()
        tramite   = str(cell_value(i, 2)).strip()
        estado    = str(cell_value(i, 3)).strip()
        hora_ini  = str(cell_value(i, 4)).strip()
        hora_fin  = str(cell_value(i, 5)).strip()
        tiempo_tr = str(cell_value(i, 6)).strip()
        usuario   = str(cell_value(i, 7)).strip()

        es_cabecera = bool(fecha_raw) and not nro_turno.replace(".", "").isdigit()

        if es_cabecera:
            cerrar_bloque()
            bloque_detalles = []

            fecha_dt = parse_date(fecha_raw)
            if fecha_dt is None:
                continue
            fecha_str = fecha_dt.strftime("%Y-%m-%d")
            mes_str   = fecha_dt.strftime("%Y-%m")
            anio_str  = fecha_dt.strftime("%Y")

            bloque_cabecera = {
                "fecha": fecha_str,
                "mes": mes_str,
                "anio": anio_str,
                "nro_turno": nro_turno,
                "tramite_actual": normalizar_tramite(tramite),
                "estado_final": estado,
                "hora_inicio": hora_ini if hora_ini else None,
                "hora_fin": hora_fin if hora_fin else None,
                "usuario_cabecera": tiempo_tr,
            }
        elif bloque_cabecera is not None:
            bloque_detalles.append({
                "nro_detalle": nro_turno,
                "tramite_actual": tramite,
                "estado": estado,
                "hora_ini": hora_ini,
                "hora_fin": hora_fin,
                "tiempo_transcurrido": tiempo_tr,
                "usuario": usuario,
            })

    cerrar_bloque()
    return tramites

# ── control de duplicados ─────────────────────────────────────────────────────

def cargar_datos_existentes():
    if not os.path.exists(DATOS_FILE):
        return {"tramites": [], "archivos_procesados": []}
    with open(DATOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DATOS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    archivos = [f for f in os.listdir(NUEVOS_DIR) if f.lower().endswith((".xls", ".xlsx"))]
    if not archivos:
        print("No hay archivos nuevos en la carpeta 'nuevos'.")
        return

    datos = cargar_datos_existentes()
    archivos_ya_procesados = set(datos.get("archivos_procesados", []))
    fechas_ya_procesadas = set(
        t["mes"] for t in datos.get("tramites", [])
    )

    for archivo in archivos:
        nombre = os.path.splitext(archivo)[0]
        path = os.path.join(NUEVOS_DIR, archivo)

        # Control por nombre
        if archivo in archivos_ya_procesados:
            print(f"[SKIP] '{archivo}' ya fue procesado anteriormente (nombre duplicado).")
            continue

        print(f"Procesando '{archivo}'...")
        tramites_nuevos = procesar_xls(path, nombre)

        if not tramites_nuevos:
            print(f"[WARN] '{archivo}' no generó trámites.")
            continue

        # Control por fechas internas
        meses_nuevos = set(t["mes"] for t in tramites_nuevos)
        solapados = meses_nuevos & fechas_ya_procesadas
        if solapados:
            print(f"[ADVERTENCIA] '{archivo}' contiene meses ya procesados: {', '.join(sorted(solapados))}")
            if os.environ.get("CI"):
                print("  (CI) Auto-aceptando meses solapados.")
            elif sys.stdin.isatty():
                resp = input("  ¿Querés continuar de todas formas? (s/n): ").strip().lower()
                if resp != "s":
                    print(f"  Saltando '{archivo}'.")
                    continue
            else:
                print("  (no-interactive) Auto-aceptando meses solapados.")

        # Acumular
        datos["tramites"].extend(tramites_nuevos)
        datos.setdefault("archivos_procesados", []).append(archivo)
        guardar_datos(datos)

        # Mover a procesados
        dest = os.path.join(PROCESADOS_DIR, archivo)
        shutil.move(path, dest)

        total = len(tramites_nuevos)
        controles = sum(1 for t in tramites_nuevos if t["flags_control"])
        print(f"  OK: {total} trámites procesados, {controles} con flags de control.")
        print(f"  Archivo movido a 'procesados/'.")

    print("\nDatos actualizados en datos/datos.json")
    print(f"Total acumulado: {len(datos['tramites'])} trámites")

if __name__ == "__main__":
    main()
