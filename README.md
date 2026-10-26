# Book Manager

## Sprint 3

### Objetivo

Obtener los precios de la competencia desde el sitio de Cúspide con
Scrapy, compararlos con los precios internos, generar alertas y reportes
en CSV y Excel, y registrar cada operación en una tabla de auditoría.

### Introducción y contexto

Una librería con venta al público compite con otras librerías con venta
online. Para competir de forma informada necesita conocer el precio de
sus libros en la web. En el Sprint 2 el sistema ya usa la base de datos;
en este sprint se agrega la obtención de precios web, las alertas y los
reportes.

### Qué cambió respecto del Sprint 2

- `scraper/`: proyecto Scrapy con `CuspideSpider`, loaders y pipelines.
- `services/services.py`: `ServicioScraping` (comparación y alertas) y
  `ServicioReporteExcel` (reporte en Excel).
- `database/auditoria.py`: decorador `auditar` y tabla `auditoria`.
- `migrations/migrations.py`: `cargar_datos_sql`.
- `ui/console.py` y `main.py`: opciones 14, 15 y 16 del menú.

### Ejecución

```python
from book_manager.main import main
main(import_default_data=False)
```
