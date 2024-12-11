from flask import Flask, request, jsonify
import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import io
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dam_levels.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Scrape and process dam levels
        result = scrape_dam_levels()
        
        if result:
            return jsonify({
                'status': 'success', 
                'message': 'Dam levels scraped successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Failed to scrape dam levels'
            }), 500
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

def scrape_dam_levels():
    try:
        # Dictionary of regions with their abbreviations and names
        regions = {
            "EC": "Eastern Cape",
            "FS": "Free State",
            "G": "Gauteng",
            "KN": "Kwazulu-Natal",
            "LP": "Limpopo",
            "M": "Mpumalanga",
            "NC": "Northern Cape",
            "NW": "North West",
            "WC": "Western Cape Total"
        }

        # Dictionary to store DataFrames for each region
        region_data = {}

        for abbreviation, name in regions.items():
            logger.info(f"Processing region: {name}")
            url = f"https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region={abbreviation}"

            try:
                response = requests.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.find_all('table')

                if not tables or len(tables) <= 4:
                    logger.warning(f"Insufficient tables found for region {name}")
                    continue

                table = tables[4]
                headers = [th.text.strip() for th in table.find_all('th')]
                rows = []

                for tr in table.find_all('tr')[1:]:
                    row_data = [td.text.strip().replace('#', '') for td in tr.find_all('td')]
                    if len(row_data) == len(headers):
                        filtered_row_data = [row_data[0], row_data[5], row_data[6], row_data[7]]
                        rows.append(filtered_row_data)

                df = pd.DataFrame(rows, columns=['Dam', 'This Week', 'Last Week', 'Last Year'])
                region_data[name] = df

            except Exception as e:
                logger.error(f"Error scraping {name}: {str(e)}")

        if not region_data:
            logger.warning("No data collected for any regions")
            return False

        # Prepare Excel output
        current_date = datetime.now().strftime('%Y%m%d')
        output_filename = f'dam_levels_{current_date}.xlsx'
        
        # Ensure outputs directory exists
        os.makedirs('outputs', exist_ok=True)
        full_path = os.path.join('outputs', output_filename)

        with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
            averages = []

            for region_name, df in region_data.items():
                # Convert to numeric values
                df['This Week'] = pd.to_numeric(df['This Week'].str.replace('#', ''), errors='coerce')
                df['Last Week'] = pd.to_numeric(df['Last Week'].str.replace('#', ''), errors='coerce')
                df['Last Year'] = pd.to_numeric(df['Last Year'].str.replace('#', ''), errors='coerce')

                # Calculate averages
                this_week_avg = df['This Week'].mean()
                last_week_avg = df['Last Week'].mean()
                last_year_avg = df['Last Year'].mean()

                averages.append([region_name, this_week_avg, last_week_avg, last_year_avg])
                df.to_excel(writer, sheet_name=region_name.replace(' ', '_'), index=False)

            # Create master sheet with averages
            averages_df = pd.DataFrame(averages, columns=['Region', 'This Week Avg', 'Last Week Avg', 'Last Year Avg'])
            averages_df[['This Week Avg', 'Last Week Avg', 'Last Year Avg']] = averages_df[['This Week Avg', 'Last Week Avg', 'Last Year Avg']].round(1)
            averages_df.to_excel(writer, sheet_name='Master', index=False)

        logger.info(f"Data saved to {full_path}")
        return True

    except Exception as e:
        logger.error(f"Scraping process failed: {str(e)}")
        return False

@app.route('/')
def index():
    return "Dam Levels Scraper is running. Use /webhook endpoint."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)