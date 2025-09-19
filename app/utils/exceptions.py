class AuthException(Exception):
    pass

class JWTDecodeError(AuthException):
    pass

class AccessTokenRequiredError(AuthException):
    pass

class FreshTokenRequiredError(AuthException):
    pass

class TokenError(AuthException):
    pass

class RefreshTokenRequiredError(TokenError):
    pass

class TokenTypeError(TokenError):
    pass

class MissingTokenError(TokenError):
    pass

class CSRFError(AuthException):
    pass


