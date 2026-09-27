"""
ANÁLISIS PROFUNDO · todas las temporadas
========================================
Empareja cada partido anotado golpe a golpe del Match Charting Project con su
partido del archivo y construye su bloque de análisis profundo.

Dos orígenes, mismo formato de salida:
  · el repositorio del proyecto (datos/mcp/*.csv), completo pero con retraso
  · las páginas de su web (datos/mcp_paginas/*.html), al día; mandan sobre el repositorio

Salida: datos/profundo.json   { clave_del_partido: {"deep": {...}, "nv": {...}} }
"""
import json
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from leer_partido import leer, _modelo

RAIZ = Path(__file__).resolve().parent.parent
D, M = RAIZ / "datos", RAIZ / "datos" / "mcp"
GOLPE = set("fbrsvzopuylmhijktq")
ZONAS = ["deuce_wide", "deuce_middle", "deuce_t", "ad_wide", "ad_middle", "ad_t"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("-", " ")
    return " ".join(sorted(re.sub(r"[^a-z ]", "", s).split()))


def ntor(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s.replace("masters", "").replace("open", "").replace("_", ""))


def clave(fecha, w, l, r):
    return f"{fecha:%Y%m%d}|{w}|{l}|{r}"


def pct(x):
    return pd.to_numeric(pd.Series(x).astype(str).str.rstrip("%"), errors="coerce") / 100


# ----------------------------------------------------------------------------
# emparejar partidos anotados con el archivo
# ----------------------------------------------------------------------------
def letras(s):
    """'Felix Auger-Aliassime' y 'Felix_Auger_Aliassime' -> 'felixaugeraliassime'."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def tor_parecido(a, b):
    return bool(a) and bool(b) and (a[:5] == b[:5] or a[:5] in b or b[:5] in a)


class Archivo:
    """Índice del archivo por pareja de jugadores, para emparejar partidos anotados."""
    def __init__(self, arch):
        self.por_par = {}
        for i, f, t, r, w, l in zip(arch.index, arch.fecha, arch.tourney_name, arch["round"], arch.winner_name, arch.loser_name):
            self.por_par.setdefault(frozenset((letras(w), letras(l))), []).append((i, f, ntor(t), r))

    def candidatos(self, p1, p2, fecha, ronda, torneo):
        """Partidos del archivo que pueden ser este, con su puntuación.
        Hace falta que coincida la ronda o el torneo; más allá de 30 días, el torneo sí o sí
        (el proyecto golpe a golpe tiene alguna fecha desviada)."""
        kt, out = ntor(torneo), []
        for i, f, t, r in self.por_par.get(frozenset((letras(p1), letras(p2))), []):
            dias = abs((f - fecha).days)
            if dias > 60:
                continue
            ts, rs = tor_parecido(kt, t), bool(ronda) and ronda == r
            if not (ts or rs) or (dias > 30 and not ts):
                continue
            out.append((3 * ts + 2 * rs - dias / 30, i))
        return out


def asignar(ofertas):
    """ofertas: [(puntuación, id_anotado, índice_archivo)]. Reparto uno a uno, de la mejor
    pareja a la peor, para que un cruce repetido no se quede con el partido equivocado."""
    usados_a, usados_m, out = set(), set(), {}
    for s, mid, i in sorted(ofertas, key=lambda x: -x[0]):
        if mid in usados_m or i in usados_a:
            continue
        usados_m.add(mid); usados_a.add(i); out[mid] = i
    return out


def emparejar(arch, mcp):
    A = Archivo(arch)
    ofertas = [(s, mid, i) for mid, p1, p2, f, ro, t in zip(mcp.match_id, mcp.p1, mcp.p2, mcp.f, mcp.ronda, mcp.tor)
               for s, i in A.candidatos(p1, p2, f, ro, t)]
    return asignar(ofertas)


# ----------------------------------------------------------------------------
# golpes codificados del punto a punto
# ----------------------------------------------------------------------------
def golpes(c):
    if not isinstance(c, str) or not c:
        return None
    m = re.match(r"[^0-9]*([4-6])", c)
    if not m:
        return None
    g, cur = [], None
    for ch in c[m.end():]:
        if ch in GOLPE:
            if cur is not None:
                g.append(cur)
            cur = ch
        elif cur is not None:
            cur += ch
    if cur is not None:
        g.append(cur)
    return g, (c[-1] if c[-1] in "@#*" else "")


# ----------------------------------------------------------------------------
# construir el bloque de un partido
# ----------------------------------------------------------------------------
def bloque(mid, row, q, T, bo):
    """row: fila del archivo; q: puntos del partido; T: tablas agrupadas por (partido, jugador)."""
    p1, p2 = T["m"].loc[mid, "Player 1"], T["m"].loc[mid, "Player 2"]
    inv = norm(p1) != norm(row.winner_name)            # ¿el jugador 1 del anotador es el perdedor?
    lado = {p1: "l" if inv else "w", p2: "w" if inv else "l"}
    J, NV = {"w": {}, "l": {}}, {"w": {}, "l": {}}
    for p, L in lado.items():
        d, v = J[L], NV[L]
        o = T["ov"].get((mid, p))
        if o is None:
            return None
        d.update(win=int(o.winners), wfh=int(o.winners_fh), wbh=int(o.winners_bh), ue=int(o.unforced),
                 ufh=int(o.unforced_fh), ubh=int(o.unforced_bh), pts=int(o.serve_pts + o.return_pts))
        n = T["nt"].get((mid, p))
        d.update(net=int(n.net_pts), netw=int(n.pts_won), netg=int(n.net_winner), pas=int(n.passed_at_net)) if n is not None \
            else d.update(net=0, netw=0, netg=0, pas=0)
        s = T["sd"].get((mid, p))
        if s is not None:
            z = [float(getattr(s, c)) for c in ZONAS]
            if sum(z):
                d["sd"], d["sdn"] = [round(x / sum(z), 3) for x in z], int(sum(z))
        d["rally"] = T["ra"].get((mid, p), {"1-3": [0, 0], "4-6": [0, 0], "7-9": [0, 0], "10": [0, 0]})
        x = T["dir"].get((mid, p))
        if x is not None:
            t = float(sum(getattr(x, c) for c in ("crosscourt", "down_middle", "down_the_line", "inside_out", "inside_in")))
            if t:
                v["cruz"], v["par"] = [int(x.crosscourt), int(t)], [int(x.down_the_line), int(t)]
        v["snv"] = [int(T["snv"].get((mid, p), 0)), int(o.serve_pts)]
        x = T["rd"].get((mid, p))
        if x is not None and x[1] > 0:
            v["prof"] = [int(x[0]), int(x[1])]                  # 'deep' ya incluye 'very_deep'
        x = T["ro"].get((mid, p))
        if x is not None and x[1] > 0:
            v["enj"] = [int(x[0]), int(x[1])]
        x = T["si"].get((mid, p))
        if x is not None:
            v["evap"] = [round(float(x[0]), 3), round(float(x[1]), 3)]
        x = T["kp"].get((mid, p))
        if x is not None and x[1] > 0:
            v["temple"] = [int(x[0]), int(x[1]), int(o.first_won + o.second_won), int(o.serve_pts)]
    if q is None or not len(q):
        return None
    # secuencia de juegos, primer golpe tras el saque, rachas y peso
    seq, prev = [], None
    s1 = {"w": [0, 0, 0], "l": [0, 0, 0]}
    gan = []
    for x in q.itertuples(index=False):
        k = (x.Set1, x.Set2, x.Gm1, x.Gm2)
        if k != prev:
            seq.append({"s": [int(x.Set1), int(x.Set2)], "g": [int(x.Gm1), int(x.Gm2)], "sv": int(x.Svr), "p": []})
            prev = k
        seq[-1]["p"].append(int(x.PtWinner))
        srv = ("l" if inv else "w") if x.Svr == 1 else ("w" if inv else "l")
        gan.append(("l" if inv else "w") if x.PtWinner == 1 else ("w" if inv else "l"))
        cod = x.c2 if isinstance(x.c2, str) and x.c2 else x.c1         # '2nd' si lo hubo, si no '1st'
        g = golpes(cod)
        if g and len(g[0]) >= 2:
            gs, fin = g
            s1[srv][2] += 1
            if (len(gs) == 2 and fin == "*") or (len(gs) == 3 and fin == "#"):
                s1[srv][0] += 1
            elif len(gs) == 2 and fin in "@#":
                s1[srv][1] += 1
    for L in "wl":
        NV[L]["s1"] = s1[L]
        best = cur = fi = 0
        for i, g in enumerate(gan):
            cur = cur + 1 if g == L else 0
            if cur > best:
                best, fi = cur, i
        r = q.iloc[fi]
        NV[L]["racha"] = [best, int(r.Set1 + r.Set2) + 1, 0, 0]
    a1 = q[q.Svr == 1]; a2 = q[q.Svr == 2]
    pA = min(max((a1.PtWinner == 1).mean() if len(a1) else .63, .4), .9)
    pB = min(max((a2.PtWinner == 2).mean() if len(a2) else .63, .4), .9)
    peso = _modelo(pA, pB, bo)
    tot = w1 = 0.0; top = None
    for j in seq:
        a = b = 0
        for w in j["p"]:
            try:
                wt = peso(j["s"][0], j["s"][1], j["g"][0], j["g"][1], a, b, j["sv"] == 1)
            except RecursionError:
                wt = 0.0
            tot += wt; w1 += wt if w == 1 else 0
            if top is None or wt > top[0]:
                top = (wt, j, a, b, w)
            a, b = (a + 1, b) if w == 1 else (a, b + 1)
    if tot <= 0:
        return None
    pw = w1 / tot
    NV["w" if not inv else "l"]["peso"] = round(pw, 3)
    NV["l" if not inv else "w"]["peso"] = round(1 - pw, 3)
    wt, j, a, b, w = top
    NV["top"] = {"w": round(wt, 3), "set": sum(j["s"]) + 1, "g": j["g"][::-1] if inv else j["g"],
                 "p": [b, a] if inv else [a, b], "sv": "w" if (j["sv"] == 1) != inv else "l",
                 "gana": "w" if (w == 1) != inv else "l"}
    return {"deep": {"mid": mid, "j1": "l" if inv else "w", "J": J, "seq": seq, "np": len(q)}, "nv": NV}


def tablas(mids):
    """Todas las tablas del repositorio, agrupadas por (partido, jugador) para acceso inmediato."""
    ids = set(mids)
    def carga(n):
        t = pd.read_csv(M / f"charting-m-stats-{n}.csv", low_memory=False)
        return t[t.match_id.isin(ids)]
    T = {"m": pd.read_csv(M / "charting-m-matches.csv", low_memory=False).set_index("match_id")}
    ov = carga("Overview"); ov = ov[ov.set == "Total"]
    T["ov"] = {(r.match_id, r.player): r for r in ov.itertuples(index=False)}
    nt = carga("NetPoints"); nt = nt[nt.row == "NetPoints"].groupby(["match_id", "player"])[["net_pts", "pts_won", "net_winner", "passed_at_net"]].sum()
    T["nt"] = {k: r for k, r in nt.iterrows()}
    sd = carga("ServeDirection"); sd = sd[sd.row.astype(str) == "1"]
    T["sd"] = {(r.match_id, r.player): r for r in sd.itertuples(index=False)}
    ra = carga("Rally"); ra = ra[ra.row.astype(str).isin(["1-3", "4-6", "7-9", "10"])]
    R = {}
    for r in ra.itertuples(index=False):
        for p, w in ((r.server, r.pl1_won), (r.returner, r.pl2_won)):
            d = R.setdefault((r.match_id, p), {"1-3": [0, 0], "4-6": [0, 0], "7-9": [0, 0], "10": [0, 0]})
            d[str(r.row)][0] += int(w); d[str(r.row)][1] += int(r.pts)
    T["ra"] = R
    di = carga("ShotDirection"); di = di[di.row == "Total"]
    T["dir"] = {(r.match_id, r.player): r for r in di.itertuples(index=False)}
    sn = carga("SnV"); sn = sn[sn.row == "SnV"]
    T["snv"] = {(r.match_id, r.player): r.snv_pts for r in sn.itertuples(index=False)}
    rd = carga("ReturnDepth"); rd = rd[rd.row.astype(str).isin(["4", "5", "6"])]
    rd = rd.groupby(["match_id", "player"]).agg(deep=("deep", "sum"), sh=("shallow", "sum"))
    T["rd"] = {k: (r.deep, r.deep + r.sh) for k, r in rd.iterrows()}
    ro = carga("ReturnOutcomes"); ro = ro[ro.row.astype(str).isin(["4", "5", "6"])]
    ro = ro.groupby(["match_id", "player"])[["in_play", "returnable"]].sum()
    T["ro"] = {k: (r.in_play, r.returnable) for k, r in ro.iterrows()}
    si = carga("ServeInfluence"); si = si[si.row.astype(str) == "1"]
    a, b = pct(si["won_1+"]).values, pct(si["won_5+"]).values
    T["si"] = {(m, p): (x, y) for m, p, x, y in zip(si.match_id, si.player, a, b) if np.isfinite(x) and np.isfinite(y)}
    kp = carga("KeyPointsServe"); kp = kp[kp.row == "BP"].groupby(["match_id", "player"])[["pts_won", "pts"]].sum()
    T["kp"] = {k: (r.pts_won, r.pts) for k, r in kp.iterrows()}
    return T


def reconstruir(deep):
    """Marcador que sale de la secuencia punto a punto, orientado ganador-perdedor."""
    seq, inv, sets = deep["seq"], deep["j1"] == "l", []
    for i, j in enumerate(seq):
        sig = seq[i + 1] if i + 1 < len(seq) else None
        if sig is None or tuple(sig["s"]) != tuple(j["s"]):
            g, ult = list(j["g"]), j["p"][-1]
            if g == [6, 6]:
                g = [7, 6] if ult == 1 else [6, 7]
            else:
                g[ult - 1] += 1
            sets.append(g[::-1] if inv else g)
    return sets


def cuadra(deep, marcador):
    """CONTROL DE CALIDAD: la secuencia punto a punto tiene que reproducir el resultado
    oficial set por set. Si no, es un partido anotado a medias o mal emparejado."""
    from limpieza import sets_del_marcador
    return reconstruir(deep) == [list(x) for x in sets_del_marcador(marcador)]


def construir(recalcular_repo=None):
    """recalcular_repo: None = solo si hay ficheros del repositorio; True/False para forzar."""
    arch = pd.read_parquet(D / "calculado.parquet", columns=["fecha", "tourney_name", "round", "winner_name", "loser_name", "score", "best_of"])
    cache = D / "profundo_repo.json"
    hay_repo = (M / "charting-m-matches.csv").exists()
    if recalcular_repo is None:
        recalcular_repo = hay_repo and not cache.exists()
    n_anot = emp = fallos = 0
    if recalcular_repo and hay_repo:
        m = pd.read_csv(M / "charting-m-matches.csv", low_memory=False)
        m = m[m.match_id.str.contains("-M-", na=False)].copy()
        m["f"] = pd.to_datetime(m.match_id.str[:8], format="%Y%m%d", errors="coerce")
        m = m[m.f.notna() & (m.f.dt.year >= arch.fecha.dt.year.min())]
        partes = m.match_id.str.split("-")
        m["ronda"] = partes.str[-3]                               # el torneo puede llevar guiones:
        m["tor"] = partes.apply(lambda x: "-".join(x[2:-3]))     # se cuenta desde el final
        m["p1"], m["p2"] = m["Player 1"], m["Player 2"]
        pares = emparejar(arch, m)
        mids = list(pares)
        T = tablas(mids)
        pts = pd.concat([pd.read_csv(f, low_memory=False, usecols=["match_id", "Pt", "Set1", "Set2", "Gm1", "Gm2", "Svr", "1st", "2nd", "PtWinner"])
                         for f in sorted(M.glob("charting-m-points-*.csv"))])
        pts = pts[pts.match_id.isin(pares)].rename(columns={"1st": "c1", "2nd": "c2"})
        num = ["Pt", "Set1", "Set2", "Gm1", "Gm2", "Svr", "PtWinner"]
        for c in num:
            pts[c] = pd.to_numeric(pts[c], errors="coerce")
        pts = pts.dropna(subset=num)                       # puntos con el marcador incompleto: fuera
        pts = pts[pts.PtWinner.isin([1, 2]) & pts.Svr.isin([1, 2])]
        for c in num:
            pts[c] = pts[c].astype(int)
        por_partido = {k: g.sort_values("Pt") for k, g in pts.groupby("match_id")}
        out, fallos = {}, 0
        for mid, i in pares.items():
            r = arch.loc[i]
            q = por_partido.get(mid)
            try:
                b = bloque(mid, r, q, T, 5 if r.best_of == 5 else 3)
            except Exception:
                b = None
            if b and cuadra(b["deep"], r.score):
                out[clave(r.fecha, r.winner_name, r.loser_name, r["round"])] = b
            else:
                fallos += 1
        json.dump(out, open(cache, "w"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        n_anot, emp = len(m), len(pares)
    else:
        out = json.load(open(cache)) if cache.exists() else {}
    # páginas de la web: mandan sobre el repositorio (están al día)
    pag = 0
    carpeta = D / "mcp_paginas"
    if carpeta.exists():
        A = Archivo(arch)
        paginas, ofertas = {}, []
        for fh in sorted(carpeta.glob("*.json")) + sorted(carpeta.glob("*.html")):
            try:
                if fh.suffix == ".json":
                    x = json.load(open(fh)); meta, deep, nv = x["meta"], x["deep"], x["nv"]
                else:
                    meta, deep, nv = leer(fh.read_text(encoding="utf-8", errors="ignore"))
                fecha = pd.Timestamp(fh.name[:8])            # la fecha va en el nombre del archivo
            except Exception:
                continue
            paginas[fh.name] = (meta, deep, nv)
            ofertas += [(s, fh.name, i) for s, i in A.candidatos(meta["ganador"], meta["perdedor"], fecha, meta["ronda"], meta["torneo"])]
        asig = asignar(ofertas)
        no_cuadra = []
        for nombre, i in asig.items():
            meta, deep, nv = paginas[nombre]
            r = arch.loc[i]
            if cuadra(deep, r.score):                        # contra el resultado OFICIAL del archivo
                out[clave(r.fecha, r.winner_name, r.loser_name, r["round"])] = {"deep": deep, "nv": nv}
                pag += 1
            else:
                no_cuadra.append(f"{nombre}: su punto a punto no reproduce el resultado oficial {r.score}")
        sin_pareja = [n for n in paginas if n not in asig]
        (carpeta / "_emparejamiento.txt").write_text(
            f"páginas convertidas: {len(paginas)} · emparejadas con el archivo: {len(asig)} · "
            f"con análisis profundo: {pag}\n\nsin pareja en el archivo ({len(sin_pareja)}):\n  " + "\n  ".join(sin_pareja[:40]) +
            f"\n\nno pasan el control de calidad ({len(no_cuadra)}):\n  " + "\n  ".join(no_cuadra[:40]) + "\n", encoding="utf-8")
    json.dump(out, open(D / "profundo.json", "w"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return n_anot, emp, len(out), fallos, pag


if __name__ == "__main__":
    n, emp, ok, fal, pag = construir(recalcular_repo=("--repo" in sys.argv) or None)
    print(f"partidos masculinos anotados: {n:,} · emparejados con el archivo: {emp:,} · con análisis profundo: {ok:,} · "
          f"descartados: {fal} · desde páginas web: {pag}")
