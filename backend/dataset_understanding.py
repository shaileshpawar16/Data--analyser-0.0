"""Dataset profiling and structural understanding utilities."""

from typing import Any

import pandas as pd


# =========================================================
# HELPERS
# =========================================================

def _detect_column_role(
    series: pd.Series,
    unique_count: int,
    row_count: int,
) -> str:
    """Infer the analytical role of a column."""

    dtype = series.dtype

    # Boolean
    if pd.api.types.is_bool_dtype(dtype):
        return "binary"

    # Numeric
    if pd.api.types.is_numeric_dtype(dtype):

        if unique_count <= 2:
            return "binary"

        # Integer columns with relatively few unique values
        # are often categorical variables.
        if (
            pd.api.types.is_integer_dtype(dtype)
            and unique_count <= 10
            and unique_count < row_count * 0.05
        ):
            return "categorical"

        return "numeric"

    # Datetime
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "datetime"

    # Try to recognize date-like object columns
    if pd.api.types.is_object_dtype(dtype):

        sample = series.dropna()

        if len(sample) > 0:
            converted = pd.to_datetime(
                sample,
                errors="coerce",
            )

            conversion_rate = converted.notna().mean()

            if conversion_rate >= 0.90:
                return "datetime"

    # Text / categorical
    if pd.api.types.is_string_dtype(dtype):

        if unique_count <= 2:
            return "binary"

        return "categorical"

    return "other"


def _detect_cardinality(
    unique_count: int,
    row_count: int,
) -> str:
    """Classify the number of unique values."""

    if row_count == 0:
        return "empty"

    if unique_count <= 10:
        return "low"

    ratio = unique_count / row_count

    if ratio <= 0.05:
        return "medium"

    if ratio <= 0.50:
        return "high"

    return "very_high"


def _detect_id_like(
    column_name: str,
    series: pd.Series,
    unique_count: int,
    row_count: int,
) -> bool:
    """Detect columns that look like identifiers."""

    name = str(column_name).lower()

    id_keywords = (
        "id",
        "identifier",
        "uuid",
        "customer_id",
        "user_id",
        "transaction_id",
        "order_id",
        "account_id",
        "product_id",
    )

    name_suggests_id = (
        name == "id"
        or name.endswith("_id")
        or name in id_keywords
        or "identifier" in name
    )

    almost_unique = (
        row_count > 0
        and unique_count / row_count >= 0.95
    )

    return bool(name_suggests_id or almost_unique)


def _numeric_summary(series: pd.Series) -> dict[str, Any]:
    """Return useful summary information for numeric columns."""

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        return {
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "standard_deviation": None,
            "zero_count": 0,
            "negative_count": 0,
        }

    return {
        "minimum": float(numeric.min()),
        "maximum": float(numeric.max()),
        "mean": float(numeric.mean()),
        "median": float(numeric.median()),
        "standard_deviation": float(numeric.std()),
        "zero_count": int((numeric == 0).sum()),
        "negative_count": int((numeric < 0).sum()),
    }


# =========================================================
# MAIN FUNCTION
# =========================================================

def dataset_understanding(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Profile the structure and analytical characteristics of a dataset.

    This stage describes the dataset. It does not perform deeper analysis
    or select visualizations.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "dataset_understanding expects a pandas DataFrame."
        )

    row_count = int(df.shape[0])
    column_count = int(df.shape[1])

    column_details = []

    for position, column_name in enumerate(df.columns):

        column = df.iloc[:, position]

        non_null_count = int(
            column.notna().sum()
        )

        missing_value_count = int(
            column.isna().sum()
        )

        unique_count = int(
            column.nunique(dropna=True)
        )

        missing_percentage = (
            (missing_value_count / row_count) * 100
            if row_count > 0
            else 0.0
        )

        role = _detect_column_role(
            column,
            unique_count,
            row_count,
        )

        cardinality = _detect_cardinality(
            unique_count,
            row_count,
        )

        id_like = _detect_id_like(
            column_name,
            column,
            unique_count,
            row_count,
        )

        details = {
            "column_name": str(column_name),

            "position": position,

            "data_type": str(column.dtype),

            "role": role,

            "non_null_count": non_null_count,

            "missing_value_count": missing_value_count,

            "missing_percentage": round(
                missing_percentage,
                2,
            ),

            "unique_value_count": unique_count,

            "cardinality": cardinality,

            "is_id_like": id_like,
        }

        # -------------------------------------------------
        # Numeric-specific information
        # -------------------------------------------------

        if role == "numeric":

            details["numeric_summary"] = (
                _numeric_summary(column)
            )

        # -------------------------------------------------
        # Categorical-specific information
        # -------------------------------------------------

        if role in ("categorical", "binary"):

            value_counts = (
                column
                .value_counts(
                    dropna=False,
                )
                .head(10)
            )

            details["top_values"] = [
                {
                    "value": (
                        None
                        if pd.isna(value)
                        else str(value)
                    ),
                    "count": int(count),
                }
                for value, count
                in value_counts.items()
            ]

        # -------------------------------------------------
        # Datetime-specific information
        # -------------------------------------------------

        if role == "datetime":

            converted = pd.to_datetime(
                column,
                errors="coerce",
            ).dropna()

            if not converted.empty:

                details["datetime_summary"] = {
                    "minimum": converted.min().isoformat(),
                    "maximum": converted.max().isoformat(),
                }

        column_details.append(details)

    # =====================================================
    # DATASET-LEVEL SUMMARY
    # =====================================================

    numeric_columns = [
        item["column_name"]
        for item in column_details
        if item["role"] == "numeric"
    ]

    categorical_columns = [
        item["column_name"]
        for item in column_details
        if item["role"] == "categorical"
    ]

    binary_columns = [
        item["column_name"]
        for item in column_details
        if item["role"] == "binary"
    ]

    datetime_columns = [
        item["column_name"]
        for item in column_details
        if item["role"] == "datetime"
    ]

    id_like_columns = [
        item["column_name"]
        for item in column_details
        if item["is_id_like"]
    ]

    return {
        "dataset": {
            "row_count": row_count,

            "column_count": column_count,

            "column_names": [
                str(column)
                for column in df.columns
            ],

            "numeric_column_count": len(
                numeric_columns
            ),

            "categorical_column_count": len(
                categorical_columns
            ),

            "binary_column_count": len(
                binary_columns
            ),

            "datetime_column_count": len(
                datetime_columns
            ),

            "id_like_column_count": len(
                id_like_columns
            ),

            "numeric_columns": numeric_columns,

            "categorical_columns": categorical_columns,

            "binary_columns": binary_columns,

            "datetime_columns": datetime_columns,

            "id_like_columns": id_like_columns,
        },

        "columns": column_details,
    }