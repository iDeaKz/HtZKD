#!/usr/bin/env python3
# scripts/test_normalization.py

import argparse
import logging
import sys
from typing import List

import pandas as pd
from app.utils.feature_normalizer import normalize_features
from app.utils.logging import setup_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Test and demonstrate feature normalization."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="normalized_dataset.csv",
        help="Path to save the normalized dataset CSV.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
    )
    return parser.parse_args()


def create_sample_dataset() -> pd.DataFrame:
    """
    Creates a sample dataset for normalization testing.

    Returns:
        pd.DataFrame: Sample dataset.
    """
    data = {
        "Feature1": [10, 20, 30, 40, 50],
        "Feature2": [5, 15, 25, 35, 45],
        "Feature3": [100, 200, 300, 400, 500],
        "Feature4": [0, 0, 0, 0, 0],  # Constant feature
        "Feature5": [1, 2, 3, 4, 5],
        "Feature6": [2, 4, 6, 8, 10],
        "Feature7": [1.1, 2.2, 3.3, 4.4, 5.5],
        "Feature8": [-1, -0.5, 0, 0.5, 1],
        "Feature9": [1, 0, 1, 0, 1],
        "Feature10": [50, 60, 70, 80, 90],
    }
    return pd.DataFrame(data)


def main():
    """
    Main function to test feature normalization.
    """
    args = parse_arguments()

    # Set up logger
    logger = setup_logger(
        "test_normalization",
        log_file="test_normalization.log",
        level=logging.getLevelName(args.log_level.upper()),
    )

    logger.info("Starting feature normalization test.")

    # Create sample dataset
    df = create_sample_dataset()
    logger.debug(f"Original dataset:\n{df}")

    # Normalize features
    features_to_normalize: List[str] = list(df.columns)
    try:
        normalized_df = normalize_features(df, features_to_normalize)
        logger.debug(f"Normalized dataset:\n{normalized_df}")
        logger.info("Feature normalization completed successfully.")
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        sys.exit(1)

    # Save normalized dataset to CSV
    try:
        normalized_df.to_csv(args.output, index=False)
        logger.info(f"Normalized dataset saved to '{args.output}'.")
    except Exception as e:
        logger.error(f"Failed to save normalized dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
