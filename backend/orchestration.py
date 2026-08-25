"""Orchestration layer for the Prototype 0.0 analysis workflow."""

from pathlib import Path
from typing import Any, Union

import pandas as pd

from analysis_engine import analysis_engine
from dataset_understanding import dataset_understanding
from file_handling import file_handling_loading
from visualization_engine import visualization_engine
from visualization_renderer import visualization_renderer


def run_prototype(
    file_path: Union[str, Path],
    max_visualizations: int = 4,
) -> dict[str, Any]:
    """Run the complete Prototype 0.0 workflow for a CSV file.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the CSV dataset.

    max_visualizations : int, default=4
        Maximum number of visualization candidates passed to the renderer.

    Returns
    -------
    dict
        Results produced by each stage of the Prototype 0.0 pipeline.
    """

    # 1. File handling
    dataframe: pd.DataFrame = file_handling_loading(file_path)

    # 2. Dataset understanding
    understanding = dataset_understanding(dataframe)

    # 3. Analysis
    analysis = analysis_engine(dataframe)

    # 4. Visualization decision engine
    visualization_recommendations = visualization_engine(
        dataframe,
        analysis,
    )

    # 5. Select only the highest-ranked visualization candidates
    candidates = visualization_recommendations.get(
        "candidate_visualizations",
        [],
    )

    selected_candidates = candidates[:max_visualizations]

    selected_recommendations = {
        **visualization_recommendations,
        "candidate_visualizations": selected_candidates,
    }

    # 6. Visualization rendering
    visualizations = visualization_renderer(
        dataframe,
        selected_recommendations,
    )

    return {
        "dataframe": dataframe,
        "dataset_understanding": understanding,
        "analysis": analysis,
        "visualization_recommendations": visualization_recommendations,
        "selected_visualization_recommendations": selected_recommendations,
        "visualizations": visualizations,
    }