from .colored import Colored
from .style import NormalStyle, WarnStyle

# @TODO: replace warn/normal using python.rich
warn = Colored(WarnStyle)
normal = Colored(NormalStyle)
