import os
import hashlib
from pathlib import Path

import psycopg
from psycopg import sql
from dotenv import load_dotenv


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

SOURCE_DIR = BASE_DIR / "data/source_sim"

# Define quais tabelas serão carregadas e suas colunas
CSV_TABLES = {
    "customers": [
        "customer_id",
        "first_name",
        "last_name",
        "state",
        "marital_status",
        "gender",
        "created_at",
        "updated_at"
    ],

    "orders": [
        "order_id",
        "customer_id",
        "status",
        "created_at",
        "updated_at",
        "delivered_at"
    ],

    "order_items": [
        "order_id",
        "product_id",
        "quantity",
        "unit_price"
    ],

    "payments": [
        "payment_id",
        "order_id",
        "status",
        "amount",
        "created_at",
        "paid_at",
        "updated_at"
    ]
}


# ============================================================
# HASH DO ARQUIVO
# ============================================================

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(65536)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# INGESTÃO CSV
# ============================================================

def load_csv(conn, table_name, columns):

    csv_path = SOURCE_DIR / f"{table_name}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {csv_path}"
        )

    file_hash = calculate_sha256(csv_path)

    with conn.cursor() as cursor:

        # Registra o arquivo se ainda não foi processado
        cursor.execute(
            """
            INSERT INTO bronze.ingestion_files (
                source_name,
                file_sha256
            )
            VALUES (%s, %s)
            ON CONFLICT (source_name, file_sha256)
            DO NOTHING
            RETURNING ingestion_id
            """,
            (csv_path.name, file_hash)
        )

        result = cursor.fetchone()

        if result is None:
            return False

        # Monta o COPY para a tabela e colunas configuradas
        copy_sql = sql.SQL(
            """
            COPY {} ({})
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE)
            """
        ).format(
            sql.Identifier("bronze", table_name),
            sql.SQL(", ").join(
                sql.Identifier(column)
                for column in columns
            )
        )

        # Envia o CSV ao PostgreSQL
        with cursor.copy(copy_sql) as copy:

            with open(csv_path, "rb") as file:

                while True:
                    chunk = file.read(65536)

                    if not chunk:
                        break

                    copy.write(chunk)

    return True


# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    results = []

    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    ) as conn:

        for table_name, columns in CSV_TABLES.items():

            loaded = load_csv(
                conn=conn,
                table_name=table_name,
                columns=columns
            )

            results.append((table_name, loaded))

    # Só informa sucesso depois do commit da transação
    for table_name, loaded in results:

        if loaded:
            print(f"{table_name}: arquivo carregado.")
        else:
            print(f"{table_name}: arquivo já processado.")


if __name__ == "__main__":
    main()

for table_name, columns in CSV_TABLES.items():
    print("Tabela:", table_name)
    print("Colunas:", columns)