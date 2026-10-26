"""Punto de entrada del sistema Book Manager."""
from __future__ import annotations

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
  RUTA_CSV,
  RUTA_SQL,
  migrar_datos,
)
from book_manager.preload_data.preload_data import (
  generar_csvs_iniciales,
)
from book_manager.repositories.repositories import (
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
  # ServicioComparacionCompetencia,  # deshabilitada (Tema 9)
  ServicioCotizacionDolar,
  ServicioLibro,
  ServicioPrecio,
  ServicioReporteExcel,
  ServicioReportes,
  ServicioScraping,
  ServicioStock,
)
from book_manager.ui.console import (
  exportar_precios,
  menu_cotizaciones,
  opcion_ejecutar_scraping,
  opcion_generar_reporte,
  opcion_historial_auditoria,
  menu_editoriales,
  menu_generos,
  menu_libros,
  menu_monedas,
  menu_precios,
  menu_stock,
  menu_tipos_cotizacion,
  opcion_obtener_cotizaciones,
  reporte_bajo_stock,
  reporte_catalogo,
  reporte_precios_bimonetarios,
)

OPCIONES_MENU: str = """
===== Book Manager =====
1) Géneros
2) Editoriales
3) Monedas
4) Tipos de Cotización
5) Libros
6) Precios
7) Stock
8) Cotizaciones del Dólar
9) Reporte: Bajo Stock
10) Reporte: Catálogo Completo
11) Obtener cotizaciones por API
12) Lista de precios bimonetaria
13) Exportar precios a CSV
14) Ejecutar scraping (Cúspide)
15) Generar reporte en Excel
16) Historial de auditoría
0) Salir
========================="""


def main(import_default_data: bool = True) -> None:
  """Inicializa la base de datos y ejecuta el menú principal.

  Args:
    import_default_data: Si es True migra los CSV a la base aunque
      ya tenga datos; si la base está vacía siempre se migra.
  """
  conexion = ConexionDB()
  conexion.crear_tablas()

  repo_genero = RepositorioGenero(conexion)
  repo_editorial = RepositorioEditorial(conexion)
  repo_moneda = RepositorioMoneda(conexion)
  repo_tipo = RepositorioTipoCotizacion(conexion)
  repo_libro = RepositorioLibro(conexion)
  repo_precio = RepositorioPrecio(conexion)
  repo_stock = RepositorioStock(conexion)
  repo_cotizacion = RepositorioCotizacionDolar(conexion)

  servicio_cotizacion = ServicioCotizacionDolar(
    repo_cotizacion, repo_tipo
  )
  servicio_precio = ServicioPrecio(
    repo_precio, repo_moneda, repo_libro, servicio_cotizacion
  )
  servicio_stock = ServicioStock(repo_stock)
  servicio_libro = ServicioLibro(
    repo_libro, repo_precio, repo_stock
  )
  servicio_reportes = ServicioReportes(
    repo_libro, repo_stock, servicio_precio
  )
  repo_auditoria = RepositorioAuditoria(conexion)
  servicio_scraping = ServicioScraping(
    conexion, repo_libro, servicio_precio
  )
  servicio_reporte_excel = ServicioReporteExcel(conexion)

  if import_default_data or not repo_libro.leer_todos():
    generar_csvs_iniciales()
    migrar_datos(RUTA_CSV, RUTA_SQL, conexion)
    print("Datos migrados correctamente a la base de datos.")

  while True:
    print(OPCIONES_MENU)
    opcion: str = input("Seleccione una opción: ").strip()

    try:
      if opcion == "1":
        menu_generos(repo_genero)
      elif opcion == "2":
        menu_editoriales(repo_editorial)
      elif opcion == "3":
        menu_monedas(repo_moneda)
      elif opcion == "4":
        menu_tipos_cotizacion(repo_tipo)
      elif opcion == "5":
        menu_libros(
          servicio_libro, repo_libro, repo_editorial,
          repo_genero, repo_moneda, servicio_cotizacion, repo_tipo,
        )
      elif opcion == "6":
        menu_precios(
          servicio_precio, servicio_cotizacion, repo_precio,
          repo_libro, repo_tipo,
        )
      elif opcion == "7":
        menu_stock(servicio_stock, repo_stock)
      elif opcion == "8":
        menu_cotizaciones(
          servicio_cotizacion, repo_cotizacion, repo_tipo
        )
      elif opcion == "9":
        reporte_bajo_stock(servicio_reportes)
      elif opcion == "10":
        reporte_catalogo(servicio_reportes)
      elif opcion == "11":
        opcion_obtener_cotizaciones(servicio_cotizacion)
      elif opcion == "12":
        reporte_precios_bimonetarios(servicio_precio, repo_moneda)
      elif opcion == "13":
        exportar_precios(servicio_precio)
      elif opcion == "14":
        opcion_ejecutar_scraping(servicio_scraping)
      elif opcion == "15":
        opcion_generar_reporte(servicio_reporte_excel)
      elif opcion == "16":
        opcion_historial_auditoria(repo_auditoria)
      elif opcion == "0":
        print("Saliendo del sistema. ¡Hasta luego!")
        break
      else:
        print("Opción inválida, intente de nuevo.")
    except ValueError as error:
      print(f"Entrada o dato inválido: {error}")


if __name__ == "__main__":
  main()
