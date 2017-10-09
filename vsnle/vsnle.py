from .clip_utils import new_clip

class Composition(object):
    className = 'Composition'
    def __init__(self, preset="FHD_24000_1001_RGB24", width=None, height=None,
             fpsnum=None, fpsden=None, format=None, duration=None, color=0x000000, tracks=3):
        """
        Constructor for a new composition.

        :param preset: string in {Resolution}_{FPS dividend}_{DPS denominator}_{VS Format}
        :param width: video width, integer, overrides preset
        :param height: video height, integer, overrides preset
        :param fpsnum: FPS dividend, integer, overrides preset
        :param fpsden: FPS denominator, integer, overrides preset
        :param format: video format, must be VS.format, overrides preset
        :param duration: the duration of the new clip, integer, in seconds.
                         Default to be 30
        :param color: the color of the new blank clip, in standard 8-bit RGB.
                    Can be string or HEX. Defaults to be black.
        :param tracks: number of tracks. Note that the tracks stack from index
                       0 on one another.
        """

        self._tracks = [None for i in range(tracks)]
        self._tracks[0] = new_clip(preset, width, height, fpsnum, fpsden, format, duration, color)
        self._duration = duration if duration and isinstance(duration, int) else 30



    @property
    def tracks(self):
        return self._tracks

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError(self.className + ': setting invalid duration.')
        self._duration = value

    def get_frame(self, timestamp):


        pass
