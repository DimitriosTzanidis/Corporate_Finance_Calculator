"""Ties the five programs together.

Pick a calculation, type in the figures, then show, save, chart or compare
the results:

    python run_calculations.py

Every step is also an ordinary function that hands back a pandas DataFrame,
so another program can skip the menus and manipulate the tables directly:

    import Calculations_Table as tables
    import run_calculations as run

    apple = tables.load_table("apple 2024")          # a table saved earlier
    small = apple[apple["Result"].abs() < 10]        # drop the day counts
    run.chart_table(small, path="apple.png")
"""

__version__ = "1.3"

import Calculations_Table as tables
import Interactive_Console as console
import financial_ratios as ratios
import time_value_of_money as tvm
import visualize_financials as charts


LABEL_WIDTH = 18
GROWTH_POINTS = 50
SPREAD = 100          # biggest result over smallest, before bars go unreadable
DIRECTORY = "."

ACTIONS = {
    "show": ("print the table again", ("s", "print")),
    "save": ("save the table to a file", ("write",)),
    "chart": ("draw a chart of the table", ("c", "plot", "graph")),
    "load": ("load a saved table into this session", ("l", "open")),
    "compare": ("compare the tables in this session", ("cmp", "diff")),
    "list": ("list the tables in this session", ("ls", "tables")),
    "again": ("another calculation", ("a", "new", "menu")),
}

CHARTS = {
    "bars": ("one bar per result", ("b", "bar")),
    "growth": ("the value compounding over the periods", ("g", "line")),
}

RUNNERS = {}  # calculation key -> function, filled in below


# ---------------------------------------------------------------- asking

def prompt(question, default=""):
    """Ask something. Gives back the answer, the default, or None at end of input."""
    try:
        return input(question).strip() or default
    except EOFError:
        print("(no input available)")
        return None
    except KeyboardInterrupt:
        print("\n(stopped)")
        return None


def ask_yes_no(question, default=True):
    answer = prompt(f"{question} {'[Y/n]' if default else '[y/N]'} ")
    if answer is None:
        return False
    if answer == "":
        return default
    return answer.lower().startswith("y")


def ask_choice(options, question="Now what?"):
    """The console's own menu and matching, over any set of options."""
    console.menu(options, question)

    while True:
        raw = prompt("> ")
        if raw is None:
            return None
        raw = raw.lower()
        if raw in console.QUIT:
            return None
        chosen = console.match(raw, options)
        if chosen is not None:
            return chosen
        print("  Please pick one of " + ", ".join(options) + ", or 'q'.")


# ------------------------------------------------------------ the calculations

def run_ratios():
    """Ask for the figures, work out every ratio, hand back a table."""
    financials = ratios.ask_financials()
    results = ratios.RatioCalculator(financials).compute_all()
    table = tables.build_table(results, name="financial ratios")
    table.attrs["inputs"] = financials.as_dict()
    return table


def run_time_value():
    """Ask for three of the four figures, solve the fourth, hand back a table."""
    known, _target = tvm.run()
    rows = [
        ("present value", known["pv"]),
        ("future value", known["fv"]),
        ("rate (%)", known["rate"] * 100),
        ("periods", known["periods"]),
    ]
    table = tables.build_table(rows, name="time value of money")
    table.attrs["inputs"] = known
    return table


RUNNERS.update({"ratios": run_ratios, "tvm": run_time_value})


# ------------------------------------------------------------------- charts

def _short(label, width=LABEL_WIDTH):
    label = str(label)
    return label if len(label) <= width else label[:width - 1] + "\u2026"


def wide_spread(table, factor=SPREAD):
    """True when the largest result would flatten the smallest into nothing."""
    sizes = [abs(value) for value in table[tables.COLUMNS[1]]
             if value == value and value]
    return len(sizes) > 1 and max(sizes) / min(sizes) > factor


def parse_rows(answer, count):
    """'1,3,5-8' -> [0, 2, 4, 5, 6, 7]"""
    picked = []
    for part in [part.strip() for part in answer.split(",") if part.strip()]:
        first, _, last = part.partition("-")
        try:
            start, end = int(first), int(last or first)
        except ValueError:
            print(f"  Not a row number: '{part}'.")
            continue
        for number in range(start, end + 1):
            if 1 <= number <= count and number - 1 not in picked:
                picked.append(number - 1)
    return picked


def pick_rows(table):
    """Number the rows and keep the ones asked for. Blank keeps the lot."""
    labels = [str(label) for label in table[tables.COLUMNS[0]]]
    width = max(len(label) for label in labels)
    for number, (label, value) in enumerate(
            zip(labels, table[tables.COLUMNS[1]]), 1):
        print(f"  {number:<3} {label:<{width}}  "
              f"{tables.format_result(value)}")

    answer = prompt("Rows to chart (blank for all, e.g. 1,3,5-8): ")
    picked = parse_rows(answer, len(labels)) if answer else []
    if not picked:
        return table
    chosen = table.iloc[picked].copy()
    chosen.attrs.update(table.attrs)
    return chosen


def chart_table(table, path=None, title=None):
    """A bar per result. Missing results are left out."""
    rows = table.dropna(subset=[tables.COLUMNS[1]])
    if rows.empty:
        print("  Nothing to chart: every result is missing.")
        return None
    return charts.plot_bars(
        [_short(label) for label in rows[tables.COLUMNS[0]]],
        list(rows[tables.COLUMNS[1]]),
        title=title or table.attrs.get("name") or "",
        ylabel="result", path=path)


def growth_series(known, points=GROWTH_POINTS):
    """The present value compounding forward, a point at a time."""
    steps = [known["periods"] * number / points for number in range(points + 1)]
    values = [tvm.future_value(known["pv"], known["rate"], step)
              for step in steps]
    return charts.Series(steps, values,
                         label=f"{known['rate'] * 100:g}% per period")


def chart_growth(table, path=None):
    """The line behind a time value of money table."""
    known = table.attrs.get("inputs") or {}
    if not known.get("periods"):
        print("  No growth to draw: this table has no periods behind it.")
        return None
    return charts.plot_lines([growth_series(known)],
                             title=table.attrs.get("name") or "",
                             xlabel="period", ylabel="value", path=path)


def chart_comparison(merged, path=None, columns=3):
    """One small panel per calculation, so different scales do not fight."""
    titles = list(merged.columns)
    series = []
    for label, row in merged.iterrows():
        values = [row[title] for title in titles]
        if all(value != value for value in values):  # every one missing
            continue
        series.append(charts.Series(titles, values, label=_short(label, 24)))

    if not series:
        print("  Nothing to chart: every result is missing.")
        return None
    # No suptitle: the table names are already along the foot of every panel,
    # and plot_grid's tight_layout would run the two into each other.
    return charts.plot_grid(series, columns=columns, path=path)


# ---------------------------------------------------- the tables in hand

def unique_name(name, session):
    if name not in session:
        return name
    number = 2
    while f"{name} ({number})" in session:
        number += 1
    return f"{name} ({number})"


def remember(table, session):
    """Name the table (handy when comparing) and keep it for this session."""
    suggestion = unique_name(table.attrs.get("name") or "table", session)
    answer = prompt(f"Name for this table [{suggestion}]: ", suggestion)
    name = unique_name(answer or suggestion, session)
    table.attrs["name"] = name
    session[name] = table
    return name


def list_tables(session):
    if not session:
        print("  No tables yet.")
        return []
    names = list(session)
    for number, name in enumerate(names, 1):
        print(f"  {number:<3} {name}  ({len(session[name])} rows)")
    return names


def choose_tables(session, question="Which tables?"):
    names = list_tables(session)
    if not names:
        return []
    answer = prompt(f"{question} (blank for all): ")
    if answer is None:
        return []
    if not answer:
        return names

    chosen = []
    for part in [part.strip() for part in answer.split(",")]:
        if part.isdigit() and 1 <= int(part) <= len(names):
            chosen.append(names[int(part) - 1])
        elif part in session:
            chosen.append(part)
        else:
            print(f"  No table called '{part}'.")
    return chosen


# ------------------------------------------------------------- the actions

def save_action(table):
    name = prompt(f"File name [{table.attrs.get('name')}]: ",
                  table.attrs.get("name"))
    fmt = prompt("Format, csv or xlsx [csv]: ", "csv")
    directory = prompt(f"Folder [{DIRECTORY}]: ", DIRECTORY)
    if name is None or fmt is None or directory is None:
        return None
    try:
        path = tables.save_table(table, name=name, directory=directory, fmt=fmt)
    except (OSError, ValueError, ImportError) as trouble:
        print(f"  Could not save it: {trouble}")
        return None
    print(f"Saved to {path}")
    return path


def load_action(session):
    name = prompt("File name (without the extension): ")
    if not name:
        return None
    fmt = prompt("Format, csv or xlsx [csv]: ", "csv")
    directory = prompt(f"Folder [{DIRECTORY}]: ", DIRECTORY)
    if fmt is None or directory is None:
        return None
    try:
        table = tables.load_table(name, directory, fmt)
    except (OSError, ValueError, KeyError) as trouble:
        print(f"  Could not load it: {trouble}")
        return None

    remember(table, session)
    print()
    tables.show(table)
    return table


def chart_action(table):
    kind = "bars"
    if (table.attrs.get("inputs") or {}).get("periods"):
        kind = ask_choice(CHARTS, "Which chart?")
        if kind is None:
            return None

    rows = table
    if kind == "bars" and wide_spread(table):
        print("\n  These results sit on very different scales, so the small "
              "ones will vanish next to the big ones.")
        rows = pick_rows(table)

    path = prompt("Image file (blank to show it on screen): ")
    if path is None:
        return None
    if kind == "growth":
        return chart_growth(table, path=path or None)
    return chart_table(rows, path=path or None)


def compare_action(session):
    if len(session) < 2:
        print("  Two tables are needed. Run another calculation, "
              "or load a saved one.")
        return None

    chosen = choose_tables(session)
    if len(chosen) < 2:
        print("  Two tables are needed.")
        return None

    merged = tables.compare(*[session[name] for name in chosen])
    print()
    tables.show_comparison(merged)

    if ask_yes_no("\nChart it?", False):
        path = prompt("Image file (blank to show it on screen): ")
        chart_comparison(merged, path=path or None)

    if ask_yes_no("Save it to a csv?", False):
        name = prompt("File name [comparison]: ", "comparison")
        if name:
            path = tables.table_path(name, DIRECTORY, "csv")
            merged.to_csv(path)
            print(f"Saved to {path}")
    return merged


def output_menu(table, session):
    """True to go back for another calculation, False to stop."""
    while True:
        action = ask_choice(ACTIONS)
        if action is None:
            return False
        if action == "again":
            return True
        if action == "show":
            print()
            tables.show(table)
        elif action == "save":
            save_action(table)
        elif action == "chart":
            chart_action(table)
        elif action == "load":
            load_action(session)
        elif action == "compare":
            compare_action(session)
        elif action == "list":
            list_tables(session)


# ---------------------------------------------------------------- the loop

def check_registry():
    """Warn if the console offers a calculation nothing here can run."""
    missing = [key for key in console.CALCULATIONS if key not in RUNNERS]
    if missing:
        print("Warning: no runner for " + ", ".join(missing))


def main():
    check_registry()
    session = {}

    while True:
        chosen = console.ask_calculation()
        if chosen is None:
            break

        runner = RUNNERS.get(chosen)
        if runner is None:
            print(f"  '{chosen}' has no runner yet.")
            continue

        print(f"\n{console.CALCULATIONS[chosen][0]}\n")
        try:
            table = runner()
        except EOFError:
            print("(no input available)")
            break
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        if table is None:
            continue

        remember(table, session)
        print()
        tables.show(table)

        if not output_menu(table, session):
            break

    print("\nBye.")
    return session


if __name__ == "__main__":
    main()
