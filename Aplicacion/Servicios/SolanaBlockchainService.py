import json
import os
import re
from datetime import datetime, timezone

from solana.rpc.api import Client
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction


def _load_signer_keypair(raw: str) -> Keypair:
    """Acepta base58 (Phantom/Solflare), hex de 64 bytes, o JSON array de 64 enteros."""
    s = raw.strip()
    if not s:
        raise ValueError("clave vacía")

    if s.startswith("["):
        arr = json.loads(s)
        if not isinstance(arr, list) or len(arr) != 64:
            raise ValueError("JSON de keypair debe ser un array de 64 enteros")
        return Keypair.from_bytes(bytes(arr))

    hex_candidate = s[2:] if s.startswith("0x") else s
    if re.fullmatch(r"[0-9a-fA-F]{128}", hex_candidate):
        return Keypair.from_bytes(bytes.fromhex(hex_candidate))

    return Keypair.from_base58_string(s)


class BlockchainConfigError(Exception):
    """Error de configuración para la conexión con Solana."""


class BlockchainWriteError(Exception):
    """Error al registrar datos en blockchain."""


class SolanaBlockchainService:
    """Registra evidencias de credenciales en Solana usando el programa Memo."""

    MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    def __init__(self):
        rpc_url = (
            os.getenv("ALCHEMY_SOLANA_RPC_URL")
            or os.getenv("SOLANA_RPC_URL")
            or ""
        ).strip()
        signer_private_key = (os.getenv("SOLANA_SIGNER_PRIVATE_KEY") or "").strip()

        if not rpc_url:
            raise BlockchainConfigError(
                "No se configuró ALCHEMY_SOLANA_RPC_URL en variables de entorno."
            )
        if not signer_private_key:
            raise BlockchainConfigError(
                "No se configuró SOLANA_SIGNER_PRIVATE_KEY para firmar transacciones."
            )

        try:
            self._signer = _load_signer_keypair(signer_private_key)
        except Exception as exc:
            raise BlockchainConfigError(
                "SOLANA_SIGNER_PRIVATE_KEY inválida. Use base58 (Phantom), "
                "hex de 128 caracteres (64 bytes), o JSON [byte,...] de 64 enteros."
            ) from exc

        self._client = Client(rpc_url)
        self._memo_program_id = Pubkey.from_string(self.MEMO_PROGRAM_ID)

    def registrar_password_hash(
        self,
        username: str,
        password_commitment: str,
        salt_hex: str,
        role: str,
    ) -> str:
        """Escribe en cadena la evidencia hash+saltar del registro."""
        balance_lamports = self._client.get_balance(self._signer.pubkey()).value
        if balance_lamports <= 0:
            raise BlockchainWriteError(
                "La wallet firmante no tiene SOL en Devnet. "
                f"Dirección: {self._signer.pubkey()} "
                "Solicita airdrop en faucet.solana.com y vuelve a intentar."
            )

        payload = {
            "app": "historias_admision",
            "event": "user_password_registered",
            "u": username,
            "r": role,
            "s": salt_hex,
            "h": password_commitment,
            "t": datetime.now(timezone.utc).isoformat(),
        }
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        instruction = Instruction(self._memo_program_id, data, [])

        try:
            latest = self._client.get_latest_blockhash()
            recent_blockhash = latest.value.blockhash
            tx = Transaction.new_signed_with_payer(
                [instruction],
                self._signer.pubkey(),
                [self._signer],
                recent_blockhash,
            )
            response = self._client.send_transaction(tx)
            return str(response.value)
        except Exception as exc:
            raise BlockchainWriteError(
                f"No se pudo registrar el hash en Solana: {exc}"
            ) from exc
