"""Exploratory data analysis engine for Prototype 0.0."""

import math
from typing import Any

import numpy as np
import pandas as pd

from dataset_understanding import dataset_understanding


# =========================================================
# BASIC VALUE CONVERSION
# =========================================================

def _number_or_none(value: Any) -> float | None:
    """Convert a numeric value into a finite Python float."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None

        number = float(value)

        if math.isfinite(number):
            return number

    except (TypeError, ValueError):

        return None

    return None


def _value_or_none(value: Any) -> Any:
    """Convert NumPy/pandas values into JSON-friendly values."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, np.generic):
        return value.item()

    return value


# =========================================================
# COLUMN HELPERS
# =========================================================

def _is_ignored_column(
    column_name: str,
    column_info: dict[str, Any],
) -> bool:
    """Determine whether a column should be excluded from analysis."""

    name = str(column_name).strip().lower()

    # Automatically generated pandas/CSV index columns
    if name.startswith("unnamed:"):
        return True

    # Columns identified as IDs by dataset understanding
    if column_info.get("is_id_like", False):
        return True

    return False


# =========================================================
# NUMERICAL ANALYSIS
# =========================================================

def _numeric_column_analysis(
    column: pd.Series,
) -> dict[str, Any]:
    """Calculate descriptive statistics for a numerical column."""

    values = pd.to_numeric(
        column,
        errors="coerce",
    ).dropna()

    if values.empty:

        return {
            "count": 0,
            "mean": None,
            "median": None,
            "mode": [],
            "standard_deviation": None,
            "variance": None,
            "minimum": None,
            "maximum": None,
            "quartiles": {
                "q1": None,
                "q2": None,
                "q3": None,
            },
            "iqr": None,
            "skewness": None,
            "zero_count": 0,
            "negative_count": 0,
        }

    q1 = values.quantile(0.25)
    q2 = values.quantile(0.50)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    return {
        "count": int(values.count()),

        "mean": _number_or_none(
            values.mean()
        ),

        "median": _number_or_none(
            values.median()
        ),

        "mode": [
            _value_or_none(value)
            for value in values.mode().tolist()
        ],

        "standard_deviation": _number_or_none(
            values.std()
        ),

        "variance": _number_or_none(
            values.var()
        ),

        "minimum": _number_or_none(
            values.min()
        ),

        "maximum": _number_or_none(
            values.max()
        ),

        "quartiles": {
            "q1": _number_or_none(q1),
            "q2": _number_or_none(q2),
            "q3": _number_or_none(q3),
        },

        "iqr": _number_or_none(iqr),

        "skewness": _number_or_none(
            values.skew()
        ),

        "zero_count": int(
            (values == 0).sum()
        ),

        "negative_count": int(
            (values < 0).sum()
        ),
    }


# =========================================================
# CATEGORICAL ANALYSIS
# =========================================================

def _categorical_column_analysis(
    column: pd.Series,
) -> dict[str, Any]:
    """Calculate frequency information for a categorical column."""

    values = column.dropna()

    value_counts = values.value_counts(
        dropna=True
    )

    non_null_count = int(
        values.count()
    )

    frequencies = []

    for value, count in value_counts.items():

        percentage = (
            (int(count) / non_null_count) * 100
            if non_null_count
            else 0
        )

        frequencies.append(
            {
                "value": _value_or_none(value),
                "count": int(count),
                "percentage": round(
                    percentage,
                    2,
                ),
            }
        )

    return {
        "unique_value_count": int(
            values.nunique(
                dropna=True
            )
        ),

        "mode": [
            _value_or_none(value)
            for value in values.mode().tolist()
        ],

        "frequency": frequencies,

        # Useful later when deciding whether
        # a categorical chart is worth showing.
        "top_category": (
            frequencies[0]
            if frequencies
            else None
        ),
    }


# =========================================================
# CORRELATION ANALYSIS
# =========================================================

def _correlation_analysis(
    numerical_data: pd.DataFrame,
) -> dict[str, Any]:
    """Calculate correlations between meaningful numerical variables."""

    if numerical_data.shape[1] < 2:

        return {
            "columns": [],
            "matrix": [],
            "relationships": [],
        }

    correlation_matrix = numerical_data.corr(
        method="pearson"
    )

    columns = [
        str(column)
        for column in correlation_matrix.columns
    ]

    matrix = [
        [
            _number_or_none(value)
            for value in row
        ]
        for row in correlation_matrix.to_numpy()
    ]

    relationships = []

    for i in range(len(columns)):

        for j in range(i + 1, len(columns)):

            correlation = correlation_matrix.iloc[
                i,
                j,
            ]

            correlation_value = _number_or_none(
                correlation
            )

            if correlation_value is None:
                continue

            absolute_correlation = abs(
                correlation_value
            )

            # Only keep relationships that have
            # some analytical strength.
            if absolute_correlation >= 0.30:

                if correlation_value >= 0:
                    direction = "positive"
                else:
                    direction = "negative"

                relationships.append(
                    {
                        "column_x": columns[i],

                        "column_y": columns[j],

                        "correlation": round(
                            correlation_value,
                            4,
                        ),

                        "absolute_correlation": round(
                            absolute_correlation,
                            4,
                        ),

                        "direction": direction,
                    }
                )

    relationships.sort(
        key=lambda item: item[
            "absolute_correlation"
        ],
        reverse=True,
    )

    return {
        "columns": columns,

        "matrix": matrix,

        "relationships": relationships,
    }


# =========================================================
# OUTLIER ANALYSIS
# =========================================================

def _outlier_analysis(
    column: pd.Series,
) -> dict[str, Any]:
    """Detect potential outliers using the 1.5 × IQR rule."""

    values = pd.to_numeric(
        column,
        errors="coerce",
    )

    valid_values = values.dropna()

    if valid_values.empty:

        return {
            "q1": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_count": 0,
            "outlier_percentage": 0.0,
            "outlier_row_positions": [],
        }

    q1 = valid_values.quantile(0.25)
    q3 = valid_values.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (
        1.5 * iqr
    )

    upper_bound = q3 + (
        1.5 * iqr
    )

    outlier_mask = (
        (values < lower_bound)
        | (values > upper_bound)
    ).fillna(False)

    outlier_positions = np.flatnonzero(
        outlier_mask.to_numpy(
            dtype=bool
        )
    ).tolist()

    outlier_count = len(
        outlier_positions
    )

    outlier_percentage = (
        (outlier_count / len(valid_values))
        * 100
        if len(valid_values)
        else 0
    )

    return {
        "q1": _number_or_none(q1),

        "q3": _number_or_none(q3),

        "iqr": _number_or_none(iqr),

        "lower_bound": _number_or_none(
            lower_bound
        ),

        "upper_bound": _number_or_none(
            upper_bound
        ),

        "outlier_count": outlier_count,

        "outlier_percentage": round(
            outlier_percentage,
            2,
        ),

        "outlier_row_positions": (
            outlier_positions[:100]
        ),
    }


# =========================================================
# CATEGORICAL × NUMERICAL RELATIONSHIPS
# =========================================================

def _categorical_numeric_relationships(
    df: pd.DataFrame,
    categorical_columns: list[str],
    numerical_columns: list[str],
) -> list[dict[str, Any]]:
    """Find useful categorical-to-numeric comparisons."""

    relationships = []

    for categorical_column in categorical_columns:

        unique_count = int(
            df[categorical_column]
            .nunique(dropna=True)
        )

        # Avoid enormous categorical columns.
        if unique_count < 2 or unique_count > 20:
            continue

        for numerical_column in numerical_columns:

            grouped = (
                df.groupby(
                    categorical_column,
                    dropna=True,
                )[numerical_column]
                .agg(
                    [
                        "count",
                        "mean",
                        "median",
                    ]
                )
                .reset_index()
            )

            grouped = grouped.dropna(
                subset=["mean"]
            )

            if len(grouped) < 2:
                continue

            means = grouped["mean"]

            minimum_mean = means.min()
            maximum_mean = means.max()

            if minimum_mean == 0:

                mean_difference_ratio = (
                    1.0
                    if maximum_mean != 0
                    else 0.0
                )

            else:

                mean_difference_ratio = abs(
                    maximum_mean
                    - minimum_mean
                ) / max(
                    abs(minimum_mean),
                    1e-12,
                )

            relationships.append(
                {
                    "categorical_column": (
                        categorical_column
                    ),

                    "numerical_column": (
                        numerical_column
                    ),

                    "category_count": (
                        int(len(grouped))
                    ),

                    "mean_difference_ratio": round(
                        float(
                            mean_difference_ratio
                        ),
                        4,
                    ),

                    "groups": [
                        {
                            "category": _value_or_none(
                                row[
                                    categorical_column
                                ]
                            ),

                            "count": int(
                                row["count"]
                            ),

                            "mean": _number_or_none(
                                row["mean"]
                            ),

                            "median": _number_or_none(
                                row["median"]
                            ),
                        }
                        for _, row
                        in grouped.iterrows()
                    ],
                }
            )

    # Most differentiated relationships first
    relationships.sort(
        key=lambda item: item[
            "mean_difference_ratio"
        ],
        reverse=True,
    )

    return relationships


# =========================================================
# MAIN ANALYSIS ENGINE
# =========================================================

def analysis_engine(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Run structured exploratory analysis on a DataFrame.

    The engine uses ``dataset_understanding`` to determine which columns
    are analytically meaningful before calculating statistics.

    ID-like columns and automatically generated ``Unnamed`` columns
    are excluded from analytical relationships.
    """

    if not isinstance(df, pd.DataFrame):

        raise TypeError(
            "analysis_engine expects a pandas DataFrame."
        )

    # =====================================================
    # DATASET UNDERSTANDING
    # =====================================================

    understanding = dataset_understanding(
        df
    )

    column_information = {
        item["column_name"]: item
        for item in understanding["columns"]
    }

    # =====================================================
    # IDENTIFY ANALYTICALLY USEFUL COLUMNS
    # =====================================================

    meaningful_numeric_columns = []

    meaningful_categorical_columns = []

    ignored_columns = []

    for column_name in df.columns:

        name = str(column_name)

        info = column_information.get(
            name,
            {},
        )

        if _is_ignored_column(
            name,
            info,
        ):

            ignored_columns.append(
                {
                    "column_name": name,
                    "reason": (
                        "Identifier or automatically "
                        "generated index column."
                    ),
                }
            )

            continue

        role = info.get(
            "role"
        )

        if role == "numeric":

            meaningful_numeric_columns.append(
                name
            )

        elif role in (
            "categorical",
            "binary",
        ):

            meaningful_categorical_columns.append(
                name
            )

    # =====================================================
    # MISSING VALUES
    # =====================================================

    missing_values = []

    for column_name in df.columns:

        column = df[column_name]

        missing_count = int(
            column.isna().sum()
        )

        missing_percentage = (
            (
                missing_count
                / len(df)
            )
            * 100
            if len(df)
            else 0.0
        )

        missing_values.append(
            {
                "column_name": str(
                    column_name
                ),

                "missing_count": (
                    missing_count
                ),

                "missing_percentage": round(
                    missing_percentage,
                    2,
                ),
            }
        )

    # =====================================================
    # NUMERICAL ANALYSIS
    # =====================================================

    numerical_columns = []

    outliers = []

    for column_name in meaningful_numeric_columns:

        column = df[column_name]

        numerical_columns.append(
            {
                "column_name": column_name,

                "data_type": str(
                    column.dtype
                ),

                "statistics": (
                    _numeric_column_analysis(
                        column
                    )
                ),
            }
        )

        outliers.append(
            {
                "column_name": column_name,

                "data_type": str(
                    column.dtype
                ),

                "analysis": (
                    _outlier_analysis(
                        column
                    )
                ),
            }
        )

    # =====================================================
    # CATEGORICAL ANALYSIS
    # =====================================================

    categorical_columns = []

    for column_name in meaningful_categorical_columns:

        column = df[column_name]

        categorical_columns.append(
            {
                "column_name": column_name,

                "data_type": str(
                    column.dtype
                ),

                "analysis": (
                    _categorical_column_analysis(
                        column
                    )
                ),
            }
        )

    # =====================================================
    # CORRELATIONS
    # =====================================================

    if meaningful_numeric_columns:

        numerical_data = df[
            meaningful_numeric_columns
        ]

    else:

        numerical_data = pd.DataFrame()

    correlation = _correlation_analysis(
        numerical_data
    )

    # =====================================================
    # CATEGORICAL × NUMERICAL RELATIONSHIPS
    # =====================================================

    categorical_numeric_relationships = (
        _categorical_numeric_relationships(
            df,
            meaningful_categorical_columns,
            meaningful_numeric_columns,
        )
    )

    # =====================================================
    # DUPLICATES
    # =====================================================

    duplicate_row_count = int(
        df.duplicated().sum()
    )

    # =====================================================
    # DATASET RESULT
    # =====================================================

    dataset_result = {
        "row_count": int(
            df.shape[0]
        ),

        "column_count": int(
            df.shape[1]
        ),

        "duplicate_row_count": (
            duplicate_row_count
        ),

        "empty": bool(
            df.empty
        ),

        "meaningful_numeric_columns": (
            meaningful_numeric_columns
        ),

        "meaningful_categorical_columns": (
            meaningful_categorical_columns
        ),

        "ignored_columns": (
            ignored_columns
        ),
    }

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "dataset": dataset_result,

        "missing_values": missing_values,

        "numerical_columns": numerical_columns,

        "categorical_columns": categorical_columns,

        "unclassified_columns": [
            {
                "column_name": str(
                    item["column_name"]
                ),

                "data_type": item[
                    "data_type"
                ],
            }
            for item in understanding["columns"]
            if item["role"]
            not in (
                "numeric",
                "categorical",
                "binary",
            )
            and not item["is_id_like"]
        ],

        "correlation": correlation,

        "categorical_numeric_relationships": (
            categorical_numeric_relationships
        ),

        "potential_outliers": outliers,
    }