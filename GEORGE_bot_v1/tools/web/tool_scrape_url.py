import os
import logging
from urllib.parse import urljoin, urlparse
import json
import hashlib
import mimetypes
import time
import requests
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import concurrent.futures

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SeleniumDriver:
    def __init__(self):
        self.options = Options()
        # Remove the --headless argument
        # self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920x1080')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--disable-extensions')
        self.options.add_experimental_option('prefs', {
            'download.default_directory': os.getcwd(),
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        })

    def __enter__(self):
        # Use a specific Chrome driver executable path (if needed)
        # driver_path = '/path/to/chromedriver'  # Replace with your actual path
        # self.driver = webdriver.Chrome(executable_path=driver_path, options=self.options)
        self.driver = webdriver.Chrome(options=self.options)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'driver'):
            self.driver.quit()


def tool_scrape_url(
        url: str,
        scrape_images: bool = False,
        scrape_text: bool = False,
        scrape_links: bool = False,
        save_images: bool = False,
        save_text: bool = False,
        save_links: bool = False,
        get_whole_page: bool = False,
        save_path: str = None,
        return_type: str = "all"  # Options: "all", "images", "text", "links", "html"
) -> dict:
    """
    Scrapes content from a URL based on specified parameters using Selenium and Chrome.
    Returns all scraping information (images, text, links, etc.).

    Args:
        url (str): The URL to scrape.
        scrape_images (bool): Whether to scrape images from the page.
        scrape_text (bool): Whether to scrape text content from the page.
        scrape_links (bool): Whether to scrape links from the page.
        save_images (bool): Whether to save scraped images locally.
        save_text (bool): Whether to save scraped text locally.
        save_links (bool): Whether to save scraped links locally.
        get_whole_page (bool): Whether to get the entire HTML content.
        save_path (str): Base path for saving files (default: current directory).
        return_type (str): What type of content to return in the response. Options: "all", "images", "text", "links", "html"

    Returns:
        dict: A dictionary containing:
            - status: "success" or "failure"
            - message: Status message
            - data: Dictionary containing scraped content based on return_type
            - scraped_images: List of image data (URLs, alt text, etc.)
            - scraped_text_elements: List of text element data (type, content, etc.)
            - scraped_links: List of link data (URLs, text, etc.)
            - saved_images: List of saved image paths
            - saved_text: Whether text was saved to a file
            - saved_links: Whether links were saved to a file
            - html_saved: Whether the entire HTML content was saved
    """
    try:
        # Initialize result dictionary
        result = {
            "status": "success",
            "message": "Scraping completed successfully",
            "data": {},
            "scraped_images": [],
            "scraped_text_elements": [],
            "scraped_links": [],
            "saved_images": [],
            "saved_text": False,
            "saved_links": False,
            "html_saved": False
        }

        # Set default save path if none provided
        save_path = save_path or os.getcwd()
        os.makedirs(save_path, exist_ok=True)

        # Headers for requests (add more if needed)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        }

        with SeleniumDriver() as driver:
            # Navigate to the URL with timeout and wait for page load
            driver.set_page_load_timeout(30)
            driver.get(url)

            # Wait for the page to be fully loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Allow dynamic content to load (adjust based on page characteristics)
            time.sleep(2)  # Adjust based on page characteristics

            # Scroll to load lazy content
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Get the page source after JavaScript execution
            page_source = driver.page_source

            # Get whole page HTML if requested
            if get_whole_page:
                result["data"]["html"] = page_source
                if save_text:
                    html_path = os.path.join(save_path, "page.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    logger.info(f"Saved HTML to {html_path}")
                    result["html_saved"] = True

            # Scrape images
            if scrape_images:
                images = []
                image_elements = driver.find_elements(By.TAG_NAME, "img")
                result["scraped_images"] = [
                    {
                        "url": element.get_attribute('src') or '',
                        "alt": element.get_attribute('alt') or '',
                        "title": element.get_attribute('title') or '',
                        "width": element.get_attribute('width') or '',
                        "height": element.get_attribute('height') or '',
                        "natural_width": element.get_property('naturalWidth'),
                        "natural_height": element.get_property('naturalHeight'),
                        "is_displayed": element.is_displayed()
                    }
                    for element in image_elements
                ]

                def process_image(element):
                    try:
                        img_url = element.get_attribute('src')
                        if not img_url:
                            return None

                        if save_images and img_url.startswith(('http://', 'https://')):
                            try:
                                response = requests.get(img_url, headers=headers, timeout=10)
                                if response.status_code == 200:
                                    content_type = response.headers.get('content-type', '')
                                    if content_type.startswith('image/'):
                                        img_name = hashlib.md5(response.content).hexdigest()[:8]
                                        ext = mimetypes.guess_extension(content_type) or '.jpg'
                                        img_path = os.path.join(save_path, "images", f"{img_name}{ext}")
                                        os.makedirs(os.path.dirname(img_path), exist_ok=True)

                                        with open(img_path, 'wb') as f:
                                            f.write(response.content)
                                        result["saved_images"].append(img_path)
                                        logger.info(f"Saved image to {img_path}")
                            except Exception as e:
                                logger.error(f"Failed to save image {img_url}: {str(e)}")

                        return img_url
                    except Exception as e:
                        logger.error(f"Failed to process image element: {str(e)}")
                        return None

                # Process images concurrently
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    image_urls = list(filter(None, executor.map(process_image, image_elements)))
                    images.extend(image_urls)

                result["data"]["images"] = images

            # Scrape text with JavaScript-rendered content
            if scrape_text:
                text_content = []
                text_elements = driver.find_elements(By.CSS_SELECTOR,
                                                    'p, h1, h2, h3, h4, h5, h6, article, section, main, [role="main"], [role="article"]')
                result["scraped_text_elements"] = [
                    {
                        "type": element.tag_name,
                        "content": element.text.strip(),
                        "html_classes": element.get_attribute('class') or '',
                        "id": element.get_attribute('id') or '',
                        "is_visible": element.is_displayed(),
                        "location": element.location
                    }
                    for element in text_elements
                ]

                for element in text_elements:
                    try:
                        text = element.text.strip()
                        if text:
                            text_content.append({
                                "type": element.tag_name,
                                "content": text,
                                "html_classes": element.get_attribute('class') or '',
                                "id": element.get_attribute('id') or '',
                                "is_visible": element.is_displayed(),
                                "location": element.location
                            })
                    except Exception as e:
                        logger.error(f"Failed to process text element: {str(e)}")

                result["data"]["text"] = text_content

                if save_text:
                    text_path = os.path.join(save_path, "content.txt")
                    with open(text_path, 'w', encoding='utf-8') as f:
                        for item in text_content:
                            f.write(f"{item['type'].upper()}:\n")
                            if item['id']:
                                f.write(f"ID: {item['id']}\n")
                            if item['html_classes']:
                                f.write(f"Classes: {item['html_classes']}\n")
                            f.write(f"Content: {item['content']}\n")
                            f.write(f"Visible: {item['is_visible']}\n\n")
                    logger.info(f"Saved text content to {text_path}")
                    result["saved_text"] = True

            # Scrape links including JavaScript-generated ones
            if scrape_links:
                links = []
                base_domain = urlparse(url).netloc
                link_elements = driver.find_elements(By.TAG_NAME, "a")
                result["scraped_links"] = [
                    {
                        "url": element.get_attribute('href') or '',
                        "text": element.text.strip(),
                        "title": element.get_attribute('title') or '',
                        "is_internal": urlparse(element.get_attribute('href') or '').netloc == base_domain,
                        "rel": element.get_attribute('rel') or '',
                        "target": element.get_attribute('target') or '',
                        "is_visible": element.is_displayed(),
                        "location": element.location
                    }
                    for element in link_elements
                ]

                for element in link_elements:
                    try:
                        href = element.get_attribute('href')
                        if href:
                            links.append({
                                "url": href,
                                "text": element.text.strip(),
                                "title": element.get_attribute('title') or '',
                                "is_internal": urlparse(href).netloc == base_domain,
                                "rel": element.get_attribute('rel') or '',
                                "target": element.get_attribute('target') or '',
                                "is_visible": element.is_displayed(),
                                "location": element.location
                            })
                    except Exception as e:
                        logger.error(f"Failed to process link element: {str(e)}")

                result["data"]["links"] = links

                if save_links:
                    links_path = os.path.join(save_path, "links.json")
                    with open(links_path, 'w', encoding='utf-8') as f:
                        json.dump(links, f, indent=2)
                    logger.info(f"Saved links to {links_path}")
                    result["saved_links"] = True

            # Filter return data based on return_type
            if return_type != "all":
                if return_type in result["data"]:
                    result["data"] = {return_type: result["data"][return_type]}
                else:
                    result["message"] += f" (Requested return_type '{return_type}' not found in scraped data)"

        return result

    except TimeoutException as e:
        error_msg = f"Page load timeout: {str(e)}"
        logger.error(error_msg)
        return {"status": "failure", "message": error_msg, "data": {}}
    except WebDriverException as e:
        error_msg = f"Selenium WebDriver error: {str(e)}"
        logger.error(error_msg)
        return {"status": "failure", "message": error_msg, "data": {}}
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return {"status": "failure", "message": error_msg, "data": {}}