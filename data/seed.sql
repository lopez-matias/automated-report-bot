CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_date TIMESTAMP NOT NULL,
    region VARCHAR(50) NOT NULL,
    total NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed'
);

INSERT INTO orders (order_date, region, total, status) VALUES
('2025-04-28 09:15:00', 'North', 1250.00, 'completed'),
('2025-04-28 10:30:00', 'South', 890.50, 'completed'),
('2025-04-28 11:00:00', 'East',  2100.00, 'completed'),
('2025-04-29 08:45:00', 'West',  450.75, 'completed'),
('2025-04-29 09:20:00', 'North', 3200.00, 'completed'),
('2025-04-30 10:10:00', 'South', 760.00, 'completed'),
('2025-04-30 14:00:00', 'East',  1890.50, 'completed'),
('2025-05-01 09:00:00', 'West',  990.00, 'completed'),
('2025-05-01 11:30:00', 'North', 2450.00, 'completed'),
('2025-05-02 10:00:00', 'South', 1100.00, 'completed'),
('2025-05-02 13:15:00', 'East',  3300.00, 'completed'),
('2025-05-03 09:45:00', 'West',  670.25, 'completed'),
('2025-05-03 15:00:00', 'North', 1800.00, 'completed'),
('2025-05-04 08:30:00', 'South', 540.00, 'completed'),
('2025-05-04 12:00:00', 'East',  2750.00, 'completed'),
('2025-05-05 10:20:00', 'West',  1340.00, 'completed'),
('2025-05-05 16:00:00', 'North', 4100.00, 'completed'),
('2025-05-06 09:10:00', 'South', 980.00, 'completed'),
('2025-05-06 11:45:00', 'East',  1650.00, 'completed'),
('2025-05-07 08:00:00', 'West',  2200.00, 'completed');
