import httpx


def main() -> None:
    response = httpx.get("http://localhost:8000/health/live", timeout=5)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()