import logging
import csv
import math
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

S3_BUCKET_NAME = "coffee-profiles"
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/"
ROAST_PROFILE_TEMPLATE = "template.html"


def get_roast_level(weight_loss_percentage):
    if weight_loss_percentage < 11:
        return "Light"
    elif 11 <= weight_loss_percentage < 13:
        return "Medium"
    elif 13 <= weight_loss_percentage < 15:
        return "Medium-Dark"
    else:
        return "Dark"


def extract_chart_metrics(data_json):
    roast_start_index = data_json["roastStartIndex"] + 1
    # skip first data points based on roast start index
    time_list = [i for i in range(len(data_json["beanTemperature"]))][
        roast_start_index:
    ]
    bean_temp = data_json["beanTemperature"][roast_start_index:]
    ibts_temp = data_json["drumTemperature"][roast_start_index:]
    ibts_ror = data_json["ibtsDerivative"][roast_start_index:]
    bean_ror = data_json["beanDerivative"][roast_start_index:]

    # extract power, fan, and drum speed settings
    actions = data_json["actions"]["actionTimeList"]
    power = [0] * len(time_list)
    drum = [0] * len(time_list)
    fan = [0] * len(time_list)

    for action in actions:
        index = action["index"]
        value = action["value"]
        if action["ctrlType"] == 0:  # Power
            for i in range(index, len(power)):
                power[i] = value
        elif action["ctrlType"] == 1:  # Fan
            for i in range(index, len(fan)):
                fan[i] = value
        elif action["ctrlType"] == 2:  # Drum
            for i in range(index, len(drum)):
                drum[i] = value

    return time_list, ibts_ror, bean_temp, ibts_temp, bean_ror, power, fan, drum


def extract_roast_data(data_json):
    time_list, ibts_ror, bean_temp, ibts_temp, bean_ror, power, fan, drum = (
        extract_chart_metrics(data_json)
    )

    weight_green = data_json.get("weightGreen", 0)
    weight_roasted = data_json.get("weightRoasted", 0)
    weight_loss_percentage = ((weight_green - weight_roasted) / weight_green) * 100

    return {
        "Roast Date": datetime.fromtimestamp(data_json["dateTime"] / 1000).strftime(
            "%m/%d/%Y"
        ),
        "Roast Length": round(
            data_json["totalRoastTime"] / 60, 2
        ),  # convert seconds to minutes
        "Weight Green": round(
            data_json["weightGreen"] * 0.035274, 2
        ),  # convert grams to ounces
        "Weight Roasted": round(
            data_json["weightRoasted"] * 0.035274, 2
        ),  # convert grams to ounces
        "Weight Loss": round(
            (data_json["weightGreen"] - data_json["weightRoasted"])
            / data_json["weightGreen"]
            * 100,
            2,
        ),
        "Time List": time_list,
        "Bean Temp": bean_temp,
        "IBTS Temp": ibts_temp,
        "Bean RoR": bean_ror,
        "IBTS RoR": ibts_ror,
        "Power": power,
        "Fan": fan,
        "Drum": drum,
        "Roast Level": get_roast_level(weight_loss_percentage),
        **data_json,
    }


def load_bean_metadata(csv_file="beans.csv"):
    beans_data = []
    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            beans_data.append(row)
    return beans_data


def get_bean_info(bean_id, beans_data):
    for bean in beans_data:
        if bean["Bean ID"] == bean_id:
            return bean
    return None
