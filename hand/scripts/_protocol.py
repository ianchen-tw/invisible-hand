from typing import Protocol


class Script(Protocol):
    def run(self):
        """ The default run command
        """
