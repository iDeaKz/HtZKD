#!/usr/bin/env python3
# scripts/normalize_debugger.py

import logging
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st
from app.utils.feature_normalizer import normalize_features
from app.utils.logging import setup_logger


def setup_streamlit_logger() -> logging.Logger:
    """
    Sets up a logger for the Streamlit app.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = setup_logger("normalize_debugger", log_file="normalize_debugger.log", level=logging.INFO)
    return logger


def load_datasets() -> dict:
    """
    Loads sample datasets for demonstration.

    Returns:
        dict: Dictionary of dataset names to DataFrames.
    """
    return {
        "Dataset 1": pd.DataFrame({
            "Feature1": [10, 20, 30, 40, 50],
            "Feature2": [5, 15, 25, 35, 45],
            "Feature3": [100, 200, 300, 400, 500],
            "Feature4": [0, 0, 0, 0, 0],  # Constant feature
        }),
        "Dataset 2": pd.DataFrame({
            "Feature1": [1, 2, 3, 4, 5],
            "Feature2": [2, 4, 6, 8, 10],
            "Feature3": [-1, 0, 1, 2, 3],
        }),
        "Dataset 3": pd.DataFrame({
            "Feature1": [50, 60, 70, 80, 90],
            "Feature2": [5.5, 6.5, 7.5, 8.5, 9.5],
            "Feature3": [0.1, 0.2, 0.3, 0.4, 0.5],
        }),
    }


def display_normalization_results(original_df: pd.DataFrame, normalized_df: pd.DataFrame, feature: str, logger: logging.Logger):
    """
    Displays the original and normalized feature alongside a Plotly chart.

    Args:
        original_df (pd.DataFrame): Original dataset.
        normalized_df (pd.DataFrame): Normalized dataset.
        feature (str): Feature to visualize.
        logger (logging.Logger): Logger instance.
    """
    try:
        comparison_df = pd.DataFrame({
            "Original": original_df[feature],
            "Normalized": normalized_df[feature],
        })
        fig = px.line(
            comparison_df,
            labels={"value": "Value", "index": "Index"},
            title=f"Feature: {feature}",
            markers=True
        )
        st.plotly_chart(fig)
        logger.info(f"Displayed normalization comparison for feature '{feature}'.")
    except Exception as e:
        st.error(f"Error visualizing feature '{feature}': {e}")
        logger.error(f"Error visualizing feature '{feature}': {e}")


def main():
    """
    Main function to run the Streamlit normalization debugger.
    """
    # Set page configuration
    st.set_page_config(
        page_title="Interactive Normalization Debugger",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Set up logger
    logger = setup_streamlit_logger()
    logger.info("Streamlit normalization debugger started.")

    # Title and description
    st.title("Interactive Normalization Debugger")
    st.write("""
        Use this tool to interactively normalize features of your datasets and visualize the results.
    """)

    # Sidebar for user controls
    st.sidebar.header("Control Panel")

    # Dropdown for dataset selection
    datasets = load_datasets()
    dataset_name = st.sidebar.selectbox("Select Dataset", list(datasets.keys()))
    selected_dataset = datasets[dataset_name]

    # Display the original dataset
    st.subheader("Original Dataset")
    st.dataframe(selected_dataset)

    # Multi-select for features to normalize
    features_to_normalize: List[str] = st.sidebar.multiselect(
        "Select Features to Normalize",
        options=selected_dataset.columns.tolist(),
        default=selected_dataset.columns.tolist()
    )

    # Normalize features when button is clicked
    if st.sidebar.button("Normalize Features"):
        if not features_to_normalize:
            st.warning("Please select at least one feature to normalize.")
            logger.warning("No features selected for normalization.")
        else:
            try:
                normalized_dataset = normalize_features(selected_dataset, features_to_normalize)
                st.subheader("Normalized Dataset")
                st.dataframe(normalized_dataset)
                logger.info(f"Features {features_to_normalize} normalized successfully.")

                # Visualization: Compare Original vs Normalized
                feature_to_visualize = st.selectbox(
                    "Select Feature for Visualization",
                    features_to_normalize,
                    help="Choose a feature to compare original and normalized values."
                )
                display_normalization_results(selected_dataset, normalized_dataset, feature_to_visualize, logger)

            except Exception as e:
                st.error(f"Normalization failed: {e}")
                logger.error(f"Normalization failed: {e}")

    # Footer
    st.sidebar.info("Interactive UI Debugger for Normalizing Features")
    logger.info("Streamlit normalization debugger finished execution.")


if __name__ == "__main__":
    main()
