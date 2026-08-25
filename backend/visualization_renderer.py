"""
Visualization rendering engine for Prototype 0.0.

Converts visualization candidates produced by visualization_engine
into PNG images encoded as base64 strings for the React frontend.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd


# =========================================================
# VISUAL STYLE
# =========================================================

# ---------------------------------------------------------
# Core application palette
# ---------------------------------------------------------

VANILLA = "#FFEBAF"

MOONSTONE = "#4CD9DB"
DEEP_MOONSTONE = "#247F86"

AZURE = "#4F86F7"
LAVENDER = "#8B7CF6"
CORAL = "#F28B6D"
GOLDEN = "#E8B84A"
MINT = "#63C7A2"
ROSE = "#D97BA6"


# ---------------------------------------------------------
# Supporting chart colors
# ---------------------------------------------------------

CHART_BACKGROUND = "#FFF9E8"
GRID_COLOR = "#DDE7E8"
AXIS_COLOR = "#6C777A"
WHITE = "#FFFFFF"


# ---------------------------------------------------------
# Controlled colorful palette
# ---------------------------------------------------------

CHART_COLORS = [
    MOONSTONE,
    AZURE,
    LAVENDER,
    CORAL,
    GOLDEN,
    MINT,
    ROSE,
]


# =========================================================
# FIGURE PREPARATION
# =========================================================

def _prepare_figure():
    """Create a consistently styled matplotlib figure."""

    fig, ax = plt.subplots(
        figsize=(8, 5),
        dpi=120,
    )

    fig.patch.set_facecolor(
        VANILLA
    )

    ax.set_facecolor(
        CHART_BACKGROUND
    )

    ax.grid(
        True,
        axis="y",
        color=GRID_COLOR,
        linewidth=0.8,
        alpha=0.85,
    )

    ax.set_axisbelow(True)

    # Subtle axis styling
    ax.tick_params(
        colors=AXIS_COLOR,
        labelsize=8,
    )

    for spine in ax.spines.values():
        spine.set_color(
            "#CBD8DA"
        )

    return fig, ax


# =========================================================
# TITLE / LABEL STYLING
# =========================================================

def _style_title(
    ax,
    title: str,
):
    """Apply the application's title style."""

    ax.set_title(
        title,
        color=DEEP_MOONSTONE,
        fontweight="bold",
        pad=12,
    )


def _style_axis_labels(ax):
    """Apply consistent axis-label styling."""

    ax.xaxis.label.set_color(
        DEEP_MOONSTONE
    )

    ax.yaxis.label.set_color(
        DEEP_MOONSTONE
    )


# =========================================================
# FIGURE → BASE64
# =========================================================

def _figure_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG."""

    buffer = BytesIO()

    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    buffer.seek(0)

    return base64.b64encode(
        buffer.read()
    ).decode("utf-8")


# =========================================================
# COLUMN SAFETY
# =========================================================

def _safe_column(
    df: pd.DataFrame,
    column: Any,
) -> bool:
    """Check whether a column exists."""

    return column in df.columns


# =========================================================
# BAR CHART
# =========================================================

def _render_bar(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    column = candidate.get(
        "x_column"
    )

    if not _safe_column(
        df,
        column,
    ):
        raise ValueError(
            f"Column '{column}' does not exist."
        )

    values = (
        df[column]
        .dropna()
        .value_counts()
        .head(20)
    )

    if values.empty:
        raise ValueError(
            f"Column '{column}' contains no usable values."
        )

    fig, ax = _prepare_figure()

    colors = [
        CHART_COLORS[index % len(CHART_COLORS)]
        for index in range(len(values))
    ]

    ax.bar(
        values.index.astype(str),
        values.values,
        color=colors,
        alpha=0.92,
        edgecolor=WHITE,
        linewidth=0.7,
    )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"Frequency of {column}",
        ),
    )

    ax.set_xlabel(
        str(column)
    )

    ax.set_ylabel(
        "Count"
    )

    _style_axis_labels(ax)

    plt.xticks(
        rotation=35,
        ha="right",
    )

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# DISTRIBUTION / HISTOGRAM
# =========================================================

def _render_distribution(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    column = candidate.get(
        "x_column"
    )

    if not _safe_column(
        df,
        column,
    ):
        raise ValueError(
            f"Column '{column}' does not exist."
        )

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        raise ValueError(
            f"Column '{column}' has no numerical values."
        )

    fig, ax = _prepare_figure()

    counts, bins, patches = ax.hist(
        values,
        bins=30,
        edgecolor=WHITE,
        linewidth=0.6,
    )

    # Controlled multi-color progression
    for index, patch in enumerate(patches):

        color = CHART_COLORS[
            index % len(CHART_COLORS)
        ]

        patch.set_facecolor(
            color
        )

        patch.set_alpha(
            0.88
        )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"Distribution of {column}",
        ),
    )

    ax.set_xlabel(
        str(column)
    )

    ax.set_ylabel(
        "Count"
    )

    _style_axis_labels(ax)

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# SPREAD / BOX PLOT
# =========================================================

def _render_spread(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    column = candidate.get(
        "x_column"
    )

    if not _safe_column(
        df,
        column,
    ):
        raise ValueError(
            f"Column '{column}' does not exist."
        )

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        raise ValueError(
            f"Column '{column}' has no numerical values."
        )

    fig, ax = _prepare_figure()

    box = ax.boxplot(
        values,
        patch_artist=True,
        boxprops={
            "facecolor": MOONSTONE,
            "edgecolor": DEEP_MOONSTONE,
            "alpha": 0.9,
        },
        medianprops={
            "color": DEEP_MOONSTONE,
            "linewidth": 2,
        },
        whiskerprops={
            "color": DEEP_MOONSTONE,
        },
        capprops={
            "color": DEEP_MOONSTONE,
        },
        flierprops={
            "marker": "o",
            "markerfacecolor": CORAL,
            "markeredgecolor": DEEP_MOONSTONE,
            "markersize": 4,
            "alpha": 0.7,
        },
    )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"Spread of {column}",
        ),
    )

    ax.set_ylabel(
        str(column)
    )

    ax.set_xticks(
        [1]
    )

    ax.set_xticklabels(
        [str(column)]
    )

    _style_axis_labels(ax)

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# SCATTER
# =========================================================

def _render_scatter(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    x_column = candidate.get(
        "x_column"
    )

    y_column = candidate.get(
        "y_column"
    )

    if not _safe_column(
        df,
        x_column,
    ):
        raise ValueError(
            f"Column '{x_column}' does not exist."
        )

    if not _safe_column(
        df,
        y_column,
    ):
        raise ValueError(
            f"Column '{y_column}' does not exist."
        )

    data = df[
        [
            x_column,
            y_column,
        ]
    ].copy()

    data[x_column] = pd.to_numeric(
        data[x_column],
        errors="coerce",
    )

    data[y_column] = pd.to_numeric(
        data[y_column],
        errors="coerce",
    )

    data = data.dropna()

    if data.empty:
        raise ValueError(
            "No usable numerical values for scatter plot."
        )

    # Avoid rendering hundreds of thousands of points.
    # Analysis still uses the complete dataset.
    if len(data) > 10000:

        data = data.sample(
            10000,
            random_state=42,
        )

    fig, ax = _prepare_figure()

    ax.scatter(
        data[x_column],
        data[y_column],
        s=16,
        alpha=0.52,
        color=MOONSTONE,
        edgecolors="none",
    )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"{y_column} by {x_column}",
        ),
    )

    ax.set_xlabel(
        str(x_column)
    )

    ax.set_ylabel(
        str(y_column)
    )

    _style_axis_labels(ax)

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# LINE
# =========================================================

def _render_line(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    x_column = candidate.get(
        "x_column"
    )

    y_column = candidate.get(
        "y_column"
    )

    if not _safe_column(
        df,
        x_column,
    ):
        raise ValueError(
            f"Column '{x_column}' does not exist."
        )

    if not _safe_column(
        df,
        y_column,
    ):
        raise ValueError(
            f"Column '{y_column}' does not exist."
        )

    data = df[
        [
            x_column,
            y_column,
        ]
    ].copy()

    data[x_column] = pd.to_datetime(
        data[x_column],
        errors="coerce",
    )

    data[y_column] = pd.to_numeric(
        data[y_column],
        errors="coerce",
    )

    data = (
        data
        .dropna()
        .sort_values(x_column)
    )

    if data.empty:
        raise ValueError(
            "No usable values for time-series chart."
        )

    if len(data) > 5000:

        data = data.iloc[
            np.linspace(
                0,
                len(data) - 1,
                5000,
                dtype=int,
            )
        ]

    fig, ax = _prepare_figure()

    ax.plot(
        data[x_column],
        data[y_column],
        color=MOONSTONE,
        linewidth=2.4,
    )

    # Small highlight points
    ax.scatter(
        data[x_column],
        data[y_column],
        color=AZURE,
        s=8,
        alpha=0.35,
        edgecolors="none",
    )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"{y_column} over {x_column}",
        ),
    )

    ax.set_xlabel(
        str(x_column)
    )

    ax.set_ylabel(
        str(y_column)
    )

    _style_axis_labels(ax)

    fig.autofmt_xdate()

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# BOX BY CATEGORY
# =========================================================

def _render_box(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    x_column = candidate.get(
        "x_column"
    )

    y_column = candidate.get(
        "y_column"
    )

    if not _safe_column(
        df,
        x_column,
    ):
        raise ValueError(
            f"Column '{x_column}' does not exist."
        )

    if not _safe_column(
        df,
        y_column,
    ):
        raise ValueError(
            f"Column '{y_column}' does not exist."
        )

    data = df[
        [
            x_column,
            y_column,
        ]
    ].copy()

    data[y_column] = pd.to_numeric(
        data[y_column],
        errors="coerce",
    )

    data = data.dropna()

    if data.empty:
        raise ValueError(
            "No usable values for box plot."
        )

    groups = []
    labels = []

    for category, group in data.groupby(
        x_column
    ):

        if len(labels) >= 15:
            break

        values = group[
            y_column
        ].dropna()

        if values.empty:
            continue

        groups.append(
            values
        )

        labels.append(
            str(category)
        )

    if not groups:
        raise ValueError(
            "No usable category groups for box plot."
        )

    fig, ax = _prepare_figure()

    box = ax.boxplot(
        groups,
        patch_artist=True,
        medianprops={
            "color": DEEP_MOONSTONE,
            "linewidth": 2,
        },
        whiskerprops={
            "color": DEEP_MOONSTONE,
        },
        capprops={
            "color": DEEP_MOONSTONE,
        },
        flierprops={
            "marker": "o",
            "markerfacecolor": CORAL,
            "markeredgecolor": DEEP_MOONSTONE,
            "markersize": 4,
            "alpha": 0.65,
        },
    )

    # Different color for every category
    for index, patch in enumerate(
        box["boxes"]
    ):

        patch.set_facecolor(
            CHART_COLORS[
                index % len(CHART_COLORS)
            ]
        )

        patch.set_edgecolor(
            DEEP_MOONSTONE
        )

        patch.set_alpha(
            0.85
        )

    _style_title(
        ax,
        candidate.get(
            "title",
            f"{y_column} by {x_column}",
        ),
    )

    ax.set_xlabel(
        str(x_column)
    )

    ax.set_ylabel(
        str(y_column)
    )

    _style_axis_labels(ax)

    ax.set_xticks(
        range(
            1,
            len(labels) + 1,
        )
    )

    ax.set_xticklabels(
        labels,
        rotation=35,
        ha="right",
    )

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# CORRELATION HEATMAP
# =========================================================

def _render_correlation_heatmap(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    requested_columns = candidate.get(
        "columns"
    )

    if requested_columns:

        columns = [
            column
            for column in requested_columns
            if column in df.columns
            and pd.api.types.is_numeric_dtype(
                df[column]
            )
            and not pd.api.types.is_bool_dtype(
                df[column]
            )
        ]

    else:

        columns = [
            column
            for column in df.columns
            if pd.api.types.is_numeric_dtype(
                df[column]
            )
            and not pd.api.types.is_bool_dtype(
                df[column]
            )
        ]

    if len(columns) < 2:

        raise ValueError(
            "Correlation heatmap requires at least "
            "two numerical columns."
        )

    data = df[
        columns
    ].copy()

    correlation = data.corr()

    fig, ax = plt.subplots(
        figsize=(7, 5.5),
        dpi=120,
    )

    fig.patch.set_facecolor(
        VANILLA
    )

    # -----------------------------------------------------
    # Custom Moonstone correlation palette
    # -----------------------------------------------------

    moonstone_cmap = LinearSegmentedColormap.from_list(
        "moonstone_correlation",
        [
            "#F3FAFA",
            "#BCEEEF",
            MOONSTONE,
            "#2FA7B0",
            DEEP_MOONSTONE,
        ],
    )

    image = ax.imshow(
        correlation,
        cmap=moonstone_cmap,
        vmin=-1,
        vmax=1,
        aspect="auto",
    )

    _style_title(
        ax,
        candidate.get(
            "title",
            "Numerical Correlation",
        ),
    )

    ax.set_xticks(
        range(
            len(columns)
        )
    )

    ax.set_yticks(
        range(
            len(columns)
        )
    )

    ax.set_xticklabels(
        [
            str(column)
            for column in columns
        ],
        rotation=35,
        ha="right",
    )

    ax.set_yticklabels(
        [
            str(column)
            for column in columns
        ]
    )

    ax.tick_params(
        colors=DEEP_MOONSTONE
    )

    # -----------------------------------------------------
    # Correlation values inside cells
    # -----------------------------------------------------

    for row in range(
        len(columns)
    ):

        for col in range(
            len(columns)
        ):

            value = correlation.iloc[
                row,
                col,
            ]

            if pd.isna(value):
                continue

            text_color = (
                WHITE
                if abs(value) > 0.55
                else DEEP_MOONSTONE
            )

            ax.text(
                col,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=8,
                fontweight="bold",
            )

    # -----------------------------------------------------
    # Colorbar
    # -----------------------------------------------------

    colorbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.046,
        pad=0.04,
    )

    colorbar.set_label(
        "Correlation",
        color=DEEP_MOONSTONE,
    )

    colorbar.ax.tick_params(
        colors=DEEP_MOONSTONE
    )

    fig.tight_layout()

    return _figure_to_base64(fig)


# =========================================================
# SINGLE CANDIDATE RENDERER
# =========================================================

def _render_candidate(
    df: pd.DataFrame,
    candidate: dict[str, Any],
) -> str:

    visualization_type = (
        candidate.get(
            "visualization_type"
        )
        or candidate.get(
            "type"
        )
    )

    if not visualization_type:

        raise ValueError(
            "Visualization candidate has no visualization type."
        )

    visualization_type = str(
        visualization_type
    ).lower()

    # -----------------------------------------------------
    # Supported aliases
    # -----------------------------------------------------

    if visualization_type == "histogram":
        visualization_type = "distribution"

    if visualization_type == "boxplot":
        visualization_type = "box"

    if visualization_type == "heatmap":
        visualization_type = "correlation_heatmap"

    if visualization_type == "correlation":
        visualization_type = "correlation_heatmap"

    # -----------------------------------------------------
    # Renderer dispatch
    # -----------------------------------------------------

    if visualization_type == "spread":

        return _render_spread(
            df,
            candidate,
        )

    if visualization_type == "distribution":

        return _render_distribution(
            df,
            candidate,
        )

    if visualization_type == "bar":

        return _render_bar(
            df,
            candidate,
        )

    if visualization_type == "scatter":

        return _render_scatter(
            df,
            candidate,
        )

    if visualization_type == "line":

        return _render_line(
            df,
            candidate,
        )

    if visualization_type == "box":

        return _render_box(
            df,
            candidate,
        )

    if visualization_type == "correlation_heatmap":

        return _render_correlation_heatmap(
            df,
            candidate,
        )

    raise ValueError(
        f"Unsupported visualization type "
        f"'{visualization_type}'."
    )


# =========================================================
# MAIN RENDERER
# =========================================================

def visualization_renderer(
    df: pd.DataFrame,
    recommendations: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Render selected visualization candidates.

    Invalid candidates are skipped rather than crashing the
    entire analysis pipeline.
    """

    if not isinstance(
        df,
        pd.DataFrame,
    ):

        raise TypeError(
            "visualization_renderer expects a pandas DataFrame."
        )

    if not isinstance(
        recommendations,
        dict,
    ):

        raise TypeError(
            "recommendations must be a dictionary."
        )

    candidates = recommendations.get(
        "candidate_visualizations",
        [],
    )

    rendered: list[
        dict[str, Any]
    ] = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        try:

            image = _render_candidate(
                df,
                candidate,
            )

            rendered.append(
                {
                    "candidate_id": candidate.get(
                        "candidate_id"
                    ),
                    "visualization_type": candidate.get(
                        "visualization_type"
                    ),
                    "title": candidate.get(
                        "title"
                    ),
                    "score": candidate.get(
                        "score"
                    ),
                    "reason": candidate.get(
                        "reason"
                    ),
                    "image": image,
                }
            )

        except Exception as error:

            # One unsuitable visualization should
            # never kill the entire analysis.
            print(
                "Skipping visualization:",
                candidate.get(
                    "candidate_id"
                ),
                "|",
                str(error),
            )

            continue

    return rendered