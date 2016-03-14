#!/usr/bin/env python3
"""
Python retro shell graphics framework built. User must have the colorama and

This module contains tests relating to Retro.

Further information can be found in retro.py or on the Github page:

    http:// TODO link

Copyright (c) 2016 Eric Buss
"""
########################################################################################################################
# Imports
########################################################################################################################
import retro
import unittest

class RetroTests(unittest.TestCase):
    ####################################################################################################################
    # Utility tests
    ####################################################################################################################
    def test_debug(self):
        """
        Test that the debug decorator correctly sets the debug flag to True.

        :return: None
        """
        class Test:
            def __init__(_self):
                _self.debug = False

            @retro.debug
            def test(_self):
                self.assertTrue(_self.debug)

        Test().test()

    def test_debug_attribute_error(self):
        """
        Test that debug throws an error if the object it is called on does not have a debug flag.

        :return: None
        """
        @retro.debug
        def test(_self):
            pass

        with self.assertRaises(retro.RetroError):
            test(None)

    def test_listen(self):
        """
        Test that the listen decorator correctly retrieves the new, old, and owner values from a decorated function as
        well as not interfering with the property function itself.

        :return: None
        """
        def _(new, old, owner):
            self.assertEqual(new, True)
            self.assertEqual(old, False)
            self.assertEqual(type(owner), Test)

        class Test:
            def __init__(_self):
                _self._property = True
                _self._listeners = {'property':[]}

            @retro.listen
            def property(_self, arg=None):
                if arg is None:
                    return _self._property
                _self._property = arg
                return _self

        self.assertFalse(Test().property(False).property())
    ####################################################################################################################
    # Buffer tests
    ####################################################################################################################
    def test_empty_buffer(self):
        """
        Test that an empty buffer is the correct size and fills the character and color buffer with the correct values.

        :return: None
        """
        buffer = retro.Buffer(4, 4)
        self.assertEqual(buffer.character_buffer, [[' ', ' ', ' ', ' '] for _ in range(4)])
        self.assertEqual(buffer.color_buffer, [[';', ';', ';', ';'] for _ in range(4)])

    def test_string_buffer(self):
        """
        Test that a src string is correctly loaded into buffers and newline characters are respected.

        :return: None
        """
        buffer = retro.Buffer(6, 2, src='Hello\nWorld')
        self.assertEqual(''.join(buffer.character_buffer[0]), 'Hello ')
        self.assertEqual(''.join(buffer.character_buffer[1]), 'World ')

    def test_draw_transparent(self):
        """
        Test that when the transparency flag is set characters are not overwritten by ' ' characters in another buffer.

        :return: None
        """
        buffer = retro.Buffer(5, 2, src='Hello\nWorld')
        buffer.draw(retro.Buffer(5, 2, src='C'), trans=True)
        self.assertEqual(''.join(buffer.character_buffer[0]), 'Cello')
        self.assertEqual(''.join(buffer.character_buffer[1]), 'World')

    def test_draw_not_transparent(self):
        """
        Test that when the transparency flag is set characters are overwritten by ' ' characters in another buffer.

        :return: None
        """
        buffer = retro.Buffer(5, 2, src='Hello\nWorld')
        buffer.draw(retro.Buffer(5, 2, src='C'), trans=False)
        self.assertEqual(''.join(buffer.character_buffer[0]), 'C    ')
        self.assertEqual(''.join(buffer.character_buffer[1]), '     ')
        pass

    def test_draw_offset(self):
        """
        Test that the Buffer will correctly draw offsets.

        :return: None
        """
        buffer = retro.Buffer(5, 2, src='Hello\nWorld')
        buffer.draw(retro.Buffer(13, 1, src='I said Hi'),-7 ,trans=False)
        self.assertEqual(''.join(buffer.character_buffer[0]), 'Hi   ')
        self.assertEqual(''.join(buffer.character_buffer[1]), 'World')

    def test_draw_component_error(self):
        """
        Test that Buffer will throw an error for invalid a non drawable object.

        :return: None
        """
        with self.assertRaises(retro.RetroError):
            retro.Buffer().draw(None)

    def test_draw_component(self):
        """
        Test that a mock component will have the correct properties applied when drawn.

        :return: None
        """
        class Test:

            def x(_self):
                return 1

            def y(_self):
                return 1

            def transparency(_self):
                return False

            def draw(_self):
                return retro.Buffer(3, 1, back='C')

        buffer = retro.Buffer(5, 2, src='Hello\nWorld').draw_component(Test())
        self.assertEqual(''.join(buffer.character_buffer[0]), 'Hello')
        self.assertEqual(''.join(buffer.character_buffer[1]), 'W   d')
        self.assertEqual(''.join(buffer.color_buffer[0]), ';;;;;')
        self.assertEqual(''.join(buffer.color_buffer[1]), ';;C;C;C;')

    def test_buffer_indexing(self):
        """
        Check that indexing is supported for the character and color buffer.

        :return: None
        """
        buffer = retro.Buffer(5, 2, src='Hello\nWorld')
        self.assertEqual(buffer[0, 0], ('H', ';'))
        buffer[1, 1] = 'O', 'C;C'
        self.assertEqual(buffer[1, 1], ('O', 'C;C'))

    def test_buffer_len(self):
        """
        Check that buffer length is correctly calculated.

        :return: None
        """
        self.assertEqual(len(retro.Buffer(10, 10)), 100)

    def test_buffer_str(self):
        """
        Check that the str method of Buffer correctly minimizes ansi sequences.

        :return: None
        """
        buffer = retro.Buffer(5, 2, src='Hello\nWorld').draw(retro.Buffer(2, 2, back=retro.CYAN), trans=False)
        self.assertEqual(str(buffer), '\x1b[0m\x1b[46m  \x1b[0mllo\x1b[0m\n\x1b[0m\x1b[46m  \x1b[0mrld\x1b[0m\n')
    ####################################################################################################################
    # Component tests
    ####################################################################################################################
    def test_x(self):
        pass

    def test_y(self):
        pass

    def test_z(self):
        pass

    def test_width(self):
        pass

    def test_height(self):
        pass

    def test_foreground(self):
        pass

    def test_background(self):
        pass

    def test_visible(self):
        pass

    def test_transparency(self):
        pass

    def test_add_components(self):
        pass

    def test_remove_components(self):
        pass

    def test_parent(self):
        pass
    ####################################################################################################################
    # Label tests
    ####################################################################################################################
    def test_text(self):
        pass

    def test_center_align(self):
        pass

    def test_left_align(self):
        pass

    def test_right_align(self):
        pass

    def test_top_align(self):
        pass

    def test_bottom_align(self):
        pass
    ####################################################################################################################
    # Image
    ####################################################################################################################
    def test_image(self):
        pass
    ####################################################################################################################
    # Button
    ####################################################################################################################
    def test_button_unfocused(self):
        pass

    def test_button_focused(self):
        pass

    def test_button_selection(self):
        pass

    def test_button_action(self):
        pass
    ####################################################################################################################
    # Input
    ####################################################################################################################
    def test_input_action(self):
        pass
    ####################################################################################################################
    # Password
    ####################################################################################################################
    def test_password_text(self):
        pass

    def test_password_pass(self):
        pass
    ####################################################################################################################
    # Editor
    ####################################################################################################################
    def test_editor_coloring(self):
        pass

    def test_editor_selection(self):
        pass
    ####################################################################################################################
    # Autocomplete
    ####################################################################################################################
    def test_autocomplete_empty(self):
        pass

    def test_autocomplete_options(self):
        pass

    def test_autocomplete_selection(self):
        pass

    def test_autocomplete_action(self):
        pass
    ####################################################################################################################
    # Progressbar
    ####################################################################################################################
    def test_progressbar(self):
        pass
    ####################################################################################################################
    # Integration tests
    ####################################################################################################################
    def test_splash(self):
        pass

if __name__ == '__main__':
    unittest.main()