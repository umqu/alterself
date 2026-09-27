

class AlterselfError(Exception):
    pass


class HTTPError(AlterselfError):

    def __init__(self, response, message):
        self.response = response
        self.status: int = getattr(response, "status_code",
                                   getattr(response, "status", 0))
        if isinstance(message, dict):
            self.code: int = message.get("code", 0)
            self.text: str = message.get("message", "unknown")
        else:
            self.code = 0
            self.text = str(message)
        super().__init__(f"HTTP {self.status} / code {self.code}: {self.text}")


class GatewayError(AlterselfError):
    pass


class SessionClosed(GatewayError):

    def __init__(self, socket=None, *, code=None):
        self.code = code or getattr(socket, "close_code", None)
        super().__init__(f"Gateway closed [{self.code}]")


class CommandError(AlterselfError):
    pass


class CheckFailed(CommandError):
    pass


class ConversionFailed(CommandError):
    def __init__(self, converter, original: Exception):
        self.converter = converter
        self.original = original
        super().__init__(f"Converter {converter!r} failed: {original}")


class CommandNotFound(CommandError):
    pass


class MissingArgument(CommandError):
    def __init__(self, param):
        self.param = param
        super().__init__(f"Missing required argument: {param.name}")


class CaptchaChallenge(AlterselfError):

    def __init__(self, sitekey: str, rqdata: str | None = None):
        self.sitekey = sitekey
        self.rqdata = rqdata
        super().__init__("Captcha required — configure a solver.")
