"""Transport-independent controller failures, mapped to HTTP by the API adapter."""


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class ProviderError(Exception):
    """A provider could not complete a request; messages must be credential-free."""


class ConfigurationError(ProviderError):
    """A required provider configuration value is missing."""
