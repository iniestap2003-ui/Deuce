"""
CÁLCULO COMPLETO · todas las temporadas del circuito principal
==============================================================
Entrada:
    datos/historico.parquet   partidos del circuito principal hasta la temporada anterior
    datos/tml/AAAA.csv        temporadas de TennisMyLife (fuente diaria)
Salida:
    datos/calculado.parquet   un partido por fila, con todas las medidas
    datos/constantes.json     referencias del circuito usadas en las medidas
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from limpieza import limpiar, juegos_totales
from metricas import construir_todo

D = Path(__file__).resolve().parent.parent / "datos"
lim = lambda s: s.replace([np.inf, -np.inf], np.nan)


def temporada(fecha):
    """Los torneos que empiezan a partir del 20 de diciembre son de la temporada siguiente
    (Brisbane, Adelaida o la United Cup arrancan a menudo el 29, 30 o 31 de diciembre)."""
    return fecha.dt.year + ((fecha.dt.month == 12) & (fecha.dt.day >= 20)).astype(int)


def cargar():
    """Histórico congelado + todas las temporadas descargadas de TennisMyLife (datos/tml/AAAA.csv).
    Para cada temporada que exista en TennisMyLife, manda TennisMyLife."""
    h = pd.read_parquet(D / "historico.parquet")
    ficheros = sorted((D / "tml").glob("[0-9][0-9][0-9][0-9].csv"))
    t = pd.concat([pd.read_csv(f, low_memory=False) for f in ficheros], ignore_index=True)
    fh = pd.to_datetime(h.tourney_date.astype(str).str[:8], format="%Y%m%d")
    ft = pd.to_datetime(t.tourney_date.astype(str).str[:8], format="%Y%m%d")
    primera_tml = int(temporada(ft).min())
    h = h[temporada(fh) < primera_tml]
    comunes = [c for c in t.columns if c in h.columns]
    return pd.concat([h[comunes], t], ignore_index=True), int(temporada(ft).max())


def calcular():
    bruto, anio_actual = cargar()
    d, informe = limpiar(bruto)
    d["fecha"] = pd.to_datetime(d.tourney_date.astype(str).str[:8], format="%Y%m%d")
    d["anio"] = temporada(d.fecha)
    d["_juegos_marcador"] = d.score.apply(juegos_totales)
    d = construir_todo(d)

    # ---- disputa: puntos por juego, contados sobre los juegos del marcador
    d["juegos"] = d["_juegos_marcador"]
    d["ppj"] = d.pts_total / d.juegos
    d.loc[~d.ppj.between(3.9, 12), "ppj"] = np.nan
    d["disputa"] = (100 * (d.ppj - 4) / 5).clip(0, 100)

    # ---- referencias del circuito (todas las temporadas)
    sv = lim(pd.concat([d.pct_pts_saque_w, d.pct_pts_saque_l])).dropna(); sv = sv[sv.between(.3, .95)]
    rs = lim(pd.concat([d.pct_pts_resto_w, d.pct_pts_resto_l])).dropna(); rs = rs[rs.between(.05, .7)]
    K = {"msv": sv.mean(), "ssv": sv.std(), "mre": rs.mean(), "sre": rs.std(),
         "tasa_bp": (d.w_bpSaved.sum() + d.l_bpSaved.sum()) / (d.w_bpFaced.sum() + d.l_bpFaced.sum()),
         "med_tension": float(d.tension.median()), "med_disputa": float(d.disputa.median())}
    d["asim2"] = ((lim(d.pct_pts_saque_w) - K["msv"]) / K["ssv"]) - ((lim(d.pct_pts_resto_w) - K["mre"]) / K["sre"])
    d["escape2"] = d.w_bpSaved - d.w_bpFaced * K["tasa_bp"]
    mt, md = K["med_tension"], K["med_disputa"]
    d["tipo"] = np.select([(d.tension >= mt) & (d.disputa >= md), (d.tension >= mt) & (d.disputa < md),
                           (d.tension < mt) & (d.disputa >= md)],
                          ["PULSO", "DUELO DE SAQUES", "MARCADOR ENGANOSO"], default="SIN HISTORIA")
    d.loc[d.disputa.isna() | d.tension.isna(), "tipo"] = "SIN DATOS"

    # ---- racha de desgaste: carga del ganador en los 7 días previos
    lg = pd.concat([d[["fecha", "winner_name", "desgaste"]].rename(columns={"winner_name": "j"}),
                    d[["fecha", "loser_name", "desgaste"]].rename(columns={"loser_name": "j"})]).sort_values("fecha")
    rr = (lg.set_index("fecha").groupby("j")["desgaste"].rolling("7D").sum().reset_index()
            .groupby(["fecha", "j"], as_index=False)["desgaste"].max().rename(columns={"desgaste": "rc"}))
    d = d.merge(rr.rename(columns={"j": "winner_name"}), on=["fecha", "winner_name"], how="left")

    # ---- rivalidad: todos los cruces del circuito principal
    d["par"] = [" vs ".join(sorted([a, b])) for a, b in zip(d.winner_name, d.loser_name)]
    riv = d.groupby("par").agg(rivn=("tension", "size"), rivt=("tension", "mean"))
    d = d.merge(riv, left_on="par", right_index=True, how="left")

    # ---- récords personales DE CADA TEMPORADA
    for col, nom in (("tension", "rec_t"), ("espectaculo", "rec_e")):
        x = pd.concat([d[["anio", "winner_name", col]].rename(columns={"winner_name": "j"}),
                       d[["anio", "loser_name", col]].rename(columns={"loser_name": "j"})])
        mx = x.groupby(["anio", "j"])[col].max()
        d[nom] = [int(pd.notna(v) and abs(v - mx.get((a, w), -9)) < 1e-9) for a, w, v in zip(d.anio, d.winner_name, d[col])]

    d = d.sort_values(["fecha", "tourney_name", "match_num"]).reset_index(drop=True)
    # las dos fuentes usan identificadores distintos (números y códigos): todo lo
    # que cruza jugadores entre temporadas se hace por NOMBRE, y los ids se guardan como texto
    for c in d.columns:
        if d[c].dtype == object:
            d[c] = d[c].where(d[c].isna(), d[c].astype(str))
    d.to_parquet(D / "calculado.parquet", index=False)
    json.dump({k: float(v) for k, v in K.items()} | {"anio_actual": anio_actual}, open(D / "constantes.json", "w"), indent=1)
    return d, informe, K


if __name__ == "__main__":
    d, inf, K = calcular()
    print("limpieza:", inf)
    print(f"partidos: {len(d):,} · temporadas {d.anio.min()}-{d.anio.max()}")
