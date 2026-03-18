import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os

print("Starting UFC Data Analysis...")

# ==========================================
# 1. LOAD THE DATA
# ==========================================
data = []
file_path = 'scrape_ufc_stats/data/fighter_data.ndjson'

if not os.path.exists(file_path):
    print(f"Error: Could not find {file_path}. Did the scraper finish running?")
    exit()

with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        data.append(json.loads(line))

df = pd.DataFrame(data)
print(f"Successfully loaded {len(df)} fighters from the raw data.")

# ==========================================
# 2. DATA CLEANING & FEATURE ENGINEERING
# ==========================================

print("Cleaning data and engineering features...")

# Ensure no_contests exists (in case some fighters didn't have it)
if 'no_contests' not in df.columns:
    df['no_contests'] = 0

# Calculate Total Fights
df['total_fights'] = df['wins'] + df['losses'] + df['draws'] + df['no_contests']

# FILTER: Keep only established fighters (3 or more fights)
df_clean = df[df['total_fights'] >= 3].copy()

# FEATURE 1: Win Rate
df_clean['win_rate'] = df_clean['wins'] / df_clean['total_fights']

# FEATURE 2: The Ape Index (Reach divided by Height)
# We must drop rows where height or reach is missing to avoid math errors
df_clean = df_clean.dropna(subset=['height_cm', 'reach_in_cm'])
df_clean['ape_index'] = df_clean['reach_in_cm'] / df_clean['height_cm']

df_clean = df_clean[(df_clean['ape_index'] > 0.85) & (df_clean['ape_index'] < 1.15)]

print(f"Data cleaned! Analyzing {len(df_clean)} established fighters.")

# ==========================================
# 3. EXPLORATORY DATA ANALYSIS (VISUALIZATIONS)
# ==========================================

print("Generating charts...")

sns.set_theme(style="whitegrid")

# --- CHART 1: Ape Index vs. Win Rate ---
plt.figure(figsize=(10, 6))
sns.regplot(
    x='ape_index', 
    y='win_rate', 
    data=df_clean, 
    scatter_kws={'alpha': 0.3, 'color': '#3498db'}, 
    line_kws={'color': '#e74c3c', 'linewidth': 2}
)
plt.title('The Ape Index: Does a Reach Advantage Equal More Wins?', fontsize=14, fontweight='bold')
plt.xlabel('Ape Index (Reach ÷ Height)', fontsize=12)
plt.ylabel('Career Win Rate (%)', fontsize=12)
plt.tight_layout()
plt.savefig('chart_ape_index.png')
print("- Saved: chart_ape_index.png")

# --- CHART 2: Stance vs. Win Rate ---
plt.figure(figsize=(8, 5))
stance_data = df_clean.groupby('stance')['win_rate'].mean().sort_values(ascending=False)

stance_plot = stance_data.plot(kind='bar', color=['#2ecc71', '#f1c40f', '#e67e22', '#95a5a6'])
plt.title('Average UFC Win Rate by Fighting Stance', fontsize=14, fontweight='bold')
plt.xlabel('Fighting Stance', fontsize=12)
plt.ylabel('Average Career Win Rate', fontsize=12)
plt.xticks(rotation=0)

for p in stance_plot.patches:
    stance_plot.annotate(f"{p.get_height():.1%}", 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha='center', va='center', xytext=(0, 5), textcoords='offset points')

plt.tight_layout()
plt.savefig('chart_stance.png')
print("- Saved: chart_stance.png")

# ==========================================
# 4. EXPORT FINAL DATASET
# ==========================================

final_columns = ['name', 'wins', 'losses', 'draws', 'total_fights', 'win_rate', 
                 'height_cm', 'reach_in_cm', 'ape_index', 'stance', 
                 'sig_striking_accuracy', 'takedown_accuracy']

df_export = df_clean[final_columns].sort_values(by='win_rate', ascending=False)
df_export.to_csv('final_cleaned_ufc_data.csv', index=False)
print("- Saved: final_cleaned_ufc_data.csv")

print("Analysis Complete! You are ready to write your Medium post.")