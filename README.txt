Financial calculators
=====================

Five files in two layers. The calculation modules hold the arithmetic and
never ask a question or print a result; the front ends do the asking and the
printing and own no arithmetic of their own. Nothing is reimplemented in two
places -- a front end that needs a formula imports it.


The calculation modules
-----------------------

  financial_ratios_v2_0.py      2.0
      The figures, the accounting identities that fill in blanks among them,
      and twenty-four ratios built on the result. Four classes carry it:
      Financials (the figures, None meaning unknown), Identity (one identity,
      able to solve for a single blank), RatioCalculator (one method per
      ratio, registered in the order they are defined), Report (printing).

  time_value_of_money_v1_2.py   1.2
      One relationship, four unknowns: fv = pv * (1 + r) ** t. Given any
      three, solve for the fourth. Also the input helpers the other programs
      borrow (ask_number, ask_rate, tidy), so a prompt behaves the same way
      wherever it appears.

Both modules run on their own as small console programs, which is what their
main() is for. Neither imports the other.


The front ends
--------------

  Interactive_Console.py        1.1
      The front door. Asks which calculator you want and runs it, then asks
      again, until you quit. Ratios and time value of money are handled here;
      tables and charts are handed to the two programs below, imported only
      when chosen so that pandas and matplotlib stay optional.

  Calculations_Table.py         1.2
      Every derived figure, every ratio and every time-value answer for a set
      of numbers, as one two-column table. Builds one table per dummy set,
      saves them (CSV by default, xlsx if asked), prints them, and prints a
      comparison with the sets side by side, matched on the calculation's
      name. Needs pandas.

  visualize_financials_v1_1.py  1.2
      The time value of money drawn rather than printed. Three views: a sweep
      (one amount, one line per rate), cases on shared axes, and a grid of one
      panel per case. Rate is carried by colour, so a chart shows t, value and
      r at once. Needs matplotlib.


Running them
------------

  python3 Interactive_Console.py        everything, through a menu
  python3 Calculations_Table.py         the dummy tables
  python3 visualize_financials_v1_1.py  the charts
  python3 financial_ratios_v2_0.py      ratios alone
  python3 time_value_of_money_v1_2.py   time value of money alone

Each of the three front ends puts /mnt/project and its own directory at the
front of sys.path, its own directory last, so a module sitting beside the file
wins over any fallback copy. They can be run from anywhere.

Every program will also run unattended, with input piped or redirected or
absent. Rather than failing at the first prompt each falls back to something
sensible: the console quits, the table saves to its default directory, the
charts draw the dummy cases. This is what makes them safe to schedule.


Conventions
-----------

Missing data is None, and it travels. A ratio with a missing input is None
rather than zero or an error, prints as "n/a", and lands in a table as a blank
cell. Nothing invented, nothing guessed, and one missing figure costs you that
figure rather than the whole run.

Blanks that can be recovered are recovered first. Two identities do that work:

  total_assets      = total_liabilities + total_equity
  net_fixed_assets  = fixed_assets + capital_improvements - depreciation

An identity fires only when exactly one of its terms is missing, and they are
applied repeatedly until nothing further can be filled -- so a figure one
identity derives can be what the next one needs. Anything filled this way is
reported as derived, never quietly mixed in with what you supplied.

Two different failures, told apart by how they arrive. None means the question
has no real answer: no rate turns 0 into 1,000, no number of periods brings a
value to one of the opposite sign. NegativePeriods means the answer exists but
faces backwards -- a value falling at a positive rate reaches its target only
by running time in reverse. It is raised rather than returned, because a
negative t returned is a negative t that some caller forgets to test for and
prints as though it meant something.

Rates may be negative; periods may not. A negative rate is erosion, which is a
real thing to model. Negative periods are refused on input and refused on
output. A rate of -100% or lower is refused too: it leaves 1 + r at zero or
below, and a negative base under the fractional powers a smooth line needs
comes back complex, which is not a thing that can be plotted.

Rates are percentages at every prompt and decimals in every formula. You type
5, the maths gets 0.05, and the display gets 5% back. The conversion happens
once, at the edge.


The dummy data
--------------

Three sets, in Calculations_Table.py. Two are complete and ordinary -- taff
and brill, near enough alike to be worth comparing. The third, corrin, is
deliberately patchy, so that the ways of saying "no number here" are on show
rather than merely implemented:

  inventory and accounts_receivable are unknown, so the ratios that need them
  report n/a while the rest of the column fills in as usual;

  total_liabilities and net_fixed_assets are unknown but recoverable, so each
  identity has a different blank to solve and both turn up as derived;

  the share price and earnings per share are absent, so price-earnings has
  nothing to divide;

  its time-value case falls from 2,000 to 1,000 at a positive rate, which is
  the case solve_periods refuses, so the solved-periods row is blank.

The chart module keeps its own dummy set, DUMMY_CASES, along the same lines:
the ordinary cases, a rate that erodes rather than grows, an amount owed
rather than held, and one case of each kind that gets refused.
