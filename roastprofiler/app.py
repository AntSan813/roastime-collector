import os
import json
import logging
from flask import (
    Flask,
    request,
    jsonify,
    send_file,
    render_template,
    send_from_directory,
)
from datetime import datetime
from werkzeug.utils import secure_filename

from .scripts.roast_data import extract_roast_data
from .scripts.html_template import generate_webpage
from .scripts.generate_roast_profile import generate_roast_profile
from .scripts.utils import (
    get_bean,
    get_beans,
    save_beans,
    get_config,
    bean_from_form,
    load_roast_full,
    get_roast_summary,
    get_roast_summaries,
    save_processed_roast,
    save_uploaded_roast,
    delete_uploaded_roast,
    is_valid_roast_id,
    resource_path,
)

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)

data_dir = resource_path("data")

os.makedirs(data_dir, exist_ok=True)

log_dir = os.path.join(os.path.expanduser("~"), "RoastProfilerLogs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@app.template_filter("datetime")
def datetime_filter(unix_timestamp):
    try:
        # Convert milliseconds to seconds
        unix_timestamp = float(unix_timestamp) / 1000.0
        return datetime.fromtimestamp(unix_timestamp).strftime("%m/%d/%y at %I:%M %p")
    except (ValueError, TypeError):
        return "Invalid date"


@app.route("/")
def index():
    beans = get_beans()
    roasts = get_roast_summaries()
    roasts.sort(key=lambda x: x["dateTime"], reverse=True)
    return render_template(
        "pages/roasts.html", roasts=roasts, beans=beans, current_page="index"
    )


@app.route("/process/<roast_id>", methods=["POST"])
def generate_roast_profile_route(roast_id):
    try:
        url = generate_roast_profile(roast_id, env="s3")
        last_processed = datetime.now().timestamp() * 1000
        processed_roast = {
            "id": roast_id,
            "profile_link": url,
            "last_processed": last_processed,
        }
        save_processed_roast(processed_roast)
        return jsonify({"profile_link": url, "last_processed": last_processed}), 200
    except Exception as e:
        logging.exception("Failed to publish roast profile")
        return jsonify({"error": str(e)}), 500


@app.route("/upload_roasts", methods=["POST"])
def upload_roasts():
    files = request.files.getlist("roast_files")
    files = [f for f in files if f and f.filename]
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    added, skipped = [], []
    for f in files:
        filename = f.filename
        try:
            roast_data_json = json.loads(f.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            skipped.append(
                {"filename": filename, "reason": "Not a valid JSON roast file."}
            )
            continue

        roast_id = roast_data_json.get("uid")
        if not is_valid_roast_id(roast_id):
            skipped.append(
                {"filename": filename, "reason": "Missing or invalid roast id (uid)."}
            )
            continue

        # confirm it's a roast the app can actually render before storing it
        try:
            extract_roast_data(roast_data_json)
        except Exception as e:
            skipped.append(
                {
                    "filename": filename,
                    "reason": f"Not a recognizable RoastTime roast ({e}).",
                }
            )
            continue

        save_uploaded_roast(roast_id, roast_data_json)
        added.append(
            {
                "filename": filename,
                "id": roast_id,
                "roastName": roast_data_json.get("roastName"),
            }
        )

    return jsonify({"added": added, "skipped": skipped}), 200


@app.route("/delete_uploaded_roast/<roast_id>", methods=["DELETE"])
def delete_uploaded_roast_route(roast_id):
    try:
        removed = delete_uploaded_roast(roast_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if removed:
        return jsonify({"message": "Uploaded roast removed."}), 200
    return jsonify({"error": "Uploaded roast not found."}), 404


@app.route("/download_qr/<roast_id>")
def download_qr(roast_id):
    qr_code_path = resource_path(f"cache/qr_codes/{roast_id}_qr.png")
    if os.path.exists(qr_code_path):
        return send_file(qr_code_path, as_attachment=True)
    else:
        return "QR code not found.", 404


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory(data_dir, filename)


@app.route("/roast_card/<roast_id>")
def roast_card(roast_id):
    roast = get_roast_summary(roast_id)
    if not roast:
        return "Roast not found.", 404
    bean = get_bean(roast["beanId"])
    return render_template("components/roast_card.html", roast=roast, bean=bean)


@app.route("/beans")
def beans_list():
    beans = get_beans()
    return render_template("pages/beans.html", beans=beans, current_page="beans_list")


@app.route("/bean/<bean_id>")
def bean_detail(bean_id):
    bean = get_bean(bean_id)
    beans = get_beans()
    return render_template("pages/bean.html", bean=bean, beans=beans)


def _save_bean_image(image_file, bean_id):
    """Persist an uploaded bean photo under data/bean_images and return the
    "/data/..." URL the app serves it from, or None if no file was provided.

    The filename is derived from the (sanitized) bean id so re-uploading replaces
    the previous photo, and the stored URL is relative so it resolves both for the
    local app and when the file is shipped to S3 with the published profile."""
    if not image_file or not image_file.filename:
        return None
    ext = os.path.splitext(secure_filename(image_file.filename))[1].lower() or ".png"
    filename = secure_filename(f"{bean_id}{ext}")
    image_dir = os.path.join(data_dir, "bean_images")
    os.makedirs(image_dir, exist_ok=True)
    image_file.save(os.path.join(image_dir, filename))
    return f"/data/bean_images/{filename}"


@app.route("/add_bean", methods=["POST"])
def add_bean():
    new_bean = bean_from_form(request.form)
    image_url = _save_bean_image(request.files.get("image_file"), new_bean["id"])
    if image_url:
        new_bean["image_url"] = image_url
    beans = get_beans()
    beans.append(new_bean)
    save_beans(beans)
    return jsonify({"message": "Bean added successfully", "bean": new_bean}), 200


@app.route("/edit_bean/<bean_id>", methods=["PUT"])
def edit_bean(bean_id):
    beans = get_beans()
    bean = next((b for b in beans if b["id"] == bean_id), None)
    if bean:
        updated_bean = bean_from_form(request.form)
        for key, value in updated_bean.items():
            bean[key] = value
        image_url = _save_bean_image(request.files.get("image_file"), bean_id)
        if image_url:
            bean["image_url"] = image_url
        save_beans(beans)
        return jsonify({"message": "Bean updated successfully", "bean": bean}), 200
    else:
        return jsonify({"message": "Bean not found"}), 404


@app.route("/delete_bean/<bean_id>", methods=["DELETE"])
def delete_bean(bean_id):
    beans = get_beans()
    beans = [bean for bean in beans if bean["id"] != bean_id]
    save_beans(beans)
    return jsonify({"message": "Bean deleted successfully"}), 200


@app.route("/bean_card/<bean_id>")
def bean_card(bean_id):
    bean = get_bean(bean_id)
    if bean:
        return render_template("components/bean_card.html", bean=bean)
    else:
        return "Bean not found", 404


@app.route("/bean_details/<bean_id>")
def bean_details(bean_id):
    bean = get_bean(bean_id)
    if bean:
        return render_template("components/bean_details.html", bean=bean)
    else:
        return "Bean not found", 404


# Roast-page visibility flags are rendered as checkboxes; an unchecked box is
# simply absent from the POST, so each is set explicitly by its presence.
ROAST_PAGE_TOGGLES = (
    "hide_buy_button",
    "hide_credit",
    "hide_chart",
    "hide_tasting",
    "hide_provenance",
)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Single settings page with three tabs (S3 / Store / Roast Pages) backed by
    one config.json. The whole form posts together, so text fields, the optional
    logo, and the roast-page toggles are all saved in one request."""
    config = get_config()
    if request.method == "POST":
        config = {**config, **request.form.to_dict()}
        for toggle in ROAST_PAGE_TOGGLES:
            config[toggle] = toggle in request.form
        logo = request.files.get("logo")
        if logo and logo.filename:
            logo.save(os.path.join(data_dir, "logo.png"))
            # Store relative to the resource root so the same value resolves both
            # as a /data/<file> URL (settings preview) and through resource_path()
            # when publishing a profile.
            config["logo_path"] = "data/logo.png"
        with open(os.path.join(data_dir, "config.json"), "w") as f:
            json.dump(config, f)
    return render_template(
        "pages/settings.html",
        config=config,
        current_page="settings",
        saved=request.method == "POST",
    )


@app.route("/preview_profile/<roast_id>")
def preview_profile(roast_id):
    roast_data = load_roast_full(roast_id)
    if not roast_data:
        return "Roast not found.", 404
    # bean may be unregistered (common for uploaded roasts) — fall back to {}
    # so the preview still renders instead of crashing on a missing bean
    bean = get_bean(roast_data.get("beanId")) or {}
    config = get_config()
    merged_data = {**roast_data, **bean, **config}

    html_out = generate_webpage(merged_data, template_env="local")
    return html_out
