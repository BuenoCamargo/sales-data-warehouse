-- ===================================================
-- DDL da camada Silver. Criando as tabelas
-- ===================================================

-- ===================================================
-- Criando a Tabela de produtos 
-- ===================================================
CREATE TABLE silver.products (
    product_id INT PRIMARY KEY,
    sku TEXT,
    title TEXT NOT NULL,
    category TEXT,
    price NUMERIC(12,2) CHECK (price >= 0),
    price_quality TEXT NOT NULL
        CHECK (price_quality IN ('valid', 'missing', 'invalid')),
    source_run_id TEXT NOT NULL,
    dwh_create_date DATETIME2, DEFAULT GETDATE()
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
    dwh_create_date DATETIME2, DEFAULT GETDATE()
);
-- ===================================================
-- Criando a Tabela de itens dos pedidos
-- ===================================================
CREATE TABLE silver.order_itens (
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT CHECK (quantity >= 0),
    unit_price NUMERIC(12,2) CHECK (unit_price >= 0),
    dwh_create_date DATETIME2, DEFAULT GETDATE()
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
    dwh_create_date DATETIME2, DEFAULT GETDATE()
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
    dwh_create_date DATETIME2, DEFAULT GETDATE()
);