import os


def pytest_deselected(items):
    if not items:
        return
    config = items[0].session.config
    config.deselected = items


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    reports = terminalreporter.getreports("")
    content = os.linesep.join(
        text for report in reports for secname, text in report.sections
    )
    deselected = getattr(config, "deselected", [])
    if deselected:
        terminalreporter.ensure_newline()
        terminalreporter.section("Deselected tests", sep="-", yellow=True, bold=True)
        content = os.linesep.join(item.nodeid for item in deselected)
        terminalreporter.line(content)
