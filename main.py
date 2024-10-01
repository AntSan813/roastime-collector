
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging
import json
import time
import sys
import csv
import os

import matplotlib
matplotlib.use('Agg')  # Use the Anti-Grain Geometry backend
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import matplotlib.pyplot as plt
import qrcode
import boto3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

S3_BUCKET_NAME = 'coffee-profiles' 
S3_BASE_URL = f'https://{S3_BUCKET_NAME}.s3.amazonaws.com/'

def extract_roast_data(data_json):
    sample_rate = data_json.get('sampleRate', 1)  # Default sample rate to 1 if not specified
    time_list = [i * sample_rate for i in range(len(data_json['beanTemperature']))]
    bean_temp = data_json['beanTemperature']
    ibts_temp = data_json['drumTemperature'] 
    bean_ror = data_json['beanDerivative']
    
    # extract power, fan, and drum speed settings
    actions = data_json['actions']['actionTimeList']
    power = [0] * len(time_list)
    drum = [0] * len(time_list)
    fan = [0] * len(time_list)
    
    for action in actions:
        index = action['index']
        value = action['value']
        if action['ctrlType'] == 0:  # Power
            for i in range(index, len(power)):
                power[i] = value
        elif action['ctrlType'] == 1:  # Fan
            for i in range(index, len(fan)):
                fan[i] = value
        elif action['ctrlType'] == 2:  # Drum
            for i in range(index, len(drum)):
                drum[i] = value
    return time_list, bean_temp, ibts_temp, bean_ror, power, fan, drum

def plot_roast_chart(time_list, bean_temp, ibts_temp, bean_ror, power, fan, drum, output_path):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # plot temperatures
    ax1.plot(time_list, bean_temp, label='Bean Temperature (BT)', color='brown')
    ax1.plot(time_list, ibts_temp, label='Drum Temperature (DT)', color='orange')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend(loc='upper left')
    
    # plot Rate of Rise (RoR)
    ax2 = ax1.twinx()
    ax2.plot(time_list, bean_ror, label='Rate of Rise (RoR)', color='blue', linestyle='--')
    ax2.set_ylabel('RoR (°C/min)')
    ax2.legend(loc='upper right')
    
    # plot power, fan, drum settings
    ax3 = ax1.twinx()
    ax3.spines.right.set_position(("axes", 1.15))
    ax3.step(time_list, power, label='Power', color='red', where='post')
    ax3.step(time_list, fan, label='Fan', color='green', where='post')
    ax3.step(time_list, drum, label='Drum Speed', color='purple', where='post')
    ax3.set_ylabel('Settings Level')
    ax3.set_ylim(0, max(max(power), max(fan), max(drum)) + 1)
    ax3.legend(loc='lower right')
    
    plt.title('Roast Profile')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f'Roast chart saved as {output_path}')

def load_beans_data(csv_file='beans.csv'):
    beans_data = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            beans_data.append(row)
    return beans_data

def get_bean_info(bean_id, beans_data):
    for bean in beans_data:
        if bean['Bean ID'] == bean_id:
            return bean
    return None  

def generate_qr_code(url, output_path):
    img = qrcode.make(url)
    img.save(output_path)
    logging.info(f'QR code saved as {output_path}')

def upload_to_s3(local_file_path, bucket_name, s3_key):
    session = boto3.Session(profile_name='coffee')
    s3_client = session.client('s3')

    try:
        content_type = 'text/html' if s3_key.endswith('.html') else 'image/png'
        s3_client.upload_file(local_file_path, bucket_name, s3_key, ExtraArgs={'ContentType': content_type})
        logging.info(f'Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}')
        return True
    except Exception as e:
        logging.error(f'Failed to upload {local_file_path} to S3: {e}')
        return False

def generate_webpage(bean_info, roast_chart_filename, webpage_local_path):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    
    # prepare data for the template
    template_vars = {
        'bean': bean_info,
        'roast_chart': f'assets/{roast_chart_filename}',
        'current_year': datetime.now().year,
    }
    
    html_out = template.render(template_vars)
    
    # save the rendered HTML to the filesystem
    with open(webpage_local_path, 'w', encoding='utf-8') as f:
        f.write(html_out)
    
    logging.info(f'Webpage saved as {webpage_local_path}')

def process_roast(file_path):
    logging.info(f'Processing roast file: {file_path}')
    
    # first, load the roast data
    with open(file_path, 'r', encoding='utf-8') as f:
        data_json = json.load(f)
    
    # next, extract roast data
    time_list, bean_temp, ibts_temp, bean_ror, power, fan, drum = extract_roast_data(data_json)
    
    # generate unique identifiers for output files
    roast_number = data_json.get('roastNumber', '1')

    # define local directories
    roast_directory = f'{roast_number}'
    qr_codes_directory = os.path.join('qr_codes')
    assets_directory = os.path.join(roast_directory, 'assets')

    # create directories if they don't exist
    os.makedirs(assets_directory, exist_ok=True)
    os.makedirs(qr_codes_directory, exist_ok=True)

    # define resource filenames
    roast_qr_code_filename = f'{roast_number}.png'
    roast_chart_filename = f'{roast_number}_roast_chart.png'
    webpage_filename = "index.html"

    # local file paths
    roast_chart_local_path = os.path.join(assets_directory, roast_chart_filename)
    webpage_local_path = os.path.join(roast_directory, webpage_filename)
    qr_code_local_path = os.path.join(qr_codes_directory, roast_qr_code_filename)

    # S3 keys (paths in the bucket)
    roast_chart_s3_key = f'{roast_directory}/assets/{roast_chart_filename}'
    webpage_s3_key = f'{roast_directory}/{webpage_filename}'

    # uncomment if uploading QR codes to S3... doesn't seem necessary though
    # qr_code_s3_key = f'qr_codes/{roast_qr_code_filename}'

    # generate and save roast chart to local filesystem 
    plot_roast_chart(time_list, bean_temp, ibts_temp, bean_ror, power, fan, drum, roast_chart_local_path)
    
    beans_data = load_beans_data()
    
    # get the bean info
    bean_id = data_json.get('beanId')
    bean_info = get_bean_info(bean_id, beans_data)
    
    if not bean_info:
        logging.error(f'Bean with ID {bean_id} not found.')
        return
    
    generate_webpage(bean_info, roast_chart_filename, webpage_local_path)

    # upload files to s3
    upload_to_s3(roast_chart_local_path, S3_BUCKET_NAME, roast_chart_s3_key)
    upload_to_s3(webpage_local_path, S3_BUCKET_NAME, webpage_s3_key)
    
    # generate QR code
    roast_url = f'{S3_BASE_URL}{roast_directory}/index.html'
    generate_qr_code(roast_url, qr_code_local_path)
    # upload_to_s3(qr_code_local_path, S3_BUCKET_NAME, qr_code_s3_key)
    
    logging.info(f'Processing of {file_path} completed.')

class RoastFileHandler(FileSystemEventHandler):
    def __init__(self, roast_directory):
        self.roast_directory = roast_directory
        self.processed_files = set()
    
    def on_created(self, event):
        if not event.is_directory: 
            time.sleep(1)  # Wait a moment for the file to be fully written
            file_name = os.path.basename(event.src_path)
            if file_name not in self.processed_files:
                self.processed_files.add(file_name)
                process_roast(event.src_path)

def main():
    # roast_folder = './tests/' 
    ## ref: https://github.com/jglogan/roastime-data/blob/main/dump_roasts.py#L266
    if sys.platform.startswith('linux'):
        config_path = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
    elif sys.platform == 'darwin':
        config_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    elif sys.platform in ['win32', 'cygwin']:
        config_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    else:
        raise NotImplementedError(f'platform {sys.platform} is not supported')
    roast_path = os.path.join(config_path, 'roast-time', 'roasts')

    print(roast_path)
    event_handler = RoastFileHandler(roast_path)
    observer = Observer()
    observer.schedule(event_handler, path=roast_path, recursive=False)
    observer.start()
    logging.info(f'Watching directory: {roast_path}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info('Stopping directory watcher.')
    observer.join()

if __name__ == '__main__':
    main()
