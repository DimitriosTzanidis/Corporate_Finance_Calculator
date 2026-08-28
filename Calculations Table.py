__version__ = "1.0"

# ---------------------------------------------------------------------------
# Calculations table.
#
# One set of numbers -> one table. The table carries a name as its title, the
# calculation names run down the left, their results down the right:
#
#   taff
#   ------------------------------------------------
#   current ratio                             2.0476
#   quick ratio                               1.1905
#   ...
#
# Everything both modules produce goes in that one table:
#
#   financial_ratios_v2_0.py    -> every ratio, plus whatever the accounting
#                                  identities filled in
#   time_value_of_money_v1_2.py -> the figures given, then fv, pv, r and t
#
# When another set of numbers comes along it becomes another table under its
# own name. compare() puts any of them side by side by name, matching rows on
# the calculation's name.
#
# The figures below are dummy, so a table can be seen straight away. Replace
# them, and the placeholder names, with the real ones.
# ---------------------------------------------------------------------------

import sys
from pathlib import Path

import pandas as pd

# Make the two project modules importable no matter where this is run from.
HERE = Path(__file__).resolve().parent
for _candidate in (HERE, Path("/mnt/project")):
    if _candidate.is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

import financial_ratios_v2_0 as fr          # noqa: E402
import time_value_of_money_v1_2 as tvm      # noqa: E402


# --- Settings ---------------------------------------------------------------

OUTPUT_DIR = HERE            # where the tables are written
FILE_FORMAT = "csv"          # "csv" or "xlsx"
DIGITS = 4                   # rounding, same as the ratio Report

COLUMNS = ["Calculation", "Result"]


# --- Dummy inputs -----------------------------------------------------------

# Each entry is one table: its name, and the numbers behind it. "taff" is a
# placeholder -- rename it to whatever the set is actually called.
#
# net_fixed_assets and total_equity are left blank on purpose so the accounting
# identities have something to solve for.

TAFF_FINANCIALS = dict(
    sales=1_200_000, cogs=720_000, ebit=260_000, interest=40_000,
    net_income=150_000, depreciation=60_000,
    current_assets=430_000, inventory=180_000, cash=90_000,
    accounts_receivable=140_000,
    current_liabilities=210_000, accounts_payable=120_000,
    fixed_assets=800_000, capital_improvements=50_000, net_fixed_assets=None,
    total_assets=1_220_000, total_liabilities=640_000, total_equity=None,
    long_term_debt=430_000, price_per_share=24.50, earnings_per_share=3.10,
)
TAFF_TVM = dict(pv=1_000.0, fv=2_000.0, rate=0.05, periods=10.0)

BRILL_FINANCIALS = dict(
    sales=1_450_000, cogs=910_000, ebit=290_000, interest=52_000,
    net_income=165_000, depreciation=72_000,
    current_assets=505_000, inventory=225_000, cash=70_000,
    accounts_receivable=185_000,
    current_liabilities=260_000, accounts_payable=140_000,
    fixed_assets=880_000, capital_improvements=65_000, net_fixed_assets=None,
    total_assets=1_378_000, total_liabilities=760_000, total_equity=None,
    long_term_debt=500_000, price_per_share=26.75, earnings_per_share=3.35,
)
BRILL_TVM = dict(pv=1_000.0, fv=2_000.0, rate=0.07, periods=8.0)

DUMMY_TABLES = {
    "taff": (TAFF_FINANCIALS, TAFF_TVM),
    "brill": (BRILL_FINANCIALS, BRILL_TVM),
}


# --- Building a table -------------------------------------------------------

def _round(value):
    """Round for the table; missing data becomes NaN, shown as n/a."""
    return float("nan") if value is None else round(value, DIGITS)


def financial_rows(values):
    """Whatever the identities filled in, then every ratio, in module order."""
    financials = fr.Financials(**values).resolve()
    calculator = fr.RatioCalculator(financials)

    rows = [(f"{field} (derived)", _round(value))
            for field, value in financials.derived().items()]
    rows += [(name, _round(calculator.compute(name)))
             for name in calculator.names()]
    return rows


def tvm_rows(case):
    """The figures given, then each unknown the module can solve for.

    The given figures are rows of their own so the solved lines can be read
    without having to look up what they were solved from -- and so they line
    up across tables when two sets are compared.
    """
    pv, fv, r, t = case["pv"], case["fv"], case["rate"], case["periods"]
    solved_rate = tvm.solve_rate(pv, fv, t)
    solved_periods = tvm.solve_periods(pv, fv, r)

    return [
        ("pv given", _round(pv)),
        ("fv given", _round(fv)),
        ("rate given, %", _round(r * 100)),
        ("periods given", _round(t)),
        ("future value (fv)", _round(tvm.future_value(pv, r, t))),
        ("present value (pv)", _round(tvm.present_value(fv, r, t))),
        ("rate per period, % (r)",
         _round(None if solved_rate is None else solved_rate * 100)),
        ("number of periods (t)", _round(solved_periods)),
    ]


def build_table(financials, tvm_case, name=None):
    """One table: calculation names on the left, results on the right."""
    df = pd.DataFrame(financial_rows(financials) + tvm_rows(tvm_case),
                      columns=COLUMNS)
    df["Result"] = pd.to_numeric(df["Result"], errors="coerce")
    df.attrs["name"] = name          # the title travels with the table
    return df


# --- Saving and loading -----------------------------------------------------

def table_path(name, directory=None, fmt=None):
    return Path(directory or OUTPUT_DIR) / f"{name}.{fmt or FILE_FORMAT}"


def save_table(df, name=None, directory=None, fmt=None):
    """Write one table out, its name as the title above the columns."""
    name = name or df.attrs.get("name")
    if not name:
        raise ValueError("the table needs a name")
    path = table_path(name, directory, fmt)

    if path.suffix == ".xlsx":
        sheet = name[:31]
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False, startrow=1)
            writer.sheets[sheet]["A1"] = name
    else:
        with open(path, "w", newline="") as handle:
            handle.write(f"{name}\n")
            df.to_csv(handle, index=False)
    return path


def load_table(name, directory=None, fmt=None):
    """Read a table back by name. The title line is skipped."""
    path = table_path(name, directory, fmt)
    df = (pd.read_excel(path, skiprows=1) if path.suffix == ".xlsx"
          else pd.read_csv(path, skiprows=1))
    df["Result"] = pd.to_numeric(df["Result"], errors="coerce")
    df.attrs["name"] = name
    return df


# --- Reading ----------------------------------------------------------------

def _fmt(value):
    return "n/a" if pd.isna(value) else f"{value:,.{DIGITS}f}"


def show(df, name=None, width=None):
    """Print a table: title on top, names left, results right."""
    name = name or df.attrs.get("name", "")
    labels = df[COLUMNS[0]].astype(str)
    results = [_fmt(v) for v in df[COLUMNS[1]]]
    left = max(labels.map(len).max(), len(name))
    right = width or max(len(r) for r in results)

    print(name)
    print("-" * (left + 2 + right))
    for label, result in zip(labels, results):
        print(f"{label:<{left}}  {result:>{right}}")


def compare(*names, directory=None, fmt=None):
    """Put named tables side by side, matched on the calculation's name.

    Pass tables or names. Each table keeps its own column of results, under
    its own title.
    """
    tables = [t if isinstance(t, pd.DataFrame) else load_table(t, directory, fmt)
              for t in names]
    titles = [t.attrs.get("name", f"table {i}") for i, t in enumerate(tables, 1)]

    merged = None
    for title, table in zip(titles, tables):
        part = table.rename(columns={COLUMNS[1]: title})
        merged = part if merged is None else merged.merge(
            part, on=COLUMNS[0], how="outer")

    # An outer merge sorts the keys, which would scramble the running order --
    # put the rows back as the tables introduced them.
    order = []
    for table in tables:
        for label in table[COLUMNS[0]]:
            if label not in order:
                order.append(label)
    merged = merged.set_index(COLUMNS[0]).reindex(order)
    return merged


def show_comparison(merged):
    """Print a comparison the same way: names left, one column per table."""
    print(merged.to_string(na_rep="n/a", float_format=lambda v: f"{v:,.{DIGITS}f}"))


# --- Run --------------------------------------------------------------------

def main():
    tables = {}
    for name, (financials, tvm_case) in DUMMY_TABLES.items():
        table = build_table(financials, tvm_case, name=name)
        save_table(table)
        tables[name] = table

    for name, table in tables.items():
        show(table)
        print()

    print("Comparison")
    show_comparison(compare(*tables.values()))


if __name__ == "__main__":
    main()
