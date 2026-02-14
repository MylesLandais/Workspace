# Production-Grade Prompt Template

## Universal Negative Prompt

```
Do not:
- Change facial identity, age, ethnicity, or body shape
- Stylize the face or body (no anime, CGI, illustration, or painterly looks)
- Add beauty filters, smoothing, or plastic skin
- Add props not listed in the prompt
- Crop the body or cut off limbs
- Introduce shadows, dramatic lighting, rim light, or colored gels
- Use cinematic grading, HDR, glow, or vignette
- Add logos, watermarks, text overlays, or borders
- Sexualize pose or exaggerate anatomy

No fantasy, cosplay exaggeration, or AI-art artifacts.
```

## Complete Prompt Template

### Section 1: Subject / Identity Lock

```
Use the woman from the provided reference images as the subject. Her identity must match
the reference exactly: same face, bone structure, proportions, skin tone, body shape, and
natural features. Do not alter facial geometry, eye spacing, nose shape, jawline, lips, or
body proportions. This is a 1:1 identity match to the reference photos.

She is a woman in her mid-20s with long dark brown hair, warm brown-hazel eyes, fair skin
with visible natural texture, and defined facial features. No beautification beyond realistic
studio photography.
```

### Section 2: Wardrobe

```
She is wearing the [COSTUME_NAME]:

- [Garment piece 1 with specific details: material, cut, closures, features]
- [Garment piece 2 with specific details]
- [Accessories with specific details]

Footwear: [FOOTWEAR_SELECTION]. Heels are visible in full-body framing,
proportionally accurate, and styled as luxury fashion elements rather than costume
exaggeration.

Costume should appear accurate to retail catalog photography, properly fitted, showing
natural body shape with realistic fabric tension and seams.
```

### Section 3: Pose & Framing

```
[Shot type: Full-body/Headshot/3/4 body] studio casting photo.
[Pose description: standing straight, facing camera, seated, etc.]
[Limb position: arms, hands, legs placement]
[Attitude: confident, neutral, relaxed]
Eye-level camera angle.
Full frame, edge-to-edge, no borders or cropping.

Prop Interaction: She may be interacting with a single prop selected from accessories
wildcard (police baton or metal handcuffs). Props are held casually and
confidently, never obstructing face or body silhouette. No restraint, no implied
action — purely visual styling consistent with fashion editorial photography.
```

### Section 4: Photography Style

```
High-end fashion catalog photography.
Realistic skin texture, visible pores, natural complexion.
Raw, authentic photo style — not airbrushed, not stylized.
True-to-life proportions and anatomy.
```

### Section 5: Technical Capture

```
Simulated high-definition digital capture using a Phase One medium-format camera.
50–70mm lens equivalent.
Crystal-clear sharpness, no motion blur, no noise.
Ultra-high resolution, 8K quality.
```

### Section 7: Tone Control (Optional)

```
Tone: confident, stylish, editorial, fashion-forward, non-provocative
```

OR

```
Tone: assertive, powerful, flirtatious but controlled, high-fashion authority
```

Use ONE tone selection per prompt. Do not combine.

---

## Example: VIP/Tease Tone Applied

When using the **flirtatious but controlled** tone with `seated_stool_kissing_baton` pose:

**Photography Style:** High-end fashion editorial with intimate, teasing aesthetic
**Background:** Clean white seamless with white stool (creates contrast with navy catsuit)
**Tone:** assertive, powerful, flirtatious but controlled, high-fashion authority, VIP tease content

**Content Classification:** VIP/Tease (exclusive creator platforms only, not public brand Instagram)

See [Quick Prompt: Kissing Baton](QUICK_PROMPT_KISSING_BATON.md) for complete ready-to-use prompt.

---

## Example: VIP/Tease Tone Applied

When using the **flirtatious but controlled** tone with the seated_stool_kissing_baton pose:

**Photography Style:** High-end fashion editorial with intimate, teasing aesthetic
**Background:** Clean white seamless with white stool (creates contrast with navy catsuit)
**Tone:** assertive, powerful, flirtatious but controlled, high-fashion authority, VIP tease content

**Content Classification:** VIP/Tease (exclusive creator platforms only, not public brand Instagram)

See [Quick Prompt: Kissing Baton](QUICK_PROMPT_KISSING_BATON.md) for complete ready-to-use prompt.

---

### Section 6: Lighting & Background

```
Flat, even studio lighting.
Soft, diffused light with no harsh shadows or dramatic contrast.
Clean white seamless studio background.
Neutral color balance.
```

## Wildcard Integration

Replace `[COSTUME_NAME]` with wildcard from `wildcards/outfits.md`:
```
[outfits: stop_traffic]
```

Replace pose and framing elements with wildcards:
```
[poses: hands_on_hips_confident]
[framing: full_body_eye_level]
```

## Example: Complete Prompt with Stop Traffic Costume

```
Use the woman from the provided reference images as the subject. Her identity must match
the reference exactly: same face, bone structure, proportions, skin tone, body shape, and
natural features. Do not alter facial geometry, eye spacing, nose shape, jawline, lips, or
body proportions. This is a 1:1 identity match to the reference photos.

She is a woman in her mid-20s with long dark brown hair, warm brown-hazel eyes, fair skin
with visible natural texture, and defined facial features. No beautification beyond realistic
studio photography.

She is wearing the **Amscan "Stop Traffic" Police Cop Officer Sexy Catsuit Halloween Costume**:

* Navy blue catsuit with crisp structured collar, cuffed sleeves, center-front zipper with
  silver badge pull tab, black side stripes along pant legs
* "Stop Traffic" name plate on chest
* Police cap with silver badge
* Faux leather gloves
* Functional belt with adjustable leg-strap holster

Footwear: Classic black Louboutin stiletto high heels with signature red sole.
Heels are visible in full-body framing, proportionally accurate, and styled as luxury
fashion elements rather than costume exaggeration.

Costume should appear accurate to retail catalog photography, properly fitted, showing
natural body shape with realistic fabric tension and seams.

Full-body studio casting photo.
Standing straight, facing the camera.
Both hands placed naturally on hips, elbows slightly outward.
Confident, neutral stance.

Prop Interaction: She may be holding a police baton naturally in one hand, arm relaxed
at side. Baton is held casually and confidently, never obstructing face or body silhouette.
No restraint, no implied action — purely visual styling consistent with fashion editorial
photography.

Eye-level camera angle.
Full frame, edge-to-edge, no borders or cropping.

High-end fashion catalog photography.
Realistic skin texture, visible pores, natural complexion.
Raw, authentic photo style — not airbrushed, not stylized.
True-to-life proportions and anatomy.

Simulated high-definition digital capture using a Phase One medium-format camera.
50–70mm lens equivalent.
Crystal-clear sharpness, no motion blur, no noise.
Ultra-high resolution, 8K quality.

Flat, even studio lighting.
Soft, diffused light with no harsh shadows or dramatic contrast.
Clean white seamless studio background.
Neutral color balance.

Tone: confident, stylish, editorial, fashion-forward, non-provocative
```
Use the woman from the provided reference images as the subject. Her identity must match
the reference exactly: same face, bone structure, proportions, skin tone, body shape, and
natural features. Do not alter facial geometry, eye spacing, nose shape, jawline, lips, or
body proportions. This is a 1:1 identity match to the reference photos.

She is a woman in her mid-20s with long dark brown hair, warm brown-hazel eyes, fair skin
with visible natural texture, and defined facial features. No beautification beyond realistic
studio photography.

She is wearing the Amscan "Stop Traffic" Police Cop Officer Sexy Catsuit Halloween Costume:
- Navy blue catsuit with crisp structured collar, cuffed sleeves, center-front zipper with
  silver badge pull tab, black side stripes along pant legs
- "Stop Traffic" name plate on chest
- Police cap with silver badge decoration
- Faux leather gloves
- Functional belt with adjustable leg-strap holster

Costume should appear accurate to retail catalog photography, properly fitted, showing
natural body shape with realistic fabric tension and seams.

Full-body studio casting photo.
Standing straight, facing the camera.
Both hands placed naturally on hips, elbows slightly outward.
Confident, neutral stance.
Eye-level camera angle.
Full frame, edge-to-edge, no borders or cropping.

High-end fashion catalog photography.
Realistic skin texture, visible pores, natural complexion.
Raw, authentic photo style — not airbrushed, not stylized.
True-to-life proportions and anatomy.

Simulated high-definition digital capture using a Phase One medium-format camera.
50–70mm lens equivalent.
Crystal-clear sharpness, no motion blur, no noise.
Ultra-high resolution, 8K quality.

Flat, even studio lighting.
Soft, diffused light with no harsh shadows or dramatic contrast.
Clean white seamless studio background.
Neutral color balance.
```

## Batch Generation Pattern

For automated prompt generation, use this pattern with wildcard substitutions:

```
[IDENTITY_LOCK_TEMPLATE]

[WILDCARD_OUTFIT_DETAIL]

[WILDCARD_POSE_FRAMING]

[PHOTOGRAPHY_STYLE_TEMPLATE]

[TECHNICAL_CAPTURE_TEMPLATE]

[LIGHTING_BACKGROUND_TEMPLATE]

[UNIVERSAL_NEGATIVE_PROMPT]
```

## Control Notes (If Model Supports)

- Identity priority: maximum
- Photorealism: maximum
- Style adherence: fashion catalog / commercial retail
- Variation: low
- Pose variance: none
