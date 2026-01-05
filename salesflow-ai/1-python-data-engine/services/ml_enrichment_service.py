from __future__ import annotations

from typing import Dict, Any, Optional

from src.models.dto.java_raw_dto import JavaProductDto


def enrich_ml_result(
    result: Dict[str, Any] | Any,
    product: Optional[JavaProductDto],
) -> Dict[str, Any]:
    """
    Enrichit un résultat ML (forecast ou anomalies) avec les métadonnées produit Java.

    - AUCUN calcul métier
    - AUCUNE dépendance au modèle ML
    - Fonction NON mutante (retourne un nouveau dict)

    Paramètres
    ----------
    result:
        Résultat ML sous forme de dict ou DTO Pydantic (ForecastResult, AnomalyResponse, etc.)
    product:
        JavaProductDto correspondant au produit (None pour forecast GLOBAL)

    Retour
    ------
    dict enrichi, prêt pour l'API / le frontend
    """

    # Support dict OU Pydantic
    if hasattr(result, "model_dump"):
        base: Dict[str, Any] = result.model_dump(by_alias=True)
    elif isinstance(result, dict):
        base = dict(result)  # copie défensive
    else:
        # fallback ultime
        try:
            base = dict(result)
        except Exception:
            base = {}

    # Enrichissement produit (UI context)
    if product:
        base["product"] = {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "price": product.price,
            "description": product.description,
            "imageUrl": product.imageUrl,
        }
    else:
        # Forecast global ou produit non trouvé
        base["product"] = None

    return base
