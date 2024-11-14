import shutil
import sys
import os
from dotenv import load_dotenv
import json

from watchdog.events import FileSystemEventHandler
from .roast_data import extract_roast_data


DATA_DIR = "data"
BEANS_FILE = os.path.join(DATA_DIR, "beans.json")
PROCESSED_ROASTS_FILE = os.path.join(DATA_DIR, "processed_roasts.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv()


def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)


def save_beans(beans):
    with open(BEANS_FILE, "w") as f:
        json.dump(beans, f, indent=4)


def save_processed_roast(roast):
    roasts = get_processed_roasts()
    # Check if roast already exists and override it if it does
    existing_roast = get_roast(roast.id)
    if existing_roast:
        roasts.remove(existing_roast)
        roasts.append(roast)
    else:
        roasts.append(roast)
    with open(PROCESSED_ROASTS_FILE, "w") as f:
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


def bean_from_form(form):
    return {
        "id": form["id"],
        "name": form["name"],
        "origin": form["origin"],
        "region": form["region"],
        "varietal": form["varietal"],
        "processing_method": form["processing_method"],
        "altitude": form["altitude"],
        "taste_notes": form["taste_notes"],
        "aroma": form["aroma"],
        "acidity": form["acidity"],
        "brew_methods": form["brew_methods"],
        "cupping_score": form["cupping_score"],
        "certifications": form["certifications"],
    }


def get_beans():
    if os.path.exists(BEANS_FILE):
        with open(BEANS_FILE, "r") as f:
            return json.load(f)
    else:
        return []


def get_processed_roasts():
    if os.path.exists(PROCESSED_ROASTS_FILE):
        with open(PROCESSED_ROASTS_FILE, "r") as f:
            return json.load(f)
    else:
        return []


def get_all_roasts():
    processed_roasts = get_processed_roasts()
    roast_path = get_roast_path()
    roast_files = [f for f in os.listdir(roast_path)]

    roasts = []
    for roast_file in roast_files:
        roast_file_path = os.path.join(roast_path, roast_file)
        try:
            with open(roast_file_path, "r") as f:
                roast_data_json = json.load(f)
                roast_data = extract_roast_data(roast_data_json)

                # check if roast has been processed
                processed_roast = next(
                    (r for r in processed_roasts if r["id"] == roast_data["id"]), None
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


def get_bean(id):
    beans = get_beans()
    return next((b for b in beans if b["id"] == id), None)


def get_roast(id):
    roasts = get_all_roasts()
    return next((r for r in roasts if r["id"] == id), None)


# file system event handler for data directory
class DataFileHandler(FileSystemEventHandler):
    def __init__(self, beans, processed_roasts):
        self.beans = beans
        self.processed_roasts = processed_roasts

    def on_modified(self, event):
        if event.src_path == BEANS_FILE:
            self.beans.clear()
            self.beans.extend(get_beans())
        elif event.src_path == PROCESSED_ROASTS_FILE:
            self.processed_roasts.clear()
            self.processed_roasts.extend(get_processed_roasts())
