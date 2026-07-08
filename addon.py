"""Podbase print-on-demand supplier integration."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

from app.addons.suppliers.base import SupplierAddon
from app.addons.suppliers.podbase.catalog import (
    normalize_podbase_catalog,
    normalize_podbase_catalog_products,
)
from app.addons.suppliers.podbase.client import PodbaseAPIError, PodbaseClient
from schemas.supplier import SupplierCatalogProduct
from app.addons.log import info, warning
from app.addons.config_serialization import dump_addon_config


class PodbaseConfig(BaseModel):
    api_key: SecretStr = Field(default=..., description="Podbase API key")
    is_active: bool = Field(default=False, description="Whether the addon is active")

    @classmethod
    def config_model(cls):
        return cls


def _map_shipping(address: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "firstName": address.get("first_name", ""),
        "lastName": address.get("last_name", ""),
        "email": address.get("email", ""),
        "address1": address.get("line1", ""),
        "city": address.get("city", ""),
        "state": address.get("state", ""),
        "zip": address.get("zip", ""),
        "country": address.get("country", ""),
        "phone": address.get("phone", ""),
    }


class PodbaseAddon(SupplierAddon):
    addon_id: str = "podbase"
    addon_name: str = "Podbase"
    addon_description: str = "Print-on-demand tech accessories via Podbase Open API."
    addon_category: str = "supplier"
    version: str = "1.0.0"

    _config: Dict[str, Any] | None = None
    _client: PodbaseClient | None = None

    @classmethod
    def config_schema(cls):
        return PodbaseConfig

    async def initialize(self, config: dict) -> None:
        validated = PodbaseConfig(**config)
        self._config = dump_addon_config(validated)
        self._client = PodbaseClient(validated.api_key.get_secret_value())
        self.is_enabled = validated.is_active
        info("Podbase", "Initialized")

    async def validate_config(self, config: dict) -> None:
        from app.core.exceptions import ValidationError

        validated = PodbaseConfig(**config)
        api_key = validated.api_key.get_secret_value()
        if not api_key:
            return
        client = PodbaseClient(api_key)
        try:
            await client.get_catalog()
        except PodbaseAPIError as exc:
            if exc.status_code == 401:
                raise ValidationError(message="Invalid API key — check your credentials") from exc
            if exc.status_code == 403:
                raise ValidationError(
                    message="API key is valid but missing required permissions: catalog:read"
                ) from exc
            raise ValidationError(message=f"Podbase API error: {exc}") from exc

    async def shutdown(self) -> None:
        self._client = None
        self._config = None
        self.is_enabled = False

    def _require_client(self) -> PodbaseClient:
        if self._client is None:
            raise PodbaseAPIError("Podbase addon is not initialized")
        return self._client

    async def list_products(self, **kwargs: Any) -> List[Dict[str, Any]]:
        catalog = await self._require_client().get_catalog()
        items = normalize_podbase_catalog(catalog)
        return [
            {
                "id": item.supplier_product_id,
                "name": item.name,
                "sku": item.sku,
                "price_cents": item.price_cents,
                "image_url": item.image_url,
            }
            for item in items
            if not item.skip_reason
        ]

    async def fetch_catalog_for_import(self, **kwargs: Any) -> List[SupplierCatalogProduct]:
        catalog = await self._require_client().get_catalog()
        return normalize_podbase_catalog_products(catalog)

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        for row in await self.list_products():
            if str(row.get("id") or "") == product_id:
                return row
        return {"error": f"Podbase variant '{product_id}' not found in catalog"}

    async def create_order(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        *,
        external_id: str | None = None,
        supplier_ref: str | None = None,
    ) -> Dict[str, Any]:
        del supplier_ref
        client = self._require_client()
        try:
            line_items = []
            for item in items:
                variant_id = str(item.get("supplier_product_id") or "").strip()
                if not variant_id:
                    continue
                line_items.append(
                    {
                        "variantId": variant_id,
                        "quantity": int(item.get("quantity") or 1),
                    }
                )
            if not line_items:
                return {"success": False, "error": "No valid Podbase line items"}

            payload: Dict[str, Any] = {
                "items": line_items,
                "shippingAddress": _map_shipping(shipping_address),
            }
            if external_id:
                payload["externalOrderId"] = external_id

            data = await client.create_order(payload)
            order_id = str(data.get("orderId") or data.get("id") or "")
            return {
                "success": True,
                "order_id": order_id,
                "status": data.get("status", "submitted"),
                "podbase_order_id": order_id,
            }
        except PodbaseAPIError as exc:
            warning("Podbase", "create_order error: {}", exc)
            return {"success": False, "error": str(exc)}

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            data = await self._require_client().get_order(order_id)
            return {
                "order_id": order_id,
                "status": data.get("status", "unknown"),
            }
        except PodbaseAPIError as exc:
            return {"order_id": order_id, "status": "error", "detail": str(exc)}

    async def sync_inventory(self) -> None:
        products = await self.list_products()
        info("Podbase", "Catalog has {} sellable variants", len(products))

    def get_routers(self) -> List[APIRouter]:
        from app.addons.suppliers.podbase.routes import api_router

        return [api_router]

    def get_admin_routes(self) -> List[APIRouter]:
        from app.addons.suppliers.podbase.routes import admin_router

        return [admin_router]

    def get_admin_templates(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "templates")

    def get_admin_static(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "static")
