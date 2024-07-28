def format_file_size(nbytes: int | str | None) -> str:
    """ Переводит количество байтов в человеко-читаемый вид """
    if nbytes is None:
        nbytes = 0
    nbytes = int(nbytes)
    postfixes = ('Б', 'кБ', 'МБ', 'ГБ', 'ТБ')

    index = 0
    while nbytes >= 1024 and index < len(postfixes) - 1:
        nbytes /= 1024
        index += 1

    return f'{nbytes:.3f} {postfixes[index]}'


def format_duration(nsec: int | float | str | None) -> str:
    """ Переводит количество секунд в человеко-читаемый вид """
    if nsec is None:
        nsec = 0
    nsec = float(nsec)
    hours = int(nsec // 3600)
    minutes = int((nsec % 3600) // 60)
    seconds = int(nsec % 60)

    return f'{hours:02}:{minutes:02}:{seconds:02}'
