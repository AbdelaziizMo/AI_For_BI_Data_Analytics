"""
AI Visualization Generator

Reads:
    output/sanitized_analysis.json
    output/visualization_plan.json
    output/visualization_validation.json

Generates PNG charts only when the visualization
validation status is SAFE_TO_GENERATE.
"""

import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ANALYSIS_FILE = BASE_DIR / "output" / "sanitized_analysis.json"
PLAN_FILE = BASE_DIR / "output" / "visualization_plan.json"
VALIDATION_FILE = (
    BASE_DIR / "output" / "visualization_validation.json"
)

OUTPUT_DIR = BASE_DIR / "output" / "visualizations"


# ============================================================
# Utility Functions
# ============================================================

def load_json(file_path: Path) -> dict:
    """Load JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def safe_filename(text: str) -> str:
    """Convert chart title into a safe filename."""

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text
    )

    return text.strip("_")


def format_number(value):
    """Format large numeric values for chart labels."""

    if pd.isna(value):
        return ""

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


# ============================================================
# Chart Generators
# ============================================================

def generate_bar_chart(
    dataframe: pd.DataFrame,
    chart: dict,
    output_path: Path
):
    """Generate a vertical bar chart."""

    x_field = chart["x"]
    y_field = chart["y"]

    title = chart["title"]

    dataframe = dataframe.copy()

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    required_fields = [
        x_field,
        y_field
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in dataframe.columns
    ]

    if missing_fields:
        raise ValueError(
            "Bar chart requires missing field(s): "
            + ", ".join(missing_fields)
        )

    # --------------------------------------------------------
    # Prepare numeric data
    # --------------------------------------------------------

    dataframe[y_field] = pd.to_numeric(
        dataframe[y_field],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            x_field,
            y_field
        ]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid data available for bar chart."
        )

    # --------------------------------------------------------
    # Prepare X-axis labels
    # --------------------------------------------------------

    labels = dataframe[x_field].astype(str)

    if "date" in x_field.lower():

        parsed_dates = pd.to_datetime(
            dataframe[x_field],
            errors="coerce"
        )

        formatted_dates = parsed_dates.dt.strftime(
            "%b %d, %Y"
        )

        labels = formatted_dates.fillna(
            dataframe[x_field].astype(str)
        )

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    plt.figure(
        figsize=(12, 7)
    )

    bars = plt.bar(
        labels,
        dataframe[y_field]
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    plt.title(
        title,
        fontsize=16,
        fontweight="bold"
    )

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    plt.xlabel(
        x_field.replace("_", " ").title()
    )

    plt.ylabel(
        y_field.replace("_", " ").title()
    )

    # --------------------------------------------------------
    # Add values above bars
    # --------------------------------------------------------

    for bar, value in zip(
        bars,
        dataframe[y_field]
    ):

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            format_number(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.xticks(
        rotation=0
    )

    plt.tight_layout()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


def generate_line_chart(
    dataframe: pd.DataFrame,
    chart: dict,
    output_path: Path
):
    """Generate a line chart."""

    x_field = chart["x"]
    y_field = chart["y"]
    series_field = chart.get("series")

    title = chart["title"]

    dataframe = dataframe.copy()

    dataframe[x_field] = pd.to_datetime(
        dataframe[x_field],
        errors="coerce"
    )

    dataframe[y_field] = pd.to_numeric(
        dataframe[y_field],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            x_field,
            y_field
        ]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid data available for line chart."
        )

    plt.figure(
        figsize=(14, 7)
    )

    if series_field:

        if series_field not in dataframe.columns:
            raise ValueError(
                f"Line chart requires missing series field: "
                f"{series_field}"
            )

        for series_value, group in dataframe.groupby(
            series_field
        ):

            group = group.sort_values(
                x_field
            )

            plt.plot(
                group[x_field],
                group[y_field],
                marker="o",
                linewidth=2,
                label=str(series_value)
            )

        plt.legend(
            title=series_field,
            bbox_to_anchor=(1.02, 1),
            loc="upper left"
        )

    else:

        dataframe = dataframe.sort_values(
            x_field
        )

        plt.plot(
            dataframe[x_field],
            dataframe[y_field],
            marker="o",
            linewidth=2
        )

    plt.title(
        title,
        fontsize=16,
        fontweight="bold"
    )

    plt.xlabel(
        x_field.replace("_", " ").title()
    )

    plt.ylabel(
        y_field.replace("_", " ").title()
    )

    plt.xticks(
        rotation=45
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


def generate_horizontal_bar_chart(
    dataframe: pd.DataFrame,
    chart: dict,
    output_path: Path
):
    """Generate a horizontal bar chart."""

    x_field = chart["x"]
    y_field = chart["y"]

    title = chart["title"]

    aggregation = chart.get(
        "aggregation",
        "sum"
    ).lower()

    dataframe = dataframe.copy()

    dataframe[x_field] = pd.to_numeric(
        dataframe[x_field],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            x_field,
            y_field
        ]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid data available for horizontal bar chart."
        )

    # --------------------------------------------------------
    # Aggregate values by category
    # --------------------------------------------------------

    supported_aggregations = {
        "sum": "sum",
        "max": "max",
        "min": "min",
        "mean": "mean"
    }

    if aggregation not in supported_aggregations:

        raise ValueError(
            f"Unsupported aggregation: {aggregation}. "
            f"Supported values: "
            f"{', '.join(supported_aggregations.keys())}"
        )

    dataframe = (
        dataframe
        .groupby(
            y_field,
            as_index=False
        )[x_field]
        .agg(
            supported_aggregations[aggregation]
        )
    )

    # --------------------------------------------------------
    # Sort and select top 10
    # --------------------------------------------------------

    dataframe = dataframe.sort_values(
        x_field,
        ascending=True
    )

    dataframe = dataframe.tail(10)

    plt.figure(
        figsize=(12, 7)
    )

    bars = plt.barh(
        dataframe[y_field].astype(str),
        dataframe[x_field]
    )

    plt.title(
        title,
        fontsize=16,
        fontweight="bold"
    )

    plt.xlabel(
        x_field.replace("_", " ").title()
    )

    plt.ylabel(
        y_field.replace("_", " ").title()
    )

    # --------------------------------------------------------
    # Add values to bars
    # --------------------------------------------------------

    for bar, value in zip(
        bars,
        dataframe[x_field]
    ):

        plt.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f" {format_number(value)}",
            va="center",
            fontsize=9
        )

    plt.grid(
        axis="x",
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


def generate_scatter_chart(
    dataframe: pd.DataFrame,
    chart: dict,
    output_path: Path
):
    """Generate a scatter chart."""

    x_field = chart["x"]
    y_field = chart["y"]
    label_field = chart.get("label")

    title = chart["title"]

    dataframe = dataframe.copy()

    dataframe[x_field] = pd.to_numeric(
        dataframe[x_field],
        errors="coerce"
    )

    dataframe[y_field] = pd.to_numeric(
        dataframe[y_field],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            x_field,
            y_field
        ]
    )

    if dataframe.empty:
        raise ValueError(
            "No valid data available for scatter chart."
        )

    # --------------------------------------------------------
    # Avoid duplicate observations
    # --------------------------------------------------------

    if label_field:

        if label_field not in dataframe.columns:
            raise ValueError(
                f"Scatter chart requires missing label field: "
                f"{label_field}"
            )

        dataframe = (
            dataframe
            .groupby(
                label_field,
                as_index=False
            )
            .agg({
                x_field: "max",
                y_field: "max"
            })
        )

    plt.figure(
        figsize=(12, 8)
    )

    plt.scatter(
        dataframe[x_field],
        dataframe[y_field],
        s=80,
        alpha=0.75
    )

    # --------------------------------------------------------
    # Add labels
    # --------------------------------------------------------

    if label_field:

        for _, row in dataframe.iterrows():

            plt.annotate(
                str(row[label_field]),
                (
                    row[x_field],
                    row[y_field]
                ),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8
            )

    plt.title(
        title,
        fontsize=16,
        fontweight="bold"
    )

    plt.xlabel(
        x_field.replace("_", " ").title()
    )

    plt.ylabel(
        y_field.replace("_", " ").title()
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


def generate_heatmap(
    dataframe: pd.DataFrame,
    chart: dict,
    output_path: Path
):
    """
    Generate a service/date heatmap.

    Expected fields:
        x -> transaction_date
        y -> service_id
        value -> daily_revenue
    """

    x_field = chart["x"]
    y_field = chart["y"]

    value_field = chart.get(
        "value",
        "daily_revenue"
    )

    title = chart["title"]

    dataframe = dataframe.copy()

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    required_fields = [
        x_field,
        y_field,
        value_field
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in dataframe.columns
    ]

    if missing_fields:

        raise ValueError(
            "Heatmap requires missing field(s): "
            + ", ".join(missing_fields)
        )

    # --------------------------------------------------------
    # Prepare data types
    # --------------------------------------------------------

    dataframe[x_field] = pd.to_datetime(
        dataframe[x_field],
        errors="coerce"
    )

    dataframe[value_field] = pd.to_numeric(
        dataframe[value_field],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=[
            x_field,
            y_field,
            value_field
        ]
    )

    if dataframe.empty:

        raise ValueError(
            "No valid data available for heatmap."
        )

    # --------------------------------------------------------
    # Create pivot table
    # --------------------------------------------------------

    pivot_table = dataframe.pivot_table(
        index=y_field,
        columns=x_field,
        values=value_field,
        aggfunc="sum"
    )

    if pivot_table.empty:

        raise ValueError(
            "Heatmap pivot table is empty."
        )

    pivot_table = pivot_table.sort_index(
        axis=0
    )

    pivot_table = pivot_table.sort_index(
        axis=1
    )

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    plt.figure(
        figsize=(14, 8)
    )

    image = plt.imshow(
        pivot_table.values,
        aspect="auto",
        interpolation="nearest"
    )

    # --------------------------------------------------------
    # X-axis labels
    # --------------------------------------------------------

    x_labels = [
        pd.to_datetime(date).strftime("%b %d")
        for date in pivot_table.columns
    ]

    plt.xticks(
        range(len(x_labels)),
        x_labels,
        rotation=45
    )

    # --------------------------------------------------------
    # Y-axis labels
    # --------------------------------------------------------

    y_labels = [
        str(value)
        for value in pivot_table.index
    ]

    plt.yticks(
        range(len(y_labels)),
        y_labels
    )

    # --------------------------------------------------------
    # Labels and title
    # --------------------------------------------------------

    plt.xlabel(
        x_field.replace("_", " ").title()
    )

    plt.ylabel(
        y_field.replace("_", " ").title()
    )

    plt.title(
        title,
        fontsize=16,
        fontweight="bold"
    )

    # --------------------------------------------------------
    # Color scale
    # --------------------------------------------------------

    colorbar = plt.colorbar(
        image
    )

    colorbar.set_label(
        value_field.replace("_", " ").title()
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# Chart Dispatcher
# ============================================================

def generate_chart(
    dataframe: pd.DataFrame,
    chart: dict,
    index: int
):
    """Generate chart based on AI visualization type."""

    chart_type = chart["type"]
    title = chart["title"]

    filename = (
        f"{index:02d}_"
        f"{safe_filename(title)}.png"
    )

    output_path = OUTPUT_DIR / filename

    if chart_type == "bar":

        generate_bar_chart(
            dataframe,
            chart,
            output_path
        )

    elif chart_type == "line":

        generate_line_chart(
            dataframe,
            chart,
            output_path
        )

    elif chart_type == "horizontal_bar":

        generate_horizontal_bar_chart(
            dataframe,
            chart,
            output_path
        )

    elif chart_type == "scatter":

        generate_scatter_chart(
            dataframe,
            chart,
            output_path
        )

    elif chart_type == "heatmap":

        generate_heatmap(
            dataframe,
            chart,
            output_path
        )

    else:

        raise ValueError(
            f"Unsupported chart type: {chart_type}"
        )

    return output_path


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("AI VISUALIZATION GENERATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Step 1: Load validation result
    # --------------------------------------------------------

    print(
        "\n[1/5] Checking visualization validation..."
    )

    try:

        validation = load_json(
            VALIDATION_FILE
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    validation_status = validation.get(
        "status"
    )

    print(
        f"Validation status: "
        f"{validation_status}"
    )

    if validation_status != "SAFE_TO_GENERATE":

        print(
            "\nGeneration BLOCKED."
        )

        print(
            "Visualization plan did not pass validation."
        )

        sys.exit(1)

    print(
        "Validation passed."
    )

    # --------------------------------------------------------
    # Step 2: Load visualization plan
    # --------------------------------------------------------

    print(
        "\n[2/5] Loading visualization plan..."
    )

    try:

        plan = load_json(
            PLAN_FILE
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    visualizations = plan.get(
        "visualizations",
        []
    )

    if not visualizations:

        print(
            "ERROR: No visualizations found in plan."
        )

        sys.exit(1)

    print(
        f"Found {len(visualizations)} visualizations."
    )

    # --------------------------------------------------------
    # Step 3: Load sanitized analytical data
    # --------------------------------------------------------

    print(
        "\n[3/5] Loading sanitized analytical data..."
    )

    try:

        analysis = load_json(
            ANALYSIS_FILE
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )

        sys.exit(1)

    if analysis.get(
        "privacy_status"
    ) != "SANITIZED":

        print(
            "ERROR: Analytical data is not SANITIZED."
        )

        print(
            "Generation BLOCKED."
        )

        sys.exit(1)

    dataframe = pd.DataFrame(
        analysis.get(
            "results",
            []
        )
    )

    if dataframe.empty:

        print(
            "ERROR: Sanitized analytical results are empty."
        )

        sys.exit(1)

    print(
        f"Loaded {len(dataframe):,} sanitized rows."
    )

    print(
        f"Available fields: "
        f"{len(dataframe.columns)}"
    )

    print(
        "Fields:"
    )

    for column in dataframe.columns:

        print(
            f"  - {column}"
        )

    # --------------------------------------------------------
    # Step 4: Prepare output directory
    # --------------------------------------------------------

    print(
        "\n[4/5] Preparing visualization output..."
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Remove previous generated charts
    # --------------------------------------------------------

    old_files = list(
        OUTPUT_DIR.glob("*.png")
    )

    for old_file in old_files:

        old_file.unlink()

    print(
        f"Removed previous PNG files: "
        f"{len(old_files)}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    # --------------------------------------------------------
    # Step 5: Generate visualizations
    # --------------------------------------------------------

    print(
        "\n[5/5] Generating visualizations..."
    )

    generated_files = []

    for index, chart in enumerate(
        visualizations,
        start=1
    ):

        title = chart.get(
            "title",
            "Untitled"
        )

        chart_type = chart.get(
            "type"
        )

        print(
            f"\n[{index}/{len(visualizations)}] "
            f"{title}"
        )

        print(
            f"    Type: {chart_type}"
        )

        print(
            f"    X: {chart.get('x')}"
        )

        print(
            f"    Y: {chart.get('y')}"
        )

        try:

            output_path = generate_chart(
                dataframe,
                chart,
                index
            )

            generated_files.append(
                output_path
            )

            print(
                "    Status: GENERATED"
            )

            print(
                f"    File: {output_path.name}"
            )

        except Exception as error:

            print(
                "    Status: FAILED"
            )

            print(
                f"    Error: {error}"
            )

            sys.exit(1)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "GENERATION SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        f"Total visualizations: "
        f"{len(visualizations)}"
    )

    print(
        f"Generated successfully: "
        f"{len(generated_files)}"
    )

    print(
        f"Output directory:"
        f"\n{OUTPUT_DIR}"
    )

    print(
        "\nGenerated files:"
    )

    for file_path in generated_files:

        print(
            f"  - {file_path.name}"
        )

    print(
        "=" * 60
    )

    print(
        "\nVISUALIZATION_GENERATION_COMPLETE"
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()