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

### Comprobar los dos archivos que empiezan por punto

Hay dos archivos cuyo nombre empieza por un punto: la carpeta **`.github`** y el archivo **`.gitignore`**. Muchos ordenadores esconden ese tipo de archivos, así que a veces no se suben al arrastrar. Hay que comprobarlo.

Mira la lista de archivos del repositorio en GitHub, arriba del todo, junto a `README.md` y `GUIA.md`.

**Si ves `.github` y `.gitignore` en la lista**, no tienes que hacer nada: pasa al punto 3.

**Si falta `.github`**, créalo a mano. Es imprescindible: es la orden que le dice a GitHub que ejecute el robot cada mañana.

1. Pulsa el botón **Add file** y elige **Create new file**.
2. En la casilla del nombre, arriba, escribe exactamente `.github/workflows/nocturno.yml`. Al escribir cada barra, GitHub convierte lo anterior en una carpeta: es normal que el texto se mueva.
3. En el cuadro grande de abajo, pega **todo** este texto, tal cual, respetando los espacios del principio de cada línea:

```yaml
name: Actualización nocturna

on:
  schedule:
    - cron: "0 6 * * *"      # 06:00 UTC · 08:00 en Murcia en verano, 07:00 en invierno
  workflow_dispatch:           # botón para lanzarlo a mano

permissions:
  contents: write              # guardar los datos nuevos en el repositorio
  pages: write                 # publicar la web
  id-token: write

concurrency:
  group: deuce
  cancel-in-progress: false

jobs:
  actualizar:
    runs-on: ubuntu-latest
    timeout-minutes: 150
    environment:
      name: github-pages
      url: ${{ steps.publicar.outputs.page_url }}
    steps:
      - name: Descargar el proyecto
        uses: actions/checkout@v6

      - name: Preparar Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Instalar librerías
        run: pip install pandas pyarrow numpy

      - name: Descargar, calcular y construir
        env:
          CONTACTO: ${{ secrets.CONTACTO }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python src/nocturno.py

      - name: Guardar los datos nuevos
        run: |
          git config user.name "deuce-robot"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add datos/tml datos/estado.json datos/profundo_repo.json
          [ -d datos/mcp_paginas ] && git add datos/mcp_paginas
          [ -f datos/mcp_sha.txt ] && git add datos/mcp_sha.txt
          git diff --cached --quiet || git commit -m "Datos del $(date -u +%F)"
          git push

      - name: Preparar la publicación
        uses: actions/configure-pages@v5

      - name: Empaquetar la web
        uses: actions/upload-pages-artifact@v5
        with:
          path: web

      - name: Publicar
        id: publicar
        uses: actions/deploy-pages@v4
```

4. Pulsa el botón verde **Commit changes…**. En la ventana que se abre, deja marcada la opción **Commit directly to the main branch** y pulsa otra vez **Commit changes**.

**Si falta `.gitignore`**, créalo igual. No es imprescindible, porque el robot ya sabe qué guardar y qué no, pero es una red de seguridad: le dice a GitHub que nunca guarde en el repositorio los archivos pesados que se fabrican cada noche.

1. Vuelve a la página principal del repositorio pulsando su nombre, **deuce**, arriba a la izquierda.
2. Pulsa **Add file** y elige **Create new file**.
3. En la casilla del nombre escribe exactamente `.gitignore`: con el punto delante, sin nada detrás.
4. En el cuadro grande, pega este texto:

```
# se generan cada noche, no se guardan
web/
datos/mcp/
datos/calculado.parquet
datos/profundo.json
datos/constantes.json
__pycache__/
```

5. Pulsa **Commit changes…** y, en la ventana, otra vez **Commit changes**.

Al terminar, vuelve a la página principal del repositorio y comprueba que ya aparecen los dos.

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
3. A la derecha, **Run workflow** y luego el botón verde **Run workflow**.
4. Tardará en torno a una hora la primera vez. Cuando termine, verás un círculo verde.
5. Pulsa sobre la ejecución y, en el recuadro **actualizar**, aparece el enlace a la web. Ya está publicada.

**Qué hace esta primera vez.** El repositorio descargable del proyecto golpe a golpe llega hasta el 21 de mayo de 2026. Todo lo anotado después (Roland Garros, la hierba, el verano americano, el US Open), y también los partidos antiguos que los voluntarios han anotado últimamente, solo está en la web de Tennis Abstract. El robot mira su lista completa, se queda con **todos los partidos masculinos que estén en nuestro archivo y aún no tengamos**, y los baja empezando por la temporada en curso, con cinco segundos de pausa entre cada uno.

Baja como mucho 600 por ejecución. Si al final del registro pone «quedan N para la próxima ejecución», puedes esperar a la mañana siguiente o pulsar otra vez **Run workflow** para acelerar. Cuando ponga «al día», ya los tienes todos. A partir de ahí, cada mañana solo baja los pocos que se hayan anotado el día anterior.

## 6. A partir de aquí

Cada mañana, a las 8:00 en verano y a las 7:00 en invierno (hora de Murcia), el robot:

- descarga los partidos del día anterior,
- recalcula todo,
- añade los partidos anotados golpe a golpe que hayan aparecido,
- comprueba que todo cuadra,
- y publica.

**Si algo falla, no se publica nada** y la web sigue con la versión anterior. GitHub te manda un correo. Abre la ejecución en rojo, busca el paso con la cruz y cópiame el mensaje: el robot explica en castellano qué ha pasado.

GitHub puede retrasar las ejecuciones programadas unos minutos cuando está muy cargado. Es normal.

**Si un partido sale sin análisis profundo** aunque en Tennis Abstract esté anotado, casi siempre es una de estas cosas: que falte el secreto `CONTACTO` (el robot no lee páginas sin él, y lo dice en el registro), que aún queden partidos pendientes de la puesta al día (el registro dice «quedan N»), o que el partido se haya anotado solo en parte, en cuyo caso no pasa el control de calidad y no entra. Pulsar **Run workflow** resuelve las dos primeras.

---

## 7. Cómo subir cambios de diseño o de cálculo

Cuando me pidas cambios en la web, te daré un paquete pequeño llamado `cambios.zip` con solo los archivos que hayan cambiado, ya dentro de sus carpetas.

1. Descomprime `cambios.zip` en tu ordenador.
2. En la página principal de tu repositorio, pulsa **Add file → Upload files**.
3. Arrastra **las carpetas** que haya dentro (por ejemplo `plantilla` o `src`). GitHub sustituye los archivos que tengan el mismo nombre en la misma carpeta y deja el resto como estaba.
4. Pulsa **Commit changes**.
5. Si quieres verlo publicado ya, ve a **Actions → Actualización nocturna → Run workflow**. Si no, se publicará solo a la mañana siguiente.

Antes de cada paquete verás el cambio aquí, en la vista previa de Claude, para que lo apruebes.

## 8. ¿Quién puede ver la web?

Cualquiera que tenga el enlace `tuusuario.github.io/deuce`, desde cualquier ordenador o móvil, sin cuenta de GitHub ni nada que instalar. Todo lo de esta guía es solo para ti y solo una vez. Tu repositorio (`github.com/tuusuario/deuce`) es la cocina; la web es lo que ven los demás.

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
