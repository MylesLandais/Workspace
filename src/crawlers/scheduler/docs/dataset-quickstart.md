# Dataset Management Quick Start Guide

This guide will help you format your image dataset and initialize a Hugging Face repository for version tracking.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # HF_TOKEN=your_hugging_face_token
   # HF_USERNAME=your_hf_username  
   # DATASET_NAME=your_dataset_name
   ```

3. **Get your HuggingFace token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token with "Write" permissions
   - Add it to your `.env` file

## Quick Setup

### 1. Initialize Dataset Structure

```bash
# Update dataset_config.py with your details first, then:
python manage_dataset.py setup --name my-image-dataset --username your-hf-username
```

This creates:
- Local dataset folder structure
- Metadata templates for different CV tasks
- Dataset card (README.md)
- HuggingFace repository

### 2. Add Your Images

Organize your images in one of these structures:

**Option A: Classification (class folders)**
```
dataset/
├── train/
│   ├── cats/
│   │   ├── cat1.jpg
│   │   └── cat2.jpg
│   └── dogs/
│       ├── dog1.jpg
│       └── dog2.jpg
└── validation/
    ├── cats/
    └── dogs/
```

**Option B: Captioning/Detection (flat with metadata)**
```
dataset/
├── train/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── metadata.jsonl
└── validation/
    ├── image3.jpg
    ├── image4.jpg
    └── metadata.jsonl
```

### 3. Create Metadata (if needed)

For **image captioning**, create `metadata.jsonl`:
```jsonl
{"file_name": "image1.jpg", "text": "A cat sitting on a windowsill"}
{"file_name": "image2.jpg", "text": "A dog playing in the park"}
```

For **object detection**, create `metadata.jsonl`:
```jsonl
{"file_name": "image1.jpg", "objects": {"bbox": [[100, 50, 200, 150]], "categories": [0]}}
{"file_name": "image2.jpg", "objects": {"bbox": [[50, 30, 180, 120]], "categories": [1]}}
```

### 4. Validate Your Dataset

```bash
python manage_dataset.py validate
```

### 5. Push to HuggingFace Hub

```bash
# Push dataset with version tag
python manage_dataset.py push --tag v1.0 --message "Initial dataset release"
```

## Advanced Usage

### Check Dataset Status
```bash
python manage_dataset.py status
```

### Push Updates with Versioning
```bash
# After making changes to your dataset
python manage_dataset.py push --tag v1.1 --message "Added 100 new images"
```

### Custom Repository
```bash
python manage_dataset.py push --repo-id username/custom-dataset-name
```

## Dataset Formats Supported

### 1. ImageFolder Format
- Automatic label inference from folder names
- Best for classification tasks
- Supports train/validation/test splits

### 2. Metadata-based Format  
- Flexible metadata in CSV/JSONL/Parquet
- Supports multiple tasks (captioning, detection, etc.)
- Custom fields and annotations

### 3. WebDataset Format
- TAR archives for large datasets
- Efficient for streaming large datasets
- Good for production pipelines

## Loading Your Dataset

Once pushed to HuggingFace Hub:

```python
from datasets import load_dataset

# Load your dataset
dataset = load_dataset("your-username/your-dataset-name")

# Access splits
train_data = dataset["train"]
val_data = dataset["validation"]

# Access individual samples
sample = train_data[0]
image = sample["image"]  # PIL Image
label = sample["label"]  # or "text", "objects", etc.
```

## Version Tracking

Your dataset versions are tracked through:
- Git commits in the HuggingFace repository
- Version tags (v1.0, v1.1, etc.)
- Dataset card updates with statistics
- Automatic metadata tracking

## Troubleshooting

### Authentication Issues
```bash
# Login manually if needed
huggingface-cli login
```

### Large Files
- Images are automatically handled with Git LFS
- No special setup needed for image files
- TAR archives also supported for very large datasets

### Metadata Validation
- Use `validate` command to check structure
- Check metadata file formats match examples
- Ensure file_name fields match actual files

## Next Steps

1. **Customize your dataset card** in `dataset/README.md`
2. **Add more metadata** fields as needed for your use case  
3. **Set up automated workflows** for dataset updates
4. **Share your dataset** with the community or your team

For more advanced features, check the individual Python files:
- `setup_dataset.py` - Dataset initialization
- `dataset_utils.py` - Loading and pushing utilities  
- `dataset_config.py` - Configuration options