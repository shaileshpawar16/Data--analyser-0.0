import time

import streamlit as st


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #FFFDF5;
    }

    /* Remove Streamlit top padding */
    .block-container {
        padding-top: 4rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }

    /* Main headings */
    .main-title {
        color: #1E3A8A;
        font-family: Inter, sans-serif;
        font-size: 48px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 10px;
    }

    .subtitle {
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 20px;
        text-align: center;
        margin-bottom: 35px;
    }

    .small-text {
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 13px;
        text-align: center;
        margin-top: 12px;
    }

    /* Uploaded file information */
    .upload-title {
        color: #1E3A8A;
        font-family: Inter, sans-serif;
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 15px;
    }

    .info-text {
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 17px;
        margin-bottom: 10px;
    }

    /* Result heading */
    .result-title {
        color: #1E3A8A;
        font-family: Inter, sans-serif;
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .result-subtitle {
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 15px;
        margin-bottom: 25px;
    }

    /* Chart cards */
    .chart-card {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 25px;
        min-height: 280px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 16px;
    }

    /* Center content */
    .center-content {
        text-align: center;
    }

    /* Processing text */
    .processing-title {
        color: #1E3A8A;
        font-family: Inter, sans-serif;
        font-size: 32px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 20px;
    }

    .processing-step {
        color: #6B7280;
        font-family: Inter, sans-serif;
        font-size: 14px;
        text-align: center;
        margin: 7px;
    }

    /* Button styling */
    div.stButton > button {
        background-color: #2563EB;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-family: Inter, sans-serif;
        font-size: 14px;
        font-weight: 500;
        min-height: 48px;
    }

    div.stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
    }

    /* File uploader */
    section[data-testid="stFileUploader"] {
        background-color: #FFFDF5;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "screen" not in st.session_state:
    st.session_state.screen = "welcome"

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

if "visualization_count" not in st.session_state:
    st.session_state.visualization_count = 4


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def go_to(screen):
    st.session_state.screen = screen
    st.rerun()


def show_chart_placeholder(number):
    st.markdown(
        f"""
        <div class="chart-card">
            Visualization {number}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# SCREEN 1: WELCOME
# ---------------------------------------------------------

if st.session_state.screen == "welcome":

    st.markdown(
        '<div style="height: 180px;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-title">Welcome.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Let us help you analyze your data.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="height: 15px;"></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:

        uploaded_file = st.file_uploader(
            "Upload File",
            type=["csv"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:

            st.session_state.uploaded_file = uploaded_file
            go_to("uploaded")

        st.markdown(
            '<div class="small-text">Only CSV files are accepted for now.</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# SCREEN 2: FILE UPLOADED
# ---------------------------------------------------------

elif st.session_state.screen == "uploaded":

    st.markdown(
        '<div style="height: 100px;"></div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.session_state.uploaded_file

    st.markdown(
        '<div class="upload-title">File uploaded successfully</div>',
        unsafe_allow_html=True,
    )

    if uploaded_file is not None:

        # Temporary information for Prototype 0.0
        # The real dataset understanding engine will replace this.
        st.markdown(
            f"""
            <div class="info-text">
                File: {uploaded_file.name}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="info-text">
                Your file is ready to be analyzed.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="info-text">
                CSV dataset detected.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="height: 30px;"></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:

        if st.button("Analyze Data", use_container_width=True):

            go_to("analyzing")


# ---------------------------------------------------------
# SCREEN 3: ANALYZING
# ---------------------------------------------------------

elif st.session_state.screen == "analyzing":

    st.markdown(
        '<div style="height: 180px;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="processing-title">Analyzing your data...</div>',
        unsafe_allow_html=True,
    )

    # Loading indicator
    progress_placeholder = st.empty()

    progress_placeholder.markdown(
        """
        <div style="
            text-align:center;
            color:#2563EB;
            font-size:28px;
            letter-spacing:8px;
        ">
            • • •
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="height: 20px;"></div>',
        unsafe_allow_html=True,
    )

    steps = [
        "Reading your file",
        "Understanding your data",
        "Running analysis",
        "Selecting visualizations",
    ]

    for step in steps:
        st.markdown(
            f'<div class="processing-step">{step}</div>',
            unsafe_allow_html=True,
        )

    # Temporary processing delay
    time.sleep(2)

    st.session_state.analysis_complete = True
    go_to("results")


# ---------------------------------------------------------
# SCREEN 4: RESULTS
# ---------------------------------------------------------

elif st.session_state.screen == "results":

    st.markdown(
        '<div style="height: 50px;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="result-title">Analysis Complete</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="result-subtitle">
            Here are the visualizations selected from your data.
        </div>
        """,
        unsafe_allow_html=True,
    )

    visualization_count = st.session_state.visualization_count

    # -----------------------------------------------------
    # 1 VISUALIZATION
    # -----------------------------------------------------

    if visualization_count == 1:

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            show_chart_placeholder(1)

    # -----------------------------------------------------
    # 2 VISUALIZATIONS
    # -----------------------------------------------------

    elif visualization_count == 2:

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            show_chart_placeholder(1)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        with col2:
            show_chart_placeholder(2)

    # -----------------------------------------------------
    # 3 VISUALIZATIONS
    # -----------------------------------------------------

    elif visualization_count == 3:

        col1, col2 = st.columns(2)

        with col1:
            show_chart_placeholder(1)

        with col2:
            show_chart_placeholder(2)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            show_chart_placeholder(3)

    # -----------------------------------------------------
    # 4 VISUALIZATIONS
    # -----------------------------------------------------

    elif visualization_count == 4:

        col1, col2 = st.columns(2)

        with col1:
            show_chart_placeholder(1)

        with col2:
            show_chart_placeholder(2)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            show_chart_placeholder(3)

        with col2:
            show_chart_placeholder(4)

    # -----------------------------------------------------
    # RESTART
    # -----------------------------------------------------

    st.markdown('<div style="height:40px;"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:

        if st.button("Analyze Another File", use_container_width=True):

            st.session_state.screen = "welcome"
            st.session_state.uploaded_file = None
            st.session_state.analysis_complete = False
            st.rerun()