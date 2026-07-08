"""Unit tests for Podbase catalog normalization."""

from app.addons.suppliers.podbase.addon import PodbaseAddon
from app.addons.suppliers.podbase.catalog import normalize_podbase_catalog
from schemas.supplier import POD_INVENTORY_PLACEHOLDER


def test_podbase_catalog_normalization():
    items = normalize_podbase_catalog(
        {
            "products": [
                {
                    "name": "Phone Case",
                    "variants": [
                        {"id": "v1", "sku": "CASE-1", "price": "12.50"},
                    ],
                }
            ]
        }
    )
    assert len(items) == 1
    assert items[0].supplier_product_id == "v1"
    assert items[0].price_cents == 1250
    assert items[0].inventory_quantity == POD_INVENTORY_PLACEHOLDER


def test_podbase_addon_identity():
    assert PodbaseAddon.addon_id == "podbase"
