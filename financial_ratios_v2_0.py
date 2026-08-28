__version__ = "2.0"

# ---------------------------------------------------------------------------
# Financial ratio calculator - object-oriented edition.
#
# Same behaviour as 1.4, reorganised into classes:
#   Financials        - the figures, with None meaning "unknown"
#   Identity          - one accounting identity, able to solve for a blank
#   RatioCalculator   - one method per ratio, auto-registered in order
#   Report            - printing of derived values and ratio lines
#   ConsoleApp        - the interactive prompt loop
#
# Every input still defaults to None, identities are still resolved to a fixed
# point before anything is computed, and ratios that lack data still report
# "n/a".
# ---------------------------------------------------------------------------


def safe_div(numerator, denominator):
    """Divide, but return None if data is missing or the denominator is zero."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


# --- Accounting identities --------------------------------------------------

class Identity:
    """One accounting identity over a set of fields.

    `terms` lists the fields involved. `solvers` maps each field to a function
    that computes it from the Financials once every other term is known.
    An identity only fires when exactly one of its terms is missing.
    """

    def __init__(self, name, terms, solvers):
        self.name = name
        self.terms = tuple(terms)
        self.solvers = solvers

    def missing(self, financials):
        return [t for t in self.terms if financials[t] is None]

    def apply(self, financials):
        """Fill in the single blank term, if there is exactly one."""
        blanks = self.missing(financials)
        if len(blanks) != 1:
            return False
        field = blanks[0]
        financials[field] = self.solvers[field](financials)
        return True


BALANCE_SHEET = Identity(
    "total_assets = total_liabilities + total_equity",
    ("total_assets", "total_liabilities", "total_equity"),
    {
        "total_assets": lambda f: f["total_liabilities"] + f["total_equity"],
        "total_liabilities": lambda f: f["total_assets"] - f["total_equity"],
        "total_equity": lambda f: f["total_assets"] - f["total_liabilities"],
    },
)

NET_FIXED_ASSETS = Identity(
    "net_fixed_assets = fixed_assets + capital_improvements - depreciation",
    ("net_fixed_assets", "fixed_assets", "capital_improvements", "depreciation"),
    {
        "net_fixed_assets":
            lambda f: f["fixed_assets"] + f["capital_improvements"] - f["depreciation"],
        "fixed_assets":
            lambda f: f["net_fixed_assets"] - f["capital_improvements"] + f["depreciation"],
        "capital_improvements":
            lambda f: f["net_fixed_assets"] - f["fixed_assets"] + f["depreciation"],
        "depreciation":
            lambda f: f["fixed_assets"] + f["capital_improvements"] - f["net_fixed_assets"],
    },
)


# --- The figures ------------------------------------------------------------

class Financials:
    """The raw figures, plus whatever the identities can derive from them."""

    FIELDS = (
        "sales", "cogs", "ebit", "interest", "net_income", "depreciation",
        "current_assets", "inventory", "cash", "accounts_receivable",
        "current_liabilities", "accounts_payable",
        "fixed_assets", "capital_improvements", "net_fixed_assets",
        "total_assets", "total_liabilities", "total_equity",
        "long_term_debt", "price_per_share", "earnings_per_share",
    )

    IDENTITIES = (BALANCE_SHEET, NET_FIXED_ASSETS)

    def __init__(self, **values):
        unknown = set(values) - set(self.FIELDS)
        if unknown:
            raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
        self._raw = {field: values.get(field) for field in self.FIELDS}
        self._data = dict(self._raw)

    # dict-ish access, so identities and ratios can read fields naturally
    def __getitem__(self, field):
        return self._data[field]

    def __setitem__(self, field, value):
        self._data[field] = value

    def get(self, field, default=None):
        return self._data.get(field, default)

    def as_dict(self):
        return dict(self._data)

    def resolve(self):
        """Apply every identity repeatedly until nothing new can be filled,
        so a value derived by one identity can feed the next."""
        changed = True
        while changed:
            before = dict(self._data)
            for identity in self.IDENTITIES:
                identity.apply(self)
            changed = self._data != before
        return self

    def derived(self):
        """Fields that were blank on input but have a value now."""
        return {field: self._data[field] for field in self.FIELDS
                if self._raw[field] is None and self._data[field] is not None}


# --- Ratios -----------------------------------------------------------------

def ratio(name):
    """Mark a method as a named ratio, for auto-registration."""
    def decorate(method):
        method.ratio_name = name
        return method
    return decorate


class RatioCalculator:
    """One method per ratio. Each returns a number, or None if data is missing."""

    def __init__(self, financials):
        self.f = financials

    # Registry of name -> method, in definition order.
    @classmethod
    def handlers(cls):
        registry = {}
        for attr in vars(cls).values():
            name = getattr(attr, "ratio_name", None)
            if name is not None:
                registry[name] = attr
        return registry

    def names(self):
        return list(self.handlers())

    def compute(self, name):
        """Compute one ratio by name. Raises KeyError if the name is unknown."""
        return self.handlers()[name](self)

    # --- Liquidity ----------------------------------------------------------

    @ratio("current ratio")
    def current_ratio(self):
        return safe_div(self.f["current_assets"], self.f["current_liabilities"])

    @ratio("quick ratio")
    def quick_ratio(self):
        ca, inv = self.f["current_assets"], self.f["inventory"]
        if ca is None or inv is None:
            return None
        return safe_div(ca - inv, self.f["current_liabilities"])

    @ratio("cash ratio")
    def cash_ratio(self):
        return safe_div(self.f["cash"], self.f["current_liabilities"])

    @ratio("net working capital to total assets")
    def nwc_to_total_assets(self):
        ca, cl = self.f["current_assets"], self.f["current_liabilities"]
        if ca is None or cl is None:
            return None
        return safe_div(ca - cl, self.f["total_assets"])

    # --- Activity / turnover ------------------------------------------------

    @ratio("inventory turnover")
    def inventory_turnover(self):
        return safe_div(self.f["cogs"], self.f["inventory"])

    @ratio("days' sales in inventory")
    def days_sales_in_inventory(self):
        return safe_div(365, self.inventory_turnover())

    @ratio("receivables turnover")
    def receivables_turnover(self):
        return safe_div(self.f["sales"], self.f["accounts_receivable"])

    @ratio("days' sales in receivables")
    def days_sales_in_receivables(self):
        return safe_div(365, self.receivables_turnover())

    @ratio("payables turnover")
    def payables_turnover(self):
        return safe_div(self.f["cogs"], self.f["accounts_payable"])

    @ratio("days' sales in payables")
    def days_sales_in_payables(self):
        return safe_div(365, self.payables_turnover())

    @ratio("net working capital turnover")
    def nwc_turnover(self):
        ca, cl = self.f["current_assets"], self.f["current_liabilities"]
        if ca is None or cl is None:
            return None
        return safe_div(self.f["sales"], ca - cl)

    @ratio("property plant and equipment turnover")
    def ppe_turnover(self):
        return safe_div(self.f["sales"], self.f["net_fixed_assets"])

    @ratio("total asset turnover")
    def total_asset_turnover(self):
        return safe_div(self.f["sales"], self.f["total_assets"])

    # --- Leverage / solvency ------------------------------------------------

    @ratio("total debt ratio")
    def total_debt_ratio(self):
        return safe_div(self.f["total_liabilities"], self.f["total_assets"])

    @ratio("debt-equity ratio")
    def debt_equity_ratio(self):
        return safe_div(self.f["total_liabilities"], self.f["total_equity"])

    @ratio("equity multiplier")
    def equity_multiplier(self):
        return safe_div(self.f["total_assets"], self.f["total_equity"])

    @ratio("long-term debt ratio")
    def long_term_debt_ratio(self):
        ltd, te = self.f["long_term_debt"], self.f["total_equity"]
        if ltd is None or te is None:
            return None
        return safe_div(ltd, ltd + te)

    @ratio("times interest earned ratio")
    def times_interest_earned(self):
        return safe_div(self.f["ebit"], self.f["interest"])

    @ratio("cash coverage ratio")
    def cash_coverage_ratio(self):
        ebit, dep = self.f["ebit"], self.f["depreciation"]
        if ebit is None or dep is None:
            return None
        return safe_div(ebit + dep, self.f["interest"])

    # --- Profitability ------------------------------------------------------

    @ratio("profit margin")
    def profit_margin(self):
        return safe_div(self.f["net_income"], self.f["sales"])

    @ratio("return on capital employed")
    def return_on_capital_employed(self):
        ta, cl = self.f["total_assets"], self.f["current_liabilities"]
        if ta is None or cl is None:
            return None
        return safe_div(self.f["ebit"], ta - cl)

    @ratio("return on assets")
    def return_on_assets(self):
        return safe_div(self.f["net_income"], self.f["total_assets"])

    @ratio("return on equity")
    def return_on_equity(self):
        return safe_div(self.f["net_income"], self.f["total_equity"])

    @ratio("du pont identity")
    def du_pont_identity(self):
        pm = self.profit_margin()
        tat = self.total_asset_turnover()
        em = self.equity_multiplier()
        if pm is None or tat is None or em is None:
            return None
        return pm * tat * em

    # --- Market value -------------------------------------------------------

    @ratio("price-earnings ratio")
    def price_earnings_ratio(self):
        return safe_div(self.f["price_per_share"], self.f["earnings_per_share"])


# --- Output -----------------------------------------------------------------

class Report:
    """Prints derived values and ratio results."""

    def __init__(self, calculator, digits=4):
        self.calculator = calculator
        self.digits = digits

    def dispatch(self, name):
        """Compute and print one ratio by name."""
        try:
            value = self.calculator.compute(name)
        except KeyError:
            print(f"{name}: unknown ratio")
            return None
        if value is None:
            print(f"{name}: n/a (missing data)")
        else:
            print(f"{name}: {round(value, self.digits)}")
        return value

    def print_derived(self, financials):
        derived = financials.derived()
        if derived:
            print("\nDerived from identities:")
            for field, value in derived.items():
                print(f"  {field} = {round(value, self.digits)}")

    def print_all(self):
        for name in self.calculator.names():
            self.dispatch(name)


# --- Interactive front end --------------------------------------------------

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
        values = {field: self.ask_number(field) for field in Financials.FIELDS}
        return Financials(**values)

    def run(self):
        financials = self.get_financials().resolve()
        report = Report(RatioCalculator(financials))
        report.print_derived(financials)
        print()
        report.print_all()


def main():
    ConsoleApp().run()


if __name__ == "__main__":
    main()
