from PIL import Image
import os
import math
from pathlib import Path
import shutil

class ImageGallery:
    def __init__(self, input_dir, output_dir, thumbnail_size=(400, 400), columns=3, images_per_page=12):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.thumb_size = thumbnail_size
        self.columns = columns
        self.images_per_page = images_per_page
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
                min-height: calc(100vh - 180px);
            }
            
            .gallery-item {
                position: relative;
                overflow: hidden;
                background: var(--thumb-bg);
                border-radius: 12px;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                display: none; /* Hide all items by default */
            }
            
            .gallery-item.visible {
                display: block; /* Show only visible items */
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
            
            /* Pagination styles */
            .pagination {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                background: var(--gallery-bg);
                position: sticky;
                bottom: 0;
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .pagination button {
                background: white;
                border: 1px solid #ddd;
                padding: 8px 16px;
                margin: 0 4px;
                cursor: pointer;
                border-radius: 4px;
                transition: all 0.3s ease;
            }
            
            .pagination button:hover {
                background: #f0f0f0;
            }
            
            .pagination button:disabled {
                background: #f5f5f5;
                color: #999;
                cursor: not-allowed;
            }
            
            .pagination .current-page {
                padding: 8px 16px;
                margin: 0 8px;
                font-weight: 500;
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
                touch-action: none;
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
            let currentPage = 1;
            const images = %s;
            const imagesPerPage = %d;
            const totalPages = Math.ceil(images.length / imagesPerPage);
            
            // Pagination functions
            function showPage(page) {
                currentPage = page;
                const start = (page - 1) * imagesPerPage;
                const end = start + imagesPerPage;
                
                // Hide all items
                document.querySelectorAll('.gallery-item').forEach(item => {
                    item.classList.remove('visible');
                });
                
                // Show items for current page
                for (let i = start; i < end && i < images.length; i++) {
                    document.querySelector(`[data-index="${i}"]`).classList.add('visible');
                }
                
                // Update pagination buttons
                document.getElementById('prevPage').disabled = page === 1;
                document.getElementById('nextPage').disabled = page === totalPages;
                document.getElementById('currentPage').textContent = `${page} / ${totalPages}`;
                
                // Scroll to top of gallery
                document.querySelector('.gallery').scrollIntoView({ behavior: 'smooth' });
            }
            
            function nextPage() {
                if (currentPage < totalPages) {
                    showPage(currentPage + 1);
                }
            }
            
            function prevPage() {
                if (currentPage > 1) {
                    showPage(currentPage - 1);
                }
            }
            
            // Lightbox functions
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
                img.src = images[currentIndex].filename;
                updateCounter();
            }
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (document.getElementById('lightbox').classList.contains('active')) {
                    if (e.key === 'Escape') closeLightbox();
                    if (e.key === 'ArrowRight') nextImage();
                    if (e.key === 'ArrowLeft') prevImage();
                } else {
                    if (e.key === 'ArrowRight') nextPage();
                    if (e.key === 'ArrowLeft') prevPage();
                }
            });
            
            // Initialize gallery
            document.addEventListener('DOMContentLoaded', function() {
                showPage(1);
            });
        </script>
        """ % (str([{'filename': img['filename']} for img in self.images]), self.images_per_page)
        
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
                <div class="gallery-item {span_class}" data-index="{idx}" onclick="openLightbox({idx})">
                    <img src="thumbnails/{img['thumbnail']}" 
                         alt="{img['filename']}"
                         loading="lazy">
                </div>
            """
        
        html += """
            </div>
            
            <!-- Pagination -->
            <div class="pagination">
                <button id="prevPage" onclick="prevPage()">← Previous</button>
                <span id="currentPage" class="current-page">1 / 1</span>
                <button id="nextPage" onclick="nextPage()">Next →</button>
            </div>
            
            <!-- Lightbox -->
            <div id="lightbox" class="lightbox" onclick="closeLightbox()">
                <div class="lightbox-content" onclick="event.stopPropagation()">
                    <img id="lightbox-image" class="lightbox-image" src="" alt="Full size image">
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

def create_gallery(input_dir, output_dir, images_per_page=12):
    """
    Create an image gallery from a directory of images.
    
    Args:
        input_dir (str): Directory containing source images
        output_dir (str): Directory to output the gallery files
        images_per_page (int): Number of images to display per page
    """
    gallery = ImageGallery(input_dir, output_dir, images_per_page=images_per_page)
    gallery.process_images()
    gallery.generate_html()
    print(f"Gallery created successfully in {output_dir}")

# Example usage
if __name__ == "__main__":
    create_gallery("./images", "./gallery_output")
