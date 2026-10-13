# Diagnóstico temporal: baja las páginas que el lector no entendió y explica por qué.
import collections, re, sys, time, traceback
from pathlib import Path
sys.path.insert(0, "src")
from descargar import get, BASE_WEB
import leer_partido as lp

nombres = [l.split()[0] for l in Path("datos/mcp_paginas/_fallos.txt").read_text().split("\n")[1:] if l.strip()]
# muestra repartida por años
porano = collections.defaultdict(list)
for n in nombres: porano[n[:4]].append(n)
muestra = nombres   # todas las apartadas
print("muestra", len(muestra), "de", len(nombres))
fines = collections.Counter(); errores = collections.Counter(); ok = 0
for i, n in enumerate(muestra):
    time.sleep(3)
    try:
        h = get(BASE_WEB + n).decode("utf-8", "ignore")
    except Exception as e:
        print("RED", n, e); continue
    vacias = [v for v in ("pointlog","overview","keypoints","serveNeut","rallyoutcomes","serve1","serve2","return1","return2","netpts1","netpts2","shotdir1","shotdir2") if not lp._filas(lp._var(h, v))]
    pl = lp._filas(lp._var(h, "pointlog"))
    raros = collections.Counter()
    for f in pl[1:]:
        if len(f) >= 5:
            m = re.search(r",\s*([a-z ]+)\.(?:\s*\(\d+-shot rally\))?\s*$", f[4])
            fin = m.group(1).strip() if m else ""
            if fin not in lp._GANA_ULTIMO | lp._PIERDE_ULTIMO:
                raros[f[4][-60:]] += 1
    fines.update({k: v for k, v in raros.items()})
    try:
        lp.leer(h); ok += 1; print("OK ", n)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        errores[f"{type(e).__name__} l.{tb.lineno}: {tb.line}"] += 1
        print("ERR", n, f"{type(e).__name__}: {e} | l.{tb.lineno}: {tb.line}")
    print("    filas pointlog:", len(pl), "| cabecera:", pl[0] if pl else None, "| vacías:", vacias, "| fines raros:", sum(raros.values()))
    if i < 3 or (raros and sum(raros.values()) < 400 and i % 5 == 0):
        for f in pl[1:4]: print("    fila:", f)
        for k, v in list(raros.items())[:5]: print("    raro:", v, repr(k))
    t = re.search(r"<title>(.*?)</title>", h); print("    título:", t.group(1) if t else None)
print("\n== RESUMEN ==  ok:", ok)
for k, v in errores.most_common(): print(v, k)
print("== FINES NO RECONOCIDOS (top 60) ==")
for k, v in fines.most_common(60): print(v, repr(k))
