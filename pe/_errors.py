
class Error(Exception):
    """Exception raised for invalid parsing expressions."""


class GrammarWarning(Warning):
    pass


class GrammarError(Error):
    pass


class ParseError(Error):

    def __init__(self,
                 message: str = None,
                 filename: str = None,
                 lineno: int = None,
                 offset: int = None,
                 text: str = None):
        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.offset = offset
        self.text = text

    @classmethod
    def from_pos(cls,
                 pos: int,
                 text: str,
                 message: str = None,
                 filename: str = None):
        """Instantiate from a full *text* and a file position *pos*"""

        # this method should work for \n and \r\n newline sequences, which
        # I assume covers all potential users
        try:
            start = text.rindex('\n', 0, pos) + 1
        except ValueError:
            start = 0
        try:
            end = text.index('\n', start)
        except ValueError:
            end = len(text)
        lineno = text.count('\n', 0, start)
        line = text[start:end]
        return cls(message,
                   filename=filename,
                   lineno=lineno,
                   offset=pos - start,
                   text=line)

    def __str__(self):
        parts = []
        if self.filename is not None:
            parts.append(f'File "{self.filename}"')
        if self.lineno is not None:
            parts.append(f'line {self.lineno}')
        if self.offset is not None:
            parts.append(f'character {self.offset}')
        if parts:
            parts = ['', '  ' + ', '.join(parts)]
        if self.text is not None:
            parts.append('    ' + self.text)
            if self.offset is not None:
                parts.append('    ' + (' ' * self.offset) + '^')
        if self.message is not None:
            name = self.__class__.__name__
            parts.append(f'{name}: {self.message}')
        return '\n'.join(parts)
