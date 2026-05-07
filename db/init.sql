CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    order_date  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    region      TEXT NOT NULL,
    total       NUMERIC(10, 2) NOT NULL,
    status      TEXT NOT NULL DEFAULT 'completed'
);

-- Seed data: 50 random orders over the last 14 days
INSERT INTO orders (order_date, region, total, status)
SELECT
    NOW() - (random() * INTERVAL '14 days'),
    (ARRAY['East', 'West', 'North', 'South'])[floor(random() * 4 + 1)::int],
    round((random() * 500 + 50)::numeric, 2),
    'completed'
FROM generate_series(1, 50);
