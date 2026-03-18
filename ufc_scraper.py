import os
import re
import time
import json
import string
import logging
import datetime
import requests
import pint
from bs4 import BeautifulSoup
from typing import Optional, Union

# --- CONFIGURATION ---
PROJECT_NAME = 'scrape_ufc_stats'
RUN_25_ITR = False  # Set to False to scrape the entire UFC database
IS_IC_DEBUG = False
LOGGER = None

# --- UTILITY FUNCTIONS ---
def setup_basic_file_paths(project_name: str):
    cwd = os.getcwd()
    project_folder = os.path.join(cwd, project_name)
    os.makedirs(project_folder, exist_ok=True)
    data_folder = os.path.join(project_folder, 'data')
    os.makedirs(data_folder, exist_ok=True)
    log_folder = os.path.join(project_folder, 'logs')
    os.makedirs(log_folder, exist_ok=True)
    log_file_path = os.path.join(log_folder, f'{project_name}.log')
    return project_folder, data_folder, log_file_path

def setup_logger(log_file_path: str):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_format = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)
    return logger

def save_ndjson(data: dict, file_path: str):
    with open(file_path, 'a', encoding='utf-8') as dump_file:
        dump_file.write(f'{json.dumps(data)}\n')

# --- THE NETWORK REQUEST (WITH TIMEOUT FIX) ---
def basic_request(url: str, logger=None) -> str:
    retries = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    while retries < 5:
        try:
            # INCREASED TIMEOUT TO 20 SECONDS
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                return response.text
            if response.status_code == 429:
                if logger: logger.warning("Rate limited! Sleeping 10s...")
                time.sleep(10)
        except requests.exceptions.RequestException as e:
            if logger: logger.warning(f"Retry {retries+1}/5 for {url} due to: {e}")
        
        time.sleep(2)
        retries += 1
    raise RuntimeError(f"Could not reach {url} after 5 attempts.")

# --- PARSING LOGIC ---
def extract_fighter_links(html: str) -> set[str]:
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.select('tr.b-statistics__table-row a')
    return set([tag.get('href') for tag in tags])

def extract_bio_data(soup: BeautifulSoup) -> dict:
    try:
        phys_data = soup.select_one('.b-list__info-box_style_small-width').get_text(strip=True, separator='_').split('_')
        height, weight, reach, stance, dob = phys_data[1], phys_data[3], phys_data[5], phys_data[7], phys_data[9]
        
        # Metric Conversion Logic
        ureg = pint.UnitRegistry()
        h_cm = None
        if height and "--" not in height:
            f, i = re.findall(r'\d+', height)
            h_cm = round((int(f)*ureg.foot + int(i)*ureg.inch).to(ureg.centimeter).magnitude, 2)
        
        w_kg = round(int(re.search(r'\d+', weight).group()) * 0.453592, 2) if weight and "--" not in weight else None
        r_cm = int(re.search(r'\d+', reach).group()) * 2.54 if reach and "--" not in reach else None
        
        return {"height_cm": h_cm, "weight_in_kg": w_kg, "reach_in_cm": r_cm, "stance": stance if stance != '--' else None}
    except:
        return {"height_cm": None, "weight_in_kg": None, "reach_in_cm": None, "stance": None}

def extract_career_data(soup: BeautifulSoup) -> dict:
    try:
        career = soup.select_one('.b-list__info-box_style_middle-width').get_text(strip=True, separator='_').split('_')
        return {
            'sig_strikes_landed_pm': float(career[2]),
            'sig_striking_accuracy': float(career[4].replace('%', '')),
            'takedown_accuracy': float(career[12].replace('%', ''))
        }
    except:
        return {'sig_strikes_landed_pm': 0, 'sig_striking_accuracy': 0, 'takedown_accuracy': 0}

def get_fighter_profile(url: str) -> dict:
    html = basic_request(url, LOGGER)
    soup = BeautifulSoup(html, 'html.parser')
    
    name = soup.select_one('.b-content__title-highlight').get_text(strip=True)
    
    # --- FIXED RECORD PARSING ---
    # Get the raw text: e.g., "Record: 24-3-1 (1 NC)"
    raw_record = soup.select_one('.b-content__title-record').get_text(strip=True)
    # Split to get just the numbers part: "24-3-1 (1 NC)"
    record_parts = raw_record.split(':')[-1].strip().split('-')
    
    try:
        wins = int(record_parts[0])
        losses = int(record_parts[1])
        
        # Use regex to find ONLY the first digit in the 'draws' section
        # This turns "1 (1 NC)" into just "1"
        draws_match = re.search(r'\d+', record_parts[2])
        draws = int(draws_match.group()) if draws_match else 0
        
        # OPTIONAL: Extract the NC count if you want it for your Medium post!
        nc_match = re.search(r'\((\d+)\s*NC\)', record_parts[2])
        no_contests = int(nc_match.group(1)) if nc_match else 0
        
    except (ValueError, IndexError) as e:
        LOGGER.warning(f"Record error for {name}: {e}")
        wins, losses, draws, no_contests = 0, 0, 0, 0
    # ----------------------------
    
    bio = extract_bio_data(soup)
    career = extract_career_data(soup)
    
    data = {
        "name": name, 
        "wins": wins, 
        "losses": losses, 
        "draws": draws,
        "no_contests": no_contests # Added this new field!
    }
    data.update(bio)
    data.update(career)
    return data

# --- MAIN EXECUTOR ---
if __name__ == "__main__":
    proj_folder, data_folder, log_path = setup_basic_file_paths(PROJECT_NAME)
    LOGGER = setup_logger(log_path)
    ndjson_path = os.path.join(data_folder, 'fighter_data.ndjson')
    
    LOGGER.info("Starting Scraper...")
    all_links = set()
    for char in string.ascii_lowercase:
        LOGGER.info(f"Fetching fighters starting with: {char.upper()}")
        try:
            links = extract_fighter_links(basic_request(f'http://ufcstats.com/statistics/fighters?char={char}&page=all', LOGGER))
            all_links.update(links)
        except: continue
    
    LOGGER.info(f"Found {len(all_links)} total fighters. Starting deep scrape...")
    
    for i, link in enumerate(all_links):
        try:
            profile = get_fighter_profile(link)
            save_ndjson(profile, ndjson_path)
            LOGGER.info(f"[{i+1}/{len(all_links)}] Scraped: {profile['name']}")
            
            if RUN_25_ITR and i >= 24: 
                LOGGER.info("Test run complete (25 fighters).")
                break
        except Exception as e:
            LOGGER.error(f"Failed on {link}: {e}")