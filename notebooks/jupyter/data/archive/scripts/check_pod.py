import os
print("Listing root directory:")
for item in os.listdir('/'):
    print(f"  {item}")
    
print("\nChecking if ComfyUI directory exists:")
if os.path.exists('/comfyui'):
    print("  ComfyUI directory exists")
    print("  Contents:")
    for item in os.listdir('/comfyui'):
        print(f"    {item}")
else:
    print("  ComfyUI directory does not exist")