"""Lector de marcadores y métricas de partido (src/limpieza.py y src/metricas.py)."""
import math

import numpy as np
import pandas as pd
import pytest

from limpieza import juegos_totales, limpiar, sets_del_marcador, victoria_completa
from metricas import construir_todo, contexto, estructura, parsear, rendimiento


# --- marcadores ---------------------------------------------------------------

@pytest.mark.parametrize("score, sets", [
    ("6-4 3-6 7-6(5)", [(6, 4), (3, 6), (7, 6)]),
    ("6-3 6-7(4) [10-6]", [(6, 3), (6, 7), (1, 0)]),      # super tiebreak = un juego
    ("6-3 6-7(4) [8-10]", [(6, 3), (6, 7), (0, 1)]),
    ("6-4 2-1 RET", [(6, 4), (2, 1)]),
    ("W/O", []), ("", []), (None, []), (float("nan"), []),
])
def test_sets_del_marcador(score, sets):
    assert sets_del_marcador(score) == sets


def test_parsear_guarda_puntos_del_tiebreak():
    assert parsear("6-4 6-7(3) 7-6(10)") == [(6, 4, None), (6, 7, 3), (7, 6, 10)]
    assert parsear("W/O") is None


@pytest.mark.parametrize("score, bo, completa", [
    ("6-4 6-4", 3, True), ("6-4 6-4", 5, False), ("6-4 3-6 6-1 6-2", 5, True), ("6-4 1-6", 3, False),
])
def test_victoria_completa(score, bo, completa):
    assert victoria_completa(score, bo) is completa


def test_juegos_totales():
    assert juegos_totales("6-4 7-6(5)") == 23
    assert math.isnan(juegos_totales("W/O"))


# --- A · estructura -------------------------------------------------------------

def test_estructura_partido_ajustado_con_vuelco():
    e = estructura("4-6 7-6(5) 6-4")
    assert (e["juegos_g"], e["juegos_p"], e["margen_juegos"], e["n_sets"]) == (17, 16, 1, 3)
    assert e["vuelco"] == 1 and e["gano_1er_set"] == 0 and e["set_decisivo"] == 1
    assert (e["tiebreaks"], e["tiebreaks_ganados"], e["margen_tb_medio"]) == (1, 1, 2)
    assert e["sets_ajustados"] == 3 and e["sets_paliza"] == 0
    assert e["trayectoria"] > 0                     # fue a más


def test_estructura_paliza():
    e = estructura("6-0 6-1")
    assert e["roscos_dados"] == 1 and e["roscos_recibidos"] == 0 and e["sets_paliza"] == 2
    assert e["tiebreaks"] == 0 and math.isnan(e["margen_tb_medio"])


def test_tension_ordena_partidos():
    # cada set a un juego de diferencia, más el plus por llegar al set decisivo
    assert estructura("7-6(5) 6-7(5) 7-6(8)")["tension"] == pytest.approx(100 * 5 / 6 * 1.15, abs=0.1)
    assert estructura("6-0 6-0")["tension"] == 0
    assert estructura("6-0 6-0")["tension"] < estructura("6-4 6-4")["tension"] < estructura("7-5 7-6")["tension"]


@pytest.mark.parametrize("score, decisivo", [
    ("6-4 3-6 6-3", 1), ("6-4 3-6 6-3 4-6 6-2", 1), ("6-3 6-7(4) [10-6]", 1),
    ("6-4 6-4", 0), ("6-4 6-4 6-4", 0), ("6-4 3-6 6-3 6-2", 0),
])
def test_set_decisivo(score, decisivo):
    assert estructura(score)["set_decisivo"] == decisivo


def test_un_3_0_a_cinco_sets_no_lleva_plus_de_tension():
    # mismos sets que un 6-4 6-4 a tres: sin plus, la misma tensión
    assert estructura("6-4 6-4 6-4")["tension"] == estructura("6-4 6-4")["tension"]


def test_volatilidad():
    assert estructura("6-4 6-4")["volatilidad"] == 0
    assert estructura("6-1 1-6 6-1")["volatilidad"] > estructura("6-4 4-6 6-4")["volatilidad"]


def test_estructura_sin_marcador():
    assert estructura("W/O") == {}


# --- B, C, D · métricas sobre la tabla de partidos ---------------------------------

def partidos():
    """Dos partidos con cifras sencillas. El segundo es un 'robo': gana con menos puntos."""
    return pd.DataFrame({
        "score": ["6-4 6-4", "4-6 7-6(5) 7-6(3)"],
        "minutes": [90, 180],
        "tourney_level": ["G", "A"], "round": ["F", "R32"],
        "winner_rank": [1, 80], "loser_rank": [10, 5],
        "w_svpt": [60, 100], "w_1stIn": [40, 60], "w_1stWon": [30, 40], "w_2ndWon": [12, 20],
        "w_ace": [8, 5], "w_df": [2, 0], "w_SvGms": [10, 16], "w_bpSaved": [2, 6], "w_bpFaced": [2, 7],
        "l_svpt": [60, 110], "l_1stIn": [36, 70], "l_1stWon": [24, 52], "l_2ndWon": [10, 26],
        "l_ace": [3, 12], "l_df": [4, 3], "l_SvGms": [10, 17], "l_bpSaved": [3, 2], "l_bpFaced": [5, 3],
    })


def test_rendimiento():
    r = rendimiento(partidos())
    assert r.loc[0, "pct_1er_dentro_w"] == pytest.approx(40 / 60)
    assert r.loc[0, "pct_gana_1er_w"] == pytest.approx(30 / 40)
    assert r.loc[0, "pct_gana_2o_w"] == pytest.approx(12 / 20)
    assert r.loc[0, "pct_pts_saque_w"] == pytest.approx(42 / 60)
    assert r.loc[0, "pct_pts_resto_w"] == pytest.approx(1 - 34 / 60)
    assert r.loc[0, "bp_convertidas_w"] == 2 and r.loc[0, "pct_bp_convertidas_w"] == pytest.approx(0.4)
    assert r.loc[0, "pts_g"] == 42 + 26 and r.loc[0, "pts_p"] == 34 + 18
    assert r.loc[0, "pts_total"] == 120 and r.loc[0, "min_por_punto"] == pytest.approx(0.75)
    # sin dobles faltas el cociente queda vacío, no infinito
    assert math.isnan(r.loc[1, "ace_df_ratio_w"])


def test_saque_a_cero_se_estima_desde_el_marcador():
    d = partidos().assign(w_SvGms=0, l_SvGms=0, _juegos_marcador=[20, 37])
    r = rendimiento(d)
    assert r.loc[0, "presion_recibida_w"] == pytest.approx(2 / 10)


def test_construir_todo():
    t = construir_todo(partidos())
    assert len(t) == 2 and t.columns.is_unique
    # robo: el ganador del segundo partido hizo menos puntos que el rival
    assert t.loc[0, "robo"] == 0 and t.loc[1, "robo"] == 1
    assert t.loc[1, "margen_robo"] > 0
    # dominación > 1 = manda el ganador
    assert t.loc[0, "dominacion_g"] > 1 > t.loc[0, "dominacion_p"]
    assert t.loc[0, "eficiencia_g"] == pytest.approx(12 / 20 - 68 / 120)
    assert t.loc[0, "pts_clave_g"] == 2 + 2 + 0 and t.loc[0, "pts_clave_total"] == 2 + 5 + 0
    assert t.loc[1, "resiliencia_g"] == 1
    assert t.loc[0, "indice_saques"] == pytest.approx(1 - 2 / 20)
    assert t.loc[0, "desgaste"] == pytest.approx(120)


def test_contexto():
    d = partidos()
    c = contexto(d, d["score"].apply(estructura).apply(pd.Series))
    assert list(c["es_sorpresa"]) == [0, 1]
    assert c.loc[0, "magnitud_sorpresa"] == 0
    assert c.loc[1, "magnitud_sorpresa"] == pytest.approx(np.log(16))
    assert c.loc[0, "importancia"] == 4 * 3 and c.loc[1, "importancia"] == 2 * 1


# --- limpieza ------------------------------------------------------------------------

def test_limpiar_descarta_y_contabiliza():
    base = partidos().assign(best_of=3, surface="Hard", winner_id=[1, 3], loser_id=[2, 4],
                             tourney_name="T", tourney_date=20260101)
    extra = base.iloc[[0, 0, 0, 0]].reset_index(drop=True)
    extra["score"] = ["6-4 1-6", "6-4 2-1 RET", "6-4 6-4", "6-4 6-4"]
    extra["round"] = ["R16", "QF", "F", "SF"]                 # el 3º repite el partido 0
    extra.loc[3, "w_1stWon"] = 99               # más puntos ganados que jugados
    df, inf = limpiar(pd.concat([base, extra], ignore_index=True))
    assert inf["entrada"] == 6 and inf["salida"] == 3
    assert inf["retiradas_y_wo"] == 1 and inf["sin_sets_suficientes"] == 1 and inf["duplicados"] == 1
    assert inf["stats_vaciadas_saque_incoherente_w"] == 1
    roto = df[df["round"] == "SF"].iloc[0]
    assert roto.score == "6-4 6-4" and math.isnan(roto.w_svpt)   # se conserva el marcador
