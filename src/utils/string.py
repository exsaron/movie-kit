import re
from typing import Callable
from collections import UserString

from kivy.utils import escape_markup


class KivyLabelString(UserString):
    """
    Имитация изменяемой строки с методами для форматирования под Kivy.
    Поддерживает цепочки методов (method chaining).

    Не является подклассом ``str``. Использовать следует в f-строке, как ``str(kls)`` либо ``kls.data``
    """
    def __init__(
            self,
            string: str | UserString,
            escape: bool = True,
            is_filename: bool = False,
    ) -> None:
        """
        :param string: оборачиваемая строка
        :param escape: ``True`` -> экранировать спецсимволы Kivy перед инициализацией
        :param is_filename: установить ``True``, если ``string`` - имя файла в формате ``%name%.%format%``
        """
        string = escape_markup(string) if escape else string
        super().__init__(string)
        self.__is_filename = is_filename

    def __setitem__(self, index, value):
        data_as_list = list(self.data)
        data_as_list[index] = value
        self.data = ''.join(data_as_list)

    def bold(self) -> 'KivyLabelString':
        self.data = f'[b]{self.data}[/b]'
        return self

    def italic(self) -> 'KivyLabelString':
        self.data = f'[i]{self.data}[/i]'
        return self

    def underline(self) -> 'KivyLabelString':
        self.data = f'[u]{self.data}[/u]'
        return self

    def strikethrough(self) -> 'KivyLabelString':
        self.data = f'[s]{self.data}[/s]'
        return self

    def color(self, hexcolor: str) -> 'KivyLabelString':
        """
        :param hexcolor: устанавливаемый цвет в формате ``#000000``
        """
        if not re.match(r'^#[0-9a-f]{6}$', hexcolor):
            raise ValueError(f'Некорректный hexcolor: {hexcolor}')
        self.data = f'[color={hexcolor}]{self.data}[/color]'
        return self

    def shorten(self, max_length: int = 60) -> 'KivyLabelString':
        """ Сократить строку до ``max_length`` символов """
        if self.__is_filename:
            *stem_parts, fmt = self.data.split('.')
            postfix = f' ... .{fmt}'
            offset = 5
            to_shorten = '.'.join(stem_parts)
        else:
            postfix = '...'
            offset = 3
            to_shorten = self.data

        if len(to_shorten) > max_length - offset:
            self.data = f'{to_shorten[:max_length - offset]}{postfix}'

        return self

    def upper(self) -> 'KivyLabelString':
        self.data = self.data.upper()
        return self


def maxlen(items: list, key: Callable = lambda x: x) -> int:
    if not items:
        return 0

    return max(len(str(key(i))) for i in items)
