import sys
import time
import requests
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("/home/jovyan/workspaces/src")))

from feed.storage.neo4j_connection import get_connection

SUBREDDITS = [
    "AddisonRae", "AliceEve", "AnadeArmas", "AnneHathaway", "AnyaTaylorJoy", "BarbaraPalvin", 
    "BotezLive", "BrecBassinger", "BrittanySnow", "BunnyGirls", "Celebs", "ChloeBennet", 
    "ClaireHolt2", "DanielleCampbell", "DoutzenKroes", "ElleFanning", "ElsaHosk", 
    "EmmaWatson", "EmmyRossum", "EricaLindbeck", "ErinHeatherton", "Florence_Pugh", 
    "GWNerdy", "GalGadot", "GirlsfromChess", "HannahBeast", "HazelGraye", "HermioneCorfield", 
    "HogwartsGoneWild", "JenniferLawrence", "Josephine_Skriver", "KatDennings", 
    "KatrinaBowden", "KiraKosarin", "KiraKosarinLewd", "LeightonMeester", "MargotRobbie", 
    "MarinKitagawaR34", "McKaylaMaroney", "MelissaBenoist", "MinkaKelly", "MirandaKerr", 
    "Models", "NatalieDormer", "NinaDobrev", "Nina_Agdal", "OfflinetvGirls", 
    "OliviaRodrigoNSFW", "OneTrueMentalOut", "OvileeWorship", "PhoebeTonkin", "Pokimane", 
    "PortiaDoubleday", "RachelCook", "RachelMcAdams", "SammiHanratty", "SaraSampaio", 
    "SarahHyland", "SelenaGomez", "ShaileneWoodley", "StellaMaxwell", "SydneySweeney", 
    "TOS_girls", "TaylorSwift", "TaylorSwiftCandids", "TaylorSwiftMidriff", 
    "Taylorhillfantasy", "VanessaHudgens", "VolleyballGirls", "WatchItForThePlot", 
    "angourierice", "annakendrick", "blakelively", "candiceswanepoel", "erinmoriartyNEW", 
    "haydenpanettiere", "howdyhowdyyallhot", "islafisher", "jenniferlovehewitt", 
    "jessicaalba", "karliekloss", "kateupton", "kayascodelario", "kristenbell", 
    "kristinefroseth", "lizgillies", "milanavayntrub", "natalieportman", "oliviadunne", 
    "sophieturner", "sunisalee", "victoriajustice", "victorious", "vsangels", 
    "SommerRay", "kendalljenner", "popheadscirclejerk", "WhatAWeeb", "ArianaGrande",
    "flexibility", "SonoBisqueDoll", "tspics", "lululemon", "JennaOrtega", "AnyaChalotra"
]

def estimate_volume(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=100"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ImageboardCheck/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return 0
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        now = time.time()
        one_day_ago = now - 86400
        count = 0
        for p in posts:
            if p["data"]["created_utc"] > one_day_ago:
                count += 1
        return count
    except Exception:
        return 0

def main():
    neo4j = get_connection()
    print(f"Connected to Neo4j. Importing {len(SUBREDDITS)} subreddits...")
    
    # Bulk merge subreddits
    query = """
    UNWIND $subs as sub_name
    MERGE (s:Subreddit {name: sub_name})
    ON CREATE SET s.created_at = datetime()
    RETURN count(s) as merged
    """
    res = neo4j.execute_write(query, parameters={"subs": SUBREDDITS})
    print(f"Merged {res[0]['merged']} subreddits.")
    
    print("\nEstimating 24h volume (last 100 posts check):")
    results = []
    for sub in SUBREDDITS:
        count = estimate_volume(sub)
        results.append((sub, count))
        # Rate limiting to be polite
        time.sleep(0.5)
    
    # Sort by volume
    results.sort(key=lambda x: x[1], reverse=True)
    
    print("\nSubreddit | 24h Est. Volume")
    print("-" * 30)
    for sub, count in results:
        v_str = str(count) if count < 100 else "100+"
        print(f"{sub:20} | {v_str}")

if __name__ == "__main__":
    main()
