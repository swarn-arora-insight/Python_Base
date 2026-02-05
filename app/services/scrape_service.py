# app/services/scrape_service.py
import os
import time
import uuid
import logging
from typing import Dict, Optional
from selenium import webdriver
import pyotp
import resend
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.logging import logger
import asyncio
from services.data_processing import DataProcessor
import glob
from dotenv import load_dotenv
load_dotenv()
base_dir = os.getcwd()

# Global Session Store: {session_id: driver}
# In a production environment, this might need more robust handling (e.g., Redis + Grid)
# but for this standalone service, a global dict works.
SESSIONS: Dict[str, webdriver.Chrome] = {}



class ScrapeService:
    def __init__(self):
        self.data_processor = DataProcessor()

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
        elif webpage == "drivecentric":
            profile_path = os.path.join(base_dir, "chrome_data_drivecentric")
            download_path = os.path.join(base_dir, "downloads", "drivecentric")
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

    @staticmethod
    def send_error_email(context: str, exception: Exception):
        try:
            resend.api_key = os.getenv("RESEND_API_KEY")
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_list = traceback.extract_tb(exc_traceback)
            
            filename = "Unknown"
            line_no = "Unknown"
            func_name = "Unknown"
            
            if tb_list:
                # Get the last frame for the most specific location
                last_frame = tb_list[-1]
                filename = last_frame.filename
                line_no = last_frame.lineno
                func_name = last_frame.name
            
            subject = f"Scraping Error - {context}"
            html_content = f"""
            <h3>Error Notification</h3>
            <p><strong>Message:</strong> {str(exception)}</p>
            <p><strong>Context:</strong> {context}</p>
            <p><strong>File:</strong> {filename}</p>
            <p><strong>Function:</strong> {func_name}</p>
            <p><strong>Line Number:</strong> {line_no}</p>
            <hr>
            <h3>Traceback</h3>
            <pre>{traceback.format_exc()}</pre>
            """
            
            params = {
                "from": "CRM-Taverna.ai <info@tavernaai.com>",
                "to": ["alok.yadav@knowledgeexcel.com"],
                "subject": subject,
                "html": html_content,
                "reply_to": "alok.yadav@knowledgeexcel.com"
            }
            
            r = resend.Emails.send(params)
            logger.info(f"Error email sent: {r}")
            
        except Exception as email_error:
            logger.error(f"Failed to send error email: {email_error}")

    # --- Flows ---

    def upload_latest_file_to_s3(self, webpage: str):
        return self.data_processor.process_and_upload(webpage, base_dir)

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
            # self.send_error_email("start_login_flow (vAuto)", e)
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
            # self.send_error_email("submit_otp_flow (vAuto)", e)
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
            # self.send_error_email("start_cargurus_login_flow", e)
            self.close_driver_safely(session_id)
            raise e


    async def start_drivecentric_login_flow(self, username: str, password: str, report_name: str) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new DriveCentric session: {session_id}")
        
        driver = self.setup_driver("drivecentric")
        SESSIONS[session_id] = driver
        logger.info(f"DriveCentric session started: {SESSIONS}")

        try:
            status = self._perform_drivecentric_login_actions(driver, username, password)
            if status == "OTP_NEEDED":
                return {
                    "status": "waiting_for_otp", 
                    "session_id": session_id, 
                    "message": "2FA required. Please submit OTP."
                }
            else:
                self._perform_drivecentric_post_login_actions(driver)
                self.close_driver_safely(session_id)
                self.upload_latest_file_to_s3("drivecentric")
                
                return {"status": "success", "message": "DriveCentric scrape completed successfully."}
        except Exception as e:
            logger.error(f"Error in start_drivecentric_login_flow: {e}")
            self.send_error_email("start_drivecentric_login_flow", e)
            self.close_driver_safely(session_id)
            raise e

    async def submit_drivecentric_otp_flow(self, session_id: str, otp: str) -> Dict[str, str]:
        if session_id not in SESSIONS:
            raise ValueError("Session not found or expired")
        
        driver = SESSIONS[session_id]
        
        try:
            logger.info("Waiting for OTP input field...")
            # Updated selector based on user provided HTML: id="code"
            otp_field = self.get_element(driver, By.ID, "code") 
            otp_field.send_keys(otp)
            
            # Updated submit button based on user provided HTML
            verify_btn = self.get_element(driver, By.CSS_SELECTOR, "button[type='submit']")
            if verify_btn:
                self.click_element(driver, verify_btn)
                logger.info("OTP submitted")
            else:
                logger.warning("OTP button not found")
            
            # Wait for successful login URL
            logger.info("Waiting for redirect to sales pipeline...")
            try:
                WebDriverWait(driver, 30).until(EC.url_contains("/pipeline/sales"))
                logger.info("Redirected to sales pipeline successfully.")
            except Exception:
                logger.warning("Timed out waiting for sales pipeline URL. Proceeding to post-login actions anyway.")

            self._perform_drivecentric_post_login_actions(driver)
            self.close_driver_safely(session_id)
            
            self.upload_latest_file_to_s3("drivecentric")
            return {"status": "success", "message": "DriveCentric scrape completed successfully."}
        
        except Exception as e:
            logger.error(f"Error in submit_drivecentric_otp_flow: {e}")
            self.send_error_email("submit_drivecentric_otp_flow", e)
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
        time.sleep(4)
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
                    # logger.info(f"Files before export: {before_files}")
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
                            # logger.info(f"Files in download folder: {glob.glob(os.path.join(download_path, "*"))}")
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
            logger.info(f"Downloaded files map: {downloaded_files_map}")
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
                        timestamp = datetime.now().strftime("%m.%d.%Y__%H-%M-%S")
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

    def _perform_drivecentric_login_actions(self, driver, username, password):
        url = "https://app.drivecentric.com"
        driver.get(url)
        logger.info("Navigated to DriveCentric Login Page")
        time.sleep(5)

        try:
            # Check if already logged in
            if "login" not in driver.current_url.lower():
                 logger.info("Url does not contain 'login', assuming already logged in or redirected.")
            
            # Additional check: If we are already on the sales pipeline, return LOGGED_IN
            if "/pipeline/sales" in driver.current_url:
                 logger.info("Already on sales pipeline.")
                 return "LOGGED_IN"

            username_field = self.get_element(driver, By.ID, "signInFormUsername")
            username_field.clear()
            username_field.send_keys(username)
            logger.info("DriveCentric username entered")

            password_field = self.get_element(driver, By.ID, "signInFormPassword")
            password_field.clear()
            password_field.send_keys(password)
            logger.info("DriveCentric password entered")

            # Uncommented and verified selector
            submit_btn = self.get_element(driver, By.CSS_SELECTOR, "button[type='submit']")
            if submit_btn:
                self.click_element(driver, submit_btn)
                logger.info("DriveCentric login submitted")
            else:
                logger.error("Login submit button not found")
            
            time.sleep(5)

            # Check for OTP Page
            # Unique element on OTP page: <drc-custom-confirm-sign-in> or input with id="code"
            # Using input id="code" as a reliable indicator
            try:
                # Wait for OTP input to appear
                otp_input = self.get_element(driver, By.ID, "code", timeout=5)
                
                if otp_input:
                    logger.info("OTP field detected. 2FA required.")
                    
                    # Check for TOTP Secret
                    totp_secret = os.getenv("DRIVECENTRIC_TOTP_SECRET")
                    if totp_secret:
                        try:
                            logger.info("Auto-generating TOTP code...")
                            totp = pyotp.TOTP(totp_secret)
                            current_otp = totp.now()
                            
                            otp_input.send_keys(current_otp)
                            logger.info("Auto-filled OTP code.")
                            
                            # Click Verify/Submit
                            verify_btn = self.get_element(driver, By.CSS_SELECTOR, "button[type='submit']")
                            if verify_btn:
                                self.click_element(driver, verify_btn)
                                logger.info("Submitted OTP automatically.")
                                
                                # Wait for redirect
                                try:
                                    WebDriverWait(driver, 15).until(EC.url_contains("/pipeline/sales"))
                                    logger.info("Auto-2FA successful. Redirected to sales pipeline.")
                                    return "LOGGED_IN"
                                except Exception:
                                    logger.warning("Auto-2FA submitted but did not redirect quickly. Checking URL again...")
                            else:
                                logger.warning("Verify button not found for auto-2FA.")
                                
                        except Exception as otp_e:
                            logger.error(f"Error during auto-2FA: {otp_e}")
                            # Fallback to manual if auto fails
                    else:
                        logger.info("No DRIVECENTRIC_TOTP_SECRET found. Manual OTP required.")

                    return "OTP_NEEDED"
            except Exception:
                pass
            
            # Check for success
            if "/pipeline/sales" in driver.current_url:
                 logger.info("Redirected to sales pipeline immediately.")
                 return "LOGGED_IN"

            # If we are here, we might be loading or on an intermediate page. 
            # Let's wait a bit more or assume logged in if no OTP was found but no error.
            # But safer to return OTP_NEEDED if ANY ambiguity, or wait for URL.
            
            logger.info("Checking final URL state...")
            try:
                 WebDriverWait(driver, 10).until(EC.url_contains("/pipeline/sales"))
                 return "LOGGED_IN"
            except Exception:
                 logger.warning("Did not reach sales pipeline and did not find OTP field. Potential issue.")
                 # Fallback: check again for OTP just in case it loaded late
                 try:
                    if self.get_element(driver, By.ID, "code", timeout=2):
                        return "OTP_NEEDED"
                 except: 
                     pass
                 
                 return "LOGGED_IN" # Assuming logged in for now, otherwise script would fail later

        except Exception as e:
            logger.error(f"Error during DriveCentric login: {e}")
            raise e

    def _perform_drivecentric_post_login_actions(self, driver):
        logger.info("Performing DriveCentric post-login actions...")
        
        downloaded_files_map = []
        download_path = os.path.join(base_dir, "downloads", "drivecentric")
        os.makedirs(download_path, exist_ok=True)

        try:
            # 1. Get available stores
            stores = self._get_drivecentric_stores(driver)
            logger.info(f"Found stores: {stores}")

            for store in stores:
                logger.info(f"Processing store: {store}")
                
                try:
                    # 2. Switch to store
                    self._switch_to_drivecentric_store(driver, store)
                    time.sleep(5) # Wait for store switch to settle

                    # 3. Navigate to Mining Deals
                    logger.info("Navigating to Mining Deals...")
                    driver.get("https://app.drivecentric.com/#/mining/deals/")
                    time.sleep(5) # Wait for page load

                    # 4. Apply Filters
                    self._apply_drivecentric_filters(driver)

                    # 5. Download
                    before_files = set(glob.glob(os.path.join(download_path, "*")))
                    self._drivecentric_download_report(driver)
                    
                    # Wait for download
                    timeout = 60
                    end_time = time.time() + timeout
                    new_file = None
                    while time.time() < end_time:
                        current_files = set(glob.glob(os.path.join(download_path, "*")))
                        new_files = current_files - before_files
                        valid_new_files = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
                        if valid_new_files:
                            new_file = valid_new_files[0]
                            break
                        time.sleep(1)
                    
                    if new_file:
                        logger.info(f"Downloaded file for {store}: {new_file}")
                        downloaded_files_map.append((store, new_file))
                    else:
                        logger.warning(f"Timeout downloading file for {store}")

                except Exception as inner_e:
                    logger.error(f"Error processing store {store}: {inner_e}")
                    self.send_error_email(f"DriveCentric Store Loop: {store}", inner_e)
                    continue

            # 6. Aggregate
            if downloaded_files_map:
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
                        logger.error(f"Error reading {file_path}: {e}")
                
                if all_dfs:
                    final_df = pd.concat(all_dfs, ignore_index=True)
                    timestamp = datetime.now().strftime("%m.%d.%Y__%H-%M-%S")
                    combined_filename = f"DriveCentric_Aggregated__{timestamp}.xlsx"
                    combined_path = os.path.join(download_path, combined_filename)
                    final_df.to_excel(combined_path, index=False)
                    logger.info(f"Aggregated file saved: {combined_path}")
            else:
                logger.warning("No files to aggregate.")

        except Exception as e:
            logger.error(f"Error in DriveCentric post-login actions: {e}")
            self.send_error_email("DriveCentric post-login actions", e)
            raise e

    def _get_drivecentric_stores(self, driver):
        try:
            logger.info("Opening profile menu to find stores...")
            # Click Profile Menu (Avatar)
            # Selector from user HTML: <drc-avatar ...> or generic avatar class
            profile_menu = self.get_element(driver, By.CSS_SELECTOR, "drc-avatar, .ui-kit-avatar")
            self.click_element(driver, profile_menu)
            time.sleep(1)

            # Click Change Stores
            logger.info("Clicking Change Stores...")
            # Look for "Change Stores" text
            change_stores_btn = self.get_element(driver, By.XPATH, "//div[contains(text(), 'Change Stores')]")
            self.click_element(driver, change_stores_btn)
            time.sleep(2)

            # Get Store Names
            logger.info("Scraping store names...")
            store_elements = driver.find_elements(By.CSS_SELECTOR, ".store-name-label")
            stores = [el.text.strip() for el in store_elements if el.text.strip()]
            
            # Close the dialog
            close_btn = self.get_element(driver, By.CSS_SELECTOR, ".card-close")
            if close_btn:
                self.click_element(driver, close_btn)
            else:
                # If no close button, maybe click outside or escape (optional, but card-close is in HTML)
                pass
            
            time.sleep(1)
            return stores

        except Exception as e:
            logger.error(f"Error getting stores: {e}")
            raise e

    def _switch_to_drivecentric_store(self, driver, store_name):
        try:
            logger.info(f"Switching to {store_name}...")
            # 1. Open Profile
            profile_menu = self.get_element(driver, By.CSS_SELECTOR, "drc-avatar, .ui-kit-avatar")
            self.click_element(driver, profile_menu)
            time.sleep(1)

            # 2. Open Change Stores
            change_stores_btn = self.get_element(driver, By.XPATH, "//div[contains(text(), 'Change Stores')]")
            self.click_element(driver, change_stores_btn)
            time.sleep(2)

            # 3. Select Store
            # Find the specific store element
            store_el = self.get_element(driver, By.XPATH, f"//div[contains(@class, 'store-name-label') and contains(text(), '{store_name}')]")
            self.click_element(driver, store_el)
            logger.info(f"Clicked {store_name}")
            
            # Wait for reload (URL might change or page refreshes)
            time.sleep(5)

        except Exception as e:
            logger.error(f"Error switching to store {store_name}: {e}")
            raise e

    def _apply_drivecentric_filters(self, driver):
        try:
            logger.info("Applying filters...")
            
            # 1. Click "Add Filter"
            # Selector: <span ...>Add Filter</span> inside <drc-chip>
            add_filter_btn = self.get_element(driver, By.XPATH, "//span[contains(text(), 'Add Filter')]")
            self.click_element(driver, add_filter_btn)
            time.sleep(1)

            # 2. Select "Deal Date Created"
            # Selector: text inside <drc-single-selection-list-item>
            date_filter_opt = self.get_element(driver, By.XPATH, "//div[contains(text(), 'Deal Date Created')]")
            self.click_element(driver, date_filter_opt)
            time.sleep(1)

            # 3. Select "Yesterday"
            # Selector: text "Yesterday" (it's a label next to radio)
            yesterday_opt = self.get_element(driver, By.XPATH, "//span[contains(text(), 'Yesterday')]")
            self.click_element(driver, yesterday_opt)
            time.sleep(1)

            # 4. Click "Save"
            # Selector: button with text "Save" inside drc-button-popup list
            # The HTML shows a Save button in the footer of the popup. 
            # We can look for the button that specifically says "Save".
            save_btn = self.get_element(driver, By.XPATH, "//button//span[contains(text(), 'Save')]")
            self.click_element(driver, save_btn)
            logger.info("Filter 'Yesterday' applied.")
            time.sleep(3) # Wait for results to filter

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            raise e

    def _drivecentric_download_report(self, driver):
        try:
            logger.info("Initiating download...")
            # Click Ellipsis
            # Select by icon name or button class. Trying both or parent button.
            # <drc-icon name="fa-ellipsis-v"> inside button
            ellipsis_btn = self.get_element(driver, By.CSS_SELECTOR, "drc-icon[name='fa-ellipsis-v']")
            # We need to click the button containing this icon usually, or the icon itself might work if it bubbles
            # Let's try finding the parent button
            try:
                ellipsis_btn = ellipsis_btn.find_element(By.XPATH, "./ancestor::button")
            except:
                pass # Try clicking icon directly if parent lookup fails
            
            self.click_element(driver, ellipsis_btn)
            time.sleep(1)
            
            # Click Download inside the list
            download_btn = self.get_element(driver, By.XPATH, "//button[contains(text(), 'Download')]")
            self.click_element(driver, download_btn)
            logger.info("Clicked Download.")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise e    