"""Carga de datos de ejemplo para el sistema Book Manager."""
from __future__ import annotations

import csv
import os
from typing import Dict, List, Tuple

from book_manager.entities.entities import (
  Editorial, Genero, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioMoneda,
  RepositorioTipoCotizacion,
)
from book_manager.services.services import (
  ServicioCotizacion, ServicioLibro,
)

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

# Precios de referencia de la competencia (Cúspide): ARS y USD.
COMPETENCIA: List[Tuple[str, float, float]] = [
  ("978-1", 12500.0, 12.5),
  ("978-2", 9200.0, 9.2),
  ("978-3", 5800.0, 5.8),
  ("978-4", 14500.0, 14.5),
  ("978-5", 8900.0, 8.9),
  ("978-6", 6800.0, 6.8),
  ("978-7", 7500.0, 7.5),
  ("978-8", 10500.0, 10.5),
  ("978-9", 10200.0, 10.2),
  ("978-10", 6200.0, 6.2),
]


def cargar_datos_iniciales(
  repo_genero: RepositorioGenero,
  repo_editorial: RepositorioEditorial,
  repo_moneda: RepositorioMoneda,
  repo_tipo: RepositorioTipoCotizacion,
  servicio_libro: ServicioLibro,
  servicio_cotizacion: ServicioCotizacion,
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
  moneda_usd: Moneda = repo_moneda.crear(
    Moneda(codigo="USD", nombre="Dólar Estadounidense")
  )
  repo_moneda.crear(Moneda(codigo="EUR", nombre="Euro"))

  mapa_tipos: Dict[str, TipoCotizacion] = {}
  for nombre_tipo in TIPOS_COTIZACION:
    mapa_tipos[nombre_tipo] = repo_tipo.crear(
      TipoCotizacion(nombre=nombre_tipo)
    )

  for nombre_tipo, (compra, venta) in COTIZACIONES_INICIALES.items():
    servicio_cotizacion.registrar_cotizacion(
      tipo_id=mapa_tipos[nombre_tipo].id,
      valor_compra=compra,
      valor_venta=venta,
    )

  for (
    isbn, titulo, autor, ed_idx, gen_idx, precio_ars, precio_usd
  ) in LIBROS:
    servicio_libro.registrar_libro(
      isbn=isbn,
      titulo=titulo,
      autor=autor,
      editorial=mapa_editoriales[ed_idx],
      genero=mapa_generos[gen_idx],
      precio_ars=precio_ars,
      precio_usd=precio_usd,
      moneda_ars=moneda_ars,
      moneda_usd=moneda_usd,
      cantidad_inicial=10,
    )

  _generar_csv_competencia()
  print("Datos iniciales cargados correctamente.")


def _generar_csv_competencia() -> None:
  """Genera el CSV con precios ARS/USD de la competencia."""
  os.makedirs(os.path.dirname(RUTA_COMPETENCIA), exist_ok=True)
  with open(
    RUTA_COMPETENCIA, "w", newline="", encoding="utf-8"
  ) as f:
    escritor = csv.writer(f)
    escritor.writerow(["isbn", "precio_ars", "precio_usd"])
    for isbn, precio_ars, precio_usd in COMPETENCIA:
      escritor.writerow([isbn, precio_ars, precio_usd])
