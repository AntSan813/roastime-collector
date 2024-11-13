from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging
import os
import qrcode

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_qr_code(url, output_path):
    img = qrcode.make(url)
    img.save(output_path)
    logging.info(f"QR code saved as {output_path}")


def generate_webpage(roast_data):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("templates/pages/roast_profile.html")
    ga_tracking_id = os.getenv("GA_TRACKING_ID")

    # prepare data for the template
    template_vars = {
        "bean": roast_data,
        "GA_TRACKING_ID": ga_tracking_id,
        "current_year": datetime.now().year,
    }

    return template.render(template_vars)
