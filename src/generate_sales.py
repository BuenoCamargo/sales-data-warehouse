import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURAÇÃO
# ============================================================

SEED = 42
NUM_CUSTOMERS = 500
NUM_ORDERS = 2000

SOURCE_SIM_DIR = Path("data/source_sim")
PRODUCTS_RAW_DIR = Path("data/raw/products")

CUSTOMER_SIMULATION_START = datetime(2025, 1, 1)
ORDER_CREATION_END = datetime(2026, 12, 31)


FIRST_NAMES = [
    "Ana", "Beatriz", "Carlos", "Daniel", "Eduardo",
    "Fernanda", "Gabriel", "Helena", "Igor", "Julia",
    "Lucas", "Mariana", "Nicolas", "Olivia", "Pedro",
    "Rafaela", "Samuel", "Tatiana", "Vinicius", "Yasmin",
    "Arthur", "Bianca", "Caio", "Diana", "Enzo",
    "Giovanna", "Heitor", "Isabela", "João", "Laura"
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues",
    "Ferreira", "Alves", "Pereira", "Lima", "Gomez",
    "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida",
    "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
    "Rocha", "Dias", "Nascimento", "Andrade", "Moreira",
    "Nunes", "Marques", "Machado", "Mendes", "Freitas"
]

STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]


# ============================================================
# CUSTOMERS
# ============================================================

def generate_customers(num_customers, seed):
    rng = random.Random(seed)

    customers = []

    for customer_id in range(1, num_customers + 1):

        created_at = CUSTOMER_SIMULATION_START + timedelta(
            days=rng.randint(0, 364)
        )

        customers.append({
            "customer_id": customer_id,
            "first_name": rng.choice(FIRST_NAMES),
            "last_name": rng.choice(LAST_NAMES),
            "state": rng.choice(STATES),
            "marital_status": rng.choice(["M", "S"]),
            "gender": rng.choice(["Male", "Female"]),
            "created_at": created_at,
            "updated_at": created_at,
        })

    return customers


def inject_customer_quality_issues(df, seed):
    df_dirty = df.copy()

    # 5%: estado em minúsculo
    idx = df_dirty.sample(
        frac=0.05,
        random_state=seed
    ).index

    df_dirty.loc[idx, "state"] = (
        df_dirty.loc[idx, "state"].str.lower()
    )

    # 3%: espaços extras no estado
    idx = df_dirty.sample(
        frac=0.03,
        random_state=seed + 1
    ).index

    df_dirty.loc[idx, "state"] = (
        " " + df_dirty.loc[idx, "state"] + " "
    )

    # 2%: marital_status ausente
    idx = df_dirty.sample(
        frac=0.02,
        random_state=seed + 2
    ).index

    df_dirty.loc[idx, "marital_status"] = None

    # 3%: representação alternativa de gender
    idx = df_dirty.sample(
        frac=0.03,
        random_state=seed + 3
    ).index

    df_dirty.loc[idx, "gender"] = (
        df_dirty.loc[idx, "gender"]
        .replace({
            "Male": "M",
            "Female": "F"
        })
    )

    return df_dirty


# ============================================================
# ORDERS
# ============================================================

def generate_orders(num_orders, customer_created_at, seed):
    rng = random.Random(seed)

    customer_ids = list(customer_created_at.keys())
    orders = []

    for order_id in range(1, num_orders + 1):

        customer_id = rng.choice(customer_ids)
        customer_creation = customer_created_at[customer_id]

        max_days = (
            ORDER_CREATION_END - customer_creation
        ).days

        order_created_at = (
            customer_creation
            + timedelta(days=rng.randint(0, max_days))
        )

        status = rng.choice([
            "pending",
            "approved",
            "cancelled"
        ])

        if status == "pending":
            order_updated_at = order_created_at
        else:
            order_updated_at = (
                order_created_at
                + timedelta(days=rng.randint(1, 14))
            )

        # Simplificação da V1:
        # todo pedido approved eventualmente é entregue.
        if status == "approved":
            delivered_at = (
                order_updated_at
                + timedelta(days=rng.randint(1, 10))
            )
        else:
            delivered_at = None

        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "status": status,
            "created_at": order_created_at,
            "updated_at": order_updated_at,
            "delivered_at": delivered_at,
        })

    return orders


def inject_order_quality_issues(df, seed):
    df_dirty = df.copy()

    # 2%: inconsistência no status
    idx = df_dirty.sample(
        frac=0.02,
        random_state=seed
    ).index

    df_dirty.loc[idx, "status"] = (
        df_dirty.loc[idx, "status"]
        .replace({
            "pending": " PENDING ",
            "approved": "Approved",
            "cancelled": "CANCELLED "
        })
    )

    # 1%: updated_at ausente
    idx = df_dirty.sample(
        frac=0.01,
        random_state=seed + 1
    ).index

    df_dirty.loc[idx, "updated_at"] = pd.NaT

    # Formato padrão da fonte
    df_dirty["created_at"] = (
        df_dirty["created_at"]
        .dt.strftime("%Y-%m-%d")
    )

    # 2%: formato de data diferente
    idx = df_dirty.sample(
        frac=0.02,
        random_state=seed + 2
    ).index

    parsed_dates = pd.to_datetime(
        df_dirty.loc[idx, "created_at"]
    )

    df_dirty.loc[idx, "created_at"] = (
        parsed_dates.dt.strftime("%Y%m%d")
    )

    return df_dirty


# ============================================================
# CATÁLOGO DE PRODUTOS
# ============================================================

def get_latest_complete_run_dir(base_dir):
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Diretório RAW não encontrado: {base_dir}"
        )

    run_dirs = sorted(
        [path for path in base_dir.iterdir() if path.is_dir()],
        key=lambda path: path.name,
        reverse=True
    )

    for run_dir in run_dirs:
        manifest_path = run_dir / "manifest.json"

        if not manifest_path.exists():
            continue

        try:
            with open(
                manifest_path,
                "r",
                encoding="utf-8"
            ) as file:
                manifest = json.load(file)

        except (OSError, json.JSONDecodeError):
            continue

        if manifest.get("status") == "complete":
            return run_dir

    raise FileNotFoundError(
        "Nenhum snapshot completo de products foi encontrado."
    )


def load_product_catalog(run_dir):
    product_catalog = {}

    page_files = sorted(
        run_dir.glob("products_skip_*.json")
    )

    if not page_files:
        raise FileNotFoundError(
            f"Nenhuma página de products encontrada em {run_dir}"
        )

    for page_file in page_files:

        with open(
            page_file,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        for product in data["products"]:
            product_catalog[product["id"]] = product["price"]

    # Validação simples contra o manifest
    manifest_path = run_dir / "manifest.json"

    with open(
        manifest_path,
        "r",
        encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    expected_total = manifest["expected_total"]

    if len(product_catalog) != expected_total:
        raise ValueError(
            "Catálogo incompleto: "
            f"esperado={expected_total}, "
            f"encontrado={len(product_catalog)}"
        )

    return product_catalog


# ============================================================
# ORDER ITEMS
# ============================================================

def generate_order_items(orders, product_catalog, seed):

    if not product_catalog:
        raise ValueError(
            "O catálogo de produtos está vazio."
        )

    rng = random.Random(seed)

    product_ids = list(product_catalog.keys())
    order_items = []

    max_products_per_order = min(
        5,
        len(product_ids)
    )

    for order in orders:

        num_products = rng.randint(
            1,
            max_products_per_order
        )

        selected_products = rng.sample(
            product_ids,
            num_products
        )

        for product_id in selected_products:

            order_items.append({
                "order_id": order["order_id"],
                "product_id": product_id,
                "quantity": rng.randint(1, 4),
                "unit_price": product_catalog[product_id],
            })

    return order_items

def build_order_totals_cents(order_items):
    """
    Calcula o valor total de cada pedido em centavos.

    Retorna:
        {
            order_id: total_cents,
            ...
        }
    """
    totals = {}

    for item in order_items:
        order_id = item["order_id"]

        unit_price_cents = round(
            float(item["unit_price"]) * 100
        )

        line_total_cents = (
            unit_price_cents * item["quantity"]
        )

        totals[order_id] = (
            totals.get(order_id, 0)
            + line_total_cents
        )

    return totals


def split_amount_cents(total_cents, num_parts, rng):
    """
    Divide um valor em N parcelas positivas,
    garantindo que a soma seja exatamente o total.
    """
    if num_parts == 1:
        return [total_cents]

    cut_points = sorted(
        rng.sample(
            range(1, total_cents),
            num_parts - 1
        )
    )

    points = [0] + cut_points + [total_cents]

    return [
        points[i + 1] - points[i]
        for i in range(num_parts)
    ]

# ============================================================
# PAYMENTS
# ============================================================
def generate_payments(
    orders,
    order_totals_cents,
    seed
):
    rng = random.Random(seed)

    payments = []
    payment_id = 1

    for order in orders:
        order_id = order["order_id"]
        order_status = order["status"]
        order_created_at = order["created_at"]
        order_updated_at = order["updated_at"]

        total_cents = order_totals_cents[order_id]

        # Evita tentar dividir poucos centavos
        # em parcelas impossíveis.
        max_payments = min(3, total_cents)

        num_payments = rng.randint(
            1,
            max_payments
        )

        amounts_cents = split_amount_cents(
            total_cents,
            num_payments,
            rng
        )

        # ----------------------------------------------------
        # APPROVED
        # Todos os pagamentos estão pagos.
        # Soma paga = valor total do pedido.
        # ----------------------------------------------------
        if order_status == "approved":

            statuses = ["paid"] * num_payments

        # ----------------------------------------------------
        # PENDING
        # Pode existir pagamento parcial,
        # mas pelo menos uma parcela continua pendente.
        # ----------------------------------------------------
        elif order_status == "pending":

            if num_payments == 1:
                statuses = ["pending"]

            else:
                paid_count = rng.randint(
                    0,
                    num_payments - 1
                )

                statuses = (
                    ["paid"] * paid_count
                    + ["pending"]
                    * (num_payments - paid_count)
                )

                rng.shuffle(statuses)

        # ----------------------------------------------------
        # CANCELLED
        # Simplificação V1:
        # representamos o valor como devolvido.
        # ----------------------------------------------------
        else:
            num_payments = 1
            amounts_cents = [total_cents]
            statuses = ["refunded"]

        # ----------------------------------------------------
        # Criação das linhas
        # ----------------------------------------------------

        for amount_cents, payment_status in zip(
            amounts_cents,
            statuses
        ):

            amount = amount_cents / 100

            payment_created_at = (
                order_created_at
                + timedelta(
                    days=rng.randint(0, 1)
                )
            )

            if payment_status == "paid":

                paid_at = payment_created_at + timedelta(
                    days=rng.randint(0, 2)
                )

                payment_updated_at = paid_at

            elif payment_status == "pending":

                paid_at = None
                payment_updated_at = (
                    payment_created_at
                )

            else:  # refunded

                paid_at = payment_created_at + timedelta(
                    days=rng.randint(0, 2)
                )

                # O reembolso/cancelamento acontece
                # posteriormente.
                payment_updated_at = max(
                    paid_at + timedelta(days=1),
                    order_updated_at
                )

            payments.append({
                "payment_id": payment_id,
                "order_id": order_id,
                "status": payment_status,
                "amount": amount,
                "created_at": payment_created_at,
                "paid_at": paid_at,
                "updated_at": payment_updated_at,
            })

            payment_id += 1

    return payments
# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    # ---------- customers ----------

    customers = generate_customers(
        num_customers=NUM_CUSTOMERS,
        seed=SEED
    )

    customer_created_at = {
        customer["customer_id"]: customer["created_at"]
        for customer in customers
    }

    # ---------- orders ----------

    orders = generate_orders(
        num_orders=NUM_ORDERS,
        customer_created_at=customer_created_at,
        seed=SEED
    )

    # ---------- products ----------

    product_run = get_latest_complete_run_dir(
        PRODUCTS_RAW_DIR
    )

    product_catalog = load_product_catalog(
        product_run
    )

    # ---------- order_items ----------

    order_items = generate_order_items(
        orders=orders,
        product_catalog=product_catalog,
        seed=SEED
    )

     # ---------- payments ----------

    order_totals_cents = build_order_totals_cents(
    order_items
    )

    payments = generate_payments(
    orders=orders,
    order_totals_cents=order_totals_cents,
    seed=SEED
    )
    # ---------- DataFrames ----------

    df_customers = pd.DataFrame(customers)
    df_orders = pd.DataFrame(orders)
    df_order_items = pd.DataFrame(order_items)
    df_payments = pd.DataFrame(payments)

    # Sujeira controlada apenas na representação da fonte
    df_customers_source = (
        inject_customer_quality_issues(
            df_customers,
            seed=SEED
        )
    )

    df_orders_source = (
        inject_order_quality_issues(
            df_orders,
            seed=SEED
        )
    )

    # ---------- CSV ----------

    SOURCE_SIM_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df_customers_source.to_csv(
        SOURCE_SIM_DIR / "customers.csv",
        index=False,
        date_format="%Y-%m-%d"
    )

    df_orders_source.to_csv(
        SOURCE_SIM_DIR / "orders.csv",
        index=False,
        date_format="%Y-%m-%d"
    )

    df_order_items.to_csv(
        SOURCE_SIM_DIR / "order_items.csv",
        index=False
    )

    df_payments.to_csv(
    SOURCE_SIM_DIR / "payments.csv",
    index=False,
    date_format="%Y-%m-%d"
    )

    # ---------- resumo ----------

    print(
        f"Snapshot de produtos usado: {product_run.name}"
    )
    print(
        f"Customers: {len(df_customers_source)}"
    )
    print(
        f"Orders: {len(df_orders_source)}"
    )
    print(
        f"Order items: {len(df_order_items)}"
    )
    print(
        f"Products disponíveis: {len(product_catalog)}"
    )
    print(
    f"Payments: {len(df_payments)}"
    )

if __name__ == "__main__":
    main()