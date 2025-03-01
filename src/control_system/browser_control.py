"""
Browser control module using Selenium.

This module handles browser automation tasks like opening URLs,
navigating pages, filling forms, etc.
"""

import logging
import time
from typing import Dict, List, Optional, Union, Any, Tuple

# Import selenium only when needed to prevent errors if not installed
logger = logging.getLogger(__name__)

class BrowserController:
    """Controller for browser automation using Selenium."""
    
    def __init__(self, browser_type: str = "chrome", headless: bool = False):
        """
        Initialize the browser controller.
        
        Args:
            browser_type: The type of browser to use (chrome, firefox, edge)
            headless: Whether to run the browser in headless mode
        """
        self.logger = logging.getLogger(__name__)
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.driver = None
        self.logger.info(f"Browser controller initialized for {browser_type}")
    
    def start_browser(self) -> bool:
        """
        Start a new browser session.
        
        Returns:
            True if successful, False otherwise
        """
        if self.driver is not None:
            self.logger.warning("Browser already running, closing existing session")
            self.close_browser()
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from selenium.webdriver.edge.service import Service as EdgeService

            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            
            if self.browser_type == "chrome":
                from selenium.webdriver.chrome.options import Options
                options = Options()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--start-maximized")
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.logger.info("Chrome browser started")
                
            elif self.browser_type == "firefox":
                from selenium.webdriver.firefox.options import Options
                options = Options()
                if self.headless:
                    options.add_argument("--headless")
                
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=options)
                self.logger.info("Firefox browser started")
                
            elif self.browser_type == "edge":
                from selenium.webdriver.edge.options import Options
                options = Options()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--start-maximized")
                
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=options)
                self.logger.info("Edge browser started")
                
            else:
                self.logger.error(f"Unsupported browser type: {self.browser_type}")
                return False
            
            # Set implicit wait time
            self.driver.implicitly_wait(10)
            return True
            
        except ImportError as e:
            self.logger.error(f"Missing required packages: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error starting browser: {str(e)}")
            return False
    
    def close_browser(self) -> bool:
        """
        Close the browser session.
        
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No browser session to close")
            return False
        
        try:
            self.driver.quit()
            self.driver = None
            self.logger.info("Browser closed")
            return True
        except Exception as e:
            self.logger.error(f"Error closing browser: {str(e)}")
            return False
    
    def navigate_to(self, url: str) -> bool:
        """
        Navigate to a specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No browser session, starting new one")
            if not self.start_browser():
                return False
        
        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            return False
    
    def get_current_url(self) -> str:
        """
        Get the current URL.
        
        Returns:
            Current URL or empty string if error
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return ""
        
        try:
            url = self.driver.current_url
            self.logger.debug(f"Current URL: {url}")
            return url
        except Exception as e:
            self.logger.error(f"Error getting current URL: {str(e)}")
            return ""
    
    def refresh_page(self) -> bool:
        """
        Refresh the current page.
        
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return False
        
        try:
            self.driver.refresh()
            self.logger.info("Page refreshed")
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing page: {str(e)}")
            return False
    
    def go_back(self) -> bool:
        """
        Navigate back to the previous page.
        
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return False
        
        try:
            self.driver.back()
            self.logger.info("Navigated back")
            return True
        except Exception as e:
            self.logger.error(f"Error navigating back: {str(e)}")
            return False
    
    def go_forward(self) -> bool:
        """
        Navigate forward to the next page.
        
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return False
        
        try:
            self.driver.forward()
            self.logger.info("Navigated forward")
            return True
        except Exception as e:
            self.logger.error(f"Error navigating forward: {str(e)}")
            return False
    
    def get_page_title(self) -> str:
        """
        Get the title of the current page.
        
        Returns:
            Page title or empty string if error
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return ""
        
        try:
            title = self.driver.title
            self.logger.debug(f"Page title: {title}")
            return title
        except Exception as e:
            self.logger.error(f"Error getting page title: {str(e)}")
            return ""
    
    def find_element(self, by_type: str, selector: str):
        """
        Find an element on the page.
        
        Args:
            by_type: Type of selector (id, class, name, xpath, css, tag, link_text)
            selector: The selector value to search for
            
        Returns:
            WebElement if found, None otherwise
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return None
        
        try:
            from selenium.webdriver.common.by import By
            
            by_types = {
                "id": By.ID,
                "class": By.CLASS_NAME,
                "name": By.NAME,
                "xpath": By.XPATH,
                "css": By.CSS_SELECTOR,
                "tag": By.TAG_NAME,
                "link_text": By.LINK_TEXT
            }
            
            if by_type.lower() not in by_types:
                self.logger.error(f"Invalid selector type: {by_type}")
                return None
            
            element = self.driver.find_element(by_types[by_type.lower()], selector)
            self.logger.debug(f"Found element with {by_type}='{selector}'")
            return element
        except Exception as e:
            self.logger.error(f"Error finding element with {by_type}='{selector}': {str(e)}")
            return None
    
    def click_element(self, by_type: str, selector: str) -> bool:
        """
        Click an element on the page.
        
        Args:
            by_type: Type of selector (id, class, name, xpath, css, tag, link_text)
            selector: The selector value to search for
            
        Returns:
            True if successful, False otherwise
        """
        element = self.find_element(by_type, selector)
        if element is None:
            return False
        
        try:
            element.click()
            self.logger.info(f"Clicked element with {by_type}='{selector}'")
            return True
        except Exception as e:
            self.logger.error(f"Error clicking element with {by_type}='{selector}': {str(e)}")
            return False
    
    def fill_text_field(self, by_type: str, selector: str, text: str) -> bool:
        """
        Fill a text field with specified text.
        
        Args:
            by_type: Type of selector (id, class, name, xpath, css, tag)
            selector: The selector value to search for
            text: Text to enter into the field
            
        Returns:
            True if successful, False otherwise
        """
        element = self.find_element(by_type, selector)
        if element is None:
            return False
        
        try:
            element.clear()  # Clear existing text
            element.send_keys(text)
            self.logger.info(f"Filled text field with {by_type}='{selector}'")
            return True
        except Exception as e:
            self.logger.error(f"Error filling text field with {by_type}='{selector}': {str(e)}")
            return False
    
    def submit_form(self, by_type: str, selector: str) -> bool:
        """
        Submit a form.
        
        Args:
            by_type: Type of selector for the form (id, class, name, xpath, css, tag)
            selector: The selector value to search for
            
        Returns:
            True if successful, False otherwise
        """
        element = self.find_element(by_type, selector)
        if element is None:
            return False
        
        try:
            element.submit()
            self.logger.info(f"Submitted form with {by_type}='{selector}'")
            return True
        except Exception as e:
            self.logger.error(f"Error submitting form with {by_type}='{selector}': {str(e)}")
            return False
    
    def take_screenshot(self, filename: str) -> bool:
        """
        Take a screenshot of the current browser window.
        
        Args:
            filename: Name of the file to save the screenshot
            
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return False
        
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return False
    
    def execute_javascript(self, script: str, *args):
        """
        Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the JavaScript
            
        Returns:
            Result of the JavaScript execution or None if error
        """
        if self.driver is None:
            self.logger.warning("No active browser session")
            return None
        
        try:
            result = self.driver.execute_script(script, *args)
            self.logger.info("Executed JavaScript")
            return result
        except Exception as e:
            self.logger.error(f"Error executing JavaScript: {str(e)}")
            return None