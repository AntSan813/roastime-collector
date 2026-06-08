import re
import sys
import os
import json
import logging

from .roast_data import extract_roast_data


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, f"roastprofiler/{relative_path}")


data_dir = resource_path("data")
os.makedirs(data_dir, exist_ok=True)
BEANS_FILE = os.path.join(data_dir, "beans.json")
ROAST_PROFILES_FILE = os.path.join(data_dir, "roast_profiles.json")

# App-owned store for roasts uploaded through the UI (as opposed to roasts read
# live from a local RoastTime install). Files are named by their RoastTime `uid`,
# matching the on-disk convention RoastTime itself uses, so the rest of the code
# can treat both sources identically.
UPLOADED_ROASTS_DIR = os.path.join(data_dir, "roasts")
os.makedirs(UPLOADED_ROASTS_DIR, exist_ok=True)

# RoastTime ids are nanoids ([A-Za-z0-9_-]); validating against this keeps the id
# safe to use as a filename (no path separators / traversal).
ROAST_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def is_valid_roast_id(roast_id):
    return bool(roast_id) and bool(ROAST_ID_RE.match(roast_id))


def save_beans(beans):
    with open(BEANS_FILE, "w") as f:
        json.dump(beans, f, indent=4)


def save_processed_roast(roast):
    roasts = get_roast_profiles()
    roasts = [r for r in roasts if r["id"] != roast["id"]]
    roasts.append(roast)
    with open(ROAST_PROFILES_FILE, "w") as f:
        json.dump(roasts, f, indent=4)


def get_roast_path():
    # find roasttime's local roast folder based on the OS
    # ref: https://github.com/jglogan/roastime-data/blob/main/dump_roasts.py#L266
    if sys.platform.startswith("linux"):
        config_path = os.environ.get(
            "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
        )
    elif sys.platform == "darwin":
        config_path = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support"
        )
    elif sys.platform in ["win32", "cygwin"]:
        config_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    else:
        raise NotImplementedError(f"platform {sys.platform} is not supported")
    roast_path = os.path.join(config_path, "roast-time", "roasts")
    return roast_path


def get_beans_path():
    # Adjust the path according to the Roast-Time application structure
    if sys.platform.startswith("linux"):
        config_path = os.environ.get(
            "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
        )
    elif sys.platform == "darwin":
        config_path = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support"
        )
    elif sys.platform in ["win32", "cygwin"]:
        config_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    else:
        raise NotImplementedError(f"platform {sys.platform} is not supported")
    beans_path = os.path.join(config_path, "roast-time", "beans")
    return beans_path


def bean_from_form(form):
    fields = [
        "id",
        "name",
        "aroma",
        "grade",
        "origin",
        "region",
        "acidity",
        "varietal",
        "altitude",
        "taste_notes",
        "description",
        "harvest_date",
        "purchase_url",
        "brew_methods",
        "cupping_score",
        "certifications",
        "processing_method",
    ]
    return {field: form.get(field) for field in fields}


def get_beans():
    beans = []
    if os.path.exists(BEANS_FILE):
        with open(BEANS_FILE, "r") as f:
            try:
                beans = json.load(f)
            except json.JSONDecodeError:
                beans = []
    else:
        beans = []

    roastime_beans = load_roastime_beans()

    combined_beans = {bean["id"]: bean for bean in roastime_beans}
    for bean in beans:
        bean_id = bean.get("id")
        if bean_id in combined_beans:
            # overlay the app's saved fields on top of the RoastTime bean
            combined_beans[bean_id] = {**combined_beans[bean_id], **bean}
        else:
            # bean exists only in beans.json (e.g. registered while RoastTime
            # isn't installed) — keep it instead of raising a KeyError
            combined_beans[bean_id] = bean

    return list(combined_beans.values())


def get_roast_profiles():
    if os.path.exists(ROAST_PROFILES_FILE):
        with open(ROAST_PROFILES_FILE, "r") as f:
            return json.load(f)
    else:
        return []


def _list_roast_files():
    """Yield (source, roast_id, path) for every roast file across both sources.

    Uploaded roasts take precedence over a local RoastTime roast with the same id,
    so a roast that exists in both is reported once, tagged "uploaded". Either
    source may be absent — the app works with uploads only, RoastTime only, or both.
    """
    sources = [
        ("uploaded", UPLOADED_ROASTS_DIR),
        ("roasttime", get_roast_path()),
    ]
    seen = set()
    for source_name, source_path in sources:
        if not source_path or not os.path.exists(source_path):
            continue
        for name in os.listdir(source_path):
            if name == ".DS_Store" or name in seen:
                continue
            seen.add(name)
            yield source_name, name, os.path.join(source_path, name)


def find_roast_file(roast_id):
    """Locate a roast file by id, preferring an uploaded copy over a RoastTime one."""
    for source_path in (UPLOADED_ROASTS_DIR, get_roast_path()):
        if source_path and os.path.exists(source_path):
            candidate = os.path.join(source_path, roast_id)
            if os.path.isfile(candidate):
                return candidate
    return None


def save_uploaded_roast(roast_id, roast_data_json):
    """Persist an uploaded roast's JSON to the app-owned store, named by its id."""
    if not is_valid_roast_id(roast_id):
        raise ValueError(f"Invalid roast id: {roast_id!r}")
    path = os.path.join(UPLOADED_ROASTS_DIR, roast_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(roast_data_json, f)
    return path


def delete_uploaded_roast(roast_id):
    """Remove an uploaded roast. Returns True if a file was deleted."""
    if not is_valid_roast_id(roast_id):
        raise ValueError(f"Invalid roast id: {roast_id!r}")
    path = os.path.join(UPLOADED_ROASTS_DIR, roast_id)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


def get_roasts():
    roasts = []
    roast_profiles = get_roast_profiles()
    for source_name, roast_id, roast_file_path in _list_roast_files():
        try:
            with open(roast_file_path, "r", encoding="utf-8") as f:
                roast_data_json = json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            logging.warning(f"Invalid JSON in roast file: {roast_file_path}")
            continue
        except Exception as e:
            logging.warning(f"Error reading roast file {roast_file_path}: {e}")
            continue

        try:
            roast_data = extract_roast_data(roast_data_json)
        except Exception as e:
            logging.warning(f"Error parsing roast {roast_file_path}: {e}")
            continue

        roast_data["source"] = source_name

        # check if roast has been processed
        processed_roast = next(
            (r for r in roast_profiles if r["id"] == roast_data["id"]), None
        )
        if processed_roast:
            roast_data["is_processed"] = True
            roast_data = {**roast_data, **processed_roast}
        else:
            roast_data["is_processed"] = False
        roasts.append(roast_data)

    return roasts


def load_roastime_beans():
    beans_path = get_beans_path()
    beans = []
    if os.path.exists(beans_path):
        bean_files = [f for f in os.listdir(beans_path)]
        for bean_file in bean_files:
            bean_file_path = os.path.join(beans_path, bean_file)
            try:
                with open(bean_file_path, "r") as f:
                    bean_data = json.load(f)
                    bean = {
                        "id": bean_data.get("uid"),
                        "farm": bean_data.get("farm"),
                        "name": bean_data.get("name"),
                        "region": bean_data.get("region"),
                        "origin": bean_data.get("country"),
                        "altitude": bean_data.get("elevation"),
                        "roasttime": True,
                        "roast_count": bean_data.get("roast_count"),
                        "description": bean_data.get("description"),
                        "certifications": "Organic" if bean_data.get("organic") else "",
                        "processing_method": bean_data.get("process"),
                    }
                    beans.append(bean)
            except Exception as e:
                logging.warning(f"Error reading bean file {bean_file_path}: {e}")
    return beans


def get_bean(bean_id):
    beans = get_beans()
    return next(
        (b for b in beans if b.get("id") == bean_id or b.get("uid") == bean_id), None
    )


def get_roast(id):
    roasts = get_roasts()
    return next((r for r in roasts if r["id"] == id), None)


def get_config():
    config_file = os.path.join(data_dir, "config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    else:
        return {}
