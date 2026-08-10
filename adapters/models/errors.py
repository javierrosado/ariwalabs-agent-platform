class ModelGatewayError(Exception):
    """Error base del Model Gateway."""


class ModelConfigError(ModelGatewayError):
    """Configuracion de modelos faltante o invalida."""


class ModelProfileError(ModelGatewayError):
    """Perfil logico de modelo no soportado."""


class ModelProviderError(ModelGatewayError):
    """Error devuelto por un proveedor de modelos."""


class ModelOutputError(ModelGatewayError):
    """Salida de modelo invalida para el contrato esperado."""
