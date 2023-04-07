"""Tests for data_cleaner-module"""

import pytest
import unittest

from wildcatpy.src import (
    get_list_values,
    flatten_list,
    select_columns,
)


@pytest.mark.data_cleaner
@pytest.mark.usefixtures("example_list_of_dicts")
class TestApi(unittest.TestCase):

    def test_flatten_list(self):
        input_list = [[1, 2, [3], 4, [5, [6, 7, 8]]]]
        expected_output = [1, 2, 3, 4, 5, 6, 7, 8]

        actual_output = flatten_list(input_list)
        self.assertTrue(expected_output, actual_output)

    def test_get_list_values(self):
        expected_output = [[1, 2], [3], ['of', 'six', 'bears']]

        assert get_list_values(self.example) == expected_output

    def test_select_columns(self):
        keep_cols = ['a', 'minimum', 5, 6]
        expected_output = [{'a': 1}, {'minimum': 3}, {5: 'six'}, {6: 'bears'}]
        assert select_columns(self.example, keep_cols) == expected_output
