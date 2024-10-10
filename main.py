import shutil
import logging
import json
import time
import sys
import os
import argparse
from dotenv import load_dotenv
import matplotlib

matplotlib.use("Agg")  # Use the Anti-Grain Geometry backend
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from scripts.s3 import upload_to_s3
from scripts.roast_data import extract_roast_data, load_bean_metadata, get_bean_info
from scripts.html_template import generate_qr_code, generate_webpage

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)


def process_roast(file_path, test=False):
    base_url = os.getenv("S3_BASE_URL")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    print(base_url, bucket_name)
    logging.info(f"Processing roast file: {file_path}")

    # first, load the roast data
    with open(file_path, "r", encoding="utf-8") as f:
        roast_data_json = json.load(f)

    # generate unique identifiers for output files
    roast_id = roast_data_json.get("uid", "1")

    # define local directories
    roast_directory = f"roasts/{roast_id}"

    os.makedirs(roast_directory, exist_ok=True)

    # local file paths
    webpage_filename = "index.html"
    webpage_local_path = os.path.join(roast_directory, webpage_filename)

    # get bean metadata
    bean_id = roast_data_json.get("beanId")
    beans_metadata = load_bean_metadata()
    bean_metadata = get_bean_info(bean_id, beans_metadata)

    roast_data = extract_roast_data(roast_data_json)
    merged_data = {**roast_data, **bean_metadata}

    # generate the HTML page
    html_out = generate_webpage(merged_data)

    # save the rendered HTML to the filesystem
    with open(webpage_local_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    # copy assets to the local directory
    assets_directory = os.path.join(roast_directory, "assets")
    os.makedirs(assets_directory, exist_ok=True)
    copy_and_overwrite("template/assets", assets_directory)

    logging.info(f"Webpage saved as {webpage_local_path}")

    if test:
        logging.info(f"Processing of {file_path} completed.")
        return

    # upload files to s3
    webpage_s3_key = f"{roast_directory}/{webpage_filename}"
    # TODO: consider batching uploads
    upload_to_s3(webpage_local_path, bucket_name, webpage_s3_key, "text/html")
    upload_to_s3(
        f"{assets_directory}/chart.js",
        bucket_name,
        f"{assets_directory}/chart.js",
        "application/javascript",
    )
    upload_to_s3(
        f"{assets_directory}/logo.png",
        bucket_name,
        f"{assets_directory}/logo.png",
        "image/png",
    )
    upload_to_s3(
        f"{assets_directory}/styles.css",
        bucket_name,
        f"{assets_directory}/styles.css",
        "text/css",
    )

    # generate QR code
    roast_url = f"{base_url}{roast_directory}/index.html"

    # generate QR code
    qr_codes_directory = os.path.join("qr_codes")
    os.makedirs(qr_codes_directory, exist_ok=True)
    roast_qr_code_filename = f"{roast_id}-qr.png"
    qr_code_local_path = os.path.join(qr_codes_directory, roast_qr_code_filename)
    generate_qr_code(roast_url, qr_code_local_path)

    logging.info(f"Processing of {file_path} completed.")


class RoastFileHandler(FileSystemEventHandler):
    def __init__(self, roast_directory):
        self.roast_directory = roast_directory
        self.processed_files = set()

    def on_created(self, event):
        if not event.is_directory:
            time.sleep(1)  # Wait a moment for the file to be fully written
            file_name = os.path.basename(event.src_path)
            if file_name not in self.processed_files:
                self.processed_files.add(file_name)
                process_roast(event.src_path, False)


def main():
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

    # add argument parser for testing
    parser = argparse.ArgumentParser(
        description="Process roast files and generate HTML pages."
    )
    parser.add_argument(
        "--test",
        help="Process a specific roast file for testing.",
    )
    args = parser.parse_args()

    if args.test:
        file_path = args.test or "/sample_roast_data.json"
        if os.path.isfile(file_path):
            process_roast(file_path, True)
        else:
            logging.error(f"Test file {file_path} does not exist.")
        return  # Exit after processing the test file

    event_handler = RoastFileHandler(roast_path)
    observer = Observer()
    observer.schedule(event_handler, path=roast_path, recursive=False)
    observer.start()
    logging.info(f"Watching directory: {roast_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopping directory watcher.")
    observer.join()


if __name__ == "__main__":
    main()
