import qrcode
import logging
from flask import url_for
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .utils import resource_path


roast_profile_template_dir = resource_path("roast_profile_template")


def generate_qr_code(url, output_path):
    img = qrcode.make(url)
    img.save(output_path)
    logging.info(f"QR code saved as {output_path}")


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
