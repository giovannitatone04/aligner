import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ============================================================
# CONFIGURAZIONE DEL MODELLO
# ============================================================

# NOTA:
# questi tempi per "consumo" NON derivano direttamente dagli studi
# di immersione sugli aligner; sono parametri espliciti del modello.
# Tienili modificabili e dichiarali sempre come standardizzazione interna.
DEFAULT_EXPOSURE_SECONDS = {
    "coffee": 30,      # 1 tazzina / 1 consumo
    "tea": 45,         # 1 tazza / 1 consumo
    "red_wine": 90,    # 1 calice / 1 consumo
    "cola": 60,        # 1 lattina/bicchiere / 1 consumo
}

# Soglie orientative su ΔE
# Le soglie clinico-percettive variano in letteratura;
# qui usiamo una classificazione semplice e trasparente.
def classify_deltae(deltae: float) -> str:
    if deltae < 1.2:
        return "non percepibile / minima"
    elif deltae < 2.7:
        return "lieve"
    elif deltae < 3.3:
        return "percepibile"
    elif deltae < 5.0:
        return "marcata"
    else:
        return "molto marcata"


# ============================================================
# STRUTTURE DATI
# ============================================================

@dataclass
class UserHabits:
    material_brand: str
    wear_days: int
    coffee_per_day: int = 0
    tea_per_day: int = 0
    red_wine_per_day: int = 0
    cola_per_day: int = 0


@dataclass
class AgentPrediction:
    agent: str
    events_per_day: int
    seconds_per_event: int
    total_exposure_hours: float
    estimated_deltae: float
    severity: str
    matched_on: str
    source_rows: List[dict]


@dataclass
class MechanicalProfile:
    brand: str
    polymer: Optional[str]
    young_modulus_MPa: Optional[float]
    yield_strength_MPa: Optional[float]
    time_window: Optional[str]
    stress_decay_percent: Optional[float]
    source: Optional[str]


@dataclass
class SurfaceProfile:
    brand: str
    polymer: Optional[str]
    thickness_pre_mm: Optional[float]
    thickness_post_mm: Optional[float]
    region: Optional[str]
    gap_mm: Optional[float]
    source: Optional[str]


# ============================================================
# UTILITÀ
# ============================================================

def parse_exposure_time_to_hours(text: str) -> Optional[float]:
    """
    Converte stringhe tipo:
    '12 h', '24h', '7 days', '14 days'
    in ore.
    """
    if pd.isna(text):
        return None

    s = str(text).strip().lower()

    # ore
    match_h = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*h", s)
    if match_h:
        return float(match_h.group(1))

    # giorni
    match_d = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(day|days|d)\b", s)
    if match_d:
        return float(match_d.group(1)) * 24.0

    return None


def safe_float(value) -> Optional[float]:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def round2(x: float) -> float:
    return round(float(x), 2)


# ============================================================
# DATABASE
# ============================================================

class AlignerEvidenceDB:
    def __init__(self, data_dir: str = "."):
        base = Path(data_dir)

        self.materials = pd.read_csv(base / "materials_master.csv")
        self.staining = pd.read_csv(base / "staining_evidence.csv")
        self.mechanical = pd.read_csv(base / "mechanical_evidence.csv")
        self.surface = pd.read_csv(base / "thermoforming_fit_surface.csv")

        # normalizzazione colonne di supporto
        self.materials["brand_norm"] = self.materials["brand"].astype(str).str.strip().str.lower()
        self.materials["polymer_norm"] = self.materials["polymer"].astype(str).str.strip().str.lower()

        self.staining["brand_norm"] = self.staining["brand"].astype(str).str.strip().str.lower()
        self.staining["polymer_norm"] = self.staining["polymer"].astype(str).str.strip().str.lower()
        self.staining["agent_norm"] = self.staining["agent"].astype(str).str.strip().str.lower()

        if "exposure_time" in self.staining.columns:
            self.staining["exposure_hours"] = self.staining["exposure_time"].apply(parse_exposure_time_to_hours)
        elif "exposure_hours" not in self.staining.columns:
            self.staining["exposure_hours"] = None

        self.mechanical["brand_norm"] = self.mechanical["brand"].astype(str).str.strip().str.lower()
        self.mechanical["polymer_norm"] = self.mechanical["polymer"].astype(str).str.strip().str.lower()

        self.surface["brand_norm"] = self.surface["brand"].astype(str).str.strip().str.lower()
        self.surface["polymer_norm"] = self.surface["polymer"].astype(str).str.strip().str.lower()

    def get_material_row(self, brand: str) -> Optional[pd.Series]:
        brand_norm = brand.strip().lower()
        rows = self.materials[self.materials["brand_norm"] == brand_norm]
        if rows.empty:
            return None
        return rows.iloc[0]

    def get_polymer_for_brand(self, brand: str) -> Optional[str]:
        row = self.get_material_row(brand)
        if row is None:
            return None
        return row.get("polymer")

    def list_available_brands(self) -> List[str]:
        return sorted(self.materials["brand"].dropna().unique().tolist())

    def get_staining_rows(self, brand: str, agent: str) -> Tuple[pd.DataFrame, str]:
        """
        Cerca prima per brand esatto + agente.
        Se non trova nulla, prova con polymer + agente.
        """
        brand_norm = brand.strip().lower()
        agent_norm = agent.strip().lower()

        exact = self.staining[
            (self.staining["brand_norm"] == brand_norm) &
            (self.staining["agent_norm"] == agent_norm)
        ].copy()

        if not exact.empty:
            return exact, "brand"

        polymer = self.get_polymer_for_brand(brand)
        if polymer:
            polymer_norm = str(polymer).strip().lower()
            by_polymer = self.staining[
                (self.staining["polymer_norm"] == polymer_norm) &
                (self.staining["agent_norm"] == agent_norm)
            ].copy()
            if not by_polymer.empty:
                return by_polymer, "polymer"

        return pd.DataFrame(), "none"

    def get_mechanical_profile(self, brand: str) -> Optional[MechanicalProfile]:
        brand_norm = brand.strip().lower()
        rows = self.mechanical[self.mechanical["brand_norm"] == brand_norm]
        if rows.empty:
            polymer = self.get_polymer_for_brand(brand)
            if polymer:
                rows = self.mechanical[self.mechanical["polymer_norm"] == polymer.strip().lower()]

        if rows.empty:
            return None

        row = rows.iloc[0]
        return MechanicalProfile(
            brand=row.get("brand"),
            polymer=row.get("polymer"),
            young_modulus_MPa=safe_float(row.get("young_modulus_MPa")),
            yield_strength_MPa=safe_float(row.get("yield_strength_MPa")),
            time_window=row.get("time_window"),
            stress_decay_percent=safe_float(row.get("stress_decay_percent")),
            source=row.get("source"),
        )

    def get_surface_profile(self, brand: str) -> Optional[SurfaceProfile]:
        brand_norm = brand.strip().lower()
        rows = self.surface[self.surface["brand_norm"] == brand_norm]
        if rows.empty:
            polymer = self.get_polymer_for_brand(brand)
            if polymer:
                rows = self.surface[self.surface["polymer_norm"] == polymer.strip().lower()]

        if rows.empty:
            return None

        row = rows.iloc[0]
        return SurfaceProfile(
            brand=row.get("brand"),
            polymer=row.get("polymer"),
            thickness_pre_mm=safe_float(row.get("thickness_pre_mm")),
            thickness_post_mm=safe_float(row.get("thickness_post_mm")),
            region=row.get("region"),
            gap_mm=safe_float(row.get("gap_mm")),
            source=row.get("source"),
        )


# ============================================================
# MOTORE DI PREDIZIONE
# ============================================================

class Level1Predictor:
    def __init__(self, db: AlignerEvidenceDB, exposure_seconds: Optional[Dict[str, int]] = None):
        self.db = db
        self.exposure_seconds = exposure_seconds or DEFAULT_EXPOSURE_SECONDS

    def compute_total_exposure_hours(self, events_per_day: int, wear_days: int, seconds_per_event: int) -> float:
        total_seconds = events_per_day * wear_days * seconds_per_event
        return total_seconds / 3600.0

    def estimate_deltae(self, brand: str, agent: str, target_hours: float) -> AgentPrediction:
        rows, matched_on = self.db.get_staining_rows(brand, agent)

        seconds_per_event = self.exposure_seconds.get(agent, 0)

        if rows.empty:
            return AgentPrediction(
                agent=agent,
                events_per_day=0,
                seconds_per_event=seconds_per_event,
                total_exposure_hours=round2(target_hours),
                estimated_deltae=0.0,
                severity="nessun dato disponibile",
                matched_on="none",
                source_rows=[],
            )

        rows = rows.dropna(subset=["deltaE"]).copy()
        rows["deltaE"] = rows["deltaE"].astype(float)

        rows = rows.dropna(subset=["exposure_hours"]).copy()

        if rows.empty:
            # Se nel CSV manca exposure_hours parsabile, usa il primo dato disponibile
            row = self.db.get_staining_rows(brand, agent)[0].iloc[0]
            deltae_ref = safe_float(row.get("deltaE")) or 0.0
            return AgentPrediction(
                agent=agent,
                events_per_day=0,
                seconds_per_event=seconds_per_event,
                total_exposure_hours=round2(target_hours),
                estimated_deltae=round2(deltae_ref),
                severity=classify_deltae(deltae_ref),
                matched_on=matched_on,
                source_rows=[row.to_dict()],
            )

        rows = rows.sort_values("exposure_hours")

        # 1 solo punto -> stima proporzionale conservativa fino al riferimento
        if len(rows) == 1:
            row = rows.iloc[0]
            ref_h = float(row["exposure_hours"])
            ref_deltae = float(row["deltaE"])

            if ref_h <= 0:
                est = ref_deltae
            else:
                ratio = min(target_hours / ref_h, 1.0)
                est = ref_deltae * ratio

            return AgentPrediction(
                agent=agent,
                events_per_day=0,
                seconds_per_event=seconds_per_event,
                total_exposure_hours=round2(target_hours),
                estimated_deltae=round2(est),
                severity=classify_deltae(est),
                matched_on=matched_on,
                source_rows=[row.to_dict()],
            )

        # 2 o più punti -> interpolazione lineare
        xs = rows["exposure_hours"].astype(float).tolist()
        ys = rows["deltaE"].astype(float).tolist()

        if target_hours <= xs[0]:
            # sotto il minimo: scala conservativa
            est = ys[0] * (target_hours / xs[0]) if xs[0] > 0 else ys[0]
        elif target_hours >= xs[-1]:
            # sopra il massimo: non estrapoliamo aggressivamente
            est = ys[-1]
        else:
            est = ys[-1]
            for i in range(len(xs) - 1):
                x1, x2 = xs[i], xs[i + 1]
                y1, y2 = ys[i], ys[i + 1]
                if x1 <= target_hours <= x2:
                    fraction = (target_hours - x1) / (x2 - x1)
                    est = y1 + fraction * (y2 - y1)
                    break

        return AgentPrediction(
            agent=agent,
            events_per_day=0,
            seconds_per_event=seconds_per_event,
            total_exposure_hours=round2(target_hours),
            estimated_deltae=round2(est),
            severity=classify_deltae(est),
            matched_on=matched_on,
            source_rows=rows.to_dict(orient="records"),
        )

    def predict(self, habits: UserHabits) -> dict:
        agents_map = {
            "coffee": habits.coffee_per_day,
            "tea": habits.tea_per_day,
            "red_wine": habits.red_wine_per_day,
            "cola": habits.cola_per_day,
        }

        per_agent_results: List[AgentPrediction] = []

        for agent, events_per_day in agents_map.items():
            seconds_per_event = self.exposure_seconds.get(agent, 0)
            total_hours = self.compute_total_exposure_hours(
                events_per_day=events_per_day,
                wear_days=habits.wear_days,
                seconds_per_event=seconds_per_event,
            )

            pred = self.estimate_deltae(
                brand=habits.material_brand,
                agent=agent,
                target_hours=total_hours,
            )
            pred.events_per_day = events_per_day
            pred.seconds_per_event = seconds_per_event
            per_agent_results.append(pred)

        total_deltae = sum(x.estimated_deltae for x in per_agent_results)
        mechanical = self.db.get_mechanical_profile(habits.material_brand)
        surface = self.db.get_surface_profile(habits.material_brand)
        polymer = self.db.get_polymer_for_brand(habits.material_brand)

        return {
            "material_brand": habits.material_brand,
            "polymer": polymer,
            "wear_days": habits.wear_days,
            "agent_predictions": [asdict(x) for x in per_agent_results],
            "total_estimated_deltae": round2(total_deltae),
            "total_severity": classify_deltae(total_deltae),
            "mechanical_profile": asdict(mechanical) if mechanical else None,
            "surface_profile": asdict(surface) if surface else None,
            "model_notes": [
                "Il ΔE totale è ottenuto come somma delle stime per singolo agente, utile come indice comparativo interno del modello.",
                "La conversione consumo -> secondi di contatto è una parametrizzazione del modello, non un dato sperimentale diretto sugli aligner.",
                "Le stime di ΔE sono ancorate ai valori riportati negli studi disponibili nel database.",
                "Le proprietà meccaniche e superficiali vengono restituite come profilo descrittivo separato, non come causa diretta del ΔE.",
            ],
        }


# ============================================================
# INTERFACCIA CLI (utile per il test e riusabile nella webapp)
# ============================================================

def ask_int(prompt: str, min_value: int = 0, max_value: int = 100) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if min_value <= value <= max_value:
                return value
            print(f"Inserisci un numero tra {min_value} e {max_value}.")
        except ValueError:
            print("Inserisci un numero intero valido.")


def choose_brand(db: AlignerEvidenceDB) -> str:
    brands = db.list_available_brands()
    print("\nMateriali disponibili:")
    for i, b in enumerate(brands, start=1):
        print(f"{i}. {b}")

    while True:
        idx = ask_int("\nSeleziona il numero del materiale: ", 1, len(brands))
        return brands[idx - 1]


def collect_user_habits_cli(db: AlignerEvidenceDB) -> UserHabits:
    brand = choose_brand(db)
    wear_days = ask_int("Quanti giorni viene indossato l'aligner? ", 1, 30)

    print("\nInserisci il numero medio di esposizioni al giorno:")
    coffee = ask_int("Caffè al giorno: ", 0, 20)
    tea = ask_int("Tè al giorno: ", 0, 20)
    red_wine = ask_int("Calici di vino rosso al giorno: ", 0, 20)
    cola = ask_int("Bibite tipo cola al giorno: ", 0, 20)

    return UserHabits(
        material_brand=brand,
        wear_days=wear_days,
        coffee_per_day=coffee,
        tea_per_day=tea,
        red_wine_per_day=red_wine,
        cola_per_day=cola,
    )


def print_report(result: dict) -> None:
    print("\n" + "=" * 70)
    print("RISULTATO")
    print("=" * 70)
    print(f"Materiale: {result['material_brand']}")
    print(f"Polimero: {result['polymer']}")
    print(f"Giorni di utilizzo: {result['wear_days']}")
    print(f"ΔE totale stimato: {result['total_estimated_deltae']}")
    print(f"Classe: {result['total_severity']}")

    print("\nDettaglio per agente:")
    for row in result["agent_predictions"]:
        print("-" * 50)
        print(f"Agente: {row['agent']}")
        print(f"Eventi/giorno: {row['events_per_day']}")
        print(f"Secondi/evento: {row['seconds_per_event']}")
        print(f"Esposizione totale standardizzata (h): {row['total_exposure_hours']}")
        print(f"ΔE stimato: {row['estimated_deltae']}")
        print(f"Classe: {row['severity']}")
        print(f"Match database: {row['matched_on']}")

        if row["source_rows"]:
            print("Fonti / righe usate:")
            for src in row["source_rows"]:
                brand = src.get("brand")
                agent = src.get("agent")
                exposure = src.get("exposure_time")
                deltae = src.get("deltaE")
                source = src.get("source")
                print(f"  - {brand} | {agent} | {exposure} | ΔE={deltae} | {source}")

    mech = result.get("mechanical_profile")
    if mech:
        print("\nProfilo meccanico:")
        print(f"  Young modulus (MPa): {mech['young_modulus_MPa']}")
        print(f"  Yield strength (MPa): {mech['yield_strength_MPa']}")
        print(f"  Stress decay (%): {mech['stress_decay_percent']}")
        print(f"  Finestra temporale: {mech['time_window']}")
        print(f"  Fonte: {mech['source']}")

    surf = result.get("surface_profile")
    if surf:
        print("\nProfilo superficiale / fit:")
        print(f"  Thickness pre (mm): {surf['thickness_pre_mm']}")
        print(f"  Thickness post (mm): {surf['thickness_post_mm']}")
        print(f"  Regione: {surf['region']}")
        print(f"  Gap (mm): {surf['gap_mm']}")
        print(f"  Fonte: {surf['source']}")

    print("\nNote modello:")
    for note in result["model_notes"]:
        print(f"  - {note}")


def main():
    db = AlignerEvidenceDB(".")
    predictor = Level1Predictor(db)

    habits = collect_user_habits_cli(db)
    result = predictor.predict(habits)
    print_report(result)


if __name__ == "__main__":
    main()