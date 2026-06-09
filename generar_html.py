import json
import os
from statistics import median

DATOS_FILE = os.path.join("datos", "datos.json")
OUTPUT_FILE = "dashboard.html"

def cargar_datos():
    with open(DATOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def seg_a_mmss(seg):
    if seg is None:
        return "—"
    m = seg // 60
    s = seg % 60
    return f"{m:02d}:{s:02d}"

def seg_a_hhmmss(seg):
    if seg is None:
        return "—"
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def generar_html(tramites):
    data_js = json.dumps(tramites, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Atención por Tótem</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  :root {{
    --bg:          #f0f2f5;
    --surface:     #ffffff;
    --surface-2:   #f8f9fb;
    --border:      rgba(0,0,0,0.07);
    --border-2:    rgba(0,0,0,0.12);
    --text-1:      #111827;
    --text-2:      #6b7280;
    --text-3:      #d1d5db;
    --blue:        #2563eb;
    --cyan:        #0891b2;
    --purple:      #7c3aed;
    --green:       #16a34a;
    --orange:      #ea580c;
    --red:         #dc2626;
    --radius:      8px;
    --shadow:      0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', 'Segoe UI', sans-serif; background: var(--bg); color: var(--text-1); font-size: 13px; line-height: 1.5; }}
  ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border-2); border-radius: 4px; }}
  * {{ scrollbar-width: thin; scrollbar-color: var(--border-2) transparent; }}

  /* ── HEADER ── */
  .header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 200;
    box-shadow: var(--shadow);
  }}
  .header-logo {{ display: flex; align-items: center; gap: 10px; }}
  .header-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--blue);
    flex-shrink: 0;
  }}
  .header-title {{ font-size: 14px; font-weight: 600; color: var(--text-1); letter-spacing: 0.1px; }}
  .header-sub {{ font-size: 11px; color: var(--text-2); margin-top: 1px; }}
  .header-right {{ font-size: 11px; color: var(--text-2); text-align: right; }}

  /* ── LAYOUT ── */
  .layout {{ display: flex; margin-top: 52px; min-height: calc(100vh - 52px); }}

  /* ── SIDEBAR ── */
  .sidebar {{
    width: 216px; min-width: 216px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 16px 12px;
    position: fixed;
    top: 52px; bottom: 0;
    overflow-y: auto;
  }}
  .sidebar-section {{
    font-size: 9px; font-weight: 700;
    color: var(--text-3);
    text-transform: uppercase; letter-spacing: 1.2px;
    margin: 16px 0 8px; padding: 0 2px;
  }}
  .sidebar-section:first-child {{ margin-top: 0; }}
  .filter-group {{ margin-bottom: 12px; }}
  .filter-label {{
    font-size: 10px; font-weight: 600;
    color: var(--text-2);
    margin-bottom: 5px; display: block; padding: 0 2px;
  }}
  .filter-label[data-for]::after {{
    content: " " attr(data-count);
    font-size: 9px; color: var(--text-3); font-weight: 400;
  }}
  .date-input {{
    width: 100%; padding: 5px 8px;
    border: 1px solid var(--border-2);
    border-radius: var(--radius);
    font-size: 11px; color: var(--text-1);
    background: var(--surface-2);
    margin-bottom: 4px; outline: none;
  }}
  .date-input:focus {{ border-color: var(--blue); box-shadow: 0 0 0 2px rgba(37,99,235,0.12); }}
  .btn-reset {{
    width: 100%; padding: 7px;
    background: transparent;
    color: var(--blue);
    border: 1px solid var(--border-2);
    border-radius: var(--radius);
    font-size: 11px; font-weight: 600;
    cursor: pointer; margin-top: 12px;
    transition: all 0.15s;
  }}
  .btn-reset:hover {{ background: rgba(37,99,235,0.05); border-color: rgba(37,99,235,0.3); }}

  /* Checklist */
  .filter-list {{
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    max-height: 150px; overflow-y: auto;
  }}
  .filter-item {{
    display: flex; align-items: center; gap: 6px;
    padding: 5px 8px; cursor: pointer;
    border-bottom: 1px solid var(--border);
    transition: background 0.1s;
  }}
  .filter-item:last-child {{ border-bottom: none; }}
  .filter-item:hover {{ background: var(--surface-2); }}
  .filter-item input[type=checkbox] {{
    accent-color: var(--blue); cursor: pointer;
    width: 12px; height: 12px; flex-shrink: 0;
  }}
  .filter-item label {{
    font-size: 11px; color: var(--text-1); cursor: pointer;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .filter-item.todos {{ background: rgba(37,99,235,0.04); }}
  .filter-item.todos label {{ font-weight: 600; color: var(--blue); }}

  /* Chips rango */
  .chips {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .chip {{
    padding: 3px 9px; border-radius: 20px; font-size: 10px;
    cursor: pointer; border: 1px solid var(--border-2);
    background: transparent; color: var(--text-2);
    transition: all 0.15s;
  }}
  .chip.active {{ background: rgba(37,99,235,0.08); color: var(--blue); border-color: rgba(37,99,235,0.3); font-weight: 600; }}

  /* ── MAIN ── */
  .main {{ margin-left: 216px; padding: 18px 20px 32px; flex: 1; min-width: 0; }}

  /* ── KPI CARDS ── */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 16px; }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 16px 14px;
    position: relative; overflow: hidden;
    box-shadow: var(--shadow);
  }}
  .kpi-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--blue);
    border-radius: var(--radius) var(--radius) 0 0;
  }}
  .kpi-card.c2::before {{ background: var(--red); }}
  .kpi-card.c3::before {{ background: var(--purple); }}
  .kpi-card.c4::before {{ background: var(--cyan); }}
  .kpi-card.c5::before {{ background: var(--green); }}
  .kpi-card.c6::before {{ background: var(--orange); }}
  .kpi-label {{
    font-size: 10px; font-weight: 500;
    color: var(--text-2);
    margin-bottom: 10px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    text-transform: uppercase; letter-spacing: 0.4px;
  }}
  .kpi-value {{
    font-size: 28px; font-weight: 700;
    color: var(--text-1); line-height: 1; letter-spacing: -0.5px;
  }}
  .kpi-sub {{ font-size: 10px; color: var(--text-2); margin-top: 6px; }}

  /* ── CARDS (charts/tables) ── */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    box-shadow: var(--shadow);
  }}
  .card-title {{
    font-size: 11px; font-weight: 600;
    color: var(--text-2);
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 14px;
  }}

  /* ── CHARTS ── */
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
  .chart-wrap {{ position: relative; height: 220px; }}
  .full {{ grid-column: 1 / -1; }}

  /* ── TABLES ── */
  .tables-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  th {{
    background: var(--surface-2);
    color: var(--text-2); font-weight: 600;
    padding: 7px 10px; text-align: left;
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.4px;
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0;
  }}
  td {{
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    color: var(--text-1);
  }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: var(--surface-2); }}
  .td-num {{ text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }}

  /* ── CONTROLES ── */
  .badge {{
    display: inline-block;
    background: #fef3c7; color: #92400e;
    border: 1px solid #fde68a;
    border-radius: 20px; padding: 1px 9px;
    font-size: 10px; font-weight: 700; margin-left: 6px;
  }}
  .flag-tag {{
    display: inline-block; padding: 2px 8px;
    border-radius: 20px; font-size: 10px; font-weight: 500; margin: 1px;
  }}
  .flag-SIN_HORA_FIN        {{ background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }}
  .flag-SIN_USUARIO_REAL    {{ background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }}
  .flag-SIN_TOTEM           {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
  .flag-MULTIPLE_TOTEM      {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
  .flag-SIN_SEGUNDA_FILA    {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
  .flag-HORA_FIN_MENOR_INI  {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
  .flag-SEGUNDA_FILA_NO_TOTEM {{ background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }}
  .no-data {{ color: var(--text-2); font-style: italic; font-size: 12px; padding: 16px 0; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-logo">
    <div class="header-dot"></div>
    <div>
      <div class="header-title">Dashboard · Atención por Tótem</div>
      <div class="header-sub" id="header-subtitle">Cargando...</div>
    </div>
  </div>
  <div class="header-right">
    <span id="header-right"></span>
  </div>
</div>

<div class="layout">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-section">Período</div>
    <div class="filter-group">
      <label class="filter-label" data-for="f-anio">Año</label>
      <div class="filter-list" id="f-anio"></div>
    </div>
    <div class="filter-group">
      <label class="filter-label" data-for="f-mes">Mes</label>
      <div class="filter-list" id="f-mes"></div>
    </div>
    <div class="filter-group">
      <label class="filter-label">Fecha desde</label>
      <input type="date" id="f-fecha-desde" class="date-input">
      <label class="filter-label" style="margin-top:4px;">Fecha hasta</label>
      <input type="date" id="f-fecha-hasta" class="date-input">
    </div>

    <div class="sidebar-section">Trámite</div>
    <div class="filter-group">
      <label class="filter-label" data-for="f-tramite">Tipo</label>
      <div class="filter-list" id="f-tramite"></div>
    </div>

    <div class="sidebar-section">Operativo</div>
    <div class="filter-group">
      <label class="filter-label" data-for="f-usuario">Usuario</label>
      <div class="filter-list" id="f-usuario"></div>
    </div>
    <div class="filter-group">
      <label class="filter-label">Rango horario</label>
      <div class="chips" id="f-rango"></div>
    </div>

    <button class="btn-reset" onclick="resetFiltros()">↺ Limpiar filtros</button>
  </aside>

  <!-- MAIN -->
  <main class="main">

    <!-- KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card c1">
        <div class="kpi-label">Trámites totales</div>
        <div class="kpi-value" id="kpi-total">—</div>
        <div class="kpi-sub" id="kpi-total-sub"></div>
      </div>
      <div class="kpi-card c2">
        <div class="kpi-label">1ra atención prom.</div>
        <div class="kpi-value" id="kpi-1ra-prom">—</div>
        <div class="kpi-sub" id="kpi-1ra-sub"></div>
      </div>
      <div class="kpi-card c3">
        <div class="kpi-label">1ra atención mediana</div>
        <div class="kpi-value" id="kpi-1ra-med">—</div>
        <div class="kpi-sub"></div>
      </div>
      <div class="kpi-card c4">
        <div class="kpi-label">Duración prom. total</div>
        <div class="kpi-value" id="kpi-dur-prom">—</div>
        <div class="kpi-sub">HH:MM:SS</div>
      </div>
      <div class="kpi-card c5">
        <div class="kpi-label">Usuarios activos</div>
        <div class="kpi-value" id="kpi-usuarios">—</div>
        <div class="kpi-sub">distintos</div>
      </div>
      <div class="kpi-card c6">
        <div class="kpi-label">Sin hora fin</div>
        <div class="kpi-value" id="kpi-sin-fin">—</div>
        <div class="kpi-sub">control de calidad</div>
      </div>
    </div>

    <!-- CHARTS -->
    <div class="charts-grid" style="margin-bottom:12px;">
      <div class="card">
        <div class="card-title">Trámites por tipo</div>
        <div class="chart-wrap"><canvas id="chart-tipo"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Trámites por usuario (Top 10)</div>
        <div class="chart-wrap"><canvas id="chart-usuario"></canvas></div>
      </div>
      <div class="card full">
        <div class="card-title">Evolución diaria</div>
        <div class="chart-wrap"><canvas id="chart-evolucion"></canvas></div>
      </div>
      <div class="card full">
        <div class="card-title">Actividad por franja horaria (intervalos de 1 hora)</div>
        <div class="chart-wrap"><canvas id="chart-franjas"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Distribución horaria</div>
        <div class="chart-wrap"><canvas id="chart-rango"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">1ra atención promedio por tipo</div>
        <div class="chart-wrap"><canvas id="chart-1ra"></canvas></div>
      </div>
    </div>

    <!-- TABLES -->
    <div class="tables-grid">
      <div class="card">
        <div class="card-title">Resumen por tipo de trámite</div>
        <div id="tabla-tipo"></div>
      </div>
      <div class="card" style="overflow-y:auto; max-height:380px;">
        <div class="card-title" style="position:sticky;top:0;background:#ffffff;padding-bottom:8px;z-index:1;">Resumen por usuario</div>
        <div id="tabla-usuario"></div>
      </div>
    </div>

    <!-- CONTROLES -->
    <div class="card" style="margin-top:12px; margin-bottom:20px;">
      <div class="card-title" style="display:flex;align-items:center;gap:8px;">
        Panel de control de calidad
        <span class="badge" id="badge-controles">0</span>
      </div>

      <!-- Resumen SIN_HORA_FIN por usuario -->
      <div style="margin-bottom:16px;">
        <div style="font-size:11px;font-weight:600;color:var(--text-2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;display:flex;align-items:center;gap:6px;">
          Sin hora fin
          <span style="background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;border-radius:20px;padding:1px 9px;font-size:10px;font-weight:700;" id="badge-sin-fin-detalle">0</span>
          <span style="font-size:10px;color:var(--text-2);font-weight:400;font-style:italic;text-transform:none;letter-spacing:0;">· excluidos de todas las métricas</span>
        </div>
        <div id="tabla-sin-fin-usuario"></div>
      </div>

      <div style="border-top:1px solid var(--border);padding-top:14px;">
        <div style="font-size:11px;font-weight:600;color:var(--text-2);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Otros flags de control</div>
        <div id="tabla-controles"></div>
      </div>
    </div>

  </main>
</div>

<script>
const TODOS_TRAMITES = {data_js};

// SIN_HORA_FIN: excluidos de métricas, solo aparecen en panel de control
const SIN_HORA_FIN = TODOS_TRAMITES.filter(t => t.flags_control && t.flags_control.includes('SIN_HORA_FIN'));
const TRAMITES_BASE = TODOS_TRAMITES.filter(t => !t.flags_control || !t.flags_control.includes('SIN_HORA_FIN'));

// ── Charts instances ──────────────────────────────────────────────────────────
const charts = {{}};

function destroyChart(id) {{
  if (charts[id]) {{ charts[id].destroy(); delete charts[id]; }}
}}

// ── Colores ───────────────────────────────────────────────────────────────────
const COLORES = ['#2563eb','#dc2626','#7c3aed','#0891b2','#16a34a','#ea580c','#db2777','#0284c7','#9333ea','#15803d'];
const RANGO_COLORES = {{'06:00 a 13:30':'#2563eb','13:30 a 21:00':'#dc2626','Fuera de rango':'#ea580c','Sin rango':'#9ca3af'}};
const CHART_FONT_COLOR = '#6b7280';
const CHART_GRID_COLOR = 'rgba(0,0,0,0.05)';

// ── Filtros en cascada con checkboxes ────────────────────────────────────────

function getChecked(id) {{
  const cont = document.getElementById(id);
  const cbTodos = cont.querySelector('input[value="__todos__"]');
  if (!cbTodos || cbTodos.checked) return null;
  const vals = [...cont.querySelectorAll('input[type=checkbox]:not([value="__todos__"])')].filter(cb => cb.checked).map(cb => cb.value);
  return vals.length ? vals : null;
}}

function getChipsActivos(id) {{
  const vals = [...document.querySelectorAll(`#${{id}} .chip.active`)].map(c => c.dataset.val);
  return vals.length ? vals : null;
}}

// Filtra TRAMITES_BASE (excluye SIN_HORA_FIN) con valores explícitos (null = sin filtro)
function filtrar(anios, meses, tramites, usuarios, rangos, desde, hasta) {{
  return TRAMITES_BASE.filter(t => {{
    if (anios    && !anios.includes(t.anio))                return false;
    if (meses    && !meses.includes(t.mes))                 return false;
    if (tramites && !tramites.includes(t.tramite_actual))   return false;
    if (usuarios && !usuarios.includes(t.usuario_cabecera)) return false;
    if (rangos   && !rangos.includes(t.rango_horario))      return false;
    if (desde    && t.fecha < desde)                        return false;
    if (hasta    && t.fecha > hasta)                        return false;
    return true;
  }});
}}

function aplicarFiltros() {{
  return filtrar(
    getChecked('f-anio'), getChecked('f-mes'), getChecked('f-tramite'),
    getChecked('f-usuario'), getChipsActivos('f-rango'),
    document.getElementById('f-fecha-desde').value,
    document.getElementById('f-fecha-hasta').value
  );
}}

// Construye la lista de checkboxes. Siempre empieza con Todos seleccionado.
function construirLista(id, valores, onChange) {{
  const cont = document.getElementById(id);
  cont.innerHTML = '';

  const mkItem = (value, text, checked, isTodos) => {{
    const item = document.createElement('div');
    item.className = 'filter-item' + (isTodos ? ' todos' : '');
    const cb  = document.createElement('input');
    cb.type = 'checkbox'; cb.value = value; cb.checked = checked;
    const lbl = document.createElement('label');
    lbl.textContent = text; lbl.title = text;
    item.appendChild(cb); item.appendChild(lbl);
    // Clic en cualquier parte de la fila
    item.addEventListener('click', e => {{
      if (e.target === cb) return; // el checkbox ya maneja su propio evento
      cb.checked = isTodos ? true : !cb.checked;
      cb.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }});
    cont.appendChild(item);
    return cb;
  }};

  const cbTodos = mkItem('__todos__', 'Todos', true, true);
  const cbItems = valores.map(v => mkItem(v, v, false, false));

  const syncTodos = () => {{
    const alguno = cbItems.some(cb => cb.checked);
    cbTodos.checked = !alguno;
    // actualizar contador
    const activos = cbItems.filter(cb => cb.checked).length;
    const lbl = document.querySelector(`label[data-for="${{id}}"]`);
    if (lbl) lbl.setAttribute('data-count', activos ? `(${{activos}}/${{valores.length}})` : `(${{valores.length}})`);
  }};

  cbTodos.addEventListener('change', () => {{
    if (cbTodos.checked) cbItems.forEach(cb => cb.checked = false);
    syncTodos();
    onChange();
  }});
  cbItems.forEach(cb => cb.addEventListener('change', () => {{ syncTodos(); onChange(); }}));
  syncTodos();
}}

// Cascada: repobla los filtros downstream del nivel que cambió.
// Lee el estado ACTUAL de los filtros upstream DESPUÉS de cada repoblación.
function cascadaDesde(nivel) {{
  const desde = document.getElementById('f-fecha-desde').value;
  const hasta = document.getElementById('f-fecha-hasta').value;

  if (nivel === 'anio' || nivel === 'fecha') {{
    const meses = uniq(filtrar(getChecked('f-anio'), null, null, null, null, desde, hasta).map(t => t.mes)).sort();
    construirLista('f-mes', meses, () => {{ cascadaDesde('mes'); actualizar(); }});
  }}
  if (nivel === 'anio' || nivel === 'mes' || nivel === 'fecha') {{
    const tramites = uniq(filtrar(getChecked('f-anio'), getChecked('f-mes'), null, null, null, desde, hasta).map(t => t.tramite_actual)).sort();
    construirLista('f-tramite', tramites, () => {{ cascadaDesde('tramite'); actualizar(); }});
  }}
  // Siempre: usuarios depende de anio + mes + tramite actuales
  const usuarios = uniq(filtrar(getChecked('f-anio'), getChecked('f-mes'), getChecked('f-tramite'), null, null, desde, hasta).map(t => t.usuario_cabecera).filter(Boolean)).sort();
  construirLista('f-usuario', usuarios, () => {{ actualizar(); }});
}}

function uniq(arr) {{ return [...new Set(arr)]; }}

function resetFiltros() {{
  // Reconstruir todos los filtros desde cero
  document.getElementById('f-fecha-desde').value = '';
  document.getElementById('f-fecha-hasta').value = '';
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  const anios = uniq(TODOS_TRAMITES.map(t => t.anio)).sort();
  construirLista('f-anio', anios, () => {{ cascadaDesde('anio'); actualizar(); }});
  cascadaDesde('anio');
  actualizar();
}}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function calcKPIs(data) {{
  const total = data.length;
  const t1a = data.map(t => t.tiempo_1ra_atencion_seg).filter(v => v !== null);
  const dur = data.map(t => t.duracion_total_seg).filter(v => v !== null);
  const usuarios = new Set(data.map(t => t.usuario_cabecera).filter(Boolean));
  const sinFin = data.filter(t => !t.hora_fin).length;

  const prom1ra = t1a.length ? Math.round(t1a.reduce((a,b)=>a+b,0)/t1a.length) : null;
  const med1ra  = t1a.length ? mediana(t1a) : null;
  const promDur = dur.length ? Math.round(dur.reduce((a,b)=>a+b,0)/dur.length) : null;

  return {{ total, prom1ra, med1ra, promDur, usuarios: usuarios.size, sinFin }};
}}

function mediana(arr) {{
  const s = [...arr].sort((a,b) => a-b);
  const m = Math.floor(s.length/2);
  return s.length % 2 ? s[m] : Math.round((s[m-1]+s[m])/2);
}}

function segAmmss(seg) {{
  if (seg === null || seg === undefined) return '—';
  if (seg >= 3600) {{
    const h = Math.floor(seg/3600), m = Math.floor((seg%3600)/60), s = seg%60;
    return `${{String(h).padStart(2,'0')}}:${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
  }}
  const m = Math.floor(seg/60), s = seg%60;
  return `${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
}}

function segAhhmmss(seg) {{
  if (seg === null || seg === undefined) return '—';
  const h = Math.floor(seg/3600), m = Math.floor((seg%3600)/60), s = seg%60;
  return `${{String(h).padStart(2,'0')}}:${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
}}

function renderKPIs(data) {{
  const k = calcKPIs(data);
  document.getElementById('kpi-total').textContent = k.total.toLocaleString('es-AR');
  document.getElementById('kpi-total-sub').textContent = `de ${{TODOS_TRAMITES.length.toLocaleString('es-AR')}} total`;
  document.getElementById('kpi-1ra-prom').textContent = segAmmss(k.prom1ra);
  document.getElementById('kpi-1ra-med').textContent  = segAmmss(k.med1ra);
  document.getElementById('kpi-dur-prom').textContent = segAhhmmss(k.promDur);
  document.getElementById('kpi-usuarios').textContent = k.usuarios;
  document.getElementById('kpi-sin-fin').textContent  = k.sinFin;
}}

// ── Agrupaciones ──────────────────────────────────────────────────────────────
function agrupar(data, campo) {{
  const map = {{}};
  data.forEach(t => {{
    const k = t[campo] || '(sin datos)';
    if (!map[k]) map[k] = {{ cant: 0, t1a: [], dur: [] }};
    map[k].cant++;
    if (t.tiempo_1ra_atencion_seg !== null) map[k].t1a.push(t.tiempo_1ra_atencion_seg);
    if (t.duracion_total_seg !== null)      map[k].dur.push(t.duracion_total_seg);
  }});
  return Object.entries(map)
    .map(([k,v]) => ({{
      label: k,
      cant: v.cant,
      prom1ra: v.t1a.length ? Math.round(v.t1a.reduce((a,b)=>a+b,0)/v.t1a.length) : null,
      promDur: v.dur.length ? Math.round(v.dur.reduce((a,b)=>a+b,0)/v.dur.length) : null,
    }}))
    .sort((a,b) => b.cant - a.cant);
}}

// ── Charts ────────────────────────────────────────────────────────────────────
const chartDefaults = {{
  plugins: {{ legend: {{ display: false }}, tooltip: {{ bodyFont: {{ size: 11 }}, titleFont: {{ size: 11 }}, backgroundColor: '#111827', borderColor: 'rgba(0,0,0,0.1)', borderWidth: 0, padding: 10 }} }},
  scales: {{
    x: {{ ticks: {{ font: {{ size: 10 }}, color: CHART_FONT_COLOR }}, grid: {{ color: CHART_GRID_COLOR }}, border: {{ color: 'transparent' }} }},
    y: {{ ticks: {{ font: {{ size: 10 }}, color: CHART_FONT_COLOR }}, grid: {{ color: CHART_GRID_COLOR }}, border: {{ color: 'transparent' }} }},
  }},
  maintainAspectRatio: false,
  animation: {{ duration: 200 }},
}};

function hbarOptions(labels, extra) {{
  return {{
    ...chartDefaults,
    indexAxis: 'y',
    scales: {{
      x: {{ ...chartDefaults.scales.x, ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR }} }},
      y: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR, callback: v => labels[v]?.length > 28 ? labels[v].slice(0,26)+'…' : labels[v] }}, grid: {{display:false}}, border: {{color:'transparent'}} }},
    }},
    ...extra,
  }};
}}

function renderChartTipo(data) {{
  destroyChart('tipo');
  const grupos = agrupar(data, 'tramite_actual');
  const labels = grupos.map(g => g.label);
  const vals   = grupos.map(g => g.cant);
  const ctx = document.getElementById('chart-tipo').getContext('2d');
  charts['tipo'] = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data: vals, backgroundColor: COLORES.slice(0, labels.length), borderRadius: 4, borderSkipped: false }}] }},
    options: hbarOptions(labels, {{
      plugins: {{ ...chartDefaults.plugins, tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.raw.toLocaleString('es-AR')}} trámites` }} }} }},
    }}),
  }});
}}

function renderChartUsuario(data) {{
  destroyChart('usuario');
  const grupos = agrupar(data, 'usuario_cabecera').slice(0, 10);
  const labels = grupos.map(g => g.label);
  const vals   = grupos.map(g => g.cant);
  const ctx = document.getElementById('chart-usuario').getContext('2d');
  charts['usuario'] = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data: vals, backgroundColor: '#7c3aed', borderRadius: 4, borderSkipped: false }}] }},
    options: hbarOptions(labels, {{
      plugins: {{ ...chartDefaults.plugins, tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.raw.toLocaleString('es-AR')}} trámites` }} }} }},
    }}),
  }});
}}

function renderChartEvolucion(data) {{
  destroyChart('evolucion');
  const map = {{}};
  data.forEach(t => {{ map[t.fecha] = (map[t.fecha]||0) + 1; }});
  const fechas = Object.keys(map).sort();
  const vals   = fechas.map(f => map[f]);
  const ctx = document.getElementById('chart-evolucion').getContext('2d');
  charts['evolucion'] = new Chart(ctx, {{
    type: 'line',
    data: {{ labels: fechas, datasets: [{{
      data: vals, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.06)',
      fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#2563eb',
    }}] }},
    options: {{
      ...chartDefaults,
      scales: {{
        x: {{ ticks: {{ font: {{size:9}}, maxTicksLimit: 15, maxRotation: 45, color: CHART_FONT_COLOR }}, grid: {{color: CHART_GRID_COLOR}}, border: {{color:'transparent'}} }},
        y: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR }}, grid: {{color: CHART_GRID_COLOR}}, border: {{color:'transparent'}} }},
      }},
      plugins: {{ ...chartDefaults.plugins, tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.raw}} trámites` }} }} }},
    }},
  }});
}}

function renderChartFranjas(data) {{
  destroyChart('franjas');
  // Construir todas las franjas del día de 06:00 a 21:00
  const franjas = [];
  for (let h = 6; h <= 20; h++) {{
    franjas.push(`${{String(h).padStart(2,'0')}}:00`);
  }}
  // Contar trámites por franja de hora
  const map = {{}};
  franjas.forEach(f => map[f] = 0);
  data.forEach(t => {{
    if (!t.hora_inicio) return;
    const h = parseInt(t.hora_inicio.split(':')[0], 10);
    const key = `${{String(h).padStart(2,'0')}}:00`;
    if (map[key] !== undefined) map[key]++;
  }});
  const vals = franjas.map(f => map[f]);
  const ctx = document.getElementById('chart-franjas').getContext('2d');
  charts['franjas'] = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels: franjas, datasets: [{{
      data: vals,
      backgroundColor: vals.map(v => {{
        const max = Math.max(...vals);
        const alpha = max ? 0.3 + (v / max) * 0.7 : 0.3;
        return `rgba(37,99,235,${{alpha.toFixed(2)}})`;
      }}),
      borderRadius: 4,
      borderSkipped: false,
    }}] }},
    options: {{
      ...chartDefaults,
      scales: {{
        x: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR }}, grid: {{color: CHART_GRID_COLOR}}, border: {{color:'transparent'}} }},
        y: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR }}, grid: {{color: CHART_GRID_COLOR}}, border: {{color:'transparent'}} }},
      }},
      plugins: {{ ...chartDefaults.plugins, tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.raw.toLocaleString('es-AR')}} trámites` }} }} }},
    }},
  }});
}}

function renderChartRango(data) {{
  destroyChart('rango');
  const map = {{}};
  data.forEach(t => {{ map[t.rango_horario] = (map[t.rango_horario]||0) + 1; }});
  const labels = Object.keys(map);
  const vals   = labels.map(l => map[l]);
  const colors = labels.map(l => RANGO_COLORES[l] || '#94b4c8');
  const ctx = document.getElementById('chart-rango').getContext('2d');
  charts['rango'] = new Chart(ctx, {{
    type: 'doughnut',
    data: {{ labels, datasets: [{{ data: vals, backgroundColor: colors, borderWidth: 2, borderColor: '#ffffff' }}] }},
    options: {{
      maintainAspectRatio: false, animation: {{duration:200}},
      plugins: {{
        legend: {{ display: true, position: 'bottom', labels: {{ font: {{size:10}}, padding: 12, color: '#6b7280' }} }},
        tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.label}}: ${{ctx.raw.toLocaleString('es-AR')}}` }} }},
      }},
    }},
  }});
}}

function renderChart1ra(data) {{
  destroyChart('1ra');
  const grupos = agrupar(data, 'tramite_actual').filter(g => g.prom1ra !== null);
  const labels = grupos.map(g => g.label);
  const vals   = grupos.map(g => g.prom1ra);
  const ctx = document.getElementById('chart-1ra').getContext('2d');
  charts['1ra'] = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data: vals, backgroundColor: '#0891b2', borderRadius: 4, borderSkipped: false }}] }},
    options: hbarOptions(labels, {{
      plugins: {{ ...chartDefaults.plugins, tooltip: {{ callbacks: {{ label: ctx => ` ${{segAmmss(ctx.raw)}}` }} }} }},
      scales: {{
        x: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR, callback: v => segAmmss(v) }}, grid: {{color: CHART_GRID_COLOR}}, border: {{color:'transparent'}} }},
        y: {{ ticks: {{ font: {{size:10}}, color: CHART_FONT_COLOR, callback: v => labels[v]?.length > 28 ? labels[v].slice(0,26)+'…' : labels[v] }}, grid: {{display:false}}, border: {{color:'transparent'}} }},
      }},
    }}),
  }});
}}

// ── Tablas ────────────────────────────────────────────────────────────────────
function renderTablaTipo(data) {{
  const grupos = agrupar(data, 'tramite_actual');
  const total  = grupos.reduce((s,g) => s+g.cant, 0);
  let html = '<table><thead><tr><th>Trámite</th><th>Cant.</th><th>%</th><th>1ra aten. prom.</th><th>Dur. total prom.</th></tr></thead><tbody>';
  grupos.forEach(g => {{
    const pct = total ? ((g.cant/total)*100).toFixed(1) : 0;
    html += `<tr>
      <td>${{g.label}}</td>
      <td style="text-align:right;font-weight:700;">${{g.cant.toLocaleString('es-AR')}}</td>
      <td style="text-align:right;color:#94b4c8;">${{pct}}%</td>
      <td style="text-align:right;">${{segAmmss(g.prom1ra)}}</td>
      <td style="text-align:right;">${{segAhhmmss(g.promDur)}}</td>
    </tr>`;
  }});
  html += '</tbody></table>';
  document.getElementById('tabla-tipo').innerHTML = html;
}}

function renderTablaUsuario(data) {{
  const grupos = agrupar(data, 'usuario_cabecera');
  let html = '<table><thead><tr><th>Usuario</th><th>Cant.</th><th>1ra aten. prom.</th><th>Dur. prom.</th></tr></thead><tbody>';
  grupos.forEach(g => {{
    html += `<tr>
      <td>${{g.label}}</td>
      <td style="text-align:right;font-weight:700;">${{g.cant.toLocaleString('es-AR')}}</td>
      <td style="text-align:right;">${{segAmmss(g.prom1ra)}}</td>
      <td style="text-align:right;">${{segAhhmmss(g.promDur)}}</td>
    </tr>`;
  }});
  html += '</tbody></table>';
  document.getElementById('tabla-usuario').innerHTML = html;
}}

function renderTablaSinFinUsuario() {{
  // Siempre muestra el universo total de SIN_HORA_FIN, sin filtros
  const badge = document.getElementById('badge-sin-fin-detalle');
  badge.textContent = SIN_HORA_FIN.length;

  const mapa = {{}};
  SIN_HORA_FIN.forEach(t => {{
    const u = t.usuario_cabecera || '— Sin usuario (TOTEM)';
    if (!mapa[u]) mapa[u] = {{ cant: 0, tramites: {{}} }};
    mapa[u].cant++;
    const tip = t.tramite_actual || '(sin tipo)';
    mapa[u].tramites[tip] = (mapa[u].tramites[tip] || 0) + 1;
  }});

  const filas = Object.entries(mapa).sort((a,b) => b[1].cant - a[1].cant);
  let html = '<table><thead><tr><th>Usuario</th><th style="text-align:right">Cant.</th><th>Tipos de trámite</th></tr></thead><tbody>';
  filas.forEach(([u, v]) => {{
    const tipos = Object.entries(v.tramites).sort((a,b)=>b[1]-a[1])
      .map(([k,c]) => `${{k}} (${{c}})`).join(', ');
    const esTotem = !u.startsWith('—') ? '' : ' style="color:var(--text-2);font-style:italic;"';
    html += `<tr>
      <td${{esTotem}}>${{u}}</td>
      <td style="text-align:right;font-weight:700;">${{v.cant}}</td>
      <td style="color:var(--text-2);font-size:10px;">${{tipos}}</td>
    </tr>`;
  }});
  html += '</tbody></table>';
  document.getElementById('tabla-sin-fin-usuario').innerHTML = html;
}}

function renderTablaControles(data) {{
  // Solo muestra flags distintos de SIN_HORA_FIN (ya están en su propia sección)
  const conFlags = data.filter(t => t.flags_control &&
    t.flags_control.some(f => f !== 'SIN_HORA_FIN'));
  document.getElementById('badge-controles').textContent = conFlags.length;
  if (!conFlags.length) {{
    document.getElementById('tabla-controles').innerHTML = '<div class="no-data">Sin inconsistencias en el universo filtrado.</div>';
    return;
  }}
  let html = '<table><thead><tr><th>Nro. turno</th><th>Fecha</th><th>Trámite</th><th>Usuario</th><th>Flags</th></tr></thead><tbody>';
  conFlags.slice(0, 100).forEach(t => {{
    const flags = t.flags_control.map(f => `<span class="flag-tag flag-${{f}}">${{f.replace(/_/g,' ')}}</span>`).join('');
    html += `<tr>
      <td>${{t.nro_turno}}</td>
      <td>${{t.fecha}}</td>
      <td>${{t.tramite_actual}}</td>
      <td>${{t.usuario_cabecera || '—'}}</td>
      <td>${{flags}}</td>
    </tr>`;
  }});
  if (conFlags.length > 100) html += `<tr><td colspan="5" style="color:#94b4c8;text-align:center;">... y ${{conFlags.length - 100}} más</td></tr>`;
  html += '</tbody></table>';
  document.getElementById('tabla-controles').innerHTML = html;
}}

// ── Inicializar filtros ───────────────────────────────────────────────────────
function poblarFiltros() {{
  // Año: siempre desde la base (excluye SIN_HORA_FIN), nunca se repobla en cascada
  const anios = uniq(TRAMITES_BASE.map(t => t.anio)).sort();
  construirLista('f-anio', anios, () => {{ cascadaDesde('anio'); actualizar(); }});

  // Fechas
  const onFecha = () => {{ cascadaDesde('fecha'); actualizar(); }};
  document.getElementById('f-fecha-desde').addEventListener('change', onFecha);
  document.getElementById('f-fecha-hasta').addEventListener('change', onFecha);

  // Chips rango
  const rangos = uniq(TRAMITES_BASE.map(t => t.rango_horario));
  const contenedor = document.getElementById('f-rango');
  ['06:00 a 13:30','13:30 a 21:00','Fuera de rango','Sin rango'].filter(r => rangos.includes(r)).forEach(r => {{
    const chip = document.createElement('span');
    chip.className = 'chip'; chip.textContent = r; chip.dataset.val = r;
    chip.onclick = () => {{ chip.classList.toggle('active'); actualizar(); }};
    contenedor.appendChild(chip);
  }});

  // Poblar cascada inicial (mes, trámite, usuario)
  cascadaDesde('anio');

  // Header info
  const fechas = TRAMITES_BASE.map(t => t.fecha).sort();
  document.getElementById('header-subtitle').textContent =
    `${{TRAMITES_BASE.length.toLocaleString('es-AR')}} trámites · ${{fechas[0]}} al ${{fechas[fechas.length-1]}}`;
  document.getElementById('header-right').textContent =
    `Archivos: ${{uniq(TRAMITES_BASE.map(t => t.archivo_origen)).join(', ')}} · ${{SIN_HORA_FIN.length}} sin hora fin excluidos`;
}}

// ── Actualizar todo ───────────────────────────────────────────────────────────
function actualizar() {{
  const data = aplicarFiltros();
  renderKPIs(data);
  renderChartTipo(data);
  renderChartUsuario(data);
  renderChartEvolucion(data);
  renderChartFranjas(data);
  renderChartRango(data);
  renderChart1ra(data);
  renderTablaTipo(data);
  renderTablaUsuario(data);
  renderTablaSinFinUsuario();
  renderTablaControles(data);
}}

poblarFiltros();
actualizar();
</script>
</body>
</html>"""
    return html

def main():
    datos = cargar_datos()
    tramites = datos["tramites"]
    html = generar_html(tramites)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generado: {OUTPUT_FILE} ({len(tramites):,} trámites)")

if __name__ == "__main__":
    main()
