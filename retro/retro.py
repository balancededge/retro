#!/usr/bin/env python3
"""
Python retro shell graphics framework built on colorama

This module contains the core framework classes for creating shell components and displaying ASCII text. Components are
added to a Retro instance that once launched takes control of the current thread.

Example usage:

    import retro

    r = retro.Retro()
    r.add_component(retro.Label('Hello World'))
    r.launch()

Further information can be found below or on the Github page:

    http:// TODO link

Copyright (c) 2016 Eric Buss
"""
# TODO documentation
# TODO testing
# TODO focus implementation in Retro
# TODO input, password, editor, button, autocomplete
# TODO animations
# TODO ascii cleanup
########################################################################################################################
# Imports
########################################################################################################################
import multiprocessing
import colorama
import shutil
import ascii
import time
import sys
import os
import re
########################################################################################################################
# Meta
########################################################################################################################
__author__  = 'Eric Buss'
__email__   = 'ejrbuss@shaw.ca'
__version__ = 'v0.0.1'
########################################################################################################################
# Constants
########################################################################################################################
# Color strings
YELLOW  = 'YELLOW'
WHITE   = 'WHITE'
RED     = 'RED'
MAGENTA = 'MAGENTA'
GREEN   = 'GREEN'
CYAN    = 'CYAN'
BLUE    = 'BLUE'
BLACK   = 'BLACK'
LIGHT_YELLOW    = 'LIGHTYELLOW_EX'
LIGHT_WHITE     = 'LIGHTWHITE_EX'
LIGHT_RED       = 'LIGHTRED_EX'
LIGHT_MAGENTA   = 'LIGHTMAGENTA_EX'
LIGHT_GREEN     = 'LIGHTGREEN_EX'
LIGHT_CYAN      = 'LIGHTCYAN_EX'
LIGHT_BLUE      = 'LIGHTBLUE_EX'
LIGHT_BLACK     = 'LIGHTBLACK_EX'
# Available colors list
_colors = ['', YELLOW, WHITE, RED, MAGENTA, GREEN, CYAN, BLUE, BLACK,
           LIGHT_YELLOW, LIGHT_WHITE, LIGHT_RED, LIGHT_MAGENTA, LIGHT_GREEN, LIGHT_CYAN, LIGHT_BLUE, LIGHT_BLACK]
# Formatting constants
CENTER  = 2
LEFT    = 0
RIGHT   = 1
TOP     = 0
BOTTOM  = 1
########################################################################################################################
# Globals
########################################################################################################################
_fallback_width     = 80        # Default shell width
_fallback_height    = 20        # Default shell height
_clear              = '\x1b[H'  # \x1b[2J\x1b[H # Use the second option if the screen is not clearing properly
_cleanup            = True      # Clear screen when Retro closes
_typecheck          = True      # Check types of args and properties
_vi                 = False     # VI mode green and slow
########################################################################################################################
# Utilities
########################################################################################################################
def debug(fn):
    """
    A decorator for setting the debug flag of a Class.

    :param fn: The function to decorate
    :return: The decorated function
    """
    def _(self):
        if _typecheck and (not hasattr(self, 'debug')):
            raise RetroError('Can only debug Objects with debug flag: received {}'.format(self))
        self.debug = True
        value = fn(self)
        self.debug = False
        return value

    return _

def listen(fn):
    """
    A decorator for attaching listeners to property function calls.

    A property function should inform a listener what it is listening to. For example the 'width' property function of
    Component is named width. Typically the real value will be stored in a private value like my_component._width. The
    property function should look like the following, substituting 'width' for your property name:

        def width(self, new_width=None):
            if new_width is None:
                return self._width
            # Type checking occurs here if the _typecheck flag is set
            self._width = new_width
            return self

    By convention the new property argument should be None. If the function is called without any arguments or None is
    passed to the function it should act as a getter and return the current value of the Property. If the function is
    called with arguments the function should act as a setter and set the property. By convention the class itself
    should be returned to allow for the chaining of property calls. For example:

        my_component.width(100).height(20)

    Listeners should be stored in the class dictionary _listeners. Listeners for a property function should be found
    indexed at the __name__ value of that property function. Listeners will be called as a function with arguments new,
    old, and owner.

    :param fn: The property function to decorate
    :return: The decorated function
    """
    def _(self, arg=None):
        if arg is None:
            return fn(self)
        for listener in self._listeners[fn.__name__]:
            listener(new=arg, old=fn(self), owner=self)
        return fn(self, arg)
    return _

def getch():
    """
    Getch multi-platform implementation by Danny Yoo. from:

        http://code.activestate.com/recipes/134892/

    We update frames on input making a getch implementation necessary. This should be friendly to most linux and windows
    systems. The try except for msvcrt will cost time one unix machines, but this loss is considered acceptable.

    :return: Read character
    """
    try:
        import msvcrt
        return msvcrt.getch()
    except:
        import sys, tty, termios
        old = termios.tcgetattr(sys.stdin.fileno())
        try:
            tty.setraw(sys.stdin.fileno())
            c = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)
        return c
########################################################################################################################
# RetroError
########################################################################################################################
class RetroError(BaseException):
    pass
########################################################################################################################
# Buffer
########################################################################################################################
class Buffer:
    """
    The Buffer manages character and color data over a set grid. Buffers provide an interface for composing this data as
    well as producing a final string for display.
    """
    def __init__(self, width=None, height=None, fore='', back='', src=None):
        """
        Buffers are meant for one off uses in draw functions as such width and height must be specified at
        instantiation. This buffer will initialized with an empty character array of the ' ' character and a color array
        of fore;back at every index. If a src is provided the Buffer will load the string into the character array
        starting at the first index.

        :param width: The width of the buffer
        :param height: The height of the buffer
        :param fore: The foreground color
        :param back: The background color
        :param src: A string src to load
        :return: The initialized Buffer
        """
        # If width or height is None the Buffer is sized to the terminal
        if width is None or height is None:
            width, height = shutil.get_terminal_size((_fallback_width, _fallback_height))
            # Reduce height by one to keep buffer on screen
            height -= 1
        # Type Check
        if _typecheck and (type(width) != int or width < 0):
            raise RetroError('Width must be a positive int: received {}'.format(width))
        if _typecheck and (type(height) != int or height < 0):
            raise RetroError('Height must be a positive int: received {}'.format(height))
        # Set attributes
        self.debug = False
        self.width = width
        self.height = height
        self.character_buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.color_buffer = [[fore + ';' + back for _ in range(width)] for _ in range(height)]
        # Load src if it is available
        if src is not None:
            source = str(src).split('\n')
            # Index
            for y in range(min(len(source), self.height)):
                for x in range(min(len(source[y]), self.width)):
                    self.character_buffer[y][x] = source[y][x]

    def draw(self, src, x=0, y=0, trans=True):
        """
        Draw a buffer onto the current buffer at the given offset. If the transparency flag is set than ' ' characters
        in the source will be skipped along with their foreground color and the background color will be ignored
        entirely.

        :param src: The source Buffer
        :param x: The x offset
        :param y: The y offset
        :param trans: The transparency flag
        :return: The composite Buffer
        """
        # Type checks
        if _typecheck and (not hasattr(src, 'character_buffer') or not hasattr(src, 'color_buffer')):
            raise RetroError('Can only draw another buffer: received {}'.format(src))
        if _typecheck and (type(x) != int):
            raise RetroError('X offset must be an int: received {}'.format(x))
        if _typecheck and (type(y) != int):
            raise RetroError('Y offset must be an int: received {}'.format(y))
        # Index
        for ry in range(src.height):
            for rx in range(src.width):
                # If outside of Buffer bounds skip
                if x + rx < 0 or x + rx > self.width - 1 or y + ry < 0 or y + ry > self.height - 1:
                    continue
                # Write src if there is a character or the transparent flag is not set
                if src.character_buffer[ry][rx] != ' ' or not trans:
                    self.character_buffer[y + ry][x + rx] = src.character_buffer[ry][rx]
                # If there is no character and the transparent flag is set skip setting colors
                if _vi or (trans and src.character_buffer[ry][rx] == ' '):
                    continue
                # If transparent inherit background from color buffer and foreground from src
                elif trans:
                    self.color_buffer[y + ry][x + rx] = src.color_buffer[ry][rx].split(';')[0] + ';' + \
                                                        self.color_buffer[y + ry][x + rx].split(';')[1]
                # Inherit colors from src
                else:
                    self.color_buffer[y + ry][x + rx] = src.color_buffer[ry][rx]
        return self

    def draw_component(self, comp):
        """
        Draw a component onto the Buffer and pass its properties as arguments.

        :param comp: The component to draw
        :return: The composite Buffer
        """
        if _typecheck and (not hasattr(comp, 'draw') or not hasattr(comp, 'x') or not hasattr(comp, 'y') or not hasattr(comp, 'transparency')):
            raise RetroError()
        return self.draw(comp.draw(), comp.x(), comp.y(), comp.transparency())

    def __getitem__(self, index):
        """
        Support indexing indexing into Buffer. Returns the character and color at the given (x, y) tuple.

        :param index: An (x, y) tuple used to index
        :return: (character, color)
        """
        x, y = index
        return self.character_buffer[y][x], self.color_buffer[y][x]

    def __setitem__(self, index, value):
        """
        Support index assignment into Buffer. Value is expected to be a tuple of character and color.

        :param index: An (x, y) tuple used to index
        :param value: (character, color)
        :return: None
        """
        x, y = index
        character, color = value
        self.character_buffer[y][x] = character
        self.color_buffer[y][x] = color

    def __len__(self):
        """
        Return the square area of the Buffer (width x height).

        :return: The square area
        """
        return self.width * self.height

    def __str__(self):
        """
        Convert buffers to a string representation with rows separated by newlines. Colors are converted to ansi
        sequences and their use is minimized to speed up the shell update process which can be quite slow. ie:

            A buffer set like so:
                [ ('H', 'CYAN;'), ('e', 'CYAN;'), ('l', ';'), ('l', ';'), ('o', ';')]
            Will compile to:
                '\x1b[0m\x1b[46mHe\x1b[0mllo\x1b[0m'
            Rather than:
                '\x1b[0m\x1b[46mH\x1b[0m\x1b[46me\x1b[0ml\x1b[0ml\x1b[0mo\x1b[0m'

        If the debug flag is set than the color names are added rather than the ansi sequences.

        :return: The string representation
        """
        compiled = ''
        # Index
        for characters, colors in zip(self.character_buffer, self.color_buffer):
            cache = ';'
            for character, color in zip(characters, colors):
                # If color is cached skip and just add the character
                if color != cache:
                    # If debug print color name
                    if self.debug:
                        compiled += color + character
                    # Get ansi sequence from colorama if needed
                    else:
                        fore, back = color.split(';')
                        fore = getattr(colorama.Fore, fore) if fore != '' else ''
                        back = getattr(colorama.Back, back) if back != '' else ''
                        compiled += colorama.Style.RESET_ALL + fore + back + character
                else:
                    compiled += character
                cache = color
            # Reset style at new line in case Retro buffer is only drawing to part of the shell
            compiled += ('' if _vi else colorama.Style.RESET_ALL) + '\n'
        return compiled

    @debug
    def summary(self):
        """
        Produce a summary version of the buffer with whitespace replace with '...' and colors shown as names along with
        Buffer metrics at the top.

        :return: The buffer summary
        """
        return 'Buffer({}x{})\n'.format(self.width, self.height) + re.sub(r' +', '...', str(self))
########################################################################################################################
# Component
########################################################################################################################
class Component:
    """
    The Component class is the most basic Object that can be drawn to screen. It maintains information about location
    and size, colors, and Buffer flags. This information is maintained as 'Properties' as detailed in the listen
    function so that they may be listened to. Component also implements the basic process for drawing.
    """
    def __init__(self):
        """
        Initializes all property values for Component. Attributes name _arg... are used to track the assigned value of
        the Property. When specifying location or width with % for instance the _... value will be recalculated at every
        draw call.

        By default _argwidth and _argheight are None and will inherit from the Components parent at the first draw call.
        All other positional values are set to 0 by default.

        Listeners for all properties are listed in _listeners. Subclasses must update this dict with new properties.

        :return: Initialized Component
        """
        # Set attributes
        self._argx = 0
        self._x = 0
        self._argy = 0
        self._y = 0
        self._z = 0
        self._argwidth = None
        self._width = 0
        self._argheight = None
        self._height = 0
        self._fore = ''
        self._back = ''
        self._visible = True
        self._trans = False
        self._components = []
        self._parent = None
        self._listeners = {
            'x':[], 'y':[], 'z':[], 'width':[], 'height':[], 'foreground':[], 'background':[],
            'visible':[], 'transparency':[], 'parent':[]
        }

    @listen
    def x(self, x=None):
        """
        Set the x position of the Component. (0, 0) corresponds to the top left of the shell.

        This value can be supplied as an int or a % value in a string. If this value is negative or larger than this
        Component's parent width only the part of the Component that is over its parent will be drawn. % is recalculated
        every frame.

        :param x: The new x value
        :return: x position on get ; self on set
        """
        if x is None:
            return self._x
        if _typecheck and ((type(x) != int) and (type(x) != str or not re.match(r'\d+%', str(x)))):
            raise RetroError('X offset must be an int or percentage: received {}'.format(x))
        self._argx = self._x = x
        return self

    @listen
    def y(self, y=None):
        """
        Set the y position of the Component. (0, 0) corresponds to the top left of the shell.

        This value can be supplied as an int or a % value in a string. If this value is negative or larger than this
        Component's parent height only the part of the Component that is over its parent will be drawn. % is
        recalculated every frame.

        :param y: The new y value
        :return: y position on get ; self on set
        """
        if y is None:
            return self._y
        if _typecheck and ((type(y) != int) and (type(y) != str or not re.match(r'\d+%', str(y)))):
            raise RetroError('Y offset must be an int or percentage: received {}'.format(y))
        self._argy = self._y = y
        return self

    @listen
    def z(self, z=None):
        """
        Set the z position of the Component. The lower the z position the earlier this Component is drawn to its
        parent's Buffer.

        This value must be an int.

        :param z: The new z value
        :return: z position on get ; self on set
        """
        if z is None:
            return self._z
        if _typecheck and (type(z) != int):
            raise RetroError('Z offset must be an int: received {}'.format(type(z)))
        self._z = z
        return self

    @listen
    def width(self, width=None):
        """
        Set the width of the Component.

        This value can be supplied as a positive int or a % value in a string. If this value is wider than this
        Component's parent width only the part of the Component that is over its parent will be drawn. % is recalculated
        every frame.

        :param width: The new width value
        :return: width on get ; self on set
        """
        if width is None:
            return self._width
        if _typecheck and (width is not None and (type(width) != int or width < 0) and (type(width) != str or not re.match(r'\d+%', str(width)))):
            raise RetroError('Width can only be None or a positive int or percentage: received {} '.format(type(width)))
        self._argwidth = self._width = width
        return self

    @listen
    def height(self, height=None):
        """
        Set the height of the Component.

        This value can be supplied as a positive int or a % value in a string. If this value is higher than this
        Component's parent height only the part of the Component that is over its parent will be drawn. % is recalculated
        every frame.

        :param height: The new height value
        :return: height on get ; self on set
        """
        if height is None:
            return self._height
        if _typecheck and (height is not None and (type(height) != int or height < 0) and (type(height) != str or not re.match(r'\d+%', str(height)))):
            raise RetroError('Height can only be None or a positive int or percentage: received {} '.format(type(height)))
        self._argheight = self._height = height
        return self

    @listen
    def foreground(self, fore=None):
        """
        Set the foreground color of the Component.

        This color will effect any characters within this Components Buffer. The Color must come from the available
        colors list. An empty string '' is equivalent to a reset.

        :param fore: The new foreground color
        :return: foreground color on get ; self on set
        """
        if fore is None:
            return self._fore
        if _typecheck and (fore not in _colors):
            raise RetroError('Foreground color not recognized: {}'.format(fore))
        self._fore = fore
        return self

    @listen
    def background(self, back=None):
        """
        Set the background color of the Component.

        This color will fill the area of this Components Buffer. The Color must come from the available colors list. An
        empty string '' is equivalent to a reset.

        :param fore: The new background color
        :return: background color on get ; self on set
        """
        if back is None:
            return self._back
        if _typecheck and (back not in _colors):
            raise RetroError('Background color not recognized: {}'.format(back))
        self._back = back
        return self

    @listen
    def visible(self, visible=None):
        """
        Set whether this Component is visible.

        :param visible: The new visible value
        :return: visible on get ; self on set
        """
        if visible is None:
            return self._visible
        self._visible = visible
        return self

    @listen
    def transparency(self, trans=None):
        """
        Set whether this Component inherits the background color of its parent and does not draw ' ' over it's parents
        characters.

        :param trans: The new transparency value
        :return: transparency on get ; self on set
        """
        if trans is None:
            return self._trans
        self._trans = trans
        return self

    @listen
    def parent(self, parent=None):
        """
        Set the parent of this component.

        The parent must have a width and height value as in cases where the width and height of the component are None
        the Component is sized off its parent. Until a Component is given a parent its draw function returns an empty
        Buffer.

        :param parent: The new parent component
        :return: parent component on get ; self on set
        """
        if parent is None:
            return self._parent
        if _typecheck and (not hasattr(parent, 'width') or not hasattr(parent, 'height')):
            raise RetroError('Parent object must have (width,height) specs: received {}'.format(type(parent)))
        self._parent = parent
        return self

    def add_listener(self, listener, fn):
        """

        :param listener:
        :param fn:
        :return:
        """
        if _typecheck and (not callable(listener)):
            raise RetroError('Listener must be callable: received {}'.format(listener))
        if _typecheck and (fn not in self._listeners):
            raise RetroError('Function must be part of component: received {}'.format(fn))
        self._listeners[fn].append(listener)
        return self

    def remove_listener(self, listener, fn):
        """
        Add a listener to Component property. The property should be specified using it function name as a string.

        :param listener: The listener function to add
        :param fn: The name of the property function to listen to
        :return: self
        """
        if _typecheck and (fn not in self._listeners):
            raise RetroError('Function must be part of component: received {}'.format(fn))
        self._listeners[fn.__name__].remove(listener)
        return self

    def draw(self):
        """

        :return:
        """
        # Return an empty buffer if the Component is not visible or not on screen
        if not self.visible() or self.parent() is None:
            return Buffer(0, 0)
        # Inherit metrics from parent if width or height are None
        self.width(self.parent().width() if self._argwidth is None else None)
        self.height(self.parent().height() if self._argheight is None else None)
        # Calculate width if it is a percent
        self._width = int(self.width() if '%' not in str(self._argwidth) else (float(self._argwidth.replace('%', '')) / 100) * self.parent().width())
        # Calculate height if it is a percent
        self._height = int(self.height() if '%' not in str(self._argheight) else (float(self._argheight.replace('%', '')) / 100) * self.parent().height())
        # Build buffer
        buffer = Buffer(self.width(), self.height(), self.foreground(), self.background())
        # Draw components
        for comp in sorted(self._components, key=lambda c: c.z):
            buffer.draw_component(comp)
        return buffer

    def __add__(self, comp):
        """

        :param comp:
        :return:
        """
        if _typecheck and (not hasattr(comp, 'draw')):
            raise RetroError('Component object must have a draw method: received {}'.format(type(comp)))
        comp.parent(self)
        self._components.append(comp)
        return self

    def __sub__(self, comp):
        """

        :param component:
        :return:
        """
        comp.parent = None
        self._components.remove(comp)
        return self

    def __contains__(self, index):
        """

        :param index:
        :return:
        """
        try:
            x, y = index
            return x > self.x > x - self.width and y > self.y > y - self.height
        except:
            return index in self._components

    def __bool__(self):
        """

        :return:
        """
        return self.visible() and self.parent() is not None

    def __len__(self):
        """

        :return:
        """
        return self._width * self._height

    def __str__(self):
        """

        :return:
        """
        return '{} metrics:({}x{})@({}x{}x{}) colors:{};{} flags:t[{}]v[{}] children:{}'.format(
            type(self).__name__,
            self.width(), self.height(), self.x(), self.y(), self.z(),
            self.foreground(), self.background(),
            self.transparency(), self.visible(),
            ''.join('\n\t' + str(comp).replace('\n', '\n\t') for comp in self._components)
        )
########################################################################################################################
# Retro
########################################################################################################################
class Retro(Component):
    """

    """
    def __init__(self):
        """

        :param w:
        :param h:
        :return:
        """
        # Initialize colorama so ansi colors work on Windows
        colorama.init()
        # Call super
        super().__init__()

    def launch(self, frametime=None):
        """
        '\x1b[2J\x1b[H'
        vs
        '\x1b\x1b[H'
        :return:
        """
        pool = multiprocessing.Pool(1)
        buffered_character = pool.apply_async(getch)
        buffered_input = ''
        last_frame = 0
        # Input Loop
        while True:
            # Wait on async input or frametime
            if buffered_character.ready() or not last_frame or (frametime is not None and time.time() - last_frame > frametime):
                # Update frame time
                last_frame = time.time()
                # Get input
                if buffered_character.ready():
                    buffered_input += buffered_character.get().decode('utf-8')
                    buffered_character = pool.apply_async(getch)
                # Build buffer
                buffer = Buffer(self._argwidth, self._argheight)
                self._width, self._height = buffer.width, buffer.height
                # Draw components
                for comp in sorted(self._components, key=lambda c: c.z()):
                    buffer.draw_component(comp)
                # Draw for vi mode
                if _vi:
                    os.write(sys.stderr.fileno(), str.encode('\x1b[H' + colorama.Fore.GREEN + str(buffer).replace('\n', '') + buffered_input))
                # Clear screen and write, os.write & stderr are used for performance reasons
                elif self._argwidth is None or self._argheight is None:
                    os.write(sys.stderr.fileno(), str.encode('\x1b[H' + str(buffer).replace('\n', '') + buffered_input))
                else:
                    os.write(sys.stderr.fileno(), str.encode('\x1b[H' + str(buffer) + buffered_input))
                # Return and clear screen if cleanup enabled
                if buffered_input.endswith('exit'):
                    if _cleanup:
                        os.system('cls' if os.name == 'nt' else 'clear')
                    return

########################################################################################################################
# Label
########################################################################################################################
class Label(Component):
    """

    """

    def __init__(self, text):
        """
        
        :param text: 
        :param xalign: 
        :param yalign: 
        :return: 
        """
        super().__init__()
        # Set attributes
        self._xalign = LEFT
        self._yalign = TOP
        self._text = str(text)
        # Set width and height to text width and height if width or height are None
        text_width, text_height = self.text_len()
        self.width(text_width).height(text_height)
        self.transparency(True)
        self._listeners.update({'xalign':[], 'yalign':[], 'text':[]})

    def text_len(self):
        """

        :return:
        """
        return max(len(_) for _ in str(self.text()).split('\n')), str(self.text()).count('\n') + 1

    def xalign(self, xalign=None):
        """
        
        :param xalign: 
        :return: 
        """
        if xalign is None:
            return self._xalign
        if _typecheck and (xalign not in [LEFT, CENTER, RIGHT]):
            raise RetroError('Unrecognized format for x alignment: received {}'.format(xalign))
        self._xalign = xalign
        return self

    def yalign(self, yalign=None):
        """
        
        :param yalign: 
        :return: 
        """
        if yalign is None:
            return self._yalign
        if _typecheck and (yalign not in [LEFT, CENTER, RIGHT]):
            raise RetroError('Unrecognized format for x alignment: received {}'.format(yalign))
        self._yalign = yalign
        return self

    def text(self, text=None):
        """

        :param text:
        :return:
        """
        if text is None:
            return self._text
        self._text = str(text)
        return self

    def draw(self):
        """

        :return:
        """
        # Get default buffer from Component
        buffer = super().draw()
        # Write text to its own buffer
        text_width, text_height = self.text_len()
        text = Buffer(text_width, text_height, self.foreground(), self.background(), self._text)
        # Calculate alignment
        x = LEFT if self.xalign() == LEFT else (self.width() - text.width) / self.xalign()
        y = TOP if self.yalign() == TOP else (self.height() - text.height) / self.yalign()
        # Draw text to buffer
        buffer.draw(text, x=int(x), y=int(y))
        return buffer

########################################################################################################################
# Image
########################################################################################################################
class Image(Component):
    pass

########################################################################################################################
# Button
########################################################################################################################
class Button(Label):
    pass

########################################################################################################################
# Input
########################################################################################################################
class Input(Label):
    pass

########################################################################################################################
# Password
########################################################################################################################
class Password(Label):
    pass

########################################################################################################################
# Editor
########################################################################################################################
class Editor(Label):
    pass

########################################################################################################################
# Autocomplete
########################################################################################################################
class Autocomplete(Component):
    pass

########################################################################################################################
# Progressbar
########################################################################################################################
class Progressbar(Component):
    pass

########################################################################################################################
# Demos
########################################################################################################################
def demo():
    """

    :return:
    """
    global _vi
    if '-vi' in sys.argv:
        _vi = True
    retro = Retro()
    label1 = Label(ascii.Ascii('Hello World')).foreground(LIGHT_MAGENTA).width('100%')
    label2 = Label('Testing').xalign(CENTER).foreground(LIGHT_MAGENTA).background(BLUE).width('50%').transparency(False)
    py = Label(ascii.Ascii('py')).foreground(LIGHT_BLUE).y(15)
    xam = Label(ascii.Ascii('xam')).foreground(LIGHT_YELLOW).x(py.width() - 2).y(15)
    comp = Component().y(10).width('50%').height('30%').background('WHITE') + label2
    retro + label1 + py + xam + comp
    print(retro)
    #retro.launch()

def hello_world():
    """
    Hello World must be one line.

    :return: None
    """
    (Retro() + Label(ascii.Ascii('Hello World')).xalign(CENTER).yalign(CENTER).width('100%').height('100%').foreground(LIGHT_MAGENTA)).launch()

def splash():
    pass

def fractal():
    pass

if __name__ == '__main__':
    #hello_world()
    demo()