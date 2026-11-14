"""Provider boundary for the future approved telephony integration.

No concrete provider is supplied: a production caller must implement this interface,
verify signed callbacks and be accepted by the release checklist before activation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCallRef:
    provider_call_id: str


class TelephonyProvider(ABC):
    @abstractmethod
    async def place_outbound_call(self, destination: str, stream_url: str) -> ProviderCallRef: ...

    @abstractmethod
    async def cancel_call(self, provider_call_id: str) -> None: ...

    @abstractmethod
    async def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> dict: ...
