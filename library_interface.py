import library_computation
import bookmarked_pages
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.reactive import reactive
from textual.containers import HorizontalGroup, VerticalScroll,Center
from textual.widgets import Button, Digits, Footer, Header, Log, Placeholder, OptionList,Input,TextArea,Select, Label,Rule
from textual.widgets.option_list import Option
from textual.app import App, ComposeResult
from textual.containers import Container, HorizontalGroup, VerticalGroup, VerticalScroll
from textual.widgets import Button, Digits, Footer, Header
import unicodedata

from textual.theme import Theme

binary_theme = Theme(
    name="binary_theme",
    primary="#7FFF5F",
    secondary="#2F51FF",
    accent="#B48EAD",
    foreground="#FFFFFF",
    background="#000000",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#151515",
    panel="#000000",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)
nonbin_theme = Theme(
    name="nonbin_theme",
    primary="#2F51FF",
    secondary="#2F51FF",
    accent="#B48EAD",
    foreground="#FFFFFF",
    background="#000000",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#151515",
    panel="#000000",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)

class OptionsMenu(VerticalGroup):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = "all"
        self.binary_encoding = False
        self.address = ""
        self.page_text = ""
        self.rendered_text = ""
        self.binary_text = ""
        self.utf_text = ""
        self.search_term = ""
        self.max_length = 1000

    def compose(self) -> ComposeResult:
        yield Center(Button("View as binary", variant = "primary", id="encoding_switch"))

        # display options
        language_options =  OptionList(
            Option("Binary", id="binary"),
            Option("Unicode", id="all"),
            Option("Chinese", id="chinese"),
            Option("Ol Chiki", id="olchiki"),
            Option("Khmer", id="khmer"),
            Option("Cuneiform", id="cuneiform"),
            Option("Egyptian Hieroglyph", id="hieroglyph"),
            Option("ASCII", id="ascii"),
            Option("English", id="english"),
            Option("Geometric", id="geometry"),
            Option("Box Drawing", id="box"), 
            Option("Runic", id="runic"), id="langoptions")
        language_options.border_title = "Language options"
        yield language_options

        # browsing options
        random_page_button = Button("Random page", variant = "primary", id="random_button")

        search_bar = Input(placeholder="Search term", id="search")
        search_bar.border_title = "Search for text"

        bookmarks = Select(((pg, pg) for pg in bookmarked_pages.PAGES.keys()), id="bookmarks")
        bookmarks.border_title = "Pages of interest"

        browsing_menu =  VerticalGroup(Center(random_page_button), search_bar, bookmarks, id="browsing_stuff")
        browsing_menu.border_title = "Browse the library..."
        yield browsing_menu

    def on_option_list_option_selected(self, message: OptionList.OptionSelected) -> None:
        self.lang = message.option_id
        if self.lang != "binary":
            self.binary_encoding = False

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            #self.parent.query_one("#page", Log).write_line(message.value)
            self.search_term = message.value
            self.get_page_content(self.search_term)

    def on_button_pressed(self, event:Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "random_button":
            self.get_page_content("")
        elif button_id == "encoding_switch":
            if self.binary_encoding:
                self.page_text = self.utf_text
            else:
                self.page_text = self.binary_text

            self.binary_encoding = not self.binary_encoding
            self.render_text()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value: 
            page = event.value
            # self.address = "None"
            self.lang = "all"
            self.binary_encoding = False
            self.query_one(OptionList).highlighted = 1
            self.get_page_content(bookmarked_pages.PAGES[page].ljust(self.max_length))
            self.render_text()

    def get_page_content(self, content) -> None:
        if self.lang == "binary":
            length = self.max_length * 32
        else:
            length = self.max_length
        # filling out string with random characters
        content = library_computation.get_full_page(content, language = self.lang, max_length = length)

        # convert to/save as binary
        if self.lang == "binary":
            self.binary_text = content
            self.page_text = self.binary_text
            self.utf_text = library_computation.change_encoding(True, self.page_text)
            self.binary_encoding = True
        else:
            # get full page content (with whitespace padding)
            self.page_text = content
            self.utf_text = self.page_text
            self.binary_text = library_computation.change_encoding(False, self.page_text)
            self.binary_encoding = False

        # save address as location in binary library
        self.address = library_computation.searchByContent(self.binary_text, language="binary", max_length = self.max_length * 32)
        
        # clear the search bar
        self.query_one("#search", Input).clear()

        # print
        self.render_text()
    
    def render_text(self):
        self.rendered_text = []
        for char in self.page_text:
            if library_computation.is_displayable(char):
                self.rendered_text.append(char)
            else:
                self.rendered_text.append('□')
        self.rendered_text = "".join(self.rendered_text)
        
        self.parent.query_one("#page", TextArea).text = self.rendered_text
        self.parent.query_one("#address", TextArea).text = self.address

        # change the css
        if self.binary_encoding:
            self.parent.query_one("#encoding_switch", Button).label = "View as unicode"
            self.app.theme = "binary_theme"
        else:
            self.parent.query_one("#encoding_switch", Button).label = "View as binary"
            self.app.theme = "nonbin_theme"

class LibraryApp(App):
    """A Textual app to display pages from the Library of Babel."""

    CSS_PATH = "library.tcss"
    # BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_mount(self) -> None:
        # Register the theme
        self.register_theme(binary_theme)  
        self.register_theme(nonbin_theme)

        # Set the app's theme
        self.theme = "nonbin_theme"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        #yield HorizontalGroup(OptionsMenu(), Log(id="page"))
        page_area = TextArea("", id="page", classes="binary")
        page_area.border_title = "page"

        address_area = TextArea(id="address")
        address_area.border_title = "library address"

        yield HorizontalGroup(OptionsMenu(id="control", classes="menu"), 
                            VerticalGroup(address_area, page_area, classes="display"))

    def on_ready(self) -> None:
        text_area = self.query_one("#page", TextArea)
        text_area.read_only = True
        control_menu = self.query_one(OptionsMenu)

        control_menu.lang = "all"
        control_menu.binary_encoding = False
        control_menu.get_page_content(bookmarked_pages.PAGES["introduction"])
        #text_area.text = bookmarked_pages.PAGES["introduction"]
        
        #self.query_one("#address", TextArea).text = library_computation.searchByContent(text_area.text, "all", max_length = 1000)
        self.query_one("#address", TextArea).read_only = True

        self.query_one("#page", TextArea).read_only = True
if __name__ == "__main__":
    app = LibraryApp()
    app.run()