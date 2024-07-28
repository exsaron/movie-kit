from kivy.utils import platform


def is_desktop():
    return platform in ('linux', 'win', 'macosx')
