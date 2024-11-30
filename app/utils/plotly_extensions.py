# app/utils/plotly_extensions.py

import plotly.express as px


def customize_figure(fig):
    """
    Applies custom styling to Plotly figures for a consistent look and feel.
    """
    fig.update_layout(
        title_font_size=24,
        legend_title_font_size=18,
        legend_font_size=14,
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="closest",
        template="plotly_dark",
        transition_duration=500
    )
    return fig
