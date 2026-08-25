from pathlib import Path
import shutil
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from file_handling import file_handling_loading
from dataset_understanding import dataset_understanding
from analysis_engine import analysis_engine
from reasoning_engine import reasoning_engine
from visualization_engine import visualization_engine
from visualization_renderer import visualization_renderer


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Prototype Analyser API",
    version="0.0.1",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "message": "Prototype Analyser backend is running.",
    }


# =========================================================
# UPLOAD + COMPLETE ANALYSIS
# =========================================================

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...)
):

    # =====================================================
    # VALIDATE FILE
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    if not file.filename.lower().endswith(".csv"):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV files are accepted "
                "for Prototype 0.0."
            ),
        )

    # =====================================================
    # TEMPORARY FILE LOCATION
    # =====================================================

    temp_directory = (
        Path(tempfile.gettempdir())
        / "prototype_analyser"
    )

    temp_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        temp_directory
        / file.filename
    )

    try:

        # =================================================
        # SAVE UPLOADED FILE
        # =================================================

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        # =================================================
        # 1. FILE HANDLING
        # =================================================

        dataframe = file_handling_loading(
            file_path
        )

        # =================================================
        # 2. DATASET UNDERSTANDING
        # =================================================

        understanding = dataset_understanding(
            dataframe
        )

        # =================================================
        # 3. ANALYSIS
        # =================================================

        analysis = analysis_engine(
            dataframe
        )

        # =================================================
        # 4. REASONING
        # =================================================
        #
        # Convert raw analytical statistics into
        # meaningful findings.
        #
        # Example:
        #
        # skewness = 8.4
        #
        # becomes:
        #
        # "vote_count is strongly right-skewed"
        #
        # =================================================

        reasoning = reasoning_engine(
            analysis
        )

        # =================================================
        # 5. VISUALIZATION DECISION
        # =================================================
        #
        # The visualization engine now receives:
        #
        #   dataframe
        #   analysis
        #
        # The reasoning layer is also returned separately
        # so we can connect it to visualization selection
        # in the next stage.
        #
        # =================================================

        visualization_recommendations = (
            visualization_engine(
                dataframe,
                analysis,
            )
        )

        # =================================================
        # 6. SELECT TOP FOUR
        # =================================================

        candidates = (
            visualization_recommendations.get(
                "candidate_visualizations",
                [],
            )
        )

        selected_candidates = candidates[:4]

        selected_recommendations = {
            **visualization_recommendations,
            "candidate_visualizations":
                selected_candidates,
        }

        # =================================================
        # 7. RENDER VISUALIZATIONS
        # =================================================

        charts = visualization_renderer(
            dataframe,
            selected_recommendations,
        )

        # =================================================
        # RESPONSE
        # =================================================

        return {

            "success": True,

            # -------------------------------------------------
            # FILE
            # -------------------------------------------------

            "file": {
                "name": file.filename,
            },

            # -------------------------------------------------
            # DATASET
            # -------------------------------------------------

            "dataset": {

                "rows": int(
                    dataframe.shape[0]
                ),

                "columns": int(
                    dataframe.shape[1]
                ),

                "column_names": [
                    str(column)
                    for column
                    in dataframe.columns
                ],
            },

            # -------------------------------------------------
            # UNDERSTANDING
            # -------------------------------------------------

            "understanding": understanding,

            # -------------------------------------------------
            # RAW ANALYSIS
            # -------------------------------------------------

            "analysis": analysis,

            # -------------------------------------------------
            # REASONING
            # -------------------------------------------------

            "reasoning": reasoning,

            # -------------------------------------------------
            # VISUALIZATION RECOMMENDATIONS
            # -------------------------------------------------

            "visualization_recommendations":
                visualization_recommendations,

            # -------------------------------------------------
            # SELECTED VISUALIZATIONS
            # -------------------------------------------------

            "selected_visualization_recommendations":
                selected_recommendations,

            # -------------------------------------------------
            # RENDERED CHARTS
            # -------------------------------------------------

            "charts": charts,
        }

    except Exception as error:

        print(
            "ANALYSIS ERROR:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        # =================================================
        # CLEAN UP TEMPORARY FILE
        # =================================================

        try:

            file_path.unlink()

        except FileNotFoundError:

            pass