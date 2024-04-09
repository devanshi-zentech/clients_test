# from models.current import gettext
from gettext import gettext


class SoulException(Exception):
    """
    Base custom exception
    to handle any expected errors
    caused by user interaction
    """

    message: str

    def __init__(self, message: str | None = None):
        if message:
            self.message = message


class NoPositionsError(SoulException):
    """
    Raise this when traders
    without any trades
    attempt to trade
    """

    message = (
        "You don't seem to have any positions currently\nIf this is a false positive, please sync wallet and try again"
    )


class InvalidTokens(SoulException):
    """
    Raise this when
    any flow encounters
    invalid tokens
    """

    message = "Invalid tokens obtained while handling the request"

    def __init__(self, tokens: list[str] | None = None):
        if tokens:
            self.message += f" : {tokens}"


class InvalidSolanaAddress(SoulException):
    """
    Raise this when
    any flow encounters
    invalid solana address
    """

    message = "Invalid solana address obtained while handling the request"

    def __init__(self, address: str):
        self.message += f" : {address}"


class DecimalsNotFoundError(SoulException):
    """
    Raise when
    for at least one token
    no decimals are obtained
    after all fallbacks
    """

    message = "Invalid tokens obtained while processing your request.\nIf this is a false positive, please sync wallet and try again"


class TransactionNotFoundError(SoulException):
    """
    Raise when
    transaction data
    does not exist for an address
    """

    message = "Transaction data unavailable.\nPlease sync and try again"


NO_LIQUDITY = gettext("Invalid token address or no liquidity found. If this is a new pair try again in 30 seconds.")
