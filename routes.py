"""Podbase addon routes."""

from app.addons.suppliers.shared_routes import build_supplier_routers, parse_standard_api_key_form

admin_router, api_router, _env = build_supplier_routers(
    "podbase",
    template_name="config.html",
    page_title="Podbase",
    parse_config_form=parse_standard_api_key_form,
)
