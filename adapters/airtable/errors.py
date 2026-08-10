class AirtableAdapterError(Exception):
    """Error base para el Airtable Adapter."""


class AirtableConfigError(AirtableAdapterError):
    """Configuracion faltante o invalida."""


class AirtableTableError(AirtableAdapterError):
    """Tabla no permitida por el contrato local."""


class AirtableRemoteError(AirtableAdapterError):
    """Error remoto de Airtable."""


class AirtableRateLimitError(AirtableRemoteError):
    """Rate limit agotado tras reintentos."""


class AirtableIdempotencyError(AirtableAdapterError):
    """Conflicto de idempotencia detectado."""
