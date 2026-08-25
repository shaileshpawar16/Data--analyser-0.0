"""
Intelligent visualization decision engine.

This module decides which visualizations provide the most
useful analytical coverage of a dataset.

The engine does not simply generate charts. It evaluates
their analytical usefulness, readability, redundancy, and
data suitability before selecting the final visualizations.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


# =========================================================
# COLUMN CLASSIFICATION
# =========================================================

def _is_numeric(series: pd.Series) -> bool:
    """Return True for genuine numerical columns."""

    return (
        pd.api.types.is_numeric_dtype(series)
        and not pd.api.types.is_bool_dtype(series)
    )


def _is_categorical(series: pd.Series) -> bool:
    """Return True for categorical/text columns."""

    return (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_categorical_dtype(series)
        or pd.api.types.is_bool_dtype(series)
    )


def _is_datetime(series: pd.Series) -> bool:
    """Return True for datetime columns."""

    return pd.api.types.is_datetime64_any_dtype(series)


def _looks_like_id(column_name: Any) -> bool:
    """Identify columns that are probably identifiers."""

    name = str(column_name).strip().lower()

    id_names = {
        "id",
        "index",
        "unnamed",
        "unnamed: 0",
        "row_id",
        "record_id",
        "customer_id",
        "user_id",
        "transaction_id",
    }

    return (
        name in id_names
        or name.endswith("_id")
        or name.endswith(" id")
    )


# =========================================================
# NUMERICAL QUALITY
# =========================================================

def _numeric_quality(
    df: pd.DataFrame,
    column: Any,
) -> dict[str, float]:
    """
    Calculate basic quality metrics for a numerical column.

    These metrics are used to decide whether a visualization
    is likely to be useful.
    """

    values = pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return {
            "count": 0,
            "unique_ratio": 0.0,
            "skewness": 0.0,
            "outlier_ratio": 0.0,
            "range_ratio": 0.0,
        }

    count = len(values)
    unique_count = values.nunique()

    unique_ratio = (
        unique_count / count
        if count
        else 0.0
    )

    skewness_value = values.skew()

    if pd.isna(skewness_value):
        skewness = 0.0
    else:
        skewness = abs(float(skewness_value))

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        outlier_ratio = 0.0
    else:
        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        outlier_count = (
            (values < lower)
            | (values > upper)
        ).sum()

        outlier_ratio = (
            outlier_count / count
            if count
            else 0.0
        )

    minimum = float(values.min())
    maximum = float(values.max())

    mean_abs = abs(float(values.mean()))

    if mean_abs == 0:
        range_ratio = 0.0
    else:
        range_ratio = (
            abs(maximum - minimum)
            / mean_abs
        )

    return {
        "count": float(count),
        "unique_ratio": float(unique_ratio),
        "skewness": float(skewness),
        "outlier_ratio": float(outlier_ratio),
        "range_ratio": float(range_ratio),
    }


# =========================================================
# CORRELATION
# =========================================================

def _correlation_strength(
    df: pd.DataFrame,
    column_a: Any,
    column_b: Any,
) -> float:
    """Return absolute Pearson correlation strength."""

    try:

        data = df[
            [column_a, column_b]
        ].copy()

        data[column_a] = pd.to_numeric(
            data[column_a],
            errors="coerce",
        )

        data[column_b] = pd.to_numeric(
            data[column_b],
            errors="coerce",
        )

        data = data.dropna()

        if len(data) < 3:
            return 0.0

        correlation = data[
            column_a
        ].corr(
            data[column_b]
        )

        if pd.isna(correlation):
            return 0.0

        return abs(float(correlation))

    except Exception:
        return 0.0


# =========================================================
# CANDIDATE CREATION
# =========================================================

def _add_candidate(
    candidates: list[dict[str, Any]],
    candidate_id: str,
    visualization_type: str,
    title: str,
    score: float,
    reason: str,
    analytical_role: str,
    **extra: Any,
) -> None:
    """Add a visualization candidate."""

    candidates.append(
        {
            "candidate_id": candidate_id,
            "visualization_type": visualization_type,
            "title": title,
            "score": round(
                float(score),
                2,
            ),
            "reason": reason,
            "analytical_role": analytical_role,
            **extra,
        }
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def visualization_engine(
    df: pd.DataFrame,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Decide which visualizations are most useful.

    The engine evaluates:

    - column type
    - skewness
    - outliers
    - uniqueness
    - correlation
    - chart usefulness
    - analytical coverage
    - redundancy
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "visualization_engine expects a pandas DataFrame."
        )

    candidates: list[dict[str, Any]] = []

    # =====================================================
    # CLASSIFY COLUMNS
    # =====================================================

    numeric_columns = [
        column
        for column in df.columns
        if _is_numeric(df[column])
    ]

    categorical_columns = [
        column
        for column in df.columns
        if _is_categorical(df[column])
    ]

    datetime_columns = [
        column
        for column in df.columns
        if _is_datetime(df[column])
    ]

    useful_numeric = [
        column
        for column in numeric_columns
        if not _looks_like_id(column)
    ]

    useful_categorical = [
        column
        for column in categorical_columns
        if not _looks_like_id(column)
    ]

    # =====================================================
    # NUMERICAL QUALITY CACHE
    # =====================================================

    numerical_quality = {
        column: _numeric_quality(
            df,
            column,
        )
        for column in useful_numeric
    }

    # =====================================================
    # 1. CORRELATION HEATMAP
    # =====================================================

    if len(useful_numeric) >= 2:

        correlation_columns = useful_numeric[:12]

        # A correlation matrix is most useful when
        # there are several numerical variables.

        base_score = 82

        if len(useful_numeric) >= 4:
            base_score += 8

        if len(useful_numeric) >= 8:
            base_score += 4

        _add_candidate(
            candidates,
            candidate_id="correlation_matrix",
            visualization_type="correlation_heatmap",
            title="Numerical Correlation",
            score=base_score,
            reason=(
                "Multiple numerical variables are available, "
                "allowing relationships between variables "
                "to be examined together."
            ),
            analytical_role="relationship_overview",
            columns=correlation_columns,
        )

    # =====================================================
    # 2. NUMERICAL RELATIONSHIPS
    # =====================================================

    if len(useful_numeric) >= 2:

        relationship_pairs = []

        for i in range(
            len(useful_numeric)
        ):

            for j in range(
                i + 1,
                len(useful_numeric),
            ):

                column_a = useful_numeric[i]
                column_b = useful_numeric[j]

                strength = _correlation_strength(
                    df,
                    column_a,
                    column_b,
                )

                relationship_pairs.append(
                    (
                        strength,
                        column_a,
                        column_b,
                    )
                )

        relationship_pairs.sort(
            reverse=True,
            key=lambda item: item[0],
        )

        for position, (
            strength,
            column_a,
            column_b,
        ) in enumerate(
            relationship_pairs[:5]
        ):

            # Strong relationships deserve more attention.

            score = (
                68
                + strength * 30
                - position * 3
            )

            if strength >= 0.7:
                score += 8

            elif strength >= 0.5:
                score += 4

            _add_candidate(
                candidates,
                candidate_id=(
                    f"relationship_"
                    f"{column_a}_"
                    f"{column_b}"
                ),
                visualization_type="scatter",
                title=(
                    f"{column_b} by {column_a}"
                ),
                score=score,
                reason=(
                    "The relationship between two "
                    "numerical variables can reveal "
                    "patterns, clusters or outliers."
                ),
                analytical_role="numerical_relationship",
                x_column=column_a,
                y_column=column_b,
                correlation_strength=round(
                    strength,
                    4,
                ),
            )

    # =====================================================
    # 3. NUMERICAL DISTRIBUTIONS
    # =====================================================

    distribution_candidates = []

    for column in useful_numeric:

        quality = numerical_quality[column]

        count = quality["count"]
        skewness = quality["skewness"]
        unique_ratio = quality["unique_ratio"]

        if count < 2:
            continue

        score = 65

        # More variation = more useful distribution.

        if unique_ratio > 0.05:
            score += 8

        if unique_ratio > 0.20:
            score += 6

        # Moderate skew makes distributions interesting.

        if 0.5 <= skewness <= 2.5:
            score += 10

        # Extremely skewed distributions are still
        # interesting, but we reduce their usefulness
        # because the chart may become unreadable.

        elif skewness > 5:
            score -= 8

        elif skewness > 3:
            score -= 3

        distribution_candidates.append(
            (
                score,
                column,
            )
        )

    distribution_candidates.sort(
        reverse=True,
        key=lambda item: item[0],
    )

    for position, (
        score,
        column,
    ) in enumerate(
        distribution_candidates[:5]
    ):

        _add_candidate(
            candidates,
            candidate_id=(
                f"distribution_{column}"
            ),
            visualization_type="distribution",
            title=f"Distribution of {column}",
            score=score - position * 2,
            reason=(
                "The distribution shows how values "
                "are concentrated, spread or skewed."
            ),
            analytical_role="distribution",
            x_column=column,
            skewness=round(
                numerical_quality[column][
                    "skewness"
                ],
                4,
            ),
        )

    # =====================================================
    # 4. NUMERICAL SPREAD
    # =====================================================

    for position, column in enumerate(
        useful_numeric
    ):

        quality = numerical_quality[column]

        skewness = quality["skewness"]
        outlier_ratio = quality[
            "outlier_ratio"
        ]
        unique_ratio = quality[
            "unique_ratio"
        ]

        # -------------------------------------------------
        # IMPORTANT:
        #
        # Very skewed data with extreme outliers often
        # produces a terrible box plot.
        #
        # Therefore we actively penalize it.
        # -------------------------------------------------

        score = 58

        if unique_ratio > 0.05:
            score += 5

        if outlier_ratio > 0.01:
            score += 4

        if 0.5 <= skewness <= 2.5:
            score += 6

        if skewness > 3:
            score -= 15

        if skewness > 5:
            score -= 12

        if outlier_ratio > 0.10:
            score -= 10

        # If the data is extremely skewed AND has many
        # outliers, this chart is usually poor.

        if (
            skewness > 5
            and outlier_ratio > 0.05
        ):
            score -= 20

        score -= position * 1.5

        # Don't generate extremely weak spread charts.

        if score < 35:
            continue

        _add_candidate(
            candidates,
            candidate_id=f"spread_{column}",
            visualization_type="spread",
            title=f"Spread of {column}",
            score=score,
            reason=(
                "The box plot shows the central range, "
                "overall spread and potential outliers."
            ),
            analytical_role="spread",
            x_column=column,
            skewness=round(
                skewness,
                4,
            ),
            outlier_ratio=round(
                outlier_ratio,
                4,
            ),
        )

    # =====================================================
    # 5. CATEGORICAL FREQUENCY
    # =====================================================

    for position, column in enumerate(
        useful_categorical[:8]
    ):

        unique_count = int(
            df[column].nunique(
                dropna=True
            )
        )

        if unique_count == 0:
            continue

        # Avoid charts with too many categories.

        if unique_count <= 20:

            score = 86

            if unique_count <= 5:
                score += 4

            elif unique_count > 12:
                score -= 6

            score -= position * 2

            _add_candidate(
                candidates,
                candidate_id=(
                    f"frequency_{column}"
                ),
                visualization_type="bar",
                title=f"Frequency of {column}",
                score=score,
                reason=(
                    "Category frequency reveals how "
                    "observations are distributed "
                    "across groups."
                ),
                analytical_role="categorical_frequency",
                x_column=column,
            )

    # =====================================================
    # 6. CATEGORY VS NUMERICAL
    # =====================================================

    if (
        useful_categorical
        and useful_numeric
    ):

        # Pick the strongest numerical variables
        # rather than blindly using the first column.

        sorted_numeric = sorted(
            useful_numeric,
            key=lambda column:
                numerical_quality[column][
                    "unique_ratio"
                ],
            reverse=True,
        )

        for category_column in (
            useful_categorical[:3]
        ):

            unique_count = int(
                df[category_column].nunique(
                    dropna=True
                )
            )

            if not (
                1 < unique_count <= 15
            ):
                continue

            numerical_column = (
                sorted_numeric[0]
            )

            _add_candidate(
                candidates,
                candidate_id=(
                    f"category_numeric_"
                    f"{category_column}_"
                    f"{numerical_column}"
                ),
                visualization_type="box",
                title=(
                    f"{numerical_column} by "
                    f"{category_column}"
                ),
                score=82,
                reason=(
                    "Comparing a numerical variable "
                    "across categories can reveal "
                    "differences between groups."
                ),
                analytical_role="group_comparison",
                x_column=category_column,
                y_column=numerical_column,
            )

    # =====================================================
    # 7. TIME SERIES
    # =====================================================

    if (
        datetime_columns
        and useful_numeric
    ):

        date_column = datetime_columns[0]

        # Prefer a numerical variable with reasonable
        # variation.

        numerical_column = max(
            useful_numeric,
            key=lambda column:
                numerical_quality[column][
                    "unique_ratio"
                ],
        )

        _add_candidate(
            candidates,
            candidate_id="time_series",
            visualization_type="line",
            title=(
                f"{numerical_column} "
                f"over {date_column}"
            ),
            score=100,
            reason=(
                "A time-based visualization can reveal "
                "trends, changes and unusual periods."
            ),
            analytical_role="time_trend",
            x_column=date_column,
            y_column=numerical_column,
        )

    # =====================================================
    # SELECTION
    # =====================================================

    selected = _select_best_visualizations(
        candidates,
        max_visualizations=4,
    )

    return {
        "candidate_visualizations": selected,
        "all_candidate_visualizations": candidates,
        "available_columns": {
            "numerical": [
                str(column)
                for column in useful_numeric
            ],
            "categorical": [
                str(column)
                for column in useful_categorical
            ],
            "datetime": [
                str(column)
                for column in datetime_columns
            ],
        },
    }


# =========================================================
# INTELLIGENT SELECTION
# =========================================================

def _select_best_visualizations(
    candidates: list[dict[str, Any]],
    max_visualizations: int = 4,
) -> list[dict[str, Any]]:
    """
    Select a diverse set of useful visualizations.

    The engine tries to maximize:

    - analytical coverage
    - chart quality
    - diversity
    - usefulness

    while reducing:

    - repeated chart types
    - redundant analytical roles
    - weak candidates
    """

    if not candidates:
        return []

    remaining = sorted(
        candidates,
        key=lambda candidate:
            candidate.get(
                "score",
                0,
            ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []

    used_roles: set[str] = set()
    used_columns: set[str] = set()

    # =====================================================
    # ROLE PRIORITY
    # =====================================================

    role_priority = [
        "time_trend",
        "relationship_overview",
        "numerical_relationship",
        "group_comparison",
        "categorical_frequency",
        "distribution",
        "spread",
    ]

    # =====================================================
    # FIRST PASS
    #
    # Try to obtain different analytical perspectives.
    # =====================================================

    for role in role_priority:

        if len(selected) >= max_visualizations:
            break

        role_candidates = [
            candidate
            for candidate in remaining
            if candidate.get(
                "analytical_role"
            ) == role
        ]

        if not role_candidates:
            continue

        best = max(
            role_candidates,
            key=lambda candidate:
                _adjusted_candidate_score(
                    candidate,
                    used_roles,
                    used_columns,
                ),
        )

        adjusted_score = (
            _adjusted_candidate_score(
                best,
                used_roles,
                used_columns,
            )
        )

        # Don't select extremely weak candidates
        # simply to fill a role.

        if adjusted_score < 40:
            continue

        selected.append(best)

        used_roles.add(
            best.get(
                "analytical_role",
                "",
            )
        )

        _register_candidate_columns(
            best,
            used_columns,
        )

        remaining.remove(best)

    # =====================================================
    # SECOND PASS
    #
    # Fill remaining slots with the strongest candidates.
    # =====================================================

    while (
        len(selected) < max_visualizations
        and remaining
    ):

        best = max(
            remaining,
            key=lambda candidate:
                _adjusted_candidate_score(
                    candidate,
                    used_roles,
                    used_columns,
                ),
        )

        adjusted_score = (
            _adjusted_candidate_score(
                best,
                used_roles,
                used_columns,
            )
        )

        if adjusted_score < 40:
            break

        selected.append(best)

        used_roles.add(
            best.get(
                "analytical_role",
                "",
            )
        )

        _register_candidate_columns(
            best,
            used_columns,
        )

        remaining.remove(best)

    # =====================================================
    # FINAL ORDER
    # =====================================================

    role_order = {
        "time_trend": 0,
        "relationship_overview": 1,
        "numerical_relationship": 2,
        "group_comparison": 3,
        "categorical_frequency": 4,
        "distribution": 5,
        "spread": 6,
    }

    selected.sort(
        key=lambda candidate: (
            role_order.get(
                candidate.get(
                    "analytical_role",
                    "",
                ),
                99,
            ),
            -float(
                candidate.get(
                    "score",
                    0,
                )
            ),
        )
    )

    return selected[:max_visualizations]


# =========================================================
# ADJUSTED SCORE
# =========================================================

def _adjusted_candidate_score(
    candidate: dict[str, Any],
    used_roles: set[str],
    used_columns: set[str],
) -> float:
    """
    Calculate the actual selection score.

    This is where redundancy penalties are applied.
    """

    score = float(
        candidate.get(
            "score",
            0,
        )
    )

    role = candidate.get(
        "analytical_role",
        "",
    )

    # -----------------------------------------------------
    # Repeated analytical role penalty
    # -----------------------------------------------------

    if role in used_roles:
        score -= 20

    # -----------------------------------------------------
    # Repeated variable penalty
    #
    # A dashboard should not keep showing the same
    # variable unless it contributes something genuinely
    # different.
    # -----------------------------------------------------

    columns = []

    for key in (
        "x_column",
        "y_column",
    ):

        value = candidate.get(key)

        if value is not None:
            columns.append(
                str(value)
            )

    repeated_columns = sum(
        column in used_columns
        for column in columns
    )

    score -= (
        repeated_columns * 5
    )

    return score


# =========================================================
# COLUMN REGISTRATION
# =========================================================

def _register_candidate_columns(
    candidate: dict[str, Any],
    used_columns: set[str],
) -> None:
    """Register variables already represented in the dashboard."""

    for key in (
        "x_column",
        "y_column",
    ):

        value = candidate.get(key)

        if value is not None:
            used_columns.add(
                str(value)
            )

    # Correlation matrix represents all of its columns.

    for column in candidate.get(
        "columns",
        [],
    ):

        used_columns.add(
            str(column)
        )