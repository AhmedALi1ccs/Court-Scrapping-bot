import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import sys
import requests
import re
import zipfile
import io

class IndianaCourtCaseScraper:
    def __init__(self, input_csv_path, output_csv_path):
        # Setup Chrome options for better compatibility
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        
        # Get Chrome version and download appropriate driver
        try:
            chrome_driver_path = self.setup_chrome_driver()
            self.driver = webdriver.Chrome(
                service=Service(chrome_driver_path),
                options=chrome_options
            )
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Please make sure Google Chrome is installed on your computer.")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Load input CSV
        self.df = pd.read_csv(input_csv_path)
        self.output_csv_path = output_csv_path
        self.results_list = []

    def get_chrome_version(self):
        """Get the installed Chrome version."""
        if sys.platform == "win32":
            import winreg
            try:
                # Try reading from Windows Registry
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                major_version = version.split('.')[0]
                return major_version
            except WindowsError:
                print("Could not determine Chrome version from registry.")
                return None
        return None

    def setup_chrome_driver(self):
        """Download and setup ChromeDriver."""
        try:
            # Get Chrome version
            chrome_version = self.get_chrome_version()
            if not chrome_version:
                print("Could not determine Chrome version. Using latest stable ChromeDriver.")
                chrome_version = "stable"

            # Create drivers directory if it doesn't exist
            if getattr(sys, 'frozen', False):
                # If running as exe
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            drivers_dir = os.path.join(base_path, 'drivers')
            os.makedirs(drivers_dir, exist_ok=True)

            # Download appropriate ChromeDriver
            driver_path = os.path.join(drivers_dir, 'chromedriver.exe')
            
            # If driver already exists, return its path
            if os.path.exists(driver_path):
                return driver_path

            # Get ChromeDriver
            if chrome_version == "stable":
                url = "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE"
            else:
                url = f"https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_{chrome_version}"

            version = requests.get(url).text.strip()
            download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"

            # Download and extract ChromeDriver
            response = requests.get(download_url)
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(drivers_dir)
            
            # Move chromedriver to the right location
            extracted_driver = os.path.join(drivers_dir, 'chromedriver-win64', 'chromedriver.exe')
            if os.path.exists(extracted_driver):
                if os.path.exists(driver_path):
                    os.remove(driver_path)
                os.rename(extracted_driver, driver_path)

            return driver_path

        except Exception as e:
            print(f"Error downloading ChromeDriver: {e}")
            print("Please download ChromeDriver manually and place it in the 'drivers' folder.")
            input("Press Enter to exit...")
            sys.exit(1)

    def navigate_and_search(self):
        # Iterate through each row in the dataframe
        for index, row in self.df.iterrows():
            try:
                # Navigate to the court case search page
                self.driver.get("https://public.courts.in.gov/mycase/#/vw/Search")

                # Wait and handle potential popups or overlays
                time.sleep(2)  # Initial wait for page load

                # Attempt to close any initial popups
                try:
                    close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Close')]")
                    for button in close_buttons:
                        button.click()
                except:
                    pass

                # Wait for Name tab to be clickable
                name_tab = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@title='Find cases by searching party information.']"))
                )
                name_tab.click()

                # Wait and find input fields with explicit waits
                last_name_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='last name']"))
                )
                
                # Simulate typing last name slowly
                last_name_input.clear()
                for char in str(row['Last Name']):
                    last_name_input.send_keys(char)
                    time.sleep(0.1)

                # Move to first name input field
                first_name_input = self.driver.find_element(By.XPATH, "//input[@placeholder='first name / initial']")
                first_name_input.clear()
                for char in str(row['First Name']):
                    first_name_input.send_keys(char)
                    time.sleep(0.1)

                # Middle name (optional)
                middle_name_input = self.driver.find_element(By.XPATH, "//input[@placeholder='middle name / initial']")
                if pd.notna(row.get('Middle Name')) and str(row.get('Middle Name', '')).strip():
                    middle_name_input.clear()
                    for char in str(row.get('Middle Name')):
                        middle_name_input.send_keys(char)
                        time.sleep(0.1)

                # Check checkboxes
                checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                for checkbox in checkboxes:
                    # Find parent label and check if not already checked
                    parent_label = checkbox.find_element(By.XPATH, "..")
                    if 'Civil' in parent_label.text or 'Probate' in parent_label.text:
                        if not checkbox.is_selected():
                            checkbox.click()

                # Find and click search button
                search_button = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'btn-primary')]")

                # Scroll into view and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                time.sleep(0.5)  # Brief wait to ensure smooth scrolling

                # Click the Search button
                search_button.click()

                # Wait for results to load
                time.sleep(2)

                # Extract results
                results = self.extract_results()

                if results:
                    # For each result found, create a new row with ALL input data plus results
                    for result in results:
                        # Start with all columns from the input row
                        new_row = row.to_dict()
                        
                        # Add the search results
                        new_row.update({
                            'Case Style': result.get('Case Style', ''),
                            'Case Number': result.get('Case Number', ''),
                            'Court': result.get('Court', ''),
                            'Case Type': result.get('Case Type', ''),
                            'Filed Date': result.get('Filed Date', ''),
                            'Case Status': result.get('Case Status', ''),
                            'Parties': result.get('Parties', ''),
                            'Attorneys': result.get('Attorneys', ''),
                            'Charges': result.get('Charges', '')
                        })
                        self.results_list.append(new_row)
                else:
                    # If no results, add a row with all input data and empty result fields
                    new_row = row.to_dict()
                    new_row.update({
                        'Case Style': '',
                        'Case Number': '',
                        'Court': '',
                        'Case Type': '',
                        'Filed Date': '',
                        'Case Status': '',
                        'Parties': '',
                        'Attorneys': '',
                        'Charges': ''
                    })
                    self.results_list.append(new_row)

                # Convert results list to dataframe and save after each person
                results_df = pd.DataFrame(self.results_list)
                results_df.to_csv(self.output_csv_path, index=False)
                print(f"Results saved to {self.output_csv_path}")

                time.sleep(1)  # Small delay between searches

            except Exception as e:
                print(f"Error processing row {index}: {e}")
                # Still save the results we have so far in case of error
                if self.results_list:
                    results_df = pd.DataFrame(self.results_list)
                    results_df.to_csv(self.output_csv_path, index=False)

    def extract_results(self):
        results = []
        try:
            # Find all result rows
            result_rows = self.driver.find_elements(By.CLASS_NAME, "result-row")
            
            for row in result_rows:
                result = {}
                try:
                    # Get the result-col-middle section
                    result_col_middle = row.find_element(By.CLASS_NAME, "result-col-middle")
                    
                    # Extract case title/style
                    title_element = result_col_middle.find_element(By.CLASS_NAME, "result-title")
                    result['Case Style'] = title_element.text.strip()
                    
                    # Extract case number
                    case_number = result_col_middle.find_element(By.CLASS_NAME, "result-subtitle")
                    result['Case Number'] = case_number.text.strip()
                    
                    # Make sure details are expanded
                    try:
                        expand_button = row.find_element(By.XPATH, ".//span[@title='Hide details' or @title='View details']")
                        if "collapse" not in expand_button.get_attribute("class"):
                            expand_button.click()
                            time.sleep(0.5)
                    except:
                        pass

                    # Find result-row-details section
                    details_section = result_col_middle.find_element(By.CLASS_NAME, "result-row-details")
                    
                    # Extract all rows in details section
                    detail_rows = details_section.find_elements(By.CLASS_NAME, "row")
                    for detail_row in detail_rows:
                        try:
                            # Get label from first column
                            label_div = detail_row.find_element(By.XPATH, ".//div[contains(@class, 'col-xs-12 col-sm-2')]")
                            label = label_div.find_element(By.CLASS_NAME, "text-muted").text.strip()
                            
                            # Get value from second column
                            value_div = detail_row.find_element(By.XPATH, ".//div[contains(@class, 'col-xs-11 col-xs-offset-1')]")
                            value = value_div.find_element(By.CLASS_NAME, "small").text.strip()
                            
                            # Map to appropriate fields
                            if "Court" in label:
                                result['Court'] = value
                            elif "Case Type" in label:
                                result['Case Type'] = value
                            elif "Filed" in label:
                                result['Filed Date'] = value
                            elif "Status" in label:
                                result['Case Status'] = value
                            elif "Charges" in label:
                                result['Charges'] = value
                            elif "Parties" in label:
                                result['Parties'] = value
                            elif "Attorneys" in label:
                                result['Attorneys'] = value
                        except Exception as e:
                            print(f"Error extracting detail row: {e}")
                    
                    # Add the result if we have data
                    if result:
                        results.append(result)
                        
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in extraction: {e}")
            
        return results
    
    def close(self):
        self.driver.quit()

def main():
    scraper = IndianaCourtCaseScraper(
        input_csv_path='Property_Radar_November_2024_Cold_Calling_Property_Radar_November (1).csv', 
        output_csv_path='court_case_results6.csv'
    )
    
    try:
        scraper.navigate_and_search()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
