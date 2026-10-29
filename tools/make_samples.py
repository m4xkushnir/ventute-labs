"""Build the synthetic seed set in samples/.

Each sample is a folder with:
  facts.json   what was true for the company that month
  output.txt   the report written from those facts
  labels.json  the problems planted in output.txt (empty list = clean)

Run: python tools/make_samples.py
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "samples"

COMPANIES = [
    ("Harbour & Pine", "furniture retail", "United Kingdom", "Bristol", "GBP", "en"),
    ("Lumen Analytics", "B2B software", "Ireland", "Cork", "EUR", "en"),
    ("Café Oriel", "hospitality", "France", "Lyon", "EUR", "fr"),
    ("Brightfield Credit", "consumer lending", "Netherlands", "Utrecht", "EUR", "en"),
    ("Kestrel Logistics", "freight", "Germany", "Leipzig", "EUR", "de"),
    ("Saltmarsh Foods", "food manufacturing", "United Kingdom", "Norwich", "GBP", "en"),
    ("Panaderia Sol", "bakery chain", "Spain", "Valencia", "EUR", "es"),
    ("Northgate Clinics", "healthcare services", "Sweden", "Malmö", "SEK", "en"),
    ("Tessera Studio", "design agency", "Italy", "Turin", "EUR", "it"),
    ("Fernhill Energy", "solar installation", "Poland", "Wrocław", "PLN", "en"),
]

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def money(v, cur):
    sym = {"GBP": "£", "EUR": "€"}.get(cur)
    return f"{sym}{v:,.0f}" if sym else f"{v:,.0f} {cur}"


def make_facts(rng, company):
    name, sector, country, city, cur, lang = company
    revenue = rng.randrange(40_000, 900_000, 1_000)
    costs = int(revenue * rng.uniform(0.7, 1.25))
    cash = rng.randrange(80_000, 3_000_000, 1_000)
    headcount = rng.randint(4, 120)
    prev_revenue = int(revenue / rng.uniform(0.85, 1.2))
    return {
        "company": name, "sector": sector, "country": country, "city": city,
        "currency": cur, "language": lang,
        "period": f"{rng.choice(MONTHS)} {rng.randint(2024, 2027)}",
        "revenue": revenue, "previous_month_revenue": prev_revenue,
        "operating_costs": costs, "operating_result": revenue - costs,
        "cash": cash, "headcount": headcount,
        "open_roles": rng.randint(0, 6),
        "top_customer_share_pct": rng.randint(5, 45),
        "events": rng.sample([
            "a supplier raised prices by 6%",
            "a competitor opened nearby",
            "the bank renewed the overdraft facility",
            "a key employee resigned",
            "a large order was delayed to next month",
            "a new product line launched",
        ], 2),
    }


def write_report(f):
    cur = f["currency"]
    growth = (f["revenue"] / f["previous_month_revenue"] - 1) * 100
    direction = "up" if growth >= 0 else "down"
    result = f["operating_result"]
    result_text = (f"an operating profit of {money(result, cur)}" if result >= 0
                   else f"an operating loss of {money(-result, cur)}")
    return (
        f"{f['company']} closed {f['period']} with revenue of {money(f['revenue'], cur)}, "
        f"{direction} {abs(growth):.1f}% on the previous month. "
        f"Operating costs were {money(f['operating_costs'], cur)}, giving {result_text}. "
        f"The company ends the month with {money(f['cash'], cur)} in cash and "
        f"{f['headcount']} people, with {f['open_roles']} open "
        f"{'role' if f['open_roles'] == 1 else 'roles'}.\n\n"
        f"This month {f['events'][0]}, and {f['events'][1]}. "
        f"The largest customer accounts for {f['top_customer_share_pct']}% of revenue"
        + (", which is a concentration risk worth watching." if f["top_customer_share_pct"] >= 30 else ".")
        + "\n"
    )


# Each fault rewrites the report and returns the label that describes it.

def fault_numeric(rng, f, text):
    cur = f["currency"]
    right = money(f["cash"], cur)
    wrong = money(int(f["cash"] * rng.choice([0.5, 1.4, 10])), cur)
    return text.replace(right, wrong), {"type": "numeric_mismatch", "field": "cash",
                                        "expected": right, "found": wrong}


def fault_hallucination(rng, f, text):
    claim = rng.choice([
        f"{f['company']} also signed a three-year contract with a national retailer.",
        "The board approved a second office in the capital.",
        "A venture fund has offered to lead a seed round.",
    ])
    return text.rstrip("\n") + " " + claim + "\n", {"type": "hallucination", "claim": claim}


def fault_contradiction(rng, f, text):
    growth_up = f["revenue"] >= f["previous_month_revenue"]
    claim = ("Revenue fell compared with last month." if growth_up
             else "Revenue grew compared with last month.")
    return text.rstrip("\n") + " " + claim + "\n", {"type": "contradiction", "claim": claim}


def fault_internal(rng, f, text):
    claim = f"With only {f['headcount'] + rng.randint(5, 20)} people on staff, hiring is the priority."
    return text.rstrip("\n") + " " + claim + "\n", {"type": "internal_inconsistency", "claim": claim}


def fault_language(rng, f, text):
    # Facts ask for a non-English report, but the text stays in English.
    return text, {"type": "wrong_language", "expected": f["language"], "found": "en"}


FAULTS = [fault_numeric, fault_hallucination, fault_contradiction, fault_internal]


def main():
    rng = random.Random(20261029)
    ROOT.mkdir(exist_ok=True)
    n = 0
    fault_i = 0
    for round_ in range(3):
        for company in COMPANIES:
            n += 1
            facts = make_facts(rng, company)
            text = write_report(facts)
            labels = []
            if round_ == 0 and facts["language"] != "en":
                text, label = fault_language(rng, facts, text)
                labels.append(label)
            else:
                facts["language"] = "en"
                if round_ > 0 and n % 3 != 0:
                    text, label = FAULTS[fault_i % len(FAULTS)](rng, facts, text)
                    fault_i += 1
                    labels.append(label)
            d = ROOT / f"sample_{n:03d}"
            d.mkdir(exist_ok=True)
            (d / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
            (d / "output.txt").write_text(text)
            (d / "labels.json").write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {n} samples to {ROOT}")


if __name__ == "__main__":
    main()
