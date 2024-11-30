# app/components/dropdowns.py

from dash import dcc
from app.models import Patient
from app import db


def get_patient_options():
    patients = Patient.query.all()
    return [{'label': f'Patient {patient.patient_id}', 'value': patient.patient_id} for patient in patients]
