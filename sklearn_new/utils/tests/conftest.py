import pytest

import sklearn_new


@pytest.fixture
def print_changed_only_false():
    sklearn_new.set_config(print_changed_only=False)
    yield
    sklearn_new.set_config(print_changed_only=True)  # reset to default
