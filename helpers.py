from solana.transaction import Pubkey


def is_solana_address(input_string: str) -> bool:
    try:
        Pubkey.from_string(input_string)
        return True
    except ValueError:
        return False
