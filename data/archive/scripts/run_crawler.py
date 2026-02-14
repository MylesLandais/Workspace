#!/usr/bin/env python3
"""Production script to run the Reddit crawler."""

import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from feed.crawler.reddit_crawler import RedditCrawler, CrawlerConfig


# Updated subscription list
SUBREDDITS = [
    "3d6", "4kTV", "5MeODMT", "aiArt", "airsonic", "allthingsprotoss", "ambientmusic", "Amd", 
    "Anarcho_Capitalism", "AnarchyChess", "androiddev", "anime", "antivirus", "AnyaChalotra", 
    "archlinux", "ArianaGrande", "ArtificialInteligence", "AskCulinary", "audioengineering", 
    "awesomewm", "AZURE", "BB_Stock", "binance", "blueteamsec", "boardgames", "btrfs", 
    "bugbounty", "BuyItForLife", "callofcthulhu", "carbonsteel", "cardano", "CemuPiracy", 
    "Celebs", "cheatengine", "chia", "Cisco", "citypop", "CleaningTips", "Clojure", "CloneHero", 
    "comfyui", "commandline", "computervision", "Controllers", "CrimsonDesert", "crtgaming", 
    "Crypto_com", "CustomKeyboards", "cutenoobs", "cybersecurity", "DarkAcademia", "Daytrading", 
    "DeadOrAlive", "debian", "deeplearning", "desktops", "DigitalCognition", "Discord_Bots", 
    "dividends", "DIYAudioCables", "DnB", "DnDHomebrew", "docker", "Documentaries", 
    "DolphinEmulator", "econmonitor", "Economics", "EDH", "eink", "ElectricalEngineering", 
    "emby", "emulation", "EmulationOniOS", "ErgoMechKeyboards", "FinalFantasy", 
    "FireEmblemHeroes", "FireEmblemThreeHouses", "FluxAI", "foliosociety", "foobar2000", 
    "Forgotten_Realms", "frugalmalefashion", "GirlsfromChess", "google", "hacking", 
    "hackthebox", "handbrake", "harrypotter", "hermanmiller", "hogwartslegacyJKR", 
    "homeautomation", "HomeDataCenter", "HomeNetworking", "homestead", "hometheater", 
    "howdyhowdyyallhot", "HowToHack", "Hue", "HVAC", "hyprland", "i2p", "InstagramMarketing", 
    "interiordecorating", "investing", "inZOI", "irc", "ITManagers", "JanitorAI_Official", 
    "Jazz", "jellyfin", "JennaOrtega", "jquery", "JRPG", "killteam", "kilocode", "kodi", 
    "laufey", "launchbox", "lawofattraction", "LeagueofLegendsMeta", "learnmachinelearning", 
    "LibbyApp", "Libraries", "LifeProTips", "linux", "linux_gaming", "linuxadmin", 
    "LittleTailBronx", "Live2D", "livesound", "lockpicking", "LollipopChainsaw", "longevity", 
    "M1Finance", "MachineLearning", "macsysadmin", "malelivingspace", "MAME", "mangadex", 
    "mangapiracy", "MetaphorReFantazio", "mikumikudance", "MiSTerFPGA", "MLQuestions", 
    "Monero", "mpv", "mtgfinance", "MUD", "musichoarder", "neovim", "nes", "Newbalance", 
    "NhimArts", "NoFapChristians", "nosurf", "OfficeChairs", "Oobabooga", "openrouter", 
    "openshift", "options", "organization", "paloaltonetworks", "pcmods", "PCSleeving", 
    "PenmanshipPorn", "perl", "Permaculture", "Persona5", "pho", "Piracy", "PiratedGames", 
    "PKMS", "playnite", "PLTR", "pokemon", "PokemonROMhacks", "PokemonScarletViolet", 
    "PrimevalEvilShatters", "privacy", "ps3hacks", "ps3homebrew", "PSP", "railgun", 
    "ravenloft", "RealDebrid", "redhat", "RetroGamePorn", "ReverseEngineering", "RG35XX", 
    "RISCV", "RobinHood", "roguelikedev", "Roms", "SABnzbd", "Sauna", "SBCGaming", "SCCM", 
    "Scholar", "scihub", "SecurityCareerAdvice", "selfreliance", "Shadowrun", "SillyTavernAI", 
    "singularity", "smashbros", "socialskills", "sonarr", "SonoBisqueDoll", "Soulseek", 
    "speedrun", "SSBM", "staub", "StrategyRpg", "suckless", "sunisalee", "sysadmin", 
    "sysadminresumes", "TaylorSwift", "TaylorSwiftPictures", "thehatedone", "thelema", 
    "TheTrove", "tmux", "Toonami", "TopazLabs", "TriangleStrategy", "tryhackme", "unixporn", 
    "unRAID", "UsabilityPorn", "valheim", "vegan", "veganfitness", "veganrecipes", "vfx", 
    "vndevs", "VPN", "vsco", "VXJunkies", "wallpapers", "wallstreetbets", "wargroove", 
    "Warhammer40k", "webdev", "webhosting", "webmarketing", "WGUCyberSecurity", "WhatAWeeb", 
    "wholesomeanimemes", "wii", "WiiHacks", "WireGuard", "worldbuilding", "yoga", "youtubedl", 
    "yuzu", "zfs", "Zig", "zlibrary"
]

# Remove duplicates while preserving order
SUBREDDITS = list(dict.fromkeys(SUBREDDITS))


def main():
    """Run the crawler with production settings."""
    config = CrawlerConfig(
        subreddits=SUBREDDITS,
        request_delay_min=10.0,
        request_delay_max=30.0,
        subreddit_delay_min=60.0,
        subreddit_delay_max=180.0,
        cycle_delay_min=300.0,
        cycle_delay_max=600.0,
        step_delay_min=5.0,
        step_delay_max=15.0,
        max_pages=1,
        limit_per_page=100,
        max_cycles=None,  # Infinite
        dry_run=False,
        mock=False,
    )
    
    crawler = RedditCrawler(config)
    crawler.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCrawler stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
