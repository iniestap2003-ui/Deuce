"""
ROBOT NOCTURNO DE DEUCE
=======================
Lo ejecuta GitHub cada madrugada. También se puede lanzar a mano:

    python src/nocturno.py              # noche normal
    python src/nocturno.py --sin-red    # reconstruir sin descargar nada (pruebas)

Pasos:
  1. Descargas (cada fuente por separado: si una falla, las demás siguen)
  2. Cálculo de las 36+ temporadas
  3. Análisis profundo (repositorio si cambió + páginas nuevas)
  4. Construcción de la web
  5. Comprobaciones. Si algo no cuadra, el robot se detiene con error:
     no se publica nada y GitHub avisa por correo. La web sigue con la versión anterior.
"""
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
RAIZ = Path(__file__).resolve().parent.parent
D, W = RAIZ / "datos", RAIZ / "web" / "datos"


def paso(nombre, fn, critico=False):
    print(f"\n== {nombre}")
    try:
        return fn()
    except Exception:
        traceback.print_exc()
        if critico:
            sys.exit(f"ERROR en «{nombre}»: no se publica nada esta noche.")
        print(f"  (fallo no crítico en «{nombre}»: se sigue con lo que ya había)")
        return None


def comprobar():
    """Última barrera antes de publicar."""
    estado_f = D / "estado.json"
    antes = json.load(open(estado_f)) if estado_f.exists() else {}
    T = json.load(open(W / "temporadas.json"))
    total = sum(v["n"] for v in T["anios"].values())
    prof = sum(v["dp"] for v in T["anios"].values())
    problemas = []
    if antes.get("partidos") and total < 0.98 * antes["partidos"]:
        problemas.append(f"hay {total} partidos y la última vez había {antes['partidos']}")
    if antes.get("profundos") and prof < 0.95 * antes["profundos"]:
        problemas.append(f"hay {prof} análisis profundos y la última vez había {antes['profundos']}")
    for f in list(W.glob("*.json")) + list(W.glob("t/*.json")) + list(W.glob("p/*.json")):
        try:
            json.loads(f.read_text(encoding="utf-8"), parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        except Exception as e:
            problemas.append(f"{f.name} no es un archivo válido ({e})")
    if not (RAIZ / "web" / "index.html").exists():
        problemas.append("falta la página web")
    if problemas:
        sys.exit("NO SE PUBLICA:\n  - " + "\n  - ".join(problemas))
    json.dump({"partidos": total, "profundos": prof, "fecha": dt.date.today().isoformat(),
               "temporadas": len(T["anios"]), "actual": T["actual"]}, open(estado_f, "w"), indent=1)
    print(f"  todo en orden: {total:,} partidos · {prof:,} análisis profundos · {len(T['anios'])} temporadas")


def main():
    sin_red = "--sin-red" in sys.argv
    cambio_repo = False
    if not sin_red:
        import descargar
        paso("Temporada en curso (TennisMyLife)", descargar.tml)
        cambio_repo = bool(paso("Repositorio golpe a golpe", descargar.mcp_repo))
        domingo = dt.date.today().weekday() == 6
        paso("Páginas nuevas de partidos anotados",
             lambda: descargar.mcp_paginas(todo=domingo, maximo=150 if domingo else 60))
    import calcular, profundo, construir_web
    paso("Cálculo de todas las temporadas", calcular.calcular, critico=True)
    r = paso("Análisis profundo", lambda: profundo.construir(recalcular_repo=cambio_repo or None), critico=True)
    print(f"  análisis profundos: {r[2]:,} · desde páginas web: {r[4]}")
    paso("Construcción de la web", construir_web.construir, critico=True)
    paso("Comprobaciones antes de publicar", comprobar, critico=True)


if __name__ == "__main__":
    main()
