__version__ = "1.0"

# Interactive console. See README.txt for what this file is and how it fits.

import sys
from pathlib import Path

# Make the two calculation modules importable no matter where this is run from.
# Each directory is moved to the front, so the one listed last wins -- HERE is
# last, meaning a module sitting beside this file beats any fallback copy.
# Removing before inserting matters: Python already puts the script's own
# directory on sys.path, so a plain "insert if not present" would skip HERE and
# leave the fallback ahead of it, quietly importing the wrong module.
HERE = Path(__file__).resolve().parent
for _candidate in (Path("/mnt/project"), HERE):
    if _candidate.is_dir():
        _path = str(_candidate)
        if _path in sys.path:
            sys.path.remove(_path)
        sys.path.insert(0, _path)

import financial_ratios_v2_0 as fr          # noqa: E402
import time_value_of_money_v1_2 as tvm      # noqa: E402


# --- Input helpers ----------------------------------------------------------
# Pinched from time_value_of_money_v1_2.py, lines 78-126, unchanged.

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


# --- Time value of money flow -----------------------------------------------
# Was main() in time_value_of_money_v1_2.py. It calls all four helpers above,
# so it had to come with them.

def time_value_console():
    choice = ask_choice()

    if choice == "fv":
        pv = ask_number("What is the starting value? ")
        percent, r = ask_rate()
        t = ask_number("Number of periods: ", minimum=0)
        fv = tvm.future_value(pv, r, t)
        print(f"The {tidy(pv)} price at a {tidy(percent)}% for {tidy(t)} periods "
              f"will increase to {round(fv, 2)}")

    elif choice == "pv":
        fv = ask_number("What is the future value? ")
        percent, r = ask_rate()
        t = ask_number("Number of periods: ", minimum=0)
        pv = tvm.present_value(fv, r, t)
        print(f"The {tidy(fv)} price in {tidy(t)} periods at {tidy(percent)}% "
              f"is worth {round(pv, 2)} today")

    elif choice == "r":
        pv = ask_number("What is the starting (present) value? ")
        fv = ask_number("What is the future value? ")
        t = ask_number("Number of periods: ", minimum=0)
        r = tvm.solve_rate(pv, fv, t)
        if r is None:
            print("Can't solve for a rate from those figures.")
        else:
            print(f"The {tidy(pv)} price growing to {tidy(fv)} over {tidy(t)} periods "
                  f"implies a rate of {round(r * 100, 4)}%")

    elif choice == "t":
        pv = ask_number("What is the starting (present) value? ")
        fv = ask_number("What is the future value? ")
        percent, r = ask_rate()
        # solve_periods now refuses a negative answer rather than returning
        # one, so the "implies negative periods" case arrives as an exception
        # instead of a t < 0 test. Same two messages as before.
        try:
            t = tvm.solve_periods(pv, fv, r)
        except tvm.NegativePeriods:
            print("Those figures imply negative periods -- you can't reach a "
                  "lower value at a non-negative rate.")
        else:
            if t is None:
                print("Can't solve for a number of periods from those figures.")
            else:
                print(f"The {tidy(pv)} price growing to {tidy(fv)} at {tidy(percent)}% "
                      f"takes {round(t, 4)} periods")


# --- Financial ratios front end ---------------------------------------------
# Pinched from financial_ratios_v2_0.py, lines 334-359, unchanged apart from
# reaching its module's classes through `fr.`.

class ConsoleApp:
    """Asks for the figures, resolves identities, prints every ratio."""

    def ask_number(self, field):
        """Prompt for one figure. Blank input -> None (treated as missing data)."""
        while True:
            raw = input(f"{field} (leave blank if unknown): ").strip()
            if raw == "":
                return None
            try:
                return float(raw)
            except ValueError:
                print("  Please enter a number, or leave it blank if unknown.")

    def get_financials(self):
        values = {field: self.ask_number(field) for field in fr.Financials.FIELDS}
        return fr.Financials(**values)

    def run(self):
        financials = self.get_financials().resolve()
        report = fr.Report(fr.RatioCalculator(financials))
        report.print_derived(financials)
        print()
        report.print_all()


def ratios_console():
    ConsoleApp().run()


# --- Picking a front end ----------------------------------------------------
# New, and the only thing here that isn't lifted: one program now holds two
# front ends, so it has to ask which one you want.

FRONT_ENDS = {
    "ratios": ("financial ratios", ratios_console),
    "tvm": ("time value of money", time_value_console),
}


def ask_front_end():
    """Return the chosen front end's function, or None to quit."""
    while True:
        raw = input("Which calculator? (ratios/tvm, or 'q' to quit): ").strip().lower()
        if raw in ("q", "quit", "exit"):
            return None
        if raw in ("ratios", "ratio", "r", "financial", "financial ratios"):
            return FRONT_ENDS["ratios"][1]
        if raw in ("tvm", "t", "time", "time value", "time value of money"):
            return FRONT_ENDS["tvm"][1]
        print("  Please answer 'ratios', 'tvm', or 'q'.")


def main():
    front_end = ask_front_end()
    if front_end is not None:
        front_end()


if __name__ == "__main__":
    main()
