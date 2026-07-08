# Podbase (`podbase`)

Print-on-demand tech accessories via Podbase Open API.

## Overview

| | |
|---|---|
| Addon ID | `podbase` |
| Category | supplier |
| Version | 1.0.0 |
| Category guide | [../README.md](../README.md) |
| Fulfillment key | `podbase` |

Multiple suppliers can be enabled at the same time. Fulfillment runs when an order becomes **paid**.

## Enable and configure

1. Install this package under `app/addons/suppliers/podbase/`
2. Open **Admin → Suppliers → Podbase** at `/admin/suppliers/podbase`
3. Enter API credentials and enable the addon

## Configuration schema

| Field | Type | Description |
|-------|------|-------------|
| `api_key` | secret | Podbase API key |
| `is_active` | bool | Whether the addon is active |

## Routes

### Public API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/suppliers/podbase/products` | List catalog products |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/suppliers/podbase` | Config form |
| POST | `/admin/suppliers/podbase/save` | Save config |
| POST | `/admin/suppliers/podbase/sync` | Trigger catalog sync |

## Core integration

- **Variant supplier fields:** paid-order fulfillment reads Podbase variant IDs from each **ProductVariant** row
- **Fulfillment:** creates Podbase order via Open API
- **Grouping:** line items grouped by fulfillment key `podbase`

## Variant supplier fields

| Field | Description |
|-------|-------------|
| `supplier_addon_id` | `podbase` |
| `supplier_product_id` | Podbase variant id |

## Catalog sync

Supported. Admin sync at `/admin/suppliers/podbase` or `POST /api/v1/admin/suppliers/podbase/sync`.

**Import model:** grouped products from the Podbase catalog; one variant per sellable unit.

| Key | Format |
|-----|--------|
| Variant dedup key | `podbase:{variantId}` |

**Prerequisites:**

- Products and variants are normalized from the Podbase catalog API.

## Provider setup

- Obtain API key from Podbase.

## Package layout

```
podbase/
├── README.md
├── addon.py
├── catalog.py
├── client.py
├── routes.py
└── templates/
```

## See also

- [Supplier addon development](../README.md)
- [Oshkelosh addon guide](../../README.md)
