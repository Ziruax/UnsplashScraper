import streamlit as st
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import time
import json

# Initialize UserAgent
ua = UserAgent()

def get_soup(url):
    """Get BeautifulSoup object with random user agent"""
    headers = {'User-Agent': ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        st.error(f"Error fetching page: {str(e)}")
        return None

def extract_image_data(figure):
    """Extract image metadata from figure element"""
    try:
        script = figure.find('script', string=re.compile('{"id"'))
        json_data = json.loads(script.string)
        
        return {
            'id': json_data['id'],
            'url': json_data['urls']['regular'],
            'full_url': json_data['urls']['full'],
            'raw_url': json_data['urls']['raw'],
            'width': json_data['width'],
            'height': json_data['height'],
            'alt': json_data.get('alt_description', ''),
            'color': json_data['color'],
            'likes': json_data['likes']
        }
    except (AttributeError, TypeError, json.JSONDecodeError, KeyError) as e:
        st.warning(f"Error parsing image data: {str(e)}")
        return None

def scrape_unsplash(search_term, orientation='', color='', min_width=0, min_height=0, max_results=20):
    """Scrape Unsplash based on parameters"""
    base_url = "https://unsplash.com/napi/search/photos"
    params = {
        'query': search_term,
        'per_page': 20,
        'page': 1,
        'xp': ''
    }
    
    if orientation:
        params['orientation'] = orientation
    if color:
        params['color'] = color
    
    images = []
    seen_ids = set()
    
    with st.spinner("Scraping Unsplash..."):
        progress_bar = st.progress(0)
        while len(images) < max_results:
            try:
                headers = {'User-Agent': ua.random}
                response = requests.get(base_url, params=params, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                if not data or 'results' not in data or not data['results']:
                    break
                
                new_images = 0
                for result in data['results']:
                    img_id = result['id']
                    if img_id in seen_ids:
                        continue
                        
                    seen_ids.add(img_id)
                    
                    # Apply dimension filters
                    if result['width'] < min_width or result['height'] < min_height:
                        continue
                    
                    images.append({
                        'id': img_id,
                        'url': result['urls']['regular'],
                        'full_url': result['urls']['full'],
                        'raw_url': result['urls']['raw'],
                        'width': result['width'],
                        'height': result['height'],
                        'alt': result.get('alt_description', ''),
                        'color': result['color'],
                        'likes': result['likes']
                    })
                    new_images += 1
                    if len(images) >= max_results:
                        break
                
                if new_images == 0:
                    break
                    
                params['page'] += 1
                progress_bar.progress(min(len(images)/max_results, 1.0))
                time.sleep(0.7)  # Be polite
                
            except Exception as e:
                st.error(f"Scraping error: {str(e)}")
                break
    
    if progress_bar is not None:
        progress_bar.empty()
    return images[:max_results]

# Streamlit UI
st.set_page_config(page_title="Advanced Unsplash Scraper", layout="wide")
st.title("🚀 Advanced Unsplash Image Scraper")
st.write("""
Scrape high-quality images from Unsplash with advanced filters.
**Note:** For educational purposes only. Respect Unsplash's [Terms of Service](https://unsplash.com/terms).
""")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Scraping Parameters")
    search_term = st.text_input("🔍 Search Term", "nature")
    orientation = st.selectbox(
        "📐 Orientation", 
        ["Any", "Landscape", "Portrait", "Squarish"]
    )
    color = st.selectbox(
        "🎨 Color Filter", 
        ["Any", "Black and White", "Black", "White", "Yellow", "Orange", 
         "Red", "Purple", "Magenta", "Green", "Teal", "Blue"]
    )
    min_width = st.number_input("📏 Min Width (px)", 0, 10000, 1200)
    min_height = st.number_input("📏 Min Height (px)", 0, 10000, 800)
    max_results = st.slider("🎯 Max Images to Scrape", 1, 100, 20)
    
    st.divider()
    st.info("""
    **Educational Purpose Only**  
    This tool demonstrates advanced web scraping techniques:
    - Dynamic AJAX handling
    - JSON data parsing
    - Advanced filtering
    - Polite scraping practices
    - Robust error handling
    """)

# Transform filter values to API format
orientation_map = {
    "Any": "",
    "Landscape": "landscape",
    "Portrait": "portrait",
    "Squarish": "squarish"
}
color_map = {
    "Any": "",
    "Black and White": "black_and_white",
    "Black": "black",
    "White": "white",
    "Yellow": "yellow",
    "Orange": "orange",
    "Red": "red",
    "Purple": "purple",
    "Magenta": "magenta",
    "Green": "green",
    "Teal": "teal",
    "Blue": "blue"
}

# Scrape button
if st.button("✨ Scrape Images", use_container_width=True):
    results = scrape_unsplash(
        search_term=search_term,
        orientation=orientation_map[orientation],
        color=color_map[color],
        min_width=min_width,
        min_height=min_height,
        max_results=max_results
    )
    
    if not results:
        st.warning("No images found matching your criteria")
    else:
        st.success(f"Found {len(results)} images!")
        st.divider()
        
        # Display results in grid
        cols = st.columns(3)
        for i, img in enumerate(results):
            with cols[i % 3]:
                with st.expander(f"Image {i+1}", expanded=True):
                    st.image(img['url'], caption=img['alt'], use_column_width=True)
                    
                    # Image metadata
                    st.caption(f"🔍 ID: `{img['id']}`")
                    st.caption(f"📏 Dimensions: {img['width']}x{img['height']}px")
                    st.caption(f"❤️ Likes: {img['likes']}")
                    st.caption(f"🎨 Color: `{img['color']}`")
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            label="Regular",
                            data=requests.get(img['url']).content,
                            file_name=f"{img['id']}_regular.jpg",
                            mime="image/jpeg",
                            key=f"reg_{i}",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            label="Full",
                            data=requests.get(img['full_url']).content,
                            file_name=f"{img['id']}_full.jpg",
                            mime="image/jpeg",
                            key=f"full_{i}",
                            use_container_width=True
                        )
                    with col3:
                        st.download_button(
                            label="RAW",
                            data=requests.get(img['raw_url']).content,
                            file_name=f"{img['id']}_raw.jpg",
                            mime="image/jpeg",
                            key=f"raw_{i}",
                            use_container_width=True
                        )

# How to use section
with st.expander("ℹ️ How to use this scraper & Technical Details"):
    st.markdown("""
    **Advanced Features:**
    
    - **AJAX API Handling**: Uses Unsplash's private JSON API
    - **Advanced Filtering**: Orientation, color, dimensions
    - **Polite Scraping**: Random user agents, delays, error handling
    - **Rich Metadata**: Dimensions, color, likes, alt text
    - **Multiple Resolutions**: Regular, Full, RAW download options
    
    **Technical Stack:**
    - Python 3.9+ (Streamlit Cloud compatible)
    - Streamlit 1.33.0
    - BeautifulSoup 4.12.3
    - Requests 2.32.2
    - Fake-UserAgent 1.5.1
    
    **Deployment Notes:**
    - Fixed Pillow dependency for Python 3.13 compatibility
    - Increased timeout values for reliability
    - Enhanced error handling
    - Optimized UI layout
    """)
    
    st.code("""
    # Core scraping function
    def scrape_unsplash(search_term, orientation='', color='', 
                        min_width=0, min_height=0, max_results=20):
        base_url = "https://unsplash.com/napi/search/photos"
        params = {'query': search_term, 'per_page': 20, 'page': 1}
        
        # ... (filter handling and pagination logic) ...
        
        while len(images) < max_results:
            # ... (API request with error handling) ...
            
            # Process JSON response
            data = response.json()
            for result in data['results']:
                # ... (apply filters and collect results) ...
            
        return images
    """, language='python')

st.caption("⚠️ Use responsibly - This tool is for educational purposes only. Respect website terms of service.")
