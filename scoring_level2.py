from __future__ import annotations

from typing import Any, Dict, List, Optional


# ============================================================
# LEVEL 2 SCORING
# Usa l'output del livello 1 e costruisce score esplorativi.
#
# IMPORTANTE:
# - Questo NON è un motore peer-reviewed diretto.
# - È una sintesi modellistica costruita sopra il livello 1.
# - I pesi sono trasparenti e modificabili.
# ============================================================


def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))


def round2(x: float) -> float:
    return round(float(x), 2)


def normalize_linear(value: Optional[float], vmin: float, vmax: float, invert: bool = False) -> Optional[float]:
    """
    Restituisce un valore 0-100.
    Se invert=True, valori alti diventano rischio più basso.
    """
    if value is None:
        return None

    if vmax == vmin:
        return 0.0

    norm = (float(value) - vmin) / (vmax - vmin)
    norm = max(0.0, min(1.0, norm))

    if invert:
        norm = 1.0 - norm

    return round2(norm * 100.0)


def get_agent_row(agent_predictions: List[Dict[str, Any]], agent_name: str) -> Optional[Dict[str, Any]]:
    for row in agent_predictions:
        if row.get("agent") == agent_name:
            return row
    return None


def compute_pigment_load_score(level1_result: Dict[str, Any]) -> float:
    """
    Misura quanto il paziente si espone complessivamente agli agenti pigmentanti
    quantitativi. Non è un dato di letteratura, è un indicatore interno.
    """
    total_events = 0
    for row in level1_result.get("agent_predictions", []):
        agent = row.get("agent")
        if agent in {"coffee", "tea", "red_wine", "cola"}:
            total_events += int(row.get("events_per_day", 0) or 0)

    wear_days = int(level1_result.get("wear_days", 0) or 0)
    total_exposure_events = total_events * wear_days

    # scala interna semplice
    # 0 eventi = 0
    # 140 eventi o più = 100
    return clamp((total_exposure_events / 140.0) * 100.0)


def compute_smoke_profile(level1_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Il fumo viene trattato come fattore superficiale separato.
    Non genera ΔE numerico se non presente nel livello 1.
    """
    smoke_row = get_agent_row(level1_result.get("agent_predictions", []), "cigarette_smoke")

    cigarettes_per_day = 0
    if smoke_row:
        cigarettes_per_day = int(smoke_row.get("events_per_day", 0) or 0)

    wear_days = int(level1_result.get("wear_days", 0) or 0)
    total_cigarettes = cigarettes_per_day * wear_days

    if total_cigarettes == 0:
        level = "assente"
        score = 0
    elif total_cigarettes <= 70:
        level = "lieve"
        score = 25
    elif total_cigarettes <= 140:
        level = "moderato"
        score = 60
    else:
        level = "elevato"
        score = 85

    note = (
        "Classificazione interna del modello basata su esposizione totale al fumo. "
        "Non rappresenta un ΔE misurato direttamente."
    )

    # Se il livello 1 avesse già un ΔE quantitativo da fumo, lo segnaliamo
    smoke_deltae = None
    if smoke_row:
        smoke_deltae = smoke_row.get("estimated_deltaE", None)

    return {
        "cigarettes_per_day": cigarettes_per_day,
        "wear_days": wear_days,
        "total_cigarettes": total_cigarettes,
        "smoke_surface_risk_level": level,
        "smoke_surface_risk_score": score,
        "smoke_deltaE_if_available": smoke_deltae,
        "note": note,
    }


def compute_staining_score(level1_result: Dict[str, Any], smoke_profile: Dict[str, Any]) -> Dict[str, Any]:
    deltae_total = float(level1_result.get("total_estimated_deltaE_numeric_agents_only", 0.0) or 0.0)
    deltae_norm = normalize_linear(deltae_total, 0.0, 10.0, invert=False) or 0.0

    pigment_load = compute_pigment_load_score(level1_result)
    smoke_score = float(smoke_profile.get("smoke_surface_risk_score", 0.0) or 0.0)

    # focus primario = estetica
    score = (
        deltae_norm * 0.70 +
        pigment_load * 0.20 +
        smoke_score * 0.10
    )

    if score < 25:
        risk_class = "basso"
    elif score < 50:
        risk_class = "moderato"
    elif score < 75:
        risk_class = "moderato-alto"
    else:
        risk_class = "alto"

    return {
        "deltae_total_numeric_agents_only": round2(deltae_total),
        "deltae_norm_0_100": round2(deltae_norm),
        "pigment_load_score": round2(pigment_load),
        "smoke_modifier_score": round2(smoke_score),
        "staining_score": round2(score),
        "staining_risk_class": risk_class,
        "note": (
            "Score esplorativo basato soprattutto su ΔE numerico da agenti quantitativi, "
            "carico pigmentante e contributo superficiale da fumo."
        ),
    }


def compute_mechanical_risk_score(level1_result: Dict[str, Any]) -> Dict[str, Any]:
    mech = level1_result.get("mechanical_profile") or {}

    young = mech.get("young_modulus_MPa", None)
    yield_strength = mech.get("yield_strength_MPa", None)
    stress_decay = mech.get("stress_decay_day15_percent", None)

    # Young e yield alti = minore rischio -> invert=True
    young_score = normalize_linear(young, 500.0, 3000.0, invert=True)
    yield_score = normalize_linear(yield_strength, 20.0, 90.0, invert=True)
    stress_score = normalize_linear(stress_decay, 0.0, 100.0, invert=False)

    available = [x for x in [young_score, yield_score, stress_score] if x is not None]

    if not available:
        return {
            "mechanical_risk_score": None,
            "mechanical_risk_class": "non disponibile",
            "components": {
                "young_modulus_risk": young_score,
                "yield_strength_risk": yield_score,
                "stress_decay_risk": stress_score,
            },
            "note": "Nessun dato meccanico disponibile."
        }

    # stress decay pesa di più
    # se qualche valore manca, ricalcolo sui pesi disponibili
    weights = []
    values = []

    if stress_score is not None:
        weights.append(0.50)
        values.append(stress_score)
    if young_score is not None:
        weights.append(0.25)
        values.append(young_score)
    if yield_score is not None:
        weights.append(0.25)
        values.append(yield_score)

    total_weight = sum(weights)
    score = sum(v * w for v, w in zip(values, weights)) / total_weight

    if score < 25:
        risk_class = "basso"
    elif score < 50:
        risk_class = "moderato"
    elif score < 75:
        risk_class = "moderato-alto"
    else:
        risk_class = "alto"

    return {
        "mechanical_risk_score": round2(score),
        "mechanical_risk_class": risk_class,
        "components": {
            "young_modulus_risk": young_score,
            "yield_strength_risk": yield_score,
            "stress_decay_risk": stress_score,
        },
        "note": (
            "Score esplorativo di vulnerabilità meccanica: aumenta con stress decay elevato "
            "e con valori più bassi di modulo di Young e yield strength."
        ),
    }


def compute_surface_risk_score(level1_result: Dict[str, Any], smoke_profile: Dict[str, Any]) -> Dict[str, Any]:
    surf = level1_result.get("surface_profile") or {}

    thickness_pre = surf.get("thickness_pre_mm", None)
    thickness_post = surf.get("thickness_post_mm", None)
    gap = surf.get("gap_mm", None)

    thickness_loss_pct = None
    if thickness_pre not in (None, 0) and thickness_post is not None:
        thickness_loss_pct = ((float(thickness_pre) - float(thickness_post)) / float(thickness_pre)) * 100.0

    thickness_loss_score = normalize_linear(thickness_loss_pct, 0.0, 40.0, invert=False)
    gap_score = normalize_linear(gap, 0.0, 0.5, invert=False)
    smoke_score = float(smoke_profile.get("smoke_surface_risk_score", 0.0) or 0.0)

    available = [x for x in [thickness_loss_score, gap_score] if x is not None]

    if not available:
        # se non ho dati di thickness/gap, tengo solo il fumo
        score = smoke_score * 0.5
        if score == 0:
            risk_class = "basso"
        elif score < 25:
            risk_class = "moderato"
        elif score < 50:
            risk_class = "moderato-alto"
        else:
            risk_class = "alto"

        return {
            "surface_risk_score": round2(score),
            "surface_risk_class": risk_class,
            "components": {
                "thickness_loss_percent": thickness_loss_pct,
                "thickness_loss_risk": thickness_loss_score,
                "gap_risk": gap_score,
                "smoke_surface_risk": smoke_score,
            },
            "note": (
                "Score superficiale calcolato con dati parziali; thickness/gap mancanti, "
                "peso maggiore del contributo smoke."
            ),
        }

    weights = []
    values = []

    if gap_score is not None:
        weights.append(0.40)
        values.append(gap_score)
    if thickness_loss_score is not None:
        weights.append(0.30)
        values.append(thickness_loss_score)

    # il fumo qui entra come modificatore superficiale separato
    weights.append(0.30)
    values.append(smoke_score)

    total_weight = sum(weights)
    score = sum(v * w for v, w in zip(values, weights)) / total_weight

    if score < 25:
        risk_class = "basso"
    elif score < 50:
        risk_class = "moderato"
    elif score < 75:
        risk_class = "moderato-alto"
    else:
        risk_class = "alto"

    return {
        "surface_risk_score": round2(score),
        "surface_risk_class": risk_class,
        "components": {
            "thickness_loss_percent": round2(thickness_loss_pct) if thickness_loss_pct is not None else None,
            "thickness_loss_risk": thickness_loss_score,
            "gap_risk": gap_score,
            "smoke_surface_risk": smoke_score,
        },
        "note": (
            "Score esplorativo di vulnerabilità superficiale: combina perdita di spessore, "
            "gap e contributo smoke."
        ),
    }


def compute_confidence_score(level1_result: Dict[str, Any]) -> Dict[str, Any]:
    score = 100.0
    penalties = []

    mech_match = level1_result.get("mechanical_profile_match", "none")
    surf_match = level1_result.get("surface_profile_match", "none")

    if mech_match == "polymer_family_proxy":
        score -= 15
        penalties.append("profilo meccanico ottenuto da proxy polymer_family")
    elif mech_match == "none":
        score -= 25
        penalties.append("profilo meccanico assente")

    if surf_match == "polymer_family_proxy":
        score -= 15
        penalties.append("profilo superficiale ottenuto da proxy polymer_family")
    elif surf_match == "none":
        score -= 25
        penalties.append("profilo superficiale assente")

    for row in level1_result.get("agent_predictions", []):
        if row.get("matched_on") == "polymer_family_proxy":
            score -= 5
            penalties.append(f"{row.get('agent')} stimato tramite proxy polymer_family")
        elif row.get("matched_on") == "none":
            score -= 8
            penalties.append(f"{row.get('agent')} senza dato disponibile")

    score = clamp(score, 0.0, 100.0)

    if score >= 85:
        level = "alta"
    elif score >= 65:
        level = "media"
    elif score >= 40:
        level = "medio-bassa"
    else:
        level = "bassa"

    return {
        "confidence_score": round2(score),
        "confidence_level": level,
        "penalties": penalties,
        "note": (
            "Score interno di robustezza del risultato: diminuisce quando il modello usa proxy "
            "o quando mancano dati per alcuni agenti o profili."
        ),
    }


def extract_drivers(
    level1_result: Dict[str, Any],
    staining: Dict[str, Any],
    mechanical: Dict[str, Any],
    surface: Dict[str, Any],
    smoke: Dict[str, Any]
) -> List[str]:
    drivers = []

    deltae_total = float(level1_result.get("total_estimated_deltaE_numeric_agents_only", 0.0) or 0.0)
    if deltae_total >= 3.0:
        drivers.append("ΔE numerico complessivo elevato")

    polymer_family = str(level1_result.get("polymer_family", "") or "")
    if "TPU" in polymer_family.upper():
        drivers.append("materiale appartenente a famiglia TPU")

    smoke_score = float(smoke.get("smoke_surface_risk_score", 0.0) or 0.0)
    if smoke_score >= 60:
        drivers.append("esposizione significativa al fumo come fattore superficiale")

    mech_score = mechanical.get("mechanical_risk_score", None)
    if mech_score is not None and mech_score >= 60:
        drivers.append("profilo meccanico con vulnerabilità aumentata")

    surf_score = surface.get("surface_risk_score", None)
    if surf_score is not None and surf_score >= 60:
        drivers.append("profilo superficiale con suscettibilità aumentata")

    for row in level1_result.get("agent_predictions", []):
        agent = row.get("agent")
        dE = row.get("estimated_deltaE", None)
        if dE is not None and float(dE) >= 2.0:
            drivers.append(f"contributo rilevante di {agent}")

    # dedup mantenendo ordine
    seen = set()
    unique = []
    for d in drivers:
        if d not in seen:
            unique.append(d)
            seen.add(d)

    return unique


def compute_global_risk_score(
    staining: Dict[str, Any],
    mechanical: Dict[str, Any],
    surface: Dict[str, Any]
) -> Dict[str, Any]:
    s1 = staining.get("staining_score", None)
    s2 = mechanical.get("mechanical_risk_score", None)
    s3 = surface.get("surface_risk_score", None)

    weights = []
    values = []

    if s1 is not None:
        weights.append(0.50)
        values.append(float(s1))
    if s2 is not None:
        weights.append(0.25)
        values.append(float(s2))
    if s3 is not None:
        weights.append(0.25)
        values.append(float(s3))

    if not values:
        return {
            "global_risk_score": None,
            "global_risk_class": "non disponibile",
            "note": "Nessun dato sufficiente per score globale."
        }

    total_weight = sum(weights)
    score = sum(v * w for v, w in zip(values, weights)) / total_weight

    if score < 25:
        risk_class = "basso"
    elif score < 50:
        risk_class = "moderato"
    elif score < 75:
        risk_class = "moderato-alto"
    else:
        risk_class = "alto"

    return {
        "global_risk_score": round2(score),
        "global_risk_class": risk_class,
        "note": (
            "Score globale esplorativo che pesa soprattutto la componente estetica "
            "e in misura minore le componenti meccanica e superficiale."
        ),
    }


def build_level2_scores(level1_result: Dict[str, Any]) -> Dict[str, Any]:
    smoke = compute_smoke_profile(level1_result)
    staining = compute_staining_score(level1_result, smoke)
    mechanical = compute_mechanical_risk_score(level1_result)
    surface = compute_surface_risk_score(level1_result, smoke)
    confidence = compute_confidence_score(level1_result)
    global_score = compute_global_risk_score(staining, mechanical, surface)

    drivers = extract_drivers(level1_result, staining, mechanical, surface, smoke)

    return {
        "smoke_profile": smoke,
        "staining_summary": staining,
        "mechanical_summary": mechanical,
        "surface_summary": surface,
        "global_summary": global_score,
        "confidence_summary": confidence,
        "drivers": drivers,
        "level2_notes": [
            "Il livello 2 è una sintesi esplorativa costruita sopra l'output evidence-based del livello 1.",
            "I pesi usati negli score sono interni al modello e modificabili.",
            "Il fumo è trattato principalmente come fattore superficiale separato, non come ΔE numerico obbligatorio.",
            "Lo score globale non sostituisce i dati sperimentali diretti del livello 1."
        ]
    }