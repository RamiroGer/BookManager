"""Configuración del proyecto Scrapy del scraper de Cúspide."""

BOT_NAME: str = "book_manager"
SPIDER_MODULES: list = ["book_manager.scraper.spiders"]
NEWSPIDER_MODULE: str = "book_manager.scraper.spiders"

ROBOTSTXT_OBEY: bool = True
USER_AGENT: str = "BookManager-Grupo56/1.0 (trabajo practico)"
DOWNLOAD_DELAY: float = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN: int = 2
LOG_LEVEL: str = "WARNING"
TELNETCONSOLE_ENABLED: bool = False
FEED_EXPORT_ENCODING: str = "utf-8"

ITEM_PIPELINES: dict = {
  "book_manager.scraper.pipelines.ValidarPrecioPipeline": 100,
  "book_manager.scraper.pipelines.ExportarJsonLinesPipeline": 300,
}
