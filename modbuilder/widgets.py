import FreeSimpleGUI as sg
import tkinter as tk


DISABLED_SLIDER_TROUGH_COLOR = "white"


def option_key(option: dict | str) -> str:
    if isinstance(option, dict):
        if "key" in option:
            return option["key"]
        option = option["name"]
    return "_".join(option.lower().split(" "))


def create_option(mod_option: dict, key: str) -> list[list]:
    mod_details = []
    if "title" in mod_option:
        mod_details.append([sg.T(mod_option["title"])])
        return mod_details

    if "style" in mod_option:
        mod_option_style = mod_option["style"]
        initial_value = mod_option["initial"] if "initial" in mod_option else mod_option["min"]
        if mod_option_style == "inline":
            if isinstance(mod_option["initial"], bool):
                t = sg.Checkbox(mod_option["name"], p=((30,10),(10,10)), k=key, default = mod_option["initial"], enable_events=bool(mod_option.get("disables")))
                mod_details.append([t])
            else:
                t = sg.T(f"{mod_option['name']}", p=((30,10),(10,10)))
                td = sg.Input(mod_option["initial"], size=22, k=key)
                mod_details.append([t, td])
        elif mod_option_style == "list":
            t = sg.T(f"{mod_option['name']}", p=((30,10),(10,10)))
            td = sg.Combo(mod_option["initial"], k=key, p=((0,20),(10,10)))
            mod_details.append([t, td])
        elif mod_option_style == "slider":
            t = sg.T(f"{mod_option['name']}", p=((30,0),(10,0)))
            td = sg.Slider((mod_option["min"], mod_option["max"]), initial_value, mod_option["increment"], orientation = "h", k = key, p=((80,80),(0,10)), expand_x=True)
            if "note" in mod_option:
                n = sg.T(mod_option['note'], font="_ 12 italic", text_color="orange", p=((10,10),(10,0)))
                mod_details.append([t, n])
            else:
                mod_details.append([t])
            mod_details.append([td])
        elif mod_option_style == "boolean":
            td = sg.Checkbox(
                mod_option["name"],
                initial_value,
                k=key,
                p=((10,0),(0,0)),
                enable_events=bool(mod_option.get("disables")) or mod_option.get("enable_events", False),
            )
            if "note" in mod_option:
                n = sg.T(mod_option['note'], font="_ 12 italic", text_color="orange", p=((10,10),(10,10)))
                mod_details.append([td, n])
            else:
                mod_details.append([td])
        elif mod_option_style == "listbox":
            option_name = sg.T(f"{mod_option['name']}", p=((30,0),(10,10)))
            listbox_values = mod_option["values"]
            listbox = sg.Listbox(
                listbox_values,
                listbox_values,
                k=key,
                s=(None, mod_option["size"]),
                select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                p=((30,30),(10,10))
            )
            mod_details.append([option_name])
            mod_details.append([listbox])
    else:
        t = sg.T(f"{mod_option['name']}", p=((10,10),(10,0)))
        if "default" in mod_option:
            td = sg.T(f"(default: {mod_option['default']}, min: {mod_option['min']}, max: {mod_option['max']})", font="_ 12", p=((0,0),(10,0)))
        else:
            td = sg.T("")

        initial_value = mod_option["initial"] if "initial" in mod_option else mod_option["min"]
        if "min" in mod_option and "max" in mod_option and "increment" in mod_option:
            i = sg.Slider((mod_option["min"], mod_option["max"]), initial_value, mod_option["increment"], orientation = "h", k = key, p=((50,50),(0,0)), expand_x=True)
        else:
            i = sg.Input(initial_value, size=6, k = key, p=((50,0),(10,0)))
        if "note" in mod_option:
            tn = sg.T(mod_option['note'], font="_ 12 italic", text_color="orange", p=((10,10),(10,0)))
            mod_details.append([t, td, tn])
        else:
            mod_details.append([t, td])
        mod_details.append([i])

    return mod_details


def load_option_values(window: sg.Window, mod_key: str, option_definitions: list[dict], saved_options: dict) -> None:
    """Restore saved values for every widget style produced by create_option."""
    for option in option_definitions:
        if "name" not in option or "title" in option:
            continue
        saved_key = option_key(option)
        if saved_key not in saved_options:
            continue
        element = window[f"{mod_key}__{saved_key}"]
        saved_value = saved_options[saved_key]
        if option.get("style") == "listbox":
            selected_values = saved_value if isinstance(saved_value, (list, tuple, set)) else [saved_value]
            selected_indices = [i for i, value in enumerate(option["values"]) if value in selected_values]
            element.update(set_to_index=selected_indices)
        else:
            element.update(saved_value)
    for option in option_definitions:
        if option.get("disables"):
            saved_key = option_key(option)
            source_value = saved_options.get(saved_key, option.get("initial", option.get("min")))
            _update_disabled_options(window, mod_key, option, source_value)


def handle_option_event(event: str, window: sg.Window, values: dict, mod_key: str, option_definitions: list[dict]) -> None:
    prefix = f"{mod_key}__"
    if not isinstance(event, str) or not event.startswith(prefix):
        return
    source_key = event.removeprefix(prefix)
    option = next((definition for definition in option_definitions if "name" in definition and option_key(definition) == source_key), None)
    if option and option.get("disables"):
        _update_disabled_options(window, mod_key, option, values[event])


def _update_disabled_options(window: sg.Window, mod_key: str, source_option: dict, source_value: object) -> None:
    disabled = bool(source_value)
    for target_key in source_option.get("disables", []):
        element = window[f"{mod_key}__{target_key}"]
        element.update(disabled=disabled)
        _update_disabled_slider_appearance(element, disabled)


def _update_disabled_slider_appearance(element: object, disabled: bool) -> None:
    """Give Tk sliders a visible disabled state and restore their theme color when enabled."""
    widget = getattr(element, "Widget", None)
    if widget is None:
        return

    try:
        active_color = getattr(widget, "_modbuilder_active_trough_color", None)
        if active_color is None:
            active_color = widget.cget("troughcolor")
            setattr(widget, "_modbuilder_active_trough_color", active_color)
        widget.configure(
            troughcolor=DISABLED_SLIDER_TROUGH_COLOR if disabled else active_color
        )
    except (AttributeError, TypeError, tk.TclError):
        # Other widget types are fully styled by their normal disabled state.
        return


def valid_option_value(mod_option: dict, mod_value: any) -> str:
    if mod_option is None:
        return None
    if mod_option.get("style") == "boolean":
        if type(mod_value) is bool:
            return None
        return f"Invalid Value: {mod_value} \n\nMust be true or false"
    if "min" not in mod_option:
        return None
    min_value = mod_option["min"]
    max_value = mod_option.get("max")
    mod_type = type(mod_option["initial"]) if "initial" in mod_option else type(min_value)
    original_value = mod_value
    try:
        mod_value = mod_type(mod_value)
        valid = min_value <= mod_value and (max_value is None or mod_value <= max_value)
    except (TypeError, ValueError):
        valid = False
    if valid:
        return None
    return f"Invalid Value: {original_value} \n\nMust be between {min_value} and {max_value}"


def generate_buttons(button_names: list[str]) -> list[sg.Button]:
    button_map = {
        "yes": sg.Yes,
        "no": sg.No,
        "ok": sg.OK,
        "cancel": sg.Cancel,
        "exit": sg.Exit,
        "submit": sg.Submit,
        "quit": sg.Quit,
        "save": sg.Save
    }
    return [button_map[name.lower()]() if name.lower() in button_map else sg.Button(name) for name in button_names]
