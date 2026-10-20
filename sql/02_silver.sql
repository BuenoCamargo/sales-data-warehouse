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
    source_run_id TEXT NOT NULL
);