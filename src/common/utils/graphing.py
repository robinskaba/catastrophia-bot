import asyncio
import io
from datetime import datetime, tzinfo

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from discord import File
from matplotlib.ticker import FuncFormatter, MaxNLocator

matplotlib.use("Agg")

_TEXT_COLOR = "#e5e5e5"
_MUTED_COLOR = "#aaaaaa"
_AXIS_COLOR = "#777777"
_LABEL_BACKGROUND = "#1e1f22"


def _style_axes(
    ax,
    title: str,
    x_axis_title: str | None,
    y_axis_title: str | None,
    title_bold: bool,
    y_tick_prefix: str,
    y_tick_suffix: str,
    x_tick_rotation: int,
) -> None:
    ax.set_title(
        title,
        fontsize=17,
        fontweight="bold" if title_bold else "normal",
        pad=15,
        color=_TEXT_COLOR,
    )

    if x_axis_title:
        ax.set_xlabel(x_axis_title, fontsize=11, color=_MUTED_COLOR)
    if y_axis_title:
        ax.set_ylabel(y_axis_title, fontsize=11, color=_MUTED_COLOR)

    def format_y_ticks(x, pos):
        if x.is_integer():
            base = f"{int(x):,}"
        else:
            base = f"{x:,.1f}"

        spaced = base.replace(",", " ")
        return f"{y_tick_prefix}{spaced}{y_tick_suffix}"

    ax.yaxis.set_major_formatter(FuncFormatter(format_y_ticks))

    ax.grid(color=_AXIS_COLOR, linestyle="--", linewidth=0.5, alpha=0.3)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(_AXIS_COLOR)
    ax.spines["left"].set_color(_AXIS_COLOR)

    ax.tick_params(colors=_MUTED_COLOR)
    if x_tick_rotation:
        ax.tick_params(axis="x", rotation=x_tick_rotation)


def _save_figure(fig) -> io.BytesIO:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", transparent=True)
    buffer.seek(0)
    plt.close(fig)
    return buffer


def _generate_line_graph_sync(
    title: str,
    x_data: list,
    y_data: list,
    color: str,
    x_axis_title: str | None,
    y_axis_title: str | None,
    title_bold: bool,
    y_tick_prefix: str,
    y_tick_suffix: str,
    x_tick_rotation: int,
) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(x_data, y_data, color=color, linewidth=2.5, marker="o", markersize=6)
    ax.fill_between(x_data, y_data, color=color, alpha=0.1)

    ax.margins(x=0)
    ax.set_ylim(bottom=0)

    _style_axes(
        ax,
        title,
        x_axis_title,
        y_axis_title,
        title_bold,
        y_tick_prefix,
        y_tick_suffix,
        x_tick_rotation,
    )

    return _save_figure(fig)


async def create_line_graph(
    title: str,
    x_data: list,
    y_data: list,
    color: str = "#5865F2",
    x_axis_title: str | None = None,
    y_axis_title: str | None = None,
    title_bold: bool = True,
    y_tick_prefix: str = "",
    y_tick_suffix: str = "",
    x_tick_rotation: int = 0,
) -> File:
    buffer = await asyncio.to_thread(
        _generate_line_graph_sync,
        title,
        x_data,
        y_data,
        color,
        x_axis_title,
        y_axis_title,
        title_bold,
        y_tick_prefix,
        y_tick_suffix,
        x_tick_rotation,
    )
    return File(buffer, filename="graph.png")


def _annotate_extreme(ax, x, y, label: str, color: str, above: bool, x_frac: float):
    ax.scatter(
        [x],
        [y],
        s=30,
        color=color,
        edgecolors=_LABEL_BACKGROUND,
        linewidths=1.2,
        zorder=5,
        clip_on=False,
    )

    # keep labels near the edges inside the plot
    if x_frac < 0.1:
        ha = "left"
    elif x_frac > 0.9:
        ha = "right"
    else:
        ha = "center"

    ax.annotate(
        label,
        xy=(x, y),
        xytext=(0, 10 if above else -10),
        textcoords="offset points",
        ha=ha,
        va="bottom" if above else "top",
        fontsize=10,
        fontweight="bold",
        color=_TEXT_COLOR,
        # backing box keeps the label readable on top of the line and band
        bbox=dict(
            boxstyle="round,pad=0.3", fc=_LABEL_BACKGROUND, ec="none", alpha=0.85
        ),
        zorder=6,
    )


def _last_index(values: np.ndarray, target: float) -> int:
    return int(np.flatnonzero(values == target)[-1])


def _generate_range_graph_sync(
    title: str,
    times: list[datetime],
    averages: list[float | None],
    lows: list[int | None],
    highs: list[int | None],
    color: str,
    tz: tzinfo,
    y_axis_title: str | None,
) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(10, 4.5))

    # None -> NaN so gaps in data break the line instead of bridging it
    avg_arr = np.array(averages, dtype=float)
    low_arr = np.array(lows, dtype=float)
    high_arr = np.array(highs, dtype=float)

    # band shows the full range within each time bucket, line shows the average
    ax.fill_between(times, low_arr, high_arr, color=color, alpha=0.25, linewidth=0)
    ax.plot(times, avg_arr, color=color, linewidth=2)

    peak = np.nanmax(high_arr)
    lowest = np.nanmin(low_arr)
    peak_i = _last_index(high_arr, peak)
    low_i = _last_index(low_arr, lowest)

    ax.margins(x=0)
    ax.set_ylim(bottom=0, top=max(peak * 1.18, 1))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    locator = mdates.AutoDateLocator(tz=tz, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator, tz=tz))

    last = max(len(times) - 1, 1)
    _annotate_extreme(
        ax,
        times[peak_i],
        peak,
        f"Peak: {int(peak)}",
        color,
        above=True,
        x_frac=peak_i / last,
    )
    # put the low label above the marker when there is no room below it
    _annotate_extreme(
        ax,
        times[low_i],
        lowest,
        f"Low: {int(lowest)}",
        color,
        above=lowest < peak * 0.15,
        x_frac=low_i / last,
    )

    _style_axes(
        ax,
        title,
        x_axis_title=None,
        y_axis_title=y_axis_title,
        title_bold=True,
        y_tick_prefix="",
        y_tick_suffix="",
        x_tick_rotation=0,
    )
    ax.xaxis.get_offset_text().set_color(_MUTED_COLOR)

    return _save_figure(fig)


async def create_range_graph(
    title: str,
    times: list[datetime],
    averages: list[float | None],
    lows: list[int | None],
    highs: list[int | None],
    tz: tzinfo,
    color: str = "#5865F2",
    y_axis_title: str | None = None,
) -> File:
    buffer = await asyncio.to_thread(
        _generate_range_graph_sync,
        title,
        times,
        averages,
        lows,
        highs,
        color,
        tz,
        y_axis_title,
    )
    return File(buffer, filename="graph.png")
