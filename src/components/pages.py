import asynckivy
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
)
from kivymd.uix.screen import MDScreen

from src.utils.string import KivyLabelString as _
from src.schemas import FileList, FileItem, FFprobeFileData
from src.services.ffmpeg import FFmpeg
from .mixins import (
    VideoInputMixin,
    SubtitleInputMixin,
    VideoOutputMixin,
    OutputMixin,
)
from config import config


class Page(MDScreen):
    fullscreen = BooleanProperty(False)
    input_area_columns: int = 0
    suspend = asynckivy.sleep(0)

    def add_widget(self, widget, *args, **kwargs):
        if 'content' in self.ids:
            # Контент, объявленный в .kv файлах разных страниц, будет добавляться не в корень Page,
            # а к элементу с ID=content
            return self.ids.content.add_widget(widget, *args, **kwargs)
        return super().add_widget(widget, *args, **kwargs)

    def get_input_files_info(self, input_files: FileList) -> None:
        ffmpeg = FFmpeg()
        asynckivy.start(ffmpeg.info(
            input_files.active,
            on_success=self.log_input_files_info,
            on_error=self.logerr_input_files_info,
        ))

    async def log_input_files_info(self, f: FileItem, output: FFprobeFileData) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.BLACK.hex)}\n')
        self.ids.log.text += output.describe_as_text()
        self.ids.log.text += '\n\n'

    async def logerr_input_files_info(self, f: FileItem, output: FFprobeFileData) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.DANGER.hex)}\n'
                              f'Ошибка\n\n')
        print(output)


class MainPage(Page):
    pass


class VideoConversionPage(VideoInputMixin, VideoOutputMixin, Page):
    input_area_columns: int = 1


class SubtitleExtractionPage(VideoInputMixin, OutputMixin, Page):
    input_area_columns: int = 1

    def do_extract(self) -> None:
        ffmpeg = FFmpeg(output=self.output_dir)
        asynckivy.start(ffmpeg.extract_subtitles(
            self.video_input_files.active,
            on_success=self.log_extract,
            on_error=self.logerr_extract,
        ))

    async def log_extract(self, f: FileItem, result: str) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.BLACK.hex)} '
                              f'{_(result).color(config.gui.colors.SUCCESS.hex).bold()}\n')

    async def logerr_extract(self, f: FileItem, result: str) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.BLACK.hex)} '
                              f'{_(result).color(config.gui.colors.DANGER.hex).bold()}\n')


class SubtitleAddingPage(VideoInputMixin, SubtitleInputMixin, OutputMixin, Page):
    input_area_columns: int = 2
    subtitle_shift_seconds: float = NumericProperty(0)

    def do_add(self) -> None:
        ffmpeg = FFmpeg(output=self.output_dir)
        try:
            shift = float(self.subtitle_shift_seconds)
        except ValueError:
            shift = 0
        asynckivy.start(ffmpeg.add_subtitles(
            videos=self.video_input_files.active,
            subtitles=self.subtitle_input_files.active,
            subtitle_shift=shift,
            on_success=self.log_add_subtitles,
            on_error=self.logerr_add_subtitles,
        ))

    async def log_add_subtitles(self, f: FileItem, result: str) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.BLACK.hex)} '
                              f'{_(result).color(config.gui.colors.SUCCESS.hex).bold()}\n')

    async def logerr_add_subtitles(self, f: FileItem, result: str) -> None:
        await asynckivy.sleep(0)
        self.ids.log.text += (f'{f.index:02}. '
                              f'{_(f.fullname, is_filename=True).bold().color(config.gui.colors.BLACK.hex)} '
                              f'{_(result).color(config.gui.colors.DANGER.hex).bold()}\n')

    def on_subtitle_shift_seconds(self, instance, value: str) -> None:
        try:
            self.subtitle_shift_seconds = float(value)
            self.ids.subtitle_shift.error = False
            self.ids.subtitle_shift_note.text = 'Сдвинуть субтитры'
        except ValueError:
            self.ids.subtitle_shift.error = True
            self.ids.subtitle_shift_note.text = 'Будет интерпретировано как 0'


class AudiotrackAddingPage(Page):
    input_area_columns: int = 2
