-- ===================================================
-- DDL da camada Silver. Criando as tabelas
-- ===================================================

-- ===================================================
-- Criando a Tabela de produtos 
-- ===================================================
CREATE TABLE silver.products (
    product_id INT PRIMARY KEY,
    product_sku TEXT,
    title TEXT NOT NULL,
    brand TEXT,
    product_price NUMERIC(12,2) CHECK (product_price >= 0),
    price_quality TEXT NOT NULL
        CHECK (price_quality IN ('valid', 'missing', 'invalid')),
    product_stock TEXT,
    product_category TEXT,
    availability_status TEXT,
    width_dimension NUMERIC(12,2),
    height_dimension NUMERIC(12,2),
    source_run_id TEXT NOT NULL,
    dwh_create_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- Criando a Tabela de clientes
-- ===================================================
CREATE TABLE silver.customers (
    customer_id INT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    state TEXT,
    marital_status TEXT,
    gender TEXT,
    created_at DATE,
    updated_at DATE,
    dwh_create_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ===================================================
-- Criando a Tabela de itens dos pedidos
-- ===================================================
CREATE TABLE silver.order_items (
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT,
    unit_price NUMERIC(12,2) CHECK (unit_price >= 0),
    dwh_create_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (order_id, product_id)
);
-- ===================================================
-- Criando a Tabela de pedidos
-- ===================================================
CREATE TABLE silver.orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    status TEXT,
    created_at DATE,
    updated_at DATE,
    delivered_at DATE,
    dwh_create_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ===================================================
-- Criando a Tabela de pagamentos
-- ===================================================
CREATE TABLE silver.payments (
    payment_id INT PRIMARY KEY,
    order_id INT,
    status TEXT,
    amount NUMERIC(16,2) CHECK (amount >= 0),
    created_at DATE,
    paid_at DATE,
    updated_at DATE,
    dwh_create_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);