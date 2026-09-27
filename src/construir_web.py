"""
CONSTRUCCIÓN DE LOS DATOS DE LA WEB
===================================
Entrada:  datos/calculado.parquet, datos/constantes.json, datos/profundo.json
Salida (web/datos/):
    temporadas.json   qué años hay y cuál es el actual
    ref.json          referencias del circuito (todas las temporadas) y evolución histórica
    t/AAAA.json       una caja por temporada: partidos, gráficos, ranking, destacado
    p/AAAA.json       análisis profundo de los partidos anotados de esa temporada
    indice.json       lo mínimo de cada partido, para buscar en todas las temporadas
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
D, W = RAIZ / "datos", RAIZ / "web" / "datos"
lim = lambda s: s.replace([np.inf, -np.inf], np.nan)


def f(x, k=2):
    try:
        x = float(x)
        return None if (np.isnan(x) or np.isinf(x)) else round(x, k)
    except (TypeError, ValueError):
        return None


def txt(x):
    """Texto limpio: un hueco nunca debe llegar a la web como NaN."""
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else str(x)


def guardar(obj, ruta):
    # allow_nan=False: si se cuela un NaN, la construcción FALLA en vez de publicar
    # un archivo que el navegador rechazaría entero
    json.dump(obj, open(ruta, 'w'), ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def clave(fecha, w, l, r):
    """Identificador estable de un partido, igual en todas las reconstrucciones."""
    return f"{fecha:%Y%m%d}|{txt(w)}|{txt(l)}|{txt(r)}"


CAMPOS = {'mi': ('minutes', 0), 'im': ('importancia', 0), 'so': ('magnitud_sorpresa', 2), 'rkw': ('winner_rank', 0),
 'rkl': ('loser_rank', 0), 'ns': ('n_sets', 0), 'mj': ('margen_juegos', 0), 'jg': ('juegos_g', 0), 'jp': ('juegos_p', 0),
 'sa': ('sets_ajustados', 0), 'sp': ('sets_paliza', 0), 'tb': ('tiebreaks', 0), 'tbg': ('tiebreaks_ganados', 0),
 'tbm': ('margen_tb_medio', 1), 'rd': ('roscos_dados', 0), 'rr': ('roscos_recibidos', 0), 'vu': ('vuelco', 0),
 'sd': ('set_decisivo', 0), 'g1': ('gano_1er_set', 0), 'te': ('tension', 1), 'vo': ('volatilidad', 2),
 'tr': ('trayectoria', 2), 'di': ('disputa', 1), 'ppj': ('ppj', 2), 'pg': ('pts_g', 0), 'pl': ('pts_p', 0),
 'pt': ('pts_total', 0), 'mpp': ('min_por_punto', 2),
 'p1w': ('pct_1er_dentro_w', 3), 'p1l': ('pct_1er_dentro_l', 3), 'g1w': ('pct_gana_1er_w', 3), 'g1l': ('pct_gana_1er_l', 3),
 'g2w': ('pct_gana_2o_w', 3), 'g2l': ('pct_gana_2o_l', 3), 'psw': ('pct_pts_saque_w', 3), 'psl': ('pct_pts_saque_l', 3),
 'prw': ('pct_pts_resto_w', 3), 'prl': ('pct_pts_resto_l', 3), 'aw': ('w_ace', 0), 'al': ('l_ace', 0),
 'dfw': ('w_df', 0), 'dfl': ('l_df', 0), 'arw': ('ace_rate_w', 3), 'arl': ('ace_rate_l', 3),
 'adw': ('ace_df_ratio_w', 1), 'adl': ('ace_df_ratio_l', 1), 'pjw': ('pts_por_juego_saque_w', 1), 'pjl': ('pts_por_juego_saque_l', 1),
 'bsw': ('pct_bp_salvadas_w', 3), 'bsl': ('pct_bp_salvadas_l', 3), 'bcw': ('pct_bp_convertidas_w', 3), 'bcl': ('pct_bp_convertidas_l', 3),
 'bgw': ('bp_generadas_w', 0), 'bgl': ('bp_generadas_l', 0), 'prew': ('presion_recibida_w', 2), 'prel': ('presion_recibida_l', 2),
 'de': ('desperdicio_g', 0), 'td': ('tasa_desperdicio_g', 3), 'mr': ('margen_robo', 3), 'pp': ('pct_pts_g', 3),
 'do': ('dominacion_g', 2), 'dop': ('dominacion_p', 2), 'ef': ('eficiencia_g', 3), 'es': ('espectaculo', 1), 'ca': ('calidad', 0),
 'asi': ('asim2', 2), 'pcl': ('pct_clave_g', 3), 'pal': ('paliza', 2), 'isq': ('indice_saques', 3), 'dsg': ('desgaste', 0),
 'escp': ('escape2', 1), 'rc': ('rc', 0), 'rivn': ('rivn', 0), 'rivt': ('rivt', 1)}

REF = {'te': 'tension', 'di': 'disputa', 'vo': 'volatilidad', 'tr': 'trayectoria', 'do': 'dominacion_g', 'es': 'espectaculo',
 'ca': 'calidad', 'pal': 'paliza', 'asi': 'asim2', 'ef': 'eficiencia_g', 'mr': 'margen_robo', 'so': 'magnitud_sorpresa',
 'dsg': 'desgaste', 'escp': 'escape2', 'pcl': 'pct_clave_g', 'isq': 'indice_saques', 'de': 'desperdicio_g',
 'td': 'tasa_desperdicio_g', 'ppj': 'ppj', 'mpp': 'min_por_punto', 'pp': 'pct_pts_g', 'pt': 'pts_total',
 'mj': 'margen_juegos', 'tbm': 'margen_tb_medio', 'rc': 'rc', 'rivt': 'rivt', 'rivn': 'rivn'}


def fila(r, k):
    o = {'k': k, 'd': r.fecha.strftime('%Y-%m-%d'), 't': txt(r.tourney_name), 's': txt(r.surface), 'r': txt(r['round']),
         'w': txt(r.winner_name), 'l': txt(r.loser_name), 'sc': txt(r.score), 'tp': txt(r.tipo),
         'in': 1 if str(r.get('indoor', '')).upper().startswith('I') else 0,
         'bo': f(r.best_of, 0), 'rb': int(r.robo) if pd.notna(r.robo) else 0,
         'rec': 'tensión' if r.rec_t else ('espectáculo' if r.rec_e else None), 'st': r.st}
    for c, (col, dec) in CAMPOS.items():
        o[c] = f(r.get(col), dec)
    return o


def hist(s, n=20):
    s = lim(s).dropna()
    if not len(s):
        return {'v': [], 'e': []}
    h, e = np.histogram(s, bins=n)
    return {'v': h.tolist(), 'e': [round(x, 2) for x in e.tolist()]}


def estilos(t):
    """Mapa de estilos de una temporada, cada jugador frente a la media de sus superficies."""
    x = pd.concat([t[['surface', 'winner_name', 'pct_pts_saque_w', 'pct_pts_resto_w']].set_axis(['s', 'j', 'sv', 're'], axis=1),
                   t[['surface', 'loser_name', 'pct_pts_saque_l', 'pct_pts_resto_l']].set_axis(['s', 'j', 'sv', 're'], axis=1)])
    x = x.replace([np.inf, -np.inf], np.nan).dropna()
    m = x.groupby('s')[['sv', 're']].transform('mean')
    x['dsv'], x['dre'] = x.sv - m.sv, x.re - m.re
    g = x.groupby('j').agg(p=('sv', 'size'), sv=('dsv', 'mean'), re=('dre', 'mean'))
    minimo = 15 if len(t) > 1500 else 8
    g = g[g.p >= minimo]
    return [{'n': str(j).split()[-1], 'full': j, 'p': int(r.p), 'sv': round(100 * r.sv, 2), 're': round(100 * r.re, 2)}
            for j, r in g.iterrows()]


def carrera(t):
    """Puntos ATP semana a semana de los catorce primeros al final de la temporada."""
    r = pd.concat([t[['fecha', 'winner_name', 'winner_rank', 'winner_rank_points']].set_axis(['f', 'j', 'rk', 'pt'], axis=1),
                   t[['fecha', 'loser_name', 'loser_rank', 'loser_rank_points']].set_axis(['f', 'j', 'rk', 'pt'], axis=1)]).dropna()
    if len(r) < 200:
        return None
    r['sem'] = r.f.dt.to_period('W-SUN').dt.start_time
    sems = sorted(r['sem'].unique())
    top = r.sort_values('f').groupby('j').tail(1).sort_values('rk').head(14).j.tolist()
    P, R = {}, {}
    for j in top:
        s = r[r.j == j].sort_values('f').groupby('sem').last().reindex(pd.DatetimeIndex(sems)).ffill().bfill()
        P[j], R[j] = [int(x) for x in s.pt], [int(x) for x in s.rk]
    return {'semanas': [pd.Timestamp(x).strftime('%Y-%m-%d') for x in sems], 'puntos': P, 'rank': R}


def construir():
    d = pd.read_parquet(D / 'calculado.parquet')
    K = json.load(open(D / 'constantes.json'))
    prof = json.load(open(D / 'profundo.json')) if (D / 'profundo.json').exists() else {}
    sys.path.insert(0, str(Path(__file__).parent))
    from limpieza import sets_del_marcador
    d['st'] = d.score.apply(lambda s: [list(x) for x in sets_del_marcador(s)])
    d['k'] = [clave(a, b, c, e) for a, b, c, e in zip(d.fecha, d.winner_name, d.loser_name, d['round'])]
    for sub in ('t', 'p'):
        (W / sub).mkdir(parents=True, exist_ok=True)

    # ---- referencias del circuito: siempre sobre TODAS las temporadas
    ref = {}
    for k, col in REF.items():
        s = lim(d[col]).dropna()
        if len(s) > 200:
            ref[k] = {'q': [f(s.quantile(q / 100)) for q in range(0, 101, 5)],
                      'min': f(s.quantile(.01)), 'max': f(s.quantile(.99)), 'med': f(s.median())}
    ev = d.groupby('anio').agg(ace=('ace_rate_w', 'mean'), ten=('tension', 'mean'), n=('tension', 'size'))
    ev = ev[(ev.n > 1500)]
    guardar({'ref': ref, 'K': K, 'evol': {'y': ev.index.tolist(), 'ace': [f(100 * x) for x in ev.ace],
               'ten': [f(x, 1) for x in ev.ten]}}, W / 'ref.json')

    # ---- una caja por temporada
    anios, indice = {}, []
    jug, tor = {}, {}
    ron = ['F', 'SF', 'QF', 'R16', 'R32', 'R64', 'R128', 'RR', 'BR', 'ER']
    for anio, t in d.groupby('anio'):
        t = t.sort_values('fecha')
        P = [fila(r, r.k) for _, r in t.iterrows()]
        for o in P:
            o['dp'] = 1 if o['k'] in prof else 0
        v = t[t.tipo != 'SIN DATOS']
        piv = pd.crosstab(v.surface, v.tipo) if len(v) else pd.DataFrame()
        ult = t.fecha.max()
        rec = t[t.fecha >= ult - pd.Timedelta(days=21)]
        dest = rec.loc[rec.espectaculo.idxmax()] if rec.espectaculo.notna().any() else None
        caja = {
            'anio': int(anio), 'partidos': P,
            'kpi': {'n': len(P), 'robos': int(t.robo.sum()), 'horas': int(t.minutes.sum() / 60),
                    'ultima': ult.strftime('%Y-%m-%d'), 'medidas': 55, 'torneos': int(t.tourney_name.nunique()),
                    'jugadores': int(pd.concat([t.winner_name, t.loser_name]).nunique())},
            'tipos': {k: int(n) for k, n in t.tipo.value_counts().items()},
            'G': {'tipo_sup': {'sup': piv.index.tolist(), 'cols': piv.columns.tolist(), 'v': piv.values.tolist(),
                               'pct': [[round(float(100 * x / row.sum()), 1) for x in row] for row in piv.values.astype(float)]}
                  if len(piv) else None,
                  'h_tension': hist(t.tension), 'h_disputa': hist(t.disputa), 'estilos': estilos(t),
                  'nube': []},
            'rk': carrera(t),
            'semana': fila(dest, dest.k) if dest is not None else None,
        }
        guardar(caja, W / 't' / f'{anio}.json')
        pa = {o['k']: prof[o['k']] for o in P if o['k'] in prof}
        if pa:
            guardar(pa, W / 'p' / f'{anio}.json')
        anios[int(anio)] = {'n': len(P), 'dp': len(pa)}
        # índice de búsqueda: nombres y torneos como números para que ocupe poco
        for i, o in enumerate(P):
            wi = jug.setdefault(o['w'], len(jug)); li = jug.setdefault(o['l'], len(jug))
            ti = tor.setdefault(o['t'], len(tor))
            indice.append([int(anio), i, wi, li, ti, ron.index(o['r']) if o['r'] in ron else o['r'], o['sc'], o['d'][5:], o['dp']])
    guardar({'j': list(jug), 't': list(tor), 'r': ron, 'p': indice}, W / 'indice.json')
    guardar({'anios': anios, 'actual': max(anios)}, W / 'temporadas.json')
    # la página: plantilla + código, sin datos dentro (los pide a web/datos/)
    P = RAIZ / 'plantilla'
    (RAIZ / 'web' / 'index.html').write_text(
        (P / 'shell.html').read_text(encoding='utf-8') + '<script>\n' + (P / 'app.js').read_text(encoding='utf-8') + '</script></body></html>',
        encoding='utf-8')
    return anios


if __name__ == '__main__':
    a = construir()
    print(f"temporadas: {len(a)} · partidos: {sum(x['n'] for x in a.values()):,} · con análisis profundo: {sum(x['dp'] for x in a.values())}")
