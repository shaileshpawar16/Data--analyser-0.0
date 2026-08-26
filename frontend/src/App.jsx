import { useState } from "react";
import "./App.css";

const API_URL = 
 import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV
    ? "http://127.0.0.1:8000"
    : "https://data-analyser-0-0-backend.onrender.com");

function App() {
  const [screen, setScreen] = useState(1);
  const [file, setFile] = useState(null);
  const [dataset, setDataset] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [charts, setCharts] = useState([]);
  const [error, setError] = useState("");

  // =====================================================
  // UPLOAD FILE
  // =====================================================

  const handleUpload = async (event) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    setError("");
    setFile(selectedFile);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        `${API_URL}/api/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      console.log("BACKEND RESPONSE:", data);

      if (!response.ok) {
        throw new Error(
          data.detail || "File upload failed."
        );
      }

      setDataset(data.dataset);
      setAnalysis(data.analysis);
      setCharts(data.charts || []);

      setScreen(2);

    } catch (err) {
      console.error(err);

      setError(
        err.message || "Something went wrong."
      );
    }
  };


  // =====================================================
  // ANALYZE DATA
  // =====================================================

  const handleAnalyze = async () => {
    setError("");
    setScreen(3);

    setTimeout(() => {
      setScreen(4);
    }, 1200);
  };


  // =====================================================
  // KEY FINDINGS
  // =====================================================

  const generateKeyFindings = () => {
    if (!analysis) return [];

    const findings = [];

    // -----------------------------------------------------
    // DATASET SIZE
    // -----------------------------------------------------

    if (dataset) {
      findings.push({
        label: "Dataset",
        text: `${dataset.rows.toLocaleString()} rows across ${dataset.columns} columns.`,
      });
    }

    // -----------------------------------------------------
    // MISSING VALUES
    // -----------------------------------------------------

    const missingValues =
      analysis.missing_values || [];

    const totalMissing = missingValues.reduce(
      (total, column) =>
        total + (column.missing_count || 0),
      0
    );

    const columnsWithMissing =
      missingValues.filter(
        (column) =>
          (column.missing_count || 0) > 0
      );

    if (totalMissing === 0) {
      findings.push({
        label: "Data quality",
        text: "No missing values were detected.",
      });
    } else {
      findings.push({
        label: "Data quality",
        text: `${totalMissing.toLocaleString()} missing values were found across ${columnsWithMissing.length} columns.`,
      });
    }

    // -----------------------------------------------------
    // CORRELATION
    // -----------------------------------------------------

    const correlation =
      analysis.correlation;

    if (
      correlation &&
      correlation.columns &&
      correlation.matrix &&
      correlation.columns.length >= 2
    ) {
      let strongestCorrelation = null;

      for (
        let i = 0;
        i < correlation.columns.length;
        i++
      ) {
        for (
          let j = i + 1;
          j < correlation.columns.length;
          j++
        ) {
          const value =
            correlation.matrix[i]?.[j];

          if (
            value === null ||
            value === undefined
          ) {
            continue;
          }

          if (
            strongestCorrelation === null ||
            Math.abs(value) >
              Math.abs(strongestCorrelation.value)
          ) {
            strongestCorrelation = {
              first:
                correlation.columns[i],
              second:
                correlation.columns[j],
              value,
            };
          }
        }
      }

      if (strongestCorrelation) {
        const direction =
          strongestCorrelation.value > 0
            ? "positive"
            : "negative";

        findings.push({
          label: "Strongest relationship",
          text: `${strongestCorrelation.first} and ${strongestCorrelation.second} show the strongest ${direction} correlation (${strongestCorrelation.value.toFixed(2)}).`,
        });
      }
    }

    // -----------------------------------------------------
    // OUTLIERS
    // -----------------------------------------------------

    const outliers =
      analysis.potential_outliers || [];

    const columnsWithOutliers =
      outliers
        .filter(
          (item) =>
            item.analysis &&
            item.analysis.outlier_count > 0
        )
        .sort(
          (a, b) =>
            b.analysis.outlier_count -
            a.analysis.outlier_count
        );

    if (columnsWithOutliers.length > 0) {
      const topOutlier =
        columnsWithOutliers[0];

      findings.push({
        label: "Potential outliers",
        text: `${topOutlier.column_name} contains ${topOutlier.analysis.outlier_count.toLocaleString()} potential outlier${topOutlier.analysis.outlier_count === 1 ? "" : "s"}.`,
      });
    } else {
      findings.push({
        label: "Potential outliers",
        text: "No potential outliers were detected in the numerical columns.",
      });
    }

    return findings.slice(0, 4);
  };


  // =====================================================
  // DOWNLOAD CHART
  // =====================================================

  const downloadChart = (
    chart,
    index
  ) => {
    const link =
      document.createElement("a");

    link.href =
      `data:image/png;base64,${chart.image}`;

    link.download =
      `${chart.visualization_type || "chart"}-${index + 1}.png`;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
  };


  // =====================================================
  // ERROR SCREEN
  // =====================================================

  if (error) {
    return (
      <main className="app">

        <section className="screen">

          <div className="welcome-content">

            <h1>
              Something went wrong.
            </h1>

            <p>
              {error}
            </p>

            <button
              className="primary-button"
              onClick={() => {
                setError("");
                setScreen(1);
                setFile(null);
                setDataset(null);
                setAnalysis(null);
                setCharts([]);
              }}
            >
              Try Again
            </button>

          </div>

        </section>

      </main>
    );
  }


  // =====================================================
  // SCREEN 1
  // =====================================================

  if (screen === 1) {
    return (
      <main className="app">

        <section className="screen welcome-screen">

          <div className="welcome-content">

            <h1>
              Welcome.
            </h1>

            <p>
              Let us help you analyze your data.
            </p>

            <label className="primary-button">

              <span>
                Upload File
              </span>

              <input
                type="file"
                accept=".csv"
                onChange={handleUpload}
              />

            </label>

            <small>
              Only CSV files are accepted for now
            </small>

          </div>

        </section>

      </main>
    );
  }

  // =====================================================
  // SCREEN 2
  // =====================================================

  if (screen === 2) {
    return (
      <main className="app">

        <section className="screen upload-screen">

          <div className="upload-content">

            <h1>
              File uploaded successfully
            </h1>

            <p>
              Your file contains{" "}
              {dataset?.rows ?? "..."} rows and{" "}
              {dataset?.columns ?? "..."} columns.
            </p>

            <p>
              Columns:{" "}
              {dataset?.column_names?.join(", ") ?? "..."}
            </p>

            <button
              className="primary-button analyze-button"
              onClick={handleAnalyze}
            >
              Analyze Data
            </button>

          </div>

        </section>

      </main>
    );
  }


  // =====================================================
  // SCREEN 3
  // =====================================================

  if (screen === 3) {
    return (
      <main className="app">

        <section className="screen analyzing-screen">

          <div className="analyzing-content">

            <h1>
              Analyzing your data
            </h1>

            <div className="dots">

              <span />
              <span />
              <span />

            </div>

            <div className="analysis-steps">

              <div>
                Reading your file
              </div>

              <div>
                Understanding your data
              </div>

              <div>
                Running analysis
              </div>

              <div>
                Selecting visualizations
              </div>

            </div>

          </div>

        </section>

      </main>
    );
  }


  // =====================================================
  // SCREEN 4
  // =====================================================

  const keyFindings =
    generateKeyFindings();

  return (
    <main className="app">

      <section className="screen complete-screen">

        {/* =================================================
            HEADER
        ================================================= */}

        <div className="complete-header">

          <h1>
            Analysis complete
          </h1>

          <p>
            Here are the visualizations selected from your data.
          </p>

        </div>


        {/* =================================================
            KEY FINDINGS
        ================================================= */}

        {keyFindings.length > 0 && (

          <section className="key-findings">

            <div className="section-heading">
              Key findings
            </div>

            <div className="findings-grid">

              {keyFindings.map(
                (finding, index) => (

                  <div
                    className="finding-card"
                    key={index}
                  >

                    <div className="finding-label">
                      {finding.label}
                    </div>

                    <div className="finding-text">
                      {finding.text}
                    </div>

                  </div>

                )
              )}

            </div>

          </section>

        )}


        {/* =================================================
            VISUALIZATIONS
        ================================================= */}

        <div
          className={`visualization-grid charts-${Math.min(
            charts.length,
            4
          )}`}
        >

          {charts.length === 0 ? (

            <div className="visualization-card">

              <span>
                No visualizations generated.
              </span>

            </div>

          ) : (

            charts.map(
              (chart, index) => (

                <div
                  className="visualization-card"
                  key={
                    chart.candidate_id ||
                    index
                  }
                >

                  <div className="chart-image-wrapper">

                    <img
                      src={`data:image/png;base64,${chart.image}`}
                      alt={
                        chart.visualization_type ||
                        "Data visualization"
                      }
                    />

                  </div>


                  <div className="chart-footer">

                    <button
                      className="download-button"
                      onClick={() =>
                        downloadChart(
                          chart,
                          index
                        )
                      }
                    >
                      ↓ Download chart
                    </button>

                  </div>

                </div>

              )
            )

          )}

        </div>

      </section>

    </main>
  );
}

export default App;