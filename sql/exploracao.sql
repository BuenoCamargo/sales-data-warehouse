INSERT INTO silver.products(
    product_id,
    product_sku,
    title,
    brand,
    product_price,
    price_quality,
    product_category,
    product_stock,
    availability_status,
    width_dimension, 
    height_dimension,
    source_run_id
)
SELECT 
    (p.value->>'id')::INT AS product_id,
    p.value->>'sku' AS product_sku,
    p.value->>'title' AS title,
    p.value->>'brand' AS brand,
    CASE
    WHEN (p.value->>'price') ~ '^[0-9]+(\.[0-9]+)?$'
        THEN (p.value->>'price')::NUMERIC(12,2)
    ELSE NULL
    END AS product_price,
    CASE
    WHEN NULLIF(BTRIM(p.value->>'price'), '') IS NULL
        THEN 'missing'
    WHEN (p.value->>'price') !~ '^[0-9]+(\.[0-9]+)?$'
        THEN 'invalid'
    ELSE 'valid'
    END AS price_quality,
    (p.value->>'stock')::INT AS product_stock,
    p.value->>'category' AS product_category,
    p.value->>'availabilityStatus' AS availability_status,
    (p.value->'dimensions'->>'width')::NUMERIC(12,2) AS width_dimension,
    (p.value->'dimensions'->>'height')::NUMERIC(12,2) AS height_dimension,
    b.run_id AS source_run_id
FROM bronze.products_raw b
CROSS JOIN LATERAL
    jsonb_array_elements(b.payload->'products') AS p(value)
WHERE b.run_id = '20261005_084631_705983'

ON CONFLICT (product_id) DO NOTHING;