class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ExternalAPIError(AppError):
    def __init__(self, message: str = "External API request failed", status_code: int = 502):
        super().__init__(message=message, status_code=status_code)

class ResourceNotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)

class ExternalAPIUnavailableError(AppError):
    def __init__(self, message: str = "External API is unavailable"):
        super().__init__(message=message, status_code=503)


class InvalidExternalAPIResponseError(AppError):
    def __init__(self, message: str = "External API returned invalid data"):
        super().__init__(message=message, status_code=502)