import json

import httpx


BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{BASE_URL}/market/health")
        print("HEALTH:", health.status_code, health.text)

        shortlist = client.get(
            f"{BASE_URL}/market/shortlist",
            params={"quote_asset": "USDT", "limit": 5},
        )
        print("SHORTLIST STATUS:", shortlist.status_code)

        data = shortlist.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()