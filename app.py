import os
import json
import logging
from watchdog.observers import Observer
from flask import (
    Flask,
    request,
    jsonify,
    send_file,
    render_template,
    send_from_directory,
)
from datetime import datetime

from scripts.generate_roast_profile import generate_roast_profile
from scripts.utils import (
    get_bean,
    get_beans,
    get_roast,
    save_beans,
    get_config,
    get_roasts,
    bean_from_form,
    DataFileHandler,
    save_processed_roast,
)

app = Flask(__name__)

DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

beans = []
roast_profiles = []

data_event_handler = DataFileHandler(beans, roast_profiles)
observer = Observer()
observer.schedule(data_event_handler, path=DATA_DIR, recursive=False)
observer.start()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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
    roasts = get_roasts()
    roasts.sort(key=lambda x: x["dateTime"], reverse=True)
    return render_template(
        "pages/roasts.html", roasts=roasts, beans=beans, current_page="index"
    )


@app.route("/process/<roast_id>", methods=["POST"])
def generate_roast_profile_route(roast_id):
    try:
        url = generate_roast_profile(roast_id)
        last_processed = datetime.now().timestamp() * 1000
        processed_roast = {
            "id": roast_id,
            "profile_link": url,
            "last_processed": last_processed,
        }
        save_processed_roast(processed_roast)
        return jsonify({"profile_link": url, "last_processed": last_processed}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/download_qr/<roast_id>")
def download_qr(roast_id):
    qr_code_path = f"cache/qr_codes/{roast_id}_qr.png"
    if os.path.exists(qr_code_path):
        return send_file(qr_code_path, as_attachment=True)
    else:
        return "QR code not found.", 404


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory("data", filename)


@app.route("/roast_card/<roast_id>")
def roast_card(roast_id):
    roast = get_roast(roast_id)
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


@app.route("/add_bean", methods=["POST"])
def add_bean():
    new_bean = bean_from_form(request.form)
    image_file = request.files.get("image_file")
    if image_file:
        image_filename = f"{new_bean['id']}_{image_file.filename}"
        image_path = os.path.join("data", "bean_images", image_filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)
        new_bean["image_url"] = f"/{image_path}"
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
        image_file = request.files.get("image_file")
        if image_file:
            image_filename = f"{bean_id}_{image_file.filename}"
            image_path = os.path.join("data", "bean_images", image_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image_file.save(image_path)
            bean["image_url"] = f"/{image_path}"
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


@app.route("/s3_settings", methods=["GET", "POST"])
def s3_settings():
    config = get_config()
    if request.method == "POST":
        logo = request.files.get("logo")
        # config["footer_text"] = request.form.get("footer_text")
        # config["s3_base_url"] = request.form.get("s3_base_url")
        # config["s3_bucket_name"] = request.form.get("s3_bucket_name")
        # config["s3_access_key"] = request.form.get("s3_access_key")
        # config["s3_secret_key"] = request.form.get("s3_secret_key")
        config = {**config, **request.form.to_dict()}
        if logo:
            logo_path = os.path.join("data", "logo.png")
            logo.save(logo_path)
            config["logo_path"] = logo_path

        print(config)
        with open(os.path.join(DATA_DIR, "config.json"), "w") as f:
            json.dump(config, f)

        return render_template(
            "pages/s3_settings.html", config=config, current_page="s3_settings"
        )
    else:
        config = get_config()
        return render_template(
            "pages/s3_settings.html", config=config, current_page="s3_settings"
        )


@app.route("/roast_profile_settings", methods=["GET", "POST"])
def roast_profile_settings():
    config = get_config()
    if request.method == "POST":
        logo = request.files.get("logo")
        # config["footer_text"] = request.form.get("footer_text")
        # config["s3_base_url"] = request.form.get("s3_base_url")
        # config["s3_bucket_name"] = request.form.get("s3_bucket_name")
        # config["s3_access_key"] = request.form.get("s3_access_key")
        # config["s3_secret_key"] = request.form.get("s3_secret_key")
        config = {**config, **request.form.to_dict()}
        if logo:
            logo_path = os.path.join("data", "logo.png")
            logo.save(logo_path)
            config["logo_path"] = logo_path

        print(config)
        with open(os.path.join(DATA_DIR, "config.json"), "w") as f:
            json.dump(config, f)

        return render_template(
            "pages/roast_profile_settings.html",
            config=config,
            current_page="roast_profile_settings",
        )
    else:
        config = get_config()
        return render_template(
            "pages/roast_profile_settings.html",
            config=config,
            current_page="roast_profile_settings",
        )


if __name__ == "__main__":
    app.run(debug=True)
