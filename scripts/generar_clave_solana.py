"""Genera un par de claves Solana para SOLANA_SIGNER_PRIVATE_KEY (solo Devnet/pruebas)."""

from solders.keypair import Keypair


def main() -> None:
    kp = Keypair()
    raw = kp.to_bytes()
    print("Dirección pública (pedir SOL en faucet Devnet con esta):")
    print(kp.pubkey())
    print()
    print("Pegá en .env como SOLANA_SIGNER_PRIVATE_KEY (hex, 64 bytes):")
    print(raw.hex())


if __name__ == "__main__":
    main()
