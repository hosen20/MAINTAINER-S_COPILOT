from app.domain.errors import InfrastructureError
from app.infra.settings import Settings
from app.infra.vault import VaultClient


def run_boot_checks(settings: Settings) -> None:
    vault = VaultClient(settings)

    if not vault.is_available():
        raise InfrastructureError("Refusing to boot: Vault is unreachable")

    secrets = vault.read_app_secrets()

    if not secrets.jwt_secret:
        raise InfrastructureError("Refusing to boot: missing JWT signing key")

    if settings.chat_state_ttl_seconds <= 0:
        raise InfrastructureError("Refusing to boot: Redis TTL must be positive")