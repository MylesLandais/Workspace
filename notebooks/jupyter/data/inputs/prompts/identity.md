# Shay Identity & Face Lock

## Core Identity Anchor Tokens

### Primary Face Lock Module

```
Use the woman from the provided reference images as the subject. Her identity must match the reference exactly: same face, bone structure, proportions, skin tone, body shape, and natural features. Do not alter facial geometry, eye spacing, nose shape, jawline, lips, or body proportions. This is a 1:1 identity match to the reference photos.

Young adult woman, Polish-American heritage, fair complexion with warm undertones, natural freckles scattered across nose bridge and cheeks, oval face shape with defined jawline, center-parted long straight dark brown hair (chest-length), warm brown eyes, natural full eyebrows (medium thickness, slight arch), genuine warm smile showing teeth, friendly approachable expression
```

### Detailed Facial Feature Tokens (High-Priority KV Cache)

```
FACE_STRUCTURE: oval face, balanced proportions, defined but soft jawline, slightly rounded chin

SKIN: fair skin tone (Fitzpatrick Type II), warm peachy undertones, light freckles concentrated on nose and upper cheeks, smooth texture, natural finish

EYES: medium-sized eyes, warm brown/hazel color, almond shape, slight upward cant at outer corners, natural eyelashes

EYEBROWS: medium thickness, dark brown, natural shape with gentle arch, well-defined without being heavy

NOSE: straight bridge, medium width, slightly rounded tip, proportionate to face

MOUTH: medium-full lips, natural pink tone, upper lip slightly thinner than lower, wide genuine smile showing upper teeth

HAIR_COLOR: dark brown (#3B2820 hex approximate), natural shine, no highlights

HAIR_TEXTURE: straight with slight natural wave/body, fine to medium strand thickness

HAIR_LENGTH: long, extending to mid-chest/breast line

HAIR_PART: clean center part
```

## Condensed Trigger Prompt (for consistent generation)

### Version A: Technical Tokens

```
fair-skinned woman, Polish-American features, natural freckles on nose and cheeks, oval face, warm brown eyes, dark brown straight hair center-parted to chest-length, genuine smile, medium eyebrows, balanced facial proportions, warm undertones, approachable expression
```

### Version B: Biometric-Style Lock

```
SUBJECT_ID: Female, age 25-30 range appearance

ETHNICITY: Polish-American, European heritage

SKIN: Fair (warm undertone), freckled

HAIR: Dark brown, straight, long (60cm), center part

EYES: Warm brown, almond-shaped

FACE: Oval, defined jawline, friendly expression

DISTINGUISHING: Natural freckle pattern across nose bridge and upper cheeks, warm genuine smile
```

### Version C: Embedding-Optimized Tokens

```
<subject_lock>
woman | fair_freckled_skin | dark_brown_straight_hair_long | center_part | warm_brown_eyes | oval_face | genuine_smile | Polish_American_features | natural_eyebrows | friendly_expression
</subject_lock>
```

## Base Identity Template for nanobanana-3

Use this as the foundation for all generation prompts. All physical traits must remain consistent across all images.

```
A realistic photograph of Shay, a woman with:
- Oval face, balanced proportions, defined but soft jawline, slightly rounded chin
- Fair skin tone (Fitzpatrick Type II), warm peachy undertones, light freckles concentrated on nose and upper cheeks, smooth texture, natural finish
- Medium-sized eyes, warm brown/hazel color, almond shape, slight upward cant at outer corners, natural eyelashes
- Medium thickness eyebrows, dark brown, natural shape with gentle arch, well-defined without being heavy
- Straight nose bridge, medium width, slightly rounded tip, proportionate to face
- Medium-full lips, natural pink tone, upper lip slightly thinner than lower
- Dark brown hair (#3B2820 hex approximate), natural shine, no highlights
- Long hair extending to mid-chest/breast line, straight with slight natural wave/body, fine to medium strand thickness, clean center part

Captured with a professional full-frame camera, ultra-detailed skin texture, natural color grading, no filters, no makeup (or subtle natural makeup), 50mm lens look, shallow depth of field, background softly blurred. Generate at least 2048x2048 resolution for later cropping to 1024x1024.
```

## Consistency Enforcement Tags

```
MAINTAIN_CONSTANT:

- Freckle distribution pattern (concentrated nose/cheeks)

- Eye color (warm brown)

- Face shape (oval)

- Skin tone (fair, warm undertone)

- Hair color (dark brown)

- Hair texture (straight)

- Hair length (chest-length when down)

- Natural eyebrow shape

- Smile characteristics

ALLOW_VARIATION:

- Hairstyle/arrangement

- Expression intensity (neutral to full smile)

- Lighting conditions

- Clothing

- Makeup intensity (generally minimal/natural)

- Hair wet vs dry state

- Angle/perspective
```

## Negative Prompt Tokens (Prevent Drift)

```
AVOID: different face shape, tan skin, olive complexion, dark skin, blonde hair, red hair, light hair, short hair, curly hair, blue eyes, green eyes, heavy makeup, dramatic eyebrows, thin lips, angular face, square jaw, no freckles, blemished skin, different ethnicity markers
```

## Single-Line Trigger for Maximum Efficiency

```
Fair-skinned Polish-American woman with natural freckles, warm brown eyes, long straight dark brown center-parted hair, oval face, genuine smile, approachable friendly expression, age 25-30 appearance
```

## nanobanana-3 Specific Format

For nanobanana-3 (Gemini 3 Image Pro), use natural language descriptions with the base identity template combined with wildcard variations. The model responds well to detailed, descriptive prompts that maintain character consistency while allowing stylistic variation.










