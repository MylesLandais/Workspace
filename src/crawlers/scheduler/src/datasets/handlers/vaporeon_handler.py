"""
Dataset handler for the Vaporeon ASR evaluation dataset.
"""
import subprocess
import json
from pathlib import Path
from src.datasets.base_handler import BaseDatasetHandler

class VaporeonHandler(BaseDatasetHandler):
    """
    Manages the Vaporeon copypasta dataset.
    This handler will download the audio from YouTube if it's not found locally.
    """

    @property
    def name(self) -> str:
        return "vaporeon"

    def info(self) -> dict:
        return {
            "name": "Vaporeon Copypasta",
            "description": "Vaporeon copypasta meme for ASR evaluation.",
            "source_url": "https://www.youtube.com/watch?v=-EWMgB26bmU",
            "content_type": "meme/copypasta",
            "language": "en",
        }

    def get(self, destination: Path = Path("evaluation_datasets")) -> Path:
        """
        Ensures the Vaporeon dataset (audio and transcript) is available.
        Downloads and extracts the audio if it doesn't exist.

        Args:
            destination (Path): The root directory for evaluation datasets.

        Returns:
            Path: The path to the downloaded audio file.
        """
        dataset_dir = destination / self.name
        self._ensure_dir(dataset_dir)

        audio_file = dataset_dir / "-EWMgB26bmU_Vaporeon copypasta (animated).mp3"
        transcript_file = dataset_dir / "reference_transcript.txt"
        metadata_file = dataset_dir / "metadata.json"

        if audio_file.exists() and transcript_file.exists():
            print(f"✓ '{self.name}' dataset already exists at {dataset_dir}")
            return audio_file

        print(f"'{self.name}' dataset not found. Downloading...")

        try:
            self._download_audio(dataset_dir)
            self._create_reference_files(dataset_dir, audio_file)
            print(f"✅ Successfully downloaded and set up '{self.name}' dataset.")
            return audio_file
        except Exception as e:
            print(f"❌ Failed to download and set up '{self.name}' dataset: {e}")
            raise

    def _download_audio(self, dataset_dir: Path):
        """Downloads the audio using yt-dlp."""
        youtube_url = self.info()["source_url"]
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", str(dataset_dir / "%(id)s_%(title)s.%(ext)s"),
            youtube_url
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    def _create_reference_files(self, dataset_dir: Path, audio_file: Path):
        """Creates the reference transcript and metadata file."""
        reference_text = """Hey guys, did you know that in terms of male human and female Pokémon breeding, Vaporeon is the most compatible Pokémon for humans? Not only are they in the field egg group, which is mostly comprised of mammals, Vaporeon are an average of 3"03' tall and 63.9 pounds, this means they're large enough to be able handle human dicks, and with their impressive Base Stats for HP and access to Acid Armor, you can be rough with one. Due to their mostly water based biology, there's no doubt in my mind that an aroused Vaporeon would be incredibly wet, so wet that you could easily have sex with one for hours without getting sore. They can also learn the moves Attract, Baby-Doll Eyes, Captivate, Charm, and Tail Whip, along with not having fur to hide nipples, so it'd be incredibly easy for one to get you in the mood. With their abilities Water Absorb and Hydration, they can easily recover from fatigue with enough water. No other Pokémon comes close to this level of compatibility. Also, fun fact, if you pull out enough, you can make your Vaporeon turn white. Vaporeon is literally built for human dick. Ungodly defense stat+high HP pool+Acid Armor means it can take cock all day, all shapes and sizes and still come for more"""

        transcript_file = dataset_dir / "reference_transcript.txt"
        with open(transcript_file, 'w') as f:
            f.write(reference_text)

        metadata = {
            **self.info(),
            "audio_file": audio_file.name,
            "reference_file": transcript_file.name,
            "duration_seconds": 164,
        }

        metadata_file = dataset_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
