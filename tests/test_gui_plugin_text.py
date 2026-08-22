import ast
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import gui


class MockWindow(dict):
  def __init__(self, values: dict):
    super().__init__(values)
    self.visibility_changed = Mock()


class PluginTextTests(unittest.TestCase):
  def test_every_enabled_plugin_declares_edit_support(self) -> None:
    unsupported = []
    plugins_path = Path(__file__).parents[1] / "modbuilder" / "plugins"
    for plugin_path in plugins_path.glob("*.py"):
      tree = ast.parse(plugin_path.read_text(encoding="utf-8"))
      debug = None
      has_options = False
      has_loader = False
      for node in tree.body:
        if isinstance(node, ast.Assign):
          assigned_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
          if "DEBUG" in assigned_names:
            debug = ast.literal_eval(node.value)
          has_options = has_options or "OPTIONS" in assigned_names
        elif isinstance(node, ast.FunctionDef) and node.name == "load_options":
          has_loader = True
      if debug is False and not (has_options or has_loader):
        unsupported.append(plugin_path.stem)

    self.assertEqual(unsupported, [])

  def test_show_mod_options_only_updates_the_previous_and_selected_plugins(self) -> None:
    previous = Mock()
    selected = Mock()
    unrelated = Mock()
    options = types.SimpleNamespace(metadata="previous_plugin")
    window = {
      "options": options,
      "previous_plugin": previous,
      "selected_plugin": selected,
      "unrelated_plugin": unrelated,
    }

    gui._show_mod_options("Selected Plugin", window)

    previous.update.assert_called_once_with(visible=False)
    selected.update.assert_called_once_with(visible=True)
    unrelated.update.assert_not_called()
    self.assertEqual(options.metadata, "selected_plugin")

  def test_plugin_names_are_published_only_after_layouts_are_attached(self) -> None:
    calls = []
    modification = Mock()
    modification.metadata = []
    modification.update.side_effect = lambda **_kwargs: calls.append("publish_names")
    options_widget = types.SimpleNamespace(
      winfo_height=lambda: 500,
      config=lambda **_kwargs: calls.append("restore_height"),
    )
    window = MockWindow({
      "modification": modification,
      "options": types.SimpleNamespace(Widget=options_widget),
    })
    window.refresh = Mock()
    window.extend_layout = Mock(side_effect=lambda *_args: calls.append("attach_layouts"))
    window.set_icon = Mock()
    plugin = types.SimpleNamespace(NAME="Example Plugin")

    with (
      patch.object(gui.mods, "load_mods"),
      patch.object(gui.mods, "MODS_LIST", {"example_plugin": plugin}),
      patch.object(gui, "_get_mod_options", return_value=[["layout"]]),
    ):
      gui._get_mods(window)

    self.assertLess(calls.index("attach_layouts"), calls.index("publish_names"))
    modification.update.assert_called_once_with(values=["Example Plugin"], value="")
    self.assertEqual(modification.metadata, ["Example Plugin"])

  def test_plugin_text_preserves_newlines_and_blank_lines(self) -> None:
    self.assertEqual(
      gui._wrap_plugin_text("First line.\n\nSecond line."),
      "First line.\n\nSecond line.",
    )

  def test_plugin_text_wraps_each_explicit_line_independently(self) -> None:
    first_line = "word " * 40
    wrapped = gui._wrap_plugin_text(f"{first_line}\nFinal line.")

    self.assertTrue(wrapped.endswith("\nFinal line."))
    self.assertGreater(wrapped.count("\n"), 1)

  def test_plugin_links_require_a_label_and_web_url(self) -> None:
    self.assertTrue(gui._valid_plugin_link({
      "label": "Instructions",
      "url": "https://example.com/article",
    }))
    self.assertFalse(gui._valid_plugin_link({
      "label": "Local file",
      "url": "file:///tmp/article.html",
    }))
    self.assertFalse(gui._valid_plugin_link({"url": "https://example.com/article"}))

  def test_plugin_link_event_opens_its_metadata_url(self) -> None:
    event = f"{gui.PLUGIN_LINK_EVENT_PREFIX}example__0"
    element = types.SimpleNamespace(metadata="https://example.com/article")
    window = {event: element}

    with patch.object(gui.webbrowser, "open") as open_browser:
      gui._open_plugin_link(window, event)

    open_browser.assert_called_once_with("https://example.com/article")

  def test_edit_selected_mod_loads_options_and_switches_tabs(self) -> None:
    listbox = types.SimpleNamespace(get_indexes=lambda: (0,))
    modification = Mock()
    add_button = Mock()
    options_column = Mock()
    tab_widget = Mock()
    add_tab_widget = object()
    window = MockWindow({
      "selected_mods": listbox,
      "modification": modification,
      "add_mod": add_button,
      "options": options_column,
      "modbuilder_tab_group": types.SimpleNamespace(Widget=tab_widget),
      "add_mod_tab": types.SimpleNamespace(Widget=add_tab_widget),
    })
    plugin = types.SimpleNamespace(NAME="Editable Plugin", load_options=Mock())
    selected_mods = {"editable_plugin": {"rows": {}}}

    with patch.object(gui.mods, "get_mod", return_value=plugin), patch.object(gui, "_show_mod_options") as show_options:
      gui._edit_selected_mod(selected_mods, window)

    modification.update.assert_called_once_with("Editable Plugin")
    show_options.assert_called_once_with("Editable Plugin", window)
    plugin.load_options.assert_called_once_with(window, selected_mods["editable_plugin"])
    add_button.update.assert_called_once_with(disabled=False)
    tab_widget.select.assert_called_once_with(add_tab_widget)

  def test_edit_selected_options_plugin_uses_generic_widget_loader(self) -> None:
    listbox = types.SimpleNamespace(get_indexes=lambda: (0,))
    window = MockWindow({
      "selected_mods": listbox,
      "modification": Mock(),
      "add_mod": Mock(),
      "options": Mock(),
      "modbuilder_tab_group": types.SimpleNamespace(Widget=Mock()),
      "add_mod_tab": types.SimpleNamespace(Widget=object()),
    })
    plugin = types.SimpleNamespace(NAME="Options Plugin", OPTIONS=[{"name": "Value"}])
    selected_mods = {"options_plugin": {"value": 5}}

    with (
      patch.object(gui.mods, "get_mod", return_value=plugin),
      patch.object(gui, "_show_mod_options"),
      patch.object(gui, "load_option_values") as load_values,
    ):
      gui._edit_selected_mod(selected_mods, window)

    load_values.assert_called_once_with(window, "options_plugin", plugin.OPTIONS, selected_mods["options_plugin"])

  def test_mod_conflicts_include_matching_store_and_ammo_categories(self) -> None:
    selected_mods = {
      "modify_store_weapon": {"type": "weapon", "discount": 25},
      "modify_store_weapon_308": {
        "type": "weapon",
        "name": "weapon_308",
        "display_name": ".308 Rifle",
      },
      "modify_store_scope_4x8": {
        "type": "sight",
        "name": "scope_4x8",
        "display_name": "4-8x Scope",
      },
      "modify_ammo_type_rifle": {"type": "rifle"},
      "modify_ammo_ammo_308": {"type": "rifle", "name": ".308 Soft Point"},
      "modify_ammo_ammo_arrow": {"type": "bow", "name": "Broadhead Arrow"},
    }

    conflicts = gui._get_mod_conflicts(selected_mods)

    self.assertEqual(conflicts, [
      'Modify Store: the "Weapon" category and ".308 Rifle"',
      'Modify Ammo: the "Rifle" category and ".308 Soft Point"',
    ])

  def test_mod_conflicts_include_population_plugins(self) -> None:
    selected_mods = {
      "increase_reserve_population": {"population_multiplier": 2},
      "modify_animal_population_0_red_deer": {"reserve_id": 0, "species_id": 1},
    }

    self.assertEqual(gui._get_mod_conflicts(selected_mods), [
      "Increase Reserve Population and Modify Animal Population"
    ])

  def test_mod_conflicts_ignore_non_overlapping_categories(self) -> None:
    selected_mods = {
      "modify_store_weapon": {"type": "weapon", "discount": 25},
      "modify_store_scope_4x8": {"type": "sight", "name": "scope_4x8"},
      "modify_ammo_type_rifle": {"type": "rifle"},
      "modify_ammo_ammo_arrow": {"type": "bow", "name": "Broadhead Arrow"},
    }

    self.assertEqual(gui._get_mod_conflicts(selected_mods), [])

  def test_conflict_confirmation_can_cancel_the_build(self) -> None:
    selected_mods = {
      "increase_reserve_population": {"population_multiplier": 2},
      "modify_animal_population_0_red_deer": {"reserve_id": 0, "species_id": 1},
    }

    with patch.object(gui, "_show_mod_conflicts_popup", return_value=False) as popup:
      self.assertFalse(gui._confirm_mod_conflicts(selected_mods))

    popup.assert_called_once()

  def test_conflict_confirmation_is_skipped_without_conflicts(self) -> None:
    with patch.object(gui, "_show_mod_conflicts_popup") as popup:
      self.assertTrue(gui._confirm_mod_conflicts({"increase_reserve_population": {}}))

    popup.assert_not_called()

  def test_finalize_hooks_run_after_plugin_processing(self) -> None:
    first = types.SimpleNamespace(finalize=Mock())
    second = types.SimpleNamespace()
    selected_mods = {
      "first": {"value": 1},
      "second": {"value": 2},
    }

    with patch.object(gui.mods, "get_mod", side_effect=[first, second]):
      gui._finalize_mods(selected_mods)

    first.finalize.assert_called_once_with(selected_mods["first"])

  def test_get_files_takes_precedence_over_file(self) -> None:
    plugin = types.SimpleNamespace(
      FILE="single.bin",
      get_files=Mock(return_value=["first.bin", "second.bin"]),
    )

    with (
      patch.object(gui.mods, "copy_all_files_to_mod", return_value=["first.bin", "second.bin"]) as copy_all,
      patch.object(gui.mods, "copy_files_to_mod") as copy_single,
    ):
      copied = gui._copy_mod_files(plugin, {"setting": 1})

    plugin.get_files.assert_called_once_with({"setting": 1})
    copy_all.assert_called_once_with(["first.bin", "second.bin"])
    copy_single.assert_not_called()
    self.assertEqual(copied, ["first.bin", "second.bin"])

  def test_none_from_get_files_falls_back_to_file(self) -> None:
    plugin = types.SimpleNamespace(FILE="single.bin", get_files=Mock(return_value=None))

    with patch.object(gui.mods, "copy_files_to_mod", return_value=["single.bin"]) as copy_single:
      copied = gui._copy_mod_files(plugin, {})

    copy_single.assert_called_once_with("single.bin")
    self.assertEqual(copied, ["single.bin"])


if __name__ == "__main__":
  unittest.main()
