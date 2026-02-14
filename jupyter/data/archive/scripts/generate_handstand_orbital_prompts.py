"""
Orbital 360° Handstand Progression Prompts for Shay Character

Generates bullet-time orbital pan prompts for handstand progression sequence.
First pass: Basic handstand progression
Second pass: With props (inversion table, ballet barre)
"""

from pathlib import Path
import json
from typing import List, Dict, Any


# Shay Identity Template
SHAY_ID = """A hyper-realistic portrait of Shay, a young Polish-American woman with a balanced oval face, soft defined jawline, and slightly rounded chin. She has fair skin (Fitzpatrick Type II) with warm peachy undertones and a dusting of light natural freckles concentrated on her nose and upper cheeks. Her eyes are almond-shaped and warm brown/hazel with a slight upward tilt at the outer corners. She has medium-thick, dark brown eyebrows with a gentle natural arch. Her nose has a straight bridge and slightly rounded tip. She has medium-full lips with a natural pink tone."""

# Cinematography Template for Orbital Pans
ORBITAL_TEMPLATE = """
[CINEMATOGRAPHY & MOVEMENT]
Camera Action: Slow-motion 360-degree orbital pan around the static subject.
Camera Path: The camera travels on a circular track around the frozen pose, maintaining consistent distance.
Sequence focus: Starting at side profile, smoothly rotating to ¾ rear view, then rear view, continuing the arc back to front.
Visual Style: Bullet-time effect, Matrix style camera movement, high frame rate, cinematic lighting.
Lens: 85mm (compression to flatten background during spin, maintains subject size consistency).

[LIGHTING CONSISTENCY]
Lighting: Three-point studio lighting fixed to the environment (not the camera). Key light from front-right, fill light from front-left, rim light from behind-left. Rim light highlights the contours as the camera rotates, creating consistent edge definition throughout the orbit.
"""


def generate_orbital_prompt(
    pose_name: str,
    pose_description: str,
    sanskrit_name: str = "",
    outfit: str = "High-waist black athletic leggings paired with black fitted athletic crop tank top, contemporary activewear silhouette."
) -> str:
    """Generate a complete orbital pan prompt for a handstand pose."""
    
    prompt = f"""[SCENE CONFIGURATION]
Subject Status: Static, frozen in pose.
Pose: {pose_name} ({sanskrit_name if sanskrit_name else pose_name}). {pose_description}. Subject remains completely frozen.
Outfit: {outfit}
Environment: Minimalist clean studio, infinite white/soft grey background.

{ORBITAL_TEMPLATE}
"""
    return prompt


def generate_first_pass_prompts() -> List[Dict[str, Any]]:
    """Generate first pass: Basic handstand progression."""
    
    poses = [
        {
            "name": "Wrist & Shoulder Warm-Up - Pike Hold",
            "sanskrit": "Preparation for Adho Mukha Vrksasana",
            "description": "Forearm plank or pike position on mat, shoulders stacked over wrists, core engaged, preparing for inversions"
        },
        {
            "name": "L-Shape Handstand (Wall-Assisted)",
            "sanskrit": "Adho Mukha Vrksasana preparation",
            "description": "Hands on floor, hips stacked over shoulders, legs straight up wall forming L-shape, building endurance and alignment"
        },
        {
            "name": "Wall-Facing Handstand",
            "sanskrit": "Adho Mukha Vrksasana against wall",
            "description": "Body straight, toes lightly touching wall for support, stomach facing wall for alignment practice"
        },
        {
            "name": "Freestanding Handstand Kick-Up Attempt",
            "sanskrit": "Adho Mukha Vrksasana entry",
            "description": "Dynamic moment kicking up into handstand mid-air, pointed toes, elegant ballet lines, progression to free balance"
        },
        {
            "name": "Full Freestanding Handstand",
            "sanskrit": "Adho Mukha Vrksasana",
            "description": "Straight vertical line from hands to pointed toes, core tight, shoulders open, graceful and powerful hold, perfect alignment"
        },
        {
            "name": "Tripod Headstand",
            "sanskrit": "Sirsasana variation",
            "description": "Tripod arm position with crown of head on mat, body straight vertical line from shoulders to toes, controlled and stable"
        },
        {
            "name": "Forearm Stand",
            "sanskrit": "Pincha Mayurasana",
            "description": "Forearms parallel on mat, body straight vertical line from shoulders to pointed toes, elegant balance, shoulders open"
        }
    ]
    
    prompts = []
    for i, pose in enumerate(poses, 1):
        full_prompt = generate_orbital_prompt(
            pose_name=pose["name"],
            sanskrit_name=pose["sanskrit"],
            pose_description=pose["description"]
        )
        
        prompts.append({
            "id": f"HANDSTAND_ORBITAL_{i:02d}",
            "name": pose["name"],
            "sanskrit": pose["sanskrit"],
            "pass": "first_pass",
            "prompt": f"{SHAY_ID}\n\n{full_prompt}",
            "metadata": {
                "camera_movement": "360-degree orbital pan",
                "cinematography": "bullet-time effect",
                "pose": pose["name"]
            }
        })
    
    return prompts


def generate_second_pass_prompts() -> List[Dict[str, Any]]:
    """Generate second pass: Handstand progression with props (inversion table, ballet barre)."""
    
    # Props variations
    props = [
        {
            "name": "Inversion Table",
            "description": "Athletic female gymnast using yoga inversion bench/table for assisted handstand prep, body inverted at controlled angle, safe training tool"
        },
        {
            "name": "Ballet Barre Handstand",
            "description": "Ballet-trained gymnast practicing handstand position with one hand or foot lightly touching ballet barre for balance support, pointed toes, elegant lines"
        },
        {
            "name": "Inversion Table Progression",
            "description": "Gymnast on inversion table transitioning from assisted inversion toward unassisted handstand form, building core and shoulder strength"
        },
        {
            "name": "Ballet Barre Balance Practice",
            "description": "Handstand variation using ballet barre for stabilization while building freestanding balance, graceful extension, ballet aesthetics"
        }
    ]
    
    prompts = []
    for i, prop in enumerate(props, 1):
        # Use inversion poses adapted for props
        prop_prompt = generate_orbital_prompt(
            pose_name=prop["name"],
            sanskrit_name="Adho Mukha Vrksasana variation",
            pose_description=prop["description"],
            outfit="High-waist black performance leggings paired with black fitted athletic crop top, ballet-inspired athletic wear"
        )
        
        prompts.append({
            "id": f"HANDSTAND_PROP_{i:02d}",
            "name": prop["name"],
            "sanskrit": "Adho Mukha Vrksasana with props",
            "pass": "second_pass",
            "prop_type": "inversion_table" if "Inversion" in prop["name"] else "ballet_barre",
            "prompt": f"{SHAY_ID}\n\n{prop_prompt}",
            "metadata": {
                "camera_movement": "360-degree orbital pan",
                "cinematography": "bullet-time effect",
                "prop": prop["name"],
                "pose": "handstand with prop support"
            }
        })
    
    return prompts


def export_prompts(prompts: List[Dict[str, Any]], output_file: str):
    """Export prompts to formatted text file."""
    output_path = Path(__file__).parent / "data" / "Prompts" / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SHAY HANDSTAND ORBITAL 360° PROMPTS\n")
        f.write("Cinematography: Bullet-time orbital pans for handstand progression\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Prompts: {len(prompts)}\n")
        f.write("Target Model: nanobanana-3 (Gemini 3 Image Pro)\n")
        f.write("Camera: 360° orbital pan with bullet-time effect\n")
        f.write("=" * 80 + "\n\n")
        
        for prompt_data in prompts:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"PROMPT: {prompt_data['id']}\n")
            f.write(f"Name: {prompt_data['name']}\n")
            f.write(f"Pass: {prompt_data['pass']}\n")
            if 'prop_type' in prompt_data:
                f.write(f"Prop: {prompt_data['prop_type']}\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(prompt_data['prompt'])
            f.write("\n\n")
            f.write("-" * 80 + "\n")
            f.write("METADATA:\n")
            for key, value in prompt_data['metadata'].items():
                f.write(f"  {key}: {value}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"Exported {len(prompts)} prompts to {output_path}")
    return output_path


def export_json(prompts: List[Dict[str, Any]], output_file: str):
    """Export prompts to JSON format."""
    output_path = Path(__file__).parent / "data" / "Prompts" / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'model': 'nanobanana-3',
            'total_prompts': len(prompts),
            'camera_movement': '360-degree orbital pan',
            'cinematography': 'bullet-time effect',
            'prompts': prompts
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(prompts)} prompts to {output_path}")
    return output_path


if __name__ == "__main__":
    # Generate first pass (basic handstand progression)
    print("Generating first pass: Basic handstand progression...")
    first_pass = generate_first_pass_prompts()
    
    # Generate second pass (with props)
    print("Generating second pass: Handstand with props (inversion table, ballet barre)...")
    second_pass = generate_second_pass_prompts()
    
    # Combine all prompts
    all_prompts = first_pass + second_pass
    
    # Export
    print("\nExporting prompts...")
    export_prompts(all_prompts, "shay_handstand_orbital_360_prompts.txt")
    export_json(all_prompts, "shay_handstand_orbital_360_prompts.json")
    
    print(f"\nGenerated {len(all_prompts)} orbital 360° handstand prompts")
    print(f"  First pass: {len(first_pass)} basic progression prompts")
    print(f"  Second pass: {len(second_pass)} prop-assisted prompts")
    print("\nUse with nanobanana-3 for bullet-time 360° orbital video generation")
