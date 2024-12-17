import textwrap, math, inspect
from modbuilder import __version__, logo, mods, party
from modbuilder.widgets import create_option, valid_option_value
import FreeSimpleGUI as sg

DEFAULT_FONT = "_ 14"
TEXT_WRAP = 142
MOD_LIST = mods.list_mods()

def _mod_name_to_key(name: str) -> str:
  if name is None:
    return ""
  return mods.get_mod_key_from_name(name)

def _get_mod_options() -> list[dict]:
  possible_mods = mods.get_mods()
  options = []
  for mod_key, mod in possible_mods.items():
    mod_details = []
    mod_details.append([sg.T("Description:", p=(10, 10), font="_ 14 underline", text_color="orange")])
    mod_details.append([sg.T(textwrap.fill(mod.DESCRIPTION, TEXT_WRAP), p=(10,0))])

    if hasattr(mod, "WARNING"):
      warning_header = sg.T("WARNING", font="_ 14", text_color="red", p=(10, 10), background_color="black")
      warning = sg.T(textwrap.fill(mod.WARNING, TEXT_WRAP), p=(10,0))
      mod_details.append([warning_header])
      mod_details.append([warning])

    if hasattr(mod, "PRESETS"):
      mod_details.append([sg.T("Presets:", font="_ 14 underline", text_color="orange", p=((10,10),(10,0)))])
      presets = []
      for preset in mod.PRESETS:
        presets.append(preset["name"])
      mod_details.append([sg.Combo(presets, k=f"preset__{mod_key}", enable_events=True, p=(30,10))])

    mod_details.append([sg.T("Options:", font="_ 14 underline", text_color="orange", p=((10,10),(10,0)))])
    if hasattr(mod, "OPTIONS"):
      for mod_option in mod.OPTIONS:
        mod_name = mod_option['name'] if "name" in mod_option else None
        key = f"{mod_key}__{_mod_name_to_key(mod_name)}"
        mod_details.extend(create_option(mod_option, key))
    else:
      mod_details.append([mod.get_option_elements()])

    options.append([sg.pin(sg.Column(mod_details, k=mod_key, visible=False, expand_y=True, expand_x=True))])
  return options

def _show_mod_options(mod_name: str, window: sg.Window) -> None:
  for mod in MOD_LIST:
    if mod == mod_name:
      window[_mod_name_to_key(mod)].update(visible=True)
    else:
      window[_mod_name_to_key(mod)].update(visible=False)

def _format_selected_mods(selected_mods: dict) -> list[str]:
  formatted_mod_options = []
  for mod_key, mod_options in selected_mods.items():
    mod = mods.get_mod(mod_key)
    if mod is not None:
      try:
        formatted_mod_options.append(mod.format(mod_options))
      except:
        pass
  return formatted_mod_options

def _valid_option_value(mod_option: dict, mod_value: any) -> str:
  return valid_option_value(mod_option, mod_value)

def _enable_mod_button(window: sg.Window) -> None:
  selected_mod_size = len(window["selected_mods"].get_list_values())
  window["build_mod"].update(disabled=(selected_mod_size == 0))
  window["save"].update(disabled=(selected_mod_size == 0))
  window["move_up"].update(disabled=(selected_mod_size == 0))
  window["move_down"].update(disabled=(selected_mod_size == 0))

def _create_party() -> None:
  layout = [
    [sg.Image(party.value), sg.Column([
      [sg.T("Your mods have successfully been created!", font="_ 20")],
      [sg.T(mods.APP_DIR_PATH / "mod", text_color="orange")],
      [sg.T(textwrap.fill("You can either load new mods to the dropzone folder or you can replace the dropzone folder.", 60))],
      [sg.VPush()],
      [sg.Push(), sg.Button("Load", k="load"), sg.Button("Replace", k="load_replace"), sg.Button("Close")]
    ], expand_x=True, expand_y=True)]
  ]

  window = sg.Window("Mod Created", layout, modal=True, icon=logo.value, font=DEFAULT_FONT)

  while True:
    event, _values = window.read()
    if event == sg.WIN_CLOSED or event == "Close":
      break
    if event == "load":
      try:
        mods.load_dropzone()
        sg.PopupQuickMessage("Mods Loaded", font="_ 28", background_color="brown")
        break
      except Exception as ex:
        sg.Popup(ex, title="Error", icon=logo.value, font=DEFAULT_FONT)
    if event == "load_replace":
      try:
        mods.load_replace_dropzone()
        sg.PopupQuickMessage("Mods Replaced", font="_ 28", background_color="brown")
        break
      except Exception as ex:
        sg.Popup(ex, title="Error", icon=logo.value, font=DEFAULT_FONT)
  window.close()

def _show_load_mod_list() -> None:
  saved_mod_lists = mods.load_saved_mod_lists()
  selected_mods_list = []
  layout = [
    [sg.T("Saved Mod Lists", font="_ 18")],
    [sg.Listbox(saved_mod_lists, expand_x=True, expand_y=True, k="saved_mod_lists", enable_events=True)],
    [sg.Button("Delete", k="delete", disabled=True), sg.Push(), sg.Button("Cancel", k="cancel"), sg.Button("Merge", k="merge", disabled=True), sg.Button("Load", k="load", disabled=True)],
    [sg.ProgressBar(100, orientation="h", k="load_progress", expand_x=True, s=(10,20))]
  ]
  window = sg.Window("Load Saved Mod List", layout, modal=True, size=(600, 300), icon=logo.value, font=DEFAULT_FONT)
  loaded_saved_mods = None
  merge = False

  while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "cancel":
      break
    if event == "delete":
      delete_confirm = sg.PopupOKCancel("Are you sure you want to delete these saved modifications?", title="Delete Confirm", icon=logo.value, font=DEFAULT_FONT)
      if delete_confirm == "OK":
        mods.delete_saved_mod_list(values["saved_mod_lists"][0])
        window["saved_mod_lists"].update(mods.load_saved_mod_lists())
        window["delete"].update(disabled=True)
        window["load"].update(disabled=True)
        window["merge"].update(disabled=True)
    elif event == "saved_mod_lists":
      if len(values["saved_mod_lists"]) == 0:
        continue
      window["delete"].update(disabled=False)
      window["load"].update(disabled=False)
      window["merge"].update(disabled=False)
    elif event == "load" or event == "merge":
      selected_mods_list = values["saved_mod_lists"][0]
      loaded_saved_mods = _load_and_validate_saved_mods(selected_mods_list, window)
      merge = event == "merge"
      break
  window.close()
  return (merge, loaded_saved_mods, selected_mods_list)

def _load_and_validate_saved_mods(mod_list_name: str, window: sg.Window) -> dict:
  loaded_mods_json = mods.load_saved_mod_list(mod_list_name)
  version = loaded_mods_json.get("version", "0.0.0")
  imported_mods = mods.validate_saved_mod_list(loaded_mods_json, version)
  loaded_mods_list = imported_mods["load"]
  if imported_mods["remove"]:
    imported_mods["remove"] = _handle_unsupported_mods(imported_mods, mod_list_name)
  if imported_mods["update"]:
    updated_mods = _handle_updating_mods(imported_mods, mod_list_name, version, window)
    loaded_mods_list.update(updated_mods)
  return loaded_mods_list

def _handle_unsupported_mods(imported_mods: dict, mod_list_name: str) -> dict:
  formatted_mods_list = "".join(f"\n - {mods.format_mod_display_name(mod_key, mod_options)}" for mod_key, mod_options in imported_mods["remove"].items())
  remove_confirm = sg.popup_scrolled(f"The following mods are disabled and cannot be loaded. Do you want to remove them from the save file?\n{formatted_mods_list}", title=f"Unsupported mod configuration", icon=logo.value, yes_no=True, font=DEFAULT_FONT)
  if remove_confirm == "Yes":
    mods_to_keep = imported_mods["load"] | imported_mods["update"]
    mods.save_mod_list(mods_to_keep, mod_list_name)
    return {}
  return imported_mods["remove"]

def _handle_updating_mods(imported_mods: dict, mod_list_name: str, version: str, window: sg.Window) -> dict:
  updated_mods = {}
  update_errors = {}
  mods_count = len(imported_mods["update"])
  plural_s = "s" if mods_count > 1 else ""
  formatted_mods_list = "".join(f"\n - {mods.format_mod_display_name(mod_key, mod_options)}" for mod_key, mod_options in imported_mods["update"].items())
  update_confirm = sg.popup_scrolled(f"Outdated configuration found for {mods_count} mod{plural_s}. Press OK to update the configuration{plural_s} automatically:\n{formatted_mods_list}", title=f"Outdated mod configuration", icon=logo.value, font=DEFAULT_FONT)
  if update_confirm == "OK":
    step = 1
    progress_step = 100 / mods_count
    for mod_key, mod_options in imported_mods["update"].items():
      try:
        updated_key, updated_options = mods.update_saved_mod_configuration(mod_key, mod_options, version)
        updated_mods[updated_key] = updated_options
      except ValueError as e:
        update_errors.update({mods.format_mod_display_name(mod_key, mod_options): e})
      load_progress = math.floor(step * progress_step)
      window["load_progress"].update(load_progress)
      step += 1
    if update_errors:
      _show_update_errors(update_errors, updated_mods)
    elif updated_mods:
      update_confirm = sg.popup_yes_no(f"Updated all mods successfully!\n\nDo you want to update the save file?", title=f"Update success!", icon=logo.value, font=DEFAULT_FONT)
      if update_confirm == "Yes":
        mods_to_keep = imported_mods["load"] | updated_mods | imported_mods["remove"]
        mods.save_mod_list(mods_to_keep, mod_list_name)
        sg.popup_quick_message("Modifications Saved", font="_ 28", background_color="brown")
  return updated_mods

def _show_update_errors(update_errors: dict, updated_mods: dict):
  formatted_errors = "".join(f"\n - {key}: {value}" for key, value in update_errors.items())
  sg.popup_scrolled(f"Update failed!\nThe following mods could not be loaded. Please recreate them with updated settings.\n\nThe save file has NOT been modified.\n{formatted_errors}", title=f"ERROR: Update failed!", icon=logo.value, font=DEFAULT_FONT)
  if updated_mods:
    formatted_mods_list = "".join(f"\n - {mods.format_mod_display_name(mod_key, mod_options)}" for mod_key, mod_options in updated_mods.items())
    sg.popup_scrolled(f"The following mods were updated successfully and will be loaded.\n\nThe save file has NOT been modified.\n{formatted_mods_list}", title=f"Update success!", icon=logo.value, font=DEFAULT_FONT)

def _move_mods(selected_mods: dict, listbox: sg.Listbox, direction: int) -> dict:
  selected_mod_indices = sorted(list(listbox.get_indexes()), reverse=(direction == 1))  # reverse if moving down the list
  if not selected_mod_indices:
    return selected_mods
  listbox_values = listbox.get_list_values()
  index_map = list(range(len(listbox_values)))
  new_selected_indicies = []

  for index in selected_mod_indices:
    new_index = index + direction
    if (
      new_index < 0  # cannot move above first position
      or new_index >= len(listbox_values)  # cannot move below last position
      or new_index in new_selected_indicies  # cannot move to a position an item has already moved to
    ):
      # example: move items 0,1,3 up the list
      # - 0 cannot move up
      # - 1 cannot move up because 0 was also selected and couldn't move
      # - 3 is moved up to 2
      new_selected_indicies.append(index)
      continue
    # Reorder the resulting mod indicies
    index_map[index], index_map[new_index] = index_map[new_index], index_map[index]
    new_selected_indicies.append(new_index)
  # Reorder the mods list based on the new index_map
  mod_keys = list(selected_mods.keys())
  selected_mods = {mod_keys[i]: selected_mods[mod_keys[i]] for i in index_map}
  updated_values = [listbox_values[i] for i in index_map]
  # Update the listbox and preserve scrollbar position
  scroll_position = listbox.TKListbox.yview()
  listbox.update(values=updated_values, set_to_index=new_selected_indicies)
  listbox.TKListbox.yview_moveto(scroll_position[0])
  return selected_mods

def _delete_mods(selected_mods: dict, listbox: sg.Listbox) -> dict:
  selected_mod_indicies = list(listbox.get_indexes())
  if not selected_mod_indicies:
    return selected_mods
  listbox_values = listbox.get_list_values()
  mod_keys = list(selected_mods.keys())
  for index in sorted(selected_mod_indicies, reverse=True):  # delete end-to-start so we don't mess up the list
    del listbox_values[index]  # delete from listbox
    del selected_mods[mod_keys[index]]  # delete from mods dict
  listbox.update(values=listbox_values)
  return selected_mods

def main() -> None:
  sg.theme("DarkAmber")
  sg.set_options({ "font": DEFAULT_FONT })

  selected_mods = {}
  loaded_mod_list_name = ""
  mod_options = _get_mod_options()
  change_path_text = "(change path)" if mods.get_dropzone() else "(set path)"

  layout = [
    [
      sg.Image(logo.value),
      sg.Column([
        [sg.T("Mod Builder - Revived", expand_x=True, font="_ 24")],
        [
          sg.T(mods.get_dropzone(), font="_ 12", k="game_path"),
          sg.T(change_path_text, font="_ 12 underline", text_color="orange", enable_events=True, k="change_path")
        ],
      ]),
      sg.Push(),
      sg.T(f"Version: {__version__}", font="_ 12", p=((0,0),(0,60)))
    ],
    [
      sg.TabGroup([[
        sg.Tab("Add Modification", [
          [
            sg.Column([
              [sg.T("Mod:", p=((18, 10), (10,0)), font="_ 14 underline", text_color="orange"), sg.Combo(MOD_LIST, k="modification", metadata=mods.list_mod_files(), enable_events=True, p=((0, 0), (10, 0)))],
              [sg.Column(mod_options, p=(0,0), k="options", expand_y=True, expand_x=True, scrollable=True, vertical_scroll_only=True)],
              [sg.Button("Add Modification", k="add_mod", button_color=f"{sg.theme_element_text_color()} on brown", disabled=True, expand_x=True)]
            ], k="mod_col", expand_y=True, expand_x=True, p=((0,0), (10,0))),
          ],
        ]),
        sg.Tab("Build Modifications (0)", [
          [
            sg.Column([
                [sg.Listbox([], expand_x=True, k="selected_mods", enable_events=True, expand_y=True, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)],
                [
                  sg.Button("Save", k="save", button_color=f"{sg.theme_element_text_color()} on brown", disabled=True),
                  sg.Button("Load", k="load", button_color=f"{sg.theme_element_text_color()} on brown"),
                  sg.Button("▲", k="move_up", button_color=f"{sg.theme_element_text_color()} on brown", disabled=True),
                  sg.Button("▼", k="move_down", button_color=f"{sg.theme_element_text_color()} on brown", disabled=True),
                  sg.Push(),
                  sg.Button("Remove", k="remove_mod", button_color=f"{sg.theme_element_text_color()} on brown", disabled=True)
                ],
                [sg.Button("Build Modifications", k="build_mod", button_color=f"{sg.theme_element_text_color()} on brown", expand_x=True, disabled=True)]
            ], k="selected_col", expand_x=True, expand_y=True, p=((0,0), (0,0))),
          ]
        ], k="build_tab")
      ]], expand_x=True, expand_y=True)
    ],
    [
      sg.ProgressBar(100, orientation="h", k="build_progress", expand_x=True, s=(10,20))
    ]
  ]

  window = sg.Window("COTW: Mod Builder - Revived", layout, resizable=True, font=DEFAULT_FONT, icon=logo.value, size=(1300, 800), finalize=True)

  while True:
    event, values = window.read()
    # print(event)
    if event == sg.WIN_CLOSED:
      break
    if event == "modification":
      mod_name = values["modification"]
      mod_key = _mod_name_to_key(mod_name)
      mod = mods.get_mod(mod_key)
      _show_mod_options(mod_name, window)
      window["add_mod"].update(disabled=False)
      window.visibility_changed()
      window["options"].contents_changed()
    elif event == "add_mod":
      mod_options = {}
      is_invalid = None

      if hasattr(mod, "add_mod"):
        result = mod.add_mod(window, values)
        is_invalid = result["invalid"]
        if not is_invalid:
          mod_options = result["options"]
          mod_key = result["key"]
      else:
        for key, value in values.items():
          if isinstance(key, str) and mod_key in key:
            option_key = key.split("__")[1]
            invalid_result = _valid_option_value(mods.get_mod_option(mod_key, option_key), value)
            if invalid_result is None:
              mod_options[option_key] = value
            else:
              is_invalid = invalid_result
              break

      if is_invalid is None:
        selected_mods[mod_key] = mod_options
        formatted_mods_list = _format_selected_mods(selected_mods)
        window["selected_mods"].update(formatted_mods_list)
        _enable_mod_button(window)
        sg.PopupQuickMessage("Mod Added", font="_ 28", background_color="brown")
        window["build_tab"].update(title=f"Build Modifications ({len(formatted_mods_list)})")
      else:
        sg.PopupOK(is_invalid, icon=logo.value, title="Error", font=DEFAULT_FONT)
    elif event == "selected_mods":
      if len(values["selected_mods"]) == 0:
        continue
      window["remove_mod"].update(disabled=False)
    elif event == "move_up":
      selected_mods = _move_mods(selected_mods, window["selected_mods"], -1)
    elif event == "move_down":
      selected_mods = _move_mods(selected_mods, window["selected_mods"], 1)
    elif event == "remove_mod":
      selected_mods = _delete_mods(selected_mods, window["selected_mods"])
      window["build_tab"].update(title=f"Build Modifications ({len(selected_mods.keys())})")
      window["remove_mod"].update(disabled=True)
      _enable_mod_button(window)
    elif event == "build_mod":
      window["build_mod"].update(disabled=True)
      mods.clear_mod()
      mod_files = []
      step = 1
      progress_step = 95 / len(selected_mods.keys())
      for mod_key, mod_options in selected_mods.items():
        mod = mods.get_mod(mod_key)
        if hasattr(mod, "FILE"):
          modded_files = mods.copy_files_to_mod(mod.FILE)
        else:
          modded_files = mods.copy_all_files_to_mod(mod.get_files(mod_options))
        mod_files += modded_files
        mods.apply_mod(mod, mod_options)

        if hasattr(mod, "merge_files"):
          merge_params = inspect.signature(mod.merge_files).parameters
          if len(merge_params) == 2:
            mod.merge_files(modded_files, mod_options)
          else:
            mod.merge_files(modded_files)
        step_progress = math.floor(step * progress_step)
        window["build_progress"].update(step_progress)
        step += 1

      mods.merge_files(mod_files)
      mods.package_mod()
      formatted_mods_list = _format_selected_mods(selected_mods)
      window["selected_mods"].update(formatted_mods_list)
      _enable_mod_button(window)
      window["remove_mod"].update(disabled=True)
      window["build_progress"].update(100)
      _create_party()
      window["build_progress"].update(0)
      window["build_tab"].update(title=f"Build Modifications (0)")
    elif event == "save":
      save_name = sg.PopupGetText("What name would you like use to save modifications?", title="Save Mods", default_text=loaded_mod_list_name, font=DEFAULT_FONT, icon=logo.value)
      if save_name:
        mods.save_mod_list(selected_mods, save_name)
        sg.PopupQuickMessage("Modifications Saved", font="_ 28", background_color="brown")
    elif event == "load":
      merge, saved_mod_list, loaded_mod_list_name = _show_load_mod_list()
      if saved_mod_list:
        selected_mods = selected_mods | saved_mod_list if merge else saved_mod_list
        formatted_mods_list = _format_selected_mods(selected_mods)
        window["selected_mods"].update(formatted_mods_list)
        _enable_mod_button(window)
        sg.PopupQuickMessage("Modifications Loaded", font="_ 28", background_color="brown")
        window["build_tab"].update(title=f"Build Modifications ({len(formatted_mods_list)})")
    elif event == "change_path":
      game_path = sg.PopupGetFolder("Select the game folder (folder with file theHunterCotW_F.exe)", "Game Path", icon=logo.value, font=DEFAULT_FONT)
      if game_path:
        mods.write_dropzone(game_path)
        window["game_path"].update(game_path)
        window["change_path"].update("(change path)")
    elif event.startswith("preset__"):
      presets = mod.PRESETS
      preset_mod_key = _mod_name_to_key(mod.NAME)
      preset_name = values[f"preset__{preset_mod_key}"]
      preset = next((preset for preset in presets if preset["name"] == preset_name), None)
      for option in preset["options"]:
        if "value" in option:
          window[f"{preset_mod_key}__{option['name']}"].update(option["value"])
        else:
          window[f"{preset_mod_key}__{option['name']}"].update(set_to_index = option["values"])
    else:
      mods.delegate_event(event, window, values)

  window.close()

if __name__ == "__main__":
    main()