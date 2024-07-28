from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileItem:
    """ Основная информация о файле """
    abs_path: Path
    index: int | None = None
    active: bool = True
    name: str | None = None
    fmt: str | None = None

    def __post_init__(self):
        self.name = self.abs_path.stem
        self.fmt = self.abs_path.suffix.removeprefix('.')

    @property
    def fullname(self) -> str:
        """ ``%name%.%format%`` """
        return f'{self.name}.{self.fmt}'


@dataclass
class FileList:
    """ Методы работы со списком файлов """
    all: list[FileItem]

    def __post_init__(self):
        self.resolve_indexes()

    def resolve_indexes(self):
        idx = 1
        for fi in self.all:
            if fi.active:
                fi.index = idx
                idx += 1
            else:
                fi.index = None

    def get(self, name: str, fmt: str) -> FileItem:
        """ Возвращает данные файла по имени и формату """
        for fi in self.all:
            if fi.name == name and fi.fmt == fmt:
                return fi

        raise IndexError(f'FileItem "{name}.{fmt}" не обнаружен.\nFILES: {self.all}')

    @classmethod
    def from_path(
            cls,
            path: Path | str,
            formats: list[str] = None,
            recursively: bool = False,
            sort: bool = True,
    ) -> 'FileList':
        """
        Собирает список файлов из целевого каталога
        :param path: целевой каталог
        :param formats: ограничение форматов искомых файлов
        :param recursively: искать ли в подкаталогах
        :param sort: сортировать ли результат по имени файла
        :return: список путей к файлам каталога
        """
        if isinstance(path, str):
            path = Path(path)
        files: list[FileItem] = []
        search_method = 'rglob' if recursively else 'glob'
        search = getattr(path, search_method)
        formats = [f'*.{f}' for f in formats] if formats else ['*']
        for fmt in formats:
            for fpath in search(fmt):
                if fpath.is_file():
                    files.append(FileItem(abs_path=fpath))

        if sort:
            files.sort(key=lambda x: x.name)

        return cls(all=files)

    @property
    def active(self) -> list[FileItem]:
        """ Возвращает список активных (отмеченных галочкой в GUI) файлов """
        return [fi for fi in self.all if fi.active]
