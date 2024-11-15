import shutil
import logging
import json
import os
from dotenv import load_dotenv

from .s3 import upload_to_s3
from .roast_data import extract_roast_data
from .html_template import generate_qr_code, generate_webpage
from .utils import get_beans


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def copy_and_overwrite(from_path, to_path):
    if not os.path.exists(to_path):
        os.makedirs(to_path)

    for item in os.listdir(from_path):
        source = os.path.join(from_path, item)
        destination = os.path.join(to_path, item)

        if os.path.isdir(source):
            copy_and_overwrite(source, destination)
        else:
            shutil.copy2(source, destination)


def generate_roast_profile(file_path, roast_id):
    base_url = os.getenv("S3_BASE_URL")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    logging.info(f"Processing roast file: {file_path}/{roast_id}")

    # Load the roast data
    roast_file_path = os.path.join(file_path, roast_id)
    if roast_file_path.endswith(".DS_Store"):
        return

    # first, load the roast data
    try:
        with open(roast_file_path, "r", encoding="utf-8") as f:
            roast_data_json = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logging.error(f"Error reading file {roast_file_path}: {e}")
        return

    # define local directories
    roast_directory = f"roasts/{roast_id}"
    roast_directory_local = f"{CACHE_DIR}/{roast_directory}"

    os.makedirs(roast_directory_local, exist_ok=True)

    # local file paths
    webpage_local_path = os.path.join(roast_directory_local, "index.html")

    # get bean metadata
    bean_id = roast_data_json.get("beanId")
    beans = get_beans()
    # bean_metadata = get_bean_info(bean_id, beans_metadata)
    bean = [bean for bean in beans if bean["id"] == bean_id][0]

    if not bean:
        logging.error(f"Bean ID {bean_id} not found.")
        return

    roast_data = extract_roast_data(roast_data_json)
    merged_data = {**roast_data, **bean}

    # generate the HTML page
    html_out = generate_webpage(merged_data)

    # save the rendered HTML to the filesystem
    with open(webpage_local_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    # copy assets to the local directory
    assets_directory = os.path.join(roast_directory, "assets")
    assets_directory_local = os.path.join(roast_directory_local, "assets")
    os.makedirs(assets_directory_local, exist_ok=True)

    copy_and_overwrite("roast_profile_template/static/js", assets_directory_local)
    copy_and_overwrite("roast_profile_template/static/css", assets_directory_local)
    copy_and_overwrite("roast_profile_template/static/images", assets_directory_local)

    logging.info(f"Webpage saved as {webpage_local_path}")

    # upload files to s3
    webpage_s3_key = f"{roast_directory}/index.html"

    # TODO: consider batching uploads
    upload_to_s3(webpage_local_path, bucket_name, webpage_s3_key, "text/html")
    upload_to_s3(
        f"{assets_directory_local}/chart.js",
        bucket_name,
        f"{assets_directory}/chart.js",
        "application/javascript",
    )
    upload_to_s3(
        f"{assets_directory_local}/logo.png",
        bucket_name,
        f"{assets_directory}/logo.png",
        "image/png",
    )
    upload_to_s3(
        f"{assets_directory_local}/styles.css",
        bucket_name,
        f"{assets_directory}/styles.css",
        "text/css",
    )

    # generate QR code
    roast_url = f"{base_url}{roast_directory}/index.html"

    # generate QR code
    qr_codes_directory = os.path.join("qr_codes")
    qr_codes_directory_local = os.path.join(CACHE_DIR, qr_codes_directory)
    os.makedirs(qr_codes_directory_local, exist_ok=True)
    qr_code_local_path = os.path.join(qr_codes_directory_local, f"{roast_id}_qr.png")
    generate_qr_code(roast_url, qr_code_local_path)

    logging.info(f"Roast Profile generated: {roast_url}")
    logging.info(f"Processing of {file_path} completed.")
    return roast_url
