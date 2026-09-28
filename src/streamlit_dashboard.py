from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.chat_history import (
    get_conversation,
    get_conversation_analyses,
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="AI BI Dashboard",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"
ANALYSES_DIR = OUTPUT_DIR / "analyses"


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

        .main {
            background: #f6f9f8;
        }

        .dashboard-title {
            color: #063f38;
            font-size: 30px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .dashboard-subtitle {
            color: #5e706d;
            margin-bottom: 24px;
        }

        .analysis-title {
            color: #006f61;
            font-size: 22px;
            font-weight: 700;
            margin-top: 10px;
        }

        .question-box {
            background: white;
            border-left: 4px solid #f47b20;
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 18px;
        }

        .conversation-box {
            background: white;
            padding: 18px;
            border-radius: 10px;
            border: 1px solid #e2e8e6;
            margin-bottom: 20px;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# QUERY PARAMETER
# ============================================================

conversation_id = st.query_params.get("conversation_id")


# ============================================================
# VALIDATE CONVERSATION ID
# ============================================================

if not conversation_id:

    st.markdown(
        '<div class="dashboard-title">'
        'AI BI Dashboard'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "No conversation was selected."
    )

    st.markdown(
        """
        Open the dashboard from the **Web Chat** after running
        a BI analysis.
        """
    )

    st.stop()


# ============================================================
# LOAD CONVERSATION
# ============================================================

try:

    conversation = get_conversation(
        conversation_id
    )

except Exception as error:

    st.error(
        f"Could not load conversation: {error}"
    )

    st.stop()


if not conversation:

    st.error(
        "The requested conversation could not be found."
    )

    st.stop()


# ============================================================
# LOAD ANALYSES
# ============================================================

try:

    analyses = get_conversation_analyses(
        conversation_id
    )

except Exception as error:

    st.error(
        f"Could not load conversation analyses: {error}"
    )

    st.stop()


# ============================================================
# HELPERS
# ============================================================

def load_analysis_artifacts(
    analysis_id: str,
):
    """
    Load artifacts belonging only to this analysis.
    """

    analysis_dir = (
        ANALYSES_DIR
        / str(analysis_id)
    )

    sanitized_path = (
        analysis_dir
        / "sanitized_analysis.json"
    )

    spec_path = (
        analysis_dir
        / "visualization_spec.json"
    )

    report_path = (
        analysis_dir
        / "ai_business_report.md"
    )

    analysis = None
    spec = None
    report = None

    # --------------------------------------------------------
    # Sanitized analysis
    # --------------------------------------------------------

    if sanitized_path.exists():

        try:

            analysis = json.loads(
                sanitized_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as error:

            st.error(
                "Could not load sanitized analysis: "
                f"{error}"
            )

    # --------------------------------------------------------
    # Visualization specification
    # --------------------------------------------------------

    if spec_path.exists():

        try:

            spec = json.loads(
                spec_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as error:

            st.error(
                "Could not load visualization specification: "
                f"{error}"
            )

    # --------------------------------------------------------
    # AI report
    # --------------------------------------------------------

    if report_path.exists():

        try:

            report = report_path.read_text(
                encoding="utf-8"
            )

        except Exception as error:

            st.error(
                "Could not load AI business report: "
                f"{error}"
            )

    return (
        analysis,
        spec,
        report,
        analysis_dir,
    )


# ============================================================
# RENDER VISUAL
# ============================================================

def render_visual(
    dataframe: pd.DataFrame,
    visual: dict,
    analysis_id: str,
    visual_index: int,
):
    """
    Render a visualization based on the visualization
    specification generated for this analysis.
    """

    visual_type = visual.get(
        "type"
    )

    title = visual.get(
        "title",
        "Visualization",
    )

    # ========================================================
    # DAILY REVENUE PEAK
    # ========================================================

    if visual_type == "daily_revenue_peak":

        x = visual.get("x")
        y = visual.get("y")

        if not x or not y:

            st.warning(
                "Invalid daily revenue peak specification."
            )

            return

        if x not in dataframe.columns:

            st.warning(
                f"Column '{x}' is not available."
            )

            return

        if y not in dataframe.columns:

            st.warning(
                f"Column '{y}' is not available."
            )

            return

        chart_df = dataframe[
            [x, y]
        ].copy()

        chart_df[x] = pd.to_datetime(
            chart_df[x],
            errors="coerce",
        )

        chart_df[y] = pd.to_numeric(
            chart_df[y],
            errors="coerce",
        )

        chart_df = (
            chart_df
            .dropna(subset=[x, y])
            .groupby(
                x,
                as_index=False,
            )[y]
            .sum()
            .sort_values(x)
        )

        if chart_df.empty:

            st.info(
                "No valid data available for this visualization."
            )

            return

        peak_index = chart_df[y].idxmax()

        peak_row = chart_df.loc[
            peak_index
        ]

        figure = px.line(
            chart_df,
            x=x,
            y=y,
            markers=True,
            title=title,
        )

        figure.add_annotation(
            x=peak_row[x],
            y=peak_row[y],
            text="Peak Revenue",
            showarrow=True,
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key=(
                f"{analysis_id}"
                f"_peak_"
                f"{visual_index}"
            ),
        )

        return

    # ========================================================
    # LINE
    # ========================================================

    if visual_type == "line":

        x = visual.get("x")
        y = visual.get("y")

        if not x or not y:

            st.warning(
                "Invalid line chart specification."
            )

            return

        if x not in dataframe.columns:

            st.warning(
                f"Column '{x}' is not available."
            )

            return

        if y not in dataframe.columns:

            st.warning(
                f"Column '{y}' is not available."
            )

            return

        chart_df = dataframe[
            [x, y]
        ].copy()

        # Try datetime conversion only when appropriate.
        converted_x = pd.to_datetime(
            chart_df[x],
            errors="coerce",
        )

        if converted_x.notna().sum() > 0:

            chart_df[x] = converted_x

        chart_df[y] = pd.to_numeric(
            chart_df[y],
            errors="coerce",
        )

        chart_df = (
            chart_df
            .dropna(subset=[x, y])
            .groupby(
                x,
                as_index=False,
            )[y]
            .sum()
            .sort_values(x)
        )

        if chart_df.empty:

            st.info(
                "No valid data available for this visualization."
            )

            return

        figure = px.line(
            chart_df,
            x=x,
            y=y,
            markers=True,
            title=title,
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key=(
                f"{analysis_id}"
                f"_line_"
                f"{visual_index}"
            ),
        )

        return

    # ========================================================
    # TOP SERVICES
    # ========================================================

    if visual_type == "top_services":

        category = visual.get(
            "category"
        )

        value = visual.get(
            "value"
        )

        if not category or not value:

            st.warning(
                "Invalid top services specification."
            )

            return

        if category not in dataframe.columns:

            st.warning(
                f"Column '{category}' is not available."
            )

            return

        if value not in dataframe.columns:

            st.warning(
                f"Column '{value}' is not available."
            )

            return

        chart_df = dataframe[
            [category, value]
        ].copy()

        chart_df[value] = pd.to_numeric(
            chart_df[value],
            errors="coerce",
        )

        chart_df = (
            chart_df
            .dropna(
                subset=[
                    category,
                    value,
                ]
            )
            .groupby(
                category,
                as_index=False,
            )[value]
            .sum()
            .sort_values(
                value,
                ascending=False,
            )
            .head(10)
        )

        if chart_df.empty:

            st.info(
                "No valid service data available."
            )

            return

        figure = px.bar(
            chart_df.sort_values(value),
            x=value,
            y=category,
            orientation="h",
            title=title,
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key=(
                f"{analysis_id}"
                f"_services_"
                f"{visual_index}"
            ),
        )

        return

    # ========================================================
    # REVENUE SHARE
    # ========================================================

    if visual_type == "revenue_share":

        category = visual.get(
            "category"
        )

        value = visual.get(
            "value"
        )

        if not category or not value:

            st.warning(
                "Invalid revenue share specification."
            )

            return

        if category not in dataframe.columns:

            st.warning(
                f"Column '{category}' is not available."
            )

            return

        if value not in dataframe.columns:

            st.warning(
                f"Column '{value}' is not available."
            )

            return

        chart_df = dataframe[
            [category, value]
        ].copy()

        chart_df[value] = pd.to_numeric(
            chart_df[value],
            errors="coerce",
        )

        chart_df = (
            chart_df
            .dropna(
                subset=[
                    category,
                    value,
                ]
            )
            .groupby(
                category,
                as_index=False,
            )[value]
            .sum()
            .sort_values(
                value,
                ascending=False,
            )
            .head(10)
        )

        if chart_df.empty:

            st.info(
                "No valid revenue share data available."
            )

            return

        figure = px.bar(
            chart_df.sort_values(value),
            x=value,
            y=category,
            orientation="h",
            title=title,
        )

        st.plotly_chart(
            figure,
            width="stretch",
            key=(
                f"{analysis_id}"
                f"_share_"
                f"{visual_index}"
            ),
        )

        return

    # ========================================================
    # UNKNOWN
    # ========================================================

    st.info(
        f"Visualization type '{visual_type}' "
        "is not supported by the dashboard yet."
    )


# ============================================================
# RENDER ANALYSIS
# ============================================================

def render_analysis(
    analysis_meta: dict,
    index: int,
):
    """
    Render one analysis with its own report and
    visualization specification.
    """

    analysis_id = analysis_meta.get(
        "analysis_id"
    )

    if not analysis_id:
        return

    (
        analysis,
        spec,
        report,
        analysis_dir,
    ) = load_analysis_artifacts(
        analysis_id
    )

    if analysis is None:

        st.warning(
            f"Analysis artifacts not found: {analysis_id}"
        )

        return

    # ========================================================
    # QUESTION
    # ========================================================

    question = (
        analysis.get(
            "business_question"
        )
        or analysis_meta.get(
            "business_question",
            "Business Analysis",
        )
    )

    st.markdown(
        f"""
        <div class="analysis-title">
            Analysis {index}
        </div>
        """,
        unsafe_allow_html=True,
    )

    safe_question = html.escape(
        str(question)
    )

    st.markdown(
        f"""
        <div class="question-box">
            <strong>Business Question:</strong><br>
            {safe_question}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # METADATA
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Analysis ID",
            str(analysis_id)[-12:],
        )

    with col2:

        follow_up = analysis_meta.get(
            "is_follow_up",
            False,
        )

        st.metric(
            "Analysis Type",
            "Follow-up"
            if follow_up
            else "New Analysis",
        )

    with col3:

        visualization_count = (
            len(
                spec.get(
                    "visuals",
                    [],
                )
            )
            if spec
            else 0
        )

        st.metric(
            "Visualizations",
            visualization_count,
        )

    # ========================================================
    # REPORT
    # ========================================================

    if report:

        with st.expander(
            "AI Business Report",
            expanded=True,
        ):

            st.markdown(
                report
            )

    # ========================================================
    # DATA
    # ========================================================

    rows = analysis.get(
        "results",
        [],
    )

    if not rows:

        st.info(
            "No visualization data available "
            "for this analysis."
        )

        st.divider()

        return

    dataframe = pd.DataFrame(
        rows
    )

    # ========================================================
    # VISUALIZATION SPEC
    # ========================================================

    if not spec:

        st.warning(
            "Visualization specification is missing "
            "for this analysis."
        )

        st.divider()

        return

    visuals = spec.get(
        "visuals",
        [],
    )

    if not visuals:

        st.info(
            "No suitable visualization was identified "
            "for this analysis."
        )

        st.divider()

        return

    # ========================================================
    # VISUALS
    # ========================================================

    st.markdown(
        "### Visualizations"
    )

    column_count = min(
        len(visuals),
        2,
    )

    columns = st.columns(
        column_count
    )

    for visual_index, visual in enumerate(
        visuals
    ):

        container = columns[
            visual_index % column_count
        ]

        with container:

            render_visual(
                dataframe=dataframe,
                visual=visual,
                analysis_id=str(analysis_id),
                visual_index=visual_index,
            )

    # ========================================================
    # PDF
    # ========================================================

    pdf_path = (
        analysis_dir
        / "ai_business_report_final.pdf"
    )

    if pdf_path.exists():

        with open(
            pdf_path,
            "rb",
        ) as pdf_file:

            st.download_button(
                label="Download Analysis PDF",
                data=pdf_file.read(),
                file_name=(
                    f"{analysis_id}_report.pdf"
                ),
                mime="application/pdf",
                key=(
                    f"{analysis_id}_pdf"
                ),
            )

    st.divider()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    'AI BI Dashboard'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Interactive visualizations and analysis history '
    'for the selected Web Chat conversation.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# CONVERSATION INFO
# ============================================================

title = conversation.get(
    "title",
    "BI Analysis",
)

st.markdown(
    f"""
    <div class="conversation-box">
        <strong>Conversation:</strong>
        {html.escape(str(title))}
        <br>
        <small>
            Conversation ID:
            {html.escape(str(conversation_id))}
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SUMMARY
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Analyses",
        len(analyses),
    )

with col2:

    st.metric(
        "Status",
        "Active",
    )

with col3:

    st.metric(
        "Data Source",
        "Sanitized BI Data",
    )


# ============================================================
# ANALYSIS HISTORY
# ============================================================

st.markdown(
    "## Analysis History"
)


if not analyses:

    st.info(
        "No completed analyses are available "
        "for this conversation."
    )

else:

    for index, analysis_meta in enumerate(
        analyses,
        start=1,
    ):

        render_analysis(
            analysis_meta=analysis_meta,
            index=index,
        )