from fastapi import HTTPException
from datetime import datetime

def validate_schema(df, required_columns):
    """
    df : pandas DataFrame
    required_columns : dict { "column_name": {"type": "int|float|str|date", "required": bool, "rules": [...] } }
    
    Example required_columns:
    {
        "product_id": {"type": "int", "required": True},
        "quantity": {"type": "float", "required": True, "rules": [">=0"]},
        "date": {"type": "date", "required": True, "format": "%Y-%m-%d"},
        "category": {"type": "str", "required": False}
    }
    """
    errors = []

    # -----------------------------
    # 1) Vérification colonnes manquantes
    # -----------------------------
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    # Early abort if columns missing
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # -----------------------------
    # 2) Validation des types + règles métiers
    # -----------------------------
    for col, rules in required_columns.items():
        expected_type = rules.get("type")
        required = rules.get("required", False)

        # Required: no null values
        if required and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values but is required.")

        # ---- TYPE CHECKS ----
        if expected_type == "int":
            if not df[col].dropna().apply(lambda x: isinstance(x, (int, float)) and float(x).is_integer()).all():
                errors.append(f"Column '{col}' must contain only integers.")

        elif expected_type == "float":
            if not df[col].dropna().apply(lambda x: isinstance(x, (int, float))).all():
                errors.append(f"Column '{col}' must contain only numeric values (int/float).")

        elif expected_type == "str":
            if not df[col].dropna().apply(lambda x: isinstance(x, str)).all():
                errors.append(f"Column '{col}' must contain only strings.")

        elif expected_type == "date":
            date_format = rules.get("format", "%Y-%m-%d")
            for idx, value in df[col].dropna().items():
                try:
                    datetime.strptime(str(value), date_format)
                except ValueError:
                    errors.append(
                        f"Column '{col}' has invalid date format at row {idx}: '{value}' "
                        f"(expected format: {date_format})"
                    )

        # -----------------------------
        # 3) Business rule validation 
        # -----------------------------
        if "rules" in rules:
            for rule in rules["rules"]:
                if rule.startswith(">="):
                    val = float(rule.replace(">=", "").strip())
                    if not (df[col] >= val).all():
                        errors.append(f"Column '{col}' must be >= {val}.")
                
                elif rule.startswith(">"):
                    val = float(rule.replace(">", "").strip())
                    if not (df[col] > val).all():
                        errors.append(f"Column '{col}' must be > {val}.")

                elif rule.startswith("<="):
                    val = float(rule.replace("<=", "").strip())
                    if not (df[col] <= val).all():
                        errors.append(f"Column '{col}' must be <= {val}.")

                elif rule.startswith("<"):
                    val = float(rule.replace("<", "").strip())
                    if not (df[col] < val).all():
                        errors.append(f"Column '{col}' must be < {val}.")

                elif rule == "non_empty_str":
                    if df[col].astype(str).str.strip().eq("").any():
                        errors.append(f"Column '{col}' cannot contain empty strings.")

    # -----------------------------
    # 4) Raise errors
    # -----------------------------
    if errors:
        raise HTTPException(status_code=400, detail=errors)
