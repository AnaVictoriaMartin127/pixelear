#!/usr/bin/env python3
"""
convertidorPixi.py — convierte una imagen en una cuadrícula de bloques de color sólido.

Ejemplos
--------
  # 32 bloques de ancho (las filas se calculan para mantener la proporción)
  python3 convertidorPixi.py foto.jpg -w 32

  # cuadrícula exacta: 40 x 25 bloques
  python3 convertidorPixi.py foto.jpg -w 40 -H 25

  # más o menos 1000 bloques en total, manteniendo la proporción
  python3 convertidorPixi.py foto.jpg -n 1000

  # además limitar a 8 colores, cada bloque de 20 px, con líneas de rejilla
  python3 convertidorPixi.py foto.jpg -w 32 -c 8 -s 20 --rejilla

  # exportar los colores de los bloques a CSV (fila, columna, r, g, b, hex)
  python3 convertidorPixi.py foto.jpg -w 32 --csv colores.csv

Requiere: pip install pillow numpy
"""
import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def cuantos_cuadritos_caben(ancho_del_recuerdo, alto_del_recuerdo,
                            columnas_que_imagino=None, filas_que_imagino=None,
                            todos_los_pedacitos=None):
    """Calcula (columnas, filas) a partir de lo que se haya pedido."""
    forma_de_la_ventana = ancho_del_recuerdo / alto_del_recuerdo
    if todos_los_pedacitos:
        columnas_que_imagino = max(1, round(math.sqrt(todos_los_pedacitos * forma_de_la_ventana)))
        filas_que_imagino = max(1, round(todos_los_pedacitos / columnas_que_imagino))
    elif columnas_que_imagino and not filas_que_imagino:
        filas_que_imagino = max(1, round(columnas_que_imagino / forma_de_la_ventana))
    elif filas_que_imagino and not columnas_que_imagino:
        columnas_que_imagino = max(1, round(filas_que_imagino * forma_de_la_ventana))
    elif not columnas_que_imagino and not filas_que_imagino:
        raise ValueError("Indica --columnas, --filas o --total")
    return columnas_que_imagino, filas_que_imagino


def derretir_la_memoria(la_foto_que_no_borro, columnas_que_imagino, filas_que_imagino,
                        colores_que_me_quedan=None, manera_de_recordar="media"):
    """Devuelve un arreglo uint8 (filas, columnas, 3): un color RGB por bloque."""
    la_foto_que_no_borro = la_foto_que_no_borro.convert("RGB")
    if manera_de_recordar == "media":
        # El remuestreo BOX promedia todos los píxeles que caen en cada bloque
        recuerdo_chiquito = la_foto_que_no_borro.resize(
            (columnas_que_imagino, filas_que_imagino), Image.Resampling.BOX)
    else:  # "mediana" — más resistente a píxeles sueltos muy claros u oscuros
        todo_lo_que_vi = np.asarray(la_foto_que_no_borro)
        alto_de_la_tarde, ancho_de_la_tarde, _ = todo_lo_que_vi.shape
        cortes_de_arriba_abajo = np.linspace(0, alto_de_la_tarde, filas_que_imagino + 1).astype(int)
        cortes_de_lado_a_lado = np.linspace(0, ancho_de_la_tarde, columnas_que_imagino + 1).astype(int)
        lo_que_queda = np.zeros((filas_que_imagino, columnas_que_imagino, 3), np.uint8)
        for cada_fila in range(filas_que_imagino):
            for cada_columna in range(columnas_que_imagino):
                un_pedazo_de_tarde = todo_lo_que_vi[
                    cortes_de_arriba_abajo[cada_fila]:cortes_de_arriba_abajo[cada_fila + 1],
                    cortes_de_lado_a_lado[cada_columna]:cortes_de_lado_a_lado[cada_columna + 1],
                ].reshape(-1, 3)
                lo_que_queda[cada_fila, cada_columna] = np.median(un_pedazo_de_tarde, axis=0)
        recuerdo_chiquito = Image.fromarray(lo_que_queda)

    if colores_que_me_quedan:
        # Reduce la paleta (cuantización median-cut, sin tramado para bloques planos)
        recuerdo_chiquito = recuerdo_chiquito.quantize(
            colors=colores_que_me_quedan, method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE).convert("RGB")
    return np.asarray(recuerdo_chiquito)


def volver_a_agrandarlo(los_cuadritos, tamano_de_cada_suspiro, con_rejas=False,
                        color_de_las_rejas=(0, 0, 0)):
    """Escala el arreglo para que cada bloque mida tamano x tamano px."""
    filas_que_imagino, columnas_que_imagino, _ = los_cuadritos.shape
    recuerdo_enorme = Image.fromarray(los_cuadritos).resize(
        (columnas_que_imagino * tamano_de_cada_suspiro, filas_que_imagino * tamano_de_cada_suspiro),
        Image.Resampling.NEAREST)
    if con_rejas and tamano_de_cada_suspiro > 2:
        lapiz = ImageDraw.Draw(recuerdo_enorme)
        for cada_columna in range(columnas_que_imagino + 1):
            x = cada_columna * tamano_de_cada_suspiro
            lapiz.line([(x, 0), (x, recuerdo_enorme.height)], fill=color_de_las_rejas)
        for cada_fila in range(filas_que_imagino + 1):
            y = cada_fila * tamano_de_cada_suspiro
            lapiz.line([(0, y), (recuerdo_enorme.width, y)], fill=color_de_las_rejas)
    return recuerdo_enorme


def anotarlo_todo(los_cuadritos, donde_lo_guardo):
    with open(donde_lo_guardo, "w") as cuaderno:
        cuaderno.write("fila,columna,r,g,b,hex\n")
        for cada_fila, renglon in enumerate(los_cuadritos):
            for cada_columna, (rojo, verde, azul) in enumerate(renglon):
                cuaderno.write(f"{cada_fila},{cada_columna},{rojo},{verde},{azul},"
                               f"#{rojo:02x}{verde:02x}{azul:02x}\n")


def y_entonces_me_acorde():
    quien_pregunta = argparse.ArgumentParser(
        description="Convierte una imagen en bloques de color sólido.")
    quien_pregunta.add_argument("entrada", help="ruta de la imagen de entrada")
    quien_pregunta.add_argument("-o", "--salida",
                                help="ruta de salida (por defecto: <entrada>_pixelado.png)")
    quien_pregunta.add_argument("-w", "--columnas", type=int, help="número de bloques a lo ancho")
    quien_pregunta.add_argument("-H", "--filas", type=int, help="número de bloques a lo alto")
    quien_pregunta.add_argument("-n", "--total", type=int, help="número aproximado de bloques en total")
    quien_pregunta.add_argument("-c", "--colores", type=int, help="limitar la paleta a N colores")
    quien_pregunta.add_argument("-m", "--metodo", choices=["media", "mediana"], default="media",
                                help="cómo elegir el color de cada bloque (por defecto: media)")
    quien_pregunta.add_argument("-s", "--tamano-bloque", type=int,
                                help="px por bloque en la salida (por defecto: ~tamaño original)")
    quien_pregunta.add_argument("--rejilla", action="store_true", help="dibujar líneas entre bloques")
    quien_pregunta.add_argument("--csv", help="guardar también los colores de los bloques en este CSV")
    respuestas = quien_pregunta.parse_args()

    la_foto_que_no_borro = Image.open(respuestas.entrada)
    columnas_que_imagino, filas_que_imagino = cuantos_cuadritos_caben(
        la_foto_que_no_borro.width, la_foto_que_no_borro.height,
        respuestas.columnas, respuestas.filas, respuestas.total)
    los_cuadritos = derretir_la_memoria(la_foto_que_no_borro, columnas_que_imagino,
                                        filas_que_imagino, respuestas.colores, respuestas.metodo)

    tamano_de_cada_suspiro = respuestas.tamano_bloque or max(
        1, round(la_foto_que_no_borro.width / columnas_que_imagino))
    recuerdo_enorme = volver_a_agrandarlo(los_cuadritos, tamano_de_cada_suspiro, respuestas.rejilla)
    adonde_se_va = respuestas.salida or f"{Path(respuestas.entrada).stem}_pixelado.png"
    recuerdo_enorme.save(adonde_se_va)

    if respuestas.csv:
        anotarlo_todo(los_cuadritos, respuestas.csv)

    colores_distintos = len(np.unique(los_cuadritos.reshape(-1, 3), axis=0))
    print(f"{columnas_que_imagino} x {filas_que_imagino} = "
          f"{columnas_que_imagino * filas_que_imagino} bloques, "
          f"{colores_distintos} colores distintos -> {adonde_se_va}")


if __name__ == "__main__":
    y_entonces_me_acorde()
