import json
import re
from subprocess import Popen, PIPE
from pathlib import Path
from typing import Awaitable, Protocol

from config import config, Defaults
from src.schemas import FileItem, FFprobeFileData, StreamType


class FFprobeCallback(Protocol):
    def __call__(self, f: FileItem, output: FFprobeFileData) -> Awaitable[None]:
        """
        :param f: данные файла
        :param output: декодированный вывод ffprobe
        """
        ...


class FFmpegCallback(Protocol):
    def __call__(self, f: FileItem, result: str) -> Awaitable[None]:
        """
        :param f: данные файла
        :param result: описание результата работы ffmpeg
        """
        ...


class FFmpeg:
    """
    Применяет ffmpeg ко множеству файлов. Вызывает коллбэки в процессе
    """
    __ffmpeg = str(config.BASE_DIR / 'data' / 'tools' / 'ffmpeg')
    __ffprobe = str(config.BASE_DIR / 'data' / 'tools' / 'ffprobe')

    def __init__(
            self,
            output: str | None = None,
            stdout=PIPE,
            stderr=PIPE,
    ) -> None:
        """
        :param output: каталог, в котором создаются результирующие файлы
        :param stdout: куда перенаправлять ``Popen`` stdout
        :param stderr: куда перенаправлять ``Popen`` stderr
        """
        self.output = output or Defaults.output()
        self.output = Path(self.output)
        self.stdout = stdout
        self.stderr = stderr

    @staticmethod
    def __extract_language_from_subtitle_filename(filename: str) -> str:
        pattern = rf'^.+\((.+?)--(.+?)\)$'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)

        return 'неизвестно'

    async def info(
            self,
            files: list[FileItem],
            on_success: FFprobeCallback | None = None,
            on_error: FFprobeCallback | None = None,
    ) -> dict[int, FFprobeFileData]:
        """
        С помощью ffprobe получает метаданные медиафайлов
        :param files: данные медиафайлов
        :param on_success: корутина, выполняемая при успехе операции с файлом
        :param on_error: корутина, выполняемая при ошибке операции с файлом
        :return: словарь с метаданными
        """
        result = {}
        for f in files:
            command = [
                self.__ffprobe,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(f.abs_path),
            ]
            proc = Popen(
                command,
                stdout=self.stdout,
                stderr=self.stderr,
            )
            out, err = proc.communicate()
            if proc.returncode == 0:
                output = FFprobeFileData(**json.loads(out.decode('utf-8')))
                if on_success is not None:
                    await on_success(f, output=output)
                print(f'{out.decode('utf-8')}\n\n')
                result[f.index] = output
            if proc.returncode != 0 and on_error is not None:
                await on_error(f, output=json.loads(err.decode('utf-8')))
                print(f'ERROR!! {err.decode('utf-8')}')

        return result

    async def convert_video(self, videos: list[FileItem]) -> None:
        # TODO
        pass

    async def extract_subtitles(
            self,
            videos: list[FileItem],
            on_success: FFmpegCallback | None = None,
            on_error: FFmpegCallback | None = None,
    ) -> None:
        """
        С помощью ``ffmpeg`` извлекает субтитры из множества видеофайлов и сохраняет в папку ``self.output``
        :param videos: данные видеофайлов
        :param on_success: корутина, выполняемая при успехе операции с файлом
        :param on_error: корутина, выполняемая при ошибке операции с файлом
        """
        for f in videos:
            f_info = (await self.info([f]))[f.index]
            for subtitle_stream in f_info.get_streams_of_type(StreamType.SUBTITLE):
                if subtitle_stream.tags.language not in config.ffmpeg.SUBTITLE_LANGUAGES_TO_EXTRACT:
                    continue

                if subtitle_stream.codec_name in Defaults.subtitle_supported_formats:
                    output_format = subtitle_stream.codec_name
                else:
                    output_format = Defaults.subtitle_supported_formats[0]

                output_filename = f'{f.name} ({subtitle_stream.tags.name}).{output_format}'
                # TODO: сохранять метаданные из потока субтитров
                command = [
                    self.__ffmpeg,
                    '-y',
                    '-i', str(f.abs_path),
                    '-map', f'0:{subtitle_stream.index}',
                    '-c', 'copy',
                    '-f', 'ass',
                    self.output / output_filename,
                ]
                proc = Popen(
                    command,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
                out, err = proc.communicate()
                proc.wait()
                if proc.returncode == 0 and on_success is not None:
                    await on_success(f, result=f'Создан файл {output_filename}')
                if proc.returncode != 0 and on_error is not None:
                    print(f'ERROR!! {err.decode('utf-8')}')
                    await on_error(f, result=f'Ошибка извлечения субтитров .{output_format}')

    async def add_subtitles(
            self,
            videos: list[FileItem],
            subtitles: list[FileItem],
            subtitle_shift: float = 0,
            on_success: FFmpegCallback | None = None,
            on_error: FFmpegCallback | None = None,
    ) -> None:
        """
        С помощью ``ffmpeg`` сшивает попарно видеофайлы и субтитры. Сохраняет результаты в ``self.output``
        :param videos: данные видеофайлов
        :param subtitles: данные субтитров
        :param subtitle_shift: сдвиг дорожки субтитров (в секундах)
        :param on_success: корутина, выполняемая при успехе операции с файлом
        :param on_error: корутина, выполняемая при ошибке операции с файлом
        """
        for video in videos:
            subtitle = None
            for s in subtitles:
                if s.index == video.index:
                    subtitle = s
            if not subtitle:
                continue

            video_info = (await self.info([video]))[video.index]
            subtitle_info = (await self.info([subtitle]))[subtitle.index]

            subtitle_language = self.__extract_language_from_subtitle_filename(subtitle.name)
            output_filename = f'{video.name} [{subtitle_language.upper()} SUB].{video.fmt}'
            # TODO: сохранить метаданные субтитров
            command = [
                self.__ffmpeg,
                '-y',
                '-i', str(video.abs_path),
                '-itsoffset', str(subtitle_shift),
                '-i', str(subtitle.abs_path),
                '-map', '0:v',
                '-map', '0:a',
                '-map', '1:s',
                '-map', '0:s',
                # '-map', '1:0',        # сохраняить исходные субтитры
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'copy',
                self.output / output_filename,
            ]
            proc = Popen(
                command,
                stdout=self.stdout,
                stderr=self.stderr,
            )
            out, err = proc.communicate()
            proc.wait()
            if proc.returncode == 0 and on_success is not None:
                await on_success(video, result=f'Создан файл {output_filename}')
            if proc.returncode != 0 and on_error is not None:
                print(f'ERROR!! {err.decode('utf-8')}')
                await on_error(video, result=f'Ошибка добавления субтитров')

    def add_audiotracks(self, videos: list[FileItem], audiotracks: list[FileItem]) -> None:
        # TODO
        pass
