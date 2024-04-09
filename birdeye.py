from decimal import Decimal

import requests

from common import PriceInfo, TokenOverview
from config import BIRD_EYE_TOKEN
from constants import MULTI_PRICE_URL
from custom_exceptions import NoPositionsError, InvalidTokens, InvalidSolanaAddress, NO_LIQUDITY
from helpers import is_solana_address


class BirdEyeClient:
    """
    Handler class to assist with all calls to BirdEye API
    """

    @property
    def _headers(self):
        return {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": BIRD_EYE_TOKEN,
        }

    def _make_api_call(self, method: str, query_url: str, *args, **kwargs) -> requests.Response:
        match method.upper():
            case "GET":
                query_method = requests.get
            case "POST":
                query_method = requests.post
            case _:
                raise ValueError(f'Unrecognised method "{method}" passed for query - {query_url}')
        resp = query_method(query_url, *args, headers=self._headers, **kwargs)
        return resp

    def fetch_prices(self, token_addresses: list[str]) -> dict[str, PriceInfo[Decimal, Decimal]]:
        """
        For a list of tokens fetches their prices
        via multi-price API ensuring each token has a price

        Args:
            token_addresses (list[str]): A list of tokens for which to fetch prices

        Returns:
           dict[str, dict[str, PriceInfo[Decimal, Decimal]]: Mapping of token to a named tuple PriceInfo with price and liquidity

        Raises:
            NoPositionsError: Raise if no tokens are provided
            InvalidToken: Raised if the API call was unsuccessful
        """
        if not token_addresses:
            raise NoPositionsError()
        request_url = f"{MULTI_PRICE_URL}?include_liquidity=true&list_address={'%2C'.join(token_addresses)}"
        api_response = self._make_api_call("GET", request_url)
        if api_response.status_code == 200:
            data = api_response.json().get('data', {})
            price_details = {}
            invalid_token_list = []
            for address, details in data.items():
                if "value" in details and "liquidity" in details:
                    price_details[address] = PriceInfo(Decimal(details["value"]), Decimal(details["liquidity"]))
                else:
                    invalid_token_list.append(address)
            if invalid_token_list:
                raise InvalidTokens(invalid_token_list)
            return price_details
        raise InvalidTokens()

    def fetch_token_overview(self, address: str) -> TokenOverview:
        """
        For a token fetches their overview
        via multi-price API ensuring each token has a price

        Args:
            address (str): A token address for which to fetch overview

        Returns:
            dict[str, float | str]: Overview with a lot of token information I don't understand

        Raises:
            InvalidSolanaAddress: Raise if invalid solana address is passed
            InvalidToken: Raised if the API call was unsuccessful
        """
        if not is_solana_address(address):
            raise InvalidSolanaAddress(address)

        request_url = f"{MULTI_PRICE_URL}?include_liquidity=true&include_decimals=true&list_address={address}"
        api_response = self._make_api_call("GET", request_url)
        if api_response.status_code == 200:
            data = api_response.json()["data"]
            token_data = data.get(address, {})

            if not token_data:
                raise InvalidTokens(tokens=[address])

            if not token_data.get("liquidity", None):
                raise ValueError(NO_LIQUDITY)

            return TokenOverview(price=Decimal(token_data.get("value", 0)), symbol=0, decimals=0, lastTradeUnixTime=0,
                                 liquidity=Decimal(token_data.get("liquidity", None)),
                                 supply=0)
        raise InvalidTokens(tokens=[address])
