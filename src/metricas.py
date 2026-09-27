"""
MÉTRICAS DE PARTIDO
===================

Todo lo que se puede extraer de un partido a partir de dos cosas:
el MARCADOR (texto, ej. "6-4 3-6 7-6(5)") y las ESTADÍSTICAS de saque.

Organizado en cuatro familias:
    A · ESTRUCTURA   qué forma tuvo el partido        (solo del marcador)
    B · RENDIMIENTO  cómo jugó cada uno               (de las estadísticas)
    C · ORIGINALES   métricas propias que combinan    (lo que nadie publica)
    D · CONTEXTO     qué significó el resultado       (ranking, torneo)

Convención: en este dataset el PRIMER número de cada set es siempre del
ganador del partido. Todas las métricas "_g" son del ganador y "_p" del perdedor.
"""

import re
import numpy as np
import pandas as pd


# ==========================================================================
# PARSEO DEL MARCADOR
# ==========================================================================

from limpieza import sets_del_marcador


def parsear(score):
    """Un solo lector de marcadores en todo el proyecto: el de limpieza.py.
    Devuelve [(juegos_g, juegos_p, puntos_del_perdedor_en_el_tiebreak | None)]."""
    s = sets_del_marcador(score)
    if not s:
        return None
    tb = {}
    for trozo in str(score).split():
        m = re.fullmatch(r"(\d{1,2})-(\d{1,2})\((\d+)\)", trozo)
        if m:
            tb[(int(m.group(1)), int(m.group(2)))] = int(m.group(3))
    return [(a, b, tb.get((a, b))) for a, b in s]


# ==========================================================================
# A · ESTRUCTURA DEL PARTIDO  (solo necesita el marcador)
# ==========================================================================

def estructura(score):
    s = parsear(score)
    if not s:
        return {}

    jg = sum(x[0] for x in s)          # juegos del ganador
    jp = sum(x[1] for x in s)          # juegos del perdedor
    n = len(s)
    difs = [x[0] - x[1] for x in s]

    # --- tiebreaks ---
    tb_jug = [x for x in s if x[2] is not None or {x[0], x[1]} == {7, 6}]
    tb_gan = sum(1 for x in tb_jug if x[0] > x[1])
    # margen del tiebreak: 7 menos los puntos del perdedor (más alto = más cómodo)
    margenes_tb = [7 - x[2] for x in s if x[2] is not None and x[0] > x[1]]

    # --- roscos y sets en blanco ---
    roscos_dados = sum(1 for x in s if x[1] == 0)
    roscos_recibidos = sum(1 for x in s if x[0] == 0)

    # --- TENSIÓN: 0 = paliza, 100 = todo al límite ---
    # cada set aporta según lo cerca que estuvo; un 6-4 aporta más que un 6-1
    cercania = [max(0.0, 1 - abs(d) / 6) for d in difs]
    tension = 100 * float(np.mean(cercania))
    if n == max(3, n) and n in (3, 5):     # llegó al set decisivo
        tension = min(100.0, tension * 1.15)

    # --- VOLATILIDAD: ¿fue un partido estable o de vaivenes? ---
    # 6-4 6-4 es estable; 6-1 1-6 6-1 es volátil aunque el margen sea igual
    volatilidad = float(np.std(difs)) if n > 1 else 0.0

    # --- TRAYECTORIA: ¿fue a más o a menos? ---
    # pendiente de la diferencia de juegos set a set
    trayectoria = float(np.polyfit(range(n), difs, 1)[0]) if n > 1 else 0.0

    return {
        "juegos_g": jg, "juegos_p": jp, "margen_juegos": jg - jp,
        "n_sets": n,
        "gano_1er_set": int(difs[0] > 0),
        "vuelco": int(difs[0] < 0),                    # perdió el 1º y ganó
        "set_decisivo": int(n in (3, 5) and n > 2),
        "sets_ajustados": sum(1 for d in difs if abs(d) <= 2),
        "sets_paliza": sum(1 for d in difs if abs(d) >= 4),
        "tiebreaks": len(tb_jug), "tiebreaks_ganados": tb_gan,
        "margen_tb_medio": float(np.mean(margenes_tb)) if margenes_tb else np.nan,
        "roscos_dados": roscos_dados, "roscos_recibidos": roscos_recibidos,
        "tension": round(tension, 1),
        "volatilidad": round(volatilidad, 2),
        "trayectoria": round(trayectoria, 2),
    }


# ==========================================================================
# B · RENDIMIENTO  (estadísticas de saque y resto)
# ==========================================================================

def rendimiento(d):
    """d es el dataframe completo. Devuelve columnas nuevas."""
    o = pd.DataFrame(index=d.index)

    for lado, otro in [("w", "l"), ("l", "w")]:
        sv = d[f"{lado}_svpt"]          # puntos jugados al saque
        p1 = d[f"{lado}_1stIn"]         # primeros servicios dentro
        g1 = d[f"{lado}_1stWon"]        # puntos ganados con el primero
        g2 = d[f"{lado}_2ndWon"]        # puntos ganados con el segundo
        gm = d[f"{lado}_SvGms"].replace(0, np.nan)   # juegos al saque
        # en algunos torneos esta columna viene a cero para todo el cuadro;
        # entonces se estima desde el marcador (cada uno sirve ~la mitad)
        if "_juegos_marcador" in d.columns:
            gm = gm.fillna(d["_juegos_marcador"] / 2)
        bs = d[f"{lado}_bpSaved"]       # bolas de break salvadas
        bf = d[f"{lado}_bpFaced"]       # bolas de break afrontadas

        o[f"pct_1er_dentro_{lado}"] = p1 / sv
        o[f"pct_gana_1er_{lado}"] = g1 / p1
        o[f"pct_gana_2o_{lado}"] = g2 / (sv - p1)
        o[f"pct_pts_saque_{lado}"] = (g1 + g2) / sv
        o[f"ace_rate_{lado}"] = d[f"{lado}_ace"] / sv
        o[f"df_rate_{lado}"] = d[f"{lado}_df"] / sv
        o[f"ace_df_ratio_{lado}"] = d[f"{lado}_ace"] / d[f"{lado}_df"].replace(0, np.nan)
        o[f"pct_bp_salvadas_{lado}"] = bs / bf.replace(0, np.nan)
        o[f"presion_recibida_{lado}"] = bf / gm          # bolas de break por juego
        o[f"pts_por_juego_saque_{lado}"] = sv / gm

    # resto: lo que uno gana al resto es lo que el otro cede con su saque
    o["pct_pts_resto_w"] = 1 - o["pct_pts_saque_l"]
    o["pct_pts_resto_l"] = 1 - o["pct_pts_saque_w"]

    # bolas de break generadas y convertidas
    o["bp_generadas_w"] = d["l_bpFaced"]
    o["bp_convertidas_w"] = d["l_bpFaced"] - d["l_bpSaved"]
    o["pct_bp_convertidas_w"] = o["bp_convertidas_w"] / o["bp_generadas_w"].replace(0, np.nan)
    o["bp_generadas_l"] = d["w_bpFaced"]
    o["bp_convertidas_l"] = d["w_bpFaced"] - d["w_bpSaved"]
    o["pct_bp_convertidas_l"] = o["bp_convertidas_l"] / o["bp_generadas_l"].replace(0, np.nan)

    # puntos totales del partido
    o["pts_g"] = (d["w_1stWon"] + d["w_2ndWon"]) + (d["l_svpt"] - d["l_1stWon"] - d["l_2ndWon"])
    o["pts_p"] = (d["l_1stWon"] + d["l_2ndWon"]) + (d["w_svpt"] - d["w_1stWon"] - d["w_2ndWon"])
    o["pts_total"] = o["pts_g"] + o["pts_p"]
    o["pct_pts_g"] = o["pts_g"] / o["pts_total"]

    # ritmo
    o["min_por_punto"] = d["minutes"] / o["pts_total"]
    o["pts_por_minuto"] = o["pts_total"] / d["minutes"]

    return o


# ==========================================================================
# C · MÉTRICAS ORIGINALES  (lo que no publica nadie)
# ==========================================================================

def originales(d, e, r):
    """d=datos crudos, e=estructura, r=rendimiento."""
    o = pd.DataFrame(index=d.index)

    # --- 1. ROBO: ganar el partido con menos puntos que el rival ---
    o["robo"] = (r["pct_pts_g"] < 0.5).astype(float)
    o.loc[r["pct_pts_g"].isna(), "robo"] = np.nan
    o["margen_robo"] = 0.5 - r["pct_pts_g"]

    # --- 2. DOMINACIÓN: % que ganas al resto / % que cedes al saque ---
    #     >1 = mandas tú. Es el mejor resumen de un partido en un solo número.
    # si alguien no cede ni un punto con su saque, el cociente no existe: queda vacío, no infinito
    o["dominacion_g"] = r["pct_pts_resto_w"] / (1 - r["pct_pts_saque_w"]).replace(0, np.nan)
    o["dominacion_p"] = r["pct_pts_resto_l"] / (1 - r["pct_pts_saque_l"]).replace(0, np.nan)

    # --- 3. EFICIENCIA: convertir puntos en juegos ---
    #     Ganar el 52% de los puntos y el 60% de los juegos = distribuyes bien.
    pct_juegos = e["juegos_g"] / (e["juegos_g"] + e["juegos_p"])
    o["eficiencia_g"] = pct_juegos - r["pct_pts_g"]

    # --- 4. DESPERDICIO: bolas de break generadas y no aprovechadas ---
    o["desperdicio_g"] = r["bp_generadas_w"] - r["bp_convertidas_w"]
    o["tasa_desperdicio_g"] = 1 - r["pct_bp_convertidas_w"]

    # --- 5. ÍNDICE DE ESCAPE: salvar bolas de break bajo presión ---
    #     pondera las salvadas por la presión total recibida
    o["escape_g"] = r["pct_bp_salvadas_w"] * np.log1p(d["w_bpFaced"])

    # --- 6. ASIMETRÍA: ¿ganaste por tu saque o por tu resto? ---
    #     positivo = ganaste sacando; negativo = ganaste restando
    o["asimetria_g"] = (r["pct_pts_saque_w"] - 0.64) - (r["pct_pts_resto_w"] - 0.36)

    # --- 7. PUNTOS IMPORTANTES GANADOS (proxy de temple) ---
    #     bolas de break salvadas + convertidas + tiebreaks ganados
    o["pts_clave_g"] = d["w_bpSaved"] + r["bp_convertidas_w"] + e["tiebreaks_ganados"]
    o["pts_clave_total"] = d["w_bpFaced"] + r["bp_generadas_w"] + e["tiebreaks"]
    o["pct_clave_g"] = o["pts_clave_g"] / o["pts_clave_total"].replace(0, np.nan)

    # --- 8. RESILIENCIA: ganar el set siguiente a uno perdido ---
    o["resiliencia_g"] = e["vuelco"]

    # --- 9. ÍNDICE DE PALIZA: cómo de contundente fue ---
    o["paliza"] = (e["roscos_dados"] * 2 + e["sets_paliza"]) / e["n_sets"]

    # --- 10. PARTIDO DE SAQUES: pocos breaks por ambos lados ---
    breaks_totales = r["bp_convertidas_w"] + r["bp_convertidas_l"]
    juegos = d["_juegos_marcador"] if "_juegos_marcador" in d.columns else (d["w_SvGms"] + d["l_SvGms"])
    o["indice_saques"] = 1 - breaks_totales / juegos.replace(0, np.nan)

    # --- 11. DESGASTE: puntos jugados ponderados por duración ---
    o["desgaste"] = r["pts_total"] * np.sqrt(d["minutes"].fillna(0) / 90)

    # --- 12. CALIDAD DEL PARTIDO: buen tenis por ambos lados ---
    #     alta si los dos sacaron bien Y hubo tensión
    o["calidad"] = (r["pct_pts_saque_w"] + r["pct_pts_saque_l"]) / 2 * e["tension"]

    return o


# ==========================================================================
# D · CONTEXTO  (qué significó el resultado)
# ==========================================================================

def contexto(d, e):
    o = pd.DataFrame(index=d.index)

    rw, rl = d["winner_rank"], d["loser_rank"]

    # --- SORPRESA: ganó el peor clasificado, y por cuánto ---
    o["es_sorpresa"] = (rw > rl).astype(float)
    #   magnitud logarítmica: ganar del 100 al 1 pesa más que del 60 al 50
    o["magnitud_sorpresa"] = np.log(rw / rl).clip(lower=0)

    # --- IMPORTANCIA DEL PARTIDO ---
    peso_nivel = d["tourney_level"].map({"G": 4, "F": 3.5, "M": 3, "A": 2, "D": 2, "C": 1}).fillna(1)
    peso_ronda = d["round"].map({"F": 3, "SF": 2.5, "QF": 2, "R16": 1.5}).fillna(1)
    o["importancia"] = peso_nivel * peso_ronda

    # --- ESPECTÁCULO: importancia x tensión ---
    o["espectaculo"] = o["importancia"] * e["tension"] / 100

    return o


# ==========================================================================
# ENSAMBLADO
# ==========================================================================

def construir_todo(d: pd.DataFrame) -> pd.DataFrame:
    e = d["score"].apply(estructura).apply(pd.Series)
    r = rendimiento(d)
    o = originales(d, e, r)
    c = contexto(d, e)
    return pd.concat([d, e, r, o, c], axis=1)
