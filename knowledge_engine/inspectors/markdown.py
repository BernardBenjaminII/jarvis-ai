from .text import TextInspector


class MarkdownInspector(TextInspector):

    extensions = (
        ".md",
        ".markdown",
    )
