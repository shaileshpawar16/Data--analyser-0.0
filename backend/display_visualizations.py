"""Manually display Prototype 0.0 visualization recommendations for a CSV file.

Example:
    .venv\\Scripts\\python.exe display_visualizations.py path\\to\\dataset.csv
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis_engine import analysis_engine
from visualization_engine import visualization_engine
from visualization_renderer import visualization_renderer


def _select_top_candidates(recommendations: dict) -> list[dict]:
    """Return up to four candidates using the engine's existing ranking."""
    candidates = recommendations["candidate_visualizations"]
    ranking_by_id = {
        item["candidate_id"]: item["rank"]
        for item in recommendations["ranking"]
    }

    return sorted(
        candidates,
        key=lambda candidate: (
            ranking_by_id.get(candidate["candidate_id"], float("inf")),
            -candidate["suitability_score"],
        ),
    )[:4]


def display_visualizations(csv_path: Path, sample_rows: int | None = None) -> None:
    """Run the visualization workflow and display its top four candidates."""
    dataframe = pd.read_csv(csv_path, nrows=sample_rows)
    analysis = analysis_engine(dataframe)
    recommendations = visualization_engine(dataframe, analysis)
    selected_candidates = _select_top_candidates(recommendations)
    selected_recommendations = {
        "candidate_visualizations": selected_candidates
    }
    rendered = visualization_renderer(dataframe, selected_recommendations)

    print("Selected visualizations:")
    for candidate in selected_candidates:
        print(
            f"- {candidate['visualization_type']}: "
            f"score {candidate['suitability_score']}"
        )
    print(f"Displaying {rendered['rendered_count']} figure(s).")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Display Prototype 0.0 visualizations for a CSV dataset."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="Optional number of CSV rows to load for manual inspection.",
    )
    arguments = parser.parse_args()
    display_visualizations(arguments.csv_path, arguments.sample_rows)
