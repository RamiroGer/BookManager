"""Carga de datos de ejemplo para el sistema Book Manager."""
from __future__ import annotations

import csv
import os
from typing import Dict, List, Tuple

from book_manager.entities.entities import (
  Editorial, Genero, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioMoneda,
  RepositorioTipoCotizacion,
)
from book_manager.services.services import ServicioLibro

RUTA_COMPETENCIA: str = os.path.join(
  os.path.dirname(__file__),
  "..", "migrations", "csv", "competencia.csv",
)

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

LIBROS: List[Tuple] = [
  ("978-1", "Cien Años de Soledad", "Gabriel García Márquez",
   0, 0, 12000),
  ("978-2", "Rayuela", "Julio Cortázar", 1, 0, 9500),
  ("978-3", "El Principito", "Antoine de Saint-Exupéry",
   2, 2, 5500),
  ("978-4", "Sapiens", "Yuval Noah Harari", 3, 3, 15000),
  ("978-5", "1984", "George Orwell", 4, 6, 8500),
  ("978-6", "Ficciones", "Jorge Luis Borges", 5, 0, 7000),
  ("978-7", "El Aleph", "Jorge Luis Borges", 6, 0, 7200),
  ("978-8", "Dune", "Frank Herbert", 7, 6, 11000),
  ("978-9", "El Resplandor", "Stephen King", 8, 7, 9800),
  ("978-10", "Recetas de mi Abuela", "Autor Varios", 9, 9, 6500),
]

COMPETENCIA: List[Tuple[str, float]] = [
  ("978-1", 12500.0),
  ("978-2", 9200.0),
  ("978-3", 5800.0),
  ("978-4", 14500.0),
  ("978-5", 8900.0),
  ("978-6", 6800.0),
  ("978-7", 7500.0),
  ("978-8", 10500.0),
  ("978-9", 10200.0),
  ("978-10", 6200.0),
]


def cargar_datos_iniciales(
  repo_genero: RepositorioGenero,
  repo_editorial: RepositorioEditorial,
  repo_moneda: RepositorioMoneda,
  repo_tipo: RepositorioTipoCotizacion,
  servicio_libro: ServicioLibro,
) -> None:
  """Puebla el sistema con datos de ejemplo (mínimo 10 c/u)."""
  mapa_generos: Dict[int, Genero] = {}
  for i, nombre in enumerate(GENEROS):
    mapa_generos[i] = repo_genero.crear(Genero(nombre=nombre))

  mapa_editoriales: Dict[int, Editorial] = {}
  for i, (nombre, pais) in enumerate(EDITORIALES):
    mapa_editoriales[i] = repo_editorial.crear(
      Editorial(nombre=nombre, pais=pais)
    )

  moneda_ars: Moneda = repo_moneda.crear(
    Moneda(codigo="ARS", nombre="Peso Argentino")
  )
  repo_moneda.crear(
    Moneda(codigo="USD", nombre="Dólar Estadounidense")
  )
  repo_moneda.crear(Moneda(codigo="EUR", nombre="Euro"))

  for nombre_tipo in TIPOS_COTIZACION:
    repo_tipo.crear(TipoCotizacion(nombre=nombre_tipo))

  for isbn, titulo, autor, ed_idx, gen_idx, precio in LIBROS:
    servicio_libro.registrar_libro(
      isbn=isbn,
      titulo=titulo,
      autor=autor,
      editorial=mapa_editoriales[ed_idx],
      genero=mapa_generos[gen_idx],
      precio_ars=float(precio),
      moneda_ars=moneda_ars,
      cantidad_inicial=10,
    )

  _generar_csv_competencia()
  print("Datos iniciales cargados correctamente.")


def _generar_csv_competencia() -> None:
  """Genera el CSV con precios de referencia de la competencia."""
  os.makedirs(os.path.dirname(RUTA_COMPETENCIA), exist_ok=True)
  with open(
    RUTA_COMPETENCIA, "w", newline="", encoding="utf-8"
  ) as f:
    escritor = csv.writer(f)
    escritor.writerow(["isbn", "precio_ars"])
    for isbn, precio in COMPETENCIA:
      escritor.writerow([isbn, precio])
