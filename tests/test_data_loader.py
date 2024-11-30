import pytest
import os
import pandas as pd
from app.data import DataLoader

@pytest.fixture
def data_loader():
    return DataLoader(data_path='app/data/')

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """
    Automatically clean up test files after each test.
    """
    yield
    for file in ['test_patient_data.csv', 'test_patient_data.xlsx', 'test_patient_data.json']:
        file_path = os.path.join('app/data/', file)
        if os.path.exists(file_path):
            os.remove(file_path)

def test_load_json_success(data_loader):
    """
    Test loading JSON with date parsing.
    """
    test_json = 'test_patient_data.json'
    test_data = pd.DataFrame({
        'patient_id': [7, 8, 9],
        'date': ['2023-03-01', '2023-03-02', '2023-03-03'],
        'healing_progress': [85.0, 75.5, 100.3]
    })
    test_json_path = os.path.join(data_loader.data_path, test_json)
    test_data.to_json(test_json_path, orient='records')

    df = data_loader.load_json(test_json)
    df['date'] = pd.to_datetime(df['date'])  # Convert to datetime
    test_data['date'] = pd.to_datetime(test_data['date'])  # Convert to datetime

    pd.testing.assert_frame_equal(df, test_data)
