# custom_theme = Theme(
#     {"keyword": "bold magenta", "keyword2": "bold red", "safe": "green", "danger": "red"}
# )


def kw(text: str):
    return f"[keyword]{text}[/]"


def kw2(text: str):
    return f"[keyword2]{text}[/]"


def safe(text: str):
    return f"[safe]{text}[/]"


def danger(text: str):
    return f"[danger]{text}[/]"


# def get_console():
#     return Console(theme=custom_theme)
