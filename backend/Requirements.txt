# Prototype Analyser

An automated exploratory data analysis tool that allows users to upload a CSV dataset and receive a structured analysis with automatically selected visualizations.

The goal is simple: reduce the amount of manual work required to understand a new dataset.

---

## Overview

When a user uploads a CSV file, the system processes the dataset through a Python-based analysis pipeline.

The application:

1. Loads and validates the uploaded dataset
2. Understands the structure of the dataset
3. Performs exploratory data analysis
4. Identifies useful statistical relationships and patterns
5. Selects visualizations based on the characteristics of the data
6. Generates the selected visualizations
7. Presents the results through a simple web interface

The current version is **Prototype 0.0**.

---

## Current Features

### Dataset Understanding

The system identifies basic structural information including:

- Number of rows
- Number of columns
- Column names
- Data types
- Non-null values
- Missing values
- Unique values
- Duplicate rows

### Exploratory Analysis

The analysis engine currently performs:

- Descriptive statistics
- Mean
- Median
- Mode
- Standard deviation
- Variance
- Minimum and maximum values
- Quartiles
- Interquartile range
- Skewness
- Categorical frequency analysis
- Missing-value analysis
- Numerical correlation analysis
- Potential outlier detection using the IQR method

### Automated Visualization Selection

The system does not simply display a fixed dashboard.

Instead, the visualization engine evaluates the dataset and recommends visualization candidates based on the available columns and analysis results.

The renderer then generates the selected charts.

Current visualization types include:

- Distribution plots
- Scatter plots
- Box plots
- Correlation heatmaps
- Categorical frequency charts

The exact visualizations depend on the uploaded dataset.

### Key Findings

The interface presents a small set of automatically generated findings, including information such as:

- Dataset size
- Data quality observations
- Strong numerical relationships
- Potential outliers

### Chart Download

Generated visualizations can be downloaded individually from the results interface.

---

## Architecture

The project follows a modular pipeline architecture:

```text
                    CSV Upload
                         │
                         ▼
                ┌─────────────────┐
                │ File Handling   │
                └────────┬────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Dataset Understanding│
              └──────────┬──────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Analysis Engine │
                └────────┬────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Visualization Engine  │
             └───────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ Visualization Renderer │
            └────────────┬───────────┘
                         │
                         ▼
                  Web Interface