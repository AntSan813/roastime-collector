import os
import logging
from dotenv import load_dotenv
from watchdog.observers import Observer
from flask import Flask, render_template, request, jsonify
from datetime import datetime

from scripts.generate_roast_profile import generate_roast_profile
from scripts.utils import (
    DataFileHandler,
    get_roast_path,
    bean_from_form,
    save_processed_roast,
    get_beans,
    get_roast,
    get_bean,
    save_beans,
    get_all_roasts,
)

app = Flask(__name__)

DATA_DIR = "data"
BEANS_FILE = os.path.join(DATA_DIR, "beans.json")
PROCESSED_ROASTS_FILE = os.path.join(DATA_DIR, "processed_roasts.json")

os.makedirs(DATA_DIR, exist_ok=True)

beans = []
processed_roasts = []

data_event_handler = DataFileHandler(beans, processed_roasts)
observer = Observer()
observer.schedule(data_event_handler, path=DATA_DIR, recursive=False)
observer.start()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


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
    roasts = get_all_roasts()
    roasts.sort(key=lambda x: x["dateTime"], reverse=True)
    return render_template("pages/roasts.html", roasts=roasts, beans=beans)


@app.route("/process/<roast_id>", methods=["POST"])
def generate_roast_profile_route(roast_id):
    roast_path = get_roast_path()
    url = generate_roast_profile(roast_path, roast_id)
    last_processed = datetime.now().timestamp() * 1000
    processed_roast = {
        "id": roast_id,
        "profile_link": url,
        "last_processed": last_processed,
    }
    save_processed_roast(processed_roast)
    return jsonify({"profile_link": url, "last_processed": last_processed}), 200


@app.route("/roast_card/<roast_id>")
def roast_card(roast_id):
    roast = get_roast(roast_id)
    bean = get_bean(roast["beanId"])
    return render_template("components/roast_card.html", roast=roast, bean=bean)


@app.route("/beans")
def beans_list():
    beans = get_beans()
    return render_template("pages/beans.html", beans=beans)


@app.route("/bean/<bean_id>")
def bean_detail(bean_id):
    bean = get_bean(bean_id)
    return render_template("pages/bean.html", bean=bean)


@app.route("/add_bean", methods=["POST"])
def add_bean():
    new_bean = bean_from_form(request.form)
    beans = get_beans()
    beans.append(new_bean)
    save_beans(beans)
    return jsonify({"message": "Bean added successfully", "bean": new_bean}), 200


@app.route("/edit_bean/<bean_id>", methods=["PUT"])
def edit_bean(bean_id):
    bean = get_bean(bean_id)
    if bean:
        bean.update(bean_from_form(request.form))
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


if __name__ == "__main__":
    app.run(debug=True)
