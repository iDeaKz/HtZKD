# app/callbacks/update_graphs.py

from dash.dependencies import Input, Output
from app.models import Patient
from app import db
import pandas as pd
import plotly.express as px


def register_callbacks(dash_app):
    @dash_app.callback(
        Output('healing-progress-graph', 'figure'),
        [Input('patient-dropdown', 'value'),
         Input('date-picker', 'start_date'),
         Input('date-picker', 'end_date')]
    )
    def update_healing_progress(selected_patients, start_date, end_date):
        query = db.session.query(Patient)
        
        if selected_patients:
            query = query.filter(Patient.patient_id.in_(selected_patients))
        
        if start_date:
            query = query.filter(Patient.date >= start_date)
        
        if end_date:
            query = query.filter(Patient.date <= end_date)
        
        df = pd.read_sql(query.statement, db.session.bind)
        
        if df.empty:
            fig = px.scatter(title="No data available for the selected criteria.")
            return fig
        
        fig = px.line(
            df,
            x='date',
            y='healing_progress',
            color='patient_id',
            title="Healing Progress Over Time",
            labels={'date': 'Date', 'healing_progress': 'Healing Progress', 'patient_id': 'Patient ID'}
        )
        fig.update_layout(transition_duration=500)
        return fig

    @dash_app.callback(
        Output('geographical-map', 'figure'),
        [Input('patient-dropdown', 'value')]
    )
    def update_geographical_map(selected_patients):
        # Placeholder for geographical data
        # Assuming you have latitude and longitude in the Patient model or related models
        # For demonstration, we'll create dummy data
        data = {
            'patient_id': [1, 2, 3],
            'latitude': [37.7749, 34.0522, 40.7128],
            'longitude': [-122.4194, -118.2437, -74.0060],
            'healing_progress': [75.0, 60.5, 90.3]
        }
        df = pd.DataFrame(data)

        if selected_patients:
            df = df[df['patient_id'].isin(selected_patients)]
        
        if df.empty:
            fig = px.scatter_mapbox(
                title="No data available for the selected criteria.",
                mapbox_style="carto-positron"
            )
            return fig

        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            size='healing_progress',
            color='healing_progress',
            hover_name='patient_id',
            size_max=15,
            zoom=3,
            mapbox_style="carto-positron",
            title="Geographical Distribution of Patients"
        )
        fig.update_layout(transition_duration=500)
        return fig
