"""
SelectiveDisclosure — reveal specific fields from ZK proofs.

⚠️ PLACEHOLDER: Needs ZK circuit integration.
"""


class SelectiveDisclosure:
    """Control which data to disclose from ZK proofs."""

    def __init__(self, disclosed_fields: list[str] | None = None) -> None:
        self._disclosed_fields = disclosed_fields or []

    @property
    def disclosed_fields(self) -> list[str]:
        """List of fields to disclose."""
        return self._disclosed_fields
