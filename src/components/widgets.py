from typing import Literal, Callable

from kivy.properties import (
    StringProperty,
    ListProperty,
)
from kivy.uix.filechooser import FileChooserIconView
from kivymd.uix.widget import MDWidget
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

from config import config, PageData, Color
from src.schemas import FileItem
from src.utils.string import KivyLabelString as _


class Paginator(MDWidget):
    """
    Невидимый виджет, инкапсулирующий логику работы с именованными страницами приложения.
    """
    current_page_name: str = StringProperty('')
    hierarchy: list[str] = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pages = config.pages
        self.menu = None
        self.height, self.size_hint_y, self.opacity, self.disabled = 0, None, 0, True

    def go_page(
            self,
            key: str | None = None,
            direction: Literal['left', 'right'] | None = None,
    ) -> None:
        """ Переключает текущую страницу по ключу либо в заданном направлении """
        if not any([key, direction]):
            page = self.pages.current
            direction = 'left'
        elif key is None:
            page = self.pages.next() if direction == 'left' else self.pages.previous()
        else:
            page = self.pages.get(key)
            direction = 'down'

        if page.content is None:
            page.load()

        sm: MDScreenManager = self.parent.ids.sm
        sm.switch_to(page.content, direction=direction)
        self.current_page_name = page.verbose

    def go_hierarchy_previous(self) -> None:
        """ Переключает страницу на предыдущую """
        if len(self.hierarchy) == 1:
            return
        if self.hierarchy:
            self.hierarchy.pop()
        if self.hierarchy:
            key = self.hierarchy.pop()
            self.go_page(key=key)

    def add_to_hierarchy(self, key: str) -> None:
        """ Добавляет страницу в историю перемещений для возможности возврата назад """
        self.hierarchy.append(key)
        if len(self.hierarchy) > config.pagination.HIERARCHY_MAX_LENGTH:
            self.hierarchy.pop(0)

    def open_menu(self, item) -> None:
        """ Открывает меню для перехода к странице по ключу """
        self.menu = MDDropdownMenu(
            caller=item,
            items=[
                {
                    'text': page.title,
                    'on_release': self.get_menu_callback(page),
                } for page in self.pages.all
            ],
        )
        self.menu.open()

    def get_menu_callback(self, page: PageData) -> Callable[[], None]:
        """ Возвращает функцию пепрехода на заданную страницу """
        def callback():
            self.go_page(key=page.key)
            self.menu.dismiss()

        return callback


class DirChooser(FileChooserIconView):
    """ Виджет выбора директорий """
    pass


class FlexibleDialog(MDDialog):
    def on_leave(self) -> None:
        return

    def on_press(self, *args) -> None:
        return


class FlexibleLabel(MDLabel):
    pass


class BlockContainer(MDRelativeLayout):
    """ Контейнер для первого виджета, переданного как позиционный аргумент """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content: MDWidget = args[0]


class FileItemWidget(MDBoxLayout):
    """ Виджет файла в списке """

    def __init__(self, *args, filename: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.selector: BlockContainer = args[0]
        self.index_label: BlockContainer = args[1]
        self.title_label: BlockContainer = args[2]
        self.filename = filename

    @classmethod
    def from_file_item(
        cls,
        file: FileItem,
        index_label_num_symbols: int,
        index_label_color: Color,
        checkbox_callback: Callable[[str, str, bool], None],
        input_area_columns: int = 1,
    ) -> 'FileItemWidget':
        """
        Создает виджет для файла
        :param file: данные файла
        :param index_label_num_symbols:
        :param index_label_color: цвет контейнера индекса файла
        :param checkbox_callback: выполнится при переключении чекбокса выбора
        :param input_area_columns: число столбцов, в которые организованы списки файлов на странице
        :return: экземпляр виджета
        """
        selector = BlockContainer(
            MDCheckbox(
                active=file.active,
                pos_hint={'center_y': 0.5},
            ),
            size_hint_x=0.02 * input_area_columns,
        )
        selector.content.bind(active=lambda _, check: checkbox_callback(file.name, file.fmt, check))

        index = BlockContainer(
            FlexibleLabel(
                text=str(file.index) if file.index else ' ',
                pos_hint={'center_y': 0.5, 'center_x': 0.5},
            ),
            size_hint_x=0.02 * input_area_columns,
            md_bg_color=index_label_color.rgba,
        )

        title = BlockContainer(
            FlexibleLabel(
                text=_(file.abs_path.name, escape=False, is_filename=True).shorten().data,
                pos_hint={'center_y': 0.5, 'x': 0.02},
            ),
            size_hint_x=1 - 0.02 * 2 * input_area_columns,
        )

        instance = cls(
            selector,
            index,
            title,
            filename=f'{file.name}.{file.fmt}',
            padding=config.gui.FILE_VIEWER_CHECKBOX_MARGIN_LEFT,
            size_hint_y=None,
            height=40,
        )
        return instance
