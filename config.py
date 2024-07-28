import re
import yaml
from pathlib import Path
from typing import Any, Type

from pydantic.dataclasses import dataclass
from pydantic import BaseModel, ConfigDict
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.properties import ObservableList, ObservableDict
from kivymd.uix.widget import MDWidget

KIVY_RGBA = tuple[float, float, float, float]


def yamlable(value: Any) -> str | int | float | bool | list | dict:
    """ Конвертирует value в понятный YAML формат """
    match value:
        case Path():
            return str(value)
        case ObservableDict():
            return dict(value)
        case ObservableList():
            return list(value)
        case _:
            return value


class Defaults:
    base_dir = Path(__file__).resolve().parent
    video_supported_formats = ['ts', 'mkv', 'mp4', 'avi', 'webm']
    audio_supported_formats = ['mp3', 'wav', 'mka']
    subtitle_supported_formats = ['ass', 'srt']

    @classmethod
    def input(cls, subdir: str) -> str:
        path = cls.base_dir / 'input' / subdir
        path.mkdir(exist_ok=True, parents=True)
        return str(path)

    @classmethod
    def output(cls) -> str:
        path = cls.base_dir / 'output'
        path.mkdir(exist_ok=True, parents=True)
        return str(path)


yaml_config_default = {
    'page_settings': {
        'videoconversion': {
            'video_input_dir': Defaults.input('video'),
            'video_input_formats': Defaults.video_supported_formats,
            'output_dir': Defaults.output(),
            'video_output_format': '',
        },
        'subtitleextraction': {
            'video_input_dir': Defaults.input('video'),
            'video_input_formats': Defaults.video_supported_formats,
            'output_dir': Defaults.output(),
        },
        'subtitleadding': {
            'video_input_dir': Defaults.input('video'),
            'video_input_formats': Defaults.video_supported_formats,
            'subtitle_input_dir': Defaults.input('subtitle'),
            'subtitle_input_formats': Defaults.subtitle_supported_formats,
            'output_dir': Defaults.output(),
        },
        'audiotrackadding': {
            'video_input_dir': Defaults.input('video'),
            'video_input_formats': Defaults.video_supported_formats,
            'audiotrack_input_dir': Defaults.input('audiotrack'),
            'audiotrack_input_formats': Defaults.audio_supported_formats,
            'output_dir': Defaults.output(),
        },
    },
}


class DataModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


@dataclass
class Color:
    r: int | None = None
    g: int | None = None
    b: int | None = None
    a: float = 1.0
    hex: str | None = None
    color_name: str = ''

    def __post_init__(self):
        if all([
            any([f is None for f in (self.r, self.g, self.b)]),
            self.hex is None,
        ]):
            raise AttributeError('Для инициализации цвета нужно передать либо r, g, b, либо color_hex')

        if self.hex is None:
            self.hex = f'#{self.r:02x}{self.g:02x}{self.b:02x}'
        else:
            if not re.match(r'^#[0-9a-f]{6}$', self.hex):
                raise ValueError(f'Некорректный color_hex: {self.hex}')
            self.r, self.g, self.b = tuple(int(self.hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    @property
    def rgba(self) -> KIVY_RGBA:
        """ Возвращает RGBA-цвет, переведенный в понятный Kivy формат """
        return self.r / 255, self.g / 255, self.b / 255, self.a

    @property
    def name(self) -> str | KIVY_RGBA:
        return self.color_name if self.color_name else self.rgba

    def __repr__(self) -> str:
        return self.color_name if self.color_name else self.hex


class Colors(DataModel):
    WHITE_VEIL: Color
    WHITE: Color
    BLACK: Color
    PRIMARY: Color
    SECONDARY: Color
    TRANSPARENT: Color
    DARK: Color
    DARK_VEIL: Color
    DANGER: Color
    DANGER_LIGHT: Color
    SUCCESS: Color
    SUCCESS_LIGHT: Color


class Formats(DataModel):
    VIDEO: list[str]
    SUBTITLE: list[str]
    AUDIOTRACK: list[str]


class GUI(DataModel):
    BORDER_RADIUS: float
    PAGE_X_RATIO: float
    PAGE_Y_RATIO: float
    BOX_SPACING: float
    LOG_PADDING: float
    FILE_VIEWER_PADDING: float
    FILE_VIEWER_CHECKBOX_MARGIN_LEFT: float
    SCROLL_BAR_WIDTH: float
    colors: Colors

    @property
    def page_size_hint(self) -> tuple[float, float]:
        return self.PAGE_X_RATIO, self.PAGE_Y_RATIO


class Pagination(DataModel):
    HIERARCHY_MAX_LENGTH: int


class Titles(DataModel):
    INPUT_DIR: str
    OUTPUT_DIR: str
    INPUT_FORMATS: str
    OUTPUT_FORMAT: str
    GO: str


class PersistentPageSettings(DataModel):
    """ Настройки страницы, дублируемые в конфиг-файл """

    @staticmethod
    def __get_page_key(cls: Type['PersistentPageSettings']) -> str:
        return cls.__name__.removesuffix('PageSettings').lower()

    def __update_value(self, field: str, value: Any) -> None:
        if not hasattr(self, field):
            raise AttributeError(f'{self.__class__.__name__} не имеет поля {field}')

        setattr(self, field, value)
        base_dir = Path(__file__).resolve().parent
        with open(base_dir / 'config.yaml', 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
        yaml_config['page_settings'][self.__get_page_key(self.__class__)][field.lower()] = yamlable(value)
        with open(base_dir / 'config.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump(yaml_config, f, encoding='utf-8')

    def update(self, field: str, value: Any) -> None:
        """ Обновляет настройку, дублирует изменения в конфиг-файл """
        self.__update_value(field, value)

    def set_default(self, field: str) -> None:
        """ Возвращает настройке значение по умолчанию, дублирует изменения в конфиг-файл """
        self.__update_value(
            field=field,
            value=yaml_config_default['page_settings'][self.__get_page_key(self.__class__)][field.lower()],
        )

    @classmethod
    def from_yaml(cls, loaded_yaml: dict[str]) -> 'PersistentPageSettings':
        """ Загружает настройки из конфиг-файла """
        kwargs = {}
        for key, value in loaded_yaml['page_settings'][cls.__get_page_key(cls)].items():
            kwargs[key.upper()] = value

        return cls(**kwargs)


class VideoConversionPageSettings(PersistentPageSettings):
    VIDEO_INPUT_DIR: Path
    VIDEO_INPUT_FORMATS: list[str]
    OUTPUT_DIR: Path
    VIDEO_OUTPUT_FORMAT: str


class SubtitleExtractionPageSettings(PersistentPageSettings):
    VIDEO_INPUT_DIR: Path
    VIDEO_INPUT_FORMATS: list[str]
    OUTPUT_DIR: Path


class SubtitleAddingPageSettings(PersistentPageSettings):
    VIDEO_INPUT_DIR: Path
    VIDEO_INPUT_FORMATS: list[str]
    SUBTITLE_INPUT_DIR: Path
    SUBTITLE_INPUT_FORMATS: list[str]
    OUTPUT_DIR: Path


class AudiotrackAddingPageSettings(PersistentPageSettings):
    pass


# т.к. IDE ругается на попытку доступа к атрибуту наследника PersistentPageSettings
PPageSettings = (
    VideoConversionPageSettings |
    SubtitleExtractionPageSettings |
    SubtitleAddingPageSettings |
    AudiotrackAddingPageSettings
)


class PageData(DataModel):
    key: str
    title: str
    verbose: str
    settings: PPageSettings | None = None
    icon: str | None = None
    content: MDWidget | None = None

    @property
    def kv_path(self) -> str:
        return str(config.BASE_DIR / 'data' / 'pages' / f'{self.key}.kv'.lower())

    def load(self):
        self.content = Builder.load_file(self.kv_path)


class PageList(DataModel):
    """ Список страниц и методы для управления им """

    all: tuple[PageData, ...]
    current: PageData | None = None

    def model_post_init(self, __context: Any) -> None:
        self.current = self.all[0]

    @property
    def index(self) -> int:
        return self.all.index(self.current)

    @property
    def length(self) -> int:
        return len(self.all)

    def get(self, key: str) -> PageData:
        """
        Возвращает страницу по ключу.
        Если ничего не найдено - пытается найти страницу по заголовку.
        """
        for page in self.all:
            if page.key == key:
                self.current = page
                return page

        for page in self.all:
            if page.title == key:
                self.current = page
                return page

        raise KeyError(f'"{key}" не обнаружен ни в ключах, ни в заголовках.\nPAGES: {self.all}')

    def next(self) -> PageData:
        new_index = self.index + 1 if self.index + 1 < self.length else 0
        self.current = self.all[new_index]
        return self.current

    def previous(self) -> PageData:
        new_index = self.index - 1 if self.index > 0 else self.length - 1
        self.current = self.all[new_index]
        return self.current

    @property
    def titles(self) -> tuple[str, ...]:
        return tuple(page.title for page in self.all)

    def ensure_settings_paths(self) -> list[Path]:
        """
        Проверяет существование указанных в настройках страниц путей.
        Если путь не существует - меняет его на дефолтный
        :return: список путей, замененных на дефолтные
        """
        invalid_paths: list[Path] = []
        for page in self.all:
            settings = page.settings
            if settings is None:
                continue
            for field, value in settings.model_dump().items():
                if isinstance(value, Path):
                    if not value.exists():
                        settings.set_default(field)
                        invalid_paths.append(value)
        return invalid_paths


class FFmpegSettings(DataModel):
    SUBTITLE_LANGUAGES_TO_EXTRACT: list[str]


class Config(DataModel):
    BASE_DIR: Path
    gui: GUI
    pagination: Pagination
    formats: Formats
    titles: Titles
    pages: PageList
    ffmpeg: FFmpegSettings


def get_config() -> Config:
    # Считываем настройки с конфиг-файла
    # Если файла нет - сначала создаем его и заполняем значениями по умолчанию
    try:
        with open(Defaults.base_dir / 'config.yaml', 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
            if not yaml_config:
                raise FileNotFoundError
    except FileNotFoundError:
        yaml_config = yaml_config_default
        with open(Defaults.base_dir / 'config.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump(yaml_config, f, encoding='utf-8')

    c = Config(
        BASE_DIR=Defaults.base_dir,
        gui=GUI(
            BORDER_RADIUS=dp(10),
            PAGE_X_RATIO=0.8,
            PAGE_Y_RATIO=0.99,
            BOX_SPACING=dp(4),
            LOG_PADDING=dp(10),
            FILE_VIEWER_PADDING=dp(1),
            FILE_VIEWER_CHECKBOX_MARGIN_LEFT=dp(4),
            SCROLL_BAR_WIDTH=dp(10),
            colors=Colors(
                WHITE_VEIL=Color(255, 255, 255, 0.3),
                WHITE=Color(255, 255, 255, 1, color_name='white'),
                BLACK=Color(0, 0, 0, 1, color_name='black'),
                PRIMARY=Color(76, 43, 166, 1),
                SECONDARY=Color(76, 43, 166, 1),
                TRANSPARENT=Color(255, 255, 255, 0),
                DARK=Color(42, 42, 42, 1),
                DARK_VEIL=Color(0, 0, 0, 0.7),
                SUCCESS=Color(0, 102, 2, 1),
                DANGER=Color(194, 4, 20, 1),
                SUCCESS_LIGHT=Color(97, 143, 98, 1),
                DANGER_LIGHT=Color(145, 86, 91, 1),
            ),
        ),
        pagination=Pagination(
            HIERARCHY_MAX_LENGTH=20,
        ),
        formats=Formats(
            VIDEO=Defaults.video_supported_formats,
            SUBTITLE=Defaults.subtitle_supported_formats,
            AUDIOTRACK=Defaults.audio_supported_formats,
        ),
        titles=Titles(
            INPUT_DIR='Input dir',
            OUTPUT_DIR='Output dir',
            INPUT_FORMATS='Input formats',
            OUTPUT_FORMAT='Output format',
            GO='Go !!!',
        ),
        pages=PageList(
            all=(
                # PageData(
                #     key='mainpage',
                #     title='Главная',
                #     verbose='Главная страница',
                # ),
                PageData(
                    key='videoconversion',
                    title='Конвертация',
                    verbose='Конвертация видео',
                    settings=VideoConversionPageSettings.from_yaml(yaml_config),
                ),
                PageData(
                    key='subtitleextraction',
                    title='-Субтитры',
                    verbose='Извлечение субтитров',
                    settings=SubtitleExtractionPageSettings.from_yaml(yaml_config),
                ),
                PageData(
                    key='subtitleadding',
                    title='+Субтитры',
                    verbose='Добавление субтитров',
                    settings=SubtitleAddingPageSettings.from_yaml(yaml_config),
                ),
                # PageData(
                #     key='audiotrackadding',
                #     title='+Аудио',
                #     verbose='Добавление аудиодорожки',
                # ),
            ),
        ),
        ffmpeg=FFmpegSettings(
            SUBTITLE_LANGUAGES_TO_EXTRACT=['eng', 'rus'],
        )
    )
    invalid_paths = c.pages.ensure_settings_paths()
    print(f'Следующие пути не существуют и были заменены на дефолтные: {invalid_paths}')
    return c


config: Config = get_config()
