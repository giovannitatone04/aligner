import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(level1_result: dict, level2_result: dict) -> str:
    return f"""
Sei un assistente scientifico per una webapp sugli aligner ortodontici.

Devi spiegare in italiano, in modo semplice ma rigoroso, il risultato del modello.
Non fare raccomandazioni cliniche.
Non inventare dati.
Separa chiaramente:
1. risultato evidence-based (livello 1)
2. sintesi esplorativa (livello 2)

DATI LIVELLO 1:
{level1_result}

DATI LIVELLO 2:
{level2_result}

Scrivi:
- un breve riassunto generale
- i principali fattori che aumentano il rischio estetico
- una nota metodologica finale molto breve
"""


def explain_results(level1_result: dict, level2_result: dict) -> str:
    prompt = build_prompt(level1_result, level2_result)

    response = client.responses.create(
        model="gpt-5",
        input=prompt,
        store=False
    )

    return response.output_text