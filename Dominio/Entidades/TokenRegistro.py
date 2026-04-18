from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TokenRegistro:
    id: int
    token: str
    expires_at: datetime
    used: bool
    created_at: datetime

    @staticmethod
    def create(token: str, hours_valid: int = 24) -> 'TokenRegistro':
        return TokenRegistro(
            id=0,
            token=token,
            expires_at=datetime.now() + timedelta(hours=hours_valid),
            used=False,
            created_at=datetime.now()
        )

    def is_valid(self) -> bool:
        return not self.used and datetime.now() < self.expires_at
