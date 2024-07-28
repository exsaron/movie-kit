from enum import Enum
from typing import NamedTuple

from pydantic import BaseModel

from src.utils.filesystem import format_file_size, format_duration
from src.utils.string import KivyLabelString as _


class Pair(NamedTuple):
    label: str
    value: str | _


class StreamType(str, Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    SUBTITLE = 'subtitle'
    ATTACHMENT = 'attachment'


class FFprobeFileStreamTags(BaseModel):
    language: str | None = None
    title: str | None = None
    BPS: str | None = None
    DURATION: str | None = None
    NUMBER_OF_FRAMES: str | None = None
    NUMBER_OF_BYTES: str | None = None
    filename: str | None = None
    mimetype: str | None = None

    @property
    def name(self) -> str:
        lang = self.language
        if self.title:
            lang = f'{lang}--{self.title}'

        return lang


class FFprobeFileStream(BaseModel):
    index: int
    codec_name: str
    codec_long_name: str | None = None
    profile: str | None = None
    codec_type: str
    codec_tag_string: str | None = None
    codec_tag: str | None = None
    width: int | None = None
    height: int | None = None
    coded_width: int | None = None
    coded_height: int | None = None
    closed_captions: int | None = None
    film_grain: int | None = None
    has_b_frames: int | None = None
    sample_aspect_ratio: str | None = None
    display_aspect_ratio: str | None = None
    pix_fmt: str | None = None
    level: int | None = None
    color_range: str | None = None
    chroma_location: str | None = None
    refs: int | None = None
    r_frame_rate: str | None = None
    avg_frame_rate: str | None = None
    time_base: str | None = None
    start_pts: int | None = None
    start_time: str | None = None
    extradata_size: int | None = None
    tags: FFprobeFileStreamTags = FFprobeFileStreamTags()


class FFprobeFileFormatTags(BaseModel):
    encoder: str | None = None
    creation_time: str | None = None


class FFprobeFileFormat(BaseModel):
    filename: str | None = None
    nb_streams: int | None = None
    nb_programs: int | None = None
    nb_stream_groups: int | None = None
    format_name: str | None = None
    format_long_name: str | None = None
    start_time: str | None = None
    duration: str | None = None
    size: str | None = None
    bit_rate: str | None = None
    probe_score: int | None = None
    tags: FFprobeFileFormatTags = FFprobeFileFormatTags()


class FFprobeFileData(BaseModel):
    """ Содержит данные о файле, получаемые от ``ffprobe``, и методы для их обработки """
    streams: list[FFprobeFileStream] = []
    format: FFprobeFileFormat = FFprobeFileFormat()

    def get_streams_of_type(self, stream_type: StreamType) -> list[FFprobeFileStream]:
        """ Возвращает данные о потоках заданного типа """
        return [s for s in self.streams if s.codec_type == stream_type]

    def describe_stream(self, stream_type: StreamType) -> str:
        """ Возвращает перечисление через запятую информации о потоках заданного типа """
        streams = self.get_streams_of_type(stream_type)
        stream_info_parts = []
        for s in streams:
            language = ''
            if stream_type in (
                StreamType.VIDEO,
                StreamType.AUDIO,
                StreamType.SUBTITLE,
            ):
                language = s.tags.name

            stream_info_parts.append(f'{language} ({s.codec_name})')

        return ', '.join(stream_info_parts) or '---'

    def describe(self) -> list[Pair]:
        """ Возвращает описание медиафайла в виде списка пар ``label:data`` """
        file_type = self.format.format_long_name or 'Неизвестно'
        size = format_file_size(self.format.size)
        duration = format_duration(self.format.duration)
        subtitle_data = self.describe_stream(StreamType.SUBTITLE)
        audiotrack_data = self.describe_stream(StreamType.AUDIO)
        return [
            Pair('Тип', _(file_type).italic().bold()),
            Pair('Размер', _(size).italic().bold()),
            Pair('Продолжительность', _(duration).italic().bold()),
            Pair('Субтитры', _(subtitle_data).italic().bold()),
            Pair('Аудиодорожки', _(audiotrack_data).italic().bold()),
        ]

    def describe_as_text(self) -> str:
        """ Возвращает строковое описание медиафайла """
        return '\n'.join([f'{pair.label}: {pair.value}' for pair in self.describe()])

    def max_stream_index(self, stream_type: StreamType) -> int:
        """
        Возвращает индекс последнего потока заданного типа
        либо ``-1``, если таких потоков нет
        """
        last_stream = max(self.get_streams_of_type(stream_type), key=lambda x: x.index)
        if not last_stream:
            return -1

        return last_stream.index
