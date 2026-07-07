import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Portal(str, enum.Enum):
    NFSE_NACIONAL = "nfse_nacional"
    NFSE_SP = "nfse_sp"


class CertificateType(str, enum.Enum):
    A1 = "A1"
    A3 = "A3"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class LogLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
