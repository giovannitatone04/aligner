from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ============================================================
# LEVEL 2 SCORING — v3
#
# NOTA METODOLOGICA:
# Questi score NON sono metriche peer-reviewed. Sono sintesi
# interne costruite su dati quantitativi del livello 1.
# I pesi sono documentati in SCORING_WEIGHTS.
# ============================================================

SCORING_WEIGHTS = {
    "staining_deltae_norm_weight": 0.70,
    "staining_pigment_load_weight": 0.20,
    "staining_smoke_weight": 0.10,
    "global_staining_weight": 0.50,
    "global_mechanical_weight": 0.25,
    "global_surface_weight": 0.25,
    "mech_stress_decay_weight": 0.50,
    "mech_young_weight": 0.25,
    "mech_yield_weight": 0.25,
    "surf_gap_weight": 0.40,
    "surf_thickness_loss_weight": 0.30,
    "surf_smoke_weight": 0.30,
}

# Intervalli derivati da Albertini et al. 2022
MECH_RANGES = {
    "young_modulus_MPa":          {"min": 500.0,  "max": 3000.0},
    "yield_strength_MPa":         {"min": 20.0,   "max": 90.0},
    "stress_decay_day15_percent": {"min": 0.0,    "max": 100.0},
}

DELTAE_SEVERE_THRESHOLD = 10.0
PIGMENT_LOAD_SATURATION = 140.0
SMOKE_THRESHOLDS = {"lieve": 70, "moderato": 140}
SMOKE_SCORES = {"assente": 0, "lieve": 25, "moderato": 60, "elevato": 85}


def clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, value))


def round2(x: float) -> float:
    return round(float(x), 2)


def _is_missing(v) -> bool:
    if v is None:
        return True
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return True


def normalize_linear(value, vmin, vmax, invert=False):
    if _is_missing(value):
        return None
    if vmax == vmin:
        return 0.0
    norm = clamp((float(value) - vmin) / (vmax - vmin))
    if invert:
        norm = 1.0 - norm
    return round2(norm * 100.0)


def weighted_mean(values, weights):
    paired = [(v, w) for v, w in zip(values, weights) if v is not None]
    if not paired:
        return None
    total_w = sum(w for _, w in paired)
    return round2(sum(v * w for v, w in paired) / total_w)


def risk_class_from_score(score):
    if score is None:
        return "non disponibile"
    if score < 25:
        return "basso"
    if score < 50:
        return "moderato"
    if score < 75:
        return "moderato-alto"
    return "alto"


def get_agent_row(agent_predictions, agent_name):
    for row in agent_predictions:
        if row.get("agent") == agent_name:
            return row
    return None


def compute_smoke_profile(level1_result):
    smoke_row = get_agent_row(level1_result.get("agent_predictions", []), "cigarette_smoke")
    cigarettes_per_day = int((smoke_row or {}).get("events_per_day", 0) or 0)
    wear_days = int(level1_result.get("wear_days", 0) or 0)
    total_cigarettes = cigarettes_per_day * wear_days

    if total_cigarettes == 0:
        level = "assente"
    elif total_cigarettes <= SMOKE_THRESHOLDS["lieve"]:
        level = "lieve"
    elif total_cigarettes <= SMOKE_THRESHOLDS["moderato"]:
        level = "moderato"
    else:
        level = "elevato"

    smoke_deltae = (smoke_row or {}).get("estimated_deltaE", None)

    return {
        "cigarettes_per_day": cigarettes_per_day,
        "wear_days": wear_days,
        "total_cigarettes": total_cigarettes,
        "smoke_surface_risk_level": level,
        "smoke_surface_risk_score": SMOKE_SCORES[level],
        "smoke_deltaE_if_available": smoke_deltae,
        "note": "Stima del rischio superficiale da fumo in base al numero di sigarette quotidiane. La variazione di colore non è quantificata numericamente nei dati disponibili.",
    }


def compute_pigment_load_score(level1_result):
    quantitative_agents = {"coffee", "tea", "red_wine", "cola"}
    total_events = sum(
        int(row.get("events_per_day", 0) or 0)
        for row in level1_result.get("agent_predictions", [])
        if row.get("agent") in quantitative_agents
    )
    wear_days = int(level1_result.get("wear_days", 0) or 0)
    return clamp((total_events * wear_days / PIGMENT_LOAD_SATURATION) * 100.0)


def compute_staining_score(level1_result, smoke_profile):
    """
    ΔE combinato via norma euclidea (L2).

    Rationale: gli agenti pigmentanti agiscono sullo stesso substrato
    (superficie dell'aligner); la somma lineare sovrastima l'effetto
    combinato. La norma L2 produce un capping naturale e cresce
    sublinearmente con il numero di agenti attivi, che è fisicamente
    più plausibile (Sharma et al. 2005 per proprietà dello spazio CIELAB).
    """
    agent_preds = level1_result.get("agent_predictions", [])
    quantitative_agents = {"coffee", "tea", "red_wine", "cola"}

    deltae_values = [
        float(row["estimated_deltaE"])
        for row in agent_preds
        if row.get("agent") in quantitative_agents and row.get("estimated_deltaE") is not None
    ]
    smoke_de = smoke_profile.get("smoke_deltaE_if_available")
    if smoke_de is not None:
        deltae_values.append(float(smoke_de))

    n_quantitative_agents = len(deltae_values)
    deltae_euclidean = math.sqrt(sum(d ** 2 for d in deltae_values)) if deltae_values else 0.0
    deltae_linear = sum(deltae_values)

    deltae_norm = clamp(normalize_linear(deltae_euclidean, 0.0, DELTAE_SEVERE_THRESHOLD) or 0.0)
    pigment_load = compute_pigment_load_score(level1_result)
    smoke_score = float(smoke_profile.get("smoke_surface_risk_score", 0.0) or 0.0)

    score = clamp(
        deltae_norm * SCORING_WEIGHTS["staining_deltae_norm_weight"]
        + pigment_load * SCORING_WEIGHTS["staining_pigment_load_weight"]
        + smoke_score * SCORING_WEIGHTS["staining_smoke_weight"]
    )

    return {
        "deltae_euclidean": round2(deltae_euclidean),
        "deltae_linear_legacy": round2(deltae_linear),
        "deltae_norm_0_100": round2(deltae_norm),
        "n_quantitative_agents": n_quantitative_agents,
        "pigment_load_score": round2(pigment_load),
        "smoke_modifier_score": round2(smoke_score),
        "staining_score": round2(score),
        "staining_risk_class": risk_class_from_score(score),
        "note": (
            "Stima della variazione di colore complessiva: considera l'intensità degli agenti coloranti (70%), "
            "la frequenza di esposizione (20%) e il rischio da fumo (10%)."
        ),
    }


def compute_mechanical_risk_score(level1_result):
    mech = level1_result.get("mechanical_profile") or {}
    young = mech.get("young_modulus_MPa", None)
    yield_s = mech.get("yield_strength_MPa", None)
    stress_decay = mech.get("stress_decay_day15_percent", None)

    young_score = normalize_linear(young, MECH_RANGES["young_modulus_MPa"]["min"], MECH_RANGES["young_modulus_MPa"]["max"], invert=True)
    yield_score = normalize_linear(yield_s, MECH_RANGES["yield_strength_MPa"]["min"], MECH_RANGES["yield_strength_MPa"]["max"], invert=True)
    stress_score = normalize_linear(stress_decay, MECH_RANGES["stress_decay_day15_percent"]["min"], MECH_RANGES["stress_decay_day15_percent"]["max"], invert=False)

    score = weighted_mean(
        [stress_score, young_score, yield_score],
        [SCORING_WEIGHTS["mech_stress_decay_weight"], SCORING_WEIGHTS["mech_young_weight"], SCORING_WEIGHTS["mech_yield_weight"]],
    )

    return {
        "mechanical_risk_score": score,
        "mechanical_risk_class": risk_class_from_score(score),
        "components": {
            "young_modulus_risk": young_score,
            "yield_strength_risk": yield_score,
            "stress_decay_risk": stress_score,
        },
        "note": "Stima della vulnerabilità meccanica basata su rilassamento della forza, rigidità e resistenza del materiale (dati da Albertini et al. 2022).",
    }


def compute_surface_risk_score(level1_result, smoke_profile):
    surf = level1_result.get("surface_profile") or {}
    thickness_pre = surf.get("thickness_pre_mm", None)
    thickness_post = surf.get("thickness_post_mm", None)
    gap = surf.get("gap_mm", None)

    thickness_loss_pct = None
    if not _is_missing(thickness_pre) and float(thickness_pre) != 0 and not _is_missing(thickness_post):
        thickness_loss_pct = ((float(thickness_pre) - float(thickness_post)) / float(thickness_pre)) * 100.0

    thickness_loss_score = normalize_linear(thickness_loss_pct, 0.0, 40.0, invert=False)
    gap_score = normalize_linear(gap, 0.0, 0.5, invert=False)
    smoke_score = float(smoke_profile.get("smoke_surface_risk_score", 0.0) or 0.0)

    has_surface_data = gap_score is not None or thickness_loss_score is not None

    if not has_surface_data:
        score = round2(smoke_score * 0.5) if smoke_score else 0.0
    else:
        score = weighted_mean(
            [gap_score, thickness_loss_score, smoke_score],
            [SCORING_WEIGHTS["surf_gap_weight"], SCORING_WEIGHTS["surf_thickness_loss_weight"], SCORING_WEIGHTS["surf_smoke_weight"]],
        )

    return {
        "surface_risk_score": score,
        "surface_risk_class": risk_class_from_score(score),
        "components": {
            "thickness_loss_percent": round2(thickness_loss_pct) if thickness_loss_pct is not None else None,
            "thickness_loss_risk": thickness_loss_score,
            "gap_risk": gap_score,
            "smoke_surface_risk": smoke_score,
        },
        "has_surface_data": has_surface_data,
        "note": "Stima dell'integrità superficiale: considera adattamento alla dentizione, riduzione di spessore e rischio da fumo. Se i dati di spessore non sono disponibili, il calcolo usa solo il contributo del fumo.",
    }


def compute_confidence_score(level1_result):
    score = 100.0
    penalties = []

    for label, match in [("meccanico", level1_result.get("mechanical_profile_match", "none")),
                          ("superficiale", level1_result.get("surface_profile_match", "none"))]:
        if match == "polymer_family_proxy":
            score -= 15
            penalties.append(f"profilo {label} da proxy polymer_family (-15)")
        elif match == "none":
            score -= 25
            penalties.append(f"profilo {label} assente (-25)")

    for row in level1_result.get("agent_predictions", []):
        agent = row.get("agent")
        if agent == "cigarette_smoke":
            continue
        match = row.get("matched_on", "none")
        if match == "polymer_family_proxy":
            score -= 5
            penalties.append(f"{agent}: dato stimato per analogia (-5 punti)")
        elif match == "none":
            score -= 8
            penalties.append(f"{agent}: nessun dato disponibile (-8 punti)")

    n_quantitative = sum(
        1 for row in level1_result.get("agent_predictions", [])
        if row.get("estimated_deltaE") is not None and row.get("agent") != "cigarette_smoke"
    )
    if n_quantitative < 2:
        score -= 10
        penalties.append(f"dati cromatici insufficienti: solo {n_quantitative} agente/i con misura diretta (-10 punti)")

    score = clamp(score, 0.0, 100.0)
    level = "alta" if score >= 85 else "media" if score >= 65 else "medio-bassa" if score >= 40 else "bassa"

    return {
        "confidence_score": round2(score),
        "confidence_level": level,
        "penalties": penalties,
        "note": "Indica quanto le stime si basino su dati reali: si riduce se i dati del materiale specifico sono assenti o stimati per analogia con altri materiali.",
    }


def extract_drivers(level1_result, staining, mechanical, surface, smoke):
    drivers = []
    deltae_euc = float(staining.get("deltae_euclidean", 0.0) or 0.0)
    if deltae_euc >= 3.0:
        drivers.append(f"Variazione di colore elevata: {round2(deltae_euc)}")
    polymer_family = str(level1_result.get("polymer_family", "") or "")
    if "TPU" in polymer_family.upper():
        drivers.append("materiale TPU: famiglia ad alta suscettibilità estetica nei dati disponibili")
    smoke_score = float(smoke.get("smoke_surface_risk_score", 0.0) or 0.0)
    if smoke_score >= 60:
        drivers.append("esposizione significativa al fumo come fattore superficiale")
    mech_score = mechanical.get("mechanical_risk_score")
    if mech_score is not None and mech_score >= 60:
        drivers.append(f"vulnerabilità meccanica elevata (score {round2(mech_score)})")
    surf_score = surface.get("surface_risk_score")
    if surf_score is not None and surf_score >= 60:
        drivers.append(f"suscettibilità superficiale elevata (score {round2(surf_score)})")
    for row in level1_result.get("agent_predictions", []):
        dE = row.get("estimated_deltaE")
        if dE is not None and float(dE) >= 2.0:
            drivers.append(f"contributo rilevante di {row.get('agent')} (variazione colore: {round2(float(dE))})")
    seen: set = set()
    return [d for d in drivers if not (seen.add(d) or d in seen - {d})]  # type: ignore


def compute_global_risk_score(staining, mechanical, surface):
    score = weighted_mean(
        [staining.get("staining_score"), mechanical.get("mechanical_risk_score"), surface.get("surface_risk_score")],
        [SCORING_WEIGHTS["global_staining_weight"], SCORING_WEIGHTS["global_mechanical_weight"], SCORING_WEIGHTS["global_surface_weight"]],
    )
    return {
        "global_risk_score": score,
        "global_risk_class": risk_class_from_score(score),
        "note": "Punteggio complessivo che combina rischio cromatico (50%), meccanico (25%) e superficiale (25%). I pesi vengono ricalibrati automaticamente se alcuni dati sono assenti.",
    }


def build_level2_scores(level1_result):
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
            "I punteggi riassumono in valori da 0 a 100 le stime basate sulla letteratura scientifica.",
            "La variazione di colore è calcolata combinando tutti gli agenti con un metodo conservativo (somma in quadratura).",
            "I criteri di calcolo sono consultabili nella pagina Fonti.",
            "Il fumo incide sul rischio superficiale; la sua variazione di colore non è quantificata numericamente nei dati attuali.",
            "L'affidabilità si riduce quando i dati del materiale specifico sono assenti o stimati per analogia.",
        ],
    }
