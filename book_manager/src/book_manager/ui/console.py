"""Interfaz de consola (CLI) para el sistema Book Manager."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from book_manager.entities.entities import (
  Editorial, Genero, Libro, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  IRepositorio,
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


def _menu_crud_simple(
  nombre_entidad: str,
  repo: IRepositorio,
  campos: List[str],
  construir: Callable[[Dict[str, str]], object],
  aplicar_cambios: Callable[[object, Dict[str, str]], None],
) -> None:
  """Menú CRUD genérico para entidades con campos simples."""
  print(f"\n--- Listado de {nombre_entidad} ---")
  for item in repo.leer_todos():
    print(f"  {item}")

  print("\n  [1] Alta")
  print("  [2] Modificar")
  print("  [3] Eliminar")
  print("  [0] Volver")
  opcion: str = input("Opción: ").strip()

  if opcion == "1":
    valores: Dict[str, str] = {
      campo: input(f"{campo}: ") for campo in campos
    }
    nuevo = construir(valores)
    print(f"Creado: {repo.crear(nuevo)}")
  elif opcion == "2":
    id_: int = int(input("ID a modificar: "))
    existente = repo.leer_por_id(id_)
    if existente is None:
      print(f"No existe id={id_}.")
      return
    valores = {
      campo: input(f"Nuevo valor de {campo}: ")
      for campo in campos
    }
    aplicar_cambios(existente, valores)
    print(f"Actualizado: {repo.actualizar(existente)}")
  elif opcion == "3":
    id_ = int(input("ID a eliminar: "))
    eliminado: bool = repo.eliminar(id_)
    mensaje: str = (
      "Eliminado." if eliminado else f"No existe id={id_}."
    )
    print(mensaje)
  else:
    print("Operación cancelada.")


def menu_generos(repo_genero: RepositorioGenero) -> None:
  """Gestiona el CRUD completo de géneros."""
  _menu_crud_simple(
    "Géneros", repo_genero, ["nombre"],
    lambda v: Genero(nombre=v["nombre"]),
    lambda e, v: setattr(e, "nombre", v["nombre"]),
  )


def menu_editoriales(repo_editorial: RepositorioEditorial) -> None:
  """Gestiona el CRUD completo de editoriales."""
  _menu_crud_simple(
    "Editoriales", repo_editorial, ["nombre", "pais"],
    lambda v: Editorial(nombre=v["nombre"], pais=v["pais"]),
    lambda e, v: (
      setattr(e, "nombre", v["nombre"]),
      setattr(e, "pais", v["pais"]),
    ),
  )


def menu_monedas(repo_moneda: RepositorioMoneda) -> None:
  """Gestiona el CRUD completo de monedas."""
  _menu_crud_simple(
    "Monedas", repo_moneda, ["codigo", "nombre"],
    lambda v: Moneda(codigo=v["codigo"], nombre=v["nombre"]),
    lambda e, v: (
      setattr(e, "codigo", v["codigo"]),
      setattr(e, "nombre", v["nombre"]),
    ),
  )


def menu_tipos_cotizacion(
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Gestiona el CRUD completo de tipos de cotización."""
  _menu_crud_simple(
    "Tipos de Cotización", repo_tipo, ["nombre"],
    lambda v: TipoCotizacion(nombre=v["nombre"]),
    lambda e, v: setattr(e, "nombre", v["nombre"]),
  )


def menu_libros(
  servicio_libro: ServicioLibro,
  repo_libro: RepositorioLibro,
  repo_editorial: RepositorioEditorial,
  repo_genero: RepositorioGenero,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Gestiona el CRUD completo de libros."""
  print("\n--- Listado de Libros ---")
  for libro in repo_libro.leer_todos():
    print(f"  {libro}")

  print("\n  [1] Alta")
  print("  [2] Modificar")
  print("  [3] Eliminar")
  print("  [0] Volver")
  opcion: str = input("Opción: ").strip()

  if opcion == "1":
    _alta_libro(
      servicio_libro, repo_editorial, repo_genero, repo_moneda
    )
  elif opcion == "2":
    _modificar_libro(repo_libro, repo_editorial, repo_genero)
  elif opcion == "3":
    id_: int = int(input("ID a eliminar: "))
    eliminado: bool = repo_libro.eliminar(id_)
    mensaje: str = (
      "Eliminado." if eliminado else f"No existe id={id_}."
    )
    print(mensaje)
  else:
    print("Operación cancelada.")


def _alta_libro(
  servicio_libro: ServicioLibro,
  repo_editorial: RepositorioEditorial,
  repo_genero: RepositorioGenero,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Da de alta un libro nuevo con sus precios y stock inicial."""
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


def _modificar_libro(
  repo_libro: RepositorioLibro,
  repo_editorial: RepositorioEditorial,
  repo_genero: RepositorioGenero,
) -> None:
  """Modifica los datos básicos de un libro existente."""
  id_: int = int(input("ID a modificar: "))
  libro: Optional[Libro] = repo_libro.leer_por_id(id_)
  if libro is None:
    print(f"No existe id={id_}.")
    return

  libro.titulo = input(f"Nuevo título (actual: {libro.titulo}): ")
  libro.autor = input(f"Nuevo autor (actual: {libro.autor}): ")

  for g in repo_genero.leer_todos():
    print(f"  [{g.id}] {g.nombre}")
  genero_id: int = int(input("Nuevo ID de género: "))
  genero: Optional[Genero] = repo_genero.leer_por_id(genero_id)
  if genero is not None:
    libro.genero = genero

  print(f"Actualizado: {repo_libro.actualizar(libro)}")


def menu_precios(
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacion,
  repo_precio: RepositorioPrecio,
  repo_libro: RepositorioLibro,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Gestiona el CRUD completo de precios."""
  print("\n--- Listado de Precios (ARS y USD) ---")
  for precio in repo_precio.leer_todos():
    print(f"  {precio}")

  print("\n  [1] Actualizar ARS según cotización (sugerido)")
  print("  [2] Modificar un precio directamente")
  print("  [3] Eliminar un precio")
  print("  [0] Volver")
  opcion: str = input("Opción: ").strip()

  if opcion == "1":
    _sugerir_y_aplicar_precio(
      servicio_precio, servicio_cotizacion, repo_libro, repo_tipo
    )
  elif opcion == "2":
    id_: int = int(input("ID de precio a modificar: "))
    precio = repo_precio.leer_por_id(id_)
    if precio is None:
      print(f"No existe id={id_}.")
      return
    precio.monto = float(
      input(f"Nuevo monto (actual: {precio.monto}): ")
    )
    print(f"Actualizado: {repo_precio.actualizar(precio)}")
  elif opcion == "3":
    id_ = int(input("ID de precio a eliminar: "))
    eliminado: bool = repo_precio.eliminar(id_)
    mensaje: str = (
      "Eliminado." if eliminado else f"No existe id={id_}."
    )
    print(mensaje)
  else:
    print("Operación cancelada.")


def _sugerir_y_aplicar_precio(
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacion,
  repo_libro: RepositorioLibro,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Calcula el ARS sugerido según cotización y ofrece aplicarlo."""
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


def menu_stock(
  servicio_stock: ServicioStock, repo_stock: RepositorioStock
) -> None:
  """Gestiona el CRUD completo de stock."""
  print("\n--- Listado de Stock ---")
  for stock in repo_stock.leer_todos():
    print(f"  {stock}")

  print("\n  [1] Ajustar cantidad (ingreso/egreso)")
  print("  [2] Modificar cantidad directamente")
  print("  [3] Eliminar registro de stock")
  print("  [0] Volver")
  opcion: str = input("Opción: ").strip()

  if opcion == "1":
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
  elif opcion == "2":
    id_: int = int(input("ID de stock a modificar: "))
    stock = repo_stock.leer_por_id(id_)
    if stock is None:
      print(f"No existe id={id_}.")
      return
    stock.cantidad = int(
      input(f"Nueva cantidad (actual: {stock.cantidad}): ")
    )
    print(f"Actualizado: {repo_stock.actualizar(stock)}")
  elif opcion == "3":
    libro_id = int(input("ID de libro cuyo stock eliminar: "))
    eliminado: bool = repo_stock.eliminar(libro_id)
    mensaje: str = (
      "Eliminado."
      if eliminado
      else f"No hay stock para el libro id={libro_id}."
    )
    print(mensaje)
  else:
    print("Operación cancelada.")


def menu_cotizaciones(
  servicio_cotizacion: ServicioCotizacion,
  repo_cotizacion: RepositorioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Gestiona el CRUD completo de cotizaciones del dólar."""
  print("\n--- Listado de Cotizaciones ---")
  for cot in repo_cotizacion.leer_todos():
    print(f"  {cot}")

  print("\n  [1] Alta (API o manual)")
  print("  [2] Modificar una cotización")
  print("  [3] Eliminar una cotización")
  print("  [0] Volver")
  opcion: str = input("Opción: ").strip()

  if opcion == "1":
    _alta_cotizacion(servicio_cotizacion, repo_tipo)
  elif opcion == "2":
    id_: int = int(input("ID de cotización a modificar: "))
    cot = repo_cotizacion.leer_por_id(id_)
    if cot is None:
      print(f"No existe id={id_}.")
      return
    cot.valor_compra = float(
      input(f"Nuevo valor compra (actual: {cot.valor_compra}): ")
    )
    cot.valor_venta = float(
      input(f"Nuevo valor venta (actual: {cot.valor_venta}): ")
    )
    print(f"Actualizada: {repo_cotizacion.actualizar(cot)}")
  elif opcion == "3":
    tipo_id: int = int(input("ID de tipo: "))
    fecha: str = input("Fecha (YYYY-MM-DD): ")
    eliminado: bool = repo_cotizacion.eliminar(tipo_id, fecha)
    mensaje: str = (
      "Eliminada."
      if eliminado
      else "No existe una cotización con ese tipo y fecha."
    )
    print(mensaje)
  else:
    print("Operación cancelada.")


def _alta_cotizacion(
  servicio_cotizacion: ServicioCotizacion,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Registra una nueva cotización, vía API o manual."""
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
