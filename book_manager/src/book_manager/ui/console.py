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
  # ServicioComparacionCompetencia,  # deshabilitada
  ServicioCotizacion,
  ServicioLibro,
  ServicioPrecio,
  ServicioReportes,
  ServicioStock,
)


def _confirmar_accion(mensaje: str) -> bool:
  """Pregunta al usuario si desea continuar con la acción."""
  respuesta: str = input(f"{mensaje} (s/n): ").strip().lower()
  return respuesta == "s"


def menu_generos(repo_genero: RepositorioGenero) -> None:
  """Lista los géneros y permite dar de alta uno nuevo."""
  print("\n--- Listado de Géneros ---")
  for genero in repo_genero.leer_todos():
    print(f"  {genero}")

  if not _confirmar_accion("\n¿Desea dar de alta un género?"):
    print("Operación cancelada.")
    return

  nombre: str = input("Nombre del género: ")
  nuevo: Genero = repo_genero.crear(Genero(nombre=nombre))
  print(f"Creado: {nuevo}")


def menu_editoriales(repo_editorial: RepositorioEditorial) -> None:
  """Lista las editoriales y permite dar de alta una nueva."""
  print("\n--- Listado de Editoriales ---")
  for editorial in repo_editorial.leer_todos():
    print(f"  {editorial}")

  if not _confirmar_accion("\n¿Desea dar de alta una editorial?"):
    print("Operación cancelada.")
    return

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

  if not _confirmar_accion("\n¿Desea dar de alta una moneda?"):
    print("Operación cancelada.")
    return

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

  if not _confirmar_accion(
    "\n¿Desea dar de alta un tipo de cotización?"
  ):
    print("Operación cancelada.")
    return

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

  if not _confirmar_accion("\n¿Desea dar de alta un libro?"):
    print("Operación cancelada.")
    return

  if not repo_editorial.leer_todos() or not repo_genero.leer_todos():
    print("Debe existir al menos una editorial y un género.")
    return

  isbn: str = input("ISBN: ")
  titulo: str = input("Título: ")
  autor: str = input("Autor (opcional): ").strip() or "Desconocido"

  for e in repo_editorial.leer_todos():
    print(f"  [{e.id}] {e.nombre}")
  editorial_id: int = int(input("ID de editorial: "))
  editorial: Optional[Editorial] = repo_editorial.leer_por_id(
    editorial_id
  )
  if editorial is None:
    print(f"No existe una editorial con id={editorial_id}.")
    return

  for g in repo_genero.leer_todos():
    print(f"  [{g.id}] {g.nombre}")
  genero_id: int = int(input("ID de género: "))
  genero: Optional[Genero] = repo_genero.leer_por_id(genero_id)
  if genero is None:
    print(f"No existe un género con id={genero_id}.")
    return

  precio_ars: float = float(input("Precio (ARS): "))
  precio_usd: float = float(input("Precio (USD): "))
  cantidad: int = int(input("Cantidad inicial de stock: "))

  moneda_ars: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "ARS"),
    None,
  )
  moneda_usd: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "USD"),
    None,
  )

  nuevo: Libro = servicio_libro.registrar_libro(
    isbn=isbn,
    titulo=titulo,
    autor=autor,
    editorial=editorial,
    genero=genero,
    precio_ars=precio_ars,
    precio_usd=precio_usd,
    moneda_ars=moneda_ars,
    moneda_usd=moneda_usd,
    cantidad_inicial=cantidad,
  )
  print(f"Creado: {nuevo}")


def _obtener_o_cargar_cotizacion(
  servicio_cotizacion: ServicioCotizacion,
  tipo: TipoCotizacion,
) -> None:
  """Asegura que exista una cotización vigente para un tipo."""
  cotizacion = servicio_cotizacion.obtener_ultima_cotizacion(
    tipo.id
  )
  if cotizacion is not None:
    return

  print(f"No hay cotización registrada para \"{tipo.nombre}\".")
  print("Consultando cotización real...")
  resultado = servicio_cotizacion.obtener_cotizacion_automatica(
    tipo.nombre
  )

  if resultado is not None:
    valor_compra, valor_venta = resultado
    print(
      f"Cotización obtenida automáticamente: "
      f"compra ${valor_compra}, venta ${valor_venta}"
    )
  else:
    print(
      "No se pudo obtener la cotización automáticamente.\n"
      "Ingrese los valores manualmente:"
    )
    valor_compra = float(input("Valor de compra (ARS): "))
    valor_venta = float(input("Valor de venta (ARS): "))

  servicio_cotizacion.registrar_cotizacion(
    tipo.id, valor_compra, valor_venta
  )


def menu_precios(
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacion,
  repo_precio: RepositorioPrecio,
  repo_libro: RepositorioLibro,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Lista precios (ARS/USD) y permite actualizar el ARS de un libro."""
  print("\n--- Listado de Precios (ARS y USD) ---")
  for precio in repo_precio.leer_todos():
    print(f"  {precio}")

  if not _confirmar_accion(
    "\n¿Desea actualizar el precio ARS de un libro?"
  ):
    print("Operación cancelada.")
    return

  for l in repo_libro.leer_todos():
    print(f"  [{l.id}] {l.titulo}")
  libro_id: int = int(input("ID de libro: "))

  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("ID de tipo de cotización: "))

  tipo: Optional[TipoCotizacion] = repo_tipo.leer_por_id(tipo_id)
  if tipo is None:
    print(f"No existe el tipo id={tipo_id}.")
    return

  _obtener_o_cargar_cotizacion(servicio_cotizacion, tipo)

  try:
    actual, sugerido, diferencia = (
      servicio_precio.comparar_ars_vs_sugerido(libro_id, tipo_id)
    )
  except ValueError as error:
    print(f"No se pudo calcular: {error}")
    return

  print(f"\nPrecio ARS actual: ${actual}")
  print(f"Precio ARS sugerido ({tipo.nombre}): ${sugerido}")
  print(f"Diferencia: ${diferencia}")

  if _confirmar_accion("\n¿Aplicar el precio sugerido al libro?"):
    actualizado = servicio_precio.aplicar_precio_ars(
      libro_id, sugerido
    )
    print(f"Precio actualizado: {actualizado}")
  else:
    print("Precio no aplicado.")


def menu_stock(
  servicio_stock: ServicioStock, repo_stock: RepositorioStock
) -> None:
  """Lista el stock y permite modificar la cantidad de un libro."""
  print("\n--- Listado de Stock ---")
  for stock in repo_stock.leer_todos():
    print(f"  {stock}")

  if not _confirmar_accion("\n¿Desea modificar el stock?"):
    print("Operación cancelada.")
    return

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
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Lista cotizaciones y registra una nueva (API o manual)."""
  print("\n--- Listado de Cotizaciones ---")
  for cot in repo_cotizacion.leer_todos():
    print(f"  {cot}")

  if not _confirmar_accion(
    "\n¿Desea registrar una nueva cotización?"
  ):
    print("Operación cancelada.")
    return

  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("ID de tipo de cotización: "))

  tipo: Optional[TipoCotizacion] = repo_tipo.leer_por_id(tipo_id)
  if tipo is None:
    print(f"No existe el tipo id={tipo_id}.")
    return

  print(f"Consultando cotización real para \"{tipo.nombre}\"...")
  resultado = servicio_cotizacion.obtener_cotizacion_automatica(
    tipo.nombre
  )

  if resultado is not None:
    valor_compra, valor_venta = resultado
    print(
      f"Cotización obtenida automáticamente: "
      f"compra ${valor_compra}, venta ${valor_venta}"
    )
  else:
    print(
      "No se pudo obtener la cotización automáticamente.\n"
      "Ingrese los valores manualmente:"
    )
    valor_compra = float(input("Valor de compra (ARS): "))
    valor_venta = float(input("Valor de venta (ARS): "))

  try:
    nueva = servicio_cotizacion.registrar_cotizacion(
      tipo_id, valor_compra, valor_venta
    )
    print(f"Registrada: {nueva}")
  except ValueError as error:
    print(f"Error: {error}")


def reporte_bajo_stock(
  servicio_reportes: ServicioReportes, umbral: int = 5
) -> None:
  """Muestra los libros con stock por debajo del umbral."""
  print(f"\n--- Reporte: Libros con Bajo Stock (<{umbral}) ---")
  for stock in servicio_reportes.libros_con_bajo_stock(umbral):
    print(f"  {stock}")


# DESHABILITADO: web scraping (Tema 9, no visto en la
# cursada). Se deja comentado para habilitar más adelante.
# def reporte_comparacion_competencia(
#   servicio_comparacion: ServicioComparacionCompetencia,
#   servicio_precio: ServicioPrecio,
#   repo_libro: RepositorioLibro,
# ) -> None:
#   """Compara los precios propios (ARS y USD) contra Cúspide."""
#   print("\n--- Reporte: Comparación con la Competencia ---")
#   for libro in repo_libro.leer_todos():
#     precio_ars = servicio_precio.precio_por_moneda(
#       libro.id, "ARS"
#     )
#     precio_usd = servicio_precio.precio_por_moneda(
#       libro.id, "USD"
#     )
#     if precio_ars is None or precio_usd is None:
#       continue
#     resultado: str = servicio_comparacion.comparar(
#       libro.isbn, precio_ars.monto, precio_usd.monto
#     )
#     print(f"  {libro.titulo}: {resultado}")


def reporte_catalogo(
  servicio_reportes: ServicioReportes,
) -> None:
  """Muestra el catálogo completo con precios (ARS/USD) y stock."""
  print("\n--- Reporte: Catálogo Completo ---")
  for item in servicio_reportes.catalogo_completo():
    libro: Libro = item["libro"]
    print(
      f"  {libro.titulo} — Stock: {item['cantidad']} — "
      f"Precios: {item['precios']}"
    )
