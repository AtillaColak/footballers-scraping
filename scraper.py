import pandas as pd
import json
import selenium
from bs4 import BeautifulSoup as bs 
import requests 
import re
import os
import time

# Let's get scrapin.
# Time complexity O(1), granted I know the amount of data and number of iteration steps. 
# BELOW ARE HELPER METHODS FOR CLARITY. 
# PS: I used a lot of prints for debugging. I commented them out once I scraped. They might come in handy in the future.


# https://cdnjs.cloudflare.com/ajax/libs/flag-icon-css/3.3.0/flags/4x3/de.svg 
# this is my first time seeing this open source styling libraries of cloudflare. But this is better than downloading the images. 
# Now I can dynamically load the flags from here and avoid putting the image loading burden on the frontend. 
# I just need a conversion method that'll convert the nationality cell of a player to the respective cdns image svg to inject to the game.

def convert_nationality_to_svg(td_cell : str) -> str:
    # assuming all 3-digit country codes extend from their 2-digit versions, I just have to substring it from the cell html.
    # input will be like: <td -ignore stylistics-><div -ignore stylistics-><a href="/country.php?countryId=FRA" -ignore stylistics-><span -ignore stylistics-></span></a></div></td>
    match = re.search(r'countryId=([A-Z]+)', td_cell)

    # Extract the country ID from the match
    if match:
        country_id = match.group(1)
        # Get the first two letters of the country ID
        first_two_letters = country_id[:2]
        return f"https://cdnjs.cloudflare.com/ajax/libs/flag-icon-css/3.3.0/flags/4x3/{first_two_letters}.svg"
    else:
        print("Country ID not found in the string.")


def extract_image(td_cell, destination_path) -> str:
    # input will be like: <td -ignore stylistics-><a href="/player.php?pid=85260"><img src="https://cdn.soccerwiki.org/images/player/85260.png" data-src="https://cdn.soccerwiki.org/images/player/85260.png" alt="Kylian Mbappé"></a></td>
    # steps: download the image at that src to the destination path with the id, add the [id].png string to the images cell in the df.
    img = td_cell.find('img')
    address = img['data-src']
    
    # Extracting the player ID from the image source URL
    player_id = address.split('/')[-1].split('.')[0]

    
    # Constructing the filename with the player ID
    filename = f"{player_id}.png"
    # print(address)
    # print(player_id)
    # print(filename)
    
    # Download the image
    response = requests.get(address)
    
    # Checking if the request was successful
    if response.status_code == 200:
        # Saving the image to the destination path
        with open(os.path.join(destination_path, filename), 'wb') as f:
            f.write(response.content)
        return filename
    else:
        # If the request was not successful, return None
        return None
    
    

def extract_name(td_cell) -> str: 
    # input will be like: <td class="text-left"><a style="text-transform:none" href="/player.php?pid=85260">Kylian Mbappé</a></td>
    a_tag = td_cell.find('a')

    # Extract the name text
    name = a_tag.text
    # print(name)
    return name

def extract_club(td_cell) -> str: 
    # input will be like: <td class="text-left"><a style="text-transform:none" href="/squad.php?clubid=338">Paris Saint-Germain</a></td>
    a_tag = td_cell.find('a')
    # same code above, but in the future I might need to change it so better to keep it separate.
    # Extract the club text
    club = a_tag.text
    # print(club)
    return club

def extract_position(td_cell) -> str: 
    # input will be like: <td class="text-left text-dark" data-sort="1024"><span data-toggle="tooltip" title="" data-original-title="Attacking Midfielder Left, Forward Left Centre">AM(L),F(LC)</span></td>
    span_tag = td_cell.find('span')
    # print(span_tag)

    # Extract the title attribute
    if span_tag and 'title' in span_tag.attrs:
        # Extract the title attribute
        title = span_tag['title']

        # Manipulate the title to form the desired string
        position = title.split(',')[0].strip() 
        # print(position)
        return position
    else:
        return "Position not found"

def extract_height(td_cell) -> str: 
    # input will be like: <td class="text-center text-dark">178</td>
    height = td_cell.text
    # print(height)
    return height

def extract_foot(td_cell) -> str: 
    # input will be like: <td class="text-center text-dark">Right</td>
    foot = td_cell.text
    # print(foot)
    return foot 

def extract_age(td_cell) -> str: 
    # input will be like: <td class="text-center text-dark" width="50" style="width:50px !important;min-width:50px !important;max-width:50px !important;">25</td>
    age = td_cell.text
    # print(age)
    return age

# then scrape the players. 
url_base = "https://en.soccerwiki.org/search/player?minrating=90&maxrating=99"

# addresses and data structures
player_data_path = "/finalized_data.json"
images = "/player_images/" # I know it's not cool to use absolute paths but this is just a script apart from the actual build. 
players_df = pd.DataFrame(columns=['nationality','image','name','club','position','height','foot', 'age'])

for i in range(38):
    offset = i * 10 
    url_current = url_base + f"&offset={offset}" 
    # Fetch the HTML content
    response = requests.get(url_current)
    html_content = response.text

    # Parse the HTML content
    soup = bs(html_content, 'html.parser')

    # Find the first tbody element and all rows in it (which should be 10). 
    player_rows = soup.find('tbody').find_all("tr")
    
    # iterate over rows.
    for each in player_rows: 
        # handle the cells. 
        # print(tds)
        tds = each.find_all("td")
        nationality = convert_nationality_to_svg(str(tds[0]))
        # I should've done this process concurrent with multiple threads to make it more efficient.
        # but it's small data so it won't be effort to improve efficiency as it's already a short process.
        image = extract_image(tds[1], images)
        name = extract_name(tds[2])
        club = extract_club(tds[3])
        position = extract_position(tds[4])
        height = extract_height(tds[5])
        foot = extract_foot(tds[6])
        age = extract_age(tds[7])
        
        time.sleep(0.3)  # Adjust the sleep time as needed
        
        # add the player to the df. 
        new_player = {"nationality": nationality, "image": image, "name": name, 
                     "club": club, "position": position, "height": height, "foot": foot, "age": age}
        players_df = players_df.append(new_player, ignore_index=True)

# convert df to json and save it to the folder.
players_df.to_json(player_data_path, orient='records')