"""
LECTOR DE PÁGINAS DE PARTIDO DEL MATCH CHARTING PROJECT
========================================================
Convierte la página de un partido de tennisabstract.com/charting/ en el mismo
formato de análisis profundo que usa Deuce (bloques DEEP y NV).

Solo lee páginas de /charting/, que el robots.txt de la web permite.
Nunca pide nada a /jsfrags/, /jsmatches/ ni /jsplayers/, que prohíbe.

Convenciones de la página, comprobadas con la final del US Open 2026:
  · Sets, juegos y puntos del registro se cuentan desde QUIEN SACA.
  · La longitud del peloteo que anota la web no cuenta el golpe que acaba
    en error (no llegó a entrar). Para saber quién dio el último golpe hay
    que contarlos todos.
"""
import re
import html as H

from functools import lru_cache

VERSION = "3"   # si cambia, se vuelven a intentar las páginas que no se entendieron


class PaginaIncompleta(ValueError):
    """La página no trae algún dato imprescindible: no es un fallo del lector."""


# ----------------------------------------------------------------------------
# lectura de la página
# ----------------------------------------------------------------------------
def _var(h, nombre):
    """Texto de una variable JavaScript de la página, respetando comillas escapadas."""
    m = re.search(r"var\s+" + nombre + r"\s*=\s*'", h)
    if not m:
        return ""
    i = j = m.end()
    while True:
        j = h.index("'", j)
        if h[j - 1] != "\\":
            return h[i:j]
        j += 1


def _filas(tabla):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tabla, re.S):
        celdas = [H.unescape(re.sub("<[^>]+>", "", c)).replace("\xa0", " ").replace("\u2011", "-").strip()
                  for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if any(celdas):
            out.append(celdas)
    return out


def _tabla(h, nombre, obligatoria=True):
    """Filas de una tabla de la página. Si falta una imprescindible se dice cuál, en vez de
    dejar que el lector tropiece más adelante con un IndexError sin explicación."""
    t = _filas(_var(h, nombre))
    if obligatoria and not t:
        raise PaginaIncompleta(f"la página no trae la tabla '{nombre}'")
    return t


def _n(celda):
    """'43  (68%)' -> 43 ; '71.3%' -> 0.713 ; '' -> None"""
    if celda is None or celda == "":
        return None
    celda = celda.strip()
    if celda.endswith("%") and "(" not in celda:
        return round(float(celda[:-1]) / 100, 4)
    m = re.match(r"-?\d+(?:\.\d+)?", celda)
    return float(m.group(0)) if m else None


def _fila(tabla, etiqueta, seccion=0):
    """Fila cuya primera celda es `etiqueta`. `seccion` elige entre repeticiones."""
    vistas = [f for f in tabla if f and f[0] == etiqueta]
    return vistas[seccion] if len(vistas) > seccion else None


def _col(tabla, cabecera_prefijo, seccion=0):
    """Índice de la columna cuya cabecera empieza por `cabecera_prefijo`."""
    if not tabla:
        return None
    cabs = [f for f in tabla if f and f[0].isupper() and len(f) > 3]
    cab = cabs[seccion] if len(cabs) > seccion else tabla[0]
    for i, c in enumerate(cab):
        if c.startswith(cabecera_prefijo):
            return i
    return None


# ----------------------------------------------------------------------------
# modelo de probabilidad para el peso de cada punto
# ----------------------------------------------------------------------------
def _modelo(pA, pB, bo):
    @lru_cache(None)
    def juego(a, b, p):
        if a >= 4 and a - b >= 2: return 1.0
        if b >= 4 and b - a >= 2: return 0.0
        if a >= 3 and b >= 3 and a == b: return p * p / (p * p + (1 - p) * (1 - p))
        return p * juego(a + 1, b, p) + (1 - p) * juego(a, b + 1, p)
    ptb = (pA + (1 - pB)) / 2
    @lru_cache(None)
    def tb(a, b):
        if a >= 7 and a - b >= 2: return 1.0
        if b >= 7 and b - a >= 2: return 0.0
        if a >= 6 and b >= 6 and a == b: return ptb * ptb / (ptb * ptb + (1 - ptb) ** 2)
        return ptb * tb(a + 1, b) + (1 - ptb) * tb(a, b + 1)
    @lru_cache(None)
    def set_(ga, gb, sa):
        if ga >= 6 and ga - gb >= 2: return 1.0
        if gb >= 6 and gb - ga >= 2: return 0.0
        if ga == 7 or gb == 7: return 1.0 if ga > gb else 0.0
        if ga == 6 and gb == 6: return tb(0, 0)
        pg = juego(0, 0, pA) if sa else 1 - juego(0, 0, pB)
        return pg * set_(ga + 1, gb, not sa) + (1 - pg) * set_(ga, gb + 1, not sa)
    need = 3 if bo == 5 else 2
    @lru_cache(None)
    def match(sa, sb, srvA):
        if sa >= need: return 1.0
        if sb >= need: return 0.0
        ps = set_(0, 0, srvA)
        return ps * match(sa + 1, sb, srvA) + (1 - ps) * match(sa, sb + 1, srvA)
    def tras_juego(sa, sb, ga, gb, srvA, ganado):
        g2a, g2b = (ga + 1, gb) if ganado else (ga, gb + 1)
        if (g2a >= 6 and g2a - g2b >= 2) or g2a == 7: return match(sa + 1, sb, not srvA)
        if (g2b >= 6 and g2b - g2a >= 2) or g2b == 7: return match(sa, sb + 1, not srvA)
        ps = set_(g2a, g2b, not srvA)
        return ps * match(sa + 1, sb, not srvA) + (1 - ps) * match(sa, sb + 1, not srvA)
    def peso(sa, sb, ga, gb, pa, pb, srvA):
        if ga == 6 and gb == 6:
            P = lambda a, b: tb(a, b) * match(sa + 1, sb, srvA) + (1 - tb(a, b)) * match(sa, sb + 1, srvA)
            return abs(P(pa + 1, pb) - P(pa, pb + 1))
        Pg = (lambda a, b: juego(a, b, pA)) if srvA else (lambda a, b: 1 - juego(b, a, pB))
        P = lambda a, b: Pg(a, b) * tras_juego(sa, sb, ga, gb, srvA, True) + (1 - Pg(a, b)) * tras_juego(sa, sb, ga, gb, srvA, False)
        return abs(P(pa + 1, pb) - P(pa, pb + 1))
    return peso


# ----------------------------------------------------------------------------
# registro punto a punto
# ----------------------------------------------------------------------------
_GANA_ULTIMO = {"winner", "ace", "service winner"}
_PIERDE_ULTIMO = {"forced error", "unforced error", "double fault"}


_VALOR = {"0": 0, "15": 1, "30": 2, "40": 3, "AD": 4, "A": 4}


def _marcador(x, desempate):
    """'30-15' -> (2, 1) ; 'AD-40' -> (4, 3) ; en un desempate '15-14' -> (15, 14). None si no se entiende."""
    try:
        v = [int(c) if desempate else _VALOR[c] for c in x.strip().upper().split("-")]
    except (KeyError, ValueError):
        return None
    return tuple(v) if len(v) == 2 else None


def _gana_por_marcador(a, b):
    """¿Ganó el jugador 1 el punto `a`? Se deduce del marcador del punto siguiente `b`."""
    if b["s"] != a["s"]:
        return b["s"][0] > a["s"][0]
    if b["g"] != a["g"]:
        return b["g"][0] > a["g"][0]
    if a["p"] is None or b["p"] is None or a["p"] == b["p"]:
        return None
    # 40-40 -> AD-40 sube el 1 ; AD-40 -> 40-40 baja el 1 (ganó el 2) ; 40-AD -> 40-40 baja el 2
    return b["p"][0] > a["p"][0] or b["p"][1] < a["p"][1]


def _puntos(h, p1, p2, gana_partido1):
    """Lista de puntos, todo orientado al JUGADOR 1 (el primero del título).
    Quién gana cada punto se lee de cómo acaba la descripción; si la página usa otra fórmula
    (anotaciones antiguas, puntos sin detalle) se deduce del marcador del punto siguiente."""
    out = []
    for f in _filas(_var(h, "pointlog"))[1:]:
        if len(f) < 5 or f[0] not in (p1, p2):
            continue
        srv1 = f[0] == p1
        s = [int(x) for x in f[1].split("-")]
        g = [int(x) for x in f[2].split("-")]
        pm = _marcador(f[3], g == [6, 6])
        if not srv1:                       # el registro cuenta desde quien saca
            s, g = s[::-1], g[::-1]
            pm = pm[::-1] if pm else None
        desc = f[4]
        m = re.search(r",\s*([a-z ]+)\.(?:\s*\(\d+-shot rally\))?\s*$", desc)
        fin = m.group(1).strip() if m else ""
        golpes = len(desc.split(";"))     # todos los golpes, incluido el fallido
        ultimo_saca = golpes % 2 == 1      # golpes impares: el último es del que saca
        if fin in _GANA_ULTIMO:
            gana_saca = ultimo_saca
        elif fin in _PIERDE_ULTIMO:
            gana_saca = not ultimo_saca
        else:
            gana_saca = None
        gana1 = None if gana_saca is None else (gana_saca == srv1)
        largo = golpes - 1 if fin in ("forced error", "unforced error") else golpes   # convención de la web
        primero_dentro = "2nd serve" not in desc.split(";")[0]
        dire = re.search(r"1st serve (wide|down the T|to body)", desc)
        out.append({"srv1": srv1, "s": s, "g": g, "p": pm, "gana1": gana1, "fin": fin,
                    "golpes": golpes, "largo": largo, "d1": dire.group(1) if (dire and primero_dentro) else None})
    for i, q in enumerate(out):
        if q["gana1"] is None:
            q["gana1"] = _gana_por_marcador(q, out[i + 1]) if i + 1 < len(out) else gana_partido1
    # algún punto suelto sin ganador (huecos en la anotación) se descarta; si son muchos, la página no vale
    sin = sum(q["gana1"] is None for q in out)
    if sin > max(2, len(out) // 50):
        raise PaginaIncompleta(f"{sin} de {len(out)} puntos sin ganador: ni la descripción ni el marcador lo dicen")
    return [q for q in out if q["gana1"] is not None]


# ----------------------------------------------------------------------------
# lector principal
# ----------------------------------------------------------------------------
def leer(h):
    titulo = re.search(r"<title>(.*?)</title>", h)
    tm = titulo and re.match(r"(\d{4}) (.*?) (\w+): (.*?) vs (.*?) Detailed Stats", titulo.group(1))
    if not tm:
        raise PaginaIncompleta("el título de la página no tiene la forma 'año torneo ronda: A vs B'")
    anio, torneo, ronda, p1, p2 = tm.groups()
    res = re.search(r"<b>([^<]*?) d\. ([^<]*?) ([0-9][^<]*)</b>", h)
    if not res:
        raise PaginaIncompleta("la página no dice el resultado ('A d. B ...'): partido sin terminar o abandonado")
    ganador, perdedor, marcador = res.group(1).strip(), res.group(2).strip(), res.group(3).strip()
    # abreviaturas tal como las escribe la página ("BS", "AZ"...), en el orden del título.
    # No se deducen del nombre: con nombres de tres palabras la web puede abreviar distinto.
    ro = _tabla(h, "rallyoutcomes", obligatoria=False)
    cab = ro[0] if ro else []
    abr = [m.group(1) for c in cab for m in [re.match(r"(.+?): W", c)] if m]
    if len(abr) != 2:
        abr = ["".join(w[0] for w in p1.split()), "".join(w[0] for w in p2.split())]
    ini = {p1: abr[0], p2: abr[1]}
    lado = {p1: "w" if p1 == ganador else "l", p2: "w" if p2 == ganador else "l"}
    bo = 5 if len(re.findall(r"\d+-\d+", re.sub(r"\(\d+\)", "", marcador))) > 3 or torneo in (
        "Australian Open", "Roland Garros", "Wimbledon", "US Open") else 3

    ov = _tabla(h, "overview")
    kp = _tabla(h, "keypoints", obligatoria=False)
    sn = _tabla(h, "serveNeut", obligatoria=False)
    pts = _puntos(h, p1, p2, p1 == ganador)
    if not pts:
        raise PaginaIncompleta("la página no trae el registro punto a punto")

    J, NV = {"w": {}, "l": {}}, {"w": {}, "l": {}}
    for k, p in ((1, p1), (2, p2)):
        L = lado[p]; d = J[L]; v = NV[L]; I = ini[p]
        # --- resumen: ganadores y errores
        fo = _fila(ov, p)
        if not fo:
            raise PaginaIncompleta(f"el resumen no tiene fila para {p}")
        cw, cu = _col(ov, "Winners"), _col(ov, "UFE")
        wm = re.match(r"(\d+)\s*\((\d+)/(\d+)\)", fo[cw]); um = re.match(r"(\d+)\s*\((\d+)/(\d+)\)", fo[cu])
        d.update(win=int(wm.group(1)), wfh=int(wm.group(2)), wbh=int(wm.group(3)),
                 ue=int(um.group(1)), ufh=int(um.group(2)), ubh=int(um.group(3)))
        # --- saque
        sv = _tabla(h, f"serve{k}")
        c_won, c_1in = _col(sv, "Won"), _col(sv, "1stIn")
        sv_pts = int(_n(_fila(sv, "Deuce Court")[1]) + _n(_fila(sv, "Ad Court")[1]))
        sv_won = int(_n(_fila(sv, "Deuce Court")[c_won]) + _n(_fila(sv, "Ad Court")[c_won]))
        zonas = ["Deuce-Wide", "Deuce-Body", "Deuce-T", "Ad-Wide", "Ad-Body", "Ad-T"]
        z = [(_n(_fila(sv, zz)[c_1in]) or 0) if _fila(sv, zz) else 0 for zz in zonas]
        tot = sum(z)
        if tot:
            d["sd"] = [round(x / tot, 3) for x in z]; d["sdn"] = int(tot)
        # --- resto
        rt = _tabla(h, f"return{k}")
        t = _fila(rt, "Total")
        if not t:
            raise PaginaIncompleta(f"la tabla de resto de {p} no tiene fila 'Total'")
        re_pts = int(_n(t[1]))
        d["pts"] = sv_pts + re_pts
        c_rtb, c_inp = _col(rt, "Returnable"), _col(rt, "inPlay")
        v["enj"] = [int(_n(t[c_inp])), int(_n(t[c_rtb]))]
        corto, prof = _fila(rt, "Svc Box"), _fila(rt, "Beh Svc Ln")   # 'Beh Svc Ln' ya incluye el cuarto trasero
        if corto and prof:
            a, b = int(_n(corto[1])), int(_n(prof[1]))
            if a + b: v["prof"] = [b, a + b]
        # --- red y saque-red
        nt = _tabla(h, f"netpts{k}", obligatoria=False)
        f = _fila(nt, "All Net Points")
        if f:
            cw2, cps = _col(nt, "Wnr at Net"), _col(nt, "Passed at Net")
            d.update(net=int(_n(f[1])), netw=int(_n(f[2])), netg=int(_n(f[cw2])), pas=int(_n(f[cps])))
        else:
            d.update(net=0, netw=0, netg=0, pas=0)
        s = _fila(nt, "Serve-and-Volley")
        v["snv"] = [int(_n(s[1])) if s else 0, sv_pts]
        # --- dirección de golpes
        sdir = _tabla(h, f"shotdir{k}", obligatoria=False)
        f = _fila(sdir, "Total") or []
        cols = [_n(x) or 0 for x in f[1:6]]
        if sum(cols):
            v["cruz"] = [int(cols[0]), int(sum(cols))]; v["par"] = [int(cols[2]), int(sum(cols))]
        # --- influencia del saque: ventaja que se evapora
        f = _fila(sn, f"{I} 1st Serve")
        if f:
            c1, c5 = _col(sn, "1+"), _col(sn, "5+")
            if c1 is not None and c5 is not None and len(f) > max(c1, c5) and f[c1] and f[c5]: v["evap"] = [_n(f[c1]), _n(f[c5])]
        # --- temple: bolas de break frente al saque corriente
        f = _fila(kp, f"{I} BP Faced")
        if f and _n(f[1]):
            v["temple"] = [int(_n(f[2])), int(_n(f[1])), sv_won, sv_pts]
        # --- peloteo por longitud
        cW = next((i for i, c in enumerate(cab) if c.startswith(f"{I}: W")), None)
        if cW is not None:            # páginas sin tabla de peloteo: se omite el dato
            rl = {}
            for et, q in (("All: 1-3 Shots", "1-3"), ("All: 4-6 Shots", "4-6"), ("All: 7-9 Shots", "7-9"), ("All: 10+ Shots", "10")):
                f = _fila(ro, et)
                rl[q] = [int(_n(f[cW]) or 0), int(_n(f[1]) or 0)] if f and len(f) > cW else [0, 0]
            d["rally"] = rl

    # --- secuencia de juegos, orientada al jugador 1
    # un desempate es un único "juego" 6-6 aunque el saque cambie dentro de él
    seq, prev = [], None
    for q in pts:
        clave = (tuple(q["s"]), tuple(q["g"]))
        if clave != prev:
            seq.append({"s": q["s"], "g": q["g"], "sv": 1 if q["srv1"] else 2, "p": []})
            prev = clave
        seq[-1]["p"].append(1 if q["gana1"] else 2)

    # --- primer golpe tras el saque, rachas y peso
    L1, L2 = lado[p1], lado[p2]
    s1 = {L1: [0, 0, 0], L2: [0, 0, 0]}
    for q in pts:
        srv = L1 if q["srv1"] else L2
        if q["golpes"] >= 3:
            s1[srv][2] += 1
            if (q["golpes"] == 3 and q["fin"] == "winner") or (q["golpes"] == 4 and q["fin"] == "forced error"):
                s1[srv][0] += 1
            elif q["golpes"] == 3 and q["fin"] in ("forced error", "unforced error"):
                s1[srv][1] += 1
    for L in "wl":
        NV[L]["s1"] = s1[L]
    gan = [(L1 if q["gana1"] else L2) for q in pts]
    for L in "wl":
        best = cur = 0; fi = 0
        for i, g in enumerate(gan):
            cur = cur + 1 if g == L else 0
            if cur > best: best, fi = cur, i
        q = pts[fi]; ss = q["s"] if L1 == "w" else q["s"][::-1]; gg = q["g"] if L1 == "w" else q["g"][::-1]
        NV[L]["racha"] = [best, sum(q["s"]) + 1, gg[0], gg[1]]
    s1pts = [q for q in pts if q["srv1"]]; s2pts = [q for q in pts if not q["srv1"]]
    pA = min(max(sum(q["gana1"] for q in s1pts) / max(len(s1pts), 1), .4), .9)
    pB = min(max(sum(not q["gana1"] for q in s2pts) / max(len(s2pts), 1), .4), .9)
    peso = _modelo(pA, pB, bo)
    tot = w1 = 0; top = None
    for j in seq:
        a = b = 0
        for w in j["p"]:
            wt = peso(j["s"][0], j["s"][1], j["g"][0], j["g"][1], a, b, j["sv"] == 1)
            tot += wt; w1 += wt if w == 1 else 0
            if top is None or wt > top[0]:
                top = (wt, j, a, b, w)
            a, b = (a + 1, b) if w == 1 else (a, b + 1)
    NV[L1]["peso"] = round(w1 / tot, 3); NV[L2]["peso"] = round(1 - w1 / tot, 3)
    wt, j, a, b, w = top
    inv = L1 == "l"
    NV["top"] = {"w": round(wt, 3), "set": sum(j["s"]) + 1,
                 "g": j["g"][::-1] if inv else j["g"], "p": [b, a] if inv else [a, b],
                 "sv": ("w" if (j["sv"] == 1) != inv else "l"), "gana": ("w" if (w == 1) != inv else "l")}

    sets = [[int(x) for x in m] for m in re.findall(r"(\d+)-(\d+)", re.sub(r"\(\d+\)", "", marcador))]
    deep = {"mid": f"{anio}-{torneo}-{ronda}-{p1}-{p2}", "j1": L1, "J": J, "seq": seq, "np": len(pts)}
    meta = {"anio": int(anio), "torneo": torneo, "ronda": ronda, "p1": p1, "p2": p2,
            "ganador": ganador, "perdedor": perdedor, "marcador": marcador, "sets": sets, "bo": bo}
    return meta, deep, NV
