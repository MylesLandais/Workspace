# Pin & Consistency Lock
```
FACE_STRUCTURE: oval face, balanced proportions, defined but soft jawline, slightly rounded chin
SKIN: fair skin tone (Fitzpatrick Type II), warm peachy undertones, light freckles concentrated on nose and upper cheeks, smooth texture, natural finish
EYES: medium-sized eyes, hazel-green eyes (distinctive green/hazel color), almond shape, slight upward cant at outer corners, natural eyelashes
EYEBROWS: medium thickness, natural color, natural shape with gentle arch, well-defined without being heavy
NOSE: straight bridge, medium width, slightly rounded tip, proportionate to face
MOUTH: medium-full lips, natural pink tone, upper lip slightly thinner than lower, wide genuine smile showing upper teeth
HAIR_COLOR: typically dyes hair blonde (can appear as dark brown naturally), natural shine
HAIR_TEXTURE: straight with slight natural wave/body, fine to medium strand thickness
HAIR_LENGTH: long, extending to mid-chest/breast line
HEIGHT: taller than 6ft (taller than Shay), uses door frame reference for height indication
BODY: tall stature, proportional build, athletic frame
```

### Key Distinguishing Features

- **EYES**: Hazel-green eyes (primary identifier - distinguishes from Shay's brown/hazel eyes)
- **HEIGHT**: Taller than 6ft, noticeably taller than Shay
- **HAIR**: Typically dyes hair blonde (natural color may be dark brown)

### Hairstyles

```
Messy bun with natural flyaways, positioned to show off ears
```

```
Elegant chignon, sleek and low to expose ear contours
```

---

## Prompt Generation System

For automated prompt generation and batch processing, see the [wildcard-based prompt system](index.md).

The system includes:
- [Identity & Face Lock](identity.md) - Character consistency tokens
- [Wildcard Categories](wildcards/) - Variable elements (hairstyles, outfits, poses, framing, lighting, backgrounds)
- [Batch Generator](batch_generator.py) - Automated prompt combination tool

**Target Model**: nanobanana-3 (Gemini 3 Image Pro)

---

## Discovered Insights

### Character Identification Keywords

When classifying prompts, look for these key indicators:

- **hazel-green eyes** (primary identifier)
- **hazel green eyes**
- **green eyes**
- **taller than 6ft**
- **taller than 6 ft**
- **6ft** (with context of height reference)
- **blonde hair** (when hair color is mentioned)
- **ariel mermaid tattoo** (often mentioned in Lexie prompts)

### Common Prompt Patterns

Lexie prompts frequently include:
- Full body studio casting photos
- Reference to door frame for height
- Ariel mermaid tattoo on hip
- Swimsuit/athletic wear contexts
- Professional model casting digitals
