__version__ = "2.3"


FIELDS = (
    "sales", "cogs", "ebit", "net_income",
    "current_assets", "inventory", "cash", "accounts_receivable",
    "current_liabilities", "accounts_payable",
    "total_assets", "total_liabilities", "total_equity",
    "long_term_debt", "price_per_share", "earnings_per_share",
)

DIGITS = 4


def safe_div(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def ratio(name):
    def decorate(method):
        method.ratio_name = name
        return method
    return decorate


class Financials:

    def __init__(self, **values):
        unknown = set(values) - set(FIELDS)
        if unknown:
            raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
        self._data = {field: values.get(field) for field in FIELDS}

    def __getitem__(self, field):
        return self._data[field]

    def __setitem__(self, field, value):
        self._data[field] = value

    def get(self, field, default=None):
        return self._data.get(field, default)

    def as_dict(self):
        return dict(self._data)


class RatioCalculator:

    def __init__(self, financials):
        self.f = financials

    @classmethod
    def handlers(cls):
        registry = {}
        for attribute in vars(cls).values():
            name = getattr(attribute, "ratio_name", None)
            if name is not None:
                registry[name] = attribute
        return registry

    def names(self):
        return list(self.handlers())

    def compute(self, name):
        return self.handlers()[name](self)

    def compute_all(self):
        return {name: handler(self)
                for name, handler in self.handlers().items()}

    @ratio("quick ratio")
    def quick_ratio(self):
        ca, inventory = self.f["current_assets"], self.f["inventory"]
        if ca is None or inventory is None:
            return None
        return safe_div(ca - inventory, self.f["current_liabilities"])

    @ratio("cash ratio")
    def cash_ratio(self):
        return safe_div(self.f["cash"], self.f["current_liabilities"])

    @ratio("net working capital to total assets")
    def nwc_to_total_assets(self):
        ca, cl = self.f["current_assets"], self.f["current_liabilities"]
        if ca is None or cl is None:
            return None
        return safe_div(ca - cl, self.f["total_assets"])

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

    @ratio("total asset turnover")
    def total_asset_turnover(self):
        return safe_div(self.f["sales"], self.f["total_assets"])

    @ratio("debt-equity ratio")
    def debt_equity_ratio(self):
        return safe_div(self.f["total_liabilities"], self.f["total_equity"])

    @ratio("equity multiplier")
    def equity_multiplier(self):
        return safe_div(self.f["total_assets"], self.f["total_equity"])

    @ratio("long-term debt ratio")
    def long_term_debt_ratio(self):
        debt, equity = self.f["long_term_debt"], self.f["total_equity"]
        if debt is None or equity is None:
            return None
        return safe_div(debt, debt + equity)

    @ratio("profit margin")
    def profit_margin(self):
        return safe_div(self.f["net_income"], self.f["sales"])

    @ratio("return on capital employed")
    def return_on_capital_employed(self):
        ta, cl = self.f["total_assets"], self.f["current_liabilities"]
        if ta is None or cl is None:
            return None
        return safe_div(self.f["ebit"], ta - cl)

    @ratio("return on equity (du pont identity)")
    def du_pont_identity(self):
        margin = self.profit_margin()
        turnover = self.total_asset_turnover()
        multiplier = self.equity_multiplier()
        if margin is None or turnover is None or multiplier is None:
            return None
        return margin * turnover * multiplier

    @ratio("price-earnings ratio")
    def price_earnings_ratio(self):
        return safe_div(self.f["price_per_share"], self.f["earnings_per_share"])


def ask_number(field):
    while True:
        raw = input(f"{field} (leave blank if unknown): ").strip()
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number, or leave it blank if unknown.")


def ask_financials():
    values = {}
    for field in FIELDS:
        values[field] = ask_number(field)
    return Financials(**values)


def format_result(value, digits=DIGITS):
    return "n/a (missing data)" if value is None else str(round(value, digits))


def print_results(results, digits=DIGITS):
    for name, value in results.items():
        print(f"{name}: {format_result(value, digits)}")


def main():
    calculator = RatioCalculator(ask_financials())
    print()
    print_results(calculator.compute_all())


if __name__ == "__main__":
    main()
