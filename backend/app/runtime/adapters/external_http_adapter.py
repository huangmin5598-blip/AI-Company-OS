# @PRODUCT Adapter — OS Core
"""External HTTP Agent Adapter.

Read-only adapter that proxies health / capabilities / cost queries to a
remote HTTP endpoint.  Execution is hard-disabled — :meth:`execute` always
returns ``{"status": "unsupported", ...}``.

Use for vendor API gateways, remote Hermes / Codex servers, or any
runtime behind an HTTP endpoint that should **not** accept execution
commands from the OS Core in v0.6.
"""
import os
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus, RuntimeSession


# ── Security constants ─────────────────────────────────────────────────

_BLOCKED_SCHEMES = frozenset({"file", "ftp", "ws", "wss"})
"""URL schemes that are never allowed as endpoint URLs."""

_METADATA_IPS = frozenset({"169.254.169.254"})
"""Cloud metadata IPs that are never allowed in endpoint URLs."""


def _validate_endpoint_url(url: str) -> str:
    """Validate *url* against security rules.

    Rules
    -----
    * Only **http** and **https** schemes are accepted.
    * ``http://`` is restricted to ``localhost`` and ``127.0.0.1`` only.
    * ``https://`` is allowed for any hostname.
    * The following are **always blocked**:
      - Schemes ``file``, ``ftp``, ``ws``, ``wss``
      - Cloud metadata IP ``169.254.169.254``

    Raises
    ------
    ValueError
        When the URL violates any of the rules above.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    # Block disallowed schemes outright
    if scheme in _BLOCKED_SCHEMES:
        raise ValueError(
            f"Blocked URL scheme '{scheme}': {url}"
        )

    # Only http / https allowed
    if scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported URL scheme '{scheme}': {url}"
        )

    # Block cloud metadata IP regardless of scheme
    if hostname in _METADATA_IPS:
        raise ValueError(
            f"Blocked metadata IP in endpoint URL: {url}"
        )

    # http:// restricted to loopback addresses only
    if scheme == "http" and hostname not in ("localhost", "127.0.0.1"):
        raise ValueError(
            f"http:// only allowed for localhost / 127.0.0.1, "
            f"got '{hostname}': {url}"
        )

    return url


# ── Adapter ────────────────────────────────────────────────────────────


class ExternalHTTPAgentAdapter(BaseRuntimeAdapter):
    """Adapter for an external (remote) AI runtime via HTTP.

    v0.6 is **read-only**: health, capabilities, and cost queries are
    proxied to the remote endpoint.  Session creation returns a local
    stub, and :meth:`execute` always returns ``unsupported`` — no POST
    is sent to the remote host.

    When the adapter is created with ``enabled=False``,
    :meth:`health_check` short-circuits to :meth:`health_check_local`
    and returns ``ONLINE`` without making any outbound HTTP call.
    """

    def __init__(
        self,
        runtime_id: str,
        display_name: str,
        endpoint: str,
        enabled: bool = True,
        auth_env: Optional[str] = None,
    ):
        _validate_endpoint_url(endpoint)
        super().__init__(runtime_id, display_name, endpoint)
        self._enabled = enabled
        self._auth_env = auth_env

    # ── Metadata properties ────────────────────────────────────────────

    @property
    def runtime_type(self) -> str:
        return "external_http"

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── Internal helpers ───────────────────────────────────────────────

    def _get_auth_header(self) -> Optional[dict[str, str]]:
        """Read a bearer token from the environment variable named by the
        ``auth_env`` configuration value.

        Returns ``None`` (no auth header) when *auth_env* is not set or
        the environment variable is empty / missing.
        """
        if not self._auth_env:
            return None
        token = os.environ.get(self._auth_env)
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    async def _get(self, path: str) -> httpx.Response:
        """Perform an authenticated GET to ``{endpoint}{path}``."""
        headers = self._get_auth_header() or {}
        async with httpx.AsyncClient(timeout=15) as client:
            return await client.get(
                f"{self._endpoint}{path}", headers=headers
            )

    # ── Lifecycle — remote via HTTP ────────────────────────────────────

    async def health_check(self) -> RuntimeStatus:
        """Check remote endpoint reachability.

        Sends a ``GET /health`` to the configured endpoint and interprets
        the JSON response.

        When *enabled* is ``False``, returns :attr:`RuntimeStatus.ONLINE`
        without making any outbound HTTP call — see
        :meth:`health_check_local`.
        """
        if not self._enabled:
            return self.health_check_local()

        try:
            resp = await self._get("/health")
            if resp.status_code == 200:
                data = resp.json()
                remote_status = data.get("status", "online")
                if remote_status == "online":
                    return RuntimeStatus.ONLINE
                if remote_status == "degraded":
                    return RuntimeStatus.DEGRADED
                return RuntimeStatus.ONLINE  # lenient default
            return RuntimeStatus.DEGRADED
        except httpx.ConnectError:
            return RuntimeStatus.OFFLINE
        except httpx.TimeoutException:
            return RuntimeStatus.OFFLINE
        except Exception:
            return RuntimeStatus.UNKNOWN

    def health_check_local(self) -> RuntimeStatus:
        """Local-only health status — always returns ``ONLINE``.

        This method is called by :meth:`health_check` when the adapter
        is configured with ``enabled=False``, allowing the system to see
        a live adapter without making any outbound HTTP calls.
        """
        return RuntimeStatus.ONLINE

    async def get_capabilities(self) -> list[dict]:
        """Fetch capabilities from the remote ``/capabilities`` endpoint.

        Sends a ``GET /capabilities`` — returns the JSON body on success
        or an empty list on any error.
        """
        try:
            resp = await self._get("/capabilities")
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception:
            return []

    # ── Execution — hard-disabled ──────────────────────────────────────

    async def create_session(
        self, goal: str, context: Optional[dict] = None
    ) -> RuntimeSession:
        """Return a stub session — no remote call, no side-effects."""
        import uuid

        return RuntimeSession(
            session_id=f"ext-{uuid.uuid4().hex[:12]}",
            goal=goal,
            context=context,
        )

    async def execute(self, session, command: str, timeout: int = 300) -> dict:
        """Hard-return ``unsupported`` — no POST is sent to the remote.

        This adapter does **not** forward execution commands to the
        remote runtime in v0.6.
        """
        return {
            "status": "unsupported",
            "output": (
                f"External HTTP adapter '{self.name}' does not support "
                f"remote execution via the v0.6 read-only interface."
            ),
            "metadata": {},
        }

    async def cancel_session(self, session_id: str) -> bool:
        """Stub — always returns ``True`` with no remote call."""
        return True

    async def get_cost(self, session_id: str) -> dict:
        """Fetch cost info from the remote ``/cost/{session_id}`` endpoint.

        Sends a ``GET /cost/{session_id}`` — returns the JSON body on
        success or a zeroed-out cost dict on any error.
        """
        try:
            resp = await self._get(f"/cost/{session_id}")
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        return {
            "tokens_in": 0,
            "tokens_out": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "duration_seconds": 0.0,
        }


# ── Factory ────────────────────────────────────────────────────────────


def create_adapter(reg: dict):
    """Factory function for dynamic adapter import.

    Expected keys in *reg*:

    ===========  ======  ================================================
    Key          Req?    Description
    ===========  ======  ================================================
    runtime_id   Yes     Unique runtime identifier.
    display_name Yes     Human-readable display name.
    endpoint     Yes     Remote HTTP(S) endpoint URL.
    enabled      No      Whether the remote is active (default ``True``).
    auth_env     No      Name of env var holding a bearer token.
    ===========  ======  ================================================
    """
    return ExternalHTTPAgentAdapter(
        runtime_id=reg["runtime_id"],
        display_name=reg["display_name"],
        endpoint=reg["endpoint"],
        enabled=reg.get("enabled", True),
        auth_env=reg.get("auth_env"),
    )
