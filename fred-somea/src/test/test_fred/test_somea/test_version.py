from fred.somea.version import version


def test_version():
    assert isinstance(version.value, str)
