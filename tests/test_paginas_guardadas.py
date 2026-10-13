"""Los análisis guardados en datos/mcp_paginas/ conservan el formato que lee profundo.py."""
import json
from pathlib import Path

import pytest

ARCHIVOS = sorted((Path(__file__).resolve().parent.parent / "datos" / "mcp_paginas").glob("*.json"))


@pytest.mark.skipif(not ARCHIVOS, reason="no hay páginas guardadas")
def test_formato_de_las_paginas_guardadas():
    malos = []
    for f in ARCHIVOS:
        x = json.loads(f.read_text(encoding="utf-8"))
        meta, deep, nv = x["meta"], x["deep"], x["nv"]
        ok = (meta["ganador"] in (meta["p1"], meta["p2"]) and meta["bo"] in (3, 5)
              and deep["j1"] in "wl" and set(deep["J"]) == {"w", "l"} and deep["seq"]
              and abs(nv["w"]["peso"] + nv["l"]["peso"] - 1) <= 0.002)
        if not ok:
            malos.append(f.name)
    assert not malos, f"{len(malos)} páginas mal formadas: {malos[:5]}"
