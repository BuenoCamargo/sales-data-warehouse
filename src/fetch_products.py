import requests
import math
from pathlib import Path
from datetime import datetime
import json
import time

URL = "https://dummyjson.com/products"

def fetch_page(skip, limit=None, get_function=requests.get, sleep_function=time.sleep):
    params = {"skip": skip}
    if limit is not None:
        params["limit"] = limit
    
    for attempt in range(1,4):
        try:
            response = get_function(URL, params=params, timeout=10)
            response.raise_for_status()

             
            return response
        except requests.exceptions.Timeout:
            if attempt == 3:
                raise
            else:
                sleep_function(attempt)
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 503 and attempt != 3:
                sleep_function(attempt)
                continue

            if error.response.status_code == 429 and attempt != 3:
                retry_after = error.response.headers.get("Retry-After")
                if retry_after:
                    sleep_function(int(retry_after))
                else:
                    sleep_function(attempt)
                continue

            raise

def save_raw_page(response, run_dir, current_skip):
    output_path = run_dir / f"products_skip_{current_skip:03d}.json"

    with open(output_path, mode="w", encoding="utf-8") as file:
        file.write(response.text)

def save_manifest(run_dir, manifest):
    manifest_path = run_dir / "manifest.json"
    with open(manifest_path, mode="w", encoding="utf-8") as file_manifest:
            json.dump(manifest, file_manifest, indent=2)

def fetch_all_products(run_dir, timestamp):
    current_skip = 0
    all_products = []

    manifest = {
        "status": "running",
        "started_at": timestamp,
        "expected_total": None,
        "expected_pages": None,
        "received_pages": 0
    }
    save_manifest(run_dir, manifest)

    try:
        response = fetch_page(current_skip)
        save_raw_page(response, run_dir, current_skip)
        manifest["received_pages"] = 1

        first_page = response.json()
        total = first_page["total"]
        limit = first_page["limit"]
        all_products = first_page["products"]
        num_pages = math.ceil(total / limit)

        manifest.update({
            "expected_total": total,
            "expected_pages": num_pages
        })
        save_manifest(run_dir, manifest)

        for page_number in range(1, num_pages):
            current_skip = page_number * limit

            response = fetch_page(current_skip, limit)
            save_raw_page(response, run_dir, current_skip)

            manifest["received_pages"] += 1
            save_manifest(run_dir, manifest)

            data = response.json()
            product_list = data["products"]
            all_products.extend(product_list)

        manifest["status"] = "complete"
        save_manifest(run_dir, manifest)

    except Exception as error:
        manifest.update({
            "status": "failed",
            "failed_skip": current_skip,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "failed_at": datetime.now().isoformat(timespec="seconds")
        })
        save_manifest(run_dir, manifest)
        raise

    return all_products

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = Path(f"data/raw/products/{timestamp}")
    run_dir.mkdir(parents=True) 

    products = fetch_all_products(run_dir, timestamp)

    print(len(products))
    print(products[0]["id"])
    print(products[-1]["id"])
