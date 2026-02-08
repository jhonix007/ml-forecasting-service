class InsufficientBalanceError(Exception):
    """Недостаточно кредитов для списания."""
    pass

class UnauthorizedError(Exception):
    """Недостаточно прав (например, не админ)."""
    pass