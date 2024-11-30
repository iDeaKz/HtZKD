# app/components/sliders.py

from dash import dcc


def date_slider():
    return dcc.RangeSlider(
        id='date-slider',
        min=0,
        max=10,
        step=1,
        marks={i: f'Day {i}' for i in range(11)},
        value=[2, 8]
    )
