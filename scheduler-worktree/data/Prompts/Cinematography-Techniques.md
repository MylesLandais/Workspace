# Cinematography Techniques for Nano Banana AIO
## Camera Movement & Orbital Pan Strategies

Universal template for creating dynamic camera movements, 360-degree orbital pans, and cinematic sequences using ComfyUI Nano Banana AIO node.

---

## Overview

To achieve dramatic, consistent 360-degree slow-motion pans around a subject using Nano Banana AIO (which utilizes Gemini to drive generation), you need to shift the prompt strategy from a **static description** to a **cinematic directive**.

The key is to instruct the model to keep the subject frozen while moving the "virtual camera."

---

## Workflow Strategies

### Workflow A: Direct Video Generation (Recommended)

If NanoBanana creates video directly (or feeds a video model), you prompt for the *camera movement* in a single generation.

**Best for:**
- Native video output models
- Seamless orbital motion
- Real-time camera movement

### Workflow B: Keyframe Stitching

Generate 4-8 static images representing specific angles (0°, 45°, 90°, etc.) and feed them into an interpolator (like RIFE or a Video Morph tool).

**Best for:**
- Image-only generation
- Maximum control over keyframe placement
- Post-processing workflows

**Recommendation:** Given standard ComfyUI setup, **Workflow A** (Prompting for motion) is usually the goal.

---

## Prompt Structure for Orbital Pan

### Core Template

```
[CHARACTER_ID] = "Your full character description here..."

[CHARACTER PREFIX SET TO CHARACTER_ID]

[SCENE CONFIGURATION]
Subject Status: Static, frozen in pose.
Pose: [Detailed pose description with specific positioning].
Outfit: [Clothing description].
Environment: Minimalist clean studio, infinite white/soft grey background.

[CINEMATOGRAPHY & MOVEMENT]
Camera Action: Slow-motion 360-degree orbital pan.
Camera Path: The camera travels on a circular track around the static subject.
Sequence focus: Starting at side profile, smoothly rotating to ¾ rear view, then rear view, continuing the arc.
Visual Style: Bullet-time effect, Matrix style camera movement, high frame rate, cinematic lighting.
Lens: 85mm (compression to flatten background during spin).

[LIGHTING CONSISTENCY]
Lighting: Three-point studio lighting fixed to the environment (not the camera). Rim light highlights the contours as the camera rotates.
```

### Key Prompt Components Explained

1. **"Subject Status: Static"** - Explicitly tells the model that the *subject* does not move; only the *camera* moves. Without this, the AI often tries to make the subject spin.

2. **"Orbital Pan" / "Circular Track"** - Strong trigger words for video models to understand the geometry of the shot.

3. **"Bullet-time"** - This is a "cheat code" keyword. It specifically refers to the *Matrix* effect where time slows down/stops, and the camera moves 360 degrees. This helps lock pose consistency.

4. **Lighting Fixed to Environment** - Critical! If you don't specify this, the light source often rotates with the camera, making the video look unnatural. Use "three-point studio lighting fixed to the environment (not the camera)" to maintain realistic lighting.

---

## Batch Prompt Schedule (For Keyframe Stitching)

If generating **Multiple Static Frames** to stitch later (using `image_count: 4`), use a **Batch Prompt Schedule** with angle-specific variations:

### Image 1 (0° / Right Side Profile)
```
[CHARACTER_ID and SCENE CONFIGURATION as above]

Camera Angle: Right Side Profile, showing the full curve of the pose, subject frozen in position.
```

### Image 2 (90° / Direct Rear View)
```
[CHARACTER_ID and SCENE CONFIGURATION as above]

Camera Angle: Direct Rear View, focusing on the symmetry of the pose and body alignment.
```

### Image 3 (180° / Left Side Profile)
```
[CHARACTER_ID and SCENE CONFIGURATION as above]

Camera Angle: Left Side Profile, mirroring the initial pose from opposite side.
```

### Image 4 (270° / Front View)
```
[CHARACTER_ID and SCENE CONFIGURATION as above]

Camera Angle: Front View, showing the pose from the front, subject frozen.
```

**Note:** If NanoBanana accepts a list for the prompt input, use the batch schedule. If not, you must queue the workflow multiple times with these variations.

---

## Example: Shay in Upward-Facing Dog (Orbital Pan)

```
[SHAY_ID] = "A hyper-realistic portrait of Shay, a young Polish-American woman with a balanced oval face, soft defined jawline, and slightly rounded chin. She has fair skin (Fitzpatrick Type II) with warm peachy undertones and a dusting of light natural freckles concentrated on her nose and upper cheeks. Her eyes are almond-shaped and warm brown/hazel with a slight upward tilt at the outer corners. She has medium-thick, dark brown eyebrows with a gentle natural arch. Her nose has a straight bridge and slightly rounded tip. She has medium-full lips with a natural pink tone. Her long, fine-to-medium thickness dark brown hair (hex #3B2820) with natural shine is styled in a sleek high ponytail secured at the crown."

[SCENE CONFIGURATION]
Subject Status: Static, frozen in pose.
Pose: Upward-Facing Dog (Urdhva Mukha Svanasana). Deep backbend, chest lifted high, arms straight pressing into mat, tops of feet grounded, thighs lifted off floor, shoulders down away from ears. Subject remains completely frozen.
Outfit: High-waist black yoga leggings paired with black fitted athletic tank top, contemporary activewear aesthetic.
Environment: Minimalist clean studio, infinite white/soft grey background.

[CINEMATOGRAPHY & MOVEMENT]
Camera Action: Slow-motion 360-degree orbital pan around the static subject.
Camera Path: The camera travels on a circular track around the frozen pose, maintaining consistent distance.
Sequence focus: Starting at side profile, smoothly rotating to ¾ rear view, then rear view, continuing the arc back to front.
Visual Style: Bullet-time effect, Matrix style camera movement, high frame rate, cinematic lighting.
Lens: 85mm (compression to flatten background during spin, maintains subject size consistency).

[LIGHTING CONSISTENCY]
Lighting: Three-point studio lighting fixed to the environment (not the camera). Key light from front-right, fill light from front-left, rim light from behind-left. Rim light highlights the contours of the backbend as the camera rotates, creating consistent edge definition throughout the orbit.
```

---

## Advanced Consistency Tips

### Input Image Strategy (ControlNet/Reference)

If you find that the character's face morphs too much as the camera turns, you need to rely heavily on your input images.

When loading reference images (`image_1` through `image_6`), ensure these images cover different angles:

- **Input Image 1:** Front face (primary identity reference)
- **Input Image 2:** Side profile (90-degree angle reference)
- **Input Image 3:** Three-quarter view (45-degree angle reference)
- **Input Image 4:** Body structure reference (full body pose)
- **Input Image 5:** Alternative angle (30-degree or 60-degree)
- **Input Image 6:** Rear/back view (if available)

**Critical:** If the model is over-relying on a front-facing reference image while you try to generate a side profile, the AI will try to "smash" the front face onto the side profile. **Ensure your input images include at least one side profile of the subject.**

### Consistency Lock Techniques

1. **Character ID Reinforcement**: Repeat the character ID block in every angle variation to maintain facial consistency.

2. **Pose Freeze Directive**: Always include "Subject Status: Static, frozen in pose" to prevent unwanted movement.

3. **Fixed Lighting**: Always specify that lighting is fixed to the environment, not the camera.

4. **Consistent Distance**: Use "maintaining consistent distance" in the camera path description to prevent zoom changes.

5. **Lens Specification**: Use a consistent lens specification (85mm recommended) to maintain compression and perspective.

---

## Common Issues & Solutions

### Issue: Subject Rotates Instead of Camera

**Solution:** Add explicit "Subject Status: Static, frozen in pose" at the beginning of the scene configuration. Remove any words that suggest subject movement (like "turning" or "rotating" applied to the character).

### Issue: Lighting Rotates with Camera

**Solution:** Always include "Three-point studio lighting fixed to the environment (not the camera)" in the lighting section. Specify that lights remain stationary while only the camera moves.

### Issue: Face Morphs Between Angles

**Solution:** 
1. Ensure reference images include multiple angles (especially side profile)
2. Reinforce character ID in every angle variation
3. Use consistent facial feature descriptions across all angles
4. Consider using ControlNet or similar tools if available

### Issue: Background Inconsistency

**Solution:** Use "infinite white/soft grey background" or "seamless studio background" to create a featureless backdrop that appears consistent from all angles.

### Issue: Pose Shifts Between Frames

**Solution:** 
1. Provide extremely detailed pose description
2. Include "frozen in pose" or "completely static" language
3. Use bullet-time or Matrix-style keywords to emphasize temporal freeze
4. Consider using pose reference images if possible

---

## Nano Banana AIO Node Configuration

### Recommended Settings

```
model_name: gemini-3-pro-image-preview
image_count: 8 (for keyframe stitching) or 1 (for direct video)
use_search: false
aspect_ratio: 1:1 (square works best for orbital pans)
image_size: 1K or 2K (depending on quality needs)
temperature: 1.0 (allows for natural variation)
```

### Input Image Strategy

- Connect 6 reference images covering multiple angles
- Prioritize: front face, side profile, three-quarter view, body structure
- Ensure images show the character clearly for identity matching
- Include various poses/angles to help the model understand 3D structure

---

## Additional Camera Movement Techniques

### Dolly In/Out (Zoom Movement)

```
Camera Action: Slow dolly forward toward the subject, maintaining focus on the face.
Camera Path: Linear movement along the z-axis, starting from medium shot and ending at close-up.
Lens: 85mm, maintaining consistent compression throughout the movement.
```

### Tracking Shot (Horizontal Movement)

```
Camera Action: Slow tracking shot moving horizontally parallel to the subject.
Camera Path: Linear horizontal movement, maintaining consistent distance and height.
Visual Style: Smooth cinematic camera glide, Steadicam quality.
```

### Arc Movement (Partial Orbit)

```
Camera Action: Slow arc movement around the subject (180-degree arc).
Camera Path: Camera travels on a curved path from side to side, maintaining consistent distance.
Sequence focus: Starting at left side profile, smoothly arcing to right side profile.
```

### Push-Pull Effect (Vertigo Shot)

```
Camera Action: Vertigo/dolly-zoom effect, combining forward dolly with reverse zoom.
Camera Path: Camera moves forward while lens zooms out, creating compression effect.
Visual Style: Dramatic perspective distortion, maintaining subject size while background changes.
```

---

## Integration with Prompt Book System

This cinematography guide works with:

- **Character Bibles**: Use character IDs from Subject-Shay.md, Subject-Lexie.md, etc.
- **Wildcard System**: Combine with poses from wildcards/yoga_poses.md, wildcards/poses.md
- **Universal Assets**: Use lighting and environment templates from Universal-Assets.md

Example integration:
1. Pull character ID from character bible
2. Pull pose from yoga_poses.md or poses.md
3. Add cinematography block from this guide
4. Combine with lighting/background from Universal-Assets.md

---

## Best Practices Summary

1. ✅ Always specify "Subject Status: Static" to prevent unwanted movement
2. ✅ Use "orbital pan" or "circular track" for 360-degree movements
3. ✅ Include "bullet-time" or "Matrix style" for temporal freeze effects
4. ✅ Specify lighting is "fixed to environment, not camera"
5. ✅ Use consistent lens specification (85mm recommended)
6. ✅ Provide multi-angle reference images (especially side profile)
7. ✅ Reinforce character ID in every angle variation
8. ✅ Use infinite/seamless backgrounds for consistency
9. ✅ Include "frozen in pose" language to maintain pose consistency
10. ✅ Test with keyframe stitching first, then move to direct video if available

---

## Quick Reference Template

```
[CHARACTER_ID] = "[Your character description]"

[SCENE CONFIGURATION]
Subject Status: Static, frozen in pose.
Pose: [Your pose description].
Outfit: [Your outfit description].
Environment: Minimalist clean studio, infinite white/soft grey background.

[CINEMATOGRAPHY & MOVEMENT]
Camera Action: [Your camera movement type].
Camera Path: [Specific path description].
Visual Style: [Style keywords].
Lens: [Lens specification].

[LIGHTING CONSISTENCY]
Lighting: Three-point studio lighting fixed to the environment (not the camera). [Additional lighting details].
```

Copy this template and fill in the bracketed sections for your specific needs!




