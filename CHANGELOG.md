## [Ejercicio 02 - Sprint 2]
- Clase ConexionDB con motor SQLite de SQLAlchemy.
- Base declarativa compartida por los modelos.
- Claves foráneas activadas en SQLite.
- Método crear_tablas.

## [Ejercicio 01 - Sprint 2]
- Rama Sprint_2 creada a partir de Sprint_1.
- Agregadas las carpetas database, models y migrations (csv y sql).
- requirements.txt con sqlalchemy y python-dotenv.
- .gitignore ignora __pycache__, .pyc y la base de datos .db.
- CHANGELOG reordenado: el último cambio se lee primero.

# Changelog

Los cambios más recientes aparecen primero.

## [Ejercicio 06 - Fix 5]
- Consulta automática a la API del dólar (DolarAPI) deshabilitada y comentada: la consigna pide trabajar sin API.
- services.py: comentados obtener_cotizacion_automatica, URL_API_DOLAR y los imports json / urllib.request.
- console.py: menu_cotizaciones y menu_precios piden la cotización manualmente; el código de la API quedó comentado.
- README.md y textos del notebook actualizados (sin API ni scraping).

## [Ejercicio 06 - Fix 4]
- aplicar_precio_ars agregado a ServicioPrecio.
- menu_precios ahora resuelve la cotización faltante (pidiéndola por consola) antes de sugerir.
- Opción de aplicar el precio sugerido al libro directamente desde el menú.

## [Ejercicio 06 - Fix 3]
- Comparación con competencia (Cúspide) deshabilitada y comentada: requiere web scraping (Tema 9, no visto).
- Opción de menú y reporte correspondiente removidos de main.py y console.py.
- CSVs de prueba limpiados de registros duplicados.

## [Ejercicio 06 - Fix 2]
- Precios duales ARS/USD por libro, tal como los muestra Cúspide.
- Corregida inconsistencia de tipos: 'fecha' mezclaba str y datetime.date entre archivos, unificado a str en entities.py, repositories.py y services.py.

## [Ejercicio 07]
- main.py con menú principal y composición de dependencias.
- Carga automática de datos iniciales si el repositorio está vacío.

## [Ejercicio 06 - Fix 1]
- Confirmación (s/n) agregada antes de cada alta.
- Campo autor hecho opcional (default 'Desconocido').
- __repr__ de Libro actualizado para mostrar el autor.
- Validación de IDs inexistentes al dar de alta un libro.
- CSVs limpiados de registros de prueba corruptos.

## [Ejercicio 06]
- Menús de consola para las 8 entidades.
- Reportes: bajo stock y catálogo completo.

## [Ejercicio 05]
- preload_data.py con datos de ejemplo (10+ registros por entidad).

## [Ejercicio 04]
- ServicioCotizacion: registro y consulta de cotizaciones cargadas manualmente.
- ServicioPrecio: precio ARS sugerido a partir del precio USD y la cotización.
- ServicioStock, ServicioLibro y ServicioReportes.

## [Ejercicio 03]
- Interfaz IRepositorio (Generic, ABC) definida.
- RepositorioCSVBase con persistencia genérica.
- Repositorios CRUD para las 8 entidades.

## [Ejercicio 02]
- Entidades definidas: Genero, Editorial, Moneda, TipoCotizacion, Libro, Precio, Stock, CotizacionDolar.
- Encapsulación aplicada mediante properties.

## [Ejercicio 01]
- Rama Sprint_1 creada.
- Estructura de directorios del proyecto generada.
- requirements.txt creado (sin dependencias externas).

## [Ejercicio 01]
- Rama Sprint_1 creada.
- Estructura de directorios del proyecto generada.
- requirements.txt creado (sin dependencias externas).

## [Ejercicio 06 - Fix CRUD]
- __pycache__ y *.pyc removidos del repositorio.
- .gitignore actualizado.
- CRUD completo en los 8 menús de consola (Listar, Alta, Modificar, Eliminar).

## [Ejercicio 06 - Fix]
- Comparación con competencia (Cúspide) deshabilitada y comentada: requiere web scraping (Tema 9, no visto).
- Opción de menú y reporte correspondiente removidos de main.py y console.py.
- CSVs de prueba limpiados de registros duplicados.

## [Ejercicio 06 - Fix 2]
- aplicar_precio_ars agregado a ServicioPrecio.
- menu_precios ahora resuelve la cotización faltante (API o manual) antes de sugerir.
- Opción de aplicar el precio sugerido al libro directamente desde el menú.

## [Ejercicio 01]
- Rama Sprint_1 creada.
- Estructura de directorios del proyecto generada.
- requirements.txt creado (sin dependencias externas).

## [Ejercicio 06 - Fix CRUD]
- __pycache__ y *.pyc removidos del repositorio.
- .gitignore actualizado.
- CRUD completo en los 8 menús de consola (Listar, Alta, Modificar, Eliminar).

## [Ejercicio 06 - Fix]
- Comparación con competencia (Cúspide) deshabilitada y comentada: requiere web scraping (Tema 9, no visto).
- Opción de menú y reporte correspondiente removidos de main.py y console.py.
- CSVs de prueba limpiados de registros duplicados.

## [Ejercicio 06 - Fix 2]
- aplicar_precio_ars agregado a ServicioPrecio.
- menu_precios ahora resuelve la cotización faltante (API o manual) antes de sugerir.
- Opción de aplicar el precio sugerido al libro directamente desde el menú.
