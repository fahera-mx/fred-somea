import os

from fred.version import Version


version = Version.from_path(
    name="fred.somea",
    dirpath=os.path.dirname(__file__)
)
