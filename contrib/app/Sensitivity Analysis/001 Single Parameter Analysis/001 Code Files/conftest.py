import pytest


def pytest_addoption(parser):
    parser.addoption("--directory", action="store", default=None, help="Base directory containing test folders")
    parser.addoption("--dir", action="store", default=None, help="Alias for --directory")


@pytest.fixture
def base_dir(request):
    base_dir = request.config.getoption("--directory")
    alias_dir = request.config.getoption("--dir")
    dir_path = base_dir or alias_dir
    if dir_path is None:
        pytest.skip("Base directory not provided. Use --directory or --dir option.")
    return dir_path
