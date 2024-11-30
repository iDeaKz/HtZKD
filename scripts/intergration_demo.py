# scripts/integration_demo.py

import pandas as pd
from app.utils.feature_normalizer import log_and_normalize

def main():
    # Example DataFrame
    data = {
        "Feature1": [10, 20, 30, 40, 50],
        "Feature2": [5, 15, 25, 35, 45],
        "Feature3": [100, 200, 300, 400, 500],
    }
    df = pd.DataFrame(data)

    print("Original DataFrame:")
    print(df)

    # Normalize features
    normalized_df = log_and_normalize(df, ["Feature1", "Feature2", "Feature3"], log_level="DEBUG")
    print("\nNormalized DataFrame:")
    print(normalized_df)

if __name__ == "__main__":
    main()
