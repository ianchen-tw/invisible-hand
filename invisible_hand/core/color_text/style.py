from colorama import Fore, Back, Style


class WarnStyle:
    @classmethod
    def txt(cls) -> str:
        return f'{Back.RED}{Fore.BLACK}'

    @classmethod
    def kw(cls) -> str:
        return f'{Back.RED}{Fore.WHITE}{Style.BRIGHT}'

    @classmethod
    def kw2(cls) -> str:
        return f'{Back.RED}{Fore.YELLOW}{Style.BRIGHT}'


class NormalStyle:
    @classmethod
    def txt(cls) -> str:
        return f'{Back.GREEN}{Fore.BLACK}'

    @classmethod
    def kw(cls) -> str:
        return f'{Back.GREEN}{Fore.WHITE}{Style.BRIGHT}'

    @classmethod
    def kw2(cls) -> str:
        return f'{Back.GREEN}{Fore.RED}{Style.NORMAL}'
