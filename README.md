# RoastTime Roast Processor

System that transforms coffee roasting data from RoastTime into a customer-friendly webpage.

demo: https://coffee-profiles.s3.amazonaws.com/roasts/f119LdNXSOSAut1ViLFwi/index.html

### **Key Features**

- **Automatically Detects New Roasts**
- **Creates Customer-Friendly Web Pages**
- **Publishes to the Web**
- **Generates QR Codes**

### **Web Page Template Features**

- **Key Roast Details:**
  - Displays important information like roast length, roast level, bean weights, and more.
- **Bean Information:**
  - Includes details about the coffee beans, such as their origin, altitude, varietal, etc.
- **Interactive Roast Chart:**
  - Shows a chart of the roasting process, similar to what you see in RoastTime, so customers can see how their coffee was roasted.
- **Helpful Explanations:**
  - Provides information on how to read the chart and understand the roasting process.

### **Getting Started**

#### **Prerequisites**
- **RoastTime Software**
  - Ensure you’re using RoastTime to record your coffee roasts.
- **Bean Information Spreadsheet**
  - Since the roast data only includes the ID of the bean, you’ll need to create a simple spreadsheet that matches the bean IDs to their names and other details.
  - For a template, take a look at the `beans.csv` file. The bean ID can be found on Roast World.

#### **Steps**

1. **Prepare the bean data**
   - Create a spreadsheet (`beans.csv`) that lists your beans, including their IDs, names, and any other information you’d like to share.
   
2. **Clone this repo**
   
4. **Customize it to your preferences**
   - **HTML Templates:** Modify the `template/index.html` file to change the structure or content of the web page.
   - **CSS Styles:** Update `template/assets/styles.css` to adjust styling to match your brand.
   - **JavaScript:** Modify `template/assets/chart.js` for custom chart behavior if needed.

5. **Configure AWS**
   - This step is only necessary if you want to publish your roast profiles to Amazon’s S3 service. If you’d rather publish to another web service or don’t want to publish anywhere, then you will need to remove the relevant logic in the code.
   - **Install and configure AWS CLI** by following the AWS documentation, and ensure the S3 configuration is set correctly in the project files.

6. **Run it**
   -  Before you roast, start main.py: `python main.py`
   -  Or, test it with the following command: `python main.py --test sample_roast_data.json` 

7. **Roast your coffee**
   - Roast as you normally would using RoastTime. After each roast is completed, the program will generate a web page and a QR code for that roast.

8. **Share the Roast Profile!**
   - Once the roast is completed, you will see the script spit out its progress in the terminal. Once it finsihes, a new QR code will be added to the `qr_codes` directory. Print or share the QR code so customers can scan it. They’ll be taken to the web page with all the roast details and bean information.


