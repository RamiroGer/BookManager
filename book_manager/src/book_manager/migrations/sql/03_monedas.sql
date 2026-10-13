INSERT INTO monedas (id, codigo, nombre) VALUES (1, 'ARS', 'Peso Argentino') ON CONFLICT DO NOTHING;
INSERT INTO monedas (id, codigo, nombre) VALUES (2, 'USD', 'Dólar Estadounidense') ON CONFLICT DO NOTHING;
INSERT INTO monedas (id, codigo, nombre) VALUES (3, 'EUR', 'Euro') ON CONFLICT DO NOTHING;
INSERT INTO monedas (id, codigo, nombre) VALUES (4, 'USD', 'Dolar') ON CONFLICT DO NOTHING;
INSERT INTO monedas (id, codigo, nombre) VALUES (5, '0', '0') ON CONFLICT DO NOTHING;
