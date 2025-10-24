import os
import typing as tp

from docxpand.image import Image 

SPECIMENS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "specimens"
)

def load_specimen(specimen_name: str) -> tp.Optional[Image]:
    """Load document Prado specimen by name.

    Args:
        specimen_name: document classification name (e.g., "granite_surface")

    Returns:
         specimen image or None if it is not found
    """
    try:
        base_name = specimen_name.lower().replace('_', '-')
        
        # Try multiple formats in order of preference
        formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']
        
        for fmt in formats:
            specimen_path = os.path.join(SPECIMENS_DIR, f"{base_name}{fmt}")
            if os.path.exists(specimen_path):
                specimen_img = Image.read(specimen_path)
                return specimen_img
        
        print(f"Specimen '{specimen_name}' not found in any supported format")
        print(f"Looked for: {[f'{base_name}{fmt}' for fmt in formats]}")
        return None
        
    except Exception as e:
        print(f"Error loading specimen '{specimen_name}': {e}")
        return None
