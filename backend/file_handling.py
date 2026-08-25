"""File-loading utilities for Prototype 0.0.

Currently, the prototype supports CSV files only.
"""

from pathlib import Path
from typing import Union

import pandas as pd


def file_handling_loading(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to the file that should be loaded.

    Returns
    -------
    pandas.DataFrame
        The dataset read from the CSV file.

    Raises
    ------
    ValueError
        If the supplied file is not a CSV file.
    """
    path = Path(file_path)

    if path.suffix.lower() != ".csv":
        raise ValueError(
            "Only CSV files are currently supported. "
            f"Received file: '{path.name}'."
        )
    return pd.read_csv(path)
