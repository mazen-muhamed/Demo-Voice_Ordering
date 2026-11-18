class DomainError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class SessionNotFound(DomainError):
    status_code = 404


class ItemNotFound(DomainError):
    status_code = 404


class InvalidTransition(DomainError):
    status_code = 409


class SessionExpired(DomainError):
    status_code = 410


class InvalidOrder(DomainError):
    status_code = 422
