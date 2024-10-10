
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging

import matplotlib
matplotlib.use('Agg')  # Use the Anti-Grain Geometry backend
import matplotlib.pyplot as plt
import qrcode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

S3_BUCKET_NAME = 'coffee-profiles' 
S3_BASE_URL = f'https://{S3_BUCKET_NAME}.s3.amazonaws.com/'
ROAST_PROFILE_TEMPLATE = 'template/index.html'

def generate_qr_code(url, output_path):
    img = qrcode.make(url)
    img.save(output_path)
    logging.info(f'QR code saved as {output_path}')

def generate_webpage(roast_data, ):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(ROAST_PROFILE_TEMPLATE)
    

    # prepare data for the template
    # update based on what you want to display in the template 
    template_vars = {
        'bean': roast_data,
        # 'roast_chart': f'assets/{roast_chart_filename}',
        # 'roast_data_json': roast_data,
        'current_year': datetime.now().year,
    }
    
    # html_out = 
    return template.render(template_vars)
    
    # save the rendered HTML to the filesystem
    # with open(webpage_local_path, 'w', encoding='utf-8') as f:
    #     f.write(html_out)
    
    # logging.info(f'Webpage saved as {webpage_local_path}')

# def plot_roast_chart(time_list, bean_temp, ibts_temp, bean_ror, power, fan, drum, output_path):
#     fig, ax1 = plt.subplots(figsize=(12, 6))
  
#     # plot temperatures
#     ax1.plot(time_list, bean_temp, label='Bean Temperature (BT)', color='brown')
#     ax1.plot(time_list, ibts_temp, label='Drum Temperature (DT)', color='orange')
#     ax1.set_xlabel('Time (s)')
#     ax1.set_ylabel('Temperature (°C)')
#     ax1.legend(loc='upper left')
  
#     # plot Rate of Rise (RoR)
#     ax2 = ax1.twinx()
#     ax2.plot(time_list, bean_ror, label='Rate of Rise (RoR)', color='blue', linestyle='--')
#     ax2.set_ylabel('RoR (°C/min)')
#     ax2.legend(loc='upper right')
  
#     # plot power, fan, drum settings
#     ax3 = ax1.twinx()
#     ax3.spines.right.set_position(("axes", 1.15))
#     ax3.step(time_list, power, label='Power', color='red', where='post')
#     ax3.step(time_list, fan, label='Fan', color='green', where='post')
#     ax3.step(time_list, drum, label='Drum Speed', color='purple', where='post')
#     ax3.set_ylabel('Settings Level')
#     ax3.set_ylim(0, max(max(power), max(fan), max(drum)) + 1)
#     ax3.legend(loc='lower right')
  
#     plt.title('Roast Profile')
#     plt.tight_layout()
#     plt.savefig(output_path)
#     plt.close()
#     logging.info(f'Roast chart saved as {output_path}')
