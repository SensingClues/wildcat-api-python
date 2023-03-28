"""Fixtures for testing of wildcat-api-python"""

import pytest
from pytest_socket import disable_socket


def pytest_runtest_setup():
    """Block any outgoing requests to external APIs"""
    disable_socket()


@pytest.fixture(scope="class")
def example_list_of_dicts(request):
    example = [
        {'a': 1, 'bare': 2},
        {'minimum': 3},
        {4: 'of', 5: 'six', 6: 'bears'}
    ]
    request.cls.example = example
