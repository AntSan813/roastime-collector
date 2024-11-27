import sys
import os
import json

from watchdog.events import FileSystemEventHandler
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


# Ensure data directory exists
def is_duplicate_bean(new_bean, beans):
    return any(bean["id"] == new_bean["id"] for bean in beans)


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
        combined_beans[bean["id"]] = {**combined_beans[bean["id"]], **bean}

    return list(combined_beans.values())


def get_roast_profiles():
    if os.path.exists(ROAST_PROFILES_FILE):
        with open(ROAST_PROFILES_FILE, "r") as f:
            return json.load(f)
    else:
        return []


def get_roasts():
    roasts = []
    roast_path = get_roast_path()
    roast_profiles = get_roast_profiles()
    if os.path.exists(roast_path):
        roast_files = [f for f in os.listdir(roast_path)]
        for roast_file in roast_files:
            roast_file_path = os.path.join(roast_path, roast_file)
            try:
                with open(roast_file_path, "r") as f:
                    roast_data_json = json.load(f)
                    roast_data = extract_roast_data(roast_data_json)

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
            except FileNotFoundError:
                print(f"File not found: {roast_file_path}")
                continue
            except json.JSONDecodeError:
                print(f"Invalid JSON format in file: {roast_file_path}")
                continue
            except Exception as e:
                print(f"Error reading file {roast_file_path}: {e}")
                continue

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
                print(f"Error reading bean file {bean_file_path}: {e}")
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


def get_base_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


# file system event handler for data directory
class DataFileHandler(FileSystemEventHandler):
    def __init__(self, beans, roast_profiles):
        self.beans = beans
        self.roast_profiles = roast_profiles

    def on_modified(self, event):
        if event.src_path == BEANS_FILE:
            self.beans.clear()
            self.beans.extend(get_beans())
        elif event.src_path == ROAST_PROFILES_FILE:
            self.roast_profiles.clear()
            self.roast_profiles.extend(get_roast_profiles())
