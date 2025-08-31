"""
Streamlit Media Tree Manager - Complete Campaign Media Organization Tool

Features:
- Visual campaign tree diagram with hierarchical structure
- Image thumbnails and video playback
- Drag-and-drop file upload with bulk support
- Advanced search and filtering by tags, name, description
- Full CRUD operations for campaigns, ad sets, and ads
- Export functionality (ZIP, CSV)
- Real-time analytics and statistics
- Responsive design with modern UI

Installation:
    pip install streamlit graphviz pillow pandas

Usage:
    streamlit run streamlit_media_tree.py
"""

import streamlit as st
from pathlib import Path
import json
import uuid
import mimetypes
import shutil
import io
import zipfile
import datetime
import base64
import graphviz
import pandas as pd
from typing import List, Dict, Any, Optional

# Optional dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configuration
DATA_DIR = Path('./media_tree_data')
MEDIA_DIR = DATA_DIR / 'media'
META_FILE = DATA_DIR / 'meta.json'
THUMB_DIR = DATA_DIR / 'thumbnails'

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'images': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'],
    'videos': ['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v', 'flv'],
    'audio': ['mp3', 'wav', 'ogg', 'aac', 'm4a']
}
ALL_ALLOWED = sum(ALLOWED_EXTENSIONS.values(), [])

# UI Configuration
ITEMS_PER_PAGE = 8
THUMBNAIL_SIZE = (200, 150)

class MediaTreeManager:
    def __init__(self):
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        
        if not META_FILE.exists():
            self.save_metadata(self.get_default_metadata())

    def get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata structure with demo data"""
        return {
            'campaign': {
                'name': 'Summer Product Launch',
                'objective': 'Increase brand awareness and drive sales for our new summer collection',
                'created_at': datetime.datetime.now().isoformat()
            },
            'ad_sets': {
                'Social Media Ads': {
                    'name': 'Social Media Ads',
                    'description': 'Ads for Facebook, Instagram, and Twitter',
                    'created_at': datetime.datetime.now().isoformat(),
                    'ads': {
                        'demo001': {
                            'id': 'demo001',
                            'name': 'Instagram Story Template',
                            'description': 'Bright and engaging story template for product showcase',
                            'tags': ['instagram', 'story', 'template', 'summer'],
                            'url': 'https://example.com/campaign1',
                            'schedule_date': None,
                            'created_at': datetime.datetime.now().isoformat(),
                            'file_path': '',
                            'mime_type': 'image/jpeg'
                        },
                        'demo002': {
                            'id': 'demo002', 
                            'name': 'Product Demo Video',
                            'description': 'Short video demonstrating key product features',
                            'tags': ['video', 'demo', 'product', 'features'],
                            'url': 'https://example.com/video',
                            'schedule_date': None,
                            'created_at': datetime.datetime.now().isoformat(),
                            'file_path': '',
                            'mime_type': 'video/mp4'
                        }
                    }
                },
                'Google Ads': {
                    'name': 'Google Ads',
                    'description': 'Search and display ads for Google Ads platform',
                    'created_at': datetime.datetime.now().isoformat(),
                    'ads': {
                        'demo003': {
                            'id': 'demo003',
                            'name': 'Search Ad Creative',
                            'description': 'Text and image combination for Google search results',
                            'tags': ['google', 'search', 'text-ad'],
                            'url': 'https://example.com/landing',
                            'schedule_date': None,
                            'created_at': datetime.datetime.now().isoformat(),
                            'file_path': '',
                            'mime_type': 'image/png'
                        }
                    }
                }
            }
        }

    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from JSON file"""
        try:
            with open(META_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_metadata()

    def save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to JSON file"""
        with open(META_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str, ensure_ascii=False)

    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        extension = filename.split('.')[-1].lower()
        return extension in ALL_ALLOWED

    def get_file_category(self, filename: str) -> str:
        """Get file category (images, videos, audio)"""
        extension = filename.split('.')[-1].lower()
        for category, extensions in ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return category
        return 'unknown'

    def save_uploaded_file(self, uploaded_file) -> tuple[str, str]:
        """Save uploaded file and return path and mime type"""
        if not self.is_allowed_file(uploaded_file.name):
            allowed_str = ', '.join(ALL_ALLOWED)
            raise ValueError(f'File type not allowed. Supported: {allowed_str}')
        
        # Generate unique filename
        file_extension = Path(uploaded_file.name).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{file_extension}"
        file_path = MEDIA_DIR / unique_name
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Get mime type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or 'application/octet-stream'
        
        # Create thumbnail for images
        if PIL_AVAILABLE and self.get_file_category(uploaded_file.name) == 'images':
            try:
                self.create_thumbnail(file_path)
            except Exception as e:
                st.warning(f"Could not create thumbnail: {e}")
        
        return str(file_path), mime_type

    def create_thumbnail(self, image_path: Path, size: tuple = THUMBNAIL_SIZE) -> Optional[str]:
        """Create thumbnail for image file"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                thumb_path = THUMB_DIR / f"thumb_{image_path.name}"
                img.save(thumb_path, optimize=True, quality=85)
                return str(thumb_path)
        except Exception:
            return None

    def get_thumbnail_path(self, file_path: str) -> Optional[str]:
        """Get thumbnail path for a media file"""
        if not file_path:
            return None
        original_path = Path(file_path)
        thumb_path = THUMB_DIR / f"thumb_{original_path.name}"
        return str(thumb_path) if thumb_path.exists() else None

    def create_ad_set(self, metadata: Dict[str, Any], name: str, description: str = ''):
        """Create new ad set"""
        name = name.strip()
        if not name:
            raise ValueError('Ad Set name is required')
        if name in metadata['ad_sets']:
            raise ValueError('Ad Set with this name already exists')
        
        metadata['ad_sets'][name] = {
            'name': name,
            'description': description,
            'created_at': datetime.datetime.now().isoformat(),
            'ads': {}
        }
        self.save_metadata(metadata)

    def create_ad(self, metadata: Dict[str, Any], ad_set_name: str, ad_data: Dict[str, Any]):
        """Create new ad in specified ad set"""
        ad_id = uuid.uuid4().hex[:8]
        ad_data.update({
            'id': ad_id,
            'created_at': datetime.datetime.now().isoformat()
        })
        metadata['ad_sets'][ad_set_name]['ads'][ad_id] = ad_data
        self.save_metadata(metadata)
        return ad_id

    def update_ad(self, metadata: Dict[str, Any], ad_set_name: str, ad_id: str, updates: Dict[str, Any]):
        """Update existing ad"""
        if ad_set_name in metadata['ad_sets'] and ad_id in metadata['ad_sets'][ad_set_name]['ads']:
            metadata['ad_sets'][ad_set_name]['ads'][ad_id].update(updates)
            self.save_metadata(metadata)

    def delete_ad(self, metadata: Dict[str, Any], ad_set_name: str, ad_id: str, delete_file: bool = False):
        """Delete ad and optionally its file"""
        if ad_set_name not in metadata['ad_sets'] or ad_id not in metadata['ad_sets'][ad_set_name]['ads']:
            return
        
        ad = metadata['ad_sets'][ad_set_name]['ads'][ad_id]
        
        if delete_file and 'file_path' in ad and ad['file_path']:
            try:
                file_path = Path(ad['file_path'])
                if file_path.exists():
                    file_path.unlink()
                
                # Delete thumbnail
                thumb_path = self.get_thumbnail_path(ad['file_path'])
                if thumb_path and Path(thumb_path).exists():
                    Path(thumb_path).unlink()
            except Exception as e:
                st.warning(f"Could not delete file: {e}")
        
        del metadata['ad_sets'][ad_set_name]['ads'][ad_id]
        self.save_metadata(metadata)

    def move_ad(self, metadata: Dict[str, Any], from_set: str, to_set: str, ad_id: str):
        """Move ad between ad sets"""
        if from_set == to_set:
            return
        
        ad = metadata['ad_sets'][from_set]['ads'].pop(ad_id)
        metadata['ad_sets'][to_set]['ads'][ad_id] = ad
        self.save_metadata(metadata)

    def search_ads(self, metadata: Dict[str, Any], query: str) -> List[tuple]:
        """Search ads by name, description, tags"""
        results = []
        query_lower = query.lower()
        
        for ad_set_name, ad_set in metadata['ad_sets'].items():
            for ad_id, ad in ad_set['ads'].items():
                # Search in name, description, tags
                searchable_text = ' '.join([
                    ad.get('name', ''),
                    ad.get('description', ''),
                    ' '.join(ad.get('tags', []))
                ]).lower()
                
                if query_lower in searchable_text:
                    results.append((ad_set_name, ad_id, ad))
        
        return results

    def get_statistics(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get campaign statistics"""
        stats = {
            'total_ad_sets': len(metadata['ad_sets']),
            'total_ads': 0,
            'ads_by_type': {'images': 0, 'videos': 0, 'audio': 0, 'other': 0},
            'ads_by_set': {}
        }
        
        for ad_set_name, ad_set in metadata['ad_sets'].items():
            ad_count = len(ad_set['ads'])
            stats['total_ads'] += ad_count
            stats['ads_by_set'][ad_set_name] = ad_count
            
            for ad in ad_set['ads'].values():
                if 'file_path' in ad and ad['file_path']:
                    category = self.get_file_category(ad['file_path'])
                    if category in stats['ads_by_type']:
                        stats['ads_by_type'][category] += 1
                    else:
                        stats['ads_by_type']['other'] += 1
        
        return stats

    def generate_tree_diagram(self, metadata: Dict[str, Any]) -> graphviz.Digraph:
        """Generate graphviz tree diagram"""
        dot = graphviz.Digraph(comment='Campaign Tree', format='svg')
        dot.attr(rankdir='TB', size='12,8')
        dot.attr('node', style='filled', fontname='Arial')
        
        # Campaign node
        campaign_name = metadata['campaign'].get('name', 'Campaign')
        objective = metadata['campaign'].get('objective', '')
        campaign_label = f"{campaign_name}"
        if objective:
            campaign_label += f"\\n{objective[:30]}{'...' if len(objective) > 30 else ''}"
        
        dot.node('campaign', campaign_label, 
                fillcolor='#1f77b4', fontcolor='white', shape='box')
        
        # Ad Set nodes
        for ad_set_name, ad_set in metadata['ad_sets'].items():
            ad_set_id = f"adset_{uuid.uuid5(uuid.NAMESPACE_DNS, ad_set_name).hex[:8]}"
            ad_count = len(ad_set['ads'])
            label = f"{ad_set_name}\\n({ad_count} ads)"
            
            dot.node(ad_set_id, label, 
                    fillcolor='#ff7f0e', fontcolor='white', shape='box')
            dot.edge('campaign', ad_set_id)
            
            # Ad nodes
            for ad_id, ad in ad_set['ads'].items():
                ad_node_id = f"ad_{ad_id}"
                ad_name = ad.get('name', 'Untitled Ad')
                
                # Determine file category for color coding
                file_category = 'unknown'
                if 'file_path' in ad and ad['file_path']:
                    file_category = self.get_file_category(ad['file_path'])
                
                # Color based on media type
                color_map = {
                    'images': '#2ca02c',
                    'videos': '#d62728', 
                    'audio': '#9467bd',
                    'unknown': '#8c564b'
                }
                color = color_map.get(file_category, '#8c564b')
                
                # Truncate long names for display
                display_name = ad_name[:20] + '...' if len(ad_name) > 20 else ad_name
                
                dot.node(ad_node_id, display_name, 
                        fillcolor=color, fontcolor='white', shape='ellipse')
                dot.edge(ad_set_id, ad_node_id)
        
        return dot

    def export_campaign_zip(self, metadata: Dict[str, Any]) -> io.BytesIO:
        """Export entire campaign as ZIP file"""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add metadata
            zip_file.writestr('campaign_metadata.json', 
                            json.dumps(metadata, indent=2, default=str))
            
            # Add media files
            for ad_set_name, ad_set in metadata['ad_sets'].items():
                for ad_id, ad in ad_set['ads'].items():
                    if 'file_path' in ad and ad['file_path']:
                        file_path = Path(ad['file_path'])
                        if file_path.exists():
                            # Organize in ZIP by ad set
                            archive_path = f"media/{ad_set_name}/{file_path.name}"
                            zip_file.write(file_path, archive_path)
        
        buffer.seek(0)
        return buffer

def render_media_preview(ad: Dict[str, Any], manager: MediaTreeManager, width: int = 150):
    """Render media preview based on file type"""
    if 'file_path' not in ad or not ad['file_path']:
        st.write("📄 Demo Content (No file)")
        return
    
    file_path = Path(ad['file_path'])
    if not file_path.exists():
        st.write("📄 Demo Content (File not found)")
        return
    
    category = manager.get_file_category(ad['file_path'])
    
    if category == 'images':
        thumb_path = manager.get_thumbnail_path(ad['file_path'])
        if thumb_path:
            st.image(thumb_path, width=width)
        else:
            st.image(ad['file_path'], width=width)
    elif category == 'videos':
        st.video(ad['file_path'])
    elif category == 'audio':
        st.audio(ad['file_path'])
    else:
        st.write(f"📄 {file_path.name}")

def main():
    # Page configuration
    st.set_page_config(
        page_title="Media Tree Manager",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize manager
    manager = MediaTreeManager()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .ad-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .tag {
        background: #e1f5fe;
        color: #01579b;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 0.1rem;
        display: inline-block;
    }
    .demo-banner {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 0.75rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Demo info banner
    st.markdown("""
    <div class="demo-banner">
        🎯 <strong>Demo Mode Active</strong> - This app comes with sample campaign data. 
        Upload your own media files to replace demo content!
    </div>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎬 Campaign Media Tree Manager</h1>
        <p>Organize your advertising campaign media with visual hierarchy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load metadata
    metadata = manager.load_metadata()
    
    # Sidebar for campaign management
    with st.sidebar:
        st.header("📊 Campaign Overview")
        
        # Campaign settings
        st.subheader("Campaign Settings")
        campaign_name = st.text_input(
            "Campaign Name", 
            value=metadata['campaign'].get('name', ''),
            key="campaign_name"
        )
        campaign_objective = st.text_area(
            "Campaign Objective", 
            value=metadata['campaign'].get('objective', ''),
            height=100,
            key="campaign_objective"
        )
        
        if st.button("💾 Save Campaign", use_container_width=True):
            metadata['campaign']['name'] = campaign_name
            metadata['campaign']['objective'] = campaign_objective
            manager.save_metadata(metadata)
            st.success("Campaign saved!")
            st.rerun()
        
        st.divider()
        
        # Statistics
        stats = manager.get_statistics(metadata)
        st.subheader("📈 Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ad Sets", stats['total_ad_sets'])
        with col2:
            st.metric("Total Ads", stats['total_ads'])
        
        # Media type breakdown
        if stats['total_ads'] > 0:
            st.subheader("Media Types")
            for media_type, count in stats['ads_by_type'].items():
                if count > 0:
                    st.write(f"• {media_type.title()}: {count}")
        
        st.divider()
        
        # Export options
        st.subheader("📦 Export")
        if st.button("📁 Download Campaign ZIP", use_container_width=True):
            zip_buffer = manager.export_campaign_zip(metadata)
            st.download_button(
                "⬇️ Download ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"campaign_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    # Main content area
    main_tab1, main_tab2, main_tab3 = st.tabs(["🌳 Campaign Tree", "📁 Ad Sets Management", "🔍 Search & Browse"])
    
    with main_tab1:
        st.subheader("Campaign Hierarchy Visualization")
        
        if metadata['ad_sets']:
            # Generate and display tree
            tree_diagram = manager.generate_tree_diagram(metadata)
            st.graphviz_chart(tree_diagram.source, use_container_width=True)
            
            # Tree legend
            st.markdown("""
            **Legend:**
            - 🔵 **Blue**: Campaign Level
            - 🟠 **Orange**: Ad Sets  
            - 🟢 **Green**: Image Ads
            - 🔴 **Red**: Video Ads
            - 🟣 **Purple**: Audio Ads
            - 🟤 **Brown**: Other File Types
            """)
        else:
            st.info("Create your first Ad Set to see the campaign tree!")
    
    with main_tab2:
        st.subheader("Ad Sets & Media Management")
        
        # Create new Ad Set
        with st.expander("➕ Create New Ad Set", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                new_ad_set_name = st.text_input("Ad Set Name", key="new_ad_set_name")
                new_ad_set_desc = st.text_input("Description (optional)", key="new_ad_set_desc")
            with col2:
                if st.button("Create Ad Set", use_container_width=True):
                    try:
                        manager.create_ad_set(metadata, new_ad_set_name, new_ad_set_desc)
                        st.success(f"Created Ad Set: {new_ad_set_name}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        
        # Display existing Ad Sets
        if not metadata['ad_sets']:
            st.info("No Ad Sets created yet. Create your first Ad Set above!")
        else:
            for ad_set_name, ad_set in metadata['ad_sets'].items():
                with st.expander(f"📂 {ad_set_name} ({len(ad_set['ads'])} ads)", expanded=True):
                    
                    # Ad Set info and controls
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**Description:** {ad_set.get('description', 'No description')}")
                        st.write(f"**Created:** {ad_set.get('created_at', 'Unknown')[:10]}")
                    with col2:
                        if st.button(f"📤 Upload Media", key=f"upload_{ad_set_name}"):
                            st.session_state[f"show_upload_{ad_set_name}"] = True
                    with col3:
                        if st.button(f"🗑️ Delete Set", key=f"delete_set_{ad_set_name}"):
                            if len(ad_set['ads']) == 0:
                                del metadata['ad_sets'][ad_set_name]
                                manager.save_metadata(metadata)
                                st.rerun()
                            else:
                                st.error("Cannot delete Ad Set with ads. Delete ads first.")
                    
                    # Upload interface
                    if st.session_state.get(f"show_upload_{ad_set_name}", False):
                        st.markdown("**📁 Upload Media Files**")
                        uploaded_files = st.file_uploader(
                            "Choose files", 
                            accept_multiple_files=True,
                            key=f"uploader_{ad_set_name}",
                            type=ALL_ALLOWED
                        )
                        
                        col_upload1, col_upload2 = st.columns([2, 1])
                        with col_upload1:
                            default_tags = st.text_input(
                                "Default tags (comma-separated)", 
                                key=f"tags_{ad_set_name}"
                            )
                        with col_upload2:
                            if st.button("🚀 Process Uploads", key=f"process_{ad_set_name}"):
                                if uploaded_files:
                                    success_count = 0
                                    for uploaded_file in uploaded_files:
                                        try:
                                            file_path, mime_type = manager.save_uploaded_file(uploaded_file)
                                            
                                            # Create ad entry
                                            ad_data = {
                                                'name': uploaded_file.name,
                                                'file_path': file_path,
                                                'mime_type': mime_type,
                                                'description': f'Uploaded from {uploaded_file.name}',
                                                'url': '',
                                                'tags': [tag.strip() for tag in default_tags.split(',') if tag.strip()],
                                                'schedule_date': None
                                            }
                                            
                                            manager.create_ad(metadata, ad_set_name, ad_data)
                                            success_count += 1
                                            
                                        except Exception as e:
                                            st.error(f"Failed to upload {uploaded_file.name}: {e}")
                                    
                                    if success_count > 0:
                                        st.success(f"Successfully uploaded {success_count} files!")
                                        st.session_state[f"show_upload_{ad_set_name}"] = False
                                        st.rerun()
                                else:
                                    st.warning("Please select files to upload")
                        
                        if st.button("❌ Cancel Upload", key=f"cancel_{ad_set_name}"):
                            st.session_state[f"show_upload_{ad_set_name}"] = False
                            st.rerun()
                    
                    # Display ads in this set
                    if ad_set['ads']:
                        st.markdown("**📺 Ads in this Set:**")
                        
                        for ad_id, ad in ad_set['ads'].items():
                            with st.container():
                                st.markdown('<div class="ad-card">', unsafe_allow_html=True)
                                
                                col_media, col_info, col_actions = st.columns([1, 3, 1])
                                
                                # Media preview
                                with col_media:
                                    render_media_preview(ad, manager, width=150)
                                
                                # Ad information
                                with col_info:
                                    st.write(f"**{ad.get('name', 'Untitled')}**")
                                    st.write(f"Description: {ad.get('description', 'No description')}")
                                    
                                    if ad.get('url'):
                                        st.markdown(f"🔗 [Link]({ad['url']})")
                                    
                                    if ad.get('tags'):
                                        tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in ad['tags']])
                                        st.markdown(f"Tags: {tags_html}", unsafe_allow_html=True)
                                    
                                    if ad.get('schedule_date'):
                                        st.write(f"📅 Scheduled: {ad['schedule_date']}")
                                
                                # Actions
                                with col_actions:
                                    if st.button("✏️ Edit", key=f"edit_{ad_id}"):
                                        st.session_state[f"editing_{ad_id}"] = True
                                    
                                    if st.button("🗑️ Delete", key=f"delete_{ad_id}"):
                                        manager.delete_ad(metadata, ad_set_name, ad_id, delete_file=True)
                                        st.rerun()
                                    
                                    # Move to other ad set
                                    other_sets = [name for name in metadata['ad_sets'].keys() if name != ad_set_name]
                                    if other_sets:
                                        move_to = st.selectbox(
                                            "Move to:", 
                                            [""] + other_sets,
                                            key=f"move_{ad_id}"
                                        )
                                        if move_to and st.button("➡️ Move", key=f"confirm_move_{ad_id}"):
                                            manager.move_ad(metadata, ad_set_name, move_to, ad_id)
                                            st.rerun()
                                
                                # Edit form
                                if st.session_state.get(f"editing_{ad_id}", False):
                                    with st.form(f"edit_form_{ad_id}"):
                                        st.markdown("**Edit Ad Details**")
                                        new_name = st.text_input("Name", value=ad.get('name', ''))
                                        new_desc = st.text_area("Description", value=ad.get('description', ''))
                                        new_url = st.text_input("URL", value=ad.get('url', ''))
                                        new_tags = st.text_input("Tags (comma-separated)", 
                                                                value=', '.join(ad.get('tags', [])))
                                        new_schedule = st.date_input("Schedule Date", value=None)
                                        
                                        col_save, col_cancel = st.columns(2)
                                        with col_save:
                                            if st.form_submit_button("💾 Save Changes"):
                                                updates = {
                                                    'name': new_name,
                                                    'description': new_desc,
                                                    'url': new_url,
                                                    'tags': [tag.strip() for tag in new_tags.split(',') if tag.strip()],
                                                    'schedule_date': new_schedule.isoformat() if new_schedule else None
                                                }
                                                manager.update_ad(metadata, ad_set_name, ad_id, updates)
                                                st.session_state[f"editing_{ad_id}"] = False
                                                st.rerun()
                                        with col_cancel:
                                            if st.form_submit_button("❌ Cancel"):
                                                st.session_state[f"editing_{ad_id}"] = False
                                                st.rerun()
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No ads in this Ad Set yet. Upload some media files!")
    
    with main_tab3:
        st.subheader("🔍 Search & Browse All Ads")
        
        # Search interface
        col_search, col_filter = st.columns([2, 1])
        with col_search:
            search_query = st.text_input("🔍 Search ads by name, description, or tags", key="search_query")
        with col_filter:
            filter_type = st.selectbox("Filter by type", ["All", "Images", "Videos", "Audio"])
        
        # Search results
        if search_query:
            search_results = manager.search_ads(metadata, search_query)
            
            if search_results:
                st.write(f"Found {len(search_results)} ads matching '{search_query}':")
                
                for ad_set_name, ad_id, ad in search_results:
                    if filter_type != "All":
                        category = manager.get_file_category(ad.get('file_path', ''))
                        if category.lower() != filter_type.lower():
                            continue
                    
                    with st.container():
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            render_media_preview(ad, manager, width=120)
                        
                        with col2:
                            st.write(f"**{ad.get('name', 'Untitled')}**")
                            st.write(f"Ad Set: {ad_set_name}")
                            st.write(f"Description: {ad.get('description', 'No description')}")
                            
                            if ad.get('tags'):
                                tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in ad['tags']])
                                st.markdown(f"Tags: {tags_html}", unsafe_allow_html=True)
                        
                        with col3:
                            st.write(f"ID: {ad_id}")
                            if ad.get('url'):
                                st.markdown(f"[🔗 Link]({ad['url']})")
                    
                    st.divider()
            else:
                st.info(f"No ads found matching '{search_query}'")
        else:
            # Browse all ads by ad set
            st.write("**Browse by Ad Set:**")
            
            for ad_set_name, ad_set in metadata['ad_sets'].items():
                if not ad_set['ads']:
                    continue
                
                st.markdown(f"### 📂 {ad_set_name}")
                
                # Pagination for this ad set
                ads_list = list(ad_set['ads'].items())
                total_ads = len(ads_list)
                
                if total_ads > ITEMS_PER_PAGE:
                    page = st.number_input(
                        f"Page for {ad_set_name}", 
                        min_value=1, 
                        max_value=(total_ads - 1) // ITEMS_PER_PAGE + 1,
                        value=1,
                        key=f"page_{ad_set_name}"
                    )
                    start_idx = (page - 1) * ITEMS_PER_PAGE
                    end_idx = start_idx + ITEMS_PER_PAGE
                    ads_list = ads_list[start_idx:end_idx]
                
                # Display ads in grid
                if ads_list:
                    cols = st.columns(min(3, len(ads_list)))
                    for idx, (ad_id, ad) in enumerate(ads_list):
                        with cols[idx % 3]:
                            # Media preview
                            render_media_preview(ad, manager, width=200)
                            
                            # Ad details
                            st.write(f"**{ad.get('name', 'Untitled')}**")
                            description = ad.get('description', 'No description')
                            st.write(f"{description[:50]}{'...' if len(description) > 50 else ''}")
                            
                            if ad.get('tags'):
                                tags_display = ', '.join(ad['tags'][:3])
                                if len(ad['tags']) > 3:
                                    tags_display += f" +{len(ad['tags']) - 3} more"
                                st.caption(f"🏷️ {tags_display}")

    # Advanced Features Section
    st.markdown("---")
    st.header("🛠️ Advanced Features")

    feature_col1, feature_col2, feature_col3 = st.columns(3)

    with feature_col1:
        st.subheader("📊 Analytics")
        if metadata['ad_sets']:
            # Create simple analytics chart
            ad_set_data = []
            for name, ad_set in metadata['ad_sets'].items():
                ad_set_data.append({
                    'Ad Set': name,
                    'Ads Count': len(ad_set['ads']),
                    'Created': ad_set.get('created_at', '')[:10]
                })
            
            if ad_set_data:
                df = pd.DataFrame(ad_set_data)
                st.dataframe(df, use_container_width=True)
                
                # Simple bar chart
                if len(df) > 1:
                    st.bar_chart(df.set_index('Ad Set')['Ads Count'])

    with feature_col2:
        st.subheader("🔄 Bulk Operations")
        
        if metadata['ad_sets']:
            bulk_ad_set = st.selectbox("Select Ad Set for bulk operations", 
                                     list(metadata['ad_sets'].keys()),
                                     key="bulk_ad_set")
            
            bulk_tags_input = st.text_input("Tags to add (comma-separated)", key="bulk_tags_input")
            if st.button("🏷️ Bulk Add Tags") and bulk_tags_input:
                tags_to_add = [tag.strip() for tag in bulk_tags_input.split(',') if tag.strip()]
                for ad_id, ad in metadata['ad_sets'][bulk_ad_set]['ads'].items():
                    existing_tags = set(ad.get('tags', []))
                    existing_tags.update(tags_to_add)
                    ad['tags'] = list(existing_tags)
                manager.save_metadata(metadata)
                st.success(f"Added tags to all ads in {bulk_ad_set}")
                st.rerun()

    with feature_col3:
        st.subheader("💾 Backup & Restore")
        
        # Backup
        if st.button("📦 Create Full Backup"):
            backup_buffer = manager.export_campaign_zip(metadata)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            st.download_button(
                "⬇️ Download Backup",
                data=backup_buffer.getvalue(),
                file_name=f"campaign_backup_{timestamp}.zip",
                mime="application/zip"
            )
        
        # Import metadata
        st.markdown("**📥 Import Metadata**")
        uploaded_meta = st.file_uploader("Upload metadata JSON", type=['json'], key="import_meta")
        if uploaded_meta and st.button("🔄 Import"):
            try:
                imported_data = json.load(uploaded_meta)
                # Validate structure
                if 'campaign' in imported_data and 'ad_sets' in imported_data:
                    manager.save_metadata(imported_data)
                    st.success("Metadata imported successfully!")
                    st.rerun()
                else:
                    st.error("Invalid metadata format")
            except Exception as e:
                st.error(f"Import failed: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🎬 <strong>Media Tree Manager</strong> | Organize your campaign media with ease</p>
        <p>💡 <strong>Tips:</strong> Use tags to categorize ads • Upload multiple files at once • Export for backup</p>
        <p>📁 Data stored in: <code>./media_tree_data/</code></p>
    </div>
    """, unsafe_allow_html=True)

    # Warning about dependencies
    if not PIL_AVAILABLE:
        st.sidebar.warning("⚠️ Pillow not installed. Image thumbnails disabled. Install with: `pip install pillow`")

# Run the application
if __name__ == "__main__":
    main()
