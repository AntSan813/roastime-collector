import shutil
import logging
import json
import os
import boto3
from botocore.exceptions import ClientError

from .roast_data import extract_roast_data
from .html_template import generate_qr_code, generate_webpage
from .utils import get_beans, get_config, get_roast_path, resource_path


cache_dir = resource_path("cache")
os.makedirs(cache_dir, exist_ok=True)


def upload_to_s3(s3_client, local_file_path, bucket_name, s3_key, content_type):
    logging.info(f"Uploading {local_file_path} to s3://{bucket_name}/{s3_key}...")
    try:
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        logging.info(f"Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}")
        return True
    except ClientError as e:
        logging.error(f"Failed to upload {local_file_path} to S3: {e}")
        raise e


def copy_and_overwrite(from_path, to_path):
    from_path = resource_path(from_path)

    if not os.path.exists(to_path):
        os.makedirs(to_path)

    for item in os.listdir(from_path):
        source = os.path.join(from_path, item)
        destination = os.path.join(to_path, item)

        if os.path.isdir(source):
            copy_and_overwrite(source, destination)
        else:
            shutil.copy2(source, destination)


def generate_roast_profile(roast_id, env="local"):
    roast_path = get_roast_path()
    config = get_config()

    base_url = config.get("s3_base_url")
    bucket_name = config.get("s3_bucket_name")
    s3_access_key = config.get("s3_access_key")
    s3_secret_key = config.get("s3_secret_key")

    logging.info(f"Processing roast file: {roast_path}/{roast_id}")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
    )

    # Load the roast data from roast-time
    roast_file_path = os.path.join(roast_path, roast_id)
    if roast_file_path.endswith(".DS_Store"):
        return

    # load the roast data
    try:
        with open(roast_file_path, "r", encoding="utf-8") as f:
            roast_data_json = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logging.error(f"Error reading file {roast_file_path}: {e}")
        return

    # define local directories
    roast_directory = f"roasts/{roast_id}"
    roast_directory_local = f"{cache_dir}/{roast_directory}"

    os.makedirs(roast_directory_local, exist_ok=True)

    # local file paths
    webpage_local_path = os.path.join(roast_directory_local, "index.html")

    # get bean data
    bean_id = roast_data_json.get("beanId")
    beans = get_beans()
    bean = [bean for bean in beans if bean["id"] == bean_id][0]

    if not bean:
        logging.error(f"Bean ID {bean_id} not found.")
        return

    roast_data = extract_roast_data(roast_data_json)
    merged_data = {**roast_data, **bean, **config}

    # generate the HTML page
    html_out = generate_webpage(merged_data, template_env=env)

    # save the rendered HTML to the filesystem
    with open(webpage_local_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    # copy assets to the local directory
    assets_folder = "static"
    if env == "s3":
        assets_folder = "assets"

    assets_directory = os.path.join(roast_directory, assets_folder)
    assets_directory_local = os.path.join(roast_directory_local, assets_folder)
    os.makedirs(assets_directory_local, exist_ok=True)
    copy_and_overwrite("static", assets_directory_local)

    logging.info(f"Webpage saved as {webpage_local_path}")

    # upload files to s3
    webpage_s3_key = f"{roast_directory}/index.html"

    logging.info(f"LOGO PATH {config['logo_path']}")
    if "logo_path" in config and config["logo_path"]:
        # add file to local assets directory
        logo_destination_path = os.path.join(assets_directory_local, "logo.png")
        logo_path = resource_path(config["logo_path"])
        shutil.copy2(logo_path, logo_destination_path)
        upload_to_s3(
            s3_client,
            logo_destination_path,
            bucket_name,
            f"{assets_directory}/logo.png",
            "image/png",
        )
    else:
        upload_to_s3(
            s3_client,
            f"{assets_directory_local}/logo.png",
            bucket_name,
            f"{assets_directory}/logo.png",
            "image/png",
        )

    # TODO: consider batching uploads
    upload_to_s3(
        s3_client,
        webpage_local_path,
        bucket_name,
        webpage_s3_key,
        "text/html",
    )
    upload_to_s3(
        s3_client,
        f"{assets_directory_local}/chart.js",
        bucket_name,
        f"{assets_directory}/chart.js",
        "application/javascript",
    )
    upload_to_s3(
        s3_client,
        f"{assets_directory_local}/styles.css",
        bucket_name,
        f"{assets_directory}/styles.css",
        "text/css",
    )

    # generate QR code
    roast_url = f"{base_url}{roast_directory}/index.html"

    # generate QR code
    qr_codes_directory = os.path.join("qr_codes")
    qr_codes_directory_local = os.path.join(cache_dir, qr_codes_directory)
    os.makedirs(qr_codes_directory_local, exist_ok=True)
    qr_code_local_path = os.path.join(qr_codes_directory_local, f"{roast_id}_qr.png")
    generate_qr_code(roast_url, qr_code_local_path)

    logging.info(f"Roast Profile generated: {roast_url}")
    logging.info(f"Processing of {roast_path} completed.")
    return roast_url
