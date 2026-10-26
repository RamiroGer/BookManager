"""Items que el spider de Cúspide entrega a los pipelines."""
import scrapy


class LibroWebItem(scrapy.Item):
  """Datos de una publicación de un libro en el sitio de Cúspide."""

  titulo_buscado = scrapy.Field()
  titulo_web = scrapy.Field()
  url = scrapy.Field()
  url_imagen = scrapy.Field()
  precio_web = scrapy.Field()
  formas_pago = scrapy.Field()
  descripcion = scrapy.Field()
  fecha_extraccion = scrapy.Field()
