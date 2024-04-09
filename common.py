from collections import namedtuple

PriceInfo = namedtuple("PriceInfo", ["value", "liquidity"])
TokenOverview = namedtuple("TokenOverview", ["price", "symbol", "decimals", "lastTradeUnixTime", "liquidity", "supply"])
