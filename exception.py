
class Error(Exception):
    """Базовый класс для других исключений"""
    pass


class ApiKeyMissing(Error):
    """Вызывается когда не получен API ответ"""

    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


class TroubleResponse(Error):
    """Вызывается когда не получен API ответ"""

    def __init__(self, message: object) -> None:
        self.message = message
        super().__init__(self.message)


class TroubleCheckToken(Error):
    """Вызывается когда не получен один из токенов """

    def __init__(self, message="Не получен один из токенов ") -> None:
        self.message = message
        super().__init__(self.message)


class TelegramError(Error):
    """Вызывается когда не получено сообщение """

    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

