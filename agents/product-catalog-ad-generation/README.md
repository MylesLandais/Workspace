# Product Catalog Ad Generation Agent

## Description

This project is a Personalized Ad Generation Assistant that helps marketing teams generate short-form video ads grounded in their product catalog. The agent pulls product metadata from a catalog (e.g., BigQuery), validates demographic targeting, and generates a video using product imagery and corporate branding standards. A human-in-the-loop feedback mechanism allows for iterative refinement of the generated ad.

The agent is defined in `content_gen_agent/agent.py` and uses the `gemini-2.5-pro` model. It orchestrates a multi-step workflow that includes product selection, storyline generation, image and video creation, and final ad assembly, with opportunities for human feedback at key stages.

This project contains default product imagery and a corporate logo that will get loaded into BigQuery as part of the deployment script.
## Changelog

See [Changelog.md](Changelog.md).

## Project Directory

```
├── content_gen_agent/
│   ├── agent.py                  # Main agent that orchestrates the ad generation workflow.
│   ├── func_tools/
│   │   ├── select_product.py     # Selects a product from BigQuery based on user input.
│   │   ├── generate_storyline.py # Generates the storyline, visual style guide, and asset sheet.
│   │   ├── generate_image.py     # Generates images based on the storyline and visual style guide.
│   │   ├── generate_video.py     # Generates video clips from images.
│   │   ├── generate_audio.py     # Generates background audio and voiceovers.
│   │   └── combine_video.py      # Combines video clips, audio, and voiceovers into a final video.
│   └── utils/
│       ├── evaluate_media.py     # Evaluates the generated media to ensure quality.
│       ├── evaluation_prompts.py # Contains prompts used for media evaluation.
│       ├── images.py             # Contains helper functions for image manipulation.
│       └── storytelling.py       # Contains prompts used for generating the storyline.
├── scripts/
│   ├── 01-setup-gcp.sh           # Enables required Google Cloud APIs.
│   ├── 02-deploy-gcs-and-bq.sh   # Deploys GCS, BigQuery, and populates with product data.
│   ├── populate_bq_with_gemini.py # Script to populate BigQuery with product metadata using Gemini.
│   └── add_padding.py          # Adds whitespace padding to images to fix aspect ratio.
├── static/
│   ├── uploads/                  # Contains all the static assets to be uploaded to GCS.
│   └── generated/                # Local directory where generated videos are saved.
└── ...
```

## Requirements

Before you begin, ensure you have:
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)

## Setup Scripts

The `scripts/` directory contains a series of automation scripts to set up the necessary Google Cloud infrastructure for the project. These scripts must be run in order.

### 1. `01-setup-gcp.sh`

This script enables the required Google Cloud APIs for the project to function correctly.

**Usage:**
```bash
bash scripts/01-setup-gcp.sh
```

### 2. `02-deploy-gcs-and-bq.sh`

This script provisions the GCS bucket, uploads all the static assets from the `static/uploads/` directory, creates the BigQuery dataset and table, and populates the table with product information using the `populate_bq_with_gemini.py` script.

**Usage:**
```bash
bash scripts/02-deploy-gcs-and-bq.sh
```

### 3. `populate_bq_with_gemini.py`

This script is called by `02-deploy-gcs-and-bq.sh` to populate the BigQuery table. It lists the product images in the GCS bucket, then uses Gemini to generate metadata (product name, description, search tags, etc.) for each product and inserts it into the BigQuery table.

#### Adding Your Own Products

To add your own products to the system, upload your product images to the `static/uploads/products/` directory. Use a descriptive filename for each image, as this will be used by Gemini to infer the product details. After adding the images, run the `02-deploy-gcs-and-bq.sh` script to upload the new products and update the BigQuery table.

## Usage

The main agent orchestrates the entire ad generation workflow, which can be broken down into the following steps:

1.  **Product Selection & Demographic Targeting**: The user provides a product name and desired demographic. The agent queries a BigQuery table to fetch product details and validates that the product is suitable for the target audience.
2.  **Storyline Generation**: The agent calls the `generate_storyline` tool to create a "before and after" narrative and a detailed visual style guide, grounded in product imagery and corporate branding.
3.  **Human Feedback & Iteration**: The generated storyline and visual guide are presented to the user for feedback. The agent incorporates the feedback to refine the creative direction.
4.  **Image Generation**: Based on the approved storyline, the agent generates a series of consistent images for the storyboard using the `generate_images_from_storyline` tool.
5.  **Video Generation**: The `generate_video` tool converts the images into video clips.
6.  **Audio & Voiceover Generation**: The `generate_audio_and_voiceover` tool creates a soundtrack and voiceover.
7.  **Final Assembly & Review**: The `combine` tool merges all assets into a final ad. The user can review the final video and provide further feedback for adjustments.

### Bring Your Own Asset Sheet

You can provide your own "asset sheet" as long as it includes the product image you are asking for. You can do this by pasting the "GCS URI" into your chat, and the agent will take this and download it. The agent will then use that asset sheet as context to generate the storyline, and move forward through the rest of the flow. Note that this allows you to skip the "product image" upload as long as it exists in your asset sheet. The GCS URI can be from any bucket that the authenticated user has access to.

### Bring Your Own Product Photo

Similarly, you can provide a direct GCS URI for a product photo instead of relying on the product selection from BigQuery. If you provide a GCS URI for the `product_photo_filename` parameter when calling the agent, it will download the image from that URI and use it as the product photo for the ad generation process.

### Hardcoded Configurations

The behavior of the agent is influenced by several hardcoded configurations in the `content_gen_agent` directory:

-   **Models**: The agent uses `gemini-2.5-pro` for storyline generation and `gemini-2.5-flash-image-preview` for image generation. The video generation is handled by `veo-3.0-fast-generate-001`, and the audio is generated using `lyria-002` and `gemini-2.5-flash-preview-tts`.
-   **Company Name**: The `COMPANY_NAME` can be set in the `.env` file. If not set, it defaults to "ACME Corp". This influences the branding of the generated content.
-   **Video Aspect Ratio**: All generated videos adhere to a `9:16` aspect ratio, suitable for short-form content platforms.
-   **Logo**: The company logo is hardcoded in `static/uploads/branding/logo.png` and is uploaded to GCS during the `02-deploy-gcs-and-bq.sh` setup script.

## General Tips and Best Practices

-   **Generating Videos with Children**: There is a known issue when generating videos that include children. It is best to avoid this, or request to be added to the allowlist for the necessary permission override.
-   **BigQuery Product Search**: The connection to BigQuery relies on an explicit input text match. This means if you search for "light bulb" but the corresponding row in BigQuery only includes "smart bulb" in its `search_tags` column, no match will be returned. Keep this in mind when debugging product search issues.
-   **Image Aspect Ratio**: For any new images added to the `static/uploads/products/` folder, ensure they are of a `9:16` aspect ratio. This is necessary to ensure consistent outputs from the image generation model. If your images do not have the correct aspect ratio, you can use the `add_padding.py` script to fix them.

### Fixing Product Image Aspect Ratio

If your product images do not have a `9:16` aspect ratio, you can run the following script to add whitespace padding and correct the dimensions. This script assumes your images have a white background.

**Usage:**
```bash
python scripts/add_padding.py
```

## Video Storage

All videos generated by the agent are stored in the GCS bucket, organized in a structured manner to ensure easy access and management.

### GCS Bucket Structure

The final, combined videos are uploaded to the `videos` folder in the GCS bucket, following a timestamp-based naming convention. The structure is as follows:

```
gs://<your-gcp-project-id>-contentgen-static/
├── videos/
│   ├── YYYY-MM-DD/
│   │   ├── HH-MM-SS/
│   │   │   ├── combined_video_1234567890.mp4
│   │   │   └── ...
│   └── ...
└── ...
```

This organization allows for easy tracking of generated videos and ensures that each ad has a unique, timestamped folder.

## Deployment

You can deploy the agent using the `agent_engine_deploy.py` script. Make sure your environment is authenticated with Google Cloud.

```bash
gcloud config set project <your-dev-project-id>
python agent_engine_deploy.py
```

### Disclaimer

This list is not an official Google product. Links on this list also are not necessarily to official Google products.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
