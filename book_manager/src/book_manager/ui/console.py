"""Interfaz de consola (CLI) para el sistema Book Manager."""
from __future__ import annotations

from datetime import date
from typing import Callable, Dict, List, Optional

from book_manager.entities.entities import (
  CotizacionDolar, Editorial, Genero, Libro, Moneda, TipoCotizacion,
)
from book_manager.repositories.repositories import (
  IRepositorio,
  RepositorioAuditoria,
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
  ServicioCotizacionDolar,
  ServicioLibro,
  ServicioPrecio,
  ServicioReporteExcel,
  ServicioReportes,
  ServicioScraping,
  ServicioStock,
)


def _confirmar_accion(mensaje: str) -> bool:
  """Pregunta al usuario si desea continuar con la acción."""
  respuesta: str = input(f"{mensaje} (s/n): ").strip().lower()
  return respuesta == "s"


def _existe_duplicado(
  repo: IRepositorio,
  campo: str,
  valor: str,
  id_excluido: Optional[int] = None,
) -> bool:
  """Indica si ya hay otro registro con el mismo valor en el campo."""
  buscado: str = valor.strip().lower()
  for item in repo.leer_todos():
    if getattr(item, "id", None) == id_excluido:
      continue
    if str(getattr(item, campo)).strip().lower() == buscado:
      return True
  return False


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
    if _existe_duplicado(repo, campos[0], valores[campos[0]]):
      print(f"Ya existe un registro con ese {campos[0]}.")
      return
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
    if _existe_duplicado(
      repo, campos[0], valores[campos[0]], existente.id
    ):
      print(f"Ya existe un registro con ese {campos[0]}.")
      return
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
  servicio_cotizacion: ServicioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
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
      servicio_libro, repo_editorial, repo_genero, repo_moneda,
      servicio_cotizacion, repo_tipo,
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
  servicio_cotizacion: ServicioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
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

  moneda_ars: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "ARS"),
    None,
  )
  moneda_usd: Optional[Moneda] = next(
    (m for m in repo_moneda.leer_todos() if m.codigo == "USD"),
    None,
  )

  if moneda_ars is None or moneda_usd is None:
    print("Deben existir las monedas ARS y USD.")
    return

  cotizacion: Optional[CotizacionDolar] = _elegir_cotizacion(
    servicio_cotizacion, repo_tipo
  )
  if cotizacion is None:
    return

  precio_ars: float = float(input("Precio (ARS): "))
  precio_usd: float = float(input("Precio (USD): "))
  cantidad: int = int(input("Cantidad inicial de stock: "))

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
    cotizacion=cotizacion,
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
  servicio_cotizacion: ServicioCotizacionDolar,
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
    if precio.moneda.codigo == "ARS":
      cotizacion = _elegir_cotizacion(servicio_cotizacion, repo_tipo)
      if cotizacion is None:
        return
      precio.cotizacion = cotizacion
    else:
      precio.cotizacion = None
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
  servicio_cotizacion: ServicioCotizacionDolar,
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

  cotizacion: CotizacionDolar = _obtener_o_cargar_cotizacion(
    servicio_cotizacion, tipo
  )

  try:
    actual, sugerido, diferencia = (
      servicio_precio.comparar_ars_vs_sugerido(libro_id, tipo_id)
    )
  except ValueError as error:
    print(f"No se pudo calcular: {error}")
    return

  print(f"\nPrecio ARS actual: ${actual}")
  print(
    f"Cotización usada ({tipo.nombre}, {cotizacion.fecha}): "
    f"${cotizacion.valor_venta}"
  )
  print(f"Precio ARS sugerido ({tipo.nombre}): ${sugerido}")
  print(f"Diferencia: ${diferencia}")

  if _confirmar_accion("\n¿Aplicar el precio sugerido al libro?"):
    actualizado = servicio_precio.aplicar_precio_ars(
      libro_id, sugerido, cotizacion
    )
    print(f"Precio actualizado: {actualizado}")
  else:
    print("Precio no aplicado.")


def _obtener_o_cargar_cotizacion(
  servicio_cotizacion: ServicioCotizacionDolar,
  tipo: TipoCotizacion,
) -> CotizacionDolar:
  """Devuelve la cotización vigente de un tipo, cargándola si falta."""
  cotizacion = servicio_cotizacion.obtener_ultima_cotizacion(
    tipo.id
  )
  if cotizacion is not None:
    return cotizacion

  print(f"No hay cotización registrada para \"{tipo.nombre}\".")
  print("Consultando cotizaciones en la API...")
  try:
    servicio_cotizacion.obtener_cotizaciones()
  except (ConnectionError, ValueError) as error:
    print(f"No se pudo usar la API: {error}")

  cotizacion = servicio_cotizacion.obtener_ultima_cotizacion(tipo.id)
  if cotizacion is not None:
    return cotizacion

  print("Ingrese los valores manualmente:")
  valor_compra: float = float(input("Valor de compra (ARS): "))
  valor_venta: float = float(input("Valor de venta (ARS): "))
  return servicio_cotizacion.registrar_cotizacion(
    tipo.id, valor_compra, valor_venta
  )


def _elegir_cotizacion(
  servicio_cotizacion: ServicioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
) -> Optional[CotizacionDolar]:
  """Pide un tipo de cotización y devuelve su cotización vigente."""
  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("ID de tipo de cotización: "))
  tipo: Optional[TipoCotizacion] = repo_tipo.leer_por_id(tipo_id)
  if tipo is None:
    print(f"No existe el tipo id={tipo_id}.")
    return None
  return _obtener_o_cargar_cotizacion(servicio_cotizacion, tipo)


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
  servicio_cotizacion: ServicioCotizacionDolar,
  repo_cotizacion: RepositorioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Gestiona el CRUD completo de cotizaciones del dólar."""
  print("\n--- Listado de Cotizaciones ---")
  for cot in repo_cotizacion.leer_todos():
    print(f"  {cot}")

  print("\n  [1] Alta manual")
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
    fecha: date = date.fromisoformat(
      input("Fecha (YYYY-MM-DD): ").strip()
    )
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
  servicio_cotizacion: ServicioCotizacionDolar,
  repo_tipo: RepositorioTipoCotizacion,
) -> None:
  """Registra manualmente una cotización para un tipo."""
  for t in repo_tipo.leer_todos():
    print(f"  [{t.id}] {t.nombre}")
  tipo_id: int = int(input("ID de tipo de cotización: "))
  valor_compra: float = float(input("Valor de compra (ARS): "))
  valor_venta: float = float(input("Valor de venta (ARS): "))

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


def opcion_obtener_cotizaciones(
  servicio_cotizacion: ServicioCotizacionDolar,
) -> None:
  """Descarga las cotizaciones de la API y las registra."""
  print("\n--- Obtener cotizaciones por API ---")
  try:
    registradas = servicio_cotizacion.obtener_cotizaciones()
  except (ConnectionError, ValueError) as error:
    print(f"No se pudieron obtener las cotizaciones: {error}")
    return
  for cot in registradas:
    print(f"  {cot}")
  print(f"{len(registradas)} cotizaciones registradas.")


def reporte_precios_bimonetarios(
  servicio_precio: ServicioPrecio,
  repo_moneda: RepositorioMoneda,
) -> None:
  """Muestra la lista de precios en pesos y en otra moneda."""
  otras: List[Moneda] = [
    m for m in repo_moneda.leer_todos() if m.codigo != "ARS"
  ]
  if not otras:
    print("No hay otras monedas además de ARS.")
    return
  for m in otras:
    print(f"  [{m.codigo}] {m.nombre}")
  codigo: str = input("Código de la moneda: ").strip().upper()
  if codigo not in [m.codigo for m in otras]:
    print(f"Moneda inválida: {codigo}.")
    return

  print(f"\n--- Lista de precios ARS / {codigo} ---")
  for libro, ars, otra in servicio_precio.lista_bimonetaria(codigo):
    texto_ars: str = "sin precio" if ars is None else f"${ars}"
    texto_otra: str = (
      "sin precio" if otra is None else f"{otra} {codigo}"
    )
    print(f"  {libro.titulo}: {texto_ars} | {texto_otra}")


def exportar_precios(servicio_precio: ServicioPrecio) -> None:
  """Exporta los precios de todas las monedas a un CSV."""
  ruta: str = servicio_precio.exportar_precios_csv()
  print(f"Precios exportados en: {ruta}")


def opcion_ejecutar_scraping(servicio_scraping: ServicioScraping) -> None:
  """Pide la diferencia para las alertas y ejecuta el scraping."""
  print("\n--- Ejecutar scraping (Cúspide) ---")
  umbral: float = float(
    input("Diferencia de precio para generar alerta (ARS): ")
  )
  print("Buscando los libros del catálogo en Cúspide...")
  try:
    resultado = servicio_scraping.ejecutar(umbral)
  except (ConnectionError, ValueError) as error:
    print(f"No se pudo ejecutar el scraping: {error}")
    return
  print(f"Libros comparados: {resultado['comparadas']}")
  print(f"Alertas generadas: {resultado['alertas']}")
  print(f"Comparación completa: {resultado['ruta_comparacion']}")
  print(f"Alertas (CSV para descargar): {resultado['ruta_alertas']}")


def opcion_generar_reporte(servicio_reporte: ServicioReporteExcel) -> None:
  """Genera el reporte en Excel con la última comparación."""
  print("\n--- Generar reporte en Excel ---")
  try:
    ruta: str = servicio_reporte.generar()
  except ValueError as error:
    print(f"No se pudo generar el reporte: {error}")
    return
  print(f"Reporte generado: {ruta}")


def opcion_historial_auditoria(repo_auditoria: RepositorioAuditoria) -> None:
  """Muestra los últimos registros de auditoría, el más reciente primero."""
  print("\n--- Historial de auditoría (últimos 50) ---")
  registros = repo_auditoria.leer_todos()
  for registro in reversed(registros[-50:]):
    print(f"  {registro}")
  print(f"{len(registros)} registros en total.")
