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

    assert 'show' not in about_modal.get_attribute('class')

    about_button.click()
    dash_duo.wait_for_element('#about-modal.show')
    assert 'show' in about_modal.get_attribute('class')

    close_button.click()
    dash_duo.wait_for_element('#about-modal:not(.show)', timeout=2)
    assert 'show' not in about_modal.get_attribute('class')
