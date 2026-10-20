import json
from pathlib import Path
from psycopg.types.json import Jsonb
from dotenv import load_dotenv
import os
import psycopg

BASE_DIR = Path(__file__).resolve().parents[1]

base_raw_dir = BASE_DIR / "data/raw/products"

run_dirs = [
    path
    for path in base_raw_dir.iterdir()
    if path.is_dir()
]

if not run_dirs:
    raise FileNotFoundError(
        "Nenhum snapshot de produtos encontrado."
    )

run_dir = max(run_dirs, key=lambda path: path.name)

print("Snapshot selecionado:", run_dir.name)

with open(run_dir / "manifest.json", encoding="utf-8") as file:
    manifest = json.load(file)

page_files = sorted(
    run_dir.glob("products_skip_*.json")
)

print("Status:", manifest["status"])
print("Páginas esperadas:", manifest["expected_pages"])
print("Páginas encontradas:", len(page_files))

if manifest["status"] != "complete":
    raise ValueError(
        "Snapshot rejeitado: ingestão não concluída."
    )
if manifest["expected_pages"] != len(page_files):
    raise ValueError(
        f"Snapshot incompleto: esperado "
        f"{manifest['expected_pages']} páginas, "
        f"encontradas {len(page_files)}."
    )
def validate_product_ids(pages):
    ids_list = []

    for _, data in pages:
        lista_produtos = data.get("products", [])

        for product in lista_produtos:
            id_product = product.get("id")
            if id_product is None:
                raise ValueError("Foram encontrado(s) ID(s) com campo vazio")
            ids_list.append(id_product)
    if len(ids_list) != len(set(ids_list)):
        raise ValueError("Foram encontrados IDs de produtos duplicados.")

def load_products(conn, run_dir, page_files, expected_total):

    pages = []
    total_products = 0

    # Primeiro, lê e valida todas as páginas
    for page_file in page_files:

        with open(page_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data.get("products"), list):
            raise ValueError(
                f"Página inválida: {page_file.name}"
            )
        
        total_products += len(data["products"])
        pages.append((page_file.name, data))

    validate_product_ids(pages)

    if total_products != expected_total:
        raise ValueError(
            f"Esperados {expected_total} produtos, "
            f"encontrados {total_products}."
        )

    with conn.cursor() as cursor:

        # Verifica se esse snapshot já foi carregado
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM bronze.products_raw
            WHERE run_id = %s
            """,
            (run_dir.name,)
        )

        existing_pages = cursor.fetchone()[0]

        if existing_pages == len(page_files):
            return False

        if existing_pages > 0:
            raise ValueError(
                "Snapshot parcialmente carregado no banco."
            )

        # Insere todas as páginas
        for file_name, data in pages:

            cursor.execute(
                """
                INSERT INTO bronze.products_raw (
                    run_id,
                    file_name,
                    payload
                )
                VALUES (%s, %s, %s)
                """,
                (
                    run_dir.name,
                    file_name,
                    Jsonb(data)
                )
            )

    return True
load_dotenv(BASE_DIR / ".env")

with psycopg.connect(
    host="localhost",
    port=5432,
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"]
) as conn:

    loaded = load_products(
        conn=conn,
        run_dir=run_dir,
        page_files=page_files,
        expected_total=manifest["expected_total"]
    )

if loaded:
    print("Snapshot carregado no PostgreSQL.")
else:
    print("Snapshot já processado.")
