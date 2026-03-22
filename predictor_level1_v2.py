from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math
import pandas as pd


# ============================================================
# LEVEL 1 PREDICTOR
# Evidence-based core:
# - direct brand match first
# - if missing, fallback to polymer_family evidence
# - smoking is accepted as input, but a numeric estimate is only
#   produced if quantitative rows exist in staining_evidence_v2.csv
#
# IMPORTANT:
# The mapping "consumption event -> seconds of contact" is NOT a
# peer-reviewed constant for aligners. It is a transparent model
# parameter for standardization in the webapp.
# ============================================================

DEFAULT_EXPOSURE_SECONDS = {
    "coffee": 30,
    "tea": 45,
    "red_wine": 90,
    "cola": 60,
    "cigarette_smoke": 300,  # model parameter only
}


@dataclass
class UserHabits:
    material_brand: str
    wear_days: int
    coffee_per_day: int = 0
    tea_per_day: int = 0
    red_wine_per_day: int = 0
    cola_per_day: int = 0
    cigarettes_per_day: int = 0


def classify_deltae(deltae: float) -> str:
    if deltae < 1.2:
        return "non percepibile / minima"
    if deltae < 2.7:
        return "lieve"
    if deltae < 3.3:
        return "percepibile"
    if deltae < 5.0:
        return "marcata"
    return "molto marcata"


def round2(x: float) -> float:
    return round(float(x), 2)


class EvidenceDB:
    def __init__(self, data_dir: str = "."):
        base = Path(data_dir)
        self.materials = pd.read_csv(base / "materials_master_v2.csv")
        self.staining = pd.read_csv(base / "staining_evidence_v2.csv")
        self.mechanical = pd.read_csv(base / "mechanical_evidence_v2.csv")
        self.surface = pd.read_csv(base / "thermoforming_fit_surface_v2.csv")

        for df in [self.materials, self.staining, self.mechanical, self.surface]:
            if "brand" in df.columns:
                df["brand_norm"] = df["brand"].astype(str).str.strip().str.lower()
            if "polymer_family" in df.columns:
                df["polymer_family_norm"] = df["polymer_family"].astype(str).str.strip().str.lower()

        self.staining["agent_norm"] = self.staining["agent"].astype(str).str.strip().str.lower()

    def list_available_brands(self) -> List[str]:
        return sorted(self.materials["brand"].dropna().unique().tolist())

    def get_material(self, brand: str) -> Optional[pd.Series]:
        rows = self.materials[self.materials["brand_norm"] == brand.strip().lower()]
        if rows.empty:
            return None
        return rows.iloc[0]

    def get_brand_polymer(self, brand: str) -> Optional[str]:
        row = self.get_material(brand)
        return None if row is None else row.get("polymer")

    def get_brand_polymer_family(self, brand: str) -> Optional[str]:
        row = self.get_material(brand)
        return None if row is None else row.get("polymer_family")

    def get_staining_rows(self, brand: str, agent: str) -> Tuple[pd.DataFrame, str]:
        brand_norm = brand.strip().lower()
        agent_norm = agent.strip().lower()

        direct = self.staining[
            (self.staining["brand_norm"] == brand_norm) &
            (self.staining["agent_norm"] == agent_norm)
        ].copy()
        if not direct.empty:
            return direct, "brand"

        fam = self.get_brand_polymer_family(brand)
        if fam:
            fam_norm = str(fam).strip().lower()
            proxy = self.staining[
                (self.staining["polymer_family_norm"] == fam_norm) &
                (self.staining["agent_norm"] == agent_norm)
            ].copy()
            if not proxy.empty:
                return proxy, "polymer_family_proxy"

        return pd.DataFrame(), "none"

    def get_mechanical_profile(self, brand: str) -> Tuple[Optional[dict], str]:
        brand_norm = brand.strip().lower()
        rows = self.mechanical[self.mechanical["brand_norm"] == brand_norm]
        if not rows.empty:
            return rows.iloc[0].to_dict(), "brand"

        fam = self.get_brand_polymer_family(brand)
        if fam:
            fam_norm = str(fam).strip().lower()
            rows = self.mechanical[self.mechanical["polymer_family_norm"] == fam_norm]
            if not rows.empty:
                # polymer-family proxy: choose the first available row,
                # but report clearly that it is a proxy
                return rows.iloc[0].to_dict(), "polymer_family_proxy"

        return None, "none"

    def get_surface_profile(self, brand: str) -> Tuple[Optional[dict], str]:
        brand_norm = brand.strip().lower()
        rows = self.surface[self.surface["brand_norm"] == brand_norm]
        if not rows.empty:
            return rows.iloc[0].to_dict(), "brand"

        fam = self.get_brand_polymer_family(brand)
        if fam:
            fam_norm = str(fam).strip().lower()
            rows = self.surface[self.surface["polymer_family_norm"] == fam_norm]
            if not rows.empty:
                return rows.iloc[0].to_dict(), "polymer_family_proxy"

        return None, "none"


class Level1Predictor:
    def __init__(self, db: EvidenceDB, exposure_seconds: Optional[Dict[str, int]] = None):
        self.db = db
        self.exposure_seconds = exposure_seconds or DEFAULT_EXPOSURE_SECONDS

    def compute_total_exposure_hours(self, events_per_day: int, wear_days: int, seconds_per_event: int) -> float:
        return (events_per_day * wear_days * seconds_per_event) / 3600.0

    def estimate_agent(self, brand: str, agent: str, events_per_day: int, wear_days: int) -> dict:
        seconds_per_event = self.exposure_seconds.get(agent, 0)
        target_hours = self.compute_total_exposure_hours(events_per_day, wear_days, seconds_per_event)
        rows, matched_on = self.db.get_staining_rows(brand, agent)

        if rows.empty:
            return {
                "agent": agent,
                "events_per_day": events_per_day,
                "seconds_per_event": seconds_per_event,
                "total_exposure_hours": round2(target_hours),
                "estimated_deltaE": None,
                "severity": "nessun dato disponibile",
                "matched_on": matched_on,
                "sources_used": [],
                "note": "Nessuna evidenza quantitativa disponibile nel dataset per questo agente."
            }

        quant = rows[rows["quantitative"] == True].dropna(subset=["deltaE", "exposure_hours"]).copy()
        if quant.empty:
            return {
                "agent": agent,
                "events_per_day": events_per_day,
                "seconds_per_event": seconds_per_event,
                "total_exposure_hours": round2(target_hours),
                "estimated_deltaE": None,
                "severity": "evidenza solo qualitativa",
                "matched_on": matched_on,
                "sources_used": rows.to_dict(orient="records"),
                "note": "Esiste evidenza qualitativa, ma nel dataset non è presente un valore ΔE quantitativo utilizzabile."
            }

        quant["deltaE"] = quant["deltaE"].astype(float)
        quant["exposure_hours"] = quant["exposure_hours"].astype(float)
        quant = quant.sort_values("exposure_hours")

        xs = quant["exposure_hours"].tolist()
        ys = quant["deltaE"].tolist()

        if len(xs) == 1:
            ref_x, ref_y = xs[0], ys[0]
            est = ref_y * min(target_hours / ref_x, 1.0) if ref_x > 0 else ref_y
        else:
            if target_hours <= xs[0]:
                est = ys[0] * (target_hours / xs[0]) if xs[0] > 0 else ys[0]
            elif target_hours >= xs[-1]:
                est = ys[-1]
            else:
                est = ys[-1]
                for i in range(len(xs) - 1):
                    x1, x2 = xs[i], xs[i + 1]
                    y1, y2 = ys[i], ys[i + 1]
                    if x1 <= target_hours <= x2:
                        t = (target_hours - x1) / (x2 - x1)
                        est = y1 + t * (y2 - y1)
                        break

        return {
            "agent": agent,
            "events_per_day": events_per_day,
            "seconds_per_event": seconds_per_event,
            "total_exposure_hours": round2(target_hours),
            "estimated_deltaE": round2(est),
            "severity": classify_deltae(est),
            "matched_on": matched_on,
            "sources_used": quant.to_dict(orient="records"),
            "note": "Stima numerica ottenuta da dati quantitativi presenti nel dataset."
        }

    def predict(self, habits: UserHabits) -> dict:
        material = self.db.get_material(habits.material_brand)
        if material is None:
            raise ValueError(f"Materiale non presente nel dataset: {habits.material_brand}")

        per_agent = [
            self.estimate_agent(habits.material_brand, "coffee", habits.coffee_per_day, habits.wear_days),
            self.estimate_agent(habits.material_brand, "tea", habits.tea_per_day, habits.wear_days),
            self.estimate_agent(habits.material_brand, "red_wine", habits.red_wine_per_day, habits.wear_days),
            self.estimate_agent(habits.material_brand, "cola", habits.cola_per_day, habits.wear_days),
            self.estimate_agent(habits.material_brand, "cigarette_smoke", habits.cigarettes_per_day, habits.wear_days),
        ]

        total_delta = sum(x["estimated_deltaE"] for x in per_agent if x["estimated_deltaE"] is not None)

        mech, mech_match = self.db.get_mechanical_profile(habits.material_brand)
        surf, surf_match = self.db.get_surface_profile(habits.material_brand)

        return {
            "material_brand": habits.material_brand,
            "polymer": material["polymer"],
            "polymer_family": material["polymer_family"],
            "structure": material["structure"],
            "wear_days": habits.wear_days,
            "agent_predictions": per_agent,
            "total_estimated_deltaE_numeric_agents_only": round2(total_delta),
            "total_severity_numeric_agents_only": classify_deltae(total_delta),
            "mechanical_profile": mech,
            "mechanical_profile_match": mech_match,
            "surface_profile": surf,
            "surface_profile_match": surf_match,
            "model_notes": [
                "Il motore usa prima il brand; se mancano dati, usa un proxy basato sulla polymer_family.",
                "La polymer_family proxy NON equivale a una misura diretta del brand richiesto.",
                "Il fumo di sigaretta è accettato come input; la stima numerica viene prodotta solo se esistono valori ΔE quantitativi nel dataset.",
                "La conversione consumo -> secondi/evento è una parametrizzazione interna del modello, non una costante peer-reviewed per gli aligner."
            ]
        }


def ask_int(prompt: str, min_value: int = 0, max_value: int = 100) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if min_value <= val <= max_value:
                return val
            print(f"Inserisci un numero tra {min_value} e {max_value}.")
        except ValueError:
            print("Inserisci un intero valido.")


def choose_brand(db: EvidenceDB) -> str:
    brands = db.list_available_brands()
    print("\nMateriali disponibili:")
    for i, b in enumerate(brands, 1):
        print(f"{i}. {b}")
    idx = ask_int("\nScegli il numero del materiale: ", 1, len(brands))
    return brands[idx - 1]


def main():
    db = EvidenceDB(".")
    predictor = Level1Predictor(db)

    brand = choose_brand(db)
    wear_days = ask_int("Giorni di utilizzo dell'aligner: ", 1, 30)
    coffee = ask_int("Caffè al giorno: ", 0, 20)
    tea = ask_int("Tè al giorno: ", 0, 20)
    wine = ask_int("Calici di vino rosso al giorno: ", 0, 20)
    cola = ask_int("Bibite tipo cola al giorno: ", 0, 20)
    smoking = ask_int("Sigarette al giorno: ", 0, 60)

    habits = UserHabits(
        material_brand=brand,
        wear_days=wear_days,
        coffee_per_day=coffee,
        tea_per_day=tea,
        red_wine_per_day=wine,
        cola_per_day=cola,
        cigarettes_per_day=smoking,
    )

    result = predictor.predict(habits)

    print("\n" + "=" * 72)
    print("RISULTATO")
    print("=" * 72)
    print(f"Materiale: {result['material_brand']}")
    print(f"Polimero: {result['polymer']}")
    print(f"Famiglia polimerica: {result['polymer_family']}")
    print(f"Struttura: {result['structure']}")
    print(f"Giorni di utilizzo: {result['wear_days']}")
    print(f"ΔE totale (solo agenti con dato quantitativo): {result['total_estimated_deltaE_numeric_agents_only']}")
    print(f"Classe: {result['total_severity_numeric_agents_only']}")

    print("\nDettaglio per agente")
    for row in result["agent_predictions"]:
        print("-" * 50)
        print(f"Agente: {row['agent']}")
        print(f"Eventi/giorno: {row['events_per_day']}")
        print(f"Secondi/evento: {row['seconds_per_event']}")
        print(f"Ore di esposizione standardizzate: {row['total_exposure_hours']}")
        print(f"ΔE stimato: {row['estimated_deltaE']}")
        print(f"Classe: {row['severity']}")
        print(f"Match: {row['matched_on']}")
        print(f"Nota: {row['note']}")

    print("\nProfilo meccanico:")
    print(result["mechanical_profile"])
    print(f"Match meccanico: {result['mechanical_profile_match']}")

    print("\nProfilo superficie/termoformatura:")
    print(result["surface_profile"])
    print(f"Match superficie: {result['surface_profile_match']}")

    print("\nNote modello:")
    for note in result["model_notes"]:
        print(f"- {note}")


if __name__ == "__main__":
    main()
