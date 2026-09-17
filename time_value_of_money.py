"""Time value of money: give any three figures and the fourth is worked out."""

import math

__version__ = "2.2"

SOLVE_DIGITS = 3
PRINT_DIGITS = 1

FIELDS = ("pv", "fv", "rate", "periods")

PROMPTS = {
    "pv": "Present value",
    "fv": "Future value",
    "rate": "Interest rate per period, as a percentage (e.g. 5 for 5%)",
    "periods": "Number of periods",
}

LABELS = {
    "pv": "present value",
    "fv": "future value",
    "rate": "rate",
    "periods": "periods",
}


def future_value_factor(rate, periods):
    return (1 + rate) ** periods


def future_value(pv, rate, periods):
    return pv * future_value_factor(rate, periods)


def present_value(fv, rate, periods):
    return fv / future_value_factor(rate, periods)


def solve_rate(pv, fv, periods):
    return (fv / pv) ** (1 / periods) - 1


def solve_periods(pv, fv, rate):
    return math.log(fv / pv) / math.log(1 + rate)


def parse_field(field, raw):
    value = float(raw)
    if field == "rate":
        return value / 100
    if field == "periods":
        return abs(value)
    return value


def show(field, value):
    if field == "rate":
        return f"{value * 100:,.{PRINT_DIGITS}f}%"
    return f"{value:,.{PRINT_DIGITS}f}"


def collect():
    known = {}
    blanks = []
    for field in FIELDS:
        if len(known) == len(FIELDS) - 1:
            blanks.append(field)
            print(f"  That's three, so solving for {LABELS[field]}.")
            break
        while True:
            raw = input(f"{PROMPTS[field]} (Enter to solve for this): ").strip()
            if not raw:
                blanks.append(field)
                break
            try:
                known[field] = parse_field(field, raw)
                break
            except ValueError:
                print("  Please enter a number, or press Enter to solve for this.")
    return known, blanks


def problem(target, known):
    """Return a message explaining why this cannot be solved, or None."""
    pv, fv = known.get("pv"), known.get("fv")
    rate, periods = known.get("rate"), known.get("periods")

    if rate is not None and rate <= -1:
        return "The rate has to be above -100%."
    if target in ("rate", "periods"):
        if pv == 0:
            return "Present value cannot be 0 when solving for the rate or the periods."
        if fv / pv <= 0:
            return "Present value and future value have to share the same sign."
    if target == "rate" and periods == 0:
        return "Over 0 periods no rate turns one amount into a different one."
    if target == "periods" and rate == 0:
        return "At a 0% rate the value never changes, so no number of periods reaches that future value."
    return None


def solve(target, known):
    if target == "fv":
        value = future_value(known["pv"], known["rate"], known["periods"])
    elif target == "pv":
        value = present_value(known["fv"], known["rate"], known["periods"])
    elif target == "rate":
        value = solve_rate(known["pv"], known["fv"], known["periods"])
    else:
        value = solve_periods(known["pv"], known["fv"], known["rate"])
    return round(value, SOLVE_DIGITS)


def echo(target, known):
    parts = [f"{LABELS[field]} {show(field, known[field])}"
             for field in FIELDS if field != target]
    print(f"Solving for {LABELS[target]}: {', '.join(parts)}")


def check(known):
    """All four given: recompute the future value and compare.

    run() never reaches this, since the prompts stop at three figures.
    Kept for checking a set of four that came from somewhere else.
    """
    message = problem("fv", known)
    if message:
        print(f"  {message}")
        return None
    expected = round(future_value(known["pv"], known["rate"], known["periods"]),
                     SOLVE_DIGITS)
    entered = known["fv"]
    if show("fv", expected) == show("fv", entered):
        print(f"All four agree, at a future value of {show('fv', entered)}.")
    else:
        print(f"Mismatch: you entered a future value of {show('fv', entered)}, "
              f"but the other three give {show('fv', expected)}.")
    return expected


def run():
    """Ask until the figures work out.

    Returns all four figures and the field that was solved for. The prompts
    stop at three figures, so there is always exactly one field to solve.
    """
    while True:
        known, blanks = collect()

        if len(blanks) != 1:
            print("  Leave exactly one field blank. The other three are needed.\n")
            continue

        target = blanks[0]
        message = problem(target, known)
        if message:
            print(f"  {message}\n")
            continue

        echo(target, known)
        known[target] = solve(target, known)
        print(f"{LABELS[target].capitalize()}: {show(target, known[target])}")
        return known, target


def main():
    known, target = run()
    return known[target]


if __name__ == "__main__":
    main()
