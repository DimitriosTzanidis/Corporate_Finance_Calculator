__version__ = "1.4"

from pathlib import Path

import pandas as pd


COLUMNS = ["Calculation", "Result"]
DIGITS = 4
FILE_FORMAT = "csv"
OUTPUT_DIR = "."


def _round(value):
    return float("nan") if value is None else round(value, DIGITS)


def _rows(results):
    pairs = results.items() if isinstance(results, dict) else results
    return [(str(label), _round(value)) for label, value in pairs]


def build_table(results, name=None):
    df = pd.DataFrame(_rows(results), columns=COLUMNS)
    df[COLUMNS[1]] = pd.to_numeric(df[COLUMNS[1]], errors="coerce")
    df.attrs["name"] = name
    return df


def table_path(name, directory=None, fmt=None):
    return Path(directory or OUTPUT_DIR) / f"{name}.{fmt or FILE_FORMAT}"


def save_table(df, name=None, directory=None, fmt=None):
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
    path = table_path(name, directory, fmt)
    df = (pd.read_excel(path, skiprows=1) if path.suffix == ".xlsx"
          else pd.read_csv(path, skiprows=1))
    df[COLUMNS[1]] = pd.to_numeric(df[COLUMNS[1]], errors="coerce")
    df.attrs["name"] = name
    return df


def format_result(value):
    return "n/a" if pd.isna(value) else f"{value:,.{DIGITS}f}"


def show(df, name=None):
    name = name or df.attrs.get("name") or ""
    labels = [str(label) for label in df[COLUMNS[0]]]
    results = [format_result(value) for value in df[COLUMNS[1]]]
    left = max([len(label) for label in labels] + [len(name)])
    right = max([len(result) for result in results] + [len(COLUMNS[1])])

    print(name)
    print("-" * (left + 2 + right))
    for label, result in zip(labels, results):
        print(f"{label:<{left}}  {result:>{right}}")


def compare(*tables):
    titles = [table.attrs.get("name") or f"table {number}"
              for number, table in enumerate(tables, 1)]

    merged = None
    for title, table in zip(titles, tables):
        part = table.rename(columns={COLUMNS[1]: title})
        merged = part if merged is None else merged.merge(
            part, on=COLUMNS[0], how="outer")

    order = []
    for table in tables:
        for label in table[COLUMNS[0]]:
            if label not in order:
                order.append(label)
    return merged.set_index(COLUMNS[0]).reindex(order)


def show_comparison(merged):
    print(merged.to_string(na_rep="n/a",
                           float_format=lambda value: f"{value:,.{DIGITS}f}"))
