"""
Página de partido inventada con el mismo esqueleto que las de
tennisabstract.com/charting/: un título, el resultado en negrita y una
variable JavaScript con una tabla HTML por bloque de estadísticas.
Las cifras son pequeñas y redondas para poder comprobarlas a mano.
"""


def tabla(*filas):
    return "<table>" + "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas) + "</table>"


def var(nombre, contenido):
    return f"var {nombre} = '{contenido}';\n"


# registro punto a punto: quién saca, sets, juegos, puntos, descripción
PUNTOS = [
    ("Ana Uno", "0-0", "0-0", "0-0", "1st serve wide, ace."),
    ("Ana Uno", "0-0", "0-0", "15-0", "1st serve down the T; forehand return, forced error."),
    ("Ana Uno", "0-0", "0-0", "30-0", "1st serve to body; backhand return; forehand crosscourt, winner."),
    ("Ana Uno", "0-0", "0-0", "40-0", "2nd serve wide; forehand return; backhand down the line, unforced error."),
    ("Ana Uno", "0-0", "0-0", "40-15", "1st serve wide; forehand return, unforced error."),
    # el registro cuenta desde quien saca: "0-1" es 1-0 para Ana
    ("Bea Dos", "0-0", "0-1", "0-0", "1st serve down the T; backhand return, winner."),
    ("Bea Dos", "0-0", "0-1", "0-15", "2nd serve wide, double fault."),
]


def pagina():
    j = ""
    j += var("rallyoutcomes", tabla(
        ["Rally", "Pts", "AU: W", "BD: W"],
        ["All: 1-3 Shots", "6", "5", "1"],
        ["All: 4-6 Shots", "1", "0", "1"],
    ))
    j += var("overview", tabla(
        ["PLAYER", "Winners", "UFE", "Other"],
        ["Ana Uno", "10 (6/4)", "5 (3/2)", "-"],
        ["Bea Dos", "7 (2/5)", "12 (8/4)", "-"],
    ))
    j += var("keypoints", tabla(
        ["KEY", "Pts", "Won", "%"],
        ["AU BP Faced", "4", "3", "75%"],
        ["BD BP Faced", "0", "0", ""],
    ))
    j += var("serveNeut", tabla(
        ["SN", "1+", "3+", "5+"],
        ["AU 1st Serve", "70%", "60%", "55%"],
        ["BD 1st Serve", "60%", "", ""],
    ))
    for k, (dp, ap, dw, aw) in ((1, (30, 30, 20, 18)), (2, (25, 25, 14, 12))):
        j += var(f"serve{k}", tabla(
            ["SERVE", "Pts", "Won", "1stIn"],
            ["Deuce Court", dp, dw, "18"],
            ["Ad Court", ap, aw, "17"],
            ["Deuce-Wide", "", "", "5"],
            ["Deuce-Body", "", "", "2"],
            ["Deuce-T", "", "", "3"],
            ["Ad-Wide", "", "", "4"],
            ["Ad-Body", "", "", "1"],
            ["Ad-T", "", "", "5"],
        ))
    j += var("return1", tabla(
        ["RETURN", "Pts", "Returnable", "inPlay"],
        ["Total", "50", "40", "30"],
        ["Svc Box", "10", "", ""],
        ["Beh Svc Ln", "20", "", ""],
    ))
    j += var("return2", tabla(
        ["RETURN", "Pts", "Returnable", "inPlay"],
        ["Total", "60", "45", "35"],
    ))
    j += var("netpts1", tabla(
        ["NET", "Pts", "Won", "Wnr at Net", "Passed at Net"],
        ["All Net Points", "12", "8", "5", "2"],
        ["Serve-and-Volley", "3", "2", "1", "0"],
    ))
    j += var("netpts2", tabla(["NET", "Pts", "Won", "Wnr at Net", "Passed at Net"]))
    j += var("shotdir1", tabla(["DIR", "Crosscourt", "Middle", "Down line", "Inside-out", "Inside-in"],
                               ["Total", "40", "20", "10", "20", "10"]))
    j += var("shotdir2", tabla(["DIR", "Crosscourt", "Middle", "Down line", "Inside-out", "Inside-in"],
                               ["Total", "0", "0", "0", "0", "0"]))
    j += var("pointlog", tabla(["Server", "Sets", "Gms", "Pts", "Description"], *PUNTOS))
    return ("<html><head><title>2026 Test Open F: Ana Uno vs Bea Dos Detailed Stats</title></head><body>"
            "<b>Ana Uno d. Bea Dos 6-4 7-6(5)</b><script>\n" + j + "</script></body></html>")
