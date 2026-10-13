"""Lector de páginas del Match Charting Project (src/leer_partido.py)."""
import pytest

from leer_partido import _filas, _modelo, _n, _puntos, _var, leer
from pagina_falsa import pagina


@pytest.fixture(scope="module")
def partido():
    return leer(pagina())


# --- piezas sueltas ----------------------------------------------------------

@pytest.mark.parametrize("celda, esperado", [
    ("43  (68%)", 43), ("71.3%", 0.713), ("-2", -2), ("", None), (None, None), ("-", None),
])
def test_numero_de_celda(celda, esperado):
    assert _n(celda) == esperado


def test_variable_con_comillas_escapadas():
    h = "var a = 'uno \\' dos'; var b = 'tres';"
    assert _var(h, "a") == "uno \\' dos"
    assert _var(h, "b") == "tres"
    assert _var(h, "c") == ""


def test_filas_limpia_etiquetas_y_entidades():
    t = "<tr><th>A&amp;B</th><td><b>1</b>&nbsp;</td></tr><tr><td></td></tr>"
    assert _filas(t) == [["A&B", "1"]]


def test_quien_gana_cada_punto():
    pts = _puntos(pagina(), "Ana Uno", "Bea Dos")
    assert [p["gana1"] for p in pts] == [True, True, True, False, True, True, True]
    assert [p["fin"] for p in pts] == ["ace", "forced error", "winner", "unforced error",
                                      "unforced error", "winner", "double fault"]
    # la web no cuenta el golpe que acaba en error
    assert [p["golpes"] for p in pts] == [1, 2, 3, 3, 2, 2, 1]
    assert [p["largo"] for p in pts] == [1, 1, 3, 2, 1, 2, 1]
    # dirección solo cuando entra el primer saque
    assert [p["d1"] for p in pts] == ["wide", "down the T", "to body", None, "wide", "down the T", None]


def test_marcador_orientado_al_jugador_1():
    pts = _puntos(pagina(), "Ana Uno", "Bea Dos")
    # Bea saca con "0-1" en su registro: para Ana es 1-0
    assert pts[-1]["g"] == [1, 0] and not pts[-1]["srv1"]


def test_modelo_de_peso():
    peso = _modelo(0.65, 0.65, 3)
    # el punto de break 30-40 pesa más que el 40-0
    assert peso(0, 0, 4, 4, 2, 3, True) > peso(0, 0, 4, 4, 3, 0, True)
    # en el desempate del set decisivo el punto pesa más que al empezar el partido
    assert peso(1, 1, 6, 6, 5, 5, True) > peso(0, 0, 0, 0, 0, 0, True)
    for args in [(0, 0, 0, 0, 0, 0, True), (1, 1, 6, 6, 6, 6, False), (1, 0, 5, 3, 3, 1, False)]:
        assert 0 <= peso(*args) <= 1


# --- lector completo ---------------------------------------------------------

def test_meta(partido):
    meta, deep, nv = partido
    assert meta == {"anio": 2026, "torneo": "Test Open", "ronda": "F", "p1": "Ana Uno", "p2": "Bea Dos",
                    "ganador": "Ana Uno", "perdedor": "Bea Dos", "marcador": "6-4 7-6(5)",
                    "sets": [[6, 4], [7, 6]], "bo": 3}
    assert deep["j1"] == "w" and deep["np"] == 7


def test_bo5_en_grand_slam():
    h = pagina().replace("Test Open", "Wimbledon")
    assert leer(h)[0]["bo"] == 5


def test_estadisticas_del_ganador(partido):
    w = partido[1]["J"]["w"]
    assert (w["win"], w["wfh"], w["wbh"], w["ue"], w["ufh"], w["ubh"]) == (10, 6, 4, 5, 3, 2)
    assert w["pts"] == 60 + 50
    assert w["sd"] == [0.25, 0.1, 0.15, 0.2, 0.05, 0.25] and w["sdn"] == 20
    assert (w["net"], w["netw"], w["netg"], w["pas"]) == (12, 8, 5, 2)
    assert w["rally"] == {"1-3": [5, 6], "4-6": [0, 1], "7-9": [0, 0], "10": [0, 0]}


def test_estadisticas_del_perdedor(partido):
    l = partido[1]["J"]["l"]
    assert (l["win"], l["ue"]) == (7, 12)
    assert l["pts"] == 50 + 60
    assert (l["net"], l["netw"]) == (0, 0)          # sin tabla de red: ceros, no error
    assert l["rally"]["1-3"] == [1, 6]


def test_bloque_nv(partido):
    nv = partido[2]
    w, l = nv["w"], nv["l"]
    assert w["enj"] == [30, 40] and w["prof"] == [20, 30]
    assert w["snv"] == [3, 60] and l["snv"] == [0, 50]
    assert w["cruz"] == [40, 100] and w["par"] == [10, 100]
    assert w["evap"] == [0.7, 0.55]
    assert w["temple"] == [3, 4, 38, 60]
    assert w["s1"] == [1, 1, 2] and l["s1"] == [0, 0, 0]
    assert w["racha"] == [3, 1, 0, 0] and l["racha"] == [1, 1, 0, 0]
    # lo que la página no trae se omite en lugar de inventarse
    for k in ("prof", "cruz", "evap", "temple"):
        assert k not in l


def test_peso_reparte_todo_el_partido(partido):
    nv = partido[2]
    assert nv["w"]["peso"] + nv["l"]["peso"] == pytest.approx(1, abs=0.001)
    assert nv["w"]["peso"] > 0.5                    # Ana ganó 6 de 7 puntos
    assert nv["top"]["set"] == 1 and nv["top"]["sv"] in "wl"


def test_secuencia_de_juegos(partido):
    seq = partido[1]["seq"]
    assert seq == [{"s": [0, 0], "g": [0, 0], "sv": 1, "p": [1, 1, 1, 2, 1]},
                   {"s": [0, 0], "g": [1, 0], "sv": 2, "p": [1, 1]}]


def test_perdedor_como_jugador_1():
    """Si el primero del título pierde, todo se reorienta sin mezclar los bloques."""
    h = pagina().replace("<b>Ana Uno d. Bea Dos 6-4 7-6(5)</b>", "<b>Bea Dos d. Ana Uno 4-6 6-3 6-2</b>")
    meta, deep, nv = leer(h)
    assert meta["ganador"] == "Bea Dos" and deep["j1"] == "l"
    assert deep["J"]["l"]["win"] == 10 and deep["J"]["w"]["win"] == 7
    assert nv["l"]["racha"][0] == 3
    assert nv["l"]["peso"] + nv["w"]["peso"] == pytest.approx(1, abs=0.001)
