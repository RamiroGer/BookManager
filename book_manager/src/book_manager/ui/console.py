"""Interfaz de consola (CLI) para el sistema Book Manager."""
from __future__ import annotations

from typing import Optional

from book_manager.entities.entities import (
  Editorial, Genero, Libro, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)
from book_manager.services.services import (
  ServicioComparacionCompetencia,
  ServicioCotizacion,
  ServicioLibro,
  ServicioPrecio,
  ServicioReportes,
  ServicioStock,
)


def menu_generos(repo_genero: RepositorioGenero) -> None:
  """Lista los géneros y permite dar de alta uno nuevo."""
  print("\n--- Listado de Géneros ---")
  for genero in repo_genero.leer_todos():
    print(f"  {genero}")

  print("\n--- Alta de Género ---")
  nombre: str = input("Nombre del género: ")
  nuevo: Genero = repo_genero.crear(Genero(nombre=nombre))
  print(f"Creado: {nuevo}")


def menu_editoriales(repo_editorial: RepositorioEditorial) -> None:
  """Lista las editoriales y permite dar de alta una nueva."""
  print("\n--- Listado de Editoriales ---")
  for editorial in repo_editorial.leer_todos():
    print(f"  {editorial}")

  print("\n--- Alta de Editorial ---")
  nombre: str = input("Nombre de la editorial: ")
  pais: str = input("País: ")
  nueva: Editorial = repo_editorial.crear(
    Editorial(nombre=nombre, pais=pais)
  )
  print(f"Creada: {nueva}")


def menu_monedas(repo_moneda: RepositorioMoneda) -> None:
  """Lista las monedas y permite dar de alta una nueva."""
  print("\n--- Listado de Monedas ---")
  for moneda in repo_moneda.leer_todos():
    print(f"  {moneda}")

  print("\n--- Alta de Moneda ---")
  codigo: str = input("Código (ej. ARS): ")
  nombre: str = input("Nombre: ")
  nueva: Moneda = repo_moneda.crear(
    Moneda(codigo=codigo, nombre=nombre)
  )
  print(f"Creada: {nueva}")


def menu_tipos_cotizacion(
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Lista los tipos de cotización y permite dar de alta uno."""
  print("\n--- Listado de Tipos de Cotización ---")
  for tipo in repo_tipo.leer_todos():
    print(f"  {tipo}")

  print("\n--- Alta de Tipo de Cotización ---")
  nombre: str = input("Nombre del tipo: ")
  nuevo: TipoCotizacion = repo_tipo.crear(
    TipoCotizacion(nombre=nombre)
  )
  print(f"Creado: {nuevo}")


def menu_libros(
  servicio_libro: ServicioLibro,
  repo_libro: RepositorioLibro,
  repo_editorial: RepositorioEditorial,
  repo_genero: RepositorioGenero,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Lista los libros y permite dar de alta uno nuevo."""
  print("\n--- Listado de Libros ---")
  for libro in repo_libro.leer_todos():
    print(f"  {libro}")

  print("\n--- Alta de Libro ---")
  isbn: str = input("ISBN: ")
  titulo: str = input("Título: ")
  autor: str = input("Autor: ")

  for e in repo_editorial.leer_todos():
    print(f"  [{e.id}] {e.nombre}")
  editorial_id: int = int(input("ID de editorial: "))
  editorial: Optional[Editorial] = repo_editorial.leer_por_id(
    editorial_id
  )

  for g in repo_genero.leer_todos():
    print(f"  [{g.id}] {g.nombre}")
  genero_id: int = int(input("ID de género: "))
  genero: Optional[Genero] = repo_genero.leer_por_id(genero_id)

  precio: float = float(input("Precio (ARS): "))
  cantidad: int = int(input("Cantidad inicial de stock: "))
  moneda_ars: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "ARS"),
    None,
  )

  nuevo: Libro = servicio_libro.registrar_libro(
    isbn=isbn,
    titulo=titulo,
    autor=autor,
    editorial=editorial,
    genero=genero,
    precio_ars=precio,
    moneda_ars=moneda_ars,
    cantidad_inicial=cantidad,
  )
  print(f"Creado: {nuevo}")


def menu_precios(
  servicio_precio: ServicioPrecio,
  repo_precio: RepositorioPrecio,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Lista los precios y permite consultar su valor en USD."""
  print("\n--- Listado de Precios ---")
  for precio in repo_precio.leer_todos():
    print(f"  {precio}")

  print("\n--- Consultar Precio en USD ---")
  libro_id: int = int(input("ID de libro: "))
  tipos = repo_tipo.leer_todos()
  for t in tipos:
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("ID de tipo de cotización: "))

  precios = servicio_precio.precios_de_libro(libro_id)
  if not precios:
    print("El libro no tiene precios registrados.")
    return
  try:
    en_usd: float = servicio_precio.convertir_a_usd(
      precios[0].monto, tipo_id
    )
    print(f"Precio en USD: ${en_usd}")
  except ValueError as error:
    print(f"No se pudo convertir: {error}")


def menu_stock(
  servicio_stock: ServicioStock, repo_stock: RepositorioStock
) -> None:
  """Lista el stock y permite modificar la cantidad de un libro."""
  print("\n--- Listado de Stock ---")
  for stock in repo_stock.leer_todos():
    print(f"  {stock}")

  print("\n--- Modificar Stock ---")
  libro_id: int = int(input("ID de libro: "))
  cantidad: int = int(
    input("Cantidad (positiva=ingreso, negativa=egreso): ")
  )
  try:
    if cantidad >= 0:
      actualizado = servicio_stock.ingresar(libro_id, cantidad)
    else:
      actualizado = servicio_stock.egresar(
        libro_id, abs(cantidad)
      )
    print(f"Stock actualizado: {actualizado}")
  except ValueError as error:
    print(f"Error: {error}")


def menu_cotizaciones(
  servicio_cotizacion: ServicioCotizacion,
  repo_cotizacion: RepositorioCotizacionDolar,
) -> None:
  """Lista las cotizaciones y actualiza el histórico desde la API."""
  print("\n--- Listado de Cotizaciones ---")
  for cot in repo_cotizacion.leer_todos():
    print(f"  {cot}")

  print("\n--- Actualizar Cotizaciones desde DolarAPI ---")
  nuevas = servicio_cotizacion.actualizar_cotizaciones()
  print(f"Cotizaciones nuevas agregadas: {len(nuevas)}")
  for cot in nuevas:
    print(f"  {cot}")


def reporte_bajo_stock(
  servicio_reportes: ServicioReportes, umbral: int = 5
) -> None:
  """Muestra los libros con stock por debajo del umbral."""
  print(f"\n--- Reporte: Libros con Bajo Stock (<{umbral}) ---")
  for stock in servicio_reportes.libros_con_bajo_stock(umbral):
    print(f"  {stock}")


def reporte_comparacion_competencia(
  servicio_comparacion: ServicioComparacionCompetencia,
  repo_libro: RepositorioLibro,
  repo_precio: RepositorioPrecio,
) -> None:
  """Compara los precios propios contra los de la competencia."""
  print("\n--- Reporte: Comparación con la Competencia ---")
  for libro in repo_libro.leer_todos():
    precios = [
      p for p in repo_precio.leer_todos()
      if p.libro.id == libro.id
    ]
    if not precios:
      continue
    resultado: str = servicio_comparacion.comparar(
      libro.isbn, precios[0].monto
    )
    print(f"  {libro.titulo}: {resultado}")


def reporte_catalogo(
  servicio_reportes: ServicioReportes,
) -> None:
  """Muestra el catálogo completo con precio y stock."""
  print("\n--- Reporte: Catálogo Completo ---")
  for item in servicio_reportes.catalogo_completo():
    libro: Libro = item["libro"]
    print(
      f"  {libro.titulo} — Stock: {item['cantidad']} — "
      f"Precios: {item['precios']}"
    )
