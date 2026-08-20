class AriwaLabsError(Exception):
    """Error base tipado del framework AriwaLabs."""


class RequestValidationError(AriwaLabsError, ValueError):
    """El request de entrada no cumple el contrato esperado."""


class AgentNotFoundError(AriwaLabsError, FileNotFoundError):
    """No existe el agente solicitado en el core o business pack activo."""


class WorkflowNotFoundError(AriwaLabsError, FileNotFoundError):
    """No existe el workflow solicitado para el agente."""


class PersistenceError(AriwaLabsError):
    """La persistencia local no pudo completarse o leerse de forma valida."""


class ToolGatewayError(AriwaLabsError):
    """Error base de ejecucion de tools."""


class ToolNotFoundError(ToolGatewayError, KeyError):
    """La tool solicitada no existe en el catalogo."""


class ToolApprovalRequiredError(ToolGatewayError, PermissionError):
    """La tool requiere aprobacion humana antes de ejecutarse."""


class ToolExecutionError(ToolGatewayError):
    """La tool no pudo ejecutarse mediante su handler o adapter."""


class HandoffRuntimeError(AriwaLabsError):
    """Error base de ejecucion de handoffs."""


class HandoffNotFoundError(HandoffRuntimeError, KeyError):
    """No existe el contrato de handoff solicitado."""


class HandoffApprovalRequiredError(HandoffRuntimeError, PermissionError):
    """El handoff requiere aprobacion humana antes de materializarse."""
