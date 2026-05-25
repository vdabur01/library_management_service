import grpc


class LibraryError(Exception):
    def __init__(self, code: grpc.StatusCode, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(LibraryError):
    def __init__(self, message: str):
        super().__init__(grpc.StatusCode.NOT_FOUND, message)


class ConflictError(LibraryError):
    def __init__(self, message: str):
        super().__init__(grpc.StatusCode.ALREADY_EXISTS, message)


class ValidationError(LibraryError):
    def __init__(self, message: str):
        super().__init__(grpc.StatusCode.INVALID_ARGUMENT, message)
