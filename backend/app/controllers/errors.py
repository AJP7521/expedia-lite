"""Transport-independent controller failures, mapped to HTTP by the API adapter."""


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class AuthenticationError(Exception):
    pass
