"""
DESCARGAS DEL ROBOT NOCTURNO
============================
Tres fuentes, cada una independiente: si una falla, las demás siguen.

  tml()          temporada en curso (y la anterior en enero) desde TennisMyLife
  mcp_repo()     repositorio del Match Charting Project, solo si su autor lo ha actualizado
  mcp_paginas()  páginas de partidos recién anotados en tennisabstract.com

Nunca se sustituye un fichero bueno por uno peor: si lo descargado tiene menos
partidos que lo que ya había, se conserva lo anterior.
"""
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.request
import urllib.robotparser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from leer_partido import leer, VERSION

RAIZ = Path(__file__).resolve().parent.parent
D = RAIZ / "datos"
CONTACTO = os.environ.get("CONTACTO", "").strip()
AGENTE = f"Mozilla/5.0 (compatible; DeuceBot/1.0; web de tenis sin animo de lucro; +mailto:{CONTACTO or 'sin-contacto'})"
# reglas publicadas en https://tennisabstract.com/robots.txt (se usan si no se puede leer en el momento)
ROBOTS_CONOCIDO = "User-agent: *\nDisallow: /jsfrags/\nDisallow: /jsmatches/\nDisallow: /jsplayers/\n"


def get(url, timeout=90):
    cab = {"User-Agent": AGENTE}
    # en GitHub el robot se identifica: las consultas anónimas a su API tienen un límite muy bajo
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"):
        cab["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(url, headers=cab)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def temporada_actual(hoy=None):
    hoy = hoy or dt.date.today()
    return hoy.year + (1 if (hoy.month == 12 and hoy.day >= 20) else 0)


# ----------------------------------------------------------------------------
# 1 · TennisMyLife
# ----------------------------------------------------------------------------
def tml():
    carpeta = D / "tml"
    carpeta.mkdir(exist_ok=True)
    actual = temporada_actual()
    anios = [actual] + ([actual - 1] if dt.date.today().month <= 2 else [])   # en enero llegan correcciones
    try:
        listado = json.loads(get("https://stats.tennismylife.org/api/data-files"))["files"]
    except Exception as e:
        print(f"  [tml] no se pudo leer el listado de ficheros ({e}); se prueba la dirección directa")
        listado = []
    informe = []
    for a in anios:
        nombre = f"{a}.csv"
        url = next((f["url"] for f in listado if f.get("name") == nombre or str(f.get("url", "")).endswith("/" + nombre)),
                   f"https://stats.tennismylife.org/data/{nombre}")
        try:
            nuevo = pd.read_csv(io.BytesIO(get(url)), low_memory=False)
        except Exception as e:
            informe.append(f"{a}: no disponible ({e})")
            continue
        faltan = {"tourney_date", "winner_name", "loser_name", "score", "w_svpt"} - set(nuevo.columns)
        if faltan:
            informe.append(f"{a}: formato inesperado, faltan {faltan}; se conserva el anterior")
            continue
        ruta = carpeta / nombre
        viejo = len(pd.read_csv(ruta, low_memory=False)) if ruta.exists() else 0
        if len(nuevo) < 0.9 * viejo:
            informe.append(f"{a}: el nuevo trae {len(nuevo)} partidos y el anterior {viejo}; se conserva el anterior")
            continue
        nuevo.to_csv(ruta, index=False)
        informe.append(f"{a}: {len(nuevo)} partidos (antes {viejo})")
    print("  [tml] " + " · ".join(informe))


# ----------------------------------------------------------------------------
# 2 · repositorio del Match Charting Project
# ----------------------------------------------------------------------------
FICHEROS_MCP = ["charting-m-matches", "charting-m-points-to-2009", "charting-m-points-2010s", "charting-m-points-2020s"] + \
    [f"charting-m-stats-{n}" for n in ("Overview", "NetPoints", "ServeDirection", "Rally", "KeyPointsServe",
                                       "ShotDirection", "ReturnDepth", "ReturnOutcomes", "ServeInfluence", "SnV")]


def mcp_repo():
    """Devuelve True si el repositorio ha cambiado y se ha descargado de nuevo."""
    marca = D / "mcp_sha.txt"
    sha = None
    try:
        sha = json.loads(get("https://api.github.com/repos/JeffSackmann/tennis_MatchChartingProject/commits/master"))["sha"]
    except Exception:
        try:   # plan B: la versión aparece en la página de cambios del repositorio
            html = get("https://github.com/JeffSackmann/tennis_MatchChartingProject/commits/master").decode("utf-8", "ignore")
            sha = re.search(r"/commit/([0-9a-f]{40})", html).group(1)
        except Exception as e:
            print(f"  [mcp] no se pudo consultar el repositorio ({e})")
            return False
    if marca.exists() and marca.read_text().strip() == sha:
        print("  [mcp] el repositorio no ha cambiado")
        return False
    carpeta = D / "mcp"
    carpeta.mkdir(exist_ok=True)
    base = "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/"
    for f in FICHEROS_MCP:
        (carpeta / f"{f}.csv").write_bytes(get(base + f + ".csv", timeout=300))
    marca.write_text(sha)
    print(f"  [mcp] repositorio actualizado ({sha[:7]}), {len(FICHEROS_MCP)} ficheros")
    return True


# ----------------------------------------------------------------------------
# 3 · páginas de partidos recién anotados
# ----------------------------------------------------------------------------
BASE_WEB = "https://tennisabstract.com/charting/"


def pendientes(nombres, excluir):
    """De todos los partidos masculinos de Tennis Abstract, los que están en NUESTRO archivo
    y aún no tenemos. Así no se pide ni un Challenger, ni una previa, ni un junior."""
    from profundo import Archivo
    arch = pd.read_parquet(D / "calculado.parquet", columns=["fecha", "anio", "tourney_name", "round", "winner_name", "loser_name"])
    A = Archivo(arch)
    actual = int(arch.anio.max())
    out = []
    for n in nombres:
        if n[:-5] in excluir:
            continue
        p = n[:-5].split("-")                 # AAAAMMDD-M-torneo(-con-guiones)-ronda-jugador1-jugador2
        if len(p) < 6:
            continue
        try:
            fecha = pd.Timestamp(p[0])
        except Exception:
            continue
        if A.candidatos(p[-2].replace("_", " "), p[-1].replace("_", " "), fecha, p[-3], "-".join(p[2:-3])):
            out.append(n)
    # primero la temporada en curso, de lo más antiguo a lo más reciente; después el resto
    out.sort(key=lambda n: (int(n[:4]) < actual, n))
    return out


def leer_robots(informe):
    """El robots.txt se lee con NUESTRA identificación. La herramienta estándar de Python se presenta
    con un nombre genérico; si la web se lo rechaza, interpreta que está prohibido TODO y el robot
    se quedaría sin leer ninguna página sin decir nada."""
    rp = urllib.robotparser.RobotFileParser("https://tennisabstract.com/robots.txt")
    try:
        rp.parse(get("https://tennisabstract.com/robots.txt", timeout=30).decode("utf-8", "ignore").splitlines())
        informe.append("robots.txt: leído")
    except Exception as e:
        rp.parse(ROBOTS_CONOCIDO.splitlines())
        informe.append(f"robots.txt: no se pudo leer ({e}); se usan sus reglas conocidas")
    return rp


def mcp_paginas(maximo=600, pausa=5):
    """Baja TODAS las páginas de partidos anotados que falten, en tandas de `maximo`.
    Deja un informe legible en datos/mcp_paginas/_diagnostico.txt."""
    carpeta = D / "mcp_paginas"
    carpeta.mkdir(exist_ok=True)
    inf = [f"Informe del robot · {dt.datetime.now():%Y-%m-%d %H:%M}"]
    try:
        _mcp_paginas(carpeta, maximo, pausa, inf)
    except Exception as e:
        inf.append(f"ERROR inesperado: {type(e).__name__}: {e}")
        raise
    finally:
        (carpeta / "_diagnostico.txt").write_text("\n".join(inf) + "\n", encoding="utf-8")
        print("  [páginas] " + "\n  [páginas] ".join(inf[1:]))


def _mcp_paginas(carpeta, maximo, pausa, inf):
    if not CONTACTO:
        inf.append("FALTA EL SECRETO CONTACTO: sin él no se lee ninguna página de Tennis Abstract.")
        return
    robots = leer_robots(inf)
    if not robots.can_fetch(AGENTE, BASE_WEB):
        inf.append("el robots.txt no permite leer la lista de partidos; no se descarga nada")
        return
    try:
        lista = get(BASE_WEB).decode("utf-8", "ignore")          # lista completa: una sola petición
    except Exception as e:
        inf.append(f"NO SE PUDO LEER LA LISTA DE PARTIDOS de Tennis Abstract: {e}")
        return
    nombres = sorted(set(re.findall(r"(\d{8}-M-[A-Za-z0-9_.\-]+?\.html)", lista)))
    inf.append(f"lista de Tennis Abstract: {len(lista)//1024} KB · partidos masculinos: {len(nombres):,}")
    # páginas que llegaron pero no se pudieron entender: se apartan 14 días (pueden estar a medio anotar).
    # Si cambia la versión del lector, se olvidan y se reintentan. Los fallos de conexión no se apuntan.
    fallos = carpeta / "_fallos.txt"
    hoy = dt.date.today()
    registro = {}
    if fallos.exists():
        lineas = fallos.read_text().split("\n")
        if lineas and lineas[0] == f"version {VERSION}":
            for linea in lineas[1:]:
                partes = linea.split()
                if len(partes) == 2:
                    registro[partes[0]] = dt.date.fromisoformat(partes[1])
    repo = D / "profundo_repo.json"
    excluir = {v["deep"]["mid"] for v in json.load(open(repo)).values()} if repo.exists() else set()
    excluir |= {f.stem for f in carpeta.glob("*.json")}                      # ya convertidas
    excluir |= {n[:-5] for n, f in registro.items() if (hoy - f).days < 14}  # apartadas
    nuevos = pendientes(nombres, excluir)
    rg = [n for n in nuevos if "Roland_Garros" in n and n.startswith(str(temporada_actual()))]
    inf.append(f"de nuestro archivo y aún sin tener: {len(nuevos):,} (de Roland Garros {temporada_actual()}: {len(rg)})")
    hechos, sin_red, no_leidas, ejemplos = 0, 0, 0, []
    for n in nuevos[:maximo]:
        url = BASE_WEB + n
        if not robots.can_fetch(AGENTE, url):
            continue
        time.sleep(pausa)
        try:
            html = get(url).decode("utf-8", "ignore")
        except Exception as e:
            sin_red += 1
            if len(ejemplos) < 5: ejemplos.append(f"sin conexión con {n}: {e}")
            continue
        try:
            meta, deep, nv = leer(html)
            json.dump({"meta": meta, "deep": deep, "nv": nv},
                      open(carpeta / n.replace(".html", ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
            hechos += 1
            registro.pop(n, None)
        except Exception as e:
            no_leidas += 1
            registro[n] = hoy
            if len(ejemplos) < 5: ejemplos.append(f"no se pudo interpretar {n}: {type(e).__name__}: {e}")
    fallos.write_text(f"version {VERSION}\n" + "\n".join(f"{n} {f.isoformat()}" for n, f in sorted(registro.items())))
    resto = max(0, len(nuevos) - maximo)
    inf.append(f"descargadas y convertidas: {hechos} · fallos de conexión: {sin_red} · no interpretadas: {no_leidas}")
    inf += ["  " + e for e in ejemplos]
    inf.append(f"quedan {resto} para la próxima ejecución" if resto else "AL DÍA: no falta ningún partido anotado de nuestro archivo")
