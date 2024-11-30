import pytest
import os
import pandas as pd
from app.data import DataLoader


@pytest.fixture
def data_loader():
    return DataLoader(data_path='app/data/')


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'patient_id': [1, 2, 3],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'healing_progress': [75.0, 60.5, 90.3]
    })


def test_load_csv_success(data_loader, sample_data):
    test_csv = 'test_patient_data.csv'
    test_csv_path = os.path.join(data_loader.data_path, test_csv)
    sample_data.to_csv(test_csv_path, index=False)

    df = data_loader.load_csv(test_csv)
    pd.testing.assert_frame_equal(df, sample_data)

    os.remove(test_csv_path)


def test_load_excel_success(data_loader, sample_data):
    test_excel = 'test_patient_data.xlsx'
    test_excel_path = os.path.join(data_loader.data_path, test_excel)
    sample_data.to_excel(test_excel_path, index=False)

    df = data_loader.load_excel(test_excel)
    pd.testing.assert_frame_equal(df, sample_data)

    os.remove(test_excel_path)


def test_load_json_success(data_loader, sample_data):
    test_json = 'test_patient_data.json'
    test_json_path = os.path.join(data_loader.data_path, test_json)
    sample_data.to_json(test_json_path, orient='records')

    df = data_loader.load_json(test_json)
    pd.testing.assert_frame_equal(df, sample_data)

    os.remove(test_json_path)
