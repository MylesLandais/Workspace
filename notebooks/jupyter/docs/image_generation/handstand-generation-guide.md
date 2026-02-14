# Handstand Orbital 360° Image Generation

Generate bullet-time orbital pan images for handstand progression using Nano Banana AIO workflow with Gemini 3 Pro.

## Quick Start

### Running in Docker Container

```bash
# Make script executable (optional)
chmod +x run_handstand_orbital_generations.py

# Run all 11 handstand orbital prompts
docker compose exec jupyterlab python run_handstand_orbital_generations.py

# Run only first pass (basic handstand progression - 7 prompts)
docker compose exec jupyterlab python run_handstand_orbital_generations.py \
  --prompt-ids HANDSTAND_ORBITAL_01,HANDSTAND_ORBITAL_02,HANDSTAND_ORBITAL_03,HANDSTAND_ORBITAL_04,HANDSTAND_ORBITAL_05,HANDSTAND_ORBITAL_06,HANDSTAND_ORBITAL_07

# Run only second pass (with props - 4 prompts)
docker compose exec jupyterlab python run_handstand_orbital_generations.py \
  --prompt-ids HANDSTAND_PROP_01,HANDSTAND_PROP_02,HANDSTAND_PROP_03,HANDSTAND_PROP_04

# Test single prompt
docker compose exec jupyterlab python run_handstand_orbital_generations.py \
  --prompt-ids HANDSTAND_ORBITAL_05
```

### Running Locally (Python 3.10+)

```bash
# Install dependencies
pip install requests python-dotenv

# Run all prompts
python run_handstand_orbital_generations.py

# Run specific prompts
python run_handstand_orbital_generations.py \
  --prompt-ids HANDSTAND_ORBITAL_01,HANDSTAND_ORBITAL_02
```

## Configuration

### Required Environment Variables

Create or update `.env` file in project root:

```env
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_runpod_endpoint_id_here
```

### Workflow Configuration

- **Workflow**: `data/Comfy_Workflow/api_google_gemini_image.json`
- **Model**: `gemini-3-pro-image-preview` (Nano Banana AIO)
- **Default Settings**:
  - Image Count: 8 variations per prompt
  - Aspect Ratio: 1:1 (square for orbital pans)
  - Image Size: 2K
  - Temperature: 1.0
  - Use Search: False (uses reference identity images)

## Generated Content

### First Pass (7 Prompts)

Basic handstand progression with bullet-time orbital cinematography:

1. **HANDSTAND_ORBITAL_01**: Wrist & shoulder warm-up - Pike hold
2. **HANDSTAND_ORBITAL_02**: L-shape handstand (wall-assisted)
3. **HANDSTAND_ORBITAL_03**: Wall-facing handstand
4. **HANDSTAND_ORBITAL_04**: Freestanding handstand kick-up attempt
5. **HANDSTAND_ORBITAL_05**: Full freestanding handstand
6. **HANDSTAND_ORBITAL_06**: Tripod headstand
7. **HANDSTAND_ORBITAL_07**: Forearm stand (Pincha Mayurasana)

### Second Pass (4 Prompts)

Handstand progression with training props:

1. **HANDSTAND_PROP_01**: Inversion table (assisted prep)
2. **HANDSTAND_PROP_02**: Ballet barre handstand (balance support)
3. **HANDSTAND_PROP_03**: Inversion table progression
4. **HANDSTAND_PROP_04**: Ballet barre balance practice

## Output Structure

```
outputs/
└── handstand_orbital_360/
    ├── HANDSTAND_ORBITAL_01/
    │   ├── Wrist_Shoulder_Warm_Up_Pike_Hold_01.png
    │   ├── Wrist_Shoulder_Warm_Up_Pike_Hold_02.png
    │   └── ... (8 variations)
    ├── HANDSTAND_ORBITAL_02/
    │   └── ... (8 variations)
    └── results_20251228_143025.json  # Generation metadata
```

Each prompt generates **8 image variations** (total: 88 images for all 11 prompts)

## Command Line Options

```bash
usage: run_handstand_orbital_generations.py [-h] [--prompt-ids PROMPT_IDS]
                                            [--delay DELAY] [--dry-run]

Generate Handstand Orbital 360° images using Nano Banana AIO

optional arguments:
  -h, --help            show this help message and exit
  --prompt-ids PROMPT_IDS
                        Comma-separated list of prompt IDs to run
                        (e.g., HANDSTAND_ORBITAL_01,HANDSTAND_ORBITAL_02)
  --delay DELAY          Delay between job submissions in seconds (default: 5)
  --dry-run             Load and display prompts without submitting jobs
```

## Monitoring Progress

The script outputs real-time progress:
- `[INIT]` - Initialization
- `[LOAD]` - Loading prompts/workflow
- `[SUBMIT]` - Job submission to RunPod
- `[POLL]` - Waiting for completion
- `[OK]` - Success messages
- `[SAVE]` - Image saving
- `[ERROR]` - Error messages
- `[BATCH COMPLETE]` - Final summary

## Troubleshooting

### Job Timeouts
Default timeout is 600 seconds (10 minutes). Increase with `--delay` if hitting rate limits:
```bash
docker compose exec jupyterlab python run_handstand_orbital_generations.py --delay 10
```

### Failed Jobs
Check `results_*.json` in output directory for detailed error information.

### Docker Container Issues
```bash
# Check container status
docker compose ps jupyterlab

# View logs
docker compose logs jupyterlab -f

# Restart container
docker compose restart jupyterlab
```

## Cinematography Details

Each prompt includes bullet-time orbital cinematography:
- **Camera Action**: Slow-motion 360-degree orbital pan around static subject
- **Camera Path**: Circular track maintaining consistent distance
- **Visual Style**: Matrix style bullet-time effect, high frame rate
- **Lens**: 85mm for compression consistency
- **Lighting**: Three-point studio lighting fixed to environment (not camera)

This ensures consistent pose framing across all orbital angles.
