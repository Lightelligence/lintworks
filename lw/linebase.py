"""Broadcast every line of a file to a simple line listener.

These two prototypical examples can be directly used as the basis for other rules.

"""
from lw import base

class LineBroadcaster(base.Broadcaster): # pylint: disable=too-few-public-methods
    """Broadcast every line of a file to all listeners.

    The update method for this Broadcaster is "update_line".

    """
    @classmethod
    def from_filename(cls, filename):
        fstream = open(filename)
        instance = cls(filename, fstream)
        fstream.close()
        return instance

    def __init__(self, filename, fstream, *args, **kwargs):
        """
        Parameters
        ----------
        filename : str
            The absolute path to the file to be opened and broadcast.

        fstream : io.TextIoWrapper or io.StringIO
            This is the opened handle to the file.
            It simplifies unit testing to do the opening outside the constructor.

        """
        super(LineBroadcaster, self).__init__(filename, fstream, *args, **kwargs)
        for i, line in enumerate(fstream.readlines()):
            self.broadcast(i, line)
        self.eof()

    def eof(self):
        self._broadcast("eof")


class LineListener(base.Listener): # pylint: disable=too-few-public-methods
    """Listen to every line of a file.

    This example shows how to create a listener for every line of a file.
    You may derive directly from this class.

    """
    subscribe_to = [LineBroadcaster]
    def __init__(self, filename, fstream, *args, **kwargs):
        self.filename = filename
        super(LineListener, self).__init__(filename, fstream, *args, **kwargs)

    def update_line(self, line_no, line):
        """
        Parameters
        ----------
        line_no : int
            The line number being broadcast. Usually used for error messages.
        line : str
            The content of the line being broadcast. Excludes newline.

        """
        pass

    def eof(self):
        pass

    def error(self, line_no, line, message):
        self.gc.rs.error(self, line_no, line, message)
