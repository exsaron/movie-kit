from typing import Callable

import asynckivy
from kivy.properties import (
    StringProperty,
    ListProperty,
    ObjectProperty,
    DictProperty,
)
from kivymd.uix.widget import MDWidget
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.divider import MDDivider

from config import config, Defaults
from .widgets import FileItemWidget
from src.schemas import FileList
from src.utils.string import maxlen, KivyLabelString as _


class BasePageMixin:
    """
    Объявляет атрибуты, которые должны быть у классов,
    с которыми смешивается миксин
    """
    ids: DictProperty
    name: StringProperty
    on_kv_post: Callable[[MDWidget], None]
    input_area_columns: int


class OutputMixin(BasePageMixin):
    output_dir_text = StringProperty(config.titles.OUTPUT_DIR)
    output_dir = StringProperty('')
    _output_dir_pre = StringProperty('')
    output_dir_chooser = ObjectProperty()

    def on_output_dir(self, instance, value: str) -> None:
        self.output_dir_text = _(f'{config.titles.OUTPUT_DIR}: {value}').shorten().data
        config.pages.get(self.name).settings.update('OUTPUT_DIR', value)

    def preset_output_dir(self, path: str) -> None:
        self._output_dir_pre = path

    def set_output_dir(self) -> None:
        self.output_dir = self._output_dir_pre

    def on_kv_post(self, base_widget: MDWidget) -> None:
        super().on_kv_post(base_widget)
        page = config.pages.get(self.name)
        self.output_dir = str(page.settings.OUTPUT_DIR)
        self._output_dir_pre = self.output_dir


class VideoInputMixin(BasePageMixin):
    video_file_viewer_title = StringProperty('Видео')

    video_input_dir_text = StringProperty(config.titles.INPUT_DIR)
    video_input_dir = StringProperty('')
    _video_input_dir_pre = StringProperty('')
    video_input_dir_chooser = ObjectProperty()

    video_input_files: FileList = ObjectProperty()

    video_input_formats_text = StringProperty(config.titles.INPUT_FORMATS)
    video_input_formats = ListProperty([])
    video_input_formats_chooser = ObjectProperty()

    def on_kv_post(self, base_widget: MDWidget) -> None:
        super().on_kv_post(base_widget)
        page = config.pages.get(self.name)
        self.video_input_formats = page.settings.VIDEO_INPUT_FORMATS
        self.video_input_dir = str(page.settings.VIDEO_INPUT_DIR)
        self._video_input_dir_pre = self.video_input_dir
        asynckivy.start(self.populate_video_formats_selection())

    @property
    def video_input_files_widgets(self) -> list[FileItemWidget]:
        return [w for w in self.ids.video_input_files.children if isinstance(w, FileItemWidget)][::-1]

    def get_video_file_widget(self, filename: str) -> FileItemWidget:
        for fw in self.video_input_files_widgets:
            if fw.filename == filename:
                return fw

        raise ValueError(f'File {filename} not found')

    def set_video_input_formats(self, active: bool, fmt: str):
        if active:
            self.video_input_formats.append(fmt)
        else:
            self.video_input_formats.remove(fmt)

    def preset_video_input_dir(self, path: str):
        self._video_input_dir_pre = path

    def set_video_input_dir(self):
        self.video_input_dir = self._video_input_dir_pre

    async def populate_video_formats_selection(self):
        for fmt in config.formats.VIDEO:
            await asynckivy.sleep(0)
            chip = MDChip(
                MDChipText(text=f'.{fmt}'),
                type='filter',
                theme_bg_color='Custom',
                md_bg_color=config.gui.colors.WHITE.rgba,
                selected_color=config.gui.colors.SUCCESS_LIGHT.rgba,
                active=fmt in self.video_input_formats,
                pos_hint={'x': 0.5, 'y': 0.5},
            )
            chip.bind(active=lambda x, y, z=fmt: self.set_video_input_formats(y, z))
            self.ids.video_formats_selection.add_widget(chip)

    def video_file_set_active(self, name: str, fmt: str, active: bool):
        self.video_input_files.get(name, fmt).active = active

        self.video_input_files.resolve_indexes()
        for f, fw in zip(
            self.video_input_files.all,
            self.video_input_files_widgets,
        ):
            fw.index_label.content.text = str(f.index) if f.index is not None else ''
            # TODO: здесь же менять цвета

    def video_file_selectors_check_all(self, check: bool):
        async def check_all():
            for fw in self.video_input_files_widgets:
                await asynckivy.sleep(0)
                fw.selector.content.active = check

        asynckivy.start(check_all())

    async def populate_video_input_files(self):
        self.ids.video_input_files.clear_widgets()
        self.video_input_files = FileList.from_path(self.video_input_dir, formats=self.video_input_formats)
        index_label_num_symbols = maxlen(self.video_input_files.all, key=lambda x: x.index)
        for idx, file in enumerate(self.video_input_files.all):
            await asynckivy.sleep(0)
            fw = FileItemWidget.from_file_item(
                file,
                index_label_num_symbols=index_label_num_symbols,
                index_label_color=config.gui.colors.SUCCESS_LIGHT,
                checkbox_callback=self.video_file_set_active,
                input_area_columns=self.input_area_columns,
            )
            self.ids.video_input_files.add_widget(fw)
            if idx < len(self.video_input_files.all) - 1:
                self.ids.video_input_files.add_widget(MDDivider())

    def on_video_input_dir(self, instance, value: str):
        self.video_input_dir_text = _(f'{config.titles.INPUT_DIR}: {value}').shorten().data
        asynckivy.start(self.populate_video_input_files())
        config.pages.get(self.name).settings.update('VIDEO_INPUT_DIR', value)

    def on_video_input_formats(self, instance, value: list[str]):
        self.video_input_formats_text = _(f'{config.titles.INPUT_FORMATS}: {', '.join(value)}').shorten().data
        config.pages.get(self.name).settings.update('VIDEO_INPUT_FORMATS', value)


class SubtitleInputMixin(BasePageMixin):
    subtitle_file_viewer_title = StringProperty('Субтитры')

    subtitle_input_dir_text = StringProperty(config.titles.INPUT_DIR)
    subtitle_input_dir = StringProperty('')
    _subtitle_input_dir_pre = StringProperty('')
    subtitle_input_dir_chooser = ObjectProperty()

    subtitle_input_files: FileList = ObjectProperty()

    subtitle_input_formats_text = StringProperty(config.titles.INPUT_FORMATS)
    subtitle_input_formats = ListProperty([])
    subtitle_input_formats_chooser = ObjectProperty()

    def on_kv_post(self, base_widget: MDWidget) -> None:
        super().on_kv_post(base_widget)
        page = config.pages.get(self.name)
        self.subtitle_input_formats = page.settings.SUBTITLE_INPUT_FORMATS
        self.subtitle_input_dir = str(page.settings.SUBTITLE_INPUT_DIR)
        self._subtitle_input_dir_pre = self.subtitle_input_dir
        asynckivy.start(self.populate_subtitle_formats_selection())

    @property
    def subtitle_input_files_widgets(self) -> list[FileItemWidget]:
        return [w for w in self.ids.subtitle_input_files.children if isinstance(w, FileItemWidget)][::-1]

    def get_subtitle_file_widget(self, filename: str) -> FileItemWidget:
        for fw in self.subtitle_input_files_widgets:
            if fw.filename == filename:
                return fw

        raise ValueError(f'File {filename} not found')

    def set_subtitle_input_formats(self, active: bool, fmt: str):
        if active:
            self.subtitle_input_formats.append(fmt)
        else:
            self.subtitle_input_formats.remove(fmt)

    def preset_subtitle_input_dir(self, path: str):
        self._subtitle_input_dir_pre = path

    def set_subtitle_input_dir(self):
        self.subtitle_input_dir = self._subtitle_input_dir_pre

    async def populate_subtitle_formats_selection(self):
        for fmt in config.formats.SUBTITLE:
            await asynckivy.sleep(0)
            chip = MDChip(
                MDChipText(text=f'.{fmt}'),
                type='filter',
                theme_bg_color='Custom',
                md_bg_color=config.gui.colors.WHITE.rgba,
                selected_color=config.gui.colors.SUCCESS_LIGHT.rgba,
                active=fmt in self.subtitle_input_formats,
                pos_hint={'x': 0.5, 'y': 0.5},
            )
            chip.bind(active=lambda x, y, z=fmt: self.set_subtitle_input_formats(y, z))
            self.ids.subtitle_formats_selection.add_widget(chip)

    def subtitle_file_set_active(self, name: str, fmt: str, active: bool):
        self.subtitle_input_files.get(name, fmt).active = active

        self.subtitle_input_files.resolve_indexes()
        for f, fw in zip(
            self.subtitle_input_files.all,
            self.subtitle_input_files_widgets,
        ):
            fw.index_label.content.text = str(f.index) if f.index is not None else ''
            # TODO: здесь же менять цвета

    def subtitle_file_selectors_check_all(self, check: bool):
        async def check_all():
            for fw in self.subtitle_input_files_widgets:
                await asynckivy.sleep(0)
                fw.selector.content.active = check

        asynckivy.start(check_all())

    async def populate_subtitle_input_files(self):
        self.ids.subtitle_input_files.clear_widgets()
        self.subtitle_input_files = FileList.from_path(self.subtitle_input_dir, formats=self.subtitle_input_formats)
        index_label_num_symbols = maxlen(self.subtitle_input_files.all, key=lambda x: x.index)
        for idx, file in enumerate(self.subtitle_input_files.all):
            await asynckivy.sleep(0)
            fw = FileItemWidget.from_file_item(
                file,
                index_label_num_symbols=index_label_num_symbols,
                index_label_color=config.gui.colors.SUCCESS_LIGHT,
                checkbox_callback=self.subtitle_file_set_active,
                input_area_columns=self.input_area_columns,
            )
            self.ids.subtitle_input_files.add_widget(fw)
            if idx < len(self.subtitle_input_files.all) - 1:
                self.ids.subtitle_input_files.add_widget(MDDivider())

    def on_subtitle_input_dir(self, instance, value: str):
        self.subtitle_input_dir_text = _(f'{config.titles.INPUT_DIR}: {value}').shorten().data
        asynckivy.start(self.populate_subtitle_input_files())
        config.pages.get(self.name).settings.update('SUBTITLE_INPUT_DIR', value)

    def on_subtitle_input_formats(self, instance, value: list[str]):
        self.subtitle_input_formats_text = _(f'{config.titles.INPUT_FORMATS}: {', '.join(value)}').shorten().data
        config.pages.get(self.name).settings.update('SUBTITLE_INPUT_FORMATS', value)


class VideoOutputMixin(OutputMixin):
    video_output_format_text = StringProperty(config.titles.OUTPUT_FORMAT)
    video_output_format = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_output_format_menu: MDDropdownMenu | None = None

    def on_kv_post(self, base_widget: MDWidget) -> None:
        super().on_kv_post(base_widget)
        page = config.pages.get(self.name)
        self.video_output_format = page.settings.VIDEO_OUTPUT_FORMAT

    def on_video_output_format(self, instance, value: str):
        self.video_output_format_text = _(f'{config.titles.OUTPUT_FORMAT}: {value}').shorten().data
        config.pages.get(self.name).settings.update('VIDEO_OUTPUT_FORMAT', value)

    def video_output_format_menu_open(self, item):
        def onchange(fmt: str):
            def callback():
                self.video_output_format = fmt
                self.video_output_format_menu.dismiss()

            return callback

        self.video_output_format_menu = MDDropdownMenu(
            caller=item,
            items=[
                {
                    'text': fmt,
                    'on_release': onchange(fmt),
                } for fmt in Defaults.video_supported_formats
            ],
        )
        self.video_output_format_menu.open()

    def set_video_output_format(self, fmt: str):
        self.video_output_format = fmt
        self.video_output_format_menu.dismiss()
