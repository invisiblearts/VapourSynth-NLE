import vapoursynth as vs
import re
import functools

def parse_preset(preset_string):
    """
    Uses regex to parse parameters from preset string.

    :param preset_string: the string to be parsed
    :return: tuple in width, height, fpsnum, fpsden, format. None if illegal string
    """
    funcName = 'parse_preset'
    valid_resolutions = {'QVGA': (320, 240),
                         'VGA': (640, 480),
                         'qHD': (640, 360),
                         'XGA': (1024, 768),
                         'HD': (1280, 720),
                         'WXGA': (1280, 768),
                         'FHD': (1920, 1080),
                         'QHD': (2560, 1440)}

    valid_format = ['RGB24', 'RGB48',
                    'YUV420P8', 'YUV420P10', 'YUV420P16',
                    'YUV422P8', 'YUV422P10', 'YUV422P16',
                    'YUV444P8', 'YUV444P10', 'YUV444P16',
                    'GRAY8', 'GRAY16']

    valid_res_string = '|'.join(valid_resolutions.keys())
    valid_format_string = '|'.join(valid_format)

    expression = re.compile(r'({res})_\d+_\d+_({form})'.format(res=valid_res_string,
                                                      form=valid_format_string))

    result = expression.match(preset_string)

    if not result:
        raise ValueError(funcName + ': Invalid preset string')
    else:
        r, fn, fd, fo = result.group().split('_')

    return valid_resolutions[r][0], valid_resolutions[r][1],\
           int(fn), int(fd), getattr(vs, fo)


def parse_color(color):
    """
    Helper function that parses a string or int to 8-bit standard RGB values.

    :param color: the color string/integer to be parsed
    :return: tuple of int: (R, G, B)
    """
    funcName = 'parse_color'
    if isinstance(color, int):
        if color > 0xFFFFFF or color < 0:
            raise ValueError(funcName + ": Invalid color value")
        r = color >> 16
        g = (color >> 8) - (r << 8)
        b = color - (r << 16) - (g << 8)
    elif isinstance(color, str):
        if color.startswith('#'):
            color = color[1:]
        color = color.capitalize()
        expression = re.compile(r'(\d|A|B|C|D|E|F){8}')
        result = expression.match(color)

        if not result:
            raise ValueError(funcName + ': Invalid color string')

        ret = result.group()
        r, g, b = map(functools.partial(int, base=16), (ret[:2], ret[2:4], ret[4:]))
    else:
        raise ValueError(funcName + ': Uninterpretable color')

    return r, g, b


def new_clip(preset="FHD_24000_1001_RGB24", width=None, height=None,
             fpsnum=None, fpsden=None, format=None, duration=None, color=0x000000):
    """
    Get a blank clip with given background color.

    :param preset: string in {Resolution}_{FPS dividend}_{DPS denominator}_{VS Format}
    :param width: video width, integer, overrides preset
    :param height: video height, integer, overrides preset
    :param fpsnum: FPS dividend, integer, overrides preset
    :param fpsden: FPS denominator, integer, overrides preset
    :param format: video format, must be VS.format, overrides preset
    :param duration: the duration of the new clip, integer, in seconds. Default to be 30
    :param color: the color of the new blank clip, in standard 8-bit RGB.
                  Can be string or HEX. Defaults to be black.
    :return: the corresponding blank clip.
    """

    funcName = "new_clip"
    format = format if isinstance(format, vs.Format) else \
        getattr(vs, format) if hasattr(vs, str(format)) else None
    w, h, fn, fd, fo, du = None, None, None, None, None, None

    try:
        w, h, fn, fd, fo = parse_preset(preset)
        r, g, b = parse_color(color)
    except ValueError as e:
        raise ValueError(funcName + ': ' + str(e))

    w = width if width else w
    h = height if height else h
    fn = fpsnum if fpsnum else fn
    fd = fpsden if fpsden else fd
    fo = format if format else fo
    du = duration if duration and isinstance(duration, int) else 30


    if not (w and h and fn and fd and fo):
        raise ValueError(funcName + ": Invalid parameters.")

    core = vs.get_core()

    rgb8_to_yuv8 = lambda r, g, b: tuple(map(int, (0.299 * r + 0.587 * g + 0.114 * b,
                                -0.169 * r - 0.331 * g + 0.5 * b + 128,
                                0.5 * r - 0.419 * g - 0.081 * b + 128)))

    rgb16_to_yuv16 = lambda r, g, b: tuple(map(int, (0.299 * r + 0.587 * g + 0.114 * b,
                                -0.169 * r - 0.331 * g + 0.5 * b + 32768,
                                0.5 * r - 0.419 * g - 0.081 * b + 32768)))

    depth8_to_16 = lambda val: (val << 8) + (1 << 7)

    if fo.value > 1000000 and fo.value < 2000000: # vs.GRAY
        if fo == vs.GRAY8:
            co = (r+g+b)/3
        elif fo == vs.GRAY16:
            co = depth8_to_16((r+g+b)/3)
        else:
            raise ValueError(funcName + ': Unsupported format')

    elif fo.value > 2000000 and fo.value < 3000000: # vs.RGB
        if fo == vs.RGB24:
            co = (r, g, b)
        elif fo == vs.RGB48:
            co = tuple(map(depth8_to_16, (r, g, b)))
        else:
            raise ValueError(funcName + ': Unsupported format')

    elif fo.value > 3000000 and fo.value < 4000000: # vs.YUV
        if fo.name.endswith('P8'):
            co = rgb8_to_yuv8(r, g, b)
        elif fo.name.endswith('P16'):
            co = rgb16_to_yuv16(*tuple(map(depth8_to_16, (r, g, b))))
        else:
            raise ValueError(funcName + ': Unsupported format')
    else:
        raise ValueError(funcName + ': Unsupported format')

    return core.std.BlankClip(width=w, height=h, format=fo,
                                   fpsnum=fn, fpsden=fd, length=du, color=co)

