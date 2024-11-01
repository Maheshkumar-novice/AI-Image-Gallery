from PIL import Image
import os
import math
from pathlib import Path
import shutil

class ImageGallery:
    def __init__(self, input_dir, output_dir, thumbnail_size=(300, 300), columns=3):
        """
        Initialize the gallery generator.
        
        Args:
            input_dir (str): Directory containing source images
            output_dir (str): Directory to output the gallery files
            thumbnail_size (tuple): Maximum width and height for thumbnails
            columns (int): Number of columns in the gallery grid
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.thumb_size = thumbnail_size
        self.columns = columns
        self.images = []
        
    def process_images(self):
        """Process all images in the input directory and create thumbnails."""
        # Create output directories if they don't exist
        thumbs_dir = self.output_dir / 'thumbnails'
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each image
        for img_path in self.input_dir.glob('*'):
            if img_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif'):
                try:
                    with Image.open(img_path) as img:
                        # Calculate aspect ratio
                        aspect_ratio = img.width / img.height
                        
                        # Determine thumbnail dimensions while maintaining aspect ratio
                        if aspect_ratio > 1:
                            thumb_width = self.thumb_size[0]
                            thumb_height = int(thumb_width / aspect_ratio)
                        else:
                            thumb_height = self.thumb_size[1]
                            thumb_width = int(thumb_height * aspect_ratio)
                        
                        # Create thumbnail
                        img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                        thumb_path = thumbs_dir / f"thumb_{img_path.name}"
                        img.save(thumb_path)
                        
                        # Store image info
                        self.images.append({
                            'filename': img_path.name,
                            'thumbnail': thumb_path.name,
                            'width': thumb_width,
                            'height': thumb_height,
                            'aspect_ratio': aspect_ratio
                        })
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

    def generate_html(self):
        """Generate responsive HTML gallery."""
        css = """
        <style>
            .gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                grid-auto-rows: 250px;
                grid-gap: 10px;
                padding: 20px;
            }
            
            .gallery-item {
                position: relative;
                overflow: hidden;
                background: #f0f0f0;
                border-radius: 8px;
            }
            
            .gallery-item img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.3s ease;
            }
            
            .gallery-item:hover img {
                transform: scale(1.05);
            }
            
            /* Span wide images across two columns */
            .gallery-item.wide {
                grid-column: span 2;
            }
            
            @media (max-width: 768px) {
                .gallery-item.wide {
                    grid-column: span 1;
                }
            }
        </style>
        """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Image Gallery</title>
            {css}
        </head>
        <body>
            <div class="gallery">
        """
        
        for img in self.images:
            # Determine if image should span multiple columns
            span_class = 'wide' if img['aspect_ratio'] > 1.7 else ''
            
            html += f"""
                <div class="gallery-item {span_class}">
                    <a href="{img['filename']}" target="_blank">
                        <img src="thumbnails/{img['thumbnail']}" 
                             alt="{img['filename']}"
                             loading="lazy">
                    </a>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(self.output_dir / 'index.html', 'w') as f:
            f.write(html)
            
        # Copy original images to output directory
        for img in self.images:
            shutil.copy2(
                self.input_dir / img['filename'],
                self.output_dir / img['filename']
            )

def create_gallery(input_dir, output_dir):
    """
    Create an image gallery from a directory of images.
    
    Args:
        input_dir (str): Directory containing source images
        output_dir (str): Directory to output the gallery files
    """
    gallery = ImageGallery(input_dir, output_dir)
    gallery.process_images()
    gallery.generate_html()
    print(f"Gallery created successfully in {output_dir}")

# Example usage
if __name__ == "__main__":
    create_gallery("./images", "./gallery_output_iter_1")
