"""
LIMPIEZA Y COHERENCIA
=====================
Reglas duras que todo partido cumple antes de entrar en Deuce. Cada descarte
queda contabilizado: un proceso que tira filas en silencio no es de fiar.
"""
import re
import numpy as np
import pandas as pd

PATRON_INCOMPLETO = r"W/O|RET|DEF|Walkover|ABN|Def\.|unfinished|\?"


def sets_del_marcador(score):
    """
    '6-4 3-6 7-6(5)'    -> [(6,4),(3,6),(7,6)]
    '6-3 6-7(4) [10-6]' -> [(6,3),(6,7),(1,0)]

    Los corchetes son el super tiebreak que sustituye al tercer set (Copa Davis,
    algunas exhibiciones): se juega a 10 puntos y vale UN juego. Contarlo como
    diez juegos hunde los puntos por juego por debajo del mínimo físico.
    """
    if not isinstance(score, str):
        return []
    out = []
    for trozo in score.split():
        stb = re.fullmatch(r"\[(\d{1,2})-(\d{1,2})\]", trozo)
        if stb:
            a, b = int(stb.group(1)), int(stb.group(2))
            out.append((1, 0) if a > b else (0, 1))
            continue
        m = re.fullmatch(r"(\d{1,2})-(\d{1,2})(?:\(\d+\))?", trozo)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return out


def victoria_completa(score, best_of):
    s = sets_del_marcador(score)
    if not s:
        return False
    return sum(1 for a, b in s if a > b) >= (3 if best_of == 5 else 2)


def juegos_totales(score):
    """Juegos jugados, contados del marcador (no de SvGms, que a veces viene a cero)."""
    s = sets_del_marcador(score)
    return sum(a + b for a, b in s) if s else np.nan


def limpiar(df):
    inf = {"entrada": len(df)}

    def paso(nombre, mascara):
        nonlocal df
        antes = len(df)
        df = df[mascara]
        inf[nombre] = antes - len(df)

    paso("sin_marcador", df.score.notna() & df.best_of.notna())
    paso("retiradas_y_wo", ~df.score.astype(str).str.contains(PATRON_INCOMPLETO, case=False, na=False, regex=True))
    paso("sin_sets_suficientes", pd.Series([victoria_completa(s, b) for s, b in zip(df.score, df.best_of)], index=df.index))
    paso("sin_datos_clave", df.surface.notna() & df.winner_id.notna() & df.loser_id.notna())
    paso("mismo_jugador", df.winner_id != df.loser_id)
    # --- estadísticas rotas: el partido existió y su marcador vale, así que NO se
    #     descarta; se vacían solo sus estadísticas y se conserva lo que sale del marcador
    ST = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced"]
    malo = pd.Series(False, index=df.index)
    motivos = {}
    for L in ("w", "l"):
        sv, p1, g1, g2 = df[f"{L}_svpt"], df[f"{L}_1stIn"], df[f"{L}_1stWon"], df[f"{L}_2ndWon"]
        m = ((sv.notna() & (sv <= 0)) | (p1 > sv) | (g1 > p1) | (g2 > (sv - p1)) | (g1 + g2 > sv)).fillna(False)
        motivos[f"saque_incoherente_{L}"] = m
        motivos[f"break_incoherente_{L}"] = (df[f"{L}_bpSaved"] > df[f"{L}_bpFaced"]).fillna(False)
    motivos["cifras_negativas"] = pd.concat([(df[f"{L}_{c}"] < 0) for L in "wl" for c in ST], axis=1).any(axis=1)
    # cada juego tiene al menos cuatro puntos: menos puntos servidos que eso es imposible
    juegos = df.score.apply(juegos_totales)
    motivos["menos_de_4_puntos_por_juego"] = ((df.w_svpt + df.l_svpt) < 4 * juegos).fillna(False)
    for k, m in motivos.items():
        inf["stats_vaciadas_" + k] = int((m & ~malo).sum())
        malo |= m
    df = df.copy()
    df.loc[malo, [f"{L}_{c}" for L in "wl" for c in ST]] = np.nan
    inf["stats_vaciadas_total"] = int(malo.sum())

    antes = len(df)
    df = df.drop_duplicates(subset=["tourney_name", "tourney_date", "winner_id", "loser_id", "score"])
    inf["duplicados"] = antes - len(df)
    inf["salida"] = len(df)
    return df.reset_index(drop=True), inf
