import qrcode
import qrcode
import logging
from PIL import Image
from flask import url_for
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .utils import resource_path


roast_profile_template_dir = resource_path("roast_profile_template")


# def generate_qr_code(url, output_path):
#     img = qrcode.make(url)
#     img.save(output_path)
#     logging.info(f"QR code saved as {output_path}")


def generate_qr_code(url, output_path, logo_path):
    # Generate the basic QR code
    qr_img = qrcode.make(url)

    # Open and resize the logo
    logo = Image.open(logo_path)
    # Adjust the size ratio as needed; 1/5 of QR's size is a reasonable start
    logo_size = (qr_img.size[0] // 5, qr_img.size[1] // 5)
    logo = logo.resize(logo_size, Image.Resampling.LANCZOS)

    # Calculate position to place the logo at the center
    pos = ((qr_img.size[0] - logo_size[0]) // 2, (qr_img.size[1] - logo_size[1]) // 2)

    # If the logo has transparency (RGBA), ensure it's preserved
    if logo.mode == "RGBA":
        qr_img.paste(logo, pos, mask=logo)
    else:
        qr_img.paste(logo, pos)

    # Save the final image
    qr_img.save(output_path)
    logging.info(f"QR code with logo saved as {output_path}")


def static_url(filename, env):
    if env == "local":
        return url_for("static", filename=filename)
    else:
        return f"assets/{filename}"


def generate_webpage(data, template_env="local"):
    env = Environment(loader=FileSystemLoader(roast_profile_template_dir))
    env.globals["url_for"] = url_for
    env.filters["static_url"] = static_url

    template = env.get_template("index.html")

    # prepare data for the template
    template_vars = {
        "data": data,
        "current_year": datetime.now().year,
        "env": template_env,
    }

    return template.render(template_vars)
