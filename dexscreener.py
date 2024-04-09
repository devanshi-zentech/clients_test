"""
Client for DexScreener APIs
"""

from decimal import Decimal
from typing import Any

import requests

from common import PriceInfo, TokenOverview
from constants import SOL_MINT, DEX_SCREENER_TOKEN_URL
from custom_exceptions import (InvalidSolanaAddress, InvalidTokens, NoPositionsError, NO_LIQUDITY,
                               TransactionNotFoundError)
from helpers import is_solana_address


class DexScreenerClient:
    """
    Handler class to assist with all calls to DexScreener API
    """

    @staticmethod
    def _validate_token_address(token_address: str):
        """
        Validates token address to be a valid solana address

        Args:
            token_address (str): Token address to validate

        Returns:
            None: If token address is valid

        Raises:
            NoPositionsError: If token address is empty
            InvalidSolanaAddress: If token address is not a valid solana address
        """
        if not token_address:
            raise NoPositionsError()
        is_valid = is_solana_address(token_address)
        if not is_valid:
            raise InvalidSolanaAddress(token_address)

    def _validate_token_addresses(self, token_addresses: list[str]):
        """
        Validates token addresses to be a valid solana address

        Args:
            token_addresses (list[str]): Token addresses to validate

        Returns:
            None: If token addresses are valid

        Raises:
            NoPositionsError: If token addresses are empty
            InvalidSolanaAddress: If any token address is not a valid solana address
        """
        if not token_addresses:
            raise NoPositionsError()
        for address in token_addresses:
            self._validate_token_address(address)

    @staticmethod
    def _validate_response(resp: requests.Response):
        """
        Validates response from API to be 200

        Args:
            resp (requests.Response): Response from API

        Returns:
            None: If response is 200

        Raises:
            InvalidTokens: If response is not 200
        """
        if resp.status_code != 200:
            raise InvalidTokens()

    def _call_api(self, token_address: str) -> dict[str, Any]:
        """
        Calls DexScreener API for a single token

        Args:
            token_address (str): Token address for which to fetch data

        Returns:
            dict[str, Any]: JSON response from API

        Raises:
            InvalidTokens: If response is not 200
            NoPositionsError: If token address is empty
            InvalidSolanaAddress: If token address is not a valid solana address
        """
        self._validate_token_address(token_address)
        request_url = DEX_SCREENER_TOKEN_URL.format(token_address)
        api_response = requests.get(request_url)
        self._validate_response(api_response)
        return api_response.json()

    def _call_api_bulk(self, token_addresses: list[str]) -> dict[str, Any]:
        """
        Calls DexScreener API for multiple tokens

        Args:
            token_addresses (list[str]): Token addresses for which to fetch data

        Returns:
            dict[str, Any]: JSON response from API

        Raises:
            InvalidTokens: If response is not 200
            NoPositionsError: If token addresses are empty
            InvalidSolanaAddress: If any token address is not a valid solana address
        """
        if not token_addresses:
            raise NoPositionsError()
        self._validate_token_addresses(token_addresses)
        token_addresses_str = ",".join(token_addresses)
        request_url = DEX_SCREENER_TOKEN_URL.format(token_addresses_str)
        api_response = requests.get(request_url)
        self._validate_response(api_response)
        return api_response.json()

    def fetch_prices_dex(self, token_addresses: list[str]) -> dict[str, PriceInfo[Decimal, Decimal]]:
        """
        For a list of tokens fetches their prices
        via multi API ensuring each token has a price

        Args:
            token_addresses (list[str]): A list of tokens for which to fetch prices

        Returns:
           dict[str, dict[Decimal, PriceInfo[str, Decimal]]: Mapping of token to a named tuple PriceInfo with price and liquidity in Decimal

        """
        if not token_addresses:
            raise NoPositionsError()

        prices = {}
        invalid_token_list = []
        for address in token_addresses:
            api_response = self._call_api(token_address=address)
            if api_response.get("pairs"):
                final_data = self.find_largest_pool_with_sol(api_response['pairs'], address)
                liquidity = Decimal(
                    final_data["liquidity"].get("usd", 0)) if "liquidity" in final_data else None

                price = Decimal(final_data.get("priceUsd", 0))
                prices[address] = PriceInfo(price, liquidity)
            else:
                invalid_token_list.append(address)
        if invalid_token_list:
            raise InvalidTokens(invalid_token_list)
        return prices

    def fetch_token_overview(self, address: str) -> TokenOverview:
        """
        For a token fetches their overview
        via Dex API ensuring each token has a price

        Args:
        address (str): A token address for which to fetch overview

        Returns:
        TokenOverview: Overview with a lot of token information I don't understand
        """
        if not is_solana_address(address):
            raise InvalidSolanaAddress(address)

        api_response = self._call_api(token_address=address)
        if api_response.get("pairs"):
            final_data = self.find_largest_pool_with_sol(api_response['pairs'], address)
            liquidity = Decimal(
                final_data["liquidity"].get("usd", 0)) if "liquidity" in final_data else None
            if not liquidity:
                raise ValueError(NO_LIQUDITY)

            price = Decimal(final_data.get("priceUsd", 0))
            symbol = final_data.get("symbol", "")
            decimals = int(final_data.get("decimals", 0))
            lastTradeUnixTime = int(final_data.get("lastTradeUnixTime", 0))
            supply = Decimal(final_data.get("supply", 0))
            return TokenOverview(price=price, symbol=symbol, decimals=decimals, lastTradeUnixTime=lastTradeUnixTime,
                                 liquidity=liquidity, supply=supply)
        raise TransactionNotFoundError()

    @staticmethod
    def find_largest_pool_with_sol(token_pairs, address):
        max_entry = {}
        max_liquidity_usd = -1

        for entry in token_pairs:  # Check if the baseToken address matches the specified address
            if entry.get("baseToken", {}).get("address") == address and entry["quoteToken"]["address"] == SOL_MINT:
                liquidity_usd = float(entry.get("liquidity", {}).get("usd", 0))
                if liquidity_usd > max_liquidity_usd:
                    max_liquidity_usd = liquidity_usd
                    max_entry = entry
        return max_entry
