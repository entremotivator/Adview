import streamlit as st
import pandas as pd
import json
import datetime
import uuid
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import io
import base64

# Page configuration
st.set_page_config(
    page_title="AI Agency Campaign Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for black theme
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        color: white;
    }
    .stApp {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(255,255,255,0.1);
        border-left: 4px solid #ffffff;
        margin: 10px 0;
    }
    .campaign-header {
        background: linear-gradient(90deg, #000000, #333333);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #ffffff;
    }
    .ad-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(255,255,255,0.1);
        margin: 10px 0;
        border: 1px solid #444444;
    }
    .success-metric {
        color: #4CAF50;
        font-weight: bold;
    }
    .warning-metric {
        color: #FF9800;
        font-weight: bold;
    }
    .danger-metric {
        color: #F44336;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a1a 0%, #000000 100%);
        color: white;
    }
    /* Override Streamlit default styles for dark theme */
    .stSelectbox > div > div {
        background-color: #2a2a2a;
        color: white;
    }
    .stTextInput > div > div > input {
        background-color: #2a2a2a;
        color: white;
        border: 1px solid #444444;
    }
    .stNumberInput > div > div > input {
        background-color: #2a2a2a;
        color: white;
        border: 1px solid #444444;
    }
    .stDateInput > div > div > input {
        background-color: #2a2a2a;
        color: white;
        border: 1px solid #444444;
    }
    .stButton > button {
        background-color: #333333;
        color: white;
        border: 1px solid #666666;
    }
    .stButton > button:hover {
        background-color: #444444;
        border: 1px solid #888888;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2a2a2a;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #000000;
        color: white;
    }
    .stExpander {
        background-color: #2a2a2a;
        border: 1px solid #444444;
    }
    .stExpander .streamlit-expanderHeader {
        background-color: #2a2a2a;
        color: white;
    }
    .stMetric {
        background-color: #2a2a2a;
        padding: 10px;
        border-radius: 5px;
    }
    .stMetric .metric-container {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'campaigns' not in st.session_state:
    st.session_state.campaigns = {}
if 'current_campaign' not in st.session_state:
    st.session_state.current_campaign = None
if 'gsheet_connected' not in st.session_state:
    st.session_state.gsheet_connected = False
if 'demo_loaded' not in st.session_state:
    st.session_state.demo_loaded = False

# Demo data
DEMO_CAMPAIGNS = {
    "ai_systems_2500": {
        "id": "ai_systems_2500",
        "name": "2500 AI Systems Bundle Campaign",
        "objective": "Lead Generation - AI Agency Services",
        "budget_daily": 500,
        "budget_total": 15000,
        "status": "Active",
        "created_date": "2025-01-01",
        "ad_sets": {
            "urgency_campaign": {
                "name": "Urgency Campaign",
                "budget": 200,
                "audience": "Business Owners 25-55",
                "placement": "Facebook + Instagram",
                "ads": {
                    "countdown_ad": {
                        "name": "48 Hours Left - Countdown",
                        "type": "Single Image",
                        "headline": "Get 2,500 AI Systems - 48 Hours Left!",
                        "primary_text": "🔥 EXCLUSIVE: 2,500 AI Systems Bundle - 90% OFF Today Only! Transform your business with our complete AI automation suite.",
                        "cta": "Claim Your AI Systems Now",
                        "status": "Active",
                        "metrics": {
                            "impressions": 45000,
                            "clicks": 1800,
                            "ctr": 4.0,
                            "cpc": 0.85,
                            "conversions": 144,
                            "conversion_rate": 8.0,
                            "cpa": 18.75,
                            "spend": 1530
                        }
                    },
                    "scarcity_video": {
                        "name": "Limited Time Video Ad",
                        "type": "Video",
                        "headline": "Only 100 Bundles Left - AI Systems",
                        "primary_text": "⏰ HURRY! Only 100 bundles remaining. Get 2,500 premium AI systems for just $4,997 (Regular: $49,970)",
                        "cta": "Secure Your Bundle",
                        "status": "Active",
                        "metrics": {
                            "impressions": 38000,
                            "clicks": 1520,
                            "ctr": 4.0,
                            "cpc": 0.92,
                            "conversions": 122,
                            "conversion_rate": 8.0,
                            "cpa": 20.50,
                            "spend": 1398
                        }
                    }
                }
            },
            "value_proposition": {
                "name": "Value Proposition Campaign",
                "budget": 200,
                "audience": "Marketing Agencies Lookalike",
                "placement": "All Placements",
                "ads": {
                    "roi_calculator": {
                        "name": "10x ROI Guarantee",
                        "type": "Carousel",
                        "headline": "10x ROI in 90 Days - Guaranteed",
                        "primary_text": "💰 Get $50,000 worth of AI tools for just $4,997. Our clients see 10x return within 90 days or money back.",
                        "cta": "Calculate Your ROI",
                        "status": "Active",
                        "metrics": {
                            "impressions": 42000,
                            "clicks": 1680,
                            "ctr": 4.0,
                            "cpc": 0.88,
                            "conversions": 134,
                            "conversion_rate": 8.0,
                            "cpa": 19.25,
                            "spend": 1478
                        }
                    }
                }
            },
            "retargeting": {
                "name": "Retargeting Campaign",
                "budget": 100,
                "audience": "Website Visitors - Past 30 Days",
                "placement": "Facebook + Instagram",
                "ads": {
                    "comeback_offer": {
                        "name": "Don't Miss Out - Special Offer",
                        "type": "Single Image",
                        "headline": "Still Thinking? Here's 20% More Off",
                        "primary_text": "🎯 We noticed you were interested in our AI systems. Here's an exclusive 20% additional discount - just for you!",
                        "cta": "Claim Extra Discount",
                        "status": "Active",
                        "metrics": {
                            "impressions": 15000,
                            "clicks": 750,
                            "ctr": 5.0,
                            "cpc": 0.75,
                            "conversions": 68,
                            "conversion_rate": 9.1,
                            "cpa": 16.50,
                            "spend": 562
                        }
                    }
                }
            }
        }
    }
}

# Google Sheets Integration Functions
def setup_google_sheets():
    """Setup Google Sheets connection"""
    st.subheader("🔗 Google Sheets Integration")
    
    with st.expander("📋 Setup Instructions", expanded=not st.session_state.gsheet_connected):
        st.markdown("""
        **To connect Google Sheets:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing one
        3. Enable Google Sheets API
        4. Create Service Account credentials
        5. Download the JSON key file
        6. Share your Google Sheet with the service account email
        7. Upload the JSON file below
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Google Service Account JSON",
            type=['json'],
            help="Upload your Google Service Account credentials JSON file"
        )
        
        if uploaded_file is not None:
            try:
                credentials_info = json.load(uploaded_file)
                st.session_state.gsheet_credentials = credentials_info
                st.success("✅ Credentials loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error loading credentials: {str(e)}")
    
    with col2:
        sheet_url = st.text_input(
            "Google Sheet URL",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
            help="Paste your Google Sheet URL here"
        )
        
        if sheet_url:
            try:
                # Extract sheet ID from URL
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
                st.session_state.sheet_id = sheet_id
                st.success(f"✅ Sheet ID extracted: {sheet_id[:20]}...")
            except:
                st.error("❌ Invalid Google Sheet URL")
    
    if st.button("🔗 Connect to Google Sheets"):
        if hasattr(st.session_state, 'gsheet_credentials') and hasattr(st.session_state, 'sheet_id'):
            try:
                # Setup credentials
                credentials = Credentials.from_service_account_info(
                    st.session_state.gsheet_credentials,
                    scopes=['https://spreadsheets.google.com/feeds',
                           'https://www.googleapis.com/auth/drive']
                )
                
                # Connect to Google Sheets
                gc = gspread.authorize(credentials)
                sheet = gc.open_by_key(st.session_state.sheet_id)
                
                st.session_state.gsheet_client = gc
                st.session_state.gsheet = sheet
                st.session_state.gsheet_connected = True
                
                st.success("🎉 Successfully connected to Google Sheets!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.error("❌ Please upload credentials and provide sheet URL first")

def sync_to_google_sheets(campaign_data):
    """Sync campaign data to Google Sheets"""
    if not st.session_state.gsheet_connected:
        return False
    
    try:
        # Prepare data for sheets
        campaigns_data = []
        ads_data = []
        metrics_data = []
        
        for campaign_id, campaign in campaign_data.items():
            # Campaign data
            campaigns_data.append([
                campaign_id,
                campaign['name'],
                campaign['objective'],
                campaign['budget_daily'],
                campaign['budget_total'],
                campaign['status'],
                campaign['created_date']
            ])
            
            # Ad sets and ads data
            for adset_id, adset in campaign['ad_sets'].items():
                for ad_id, ad in adset['ads'].items():
                    ads_data.append([
                        campaign_id,
                        adset_id,
                        ad_id,
                        ad['name'],
                        ad['type'],
                        ad['headline'],
                        ad['primary_text'],
                        ad['cta'],
                        ad['status']
                    ])
                    
                    # Metrics data
                    if 'metrics' in ad:
                        metrics = ad['metrics']
                        metrics_data.append([
                            campaign_id,
                            adset_id,
                            ad_id,
                            metrics.get('impressions', 0),
                            metrics.get('clicks', 0),
                            metrics.get('ctr', 0),
                            metrics.get('cpc', 0),
                            metrics.get('conversions', 0),
                            metrics.get('conversion_rate', 0),
                            metrics.get('cpa', 0),
                            metrics.get('spend', 0),
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ])
        
        # Update sheets
        sheet = st.session_state.gsheet
        
        # Campaigns sheet
        try:
            campaigns_ws = sheet.worksheet('Campaigns')
        except:
            campaigns_ws = sheet.add_worksheet('Campaigns', 1000, 10)
        
        campaigns_ws.clear()
        campaigns_ws.append_row(['Campaign ID', 'Name', 'Objective', 'Daily Budget', 'Total Budget', 'Status', 'Created Date'])
        for row in campaigns_data:
            campaigns_ws.append_row(row)
        
        # Ads sheet
        try:
            ads_ws = sheet.worksheet('Ads')
        except:
            ads_ws = sheet.add_worksheet('Ads', 1000, 15)
        
        ads_ws.clear()
        ads_ws.append_row(['Campaign ID', 'Ad Set ID', 'Ad ID', 'Name', 'Type', 'Headline', 'Primary Text', 'CTA', 'Status'])
        for row in ads_data:
            ads_ws.append_row(row)
        
        # Metrics sheet
        try:
            metrics_ws = sheet.worksheet('Metrics')
        except:
            metrics_ws = sheet.add_worksheet('Metrics', 1000, 15)
        
        if len(metrics_data) > 0:
            metrics_ws.clear()
            metrics_ws.append_row(['Campaign ID', 'Ad Set ID', 'Ad ID', 'Impressions', 'Clicks', 'CTR', 'CPC', 'Conversions', 'Conversion Rate', 'CPA', 'Spend', 'Updated'])
            for row in metrics_data:
                metrics_ws.append_row(row)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Sync failed: {str(e)}")
        return False

def load_demo_data():
    """Load demo campaign data"""
    st.session_state.campaigns = DEMO_CAMPAIGNS.copy()
    st.session_state.current_campaign = "ai_systems_2500"
    st.session_state.demo_loaded = True
    st.success("🎉 Demo data loaded successfully!")

def create_campaign_dashboard():
    """Create main campaign dashboard"""
    if not st.session_state.campaigns:
        st.info("👆 Load demo data or create a new campaign to get started!")
        return
    
    campaign = st.session_state.campaigns[st.session_state.current_campaign]
    
    # Campaign header
    st.markdown(f"""
    <div class="campaign-header">
        <h1>🚀 {campaign['name']}</h1>
        <p>{campaign['objective']}</p>
        <p><strong>Status:</strong> {campaign['status']} | <strong>Daily Budget:</strong> ${campaign['budget_daily']} | <strong>Total Budget:</strong> ${campaign['budget_total']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate overall metrics
    total_impressions = 0
    total_clicks = 0
    total_conversions = 0
    total_spend = 0
    
    for adset in campaign['ad_sets'].values():
        for ad in adset['ads'].values():
            if 'metrics' in ad:
                metrics = ad['metrics']
                total_impressions += metrics.get('impressions', 0)
                total_clicks += metrics.get('clicks', 0)
                total_conversions += metrics.get('conversions', 0)
                total_spend += metrics.get('spend', 0)
    
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    overall_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    overall_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👁️ Impressions</h3>
            <h2>{total_impressions:,}</h2>
            <p class="success-metric">+12% vs last week</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🖱️ Clicks</h3>
            <h2>{total_clicks:,}</h2>
            <p class="success-metric">CTR: {overall_ctr:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 Conversions</h3>
            <h2>{total_conversions}</h2>
            <p class="success-metric">Rate: {overall_conversion_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Spend</h3>
            <h2>${total_spend:,.0f}</h2>
            <p class="warning-metric">CPA: ${overall_cpa:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        roas = (total_conversions * 4997 / total_spend) if total_spend > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 ROAS</h3>
            <h2>{roas:.1f}x</h2>
            <p class="{'success-metric' if roas >= 5 else 'warning-metric'}">Target: 5.0x</p>
        </div>
        """, unsafe_allow_html=True)

def create_performance_charts():
    """Create performance visualization charts"""
    if not st.session_state.campaigns:
        return
    
    campaign = st.session_state.campaigns[st.session_state.current_campaign]
    
    st.subheader("📊 Performance Analytics")
    
    # Prepare data for charts
    ad_names = []
    impressions = []
    clicks = []
    conversions = []
    spend = []
    ctr = []
    conversion_rates = []
    
    for adset_name, adset in campaign['ad_sets'].items():
        for ad_name, ad in adset['ads'].items():
            if 'metrics' in ad:
                metrics = ad['metrics']
                ad_names.append(ad['name'])
                impressions.append(metrics.get('impressions', 0))
                clicks.append(metrics.get('clicks', 0))
                conversions.append(metrics.get('conversions', 0))
                spend.append(metrics.get('spend', 0))
                ctr.append(metrics.get('ctr', 0))
                conversion_rates.append(metrics.get('conversion_rate', 0))
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Performance by Ad
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name='Impressions', x=ad_names, y=impressions, yaxis='y', offsetgroup=1))
        fig1.add_trace(go.Bar(name='Clicks', x=ad_names, y=clicks, yaxis='y2', offsetgroup=2))
        fig1.update_layout(
            title='📈 Impressions vs Clicks by Ad',
            xaxis=dict(title='Ads'),
            yaxis=dict(title='Impressions', side='left'),
            yaxis2=dict(title='Clicks', side='right', overlaying='y'),
            barmode='group',
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Conversion Performance
        fig2 = px.scatter(
            x=spend, 
            y=conversions, 
            size=impressions,
            hover_name=ad_names,
            labels={'x': 'Spend ($)', 'y': 'Conversions'},
            title='💰 Spend vs Conversions (Size = Impressions)'
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # CTR and Conversion Rate comparison
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='CTR (%)', x=ad_names, y=ctr))
    fig3.add_trace(go.Bar(name='Conversion Rate (%)', x=ad_names, y=conversion_rates))
    fig3.update_layout(
        title='🎯 CTR vs Conversion Rate by Ad',
        xaxis=dict(title='Ads'),
        yaxis=dict(title='Rate (%)'),
        barmode='group',
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)

def create_ad_management():
    """Create ad management interface"""
    if not st.session_state.campaigns:
        return
    
    st.subheader("📝 Ad Management")
    
    campaign = st.session_state.campaigns[st.session_state.current_campaign]
    
    # Ad Set tabs
    adset_names = list(campaign['ad_sets'].keys())
    tabs = st.tabs([adset.replace('_', ' ').title() for adset in adset_names])
    
    for i, (adset_key, adset) in enumerate(campaign['ad_sets'].items()):
        with tabs[i]:
            st.markdown(f"**Budget:** ${adset['budget']} | **Audience:** {adset['audience']} | **Placement:** {adset['placement']}")
            
            # Display ads in this ad set
            for ad_key, ad in adset['ads'].items():
                with st.expander(f"📢 {ad['name']}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="ad-card">
                            <h4>{ad['headline']}</h4>
                            <p>{ad['primary_text'][:150]}...</p>
                            <p><strong>CTA:</strong> {ad['cta']}</p>
                            <p><strong>Type:</strong> {ad['type']} | <strong>Status:</strong> {ad['status']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if 'metrics' in ad:
                            metrics = ad['metrics']
                            st.metric("Impressions", f"{metrics['impressions']:,}")
                            st.metric("CTR", f"{metrics['ctr']:.1f}%")
                            st.metric("Conversions", metrics['conversions'])
                            st.metric("CPA", f"${metrics['cpa']:.2f}")
                    
                    # Edit buttons
                    col_edit1, col_edit2, col_edit3 = st.columns(3)
                    with col_edit1:
                        if st.button(f"✏️ Edit", key=f"edit_{ad_key}"):
                            st.session_state[f"editing_{ad_key}"] = True
                    with col_edit2:
                        if st.button(f"⏸️ Pause", key=f"pause_{ad_key}"):
                            ad['status'] = 'Paused'
                            st.success("Ad paused!")
                    with col_edit3:
                        if st.button(f"🗑️ Delete", key=f"delete_{ad_key}"):
                            del adset['ads'][ad_key]
                            st.success("Ad deleted!")
                            st.rerun()

def create_new_campaign():
    """Create new campaign interface"""
    st.subheader("➕ Create New Campaign")
    
    with st.form("new_campaign_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_name = st.text_input("Campaign Name", placeholder="e.g., AI Systems Holiday Sale")
            objective = st.selectbox("Campaign Objective", 
                                   ["Lead Generation", "Conversions", "Traffic", "Brand Awareness", "Reach"])
            daily_budget = st.number_input("Daily Budget ($)", min_value=10, value=100)
        
        with col2:
            total_budget = st.number_input("Total Budget ($)", min_value=100, value=3000)
            start_date = st.date_input("Start Date", datetime.date.today())
            end_date = st.date_input("End Date", datetime.date.today() + datetime.timedelta(days=30))
        
        submitted = st.form_submit_button("🚀 Create Campaign")
        
        if submitted and campaign_name:
            campaign_id = str(uuid.uuid4())[:8]
            new_campaign = {
                "id": campaign_id,
                "name": campaign_name,
                "objective": objective,
                "budget_daily": daily_budget,
                "budget_total": total_budget,
                "status": "Draft",
                "created_date": start_date.strftime('%Y-%m-%d'),
                "ad_sets": {}
            }
            
            st.session_state.campaigns[campaign_id] = new_campaign
            st.session_state.current_campaign = campaign_id
            st.success(f"✅ Campaign '{campaign_name}' created successfully!")
            st.rerun()

# Main App
def main():
    # Sidebar
    with st.sidebar:
        st.title("🚀 AI Campaign Manager")
        st.markdown("---")
        
        # Demo data section
        st.subheader("🎯 Quick Start")
        if st.button("📊 Load Demo Data", use_container_width=True):
            load_demo_data()
            st.rerun()
        
        if st.session_state.demo_loaded:
            st.success("✅ Demo data loaded!")
        
        st.markdown("---")
        
        # Campaign selection
        if st.session_state.campaigns:
            st.subheader("📋 Select Campaign")
            campaign_options = {v['name']: k for k, v in st.session_state.campaigns.items()}
            selected_campaign = st.selectbox(
                "Choose Campaign",
                options=list(campaign_options.keys()),
                index=0 if st.session_state.current_campaign else 0
            )
            st.session_state.current_campaign = campaign_options[selected_campaign]
        
        st.markdown("---")
        
        # Google Sheets sync
        if st.session_state.gsheet_connected:
            st.success("✅ Google Sheets Connected")
            if st.button("🔄 Sync to Sheets", use_container_width=True):
                with st.spinner("Syncing..."):
                    if sync_to_google_sheets(st.session_state.campaigns):
                        st.success("✅ Data synced successfully!")
                    else:
                        st.error("❌ Sync failed!")
        else:
            st.info("📊 Connect Google Sheets for live data storage")
    
    # Main content
    st.title("🚀 AI Agency Campaign Manager")
    st.markdown("**Manage your Facebook ad campaigns with live Google Sheets integration**")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📈 Analytics", "📝 Ad Management", "➕ New Campaign", "🔗 Google Sheets"])
    
    with tab1:
        create_campaign_dashboard()
    
    with tab2:
        create_performance_charts()
    
    with tab3:
        create_ad_management()
    
    with tab4:
        create_new_campaign()
    
    with tab5:
        setup_google_sheets()
    
    # Footer
    st.markdown("---")
    st.markdown("**💡 AI Agency Campaign Manager** - Built with Streamlit | Data synced with Google Sheets")

if __name__ == "__main__":
    main()

