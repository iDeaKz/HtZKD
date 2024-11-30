import pytest
import pandas as pd
from app.data import DataProcessor


@pytest.fixture
def data_processor():
    return DataProcessor()


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'patient_id': [1, 2, 3],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'healing_progress': [75.0, 60.5, 90.3]
    })


def test_clean_data(data_processor):
    raw_data = {
        'patient_id': [1, 2, None, 4],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
        'healing_progress': [75.0, None, 90.3, 85.5]
    }
    df = pd.DataFrame(raw_data)
    cleaned_df = data_processor.clean_data(df)

    expected_data = {
        'patient_id': [1, 4],
        'date': ['2023-01-01', '2023-01-04'],
        'healing_progress': [75.0, 85.5]
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df['date'] = pd.to_datetime(expected_df['date']).dt.date

    pd.testing.assert_frame_equal(cleaned_df.reset_index(drop=True), expected_df)


def test_transform_data(data_processor, sample_data):
    transformed_df = data_processor.transform_data(sample_data)
    expected_data = {
        'patient_id': [1, 2, 3],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'healing_progress': [75.0, 60.5, 90.3],
        'cumulative_healing': [75.0, 135.5, 225.8]
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df['date'] = pd.to_datetime(expected_df['date']).dt.date
    transformed_df['date'] = pd.to_datetime(transformed_df['date']).dt.date

    pd.testing.assert_frame_equal(transformed_df.reset_index(drop=True), expected_df)
