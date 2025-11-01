import os
import requests

# GitHub API endpoint for the folder
API_URL = "https://api.github.com/repos/pashov/audits/contents/team/md"

# Output directory
OUTPUT_DIR = "downloaded_md_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Step 1: Fetch folder contents from GitHub API
response = requests.get(API_URL)
if response.status_code != 200:
    raise Exception(f"Failed to fetch {API_URL}: {response.status_code}")

files = response.json()

# Step 2: Filter for .md files and download
count = 0
for file in files:
    if file["name"].endswith(".md"):
        print(f"Downloading {file['name']}...")
        content = requests.get(file["download_url"])
        if content.status_code == 200:
            with open(os.path.join(OUTPUT_DIR, file["name"]), "wb") as f:
                f.write(content.content)
            count += 1
        else:
            print(f"❌ Failed to download {file['name']}")

print(f"\n✅ Downloaded {count} Markdown files into '{OUTPUT_DIR}' folder.")
