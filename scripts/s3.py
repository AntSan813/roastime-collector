import logging
import boto3

S3_PROFILE = "coffee"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def upload_to_s3(local_file_path, bucket_name, s3_key, content_type):
    session = boto3.Session(profile_name=S3_PROFILE)
    s3_client = session.client("s3")

    try:
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        logging.info(f"Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload {local_file_path} to S3: {e}")
        return False
