import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import widgets


class WidgetEditingTests(unittest.TestCase):
  def test_load_option_values_supports_every_create_option_widget_style(self) -> None:
    definitions = [
      {"name": "Plain Slider", "min": 0, "max": 10, "initial": 1, "increment": 1},
      {"name": "Plain Input", "min": 0, "max": 10, "initial": 1},
      {"name": "Inline Input", "style": "inline", "min": 0, "initial": 1},
      {"name": "Inline Boolean", "style": "inline", "min": False, "initial": False},
      {"name": "Choice", "style": "list", "min": 0, "initial": ["One", "Two"]},
      {"name": "Styled Slider", "style": "slider", "min": 0, "max": 10, "initial": 1, "increment": 1},
      {"name": "Boolean", "style": "boolean", "min": False, "initial": False},
      {"name": "Many", "style": "listbox", "values": ["A", "B", "C"], "size": 3},
      {"title": "Section"},
    ]
    saved = {
      "plain_slider": 8,
      "plain_input": 7,
      "inline_input": 6,
      "inline_boolean": True,
      "choice": "Two",
      "styled_slider": 5,
      "boolean": True,
      "many": ["A", "C"],
    }
    elements = {f"example__{key}": Mock() for key in saved}

    widgets.load_option_values(elements, "example", definitions, saved)

    for key, value in saved.items():
      if key == "many":
        elements[f"example__{key}"].update.assert_called_once_with(set_to_index=[0, 2])
      else:
        elements[f"example__{key}"].update.assert_called_once_with(value)

  def test_explicit_option_key_decouples_saved_key_from_label(self) -> None:
    definition = {"name": "Friendly Display Label", "key": "stable_saved_key", "style": "boolean", "initial": False, "min": False}
    element = Mock()

    self.assertEqual(widgets.option_key(definition), "stable_saved_key")
    widgets.load_option_values(
      {"example__stable_saved_key": element},
      "example",
      [definition],
      {"stable_saved_key": True},
    )

    element.update.assert_called_once_with(True)

  def test_boolean_option_can_disable_related_widgets(self) -> None:
    definition = {
      "name": "Use Automatic Values",
      "key": "automatic",
      "style": "boolean",
      "initial": False,
      "min": False,
      "disables": ["manual_one", "manual_two"],
    }
    first = Mock()
    second = Mock()
    window = {
      "example__automatic": Mock(),
      "example__manual_one": first,
      "example__manual_two": second,
    }

    widgets.handle_option_event(
      "example__automatic",
      window,
      {"example__automatic": True},
      "example",
      [definition],
    )

    first.update.assert_called_once_with(disabled=True)
    second.update.assert_called_once_with(disabled=True)

  def test_disabled_slider_changes_and_restores_its_trough_color(self) -> None:
    class SliderWidget:
      def __init__(self):
        self.trough_color = "theme-brown"

      def cget(self, option):
        self.assert_option = option
        return self.trough_color

      def configure(self, **kwargs):
        self.trough_color = kwargs["troughcolor"]

    slider_widget = SliderWidget()
    slider = SimpleNamespace(Widget=slider_widget)

    widgets._update_disabled_slider_appearance(slider, True)
    self.assertEqual(slider_widget.trough_color, widgets.DISABLED_SLIDER_TROUGH_COLOR)

    widgets._update_disabled_slider_appearance(slider, False)
    self.assertEqual(slider_widget.trough_color, "theme-brown")


if __name__ == "__main__":
  unittest.main()
