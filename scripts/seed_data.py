# scripts/seed_data.py

import pandas as pd
from app import create_app
from app.models import db, Patient
from app.data.data_loader import DataLoader
from app.data.data_processor import DataProcessor


def seed_data():
    loader = DataLoader()
    processor = DataProcessor()

    # Load patient data from CSV
    df = loader.load_csv('app/data/patient_data.csv')
    df = processor.clean_data(df)

    # Insert data into the database
    for _, row in df.iterrows():
        patient = Patient(
            patient_id=row['patient_id'],
            date=pd.to_datetime(row['date']).date(),
            healing_progress=row['healing_progress']
        )
        db.session.add(patient)

    db.session.commit()
    print("Data seeding completed.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_data()
