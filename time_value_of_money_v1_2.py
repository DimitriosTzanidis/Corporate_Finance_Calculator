__version__ = "1.2"

# ---------------------------------------------------------------------------
# Time value of money.
#
# One relationship, four unknowns. Given any three, solve for the fourth:
#   future value:   fv = pv * (1 + r) ** t
#   present value:  pv = fv / (1 + r) ** t
#   rate:           r  = (fv / pv) ** (1 / t) - 1      (t-th root)
#   periods:        t  = ln(fv / pv) / ln(1 + r)       (logarithm)
#
# The shared piece (1 + r) ** t is the "future value factor", written once in
# future_value_factor() and reused by the fv/pv formulas.
#
# New in 1.1: solve_rate() and solve_periods(). Both need pv AND fv known, and
# both are more fragile than the fv/pv formulas -- they can be asked questions
# with no real answer -- so they guard their inputs and return None instead of
# crashing.
#
# New in 1.2: the number of periods is kept non-negative -- negative periods
# are nonsensical in a forward-looking model, so they're rejected on input and
# a solved t that comes out negative is reported as inconsistent. The rate may
# be negative, representing erosion/depreciation (value shrinking each period),
# so it is accepted and reported as-is.
# ---------------------------------------------------------------------------

import math


def future_value_factor(r, t):
    """(1 + r) ** t -- the factor the fv/pv formulas are built on."""
    return (1 + r) ** t


def future_value(pv, r, t):
    """Grow a present value forward t periods at rate r."""
    return pv * future_value_factor(r, t)


def present_value(fv, r, t):
    """Discount a future value back t periods at rate r."""
    return fv / future_value_factor(r, t)


def solve_rate(pv, fv, t):
    """Rate per period that turns pv into fv over t periods.

    Returns None when the question has no real answer: pv of zero (nothing to
    grow), t of zero (the 1/t exponent blows up), or fv/pv <= 0 (a real t-th
    root needs a positive ratio).
    """
    if None in (pv, fv, t) or pv == 0 or t == 0:
        return None
    ratio = fv / pv
    if ratio <= 0:
        return None
    return ratio ** (1 / t) - 1


def solve_periods(pv, fv, r):
    """Number of periods for pv to reach fv at rate r.

    Returns None when the question has no real answer: pv of zero, fv/pv <= 0
    or 1 + r <= 0 (both are inside logarithms), or r == 0 (no growth, so pv can
    never reach a different fv -- the log denominator would be zero).
    """
    if None in (pv, fv, r) or pv == 0:
        return None
    ratio = fv / pv
    if ratio <= 0 or 1 + r <= 0:
        return None
    denom = math.log(1 + r)
    if denom == 0:
        return None
    return math.log(ratio) / denom


# --- Input helpers ----------------------------------------------------------

def ask_choice():
    """Return "fv", "pv", "r", or "t" -- which unknown the user wants to solve."""
    while True:
        raw = input("Solve for which? (fv/pv/r/t): ").strip().lower()
        if raw in ("fv", "f", "future", "future value"):
            return "fv"
        if raw in ("pv", "p", "present", "present value"):
            return "pv"
        if raw in ("r", "rate", "interest", "interest rate"):
            return "r"
        if raw in ("t", "periods", "time", "number of periods"):
            return "t"
        print("  Please answer 'fv', 'pv', 'r', or 't'.")


def ask_number(prompt, minimum=None):
    """Prompt until a valid number is entered. If `minimum` is given, values
    below it are rejected and re-prompted (used to keep periods >= 0)."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Please enter {tidy(minimum)} or more.")
            continue
        return value


def ask_rate():
    """Ask for the interest rate as a percentage, return (percent, decimal).

    The user types a percentage (5 for 5%); the formulas need the decimal
    (0.05), so we hand back both -- the percent for display, r for the maths.
    Negative rates are allowed: they represent value shrinking each period.
    """
    percent = ask_number("Interest rate as a percentage (e.g. 5 for 5%): ")
    return percent, percent / 100


def tidy(x):
    """Show whole numbers without a trailing .0, otherwise leave as-is."""
    return int(x) if float(x).is_integer() else x


# --- Main flow --------------------------------------------------------------

def main():
    choice = ask_choice()

    if choice == "fv":
        pv = ask_number("What is the starting value? ")
        percent, r = ask_rate()
        t = ask_number("Number of periods: ", minimum=0)
        fv = future_value(pv, r, t)
        print(f"The {tidy(pv)} price at a {tidy(percent)}% for {tidy(t)} periods "
              f"will increase to {round(fv, 2)}")

    elif choice == "pv":
        fv = ask_number("What is the future value? ")
        percent, r = ask_rate()
        t = ask_number("Number of periods: ", minimum=0)
        pv = present_value(fv, r, t)
        print(f"The {tidy(fv)} price in {tidy(t)} periods at {tidy(percent)}% "
              f"is worth {round(pv, 2)} today")

    elif choice == "r":
        pv = ask_number("What is the starting (present) value? ")
        fv = ask_number("What is the future value? ")
        t = ask_number("Number of periods: ", minimum=0)
        r = solve_rate(pv, fv, t)
        if r is None:
            print("Can't solve for a rate from those figures.")
        else:
            print(f"The {tidy(pv)} price growing to {tidy(fv)} over {tidy(t)} periods "
                  f"implies a rate of {round(r * 100, 4)}%")

    elif choice == "t":
        pv = ask_number("What is the starting (present) value? ")
        fv = ask_number("What is the future value? ")
        percent, r = ask_rate()
        t = solve_periods(pv, fv, r)
        if t is None:
            print("Can't solve for a number of periods from those figures.")
        elif t < 0:
            print("Those figures imply negative periods -- you can't reach a "
                  "lower value at a non-negative rate.")
        else:
            print(f"The {tidy(pv)} price growing to {tidy(fv)} at {tidy(percent)}% "
                  f"takes {round(t, 4)} periods")


if __name__ == "__main__":
    main()
