# app/utils/feature_normalizer.py

import logging
from typing import List

import pandas as pd
from app.utils.logging import setup_logger

# Initialize logger
logger = setup_logger("feature_normalizer", log_file="normalization.log", level=logging.DEBUG)


def normalize_features(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Normalizes selected features in a DataFrame using min-max scaling.

    Args:
        df (pd.DataFrame): Input DataFrame containing features.
        features (List[str]): List of column names to normalize.

    Returns:
        pd.DataFrame: DataFrame with normalized features.
    """
    logger.info("Starting feature normalization...")

    normalized_df = df.copy()
    for feature in features:
        if feature not in df.columns:
            logger.error(f"Feature '{feature}' not found in DataFrame.")
            raise ValueError(f"Feature '{feature}' not found in DataFrame.")

        min_val = df[feature].min()
        max_val = df[feature].max()

        if min_val == max_val:
            logger.warning(f"Feature '{feature}' has constant values. Skipping normalization.")
            normalized_df[feature] = df[feature]
        else:
            normalized_df[feature] = (df[feature] - min_val) / (max_val - min_val)
            logger.debug(f"Normalized '{feature}': min={min_val}, max={max_val}")

    logger.info("Feature normalization completed successfully.")
    return normalized_df


def log_and_normalize(
    df: pd.DataFrame,
    features: List[str],
    log_level: str = "INFO",
    log_file: str = "normalization.log",
) -> pd.DataFrame:
    """
    Normalizes features and sets up logging dynamically.

    Args:
        df (pd.DataFrame): Input DataFrame containing features.
        features (List[str]): List of column names to normalize.
        log_level (str): Logging level (e.g., "INFO", "DEBUG").
        log_file (str): Path to the log file.

    Returns:
        pd.DataFrame: DataFrame with normalized features.
    """
    dynamic_logger = setup_logger(
        "dynamic_feature_normalizer", log_file, getattr(logging, log_level.upper())
    )
    try:
        normalized_data = normalize_features(df, features)
        dynamic_logger.info("Normalization completed successfully.")
        return normalized_data
    except Exception as e:
        dynamic_logger.error(f"Normalization failed: {e}")
        raise
