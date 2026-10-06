class EmailAlreadyExistsError(Exception):
    """Raised when a user tries to register with an existing email."""
    pass