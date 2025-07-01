"""Interactive CLI interface using Textual."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Static, TextArea

from ..parser.mdx_parser import MDXParseError, MDXParser


class InteractiveApp(App):
    """Interactive MDX to DAX converter application."""

    CSS = """
    .mdx-input {
        border: solid $primary;
        height: 40%;
    }
    
    .dax-output {
        border: solid $success;
        height: 40%;
    }
    
    .explanation {
        border: solid $accent;
        height: 20%;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("f5", "convert", "Convert"),
        Binding("ctrl+s", "save", "Save DAX"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Vertical():
            yield Static("MDX Input:", classes="label")
            yield TextArea(
                placeholder="Enter your MDX query here...",
                id="mdx_input",
                classes="mdx-input",
            )

            with Horizontal():
                yield Button("Convert (F5)", id="convert_btn", variant="primary")
                yield Button("Clear", id="clear_btn")
                yield Button("Save DAX (Ctrl+S)", id="save_btn", variant="success")

            yield Static("Generated DAX:", classes="label")
            yield TextArea(read_only=True, id="dax_output", classes="dax-output")

            yield Static("Explanation:", classes="label")
            yield TextArea(read_only=True, id="explanation", classes="explanation")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "convert_btn":
            self.action_convert()
        elif event.button.id == "clear_btn":
            self.action_clear()
        elif event.button.id == "save_btn":
            self.action_save()

    def action_convert(self) -> None:
        """Convert MDX to DAX."""
        mdx_input = self.query_one("#mdx_input", TextArea)
        dax_output = self.query_one("#dax_output", TextArea)
        explanation = self.query_one("#explanation", TextArea)

        mdx_query = mdx_input.text.strip()
        if not mdx_query:
            dax_output.text = "Error: No MDX query provided"
            explanation.text = ""
            return

        try:
            parser = MDXParser()
            ir_query = parser.parse(mdx_query)

            # Generate DAX and explanation
            dax_query = ir_query.to_dax()
            readable_explanation = ir_query.to_human_readable()

            dax_output.text = dax_query
            explanation.text = readable_explanation

        except MDXParseError as e:
            dax_output.text = f"Parse Error: {e}"
            explanation.text = ""
        except Exception as e:
            dax_output.text = f"Unexpected Error: {e}"
            explanation.text = ""

    def action_clear(self) -> None:
        """Clear all text areas."""
        mdx_input = self.query_one("#mdx_input", TextArea)
        dax_output = self.query_one("#dax_output", TextArea)
        explanation = self.query_one("#explanation", TextArea)

        mdx_input.text = ""
        dax_output.text = ""
        explanation.text = ""

    def action_save(self) -> None:
        """Save DAX output to file."""
        dax_output = self.query_one("#dax_output", TextArea)

        if not dax_output.text.strip():
            return

        # Simple save to current directory
        try:
            with open("output.dax", "w") as f:
                f.write(dax_output.text)
            self.notify("DAX saved to output.dax")
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")
