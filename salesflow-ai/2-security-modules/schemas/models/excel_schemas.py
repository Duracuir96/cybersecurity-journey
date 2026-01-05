"""
Schema definitions for Excel/CSV uploads.

ONLY static schema definitions.
NO logic. NO Java calls.
"""

# ============================================================
# SALES IMPORT SCHEMA (INPUT ONLY)
# ============================================================

REQUIRED_SALES_SCHEMA = {
    "__rules__": {
        # At least ONE of these fields must be present per row
        "one_of": [
            ["product_id", "sku", "name"]
        ]
    },

    "product_id": {
        "type": "int",
        "required": False,
        "description": "Java Product.id (optional if sku or name provided)"
    },

    "sku": {
        "type": "str",
        "required": False,
        "description": "Product SKU (used to resolve productId)"
    },

    "name": {
        "type": "str",
        "required": False,
        "description": "Product name (used to resolve productId if sku/id missing)"
    },

    "quantity": {
        "type": "float",
        "required": True,
        "rules": [">0"],
        "description": "Quantity sold (must be > 0)"
    },

    "sale_date": {
        "type": "date",
        "required": True,
        "format": "%Y-%m-%d",
        "description": "Sale date (validated, NOT sent to Java)"
    },

    "unit_price": {
        "type": "float",
        "required": False,
        "rules": [">=0"],
        "description": "Optional override (ignored in MVP)"
    }
}
