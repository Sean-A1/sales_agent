from .base import ConversionProfile
from .financial_rfp import financial_rfp

_REGISTRY: dict[str, ConversionProfile] = {
    "financial_rfp": financial_rfp,
}


def get_profile(name: str) -> ConversionProfile:
    """Return a ConversionProfile by name; raise ValueError for unknown names."""
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown conversion profile {name!r}. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]
