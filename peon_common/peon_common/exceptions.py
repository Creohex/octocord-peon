"""Custom exceptions definitions."""


class Error(Exception):
    """Base error."""

    def __init__(self, message=None, *args, **kwargs):
        args = args
        kwargs = kwargs
        message = message.format(*args, **kwargs) if args or kwargs else message

        super(Error, self).__init__(message)

        # if not hasattr(self, "message"):
        #     self.message = message


class CommandError(Error):
    def __init__(self, message=None):
        super().__init__(message)


class CommandMalformed(CommandError):
    def __init__(self, message=None):
        super().__init__(message)


class CommandExecutionError(CommandError):
    def __init__(self, message=None):
        super().__init__(message)


class CommandAccessRestricted(CommandError):
    def __init__(self, message=None):
        super().__init__(message)


class DocumentNotFound(Error):
    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
