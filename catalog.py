"""Podbase catalog normalization."""

from __future__ import annotations

from typing import Any

from app.addons.suppliers.catalog_utils import decimal_price_to_cents, int_price_to_cents
from schemas.supplier import (
    POD_INVENTORY_PLACEHOLDER,
    SupplierCatalogItem,
    SupplierCatalogProduct,
    SupplierCatalogVariant,
)


def _iter_catalog_rows(catalog: Any) -> list[dict[str, Any]]:
    if isinstance(catalog, list):
        return [r for r in catalog if isinstance(r, dict)]
    if not isinstance(catalog, dict):
        return []
    for key in ("products", "data", "items", "catalog"):
        val = catalog.get(key)
        if isinstance(val, list):
            return [r for r in val if isinstance(r, dict)]
    return []


def normalize_podbase_catalog(catalog: Any) -> list[SupplierCatalogItem]:
    items: list[SupplierCatalogItem] = []
    for product in _iter_catalog_rows(catalog):
        product_name = str(product.get("name") or product.get("title") or "Podbase product")
        variants = product.get("variants")
        if not isinstance(variants, list):
            variant_id = str(product.get("id") or product.get("variantId") or product.get("sku") or "").strip()
            if not variant_id:
                continue
            price = product.get("price") or product.get("retailPrice") or product.get("basePrice")
            price_cents = int_price_to_cents(price) if isinstance(price, int) else decimal_price_to_cents(price)
            sku = str(product.get("sku") or f"podbase-{variant_id}")
            items.append(
                SupplierCatalogItem(
                    external_key=f"podbase:{variant_id}",
                    name=product_name,
                    description=product.get("description"),
                    price_cents=price_cents,
                    sku=sku,
                    image_url=product.get("imageUrl") or product.get("image"),
                    supplier_value="podbase",
                    supplier_product_id=variant_id,
                    supplier_variant_id="",
                    inventory_quantity=POD_INVENTORY_PLACEHOLDER,
                )
            )
            continue
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            variant_id = str(variant.get("id") or variant.get("variantId") or variant.get("sku") or "").strip()
            if not variant_id:
                continue
            name = str(variant.get("name") or variant.get("title") or product_name)
            price = variant.get("price") or variant.get("retailPrice") or product.get("price")
            price_cents = int_price_to_cents(price) if isinstance(price, int) else decimal_price_to_cents(price)
            sku = str(variant.get("sku") or f"podbase-{variant_id}")
            items.append(
                SupplierCatalogItem(
                    external_key=f"podbase:{variant_id}",
                    name=name,
                    description=product.get("description"),
                    price_cents=price_cents,
                    sku=sku,
                    image_url=variant.get("imageUrl") or variant.get("image") or product.get("imageUrl"),
                    supplier_value="podbase",
                    supplier_product_id=variant_id,
                    supplier_variant_id="",
                    inventory_quantity=POD_INVENTORY_PLACEHOLDER,
                )
            )
    return items


def normalize_podbase_catalog_products(catalog: Any) -> list[SupplierCatalogProduct]:
    """Map Podbase catalog rows to grouped catalog products."""
    products: list[SupplierCatalogProduct] = []
    for product in _iter_catalog_rows(catalog):
        parent_id = str(product.get("id") or product.get("productId") or "").strip()
        product_name = str(product.get("name") or product.get("title") or "Podbase product")
        description = product.get("description")
        variants_raw = product.get("variants")
        variants: list[SupplierCatalogVariant] = []

        if not isinstance(variants_raw, list):
            variant_id = str(product.get("id") or product.get("variantId") or product.get("sku") or "").strip()
            if not variant_id:
                continue
            parent_id = parent_id or variant_id
            price = product.get("price") or product.get("retailPrice") or product.get("basePrice")
            price_cents = int_price_to_cents(price) if isinstance(price, int) else decimal_price_to_cents(price)
            image_url = product.get("imageUrl") or product.get("image")
            image_urls = [str(image_url).strip()] if image_url else []
            variants.append(
                SupplierCatalogVariant(
                    external_key=f"podbase:{variant_id}",
                    title=product_name,
                    attributes={},
                    price_cents=price_cents,
                    sku=str(product.get("sku") or f"podbase-{variant_id}"),
                    inventory_quantity=POD_INVENTORY_PLACEHOLDER,
                    supplier_product_id=variant_id,
                    supplier_variant_id="",
                    image_urls=image_urls,
                )
            )
        else:
            if not parent_id:
                continue
            for variant in variants_raw:
                if not isinstance(variant, dict):
                    continue
                variant_id = str(variant.get("id") or variant.get("variantId") or variant.get("sku") or "").strip()
                if not variant_id:
                    continue
                name = str(variant.get("name") or variant.get("title") or product_name)
                price = variant.get("price") or variant.get("retailPrice") or product.get("price")
                price_cents = int_price_to_cents(price) if isinstance(price, int) else decimal_price_to_cents(price)
                image_url = variant.get("imageUrl") or variant.get("image") or product.get("imageUrl")
                image_urls = [str(image_url).strip()] if image_url else []
                variants.append(
                    SupplierCatalogVariant(
                        external_key=f"podbase:{variant_id}",
                        title=name,
                        attributes={},
                        price_cents=price_cents,
                        sku=str(variant.get("sku") or f"podbase-{variant_id}"),
                        inventory_quantity=POD_INVENTORY_PLACEHOLDER,
                        supplier_product_id=variant_id,
                        supplier_variant_id="",
                        image_urls=image_urls,
                    )
                )

        if not variants:
            continue
        product_image_url = product.get("imageUrl") or product.get("image")
        product_images = [str(product_image_url).strip()] if product_image_url else []
        products.append(
            SupplierCatalogProduct(
                external_product_key=f"podbase:{parent_id}",
                name=product_name,
                description=description if isinstance(description, str) else None,
                product_type=None,
                image_urls=product_images,
                image_alt_texts=[],
                variants=variants,
                supplier_value="podbase",
            )
        )
    return products
