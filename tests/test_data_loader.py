# tests/test_data_loader.py

import pytest
import os
import pandas as pd
from app.data import DataLoader


@pytest.fixture
def data_loader():
    return DataLoader(data_path='app/data/')


def test_load_csv_success(data_loader, monkeypatch):
    # Mocking the existence of a CSV file
    test_csv = 'test_patient_data.csv'
    test_data = pd.DataFrame({
        'patient_id': [1, 2, 3],
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'healing_progress': [75.0, 60.5, 90.3]
    })
    test_csv_path = os.path.join(data_loader.data_path, test_csv)
    test_data.to_csv(test_csv_path, index=False)

    df = data_loader.load_csv(test_csv)
    pd.testing.assert_frame_equal(df, test_data)

    # Cleanup
    os.remove(test_csv_path)


def test_load_csv_file_not_found(data_loader):
    with pytest.raises(FileNotFoundError):
        data_loader.load_csv('non_existent_file.csv')


def test_load_excel_success(data_loader, monkeypatch):
    # Mocking the existence of an Excel file
    test_excel = 'test_patient_data.xlsx'
    test_data = pd.DataFrame({
        'patient_id': [4, 5, 6],
        'date': ['2023-02-01', '2023-02-02', '2023-02-03'],
        'healing_progress': [80.0, 70.5, 95.3]
    })
    test_excel_path = os.path.join(data_loader.data_path, test_excel)
    test_data.to_excel(test_excel_path, index=False)

    df = data_loader.load_excel(test_excel)
    pd.testing.assert_frame_equal(df, test_data)

    # Cleanup
    os.remove(test_excel_path)


def test_load_json_success(data_loader, monkeypatch):
    # Mocking the existence of a JSON file
    test_json = 'test_patient_data.json'
    test_data = pd.DataFrame({
        'patient_id': [7, 8, 9],
        'date': ['2023-03-01', '2023-03-02', '2023-03-03'],
        'healing_progress': [85.0, 75.5, 100.3]
    })
    test_json_path = os.path.join(data_loader.data_path, test_json)
    test_data.to_json(test_json_path, orient='records')

    df = data_loader.load_json(test_json)
    pd.testing.assert_frame_equal(df, test_data)

    # Cleanup
    os.remove(test_json_path)
