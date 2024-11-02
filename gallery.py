from PIL import Image
import os
import math
from pathlib import Path
import shutil
import json

class ImageGallery:
    def __init__(self, input_dir, output_dir, thumbnail_size=(400, 400), columns=3, images_per_page=12):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.thumb_size = thumbnail_size
        self.columns = columns
        self.images_per_page = images_per_page
        self.images = []
        self.likes_file = self.output_dir / 'likes.json'

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

        # Load existing likes if available
        self.load_likes()

    def load_likes(self):
        """Load likes from JSON file or initialize if not exists."""
        if self.likes_file.exists():
            try:
                with open(self.likes_file, 'r') as f:
                    self.likes = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.likes = {img['filename']: 0 for img in self.images}
        else:
            self.likes = {img['filename']: 0 for img in self.images}

    def save_likes(self):
        """Save likes to JSON file."""
        with open(self.likes_file, 'w') as f:
            json.dump(self.likes, f)

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

            .random-image-btn {
                position: fixed;
                top: 30px;
                right: 30px;
                background: white;
                border: 2px solid #007bff;
                color: #007bff;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                cursor: pointer;
                z-index: 4000;
                transition: all 0.3s ease;
            }
            
            .random-image-btn:hover {
                background: #007bff;
                color: white;
                transform: scale(1.1);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            }
            
            @media (max-width: 768px) {
                .random-image-btn {
                    bottom: 20px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                }
            }

            /* Like Button Styles */
            .like-container {
                position: absolute;
                bottom: 10px;
                right: 10px;
                z-index: 10;
            }
            
            .like-button {
                background: none;
                border: none;
                cursor: pointer;
                font-size: 24px;
                display: flex;
                align-items: center;
                transition: transform 0.2s ease;
            }
            
            .like-button:hover {
                transform: scale(1.2);
            }
            
            .like-button.liked .heart-icon {
                color: #ff4136;
                animation: heart-beat 0.5s ease;
            }
            
            .like-count {
                margin-left: 5px;
                font-size: 16px;
                color: #333;
            }
            
            /* Heart Beat Animation */
            @keyframes heart-beat {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.3); }
            }
            
            /* Lightbox Like */
            .lightbox-like-container {
                position: absolute;
                bottom: 20px;
                right: 20px;
            }
            
            .lightbox-like-button {
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
            
            .lightbox-like-button:hover {
                background: white;
                transform: scale(1.1);
            }
            
            .lightbox-like-count {
                position: absolute;
                bottom: -30px;
                right: 0;
                background: white;
                padding: 5px 10px;
                border-radius: 15px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            }
        </style>
        """
        
        js = """
        <script>
            function fetchLikes(url) {
                let data = null;
                const xhr = new XMLHttpRequest();
                xhr.open('GET', url, false);  // false makes it synchronous
                xhr.send();
                
                if (xhr.status === 200) {
                    data = JSON.parse(xhr.responseText);
                }
                return data;
            }
            let currentIndex = 0;
            let currentPage = 1;
            const images = %s;
            const imagesPerPage = %d;
            const totalPages = Math.ceil(images.length / imagesPerPage);
            let touchStartX = 0;
            let touchEndX = 0;
            let likes = fetchLikes('/likes') || {};

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
                    const galleryItem = document.querySelector(`[data-index="${i}"]`)
                    galleryItem.classList.add('visible');
                    const likeButton = galleryItem.querySelector('.like-button');
                    const likeCountEl = galleryItem.querySelector('.like-count');
                    likeButton.classList.add('liked');
                    likeCountEl.textContent = likes[images[i].filename];
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
                let likeContainer = document.querySelector('.lightbox-like-count');
                likeContainer.textContent = likes[images[currentIndex].filename];
                updateCounter();
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

            // New Random Image Function
            function showRandomImage() {
                const randomIndex = Math.floor(Math.random() * images.length);
                openLightbox(randomIndex);
            }

            // Like functions
            function toggleLike(filename, isLightbox = false) {
                const oldLikeCount = likes[filename] || 0;
                likes[filename] = oldLikeCount + 1;

                // Update like button and count
                updateLikeButton(filename, isLightbox);

                // Save likes to server (you'd replace this with actual backend logic)
                fetch('/save-likes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(likes)
                }).then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    return data;
                })
                .catch(error => {
                    console.error('Error saving likes:', error);
                    return null;
                });
                likes = likes || fetchLikes('/likes');
            }

            function updateLikeButton(filename, isLightbox = false) {
                const likeCount = likes[filename] || 0;
                
                if (isLightbox) {
                    const lightboxLikeButton = document.getElementById('lightbox-like-button');
                    const lightboxLikeCount = document.getElementById('lightbox-like-count');
                    
                    lightboxLikeButton.classList.add('liked');
                    lightboxLikeCount.textContent = likeCount;
                } else {
                    const galleryItem = document.querySelector(`.gallery-item[data-filename="${filename}"]`);
                    if (galleryItem) {
                        const likeButton = galleryItem.querySelector('.like-button');
                        const likeCountEl = galleryItem.querySelector('.like-count');
                        
                        likeButton.classList.add('liked');
                        likeCountEl.textContent = likeCount;
                    }
                }
            }

            // Extend existing lightbox to include like feature
            function openLightbox(index) {
                currentIndex = index;
                updateLightboxImage();
                document.getElementById('lightbox').classList.add('active');
                updateCounter();
                
                // Reset like button state
                const lightboxLikeButton = document.getElementById('lightbox-like-button');
                const lightboxLikeCount = document.getElementById('lightbox-like-count');
                const currentFilename = images[currentIndex].filename;
                
                lightboxLikeButton.classList.remove('liked');
                lightboxLikeButton.onclick = () => toggleLike(currentFilename, true);
                lightboxLikeCount.textContent = likes[currentFilename] || 0;
            }

            // Keyboard navigation (updated to include like feature)
            document.addEventListener('keydown', function(e) {
                if (document.getElementById('lightbox').classList.contains('active')) {
                    if (e.key === 'Escape') closeLightbox();
                    if (e.key === 'ArrowRight') nextImage();
                    if (e.key === 'ArrowLeft') prevImage();
                    if (e.key === 'r' || e.key === 'R') showRandomImage();
                    if (e.key === 'l' || e.key === 'L') {
                        const currentFilename = images[currentIndex].filename;
                        toggleLike(currentFilename, true);
                    }
                } else {
                    if (e.key === 'ArrowRight') nextPage();
                    if (e.key === 'ArrowLeft') prevPage();
                    if (e.key === 'r' || e.key === 'R') showRandomImage();
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
            likes_count = self.likes.get(img['filename'], 0)
            
            html += f"""
                <div class="gallery-item {span_class}" data-index="{idx}" data-filename="{img['filename']}" onclick="openLightbox({idx})">
                    <img src="thumbnails/{img['thumbnail']}" 
                         alt="{img['filename']}"
                         loading="lazy">
                    <div class="like-container">
                        <button class="like-button" onclick="event.stopPropagation(); toggleLike('{img['filename']}')">
                            <span class="heart-icon">❤️</span>
                            <span class="like-count">{likes_count}</span>
                        </button>
                    </div>
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

            <!-- Random Image Button -->
            <div class="random-image-btn" onclick="showRandomImage()" title="Show Random Image">
                🎲
            </div>
            
            <!-- Lightbox -->
            <div id="lightbox" class="lightbox" onclick="closeLightbox()">
                <div class="lightbox-content" onclick="event.stopPropagation()">
                    <img id="lightbox-image" class="lightbox-image" src="" alt="Full size image">
                    <button class="lightbox-nav prev-button" onclick="prevImage()">←</button>
                    <button class="lightbox-nav next-button" onclick="nextImage()">→</button>
                    <button class="close-button" onclick="closeLightbox()">×</button>
                    <div id="counter" class="counter">1 / 1</div>
                    
                    <!-- Lightbox Like Button -->
                    <div class="lightbox-like-container">
                        <button id="lightbox-like-button" class="lightbox-like-button" onclick="toggleLike(images[currentIndex].filename, true)">
                            ❤️
                        </button>
                        <div id="lightbox-like-count" class="lightbox-like-count">0</div>
                    </div>
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

        # Save likes
        self.save_likes()

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
