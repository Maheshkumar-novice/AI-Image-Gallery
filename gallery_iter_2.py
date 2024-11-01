from PIL import Image
import os
import math
from pathlib import Path
import shutil

class ImageGallery:
    def __init__(self, input_dir, output_dir, thumbnail_size=(300, 300), columns=3):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.thumb_size = thumbnail_size
        self.columns = columns
        self.images = []

    def process_images(self):
        thumbs_dir = self.output_dir / 'thumbnails'
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        
        for img_path in self.input_dir.glob('*'):
            if img_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif'):
                try:
                    with Image.open(img_path) as img:
                        # Get original dimensions
                        orig_width, orig_height = img.size
                        aspect_ratio = orig_width / orig_height
                        
                        # Calculate thumbnail dimensions
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
                        
                        self.images.append({
                            'filename': img_path.name,
                            'thumbnail': thumb_path.name,
                            'width': orig_width,
                            'height': orig_height,
                            'aspect_ratio': aspect_ratio
                        })
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

    def generate_html(self):
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
                cursor: pointer;
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
            
            .gallery-item.wide {
                grid-column: span 2;
            }
            
            /* Lightbox styles */
            .lightbox {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.9);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }
            
            .lightbox.active {
                display: flex;
            }
            
            .lightbox-content {
                position: relative;
                max-width: 90%;
                max-height: 90vh;
                margin: auto;
            }
            
            .lightbox-image {
                max-width: 100%;
                max-height: 90vh;
                object-fit: contain;
            }
            
            .lightbox-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                font-size: 20px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .lightbox-nav:hover {
                background: rgba(255, 255, 255, 1);
            }
            
            .prev-button {
                left: 20px;
            }
            
            .next-button {
                right: 20px;
            }
            
            .close-button {
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                font-size: 20px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .close-button:hover {
                background: rgba(255, 255, 255, 1);
            }
            
            @media (max-width: 768px) {
                .gallery-item.wide {
                    grid-column: span 1;
                }
            }
        </style>
        """
        
        js = """
        <script>
            let currentIndex = 0;
            const images = %s;
            
            function openLightbox(index) {
                currentIndex = index;
                updateLightboxImage();
                document.getElementById('lightbox').classList.add('active');
            }
            
            function closeLightbox() {
                document.getElementById('lightbox').classList.remove('active');
            }
            
            function nextImage() {
                currentIndex = (currentIndex + 1) %% images.length;
                updateLightboxImage();
            }
            
            function prevImage() {
                currentIndex = (currentIndex - 1 + images.length) %% images.length;
                updateLightboxImage();
            }
            
            function updateLightboxImage() {
                const img = document.getElementById('lightbox-image');
                img.src = images[currentIndex].filename;
            }
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (!document.getElementById('lightbox').classList.contains('active')) return;
                
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowRight') nextImage();
                if (e.key === 'ArrowLeft') prevImage();
            });
        </script>
        """ % str([{'filename': img['filename']} for img in self.images])
        
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
        
        for idx, img in enumerate(self.images):
            span_class = 'wide' if img['aspect_ratio'] > 1.7 else ''
            
            html += f"""
                <div class="gallery-item {span_class}" onclick="openLightbox({idx})">
                    <img src="thumbnails/{img['thumbnail']}" 
                         alt="{img['filename']}"
                         loading="lazy">
                </div>
            """
        
        html += """
            </div>
            
            <!-- Lightbox -->
            <div id="lightbox" class="lightbox" onclick="closeLightbox()">
                <div class="lightbox-content" onclick="event.stopPropagation()">
                    <img id="lightbox-image" class="lightbox-image" src="" alt="Full size image">
                    <button class="lightbox-nav prev-button" onclick="prevImage()">←</button>
                    <button class="lightbox-nav next-button" onclick="nextImage()">→</button>
                    <button class="close-button" onclick="closeLightbox()">×</button>
                </div>
            </div>
        """
        
        html += js + """
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
    create_gallery("./images", "./gallery_output_iter_2")
