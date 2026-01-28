# app/services/scrape_service.py
import os
import time
import uuid
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.logging import logger
import pandas as pd
import glob
from utils.leadBoostAI_AWS_connection_dump_file import upload_df_to_s3_parquet
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
base_dir = os.getcwd()

# Global Session Store: {session_id: driver}
# In a production environment, this might need more robust handling (e.g., Redis + Grid)
# but for this standalone service, a global dict works.
SESSIONS: Dict[str, webdriver.Chrome] = {}

class ScrapeService:
    @staticmethod
    def setup_driver(webpage):
        # Define paths - adapting to be relative to the service or project root
        # Assuming run from project root or handling absolute paths carefully
        # base_dir = os.getcwd() 
        download_path = os.path.join(base_dir, "downloads")
        if webpage == "vauto":
            profile_path = os.path.join(base_dir, "chrome_data")
            download_path = os.path.join(base_dir, "downloads", "vauto")
        elif webpage == "cargurus":
            profile_path = os.path.join(base_dir, "chrome_data_cargurus")
            download_path = os.path.join(base_dir, "downloads", "cargurus")
        else:
            profile_path = os.path.join(base_dir, "chrome_data_other")
            download_path = os.path.join(base_dir, "downloads", "other")
        if not os.path.exists(download_path):
            logger.info(f"Download path does not exist: {download_path}")
            os.makedirs(download_path)
        
        logger.info(f"Download path set to: {download_path}")
        logger.info(f"Profile path set to: {profile_path}")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1366,900")
        # chrome_options.add_argument("--headless") 
        
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.cookies": 1,
                "network.cookie.cookieBehavior": 0,
                "profile.block_third_party_cookies": False,
                "profile.cookie_controls_mode": 0,
                "download.default_directory": download_path,
            },
        )

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        chrome_options.add_argument(
            "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure,BlockThirdPartyCookies"
        )
        
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        chrome_options.set_capability("unhandledPromptBehavior", "accept")

        # Local Chrome Profile (Persistence)
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument("--profile-directory=Default")

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def get_element(self, driver, by, value, timeout=30):
        try:
            logger.info(f"Looking for element: {value} by {by}")
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"Element not found: {value} by {by}. Error: {e}")
            raise

    def click_element(self, driver, element):
        try:
            element.click()
            logger.info("Clicked element successfully.")
        except Exception as e:
            logger.warning(f"Normal click failed: {e}. Trying JS click...")
            try:
                driver.execute_script("arguments[0].click();", element)
                logger.info("JS click successful.")
            except Exception as js_e:
                logger.error(f"JS click also failed: {js_e}")
                raise

    def close_driver_safely(self, session_id):
        if session_id in SESSIONS:
            logger.info(f"Closing session {session_id}")
            driver = SESSIONS.pop(session_id)
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

    # --- Flows ---

    def upload_latest_file_to_s3(self, webpage: str):
        try:
            if webpage == "vauto":
                download_path = os.path.join(base_dir, "downloads", "vauto")
            elif webpage == "cargurus":
                download_path = os.path.join(base_dir, "downloads", "cargurus")
            else:
                download_path = os.path.join(base_dir, "downloads", "other")
            # Get list of files in download path
            list_of_files = glob.glob(os.path.join(download_path, "*")) 
            logger.info(f"List of files found: {list_of_files}")
            
            if not list_of_files:
                logger.warning("No files found in downloads directory to upload.")
                return

            # Find the latest file based on creation time
            latest_file = max(list_of_files, key=os.path.getctime)
            logger.info(f"Latest file found: {latest_file}")

            # Read file into DataFrame
            if latest_file.endswith(".csv"):
                df = pd.read_csv(latest_file)

            elif latest_file.endswith(".xls"):
                logger.info("xls file found")
                xlsx_path = latest_file.replace(".xls", ".xlsx")

                df = pd.read_excel(latest_file, engine="xlrd")
                df.to_excel(xlsx_path, index=False, engine="openpyxl")
                df = pd.read_excel(xlsx_path)

            elif latest_file.endswith(".xlsx"):
                df = pd.read_excel(latest_file)

            else:
                logger.warning(f"Unsupported file format: {latest_file}")
                return

        # ---------- SANITIZE DATAFRAME (PERMANENT FIX) ----------
            for col in df.columns:
                if df[col].dtype == "object":

                    # Try to understand if column is numeric
                    numeric_ratio = (
                        pd.to_numeric(df[col], errors="coerce")
                        .notna()
                        .mean()
                    )

                    if numeric_ratio > 0.8:
                        # Mostly numeric → clean & convert
                        df[col] = (
                            df[col]
                            .astype(str)
                            .str.replace(",", "", regex=False)
                        )
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        logger.info(f"Column '{col}' normalized as NUMERIC")
                    else:
                        # Mostly text → force string
                        df[col] = (
                            df[col]
                            .astype(str)
                            .replace("nan", None)
                        )
                        logger.info(f"Column '{col}' normalized as STRING")
        # -------------------------------------------------------


            # Date partitions
            now = datetime.utcnow()
            year = now.year
            month = f"{now.month:02d}"
            day = f"{now.day:02d}"

            # ---------- ADD EMPTY PARTITION COLUMNS ----------
            for col in ["year", "month", "day"]:
                if col not in df.columns:
                    df[col] = None

            logger.info("Empty columns added: year, month, day")

            df["year"] = year
            df["month"] = month
            df["day"] = day


            # S3 Upload Constants

            BUCKET = os.getenv("S3_BUCKET")
            PROJECT_NAME = os.getenv("S3_PROJECT_NAME")
            ATHENA_DB = os.getenv("ATHENA_DB")
            ATHENA_TABLE = os.getenv("ATHENA_TABLE")
            ATHENA_OUTPUT = os.getenv("ATHENA_OUTPUT")
            

            # Upload to S3
            s3_path = upload_df_to_s3_parquet(
                df=df,
                bucket=BUCKET,
                project_name=PROJECT_NAME,
                database=ATHENA_DB,
                table_name=ATHENA_TABLE,
                athena_output=ATHENA_OUTPUT
            )
            logger.info(f"File successfully uploaded to S3: {s3_path}")
            return s3_path

        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise e

    async def start_login_flow(self, username: str, password: str, report_name: str) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new session: {session_id}")
        
        driver = self.setup_driver("vauto")
        SESSIONS[session_id] = driver

        try:
            status = self._perform_login_actions(driver, username, password)
            if status == "OTP_NEEDED":
                return {
                    "status": "waiting_for_otp", 
                    "session_id": session_id, 
                    "message": "2FA required. Please submit OTP."
                }
            else:
                self._perform_post_login_actions(driver, report_name)
                self.close_driver_safely(session_id)
                self.upload_latest_file_to_s3("vauto")
                
                return {"status": "success", "message": "Scrape completed successfully (No 2FA needed)."}
        except Exception as e:
            logger.error(f"Error in start_login_flow: {e}")
            self.close_driver_safely(session_id)
            raise e

    async def submit_otp_flow(self, session_id: str, otp: str, report_name: str) -> Dict[str, str]:
        if session_id not in SESSIONS:
            raise ValueError("Session not found or expired")
        
        driver = SESSIONS[session_id]
        
        try:
            logger.info("Waiting for OTP input field...")
            otp_field = self.get_element(driver, By.ID, "input-verification-code")
            otp_field.send_keys(otp)
            
            verify_btn = self.get_element(driver, By.ID, "button-account-recovery-submit")
            if verify_btn:
                WebDriverWait(driver, 10).until(lambda d: verify_btn.is_enabled())
                self.click_element(driver, verify_btn)
                logger.info("OTP submitted")
            else:
                logger.warning("OTP button not found")
            
            # # Select vAuto Product
            try:
                logger.info("Waiting for Product Selection...")
                product_tile = self.get_element(driver, By.ID, "product-tile-VAT_prod", timeout=20)
                if product_tile:
                    self.click_element(driver, product_tile)
                    logger.info("vAuto product selected")
                else:
                    logger.warning("vAuto product tile not found")
            except Exception as e:
                logger.error(f"Error selecting vAuto product: {e}")
                pass

            self._perform_post_login_actions(driver, report_name)
            self.close_driver_safely(session_id)
            
            self.upload_latest_file_to_s3("vauto")
            return {"status": "success", "message": "Scrape completed successfully."}
        
        except Exception as e:
            logger.error(f"Error in submit_otp_flow: {e}")
            self.close_driver_safely(session_id)
            raise e

    async def start_cargurus_login_flow(self, username: str, password: str) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new CarGurus session: {session_id}")
        
        driver = self.setup_driver("cargurus")
        SESSIONS[session_id] = driver

        try:
            self._perform_cargurus_login_actions(driver, username, password)
            self._perform_cargurus_post_login_actions(driver)
            self.close_driver_safely(session_id)
            # self.upload_latest_file_to_s3() # Uncomment if we actually download a file
            self.upload_latest_file_to_s3("cargurus")
            return {"status": "success", "message": "CarGurus scrape completed successfully."}
        except Exception as e:
            logger.error(f"Error in start_cargurus_login_flow: {e}")
            self.close_driver_safely(session_id)
            raise e

    # --- Internal Selenium Actions ---

    def _perform_login_actions(self, driver, username, password):
        driver.get("https://provision.vauto.app.coxautoinc.com/Va/api/vauto/oauth2Callback/V1/landingPage")
        logger.info("Navigated to Login Page")
        time.sleep(5)

        username_field = self.get_element(driver, By.ID, "username")
        username_field.send_keys(username)
        self.click_element(driver, self.get_element(driver, By.ID, "signIn"))
        logger.info("Username entered")

        password_field = self.get_element(driver, By.ID, "password")
        time.sleep(1) 
        password_field.send_keys(password)
        logger.info("Password entered")
        
        time.sleep(1) 
        self.click_element(driver, self.get_element(driver, By.ID, "signIn"))
        logger.info("Credentials submitted")
        
        try:
            time.sleep(5)
            if "Va/Dashboard" in driver.current_url:
                logger.info("Login successful, redirected to Dashboard.")
                return "LOGGED_IN"
            logger.info("Checking for 2FA screen...")
            sms_button = self.get_element(driver, By.ID, "button-verify-by-sms", timeout=5)
            if sms_button:
                self.click_element(driver, sms_button)
                logger.info("SMS 2FA selected")
                return "OTP_NEEDED"
        except Exception:
            logger.info("2FA screen not found or timed out. Assuming already logged in.")
            return "LOGGED_IN"

    def _perform_post_login_actions(self, driver, report_name):
        logger.info("Navigating to Inventory page...")
        time.sleep(5)
        driver.get("https://provision.vauto.app.coxautoinc.com/Va/Inventory/")
        
        logger.info("Waiting for 'Reports/Customize' button...")
        reports_btn = self.get_element(driver, By.XPATH, "//button[contains(text(), 'Reports/Customize')]")
        if reports_btn:
            self.click_element(driver, reports_btn)
            logger.info("'Reports/Customize' clicked")
        else:
            logger.warning("'Reports/Customize' button not found")    

        logger.info(f"Selecting Report: {report_name}...")
        report_item = self.get_element(driver, By.XPATH, f"//span[contains(text(), '{report_name}')]")
        if report_item:
            self.click_element(driver, report_item)
            logger.info("Report selected")
        else:
            logger.warning(f"Report '{report_name}' not found") 

        time.sleep(4)   
        
        logger.info("Downloading Excel...")
        excel_btn = self.get_element(driver, By.XPATH, "//span[text()='Excel']")
        if excel_btn:    
            self.click_element(driver, excel_btn)  
        else:
            logger.warning("Excel button not found")    
        
        logger.info("Excel download initiated")
        time.sleep(10)

    def _perform_cargurus_login_actions(self, driver, username, password):
        # Using the URL provided by the user
        url = "https://www.cargurus.com/Cars/dealerdashboard/app/home?tmLogin=true&serviceProvider=sp291629"
        driver.get(url)
        logger.info("Navigated to CarGurus Login Page")
        time.sleep(5)
        if "cargurus.com/Cars/dealerdashboard/app/home" in driver.current_url:
             logger.info("Successfully redirected to CarGurus domain.")
        else:
            # 1. Enter Email
            username_field = self.get_element(driver, By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            logger.info("CarGurus email entered")
            
            # 2. Click "Continue with email"
            continue_btn = self.get_element(driver, By.ID, "kc-login")
            self.click_element(driver, continue_btn)
            logger.info("CarGurus continue button clicked")
            
            # 3. Wait for Password field (Assuming it appears after email)
            # Note: The exact ID might depend on the next page, but often it's 'password'
            password_field = self.get_element(driver, By.ID, "password", timeout=10)
            password_field.send_keys(password)
            logger.info("CarGurus password entered")
            
            # 4. Submit (Button might be same 'kc-login' or different)
            # Re-fetching login button just in case
            login_btn = self.get_element(driver, By.ID, "kc-login")
            self.click_element(driver, login_btn)
            logger.info("CarGurus login form submitted")
            
            time.sleep(5)
        
    def _perform_cargurus_post_login_actions(self, driver):
        logger.info("Performing CarGurus post-login actions...")
        # Placeholder: Verify login? Navigate?
        if "cargurus.com/Cars/dealerdashboard/app/home" in driver.current_url:
            logger.info("Successfully redirected to CarGurus domain.")

            # Handle "Promote the right cars" popup
            try:
                logger.info("Checking for post-login popup...")
                # Using the specific class from user provided HTML, but XPATH text is more readable and likely stable enough for "Close"
                # The user HTML: <button class="hRxAe jve5q" type="button">Close</button>
                # OR <button aria-label="Close dialog" ...>
                
                # Trying specifically the "Close" text button first as it matches the user's intent to "close this pop"
                close_btn = self.get_element(driver, By.XPATH, "//button[text()='Close']", timeout=10)
                if close_btn:
                    self.click_element(driver, close_btn)
                    logger.info("Popup closed using 'Close' button.")
                else:
                    logger.info("'Close' button not found, checking for 'Close dialog' icon...")
                    close_icon = self.get_element(driver, By.XPATH, "//button[@aria-label='Close dialog']", timeout=5)
                    if close_icon:
                        self.click_element(driver, close_icon)
                        logger.info("Popup closed using 'Close dialog' icon.")
            except Exception as e:
                logger.warning(f"Popup close attempted but failed or popup not present: {e}")

            # Navigate to PriceVantage
            try:
                logger.info("Navigating to PriceVantage...")
                price_vantage_link = self.get_element(driver, By.XPATH, "//a[@title='PriceVantage']")
                if price_vantage_link:
                    self.click_element(driver, price_vantage_link)
                    logger.info("Clicked PriceVantage link.")
                    time.sleep(3) # Wait for page load
                else:
                    logger.warning("PriceVantage link not found")
            except Exception as e:
                logger.error(f"Failed to navigate to PriceVantage: {e}")
                return

            stores = [
                "Palm Beach Mitsubishi",
                "Taverna Chrysler Dodge Jeep Ram Fiat",
                "Taverna INFINITI North Miami"
            ]

            downloaded_files_map = [] # List of tuples (store_name, file_path)
            download_path = os.path.join(base_dir, "downloads", "cargurus")
            logger.info(f"Download path: {download_path}")
            
            for store in stores:
                try:
                    logger.info(f"Processing store: {store}")
                    
                    # Open Dealership Selector
                    logger.info("Opening dealership selector...")
                    dealership_dropdown = self.get_element(driver, By.XPATH, "//button[@aria-label='Change dealership']")
                    if dealership_dropdown:
                        self.click_element(driver, dealership_dropdown)
                        time.sleep(2)
                    else:
                        logger.warning("Dealership dropdown not found")
                    
                    # Select Store
                    logger.info(f"Selecting {store}...")
                    store_option = self.get_element(driver, By.XPATH, f"//span[contains(text(), '{store}')] | //div[contains(text(), '{store}')]")
                    if store_option:
                        self.click_element(driver, store_option)
                        logger.info(f"Selected {store}.")
                        time.sleep(3) # Wait for data to reload
                    else:
                        logger.warning(f"Store '{store}' not found in dropdown")

                    # Capture files before export
                    before_files = set(glob.glob(os.path.join(download_path, "*")))
                    logger.info(f"Files before export: {before_files}")
                    # Click Export
                    logger.info("Clicking Export button...")
                    export_btn = self.get_element(driver, By.XPATH, "//button[contains(text(), 'Export')]")
                    if export_btn:
                        self.click_element(driver, export_btn)
                        logger.info(f"Export initiated for {store}.")
                        
                        # Wait for NEW file to appear
                        timeout = 60
                        end_time = time.time() + timeout
                        new_file = None
                        logger.info("Waiting for new file to appear...")
                        while time.time() < end_time:
                            logger.info(f"Files in download folder: {glob.glob(os.path.join(download_path, "*"))}")
                            current_files = set(glob.glob(os.path.join(download_path, "*")))
                            new_files = current_files - before_files
                            if new_files:
                                logger.info(f"New files found: {new_files}")
                                # Filter out crdownload or tmp files if necessary, usually standard excel extensions are final
                                valid_new_files = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
                                if valid_new_files:
                                    new_file = valid_new_files[0] # Take the first new file found
                                    break
                            time.sleep(1)
                        
                        if new_file:
                            logger.info(f"New file file detected for {store}: {new_file}")
                            downloaded_files_map.append((store, new_file))
                        else:
                            logger.warning(f"Timeout waiting for file download for {store}")

                    else:
                        logger.warning("Export button not found")

                except Exception as e:
                    logger.error(f"Error processing store {store}: {e}")
                    continue
            
            logger.info("All stores processed. Starting aggregation...")
            
            if downloaded_files_map:
                try:
                    all_dfs = []
                    for store_name, file_path in downloaded_files_map:
                        try:
                            if file_path.endswith('.csv'):
                                df = pd.read_csv(file_path)
                            elif file_path.endswith(('.xls', '.xlsx')):
                                df = pd.read_excel(file_path)
                            else:
                                continue
                            
                            df['store'] = store_name
                            all_dfs.append(df)
                        except Exception as e:
                            logger.error(f"Error reading file {file_path}: {e}")
                    
                    if all_dfs:
                        final_df = pd.concat(all_dfs, ignore_index=True)
                        timestamp = datetime.now().strftime("%m.%d.%Y__%H:%M:%S")
                        combined_filename = f"CarGurus_Aggregated__{timestamp}.xlsx"
                        combined_path = os.path.join(download_path, combined_filename)
                        
                        final_df.to_excel(combined_path, index=False)
                        logger.info(f"Aggregated file saved to: {combined_path}")
                        
                        # Trigger upload for this specific file, or rely on upload_latest_file_to_s3 picking it up
                        # Since upload_latest_file_to_s3 picks the latest file, and we just saved this, it should work.
                        # self.upload_latest_file_to_s3("cargurus")
                    else:
                        logger.warning("No dataframes to aggregate.")
                except Exception as e:
                    logger.error(f"Error during aggregation: {e}")
            else:
                logger.warning("No files downloaded to aggregate.")
        else:
            logger.info("Failed to redirect to CarGurus domain.")    