import time

from kivy.factory import Factory
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp

from src.components.widgets import (
    Paginator,
    FlexibleDialog,
    FlexibleLabel,
    FileItemWidget,
    BlockContainer,
)
from src.components.pages import (
    MainPage,
    VideoConversionPage,
    SubtitleExtractionPage,
    SubtitleAddingPage,
    AudiotrackAddingPage,
)
from src.utils.common import is_desktop


class MoviekitApp(MDApp):
    def build(self):
        self.title = 'MovieKit'
        Clock.schedule_interval(self._update_clock, 1 / 60)
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Darkslateblue'
        self.root.ids.paginator.go_page()
        if is_desktop():
            # почему? потому что я забил на адаптивность
            Window.maximize()
            Window.on_restore = Window.maximize

    def on_start(self):
        pass

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def _update_clock(self, dt):
        self.time = time.time()


if __name__ == '__main__':
    Factory.register('Paginator', Paginator)
    Factory.register('FlexibleDialog', FlexibleDialog)
    Factory.register('FlexibleLabel', FlexibleLabel)
    Factory.register('FileItemWidget', FileItemWidget)
    Factory.register('BlockContainer', BlockContainer)
    Factory.register('MainPage', MainPage)
    Factory.register('VideoConversionPage', VideoConversionPage)
    Factory.register('SubtitleExtractionPage', SubtitleExtractionPage)
    Factory.register('SubtitleAddingPage', SubtitleAddingPage)
    Factory.register('AudiotrackAddingPage', AudiotrackAddingPage)
    MoviekitApp().run()
