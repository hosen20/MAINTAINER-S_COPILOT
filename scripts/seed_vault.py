import os

import hvac
from dotenv import load_dotenv

load_dotenv()

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "dev-root-token")
VAULT_MOUNT = os.getenv("VAULT_MOUNT", "secret")
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "maintainers-copilot/local")

client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

if not client.is_authenticated():
    raise RuntimeError("Vault authentication failed")

client.secrets.kv.v2.create_or_update_secret(
    mount_point=VAULT_MOUNT,
    path=VAULT_SECRET_PATH,
    secret={
        "database_password": "local-dev-db-password",
        "jwt_secret": "local-dev-jwt-secret-change-me",
        "minio_access_key": "minioadmin",
        "minio_secret_key": "minioadmin123",
        "llm_api_key": "local-placeholder",
    },
)

print(f"Seeded Vault secret at {VAULT_MOUNT}/{VAULT_SECRET_PATH}")