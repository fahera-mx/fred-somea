from fred.cli.interface import AbstractCLI


class CLI(AbstractCLI):

    @property
    def version(self):
        from fred.somea.version import version
        return version.value
