__version__ = "1.2"

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


FIGURE_SIZE = (10, 6)
PANEL_SIZE = (3.6, 3.1)
DPI = 150
LEGEND_LIMIT = 8


class Series:

    def __init__(self, x, y, label=None):
        self.x = list(x)
        self.y = _numeric(y)
        self.label = label

    def rows(self):
        return list(zip(self.x, self.y))


def _numeric(values):
    return [float("nan") if value is None else float(value)
            for value in values]


def _finite(values):
    return [value for value in values if value == value]


def amount_formatter(values):
    finite = _finite(values)
    span = max((abs(value) for value in finite), default=1) or 1
    places = 0 if span >= 100 else (2 if span >= 1 else 4)
    return FuncFormatter(lambda value, _position: f"{value:,.{places}f}")


def percent_formatter(value, _position=None):
    return f"{value * 100:g}%"


def finish(figure, path=None):
    figure.tight_layout()
    if path:
        path = Path(path)
        figure.savefig(path, dpi=DPI)
        print(f"Saved to {path}")
        plt.close(figure)
    else:
        plt.show()
    return figure


def _dress(axes, title="", xlabel="", ylabel=""):
    axes.set_title(title)
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.grid(True, linewidth=0.4, alpha=0.4)
    axes.axhline(0, linewidth=0.8, color="0.3")


def plot_lines(series, title="", xlabel="", ylabel="", path=None,
               legend_limit=LEGEND_LIMIT):
    if not series:
        raise ValueError("nothing to draw")

    figure, axes = plt.subplots(figsize=FIGURE_SIZE)
    everything = []
    for line in series:
        everything.extend(line.y)
        axes.plot(line.x, line.y, linewidth=2, label=line.label)

    _dress(axes, title, xlabel, ylabel)
    axes.yaxis.set_major_formatter(amount_formatter(everything))
    axes.margins(x=0)
    if len(series) <= legend_limit and any(line.label for line in series):
        axes.legend(frameon=False)
    return finish(figure, path)


def plot_bars(labels, values, title="", xlabel="", ylabel="", path=None):
    if not labels:
        raise ValueError("nothing to draw")

    heights = _numeric(values)
    figure, axes = plt.subplots(figsize=FIGURE_SIZE)
    positions = list(range(len(labels)))
    axes.bar(positions, heights, width=0.7)

    _dress(axes, title, xlabel, ylabel)
    axes.set_xticks(positions)
    axes.set_xticklabels([str(label) for label in labels],
                         rotation=45, ha="right", fontsize=8)
    axes.yaxis.set_major_formatter(amount_formatter(heights))
    return finish(figure, path)


def plot_grid(series, columns=3, title="", xlabel="", ylabel="", path=None):
    if not series:
        raise ValueError("nothing to draw")

    rows = -(-len(series) // columns)
    figure, grid = plt.subplots(rows, columns, squeeze=False,
                                figsize=(PANEL_SIZE[0] * columns,
                                         PANEL_SIZE[1] * rows))
    panels = [panel for row in grid for panel in row]

    for panel, line in zip(panels, series):
        panel.plot(line.x, line.y, linewidth=2)
        panel.set_title(line.label or "", fontsize=9)
        panel.set_xlabel(xlabel, fontsize=8)
        panel.set_ylabel(ylabel, fontsize=8)
        panel.tick_params(labelsize=8)
        panel.grid(True, linewidth=0.4, alpha=0.4)
        panel.axhline(0, linewidth=0.8, color="0.3")
        panel.yaxis.set_major_formatter(amount_formatter(line.y))

    for panel in panels[len(series):]:
        panel.axis("off")

    if title:
        figure.suptitle(title)
    return finish(figure, path)
