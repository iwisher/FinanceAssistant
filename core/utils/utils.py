import re
import random

import torch
import whisper
from whisper import Whisper
  
def extract_video_info(text):
    """
    Extracts views, days, hours, and minutes from a YouTube video 
    description, handling different cases for missing time components.

    Args:
        text: The text containing the video information.

    Returns:
        A dictionary containing the extracted information, 
        or None if no match is found.
    """
    
    # Case 0: Months, Days, hours, and minutes
    pattern_mdhm = r"(\d+,\d+|\w+)\sviews\s(\d+)\smonths?\sago\s"
    match_mdhm = re.search(pattern_mdhm, text, re.VERBOSE)
    
    # Case 0: Months, Days, hours, and minutes
    pattern_week= r"(\d+,\d+|\w+)\sviews\s(\d+)\sweeks?\sago\s"
    match_week = re.search(pattern_week, text, re.VERBOSE)

    # Case 1: Days, hours, and minutes
    pattern_dhm = r"(\d+,\d+|\w+)\sviews\s(\d+)\sdays?\sago\s(\d+)\shour?s?,\s(\d+)\sminutes?"
    match_dhm = re.search(pattern_dhm, text, re.VERBOSE)

    # Case 2: Days and minutes
    pattern_dm = r"(\d+,\d+|\w+)\sviews\s(\d+)\sdays?\sago\s(\d+)\sminutes?"
    match_dm = re.search(pattern_dm, text, re.VERBOSE)

    # Case 3: Hours and minutes
    pattern_hm = r"(\d+,\d+|\w+)\sviews\s(\d+)\shours?\sago,\s(\d+)\sminutes?"
    match_hm = re.search(pattern_hm, text, re.VERBOSE)

    # Case 4: Only minutes
    pattern_m = r"(\d+,\d+|\w+)\sviews\s(\d+)\sminutes?\sago"
    match_m = re.search(pattern_m, text, re.VERBOSE)

    # Case 5: Only hours
    pattern_h = r"(\d+,\d+|\w+)\sviews\s(\d+)\shours?\sago"
    match_h = re.search(pattern_h, text, re.VERBOSE)

    if match_mdhm:
        views = int(match_mdhm.group(1).replace(",", "")) if match_mdhm.group(1).replace(",", "").isdigit() else match_mdhm.group(1)
        days = int(match_mdhm.group(2))*30 + random.randint(1, 31)
        hours = random.randint(1, 24)
        minutes = random.randint(1, 60)
    elif match_week:
        views = int(match_week.group(1).replace(",", "")) if match_week.group(1).replace(",", "").isdigit() else match_week.group(1)
        days = int(match_week.group(2))*7 + random.randint(1, 5)
        hours = random.randint(1, 24)
        minutes = random.randint(1, 60)
    elif match_dhm:
        views = int(match_dhm.group(1).replace(",", "")) if match_dhm.group(1).replace(",", "").isdigit() else match_dhm.group(1)
        days = int(match_dhm.group(2))
        hours = int(match_dhm.group(3))
        minutes = int(match_dhm.group(4))
    elif match_dm:
        views = int(match_dm.group(1).replace(",", "")) if match_dm.group(1).replace(",", "").isdigit() else match_dm.group(1)
        days = int(match_dm.group(2))
        hours = 0
        minutes = int(match_dm.group(3))
    elif match_hm:
        views = int(match_hm.group(1).replace(",", "")) if match_hm.group(1).replace(",", "").isdigit() else match_hm.group(1)
        days = 0
        hours = int(match_hm.group(2))
        minutes = int(match_hm.group(3))
    elif match_m:
        views = int(match_m.group(1).replace(",", "")) if match_m.group(1).replace(",", "").isdigit() else match_m.group(1)
        days = 0
        hours = 0
        minutes = int(match_m.group(2))
    elif match_h:
        views = int(match_h.group(1).replace(",", "")) if match_h.group(1).replace(",", "").isdigit() else match_h.group(1)
        days = 0
        hours = int(match_h.group(2))
        minutes = 0
    else:
        return None

    return {
        "views": views,
        "days": days,
        "hours": hours,
        "minutes": minutes,
    }

GLOBAL_WHISPER = None

def get_whisper()-> Whisper:
    global GLOBAL_WHISPER
    if GLOBAL_WHISPER is None:
        device = torch.device(
            'cuda') if torch.cuda.is_available() else torch.device('cpu')
        GLOBAL_WHISPER = whisper.load_model("turbo", device=device)
    
    # turbo is the bestter balance between speed and accuracy
    print("Whisper model loaded.")
    
    return    GLOBAL_WHISPER 

    
if __name__ == '__main__':
    # Test the function
    test_strings = [
        "Hurricane fallout, AlphaFold, Google breakup, Trump surge, VC giveback, TikTok survey by All-In Podcast 239,147 views 1 day ago 1 hour, 24 minutes",
        "In conversation with Mark Cuban by All-In Podcast 395,571 views 10 days ago 2 hours, 6 minutes",
        "Ingo Uytdehaage, Adyen | All-In Summit 2024 by All-In Podcast 36,900 views 3 days ago 25 minutes",
        "华尔街这是疯了吗？NaNa说美股(2024.10.11) by NaNa说美股 59,034 views 12 hours ago",
        "Yen Carry Trade, Recession odds grow, Buffett cash pile, Google ruled monopoly, Kamala picks Walz by All-In Podcast 444,957 views 44 minutes ago, 20 seconds",
        "Israeli prime minister warns U.N. peacekeepers to evacuate southern Lebanon by NBC News 1,567 views 30 minutes ago 1 minute, 38 seconds",
        "More young men are showing support for Donald Trump&nbsp; by NBC News No views 1 minute ago 2 minutes, 35 seconds",
        "Yen Carry Trade, Recession odds grow, Buffett cash pile, Google ruled monopoly, Kamala picks Walz by All-In Podcast 444,957 views 44 minutes ago",
        "Break up Google, Starbucks CEO out, Kamala’s price controls, Boeing disaster, Kursk offensive by All-In Podcast 511,296 views 1 month ago 1 hour, 46 minutes",
        "Yen Carry Trade, Recession odds grow, Buffett cash pile, Google ruled monopoly, Kamala picks Walz by All-In Podcast 444,965 views 2 months ago 1 hour, 44 minutes",
        "Marc Benioff | All-In Summit 2024 by All-In Podcast 177,597 views 4 weeks ago 40 minutes",
        "John Mearsheimer and Jeffrey Sachs | All-In Summit 2024 by All-In Podcast 1,867,233 views 3 weeks ago 54 minutes",
        "Manhunt underway for suspect after deadly home invasion by NBC News 770 views 44 minutes ago 1 minute, 26 seconds"
    ]

    for string in test_strings:
        result = extract_video_info(string)
        print(f"Input: {string}")
        print(f"Output: {result}")
        print()