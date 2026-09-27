# Cómo poner Deuce en marcha en GitHub

Se hace una sola vez. Unos veinte o treinta minutos. Después, la web se actualiza sola cada mañana.

---

## 1. Crear la cuenta y el repositorio

1. Entra en **github.com** y crea una cuenta si no la tienes. El nombre de usuario que elijas saldrá en la dirección de la web: `tuusuario.github.io/deuce`.
2. Arriba a la derecha, pulsa **+** y luego **New repository**.
3. Nombre: **deuce**. Marca **Public**. No marques ninguna casilla más (ni README, ni .gitignore, ni licencia).
4. Pulsa **Create repository**.

## 2. Subir los archivos

1. En la página del repositorio recién creado, pulsa el enlace **uploading an existing file**.
2. Abre en tu ordenador la carpeta `deuce-github` que te he dado y **arrastra todo su contenido** (no la carpeta en sí, lo que hay dentro) a la ventana del navegador.
3. Espera a que terminen de subir. El archivo más pesado, `datos/profundo_repo.json`, ocupa unos 15 MB.
4. Abajo, pulsa **Commit changes**.

**Comprobación importante.** Los nombres que empiezan por punto se esconden en muchos ordenadores y a veces no se suben. Mira la lista de archivos del repositorio y comprueba que aparece la carpeta **`.github`**. Si no está, créala a mano:

1. Pulsa **Add file → Create new file**.
2. En el nombre escribe exactamente: `.github/workflows/nocturno.yml` (al escribir las barras, GitHub crea las carpetas solo).
3. Abre en tu ordenador el archivo `.github/workflows/nocturno.yml` del paquete con el Bloc de notas, copia todo su contenido y pégalo.
4. Pulsa **Commit changes**.

Haz lo mismo con `.gitignore` si tampoco aparece.

## 3. Activar la web

1. En el repositorio, pulsa **Settings** (arriba a la derecha).
2. En el menú de la izquierda, **Pages**.
3. En **Build and deployment → Source**, elige **GitHub Actions**.

## 4. Poner tu correo de contacto

El robot se identifica ante Tennis Abstract con tu correo, para que su autor pueda escribirte si lo necesita. El correo se guarda en un ajuste privado: no aparece en ningún archivo público.

1. En **Settings**, menú de la izquierda: **Secrets and variables → Actions**.
2. Pulsa **New repository secret**.
3. Name: `CONTACTO` · Secret: tu correo.
4. **Add secret**.

Si no lo pones, la web se actualiza igual con todo lo demás, pero no incorpora partidos nuevos con análisis profundo.

## 5. Primera ejecución

1. Pulsa la pestaña **Actions**. Si GitHub pregunta si quieres activar los flujos de trabajo, acepta.
2. En la izquierda, **Actualización nocturna**.
3. A la derecha, **Run workflow**. Marca la casilla **Repasar la lista completa de partidos anotados** (así recoge de una vez los partidos de junio a septiembre que el repositorio aún no tiene) y pulsa el botón verde.
4. Tardará entre diez minutos y media hora. Cuando termine, verás un círculo verde.
5. Pulsa sobre la ejecución y, en el recuadro **actualizar**, aparece el enlace a la web. Ya está publicada.

**Por qué hace falta esta primera ejecución con la casilla marcada.** El repositorio descargable del proyecto golpe a golpe llega hasta el 21 de mayo de 2026. Todo lo anotado después (Roland Garros entero, la hierba, el verano americano, el US Open) solo está en la web de Tennis Abstract, y el robot tiene que ir a leerlo página a página. Hasta que no lo haga, esos torneos aparecen en Deuce sin análisis profundo.

Con la casilla marcada, el robot recoge hasta 300 partidos, empezando por los más antiguos (Roland Garros primero), con doce segundos de pausa entre cada uno para no cargar la web de Tennis Abstract: algo menos de una hora. Si quedan más pendientes, los irá recogiendo las noches siguientes (60 cada noche, 150 los domingos). Los partidos que ya trae el repositorio no se vuelven a pedir.

## 6. A partir de aquí

Cada mañana, a las 8:00 en verano y a las 7:00 en invierno (hora de Murcia), el robot:

- descarga los partidos del día anterior,
- recalcula todo,
- añade los partidos anotados golpe a golpe que hayan aparecido,
- comprueba que todo cuadra,
- y publica.

**Si algo falla, no se publica nada** y la web sigue con la versión anterior. GitHub te manda un correo. Abre la ejecución en rojo, busca el paso con la cruz y cópiame el mensaje: el robot explica en castellano qué ha pasado.

GitHub puede retrasar las ejecuciones programadas unos minutos cuando está muy cargado. Es normal.

**Si un torneo reciente sale sin análisis profundo** aunque en Tennis Abstract esté anotado, casi siempre es una de estas dos cosas: que falte el secreto `CONTACTO` (el robot no lee páginas sin él, y lo dice en el registro de la ejecución), o que aún queden partidos pendientes de la puesta al día. Lanzar a mano una ejecución con la casilla marcada lo resuelve.

---

## Qué hay en el paquete

| Carpeta | Contenido |
|---|---|
| `src/` | El robot: descargas, limpieza, las 55 medidas, el análisis profundo y la construcción de la web |
| `plantilla/` | El diseño de la web |
| `datos/historico.parquet` | Los partidos del circuito principal desde 1991 hasta 2025 |
| `datos/tml/` | La temporada en curso, que el robot actualiza cada mañana |
| `datos/profundo_repo.json` | Los 6.578 análisis golpe a golpe del repositorio del proyecto |
| `datos/mcp_paginas/` | Los partidos anotados que el robot va leyendo de la web |
| `.github/workflows/` | La orden que le dice a GitHub cuándo ejecutar el robot |

La web en sí (`web/`) no está en el paquete: el robot la construye cada noche.
