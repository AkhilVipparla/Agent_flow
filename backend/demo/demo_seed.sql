-- Sample retail data for the read-only demo database (DEMO_DATABASE_URL).
-- This is a SEPARATE database from the app's own (DATABASE_URL); it holds nothing private.
-- Re-runnable: drops and recreates its own tables. Data is deterministic.

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    country     TEXT NOT NULL,
    segment     TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers (id),
    order_date  DATE NOT NULL,
    status      TEXT NOT NULL
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INT NOT NULL REFERENCES orders (id),
    product_id INT NOT NULL REFERENCES products (id),
    quantity   INT NOT NULL
);

INSERT INTO customers (name, country, segment, signup_date) VALUES
 ('Northwind Traders',   'United States',  'Enterprise', '2024-01-15'),
 ('Contoso Ltd',         'United Kingdom', 'Enterprise', '2024-02-03'),
 ('Fabrikam Inc',        'Germany',        'SMB',        '2024-03-21'),
 ('Tailspin Toys',       'United States',  'SMB',        '2024-04-09'),
 ('Wide World Importers','Australia',      'Enterprise', '2024-05-30'),
 ('Adventure Works',     'Canada',         'SMB',        '2024-06-12'),
 ('Litware Group',       'India',          'Startup',    '2024-07-04'),
 ('Proseware Co',        'France',         'Startup',    '2024-08-18'),
 ('Lucerne Publishing',  'Switzerland',    'SMB',        '2024-09-25'),
 ('Margie''s Travel',    'United States',  'Startup',    '2024-10-11'),
 ('Coho Winery',         'Italy',          'SMB',        '2024-11-02'),
 ('Alpine Ski House',    'Austria',        'Enterprise', '2024-12-19');

INSERT INTO products (name, category, unit_price) VALUES
 ('Analytics Suite',      'Software',  1200.00),
 ('Cloud Storage 1TB',    'Software',   150.00),
 ('Support Plan Gold',    'Services',   800.00),
 ('Onboarding Workshop',  'Services',  2500.00),
 ('Edge Gateway',         'Hardware',   950.00),
 ('Sensor Pack (10)',     'Hardware',   320.00),
 ('API Credits 100k',     'Software',    90.00),
 ('Training Seat',        'Services',   400.00);

-- 60 orders spread over 2025, deterministic via modular arithmetic.
INSERT INTO orders (customer_id, order_date, status)
SELECT 1 + (g * 7) % 12,
       DATE '2025-01-01' + ((g * 5) % 330),
       CASE WHEN g % 11 = 0 THEN 'refunded'
            WHEN g % 7  = 0 THEN 'pending'
            ELSE 'completed' END
FROM generate_series(1, 60) AS g;

-- 140 line items attached to those orders.
INSERT INTO order_items (order_id, product_id, quantity)
SELECT 1 + (g % 60),
       1 + (g * 3) % 8,
       1 + (g % 5)
FROM generate_series(1, 140) AS g;
