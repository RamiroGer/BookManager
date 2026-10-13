INSERT INTO cotizaciones (id, tipo_id, fecha, valor_compra, valor_venta) VALUES (1, 1, '2026-09-30', 1490.0, 1540.0) ON CONFLICT DO NOTHING;
INSERT INTO cotizaciones (id, tipo_id, fecha, valor_compra, valor_venta) VALUES (2, 2, '2026-09-30', 1540.0, 1560.0) ON CONFLICT DO NOTHING;
