# tests/test_callbacks.py

import pytest
from dash.testing.application_runners import import_app


@pytest.fixture
def dash_app():
    app = import_app('app')
    return app


def test_layout(dash_duo, dash_app):
    dash_duo.start_server(dash_app)
    dash_duo.wait_for_text_to_equal('H(t) Zkaedi Healing Solution Dashboard', 'h1')
    assert dash_duo.find_element('#patient-dropdown')
    assert dash_duo.find_element('#date-picker')
    assert dash_duo.find_element('#about-button')
    assert dash_duo.find_element('#healing-progress-graph')
    assert dash_duo.find_element('#geographical-map')


def test_about_modal_toggle(dash_duo, dash_app):
    dash_duo.start_server(dash_app)
    
    about_button = dash_duo.find_element('#about-button')
    about_modal = dash_duo.find_element('#about-modal')
    close_button = dash_duo.find_element('#close-about')
    
    # Initially, modal should be closed
    assert not about_modal.get_attribute('class').contains('show')
    
    # Click the about button to open the modal
    about_button.click()
    dash_duo.wait_for_element('#about-modal.show')
    assert about_modal.get_attribute('class').contains('show')
    
    # Click the close button to close the modal
    close_button.click()
    dash_duo.wait_for_element('#about-modal', timeout=1, log_level='warn')
    assert not about_modal.get_attribute('class').contains('show')
