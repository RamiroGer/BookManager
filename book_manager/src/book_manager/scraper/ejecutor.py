"""Punto de entrada que ejecuta el spider de Cúspide en un proceso aparte.

Se corre como proceso separado porque el reactor de Twisted de Scrapy
no puede reiniciarse dentro de la misma sesión de Python.
"""
import argparse
import os
from typing import List, Optional

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from book_manager.scraper.spiders.cuspide import CuspideSpider, URL_BASE


def ejecutar(titulos: str, salida: str, base_url: str) -> None:
  """Lanza el spider y espera a que termine la búsqueda."""
  os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "book_manager.scraper.settings"
  )
  configuracion = get_project_settings()
  configuracion.set("RUTA_SALIDA", salida, priority="cmdline")
  proceso = CrawlerProcess(configuracion)
  proceso.crawl(CuspideSpider, titulos_archivo=titulos, base_url=base_url)
  proceso.start()


def main(argumentos: Optional[List[str]] = None) -> None:
  """Lee los argumentos de línea de comandos y ejecuta el spider."""
  parser = argparse.ArgumentParser(description="Scraper de Cúspide")
  parser.add_argument("--titulos", required=True)
  parser.add_argument("--salida", required=True)
  parser.add_argument("--base-url", default=URL_BASE)
  args = parser.parse_args(argumentos)
  ejecutar(args.titulos, args.salida, args.base_url)


if __name__ == "__main__":
  main()
