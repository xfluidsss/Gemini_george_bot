tool_type_for_TOOL_MANAGER = "web"
tool_depth_crowler_short_description = "   Crawls web pages, extracts images and links, and optionally saves them to files.  "

import json
import urllib
import requests
from requests.exceptions import SSLError
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
import os
from PIL import Image

# --- Configuration ---

# Set of phrases to exclude from links
EXCLUDED_PHRASES = {
    "membership", "login", "sign up", "register", "account", "forgot password",
    "user profile", "checkout", "shopping cart", "payment", "terms of service",
    "privacy policy", "about us", "contact us", "error", "help", "support", "faq",
    "careers", "blog", "forum", "community", "newsletter", "subscription",
    "unsubscribe", "feedback", "feedback form", "feedback survey",
    "feedback submission", "feedback response"
}

# --- Helper Functions ---

def sanitize_filename(filename):
    """Replaces invalid characters in a filename with underscores."""
    safe_filename = re.sub(r'[\/:*?"<>|]', '_', filename)
    return safe_filename


def filter_link(link):
    """Filters links based on excluded phrases and image extensions."""
    if any(phrase.lower() in link.lower() for phrase in EXCLUDED_PHRASES):
        return False

    image_extensions = [".jpeg", ".jpg", ".gif", ".png"]
    for extension in image_extensions:
        if link.endswith(extension):
            return False
    return True


# --- Crawler Functions ---

def crawl_links(starting_links, visited_links=None, depth=1, max_depth=3, strategy="depth_first"):
    """Crawls a set of links recursively, extracting images and links."""
    if visited_links is None:
        visited_links = set()

    all_found_links = set()
    extracted_images = []  # Changed to a list to store image data

    # Depth-First Search (DFS)
    if strategy == "depth_first":
        for link in starting_links:
            if link not in visited_links and depth <= max_depth:
                try:
                    response = requests.get(link)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    new_links = set()
                    images = []  # Changed to a list to store image data

                    # Extract images with alt descriptions
                    for tag in soup.find_all('img'):
                        href = tag.get('src')
                        if href:
                            image_url = urljoin(link, href)
                            alt_description = tag.get('alt', "no alt description")  # Default to "no alt description"
                            image_source = "img"  # Indicate source as 'img'
                            images.append(
                                {
                                    "url": image_url,
                                    "alt": alt_description,
                                    "source": image_source
                                }
                            )
                            print(f"Found image: {image_url}  {alt_description}")

                    # Extract links
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if href and href.startswith('http'):
                            if filter_link(href):
                                new_links.add(href)
                                if href not in visited_links:
                                    with open(f"Layer{depth}.txt", "a", encoding="utf-8") as file:
                                        print(f"Saving link {href} on layer {depth}")
                                        file.write(href + '\n')
                        else:
                            full_link = urljoin(str(link), str(href))
                            if full_link.startswith('http') and filter_link(full_link):
                                new_links.add(full_link)
                                if full_link not in visited_links:
                                    with open(f"Layer{depth}.txt", "a", encoding="utf-8") as file:
                                        print(f"Saving link {full_link} on layer {depth}")
                                        file.write(full_link + '\n')

                    all_found_links.update(new_links)
                    extracted_images.extend(images)

                    # Recursively crawl new links
                    all_found_links, visited_links, extracted_images = crawl_links(
                        new_links, visited_links, depth + 1, max_depth, strategy
                    )

                except requests.exceptions.RequestException as e:
                    print(f"Error crawling link: {link}, Reason: {e}")
                finally:
                    visited_links.add(link)
            else:
                print("Link has already been visited or depth limit reached: Skipping...")

    # Breadth-First Search (BFS)
    elif strategy == "breadth_first":
        links_to_visit = starting_links.copy()
        while links_to_visit and depth <= max_depth:
            current_links = links_to_visit.copy()
            links_to_visit.clear()
            for link in current_links:
                if link not in visited_links:
                    try:
                        response = requests.get(link)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        new_links = set()
                        images = []  # Changed to a list to store image data

                        # Extract images with alt descriptions
                        for tag in soup.find_all('img'):
                            href = tag.get('src')
                            if href:
                                image_url = urljoin(link, href)
                                alt_description = tag.get('alt', "no alt description")
                                image_source = "img"
                                images.append(
                                    {
                                        "url": image_url,
                                        "alt": alt_description,
                                        "source": image_source
                                    }
                                )
                                print(f"Found image: {image_url}  {alt_description}")

                        # Extract links
                        for link in soup.find_all('a'):
                            href = link.get('href')
                            if href and href.startswith('http'):
                                if filter_link(href):
                                    new_links.add(href)
                                    if href not in visited_links:
                                        with open(f"Layer{depth}.txt", "a", encoding="utf-8") as file:
                                            print(f"Saving link {href} on layer {depth}")
                                            file.write(href + '\n')
                            else:
                                full_link = urljoin(str(link), str(href))
                                if full_link.startswith('http') and filter_link(full_link):
                                    new_links.add(full_link)
                                    if full_link not in visited_links:
                                        with open(f"Layer{depth}.txt", "a", encoding="utf-8") as file:
                                            print(f"Saving link {full_link} on layer {depth}")
                                            file.write(full_link + '\n')

                        all_found_links.update(new_links)
                        extracted_images.extend(images)

                        # Add new links to the list to be visited
                        links_to_visit.update(new_links)

                    except requests.exceptions.RequestException as e:
                        print(f"Error crawling link: {link}, Reason: {e}")
                    finally:
                        visited_links.add(link)
                else:
                    print("Link has already been visited: Skipping...")
            depth += 1
    else:
        print("Depth limit reached: Stopping crawling.")

    print(f"Processing Layer: {depth}")
    return all_found_links, visited_links, extracted_images

# --- Tool Function ---

def tool_depth_crowler(
    links: list[str],
    max_depth: int = 3,
    strategy: str = "depth_first",
    save_images: bool = False,
    save_links: bool = False,
    save_folder: str = "scraped_data",
    return_found_links: bool = True,
    return_found_images: bool = True,
):
    """
    Crawls web pages, extracts images and links, and optionally saves them to files.

    Args:
        links (list[str]): List of starting URLs to crawl.
        max_depth (int): The maximum depth to crawl.
        strategy (str): Crawling strategy depth_first" or breadth_first
        save_images (bool): Whether to save extracted images.
        save_links (bool): Whether to save extracted links.
        save_folder (str): The directory to save scraped data.
        return_found_links (bool): Whether to return the list of found links.
        return_found_images (bool): Whether to return the list of found images.

    Returns:
        dict: A dictionary containing the following keys:
            - found_links: A list of found links at each depth level
            - found_images: A list of found images at each depth level
            - message: A message indicating the completion of crawling.
    """
    # Create text files for each layer if they don't exist
    for i in range(1, max_depth + 1):
        with open(f"Layer{i}.txt", "w") as file:
            pass

    # Create text files for extracted images from each layer
    for i in range(1, max_depth + 1):
        with open(f"Images_Layer{i}.txt", "w") as file:
            pass

    # Initialize sets to store links and visited links
    all_found_links = set()
    visited_links = set()

    # Crawl links recursively through multiple layers
    found_links = []
    found_images = []
    for depth in range(1, max_depth + 1):
        links, visited_links, extracted_images = crawl_links(
            links, visited_links, depth=depth, max_depth=max_depth, strategy=strategy
        )

        # Save links if requested
        if save_links:
            os.makedirs(save_folder, exist_ok=True)
            with open(os.path.join(save_folder, f"Layer{depth}.txt"), "w", encoding="utf-8") as file:
                for link in links:
                    file.write(link + "\n")

        # Save images if requested
        if save_images:
            os.makedirs(save_folder, exist_ok=True)
            with open(os.path.join(save_folder, f"Images_Layer{depth}.txt"), "w", encoding="utf-8") as file:
                for image_data in extracted_images:
                    file.write(f"{image_data['url']} ****** {image_data['alt']} ****** {image_data['source']}\n")

        # Store found links and images for return
        if return_found_links:
            found_links.append(list(links))
        if return_found_images:
            found_images.append(extracted_images)

    # Create the response dictionary
    response = {"message": "Web page crawling and image extraction completed."}

    # Add found links and images to the response if requested
    if return_found_links:
        response["found_links"] = found_links
    if return_found_images:
        response["found_images"] = found_images

    return response