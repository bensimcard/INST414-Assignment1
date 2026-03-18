**Author:** Benjamin Sim
**Course:** INST414 - Data Science Techniques  
**Date:** February 2026

## Project Overview
This repository contains the code and data for my INST414 Assignment 1 project. The goal of this analysis was to act as a data scientist working for the UFC. The project attempts to answer a specific business question: Do physical outliers (like reach-to-height ratio) and tactical traits (like fighting stance) act as reliable predictors of career success in mixed martial arts?

To answer this, I built a custom Python web scraper to collect historical fighter data from `ufcstats.com`, engineered new performance metrics using Pandas, and visualized the findings.

Read the full analysis and methodology on Medium here: 

## Repository Contents

ufc_scraper.py: The data collection script. It utilizes `BeautifulSoup` and `requests` to scrape fighter profiles. It includes error handling (like Regex parsing for "No Contests") and custom timeouts to navigate serverside latency.

analyze_ufc.py: The data processing and visualization script. It loads the raw `.ndjson` data, filters out fighters with fewer than three bouts, engineers the "Ape Index" and "Win Rate" features, and uses `seaborn` to generate the final charts.

final_cleaned_ufc_data.csv: The clean, structured dataset exported after the Pandas analysis, containing metrics for established UFC fighters.

chart_ape_index.png: A scatter plot with a regression line demonstrating the positive correlation between a higher reach-to-height ratio and career win percentage.

chart_stance.png: A bar chart comparing the historical win rates of the Orthodox, Southpaw, and Switch fighting stances.

# How to Run the Code

# 1. Requirements
Ensure you have Python installed, then install the necessary dependencies:
pip install pandas beautifulsoup4 requests pint matplotlib seaborn

# 2. Data Collection
To collect the raw data, run the scraper script. 
This will output a raw `fighter_data.ndjson` file into a dynamically generated `scrape_ufc_stats/data/` directory.

# 3. Data Analysis
To clean the data, engineer the features, and generate the visualizations, run the analysis script:
python analyze_ufc.py

This will output the clean CSV and the two PNG chart files directly into your project directory.

# Key Findings
1.  **The Ape Index:** There is a measurable positive correlation between a fighter's "Ape Index" (reach divided by height) and their long-term win rate. Fighters with an index > 1.04 consistently outperform those with average proportions.
2.  **Stance Advantage:** The "Switch" and "Southpaw" stances hold a slight statistical advantage over the traditional "Orthodox" stance, likely due to the unfamiliar angles they present to majority-Orthodox opponents.