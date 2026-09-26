#!/usr/bin/env python3
"""
convertidorPixiPrueba.py — como convertidorPixi.py, pero pensado para pintar:
  1. siempre dibuja una rejilla, y
  2. a la derecha de cada columna de color deja una columna blanca
     para probar la mezcla antes de pintar el cuadro de verdad.

Necesita estar en la misma carpeta que convertidorPixi.py.

Ejemplos
--------
  # 8 columnas de color (+ 8 columnas blancas de prueba)
  python3 convertidorPixiPrueba.py foto.jpg -w 8

  # columnas blancas a la mitad del ancho, rejilla gris de 3 px
  python3 convertidorPixiPrueba.py foto.jpg -w 16 -b 0.5 -g 3 --color-rejilla 128,128,128

  # también guardar la lista de colores
  python3 convertidorPixiPrueba.py foto.jpg -w 8 -c 6 --csv colores.csv
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from convertidorPixi import cuantos_cuadritos_caben, derretir_la_memoria, anotarlo_todo


def la_hoja_de_ensayo(los_cuadritos, tamano_de_cada_suspiro, cuanto_blanco_me_das=1.0,
                      grosor_de_las_rejas=2, color_de_las_rejas=(0, 0, 0)):
    """Dibuja cada columna de color seguida de una columna blanca, todo con rejilla."""
    filas_que_imagino, columnas_que_imagino, _ = los_cuadritos.shape
    ancho_del_color = tamano_de_cada_suspiro
    ancho_del_silencio = max(1, round(tamano_de_cada_suspiro * cuanto_blanco_me_das))
    un_par_de_columnas = ancho_del_color + ancho_del_silencio

    lienzo_en_blanco = Image.new(
        "RGB", (columnas_que_imagino * un_par_de_columnas, filas_que_imagino * tamano_de_cada_suspiro),
        (255, 255, 255))
    pincel = ImageDraw.Draw(lienzo_en_blanco)

    for cada_fila in range(filas_que_imagino):
        for cada_columna in range(columnas_que_imagino):
            x = cada_columna * un_par_de_columnas
            y = cada_fila * tamano_de_cada_suspiro
            pincel.rectangle([x, y, x + ancho_del_color - 1, y + tamano_de_cada_suspiro - 1],
                             fill=tuple(int(v) for v in los_cuadritos[cada_fila, cada_columna]))

    # la rejilla: bordes de cada cuadro de color y de cada cuadro blanco
    donde_caen_las_lineas = set()
    for cada_columna in range(columnas_que_imagino):
        donde_caen_las_lineas.add(cada_columna * un_par_de_columnas)
        donde_caen_las_lineas.add(cada_columna * un_par_de_columnas + ancho_del_color)
    donde_caen_las_lineas.add(lienzo_en_blanco.width - 1)
    for x in donde_caen_las_lineas:
        pincel.line([(x, 0), (x, lienzo_en_blanco.height)], fill=color_de_las_rejas,
                    width=grosor_de_las_rejas)
    for cada_fila in range(filas_que_imagino + 1):
        y = min(cada_fila * tamano_de_cada_suspiro, lienzo_en_blanco.height - 1)
        pincel.line([(0, y), (lienzo_en_blanco.width, y)], fill=color_de_las_rejas,
                    width=grosor_de_las_rejas)
    return lienzo_en_blanco


def antes_de_pintar():
    quien_pregunta = argparse.ArgumentParser(
        description="Bloques de color con rejilla y una columna blanca de prueba junto a cada columna.")
    quien_pregunta.add_argument("entrada", help="ruta de la imagen de entrada")
    quien_pregunta.add_argument("-o", "--salida",
                                help="ruta de salida (por defecto: <entrada>_prueba.png)")
    quien_pregunta.add_argument("-w", "--columnas", type=int, help="número de columnas de color")
    quien_pregunta.add_argument("-H", "--filas", type=int, help="número de filas")
    quien_pregunta.add_argument("-n", "--total", type=int, help="número aproximado de bloques de color")
    quien_pregunta.add_argument("-c", "--colores", type=int, help="limitar la paleta a N colores")
    quien_pregunta.add_argument("-m", "--metodo", choices=["media", "mediana"], default="media",
                                help="cómo elegir el color de cada bloque (por defecto: media)")
    quien_pregunta.add_argument("-s", "--tamano-bloque", type=int,
                                help="px por bloque (por defecto: ~tamaño original de la foto)")
    quien_pregunta.add_argument("-b", "--ancho-blanco", type=float, default=1.0,
                                help="ancho de la columna blanca, relativo al bloque (por defecto: 1 = igual)")
    quien_pregunta.add_argument("-g", "--grosor", type=int, default=2,
                                help="grosor de la rejilla en px (por defecto: 2)")
    quien_pregunta.add_argument("--color-rejilla", default="0,0,0",
                                help="color de la rejilla como R,G,B (por defecto: 0,0,0 negro)")
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
    color_de_las_rejas = tuple(int(v) for v in respuestas.color_rejilla.split(","))
    la_hoja = la_hoja_de_ensayo(los_cuadritos, tamano_de_cada_suspiro, respuestas.ancho_blanco,
                                respuestas.grosor, color_de_las_rejas)
    adonde_se_va = respuestas.salida or f"{Path(respuestas.entrada).stem}_prueba.png"
    la_hoja.save(adonde_se_va)

    if respuestas.csv:
        anotarlo_todo(los_cuadritos, respuestas.csv)

    colores_distintos = len(np.unique(los_cuadritos.reshape(-1, 3), axis=0))
    print(f"{columnas_que_imagino} x {filas_que_imagino} bloques (+ {columnas_que_imagino} columnas blancas), "
          f"{colores_distintos} colores distintos -> {adonde_se_va}")


if __name__ == "__main__":
    antes_de_pintar()
