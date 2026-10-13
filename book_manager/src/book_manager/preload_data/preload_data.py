"""Datos iniciales del sistema Book Manager para la migración."""
from __future__ import annotations

import csv
import os
from datetime import date
from typing import Dict, List, Tuple

RUTA_CSV: str = os.path.join(
  os.path.dirname(os.path.abspath(__file__)),
  "..", "migrations", "csv",
)

MONEDAS: List[Tuple[str, str]] = [
  ("ARS", "Peso Argentino"),
  ("USD", "Dólar Estadounidense"),
  ("EUR", "Euro"),
]

GENEROS: List[str] = [
  "Novela", "Ensayo", "Infantil", "Técnico", "Poesía",
  "Biografía", "Ciencia Ficción", "Terror", "Historia", "Cocina",
]

EDITORIALES: List[Tuple[str, str]] = [
  ("Planeta", "Argentina"),
  ("Sudamericana", "Argentina"),
  ("Penguin Random House", "España"),
  ("Anagrama", "España"),
  ("Alfaguara", "España"),
  ("Paidós", "Argentina"),
  ("Emecé", "Argentina"),
  ("Siglo XXI", "Argentina"),
  ("Tusquets", "España"),
  ("Edhasa", "Argentina"),
]

TIPOS_COTIZACION: List[str] = [
  "Oficial", "Blue", "MEP", "Tarjeta",
  "Mayorista", "Cripto", "CCL", "Ahorro",
  "Turista", "Solidario",
]

# Cotización inicial de referencia por tipo (compra, venta) en ARS.
COTIZACIONES_INICIALES: Dict[str, Tuple[float, float]] = {
  "Oficial": (940.0, 980.0),
  "Blue": (1180.0, 1200.0),
  "MEP": (1150.0, 1170.0),
  "Tarjeta": (1250.0, 1270.0),
  "Mayorista": (930.0, 935.0),
  "Cripto": (1170.0, 1190.0),
  "CCL": (1160.0, 1180.0),
  "Ahorro": (1250.0, 1270.0),
  "Turista": (1250.0, 1270.0),
  "Solidario": (1250.0, 1270.0),
}

# Libros con precio en ARS y en USD, tal como los muestra Cúspide.
# (isbn, titulo, autor, editorial_idx, genero_idx, precio_ars, precio_usd)
LIBROS: List[Tuple] = [
  ("978-1", "Cien Años de Soledad", "Gabriel García Márquez",
   0, 0, 12000.0, 12.0),
  ("978-2", "Rayuela", "Julio Cortázar", 1, 0, 9500.0, 9.5),
  ("978-3", "El Principito", "Antoine de Saint-Exupéry",
   2, 2, 5500.0, 5.5),
  ("978-4", "Sapiens", "Yuval Noah Harari", 3, 3, 15000.0, 15.0),
  ("978-5", "1984", "George Orwell", 4, 6, 8500.0, 8.5),
  ("978-6", "Ficciones", "Jorge Luis Borges", 5, 0, 7000.0, 7.0),
  ("978-7", "El Aleph", "Jorge Luis Borges", 6, 0, 7200.0, 7.2),
  ("978-8", "Dune", "Frank Herbert", 7, 6, 11000.0, 11.0),
  ("978-9", "El Resplandor", "Stephen King", 8, 7, 9800.0, 9.8),
  ("978-10", "Recetas de mi Abuela", "Autor Varios",
   9, 9, 6500.0, 6.5),
]


def _escribir_csv(
  carpeta: str,
  archivo: str,
  encabezados: List[str],
  filas: List[List],
) -> None:
  """Escribe un archivo CSV con encabezados y filas."""
  ruta: str = os.path.join(carpeta, archivo)
  with open(ruta, "w", newline="", encoding="utf-8") as f:
    escritor = csv.writer(f)
    escritor.writerow(encabezados)
    escritor.writerows(filas)


def generar_csvs_iniciales(carpeta: str = RUTA_CSV) -> None:
  """Genera los CSV de origen (formato del Sprint 1) si no existen."""
  if os.path.exists(os.path.join(carpeta, "libros.csv")):
    return
  os.makedirs(carpeta, exist_ok=True)
  hoy: str = date.today().isoformat()

  _escribir_csv(
    carpeta, "generos.csv", ["id", "nombre"],
    [[i, n] for i, n in enumerate(GENEROS, 1)],
  )
  _escribir_csv(
    carpeta, "editoriales.csv", ["id", "nombre", "pais"],
    [[i, n, p] for i, (n, p) in enumerate(EDITORIALES, 1)],
  )
  _escribir_csv(
    carpeta, "monedas.csv", ["id", "codigo", "nombre"],
    [[i, c, n] for i, (c, n) in enumerate(MONEDAS, 1)],
  )
  _escribir_csv(
    carpeta, "tipos_cotizacion.csv", ["id", "nombre"],
    [[i, n] for i, n in enumerate(TIPOS_COTIZACION, 1)],
  )
  _escribir_csv(
    carpeta, "cotizaciones.csv",
    ["id", "tipo_id", "fecha", "valor_compra", "valor_venta"],
    [
      [i, i, hoy, *COTIZACIONES_INICIALES[nombre]]
      for i, nombre in enumerate(TIPOS_COTIZACION, 1)
    ],
  )

  libros: List[List] = []
  precios: List[List] = []
  stocks: List[List] = []
  for i, (isbn, titulo, autor, ed, gen, ars, usd) in enumerate(
    LIBROS, 1
  ):
    libros.append([i, isbn, titulo, autor, ed + 1, gen + 1])
    precios.append([len(precios) + 1, i, 1, ars])
    precios.append([len(precios) + 1, i, 2, usd])
    stocks.append([i, i, 10])
  _escribir_csv(
    carpeta, "libros.csv",
    ["id", "isbn", "titulo", "autor", "editorial_id", "genero_id"],
    libros,
  )
  _escribir_csv(
    carpeta, "precios.csv",
    ["id", "libro_id", "moneda_id", "monto"], precios,
  )
  _escribir_csv(
    carpeta, "stocks.csv", ["id", "libro_id", "cantidad"], stocks
  )
