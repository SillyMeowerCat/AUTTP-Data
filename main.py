SCRAPE_LIMIT = 20
print("[!] IF YOU FIND ANY ERRORS PLEASE REPORT TO SILLYMEOWERCAT ON REDDIT OR GITHUB")

PREFIX = "UTTP"
url = f"https://www.youtube.com/results?search_query={PREFIX}&sp=EgIQAg%3D%3D"

# Importing external libraries
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

#Initializing the console
console = Console()
console.rule("[bold blue]AUTTP Scraper[/bold blue]")

#Checking for updates
def update():
    try:
        resp = requests.get("https://raw.githubusercontent.com/SillyMeowerCat/AUTTP-Data/refs/heads/main/data.json",timeout=10)
        resp.raise_for_status()
        console.print("[green]JSON is up to date[/green]")
        return resp.json()
    except Exception as e:
        console.print("[yellow]JSON could not be loaded, defaulting to cache[/yellow]")
        if os.path.exists("data.json"):
            with open("data.json", "r") as f:
                console.print("[green]Loaded cache[/green]")
                return json.load(f)
        else:
            console.print("[yellow]No cache found, creating one[/yellow]")
            return []

#Fetching Channel Names
def fetch_names(username, driver):
    try:
        url = f"https://www.youtube.com/{username}"
        driver.get(url)
        time.sleep(2)
        try:
            name_elem = driver.find_element(By.XPATH, "//ytd-c4-tabbed-header-renderer//h1//yt-formatted-string")
            name = name_elem.text.strip()
            if name:
                return name
        except Exception as e:
            console.print("[yellow]Error fetching name: " + str(e) + "[/yellow]")
        try:
            name = driver.title.replace(" - YouTube", "").strip()
            if name and not name.startswith("@"):
                return name
        except Exception as e:
            console.print("[yellow]Error fetching name: " + str(e) + "[/yellow]")
    except Exception as e:
        console.print(f"[red]Error fetching name: {username} Please go to the JSON and get the name or contact SillyMeowerCat[/red]")

#Deduplication Method
local_data = []
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        local_data = json.load(f)
        console.print(f"[green]Loaded {len(local_data)} entries from local data.json[/green]")

existing_usernames = set()
for dat in local_data:
    if isinstance(dat, dict):
        uname = dat.get('username', '').strip().lower()
        if uname:
            existing_usernames.add(uname)

#Merges Data
data = update()
if not isinstance(data, list):
    data = []

# Use local data as the base
data = local_data

console.print(f"[blue]Loaded {len(existing_usernames)} existing usernames from database[/blue]")

#Sets Options to bypass captcha and other issues
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('window-size=1920,1080')
driver = webdriver.Chrome(options=options)

#Looks for channel names
updated = False
for channel in data:
    if ('name' not in channel or not channel['name']) and 'username' in channel:
        actual_name = fetch_names(channel['username'], driver)
        if actual_name and actual_name != channel.get('name', ''):
            channel['name'] = actual_name
            updated = True

#Searches for UTTP
driver.get(url)
time.sleep(2)
channel_cards = driver.find_elements(By.XPATH, "//ytd-channel-renderer")

new_data = []
new_usernames_this_run = set()
counter = 0

#Main Logic
for card in channel_cards:
    if counter >= SCRAPE_LIMIT:
        break
    try:
        name_elem = card.find_element(By.XPATH, ".//ytd-channel-name//div[@id='text-container']//yt-formatted-string")
        name = name_elem.text.strip()
        handle_element = card.find_element(By.XPATH, ".//*[contains(text(), '@')]")
        username = handle_element.text.strip()
        username_norm = username.strip().lower()
        
        # Check if username matches PREFIX criteria first
        if username and username.startswith('@') and PREFIX.lower() in username.lower():
            # Then check if this username already exists in our data
            if username_norm not in existing_usernames and username_norm not in new_usernames_this_run:
                #Checks if the name is AUTTP
                if not ("anti" in name.lower() or "auttp" in name.lower() or "anti" in username.lower() or "auttp" in username.lower()):
                    data.append({"name": name, "username": username})
                    new_data.append({"name": name, "username": username})
                    existing_usernames.add(username_norm)
                    new_usernames_this_run.add(username_norm)
                    counter += 1
                    console.print(f"[green]Found new username: {username}[/green]")
                else:
                  console.print(f"[cyan]Skipping non-UTTP username: {username}[/cyan]")
            else:
                console.print(f"[yellow]Skipping duplicate: {username}[/yellow]")
    except Exception as e:
        console.print("[red]Error parsing channel card: " + str(e) + "[/red]")
driver.quit()

if new_data:
    table = Table(title="New Usernames Found", box=box.DOUBLE_EDGE, header_style="bold magenta")
    table.add_column("Channel Name", style="cyan")
    table.add_column("Username", style="green")
    for dat in new_data:
        table.add_row(dat['name'], dat['username'])
    console.print(table)
else:
    console.print("[bold yellow]No new usernames found[/bold yellow]")

if updated:
    console.print("[bold green]Updated existing usernames[/bold green]")

#Prevents JSON Overwrites
if new_data or updated:
    with open("data.json", 'w') as f:
        json.dump(data, f, indent=4)
    console.print("[green]JSON updated[/green]")
else:
    console.print("[yellow]No changes to save[/yellow]")
