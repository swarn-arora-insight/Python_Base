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

# Global Session Store: {session_id: driver}
# In a production environment, this might need more robust handling (e.g., Redis + Grid)
# but for this standalone service, a global dict works.
SESSIONS: Dict[str, webdriver.Chrome] = {}

class ScrapeService:
    @staticmethod
    def setup_driver():
        # Define paths - adapting to be relative to the service or project root
        # Assuming run from project root or handling absolute paths carefully
        base_dir = os.getcwd() 
        download_path = os.path.join(base_dir, "downloads")
        profile_path = os.path.join(base_dir, "chrome_data")
        
        if not os.path.exists(download_path):
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

    # def convert_xls_to_xlsx(xls_path):
    #     xlsx_path = xls_path.replace(".xls", ".xlsx")
    #     df = pd.read_excel(xls_path, engine="xlrd")
    #     df.to_excel(xlsx_path, index=False, engine="openpyxl")
    #     return xlsx_path

    def upload_latest_file_to_s3(self):
        try:
            download_path = os.path.join(os.getcwd(), "downloads")
            # Get list of files in download path
            list_of_files = glob.glob(os.path.join(download_path, "*")) 
            
            if not list_of_files:
                logger.warning("No files found in downloads directory to upload.")
                return

            # Find the latest file based on creation time
            latest_file = max(list_of_files, key=os.path.getctime)
            logger.info(f"Latest file found: {latest_file}")

            # Read file into DataFrame
            if latest_file.endswith(".csv"):
                df = pd.read_csv(latest_file)
            elif latest_file.endswith(".xlsx") or latest_file.endswith(".xls"):
                if latest_file.endswith(".xls"):
                    logger.info("xls file found")
                    try:
                    # latest_file = self.convert_xls_to_xlsx(latest_file)
                        xlsx_path = latest_file.replace(".xls", ".xlsx")
                        logger.info(f"xlsx_path: {xlsx_path}")
                        df = pd.read_excel(latest_file, engine="xlrd")
                    
                        df.to_excel(xlsx_path, index=False, engine="openpyxl")
                        logger.info("xlsx file created")
                        df = pd.read_excel(xlsx_path)
                        logger.info(f"df: {df}")
                    except Exception as e:
                        logger.error(f"Error converting xls to xlsx: {e}")
                        raise
                else:
                    df = pd.read_excel(latest_file)

            else:
                logger.warning(f"Unsupported file format: {latest_file}")
                return

            # --- SANITIZE DATAFRAME ---
            # Convert all object columns to string to avoid PyArrow mixed-type errors
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)
            # --------------------------

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
        
        driver = self.setup_driver()
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
                self.upload_latest_file_to_s3()
                
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
            
            self.upload_latest_file_to_s3()
            return {"status": "success", "message": "Scrape completed successfully."}
        
        except Exception as e:
            logger.error(f"Error in submit_otp_flow: {e}")
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