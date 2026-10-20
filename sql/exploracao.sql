SELECT
    COUNT(*) AS total_paginas,
    SUM(
        jsonb_array_length(payload -> 'products')
    ) AS total_produtos
FROM bronze.products_raw;