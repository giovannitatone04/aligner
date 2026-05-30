from predictor_level1_v2 import EvidenceDB, Level1Predictor, UserHabits
from scoring_level2 import build_level2_scores


# ============================================================
# CORE FUNCTION (riutilizzabile per webapp)
# ============================================================

def run_full_model(
    material_brand: str,
    wear_days: int,
    coffee_per_day: int,
    tea_per_day: int,
    red_wine_per_day: int,
    cola_per_day: int,
    cigarettes_per_day: int,
):
    db = EvidenceDB(".")
    predictor = Level1Predictor(db)

    habits = UserHabits(
        material_brand=material_brand,
        wear_days=wear_days,
        coffee_per_day=coffee_per_day,
        tea_per_day=tea_per_day,
        red_wine_per_day=red_wine_per_day,
        cola_per_day=cola_per_day,
        cigarettes_per_day=cigarettes_per_day,
    )

    level1_result = predictor.predict(habits)
    level2_result = build_level2_scores(level1_result)

    return {
        "level1": level1_result,
        "level2": level2_result,
    }


# ============================================================
# CLI (uso da terminale)
# ============================================================

def ask_int(prompt, min_val=0, max_val=100):
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Inserisci un numero tra {min_val} e {max_val}")
        except:
            print("Inserisci un numero valido")


def choose_material(db):
    materials = db.list_available_brands()
    print("\nMateriali disponibili:")
    for i, m in enumerate(materials):
        print(f"{i+1}. {m}")

    idx = ask_int("\nSeleziona materiale: ", 1, len(materials))
    return materials[idx - 1]


# ============================================================
# STAMPA RISULTATI
# ============================================================

def print_results(results):
    l1 = results["level1"]
    l2 = results["level2"]

    print("\n" + "=" * 70)
    print("RISULTATO MODELLO")
    print("=" * 70)

    print("\n--- MATERIALE ---")
    print("Brand:", l1["material_brand"])
    print("Polimero:", l1["polymer"])
    print("Famiglia:", l1["polymer_family"])
    print("Struttura:", l1["structure"])

    print("\n--- ESTETICA (LEVEL 1) ---")
    print("ΔE totale:", l1["total_estimated_deltaE_numeric_agents_only"])

    print("\nDettaglio agenti:")
    for a in l1["agent_predictions"]:
        print(f"- {a['agent']}: ΔE={a['estimated_deltaE']} | match={a['matched_on']}")

    print("\n--- MECCANICA ---")
    print(l1["mechanical_profile"])

    print("\n--- SUPERFICIE ---")
    print(l1["surface_profile"])

    print("\n" + "=" * 70)
    print("LEVEL 2 (SINTESI)")
    print("=" * 70)

    print("\nStaining score:", l2["staining_summary"]["staining_score"])
    print("Classe:", l2["staining_summary"]["staining_risk_class"])

    print("\nMechanical risk:", l2["mechanical_summary"]["mechanical_risk_score"])
    print("Classe:", l2["mechanical_summary"]["mechanical_risk_class"])

    print("\nSurface risk:", l2["surface_summary"]["surface_risk_score"])
    print("Classe:", l2["surface_summary"]["surface_risk_class"])

    print("\nGlobal risk:", l2["global_summary"]["global_risk_score"])
    print("Classe:", l2["global_summary"]["global_risk_class"])

    print("\nConfidence:", l2["confidence_summary"]["confidence_score"])
    print("Livello:", l2["confidence_summary"]["confidence_level"])

    print("\nSmoke profile:")
    print(l2["smoke_profile"])

    print("\nDrivers principali:")
    for d in l2["drivers"]:
        print("-", d)


# ============================================================
# MAIN
# ============================================================

def main():
    db = EvidenceDB(".")

    material = choose_material(db)
    wear_days = ask_int("Giorni di utilizzo: ", 1, 30)

    print("\n--- ABITUDINI ---")
    coffee = ask_int("Caffè/giorno: ", 0, 20)
    tea = ask_int("Tè/giorno: ", 0, 20)
    wine = ask_int("Vino rosso/giorno: ", 0, 20)
    cola = ask_int("Cola/giorno: ", 0, 20)
    smoke = ask_int("Sigarette/giorno: ", 0, 60)

    results = run_full_model(
        material,
        wear_days,
        coffee,
        tea,
        wine,
        cola,
        smoke
    )

    print_results(results)


if __name__ == "__main__":
    main()