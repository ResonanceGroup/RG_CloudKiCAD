from typing import Literal, Optional

Role = Literal["admin", "designer", "viewer"]

ROLE_ORDER: dict[Role, int] = {
    "viewer": 1,
    "designer": 2,
    "admin": 3,
}


def normalize_role(value: Optional[str]) -> Optional[Role]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered not in ROLE_ORDER:
        return None
    return lowered  # type: ignore[return-value]


def role_meets_minimum(role: Role, minimum: Role) -> bool:
    return ROLE_ORDER[role] >= ROLE_ORDER[minimum]
