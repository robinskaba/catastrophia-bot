import asyncio
import io

import matplotlib
import matplotlib.pyplot as plt
from discord import File

# Use a non-interactive backend for thread safety when rendering images
matplotlib.use("Agg")


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
    
    # Remove the horizontal gap before the first point and ensure the fill touches the bottom
    ax.margins(x=0)
    ax.set_ylim(bottom=0)

    ax.set_title(
        title,
        fontsize=17,
        fontweight="bold" if title_bold else "normal",
        pad=15,
        color="#e5e5e5",
    )

    if x_axis_title:
        ax.set_xlabel(x_axis_title, fontsize=11, color="#aaaaaa")
    if y_axis_title:
        ax.set_ylabel(y_axis_title, fontsize=11, color="#aaaaaa")

    if y_tick_prefix or y_tick_suffix:
        from matplotlib.ticker import StrMethodFormatter

        ax.yaxis.set_major_formatter(
            StrMethodFormatter(f"{y_tick_prefix}{{x:g}}{y_tick_suffix}")
        )

    ax.grid(color="#777777", linestyle="--", linewidth=0.5, alpha=0.3)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#777777")
    ax.spines["left"].set_color("#777777")

    ax.tick_params(colors="#aaaaaa")
    if x_tick_rotation:
        ax.tick_params(axis="x", rotation=x_tick_rotation)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", transparent=True)
    buffer.seek(0)
    plt.close(fig)

    return buffer


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
