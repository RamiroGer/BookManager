"""Punto de entrada del sistema Book Manager."""
from __future__ import annotations

from book_manager.preload_data.preload_data import (
  cargar_datos_iniciales,
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
from book_manager.ui.console import (
  menu_cotizaciones,
  menu_editoriales,
  menu_generos,
  menu_libros,
  menu_monedas,
  menu_precios,
  menu_stock,
  menu_tipos_cotizacion,
  reporte_bajo_stock,
  reporte_catalogo,
  reporte_comparacion_competencia,
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
10) Reporte: Comparación con Competencia
11) Reporte: Catálogo Completo
0) Salir
========================="""


def main(import_default_data: bool = True) -> None:
  """Inicializa el sistema y ejecuta el menú principal."""
  repo_genero = RepositorioGenero()
  repo_editorial = RepositorioEditorial()
  repo_moneda = RepositorioMoneda()
  repo_tipo = RepositorioTipoCotizacion()
  repo_libro = RepositorioLibro(repo_editorial, repo_genero)
  repo_precio = RepositorioPrecio(repo_libro, repo_moneda)
  repo_stock = RepositorioStock(repo_libro)
  repo_cotizacion = RepositorioCotizacionDolar(repo_tipo)

  servicio_cotizacion = ServicioCotizacion(
    repo_cotizacion, repo_tipo
  )
  servicio_precio = ServicioPrecio(
    repo_precio, repo_moneda, servicio_cotizacion
  )
  servicio_stock = ServicioStock(repo_stock)
  servicio_libro = ServicioLibro(
    repo_libro, repo_precio, repo_stock
  )
  servicio_comparacion = ServicioComparacionCompetencia(
    repo_libro
  )
  servicio_reportes = ServicioReportes(
    repo_libro, repo_stock, servicio_precio
  )

  if import_default_data and not repo_libro.leer_todos():
    cargar_datos_iniciales(
      repo_genero,
      repo_editorial,
      repo_moneda,
      repo_tipo,
      servicio_libro,
    )

  while True:
    print(OPCIONES_MENU)
    opcion: str = input("Seleccione una opción: ").strip()

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
        repo_genero, repo_moneda,
      )
    elif opcion == "6":
      menu_precios(servicio_precio, repo_precio, repo_tipo)
    elif opcion == "7":
      menu_stock(servicio_stock, repo_stock)
    elif opcion == "8":
      menu_cotizaciones(servicio_cotizacion, repo_cotizacion)
    elif opcion == "9":
      reporte_bajo_stock(servicio_reportes)
    elif opcion == "10":
      reporte_comparacion_competencia(
        servicio_comparacion, repo_libro, repo_precio
      )
    elif opcion == "11":
      reporte_catalogo(servicio_reportes)
    elif opcion == "0":
      print("Saliendo del sistema. ¡Hasta luego!")
      break
    else:
      print("Opción inválida, intente de nuevo.")


if __name__ == "__main__":
  main()
