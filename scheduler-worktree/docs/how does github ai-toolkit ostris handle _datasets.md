<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# how does github ai-toolkit ostris handle "datasets" we have them uploading but we want to mirror this using a jupyter notebook for our training diffusion experiments (lab)

Here’s how the GitHub AI-toolkit by Ostris handles "datasets" and how you can mirror this workflow using a Jupyter notebook for running your own training diffusion experiments:

***

## How Ostris AI-Toolkit Handles Datasets

- **Dataset Structure:** Ostris expects datasets to be folders containing images (`.jpg`, `.jpeg`, `.png`) paired with text files (`.txt`) for captions. Each image (`image1.jpg`) should have a corresponding caption file (`image1.txt`). The caption can include a `[trigger]` word configurable via the toolkit settings. Images are never upscaled; they are downscaled and automatically bucketed by aspect ratio or resolution for efficient batching during training. Cropping or resizing beforehand is not necessary.[^1]
- **Automatic Processing:** The loader scans your dataset folder, checks dimensions, filters out images below the set minimum resolution, and applies transformations (rescaling, cropping, etc.) required for training. Captions are integrated automatically if present.[^2][^1]
- **Advanced Features:** The toolkit supports:
    - Augmentation configuration via YAML configs.
    - Bucket management for efficient variable aspect ratio batching.
    - Integration of prompts/captions alongside images.
    - Latent and CLIP caching for speedup if enabled.
    - Training folder and bucket settings configuration via the UI or config files.[^2][^1]

***

## Mirroring Ostris Dataset Handling in Jupyter Notebook

You can replicate Ostris's dataset pipeline for diffusion model training in a Jupyter notebook by following these steps:

### 1. Dataset Folder Structure

- Folder named, e.g., `my_dataset/`
    - `image1.jpg`
    - `image1.txt` (contains caption for image1)
    - `image2.jpg`
    - `image2.txt`
    - ...


### 2. Loading Data in Jupyter

Use PyTorch’s `Dataset` and `DataLoader` with similar logic:

```python
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import os

class CaptionedImageDataset(Dataset):
    def __init__(self, folder, resolution=512):
        self.folder = folder
        self.img_files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        self.resolution = resolution
        self.transform = transforms.Compose([
            transforms.Resize((resolution, resolution)),
            transforms.ToTensor(),
        ])
    def __len__(self):
        return len(self.img_files)
    def __getitem__(self, idx):
        img_file = self.img_files[idx]
        img_path = os.path.join(self.folder, img_file)
        caption_path = os.path.splitext(img_path) + '.txt'
        image = Image.open(img_path).convert('RGB')
        image = self.transform(image)
        caption = ''
        if os.path.exists(caption_path):
            with open(caption_path, 'r', encoding='utf-8') as f:
                caption = f.read().strip()
        return image, caption
```

- You can then create a `DataLoader` as:

```python
dataset = CaptionedImageDataset('my_dataset', resolution=512)
dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
```


### 3. Extend Features as Needed

- Add multi-resolution bucketing or augmentation options by customizing the dataset class.
- Use similar naming conventions and config-file-driven training as Ostris.
- Optionally, mirror Ostris’s logic for “buckets” and batch prep by organizing images by resolution buckets before training.

***

## Key Points

- Ostris’s toolkit automatically processes images and captions, downscales/buckets images for training, and expects parallel text files for image captions.[^1][^2]
- In a Jupyter notebook, mirror this by using a folder structure with images and captions, and loading them with a custom PyTorch Dataset that follows these conventions.
- Integrate additional features like augmentation and bucketing as needed to match Ostris’s pipeline or your diffusion experiment requirements.

This approach will allow you to prototype, visualize, and experiment with the same style of datasets and preprocessing both in the Ostris UI and in your Jupyter notebook-based experiments.[^2][^1]

<div style="text-align: center">⁂</div>

[^1]: https://github.com/ostris/ai-toolkit

[^2]: https://github.com/ostris/ai-toolkit/blob/main/toolkit/data_loader.py

[^3]: https://www.kdjingpai.com/en/ai-toolkit-by-ostris/

[^4]: https://www.youtube.com/watch?v=qRrip3TdXKk

[^5]: https://www.youtube.com/watch?v=8ijPvfK38uw

[^6]: https://thedispatch.ai/reports/1551/

[^7]: https://www.aisharenet.com/en/ai-toolkit-by-ostris/

[^8]: https://www.youtube.com/watch?v=3gvsllg_oug

[^9]: https://www.reddit.com/r/StableDiffusion/comments/1ey3ck1/flux1_dev_lora_training_using_ostris_aitoolkit_on/

[^10]: https://www.reddit.com/r/FluxAI/comments/1fbs4kn/inference_script_for_ostrisaitoolkit_loras/

[^11]: https://socket.dev/pypi/package/ostris-ai-toolkit

[^12]: https://discourse.jupyter.org/t/ideas-on-how-to-integrate-ai-in-my-jupyter-kernel-gonb-akin-to-copilot/22933

[^13]: https://neurocanvas.net/blog/2024/ai-toolkit-guide/

[^14]: https://blog.paperspace.com/fine-tune-flux-schnell-dev/

[^15]: https://github.com/cozy-creator/ostris-ai-toolkit

[^16]: https://www.e2enetworks.com/blog/step-by-step-guide-to-fine-tune-flux-1-with-ai-toolkit-and-generate-images-for-ecommerce

[^17]: https://www.reddit.com/r/StableDiffusion/comments/1ev6zd1/best_way_to_prepare_a_dataset_for_training_lora/

[^18]: https://github.com/ostris/ai-toolkit/issues/320

[^19]: https://www.reddit.com/r/StableDiffusion/comments/1ezf0um/after_training_a_flux_lora_with_aitoolkit_the/

[^20]: https://gist.github.com/AndrewAltimit/2703c551eb5737de5a4c6767d3626cb8

