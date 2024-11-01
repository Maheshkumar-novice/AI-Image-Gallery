from PIL import Image
import os
import math
from pathlib import Path
import shutil

class ImageGallery:
    def __init__(self, input_dir, output_dir, thumbnail_size=(400, 400), columns=3):
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
                        
                        # Create high-quality thumbnail
                        thumb = img.copy()
                        thumb.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                        thumb_path = thumbs_dir / f"thumb_{img_path.name}"
                        
                        # Save with high quality
                        if img_path.suffix.lower() in ('.jpg', '.jpeg'):
                            thumb.save(thumb_path, 'JPEG', quality=95)
                        else:
                            thumb.save(thumb_path)
                        
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
            :root {
                --gallery-bg: #f8f9fa;
                --thumb-bg: #ffffff;
                --overlay-bg: rgba(0, 0, 0, 0.95);
                --text-color: #333;
            }
            
            body {
                margin: 0;
                padding: 0;
                background-color: var(--gallery-bg);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            }
            
            .gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                grid-auto-rows: 300px;
                grid-gap: 20px;
                padding: 20px;
                max-width: 1800px;
                margin: 0 auto;
            }
            
            .gallery-item {
                position: relative;
                overflow: hidden;
                background: var(--thumb-bg);
                border-radius: 12px;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .gallery-item:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
            }
            
            .gallery-item img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.5s ease;
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
                background-color: var(--overlay-bg);
                z-index: 1000;
                justify-content: center;
                align-items: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .lightbox.active {
                display: flex;
                opacity: 1;
            }
            
            .lightbox-content {
                position: relative;
                max-width: 90%;
                max-height: 90vh;
                margin: auto;
                transition: transform 0.3s ease;
                touch-action: none; /* Prevents default touch behaviors */
            }
            
            .lightbox-image {
                max-width: 100%;
                max-height: 90vh;
                object-fit: contain;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .lightbox-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                font-size: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
            
            .lightbox-nav:hover {
                background: white;
                transform: translateY(-50%) scale(1.1);
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
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                font-size: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
            
            .close-button:hover {
                background: white;
                transform: scale(1.1);
            }
            
            .loading-spinner {
                display: none;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 50px;
                height: 50px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                to {
                    transform: translate(-50%, -50%) rotate(360deg);
                }
            }
            
            .counter {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(255, 255, 255, 0.9);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                color: #333;
            }
            
            @media (max-width: 768px) {
                .gallery {
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    grid-auto-rows: 250px;
                    padding: 10px;
                    grid-gap: 10px;
                }
                
                .gallery-item.wide {
                    grid-column: span 1;
                }
                
                .lightbox-nav {
                    width: 40px;
                    height: 40px;
                    font-size: 20px;
                }
                
                .close-button {
                    width: 40px;
                    height: 40px;
                    font-size: 20px;
                }
            }
        </style>
        """
        
        js = """
        <script>
            let currentIndex = 0;
            const images = %s;
            let touchStartX = 0;
            let touchEndX = 0;
            let isDragging = false;
            let startTime = 0;
            
            function openLightbox(index) {
                currentIndex = index;
                updateLightboxImage();
                document.getElementById('lightbox').classList.add('active');
                updateCounter();
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
            
            function updateCounter() {
                document.getElementById('counter').textContent = 
                    `${currentIndex + 1} / ${images.length}`;
            }
            
            function updateLightboxImage() {
                const img = document.getElementById('lightbox-image');
                const spinner = document.getElementById('loading-spinner');
                
                // Show loading spinner
                spinner.style.display = 'block';
                img.style.opacity = '0.3';
                
                // Preload new image
                const newImg = new Image();
                newImg.onload = function() {
                    img.src = images[currentIndex].filename;
                    img.style.opacity = '1';
                    spinner.style.display = 'none';
                    updateCounter();
                };
                newImg.src = images[currentIndex].filename;
            }
            
            // Touch events
            document.getElementById('lightbox').addEventListener('touchstart', function(e) {
                touchStartX = e.touches[0].clientX;
                startTime = new Date().getTime();
                isDragging = false;
            });
            
            document.getElementById('lightbox').addEventListener('touchmove', function(e) {
                if (e.touches.length > 1) return; // Ignore multi-touch
                isDragging = true;
                touchEndX = e.touches[0].clientX;
                
                // Calculate drag distance
                const dragDistance = touchEndX - touchStartX;
                const content = document.querySelector('.lightbox-content');
                
                // Apply transform during drag
                content.style.transform = `translateX(${dragDistance}px)`;
            });
            
            document.getElementById('lightbox').addEventListener('touchend', function(e) {
                const content = document.querySelector('.lightbox-content');
                content.style.transform = '';
                
                if (!isDragging) return;
                
                const dragDistance = touchEndX - touchStartX;
                const dragDuration = new Date().getTime() - startTime;
                const velocity = Math.abs(dragDistance) / dragDuration;
                
                // Threshold for swipe
                if (Math.abs(dragDistance) > 50 || velocity > 0.5) {
                    if (dragDistance > 0) {
                        prevImage();
                    } else {
                        nextImage();
                    }
                }
            });
            
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
                    <div id="loading-spinner" class="loading-spinner"></div>
                    <button class="lightbox-nav prev-button" onclick="prevImage()">←</button>
                    <button class="lightbox-nav next-button" onclick="nextImage()">→</button>
                    <button class="close-button" onclick="closeLightbox()">×</button>
                    <div id="counter" class="counter">1 / 1</div>
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
    create_gallery("./images", "./gallery_output_iter_3")
