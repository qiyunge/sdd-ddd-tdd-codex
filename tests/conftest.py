import pytest

from tests.support.database import seed


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "enrollment.db"
    seed(path)
    return path
