from IPython.terminal.embed import InteractiveShellEmbed
from prompt_toolkit.layout import FormattedTextControl, Window, WindowAlign, to_container


def get_titlebar_text():
    return [
        ('class:title', ' Hello world '),
        ('class:title', ' (Press [Ctrl-Q] to quit.)'),
    ]


windows = to_container(
    Window(height=1,
           content=FormattedTextControl(get_titlebar_text),
           align=WindowAlign.CENTER)
)

shell = InteractiveShellEmbed()
children = shell.pt_app.layout.container.get_children()
children.insert(0, windows)
shell.interact()

