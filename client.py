"""Podbase Open API client."""

from __future__ import annotations

from typing import Any

import httpx

PODBASE_BASE = "https://open-api.podbase.com"


class PodbaseAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class PodbaseClient:
    def __init__(self, api_key: str, *, timeout: float = 30.0):
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key, "Content-Type": "application/json"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{PODBASE_BASE}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(
                method, url, headers=self._headers(), params=params, json=json
            )
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        if resp.status_code >= 400:
            message = data.get("message", resp.text) if isinstance(data, dict) else resp.text
            raise PodbaseAPIError(str(message), status_code=resp.status_code, body=data)
        return data

    async def get_catalog(self) -> Any:
        return await self._request("GET", "/catalog")

    async def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request("POST", "/orders", json=payload)
        return data if isinstance(data, dict) else {"result": data}

    async def get_order(self, order_id: str) -> dict[str, Any]:
        data = await self._request("GET", f"/orders/{order_id}")
        return data if isinstance(data, dict) else {"result": data}
