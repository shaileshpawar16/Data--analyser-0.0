"""
Reasoning engine for automated exploratory data analysis.

Converts structured analysis results into ranked analytical findings.

This layer does not generate visualizations.
It identifies what is interesting, important, unusual, or worth visualizing.
"""

from typing import Any


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Keep a score between minimum and maximum."""
    return max(minimum, min(maximum, value))


def _severity_label(score: float) -> str:
    """Convert a numeric score into a readable severity."""
    if score >= 0.80:
        return "high"

    if score >= 0.55:
        return "moderate"

    return "low"


# ============================================================
# MISSING VALUE FINDINGS
# ============================================================

def _missing_value_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify columns with meaningful missing values."""

    findings = []

    for item in analysis.get("missing_values", []):
        column_name = item.get("column_name")
        missing_count = int(item.get("missing_count", 0))
        missing_percentage = _safe_float(
            item.get("missing_percentage")
        ) or 0.0

        if missing_count == 0:
            continue

        score = _clamp(missing_percentage / 50.0)

        findings.append(
            {
                "finding_type": "missing_values",
                "column": column_name,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": f"Missing values in {column_name}",
                "message": (
                    f"{column_name} contains {missing_count} missing "
                    f"values ({missing_percentage:.2f}% of the column)."
                ),
                "details": {
                    "missing_count": missing_count,
                    "missing_percentage": missing_percentage,
                },
            }
        )

    return findings


# ============================================================
# OUTLIER FINDINGS
# ============================================================

def _outlier_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify numerical columns containing potential outliers."""

    findings = []

    for item in analysis.get("potential_outliers", []):
        column_name = item.get("column_name")
        outlier_analysis = item.get("analysis", {})

        outlier_count = int(
            outlier_analysis.get("outlier_count", 0)
        )

        outlier_percentage = _safe_float(
            outlier_analysis.get("outlier_percentage")
        ) or 0.0

        if outlier_count == 0:
            continue

        score = _clamp(outlier_percentage / 10.0)

        findings.append(
            {
                "finding_type": "outliers",
                "column": column_name,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": f"Potential outliers in {column_name}",
                "message": (
                    f"{column_name} contains {outlier_count} potential "
                    f"outliers ({outlier_percentage:.2f}% of non-null values)."
                ),
                "details": {
                    "outlier_count": outlier_count,
                    "outlier_percentage": outlier_percentage,
                    "lower_bound": outlier_analysis.get("lower_bound"),
                    "upper_bound": outlier_analysis.get("upper_bound"),
                },
            }
        )

    return findings


# ============================================================
# SKEW / DISTRIBUTION FINDINGS
# ============================================================

def _distribution_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Identify strongly skewed numerical distributions.

    Skewness:
        near 0       -> relatively symmetric
        positive     -> right-skewed
        negative     -> left-skewed
    """

    findings = []

    for item in analysis.get("numerical_columns", []):
        column_name = item.get("column_name")
        statistics = item.get("statistics", {})

        skewness = _safe_float(
            statistics.get("skewness")
        )

        if skewness is None:
            continue

        absolute_skewness = abs(skewness)

        # Ignore relatively symmetric distributions.
        if absolute_skewness < 1.0:
            continue

        score = _clamp(
            (absolute_skewness - 1.0) / 3.0
        )

        if skewness > 0:
            direction = "right-skewed"
        else:
            direction = "left-skewed"

        findings.append(
            {
                "finding_type": "distribution",
                "column": column_name,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": f"{column_name} is {direction}",
                "message": (
                    f"{column_name} has a skewness of {skewness:.2f}, "
                    f"indicating a {direction} distribution."
                ),
                "details": {
                    "skewness": skewness,
                    "direction": direction,
                },
            }
        )

    return findings


# ============================================================
# CORRELATION FINDINGS
# ============================================================

def _correlation_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Identify meaningful numerical relationships.

    Only one copy of each pair is returned.
    Self-correlations are ignored.
    """

    correlation = analysis.get("correlation", {})

    columns = correlation.get("columns", [])
    matrix = correlation.get("matrix", [])

    findings = []

    if len(columns) < 2:
        return findings

    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):

            try:
                value = _safe_float(matrix[i][j])
            except (IndexError, TypeError):
                continue

            if value is None:
                continue

            absolute_correlation = abs(value)

            # Weak relationships are not particularly useful
            # as "relationship" findings.
            if absolute_correlation < 0.30:
                continue

            score = _clamp(
                (absolute_correlation - 0.30) / 0.70
            )

            if value > 0:
                direction = "positive"
            else:
                direction = "negative"

            findings.append(
                {
                    "finding_type": "correlation",
                    "column": f"{columns[i]} / {columns[j]}",
                    "score": round(score, 3),
                    "severity": _severity_label(score),
                    "title": (
                        f"{columns[i]} and {columns[j]} "
                        f"show a {direction} relationship"
                    ),
                    "message": (
                        f"The correlation between {columns[i]} and "
                        f"{columns[j]} is {value:.2f}."
                    ),
                    "details": {
                        "column_x": columns[i],
                        "column_y": columns[j],
                        "correlation": value,
                        "direction": direction,
                    },
                }
            )

    return findings


# ============================================================
# CATEGORICAL FINDINGS
# ============================================================

def _categorical_findings(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Identify dominant categories."""

    findings = []

    for item in analysis.get("categorical_columns", []):

        column_name = item.get("column_name")
        categorical_analysis = item.get("analysis", {})

        frequency = categorical_analysis.get(
            "frequency",
            []
        )

        if not frequency:
            continue

        first = frequency[0]

        top_value = first.get("value")
        top_percentage = _safe_float(
            first.get("percentage")
        ) or 0.0

        unique_count = int(
            categorical_analysis.get(
                "unique_value_count",
                0,
            )
        )

        # A category is interesting when it dominates
        # the column substantially.
        if top_percentage < 50:
            continue

        score = _clamp(
            (top_percentage - 50.0) / 50.0
        )

        findings.append(
            {
                "finding_type": "categorical_distribution",
                "column": column_name,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": f"{column_name} has a dominant category",
                "message": (
                    f"'{top_value}' represents approximately "
                    f"{top_percentage:.2f}% of non-null values "
                    f"in {column_name}."
                ),
                "details": {
                    "top_value": top_value,
                    "top_percentage": top_percentage,
                    "unique_value_count": unique_count,
                },
            }
        )

    return findings


# ============================================================
# DATASET LEVEL FINDINGS
# ============================================================

def _dataset_findings(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Identify important dataset-level properties."""

    findings = []

    dataset = analysis.get("dataset", {})

    row_count = int(dataset.get("row_count", 0))
    column_count = int(dataset.get("column_count", 0))
    duplicate_row_count = int(
        dataset.get("duplicate_row_count", 0)
    )

    if duplicate_row_count > 0 and row_count > 0:

        percentage = (
            duplicate_row_count / row_count
        ) * 100

        score = _clamp(
            percentage / 20.0
        )

        findings.append(
            {
                "finding_type": "duplicates",
                "column": None,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": "Duplicate rows detected",
                "message": (
                    f"The dataset contains {duplicate_row_count} "
                    f"duplicate rows ({percentage:.2f}% of all rows)."
                ),
                "details": {
                    "duplicate_row_count": duplicate_row_count,
                    "duplicate_percentage": round(
                        percentage,
                        2,
                    ),
                },
            }
        )

    # Very wide datasets deserve attention.
    if column_count >= 50:

        score = _clamp(
            (column_count - 50) / 150
        )

        findings.append(
            {
                "finding_type": "dataset_structure",
                "column": None,
                "score": round(score, 3),
                "severity": _severity_label(score),
                "title": "Wide dataset",
                "message": (
                    f"The dataset contains {column_count} columns "
                    f"across {row_count} rows."
                ),
                "details": {
                    "row_count": row_count,
                    "column_count": column_count,
                },
            }
        )

    return findings


# ============================================================
# MAIN REASONING ENGINE
# ============================================================

def reasoning_engine(
    analysis: dict[str, Any],
    max_findings: int = 20,
) -> dict[str, Any]:
    """
    Convert analysis results into ranked analytical findings.

    Parameters
    ----------
    analysis:
        Output produced by analysis_engine().

    max_findings:
        Maximum number of findings returned.

    Returns
    -------
    dict
        Structured reasoning results.
    """

    if not isinstance(analysis, dict):
        raise TypeError(
            "reasoning_engine expects a dictionary "
            "returned by analysis_engine."
        )

    findings: list[dict[str, Any]] = []

    findings.extend(
        _dataset_findings(analysis)
    )

    findings.extend(
        _missing_value_findings(analysis)
    )

    findings.extend(
        _outlier_findings(analysis)
    )

    findings.extend(
        _distribution_findings(analysis)
    )

    findings.extend(
        _correlation_findings(analysis)
    )

    findings.extend(
        _categorical_findings(analysis)
    )

    # Highest-value findings first.
    findings.sort(
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    findings = findings[:max_findings]

    return {
        "finding_count": len(findings),
        "findings": findings,
    }