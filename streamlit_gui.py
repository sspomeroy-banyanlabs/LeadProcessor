#!/usr/bin/env python3
"""
Universal CSV-to-ClickUp Processor - Streamlit GUI
==================================================

Beautiful, demo-ready interface for the universal processor.
Perfect for showing non-technical users how powerful this tool is!

Usage:
    streamlit run streamlit_gui.py
"""

import streamlit as st
import pandas as pd
import requests
import json
import os
import tempfile
from datetime import datetime
import sys
import logging
from io import StringIO

# Add the scripts directory to path so we can import our processor
sys.path.append('scripts')

# Import our universal processor
try:
    from universal_processor import UniversalClickUpProcessor
except ImportError:
    st.error("❌ Could not import universal_processor. Make sure the file exists in the scripts/ directory.")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Universal CSV-to-ClickUp Processor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🚀 Universal CSV-to-ClickUp Processor</h1>
    <p>Automatically discover any ClickUp board structure and intelligently import CSV data</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for configuration
st.sidebar.header("🔧 Configuration")

# ClickUp Token Input
clickup_token = st.sidebar.text_input(
    "ClickUp API Token",
    type="password",
    help="Get your token from ClickUp Settings → Apps → API"
)

# Discover available lists if token is provided
available_lists = {}
if clickup_token:
    with st.sidebar:
        with st.spinner("🔍 Discovering your ClickUp boards..."):
            try:
                headers = {'Authorization': clickup_token}
                response = requests.get('https://api.clickup.com/api/v2/team', headers=headers)
                
                if response.status_code == 200:
                    teams = response.json()['teams']
                    for team in teams:
                        spaces_response = requests.get(f'https://api.clickup.com/api/v2/team/{team["id"]}/space', headers=headers)
                        if spaces_response.status_code == 200:
                            spaces = spaces_response.json()['spaces']
                            for space in spaces:
                                lists_response = requests.get(f'https://api.clickup.com/api/v2/space/{space["id"]}/list', headers=headers)
                                if lists_response.status_code == 200:
                                    lists = lists_response.json()['lists']
                                    for list_item in lists:
                                        list_name = f"{space['name']} → {list_item['name']}"
                                        available_lists[list_name] = list_item['id']
                    
                    st.sidebar.success(f"✅ Found {len(available_lists)} accessible boards!")
                else:
                    st.sidebar.error("❌ Invalid token or no access")
            except Exception as e:
                st.sidebar.error(f"❌ Error discovering boards: {str(e)}")

# List selection
selected_list = None
if available_lists:
    selected_list_name = st.sidebar.selectbox(
        "Select ClickUp Board",
        options=list(available_lists.keys()),
        help="Choose which board to import data into"
    )
    selected_list = available_lists[selected_list_name]
    st.sidebar.info(f"📋 Selected List ID: `{selected_list}`")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📤 CSV Upload & Processing")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload any CSV file - the processor will automatically map columns to ClickUp fields"
    )
    
    # Show CSV preview
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("📊 CSV Preview")
        st.dataframe(df.head(), use_container_width=True)
        st.info(f"📈 Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Show columns
        st.subheader("📝 CSV Columns")
        cols = st.columns(3)
        for i, col in enumerate(df.columns):
            with cols[i % 3]:
                st.code(col)

with col2:
    st.header("⚙️ Processing Options")
    
    # Test mode toggle
    test_mode = st.checkbox(
        "🧪 Test Mode",
        value=True,
        help="Process only first 3 rows for testing"
    )
    
    # Processing button
    process_button = st.button(
        "🚀 Process CSV",
        type="primary",
        disabled=not (clickup_token and selected_list and uploaded_file is not None),
        use_container_width=True
    )

# Processing section
if process_button:
    st.header("🔄 Processing Results")
    
    # Create temporary file for processing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        uploaded_file.seek(0)
        tmp_file.write(uploaded_file.read().decode('utf-8'))
        tmp_file_path = tmp_file.name
    
    try:
        # Capture logs
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize processor
        status_text.text("🔍 Initializing Universal Processor...")
        progress_bar.progress(20)
        
        processor = UniversalClickUpProcessor(clickup_token, selected_list)
        
        # Show discovered fields
        status_text.text("📋 Discovering board structure...")
        progress_bar.progress(40)
        
        if processor.discovered_fields:
            st.subheader("🎯 Auto-Discovered Board Structure")
            
            field_data = []
            for field_name, field in processor.discovered_fields.items():
                field_info = {
                    "Field Name": field_name,
                    "Type": field.type,
                    "ID": field.id[:8] + "..."  # Shortened for display
                }
                if field.options:
                    field_info["Options"] = ", ".join(list(field.options.keys())[:3]) + "..."
                else:
                    field_info["Options"] = "N/A"
                field_data.append(field_info)
            
            st.dataframe(pd.DataFrame(field_data), use_container_width=True)
        
        # Process CSV
        status_text.text("🧠 Building intelligent mapping...")
        progress_bar.progress(60)
        
        success = processor.process_csv(tmp_file_path, test_mode=test_mode)
        
        progress_bar.progress(100)
        
        if success:
            status_text.text("✅ Processing completed successfully!")
            st.markdown("""
            <div class="success-box">
                <h3>🎉 Success!</h3>
                <p>Your CSV has been successfully processed and uploaded to ClickUp!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show processing summary
            st.subheader("📊 Processing Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📁 Rows Processed", len(df) if not test_mode else min(3, len(df)))
            with col2:
                st.metric("📝 Fields Mapped", len(processor.csv_mapping))
            with col3:
                st.metric("🎯 Board Fields", len(processor.discovered_fields))
            
            # Show field mapping
            if processor.csv_mapping:
                st.subheader("🔗 Intelligent Field Mapping")
                mapping_data = []
                for csv_col, clickup_field_id in processor.csv_mapping.items():
                    # Find field name
                    field_name = "Unknown"
                    for fname, field in processor.discovered_fields.items():
                        if field.id == clickup_field_id:
                            field_name = fname
                            break
                    
                    mapping_data.append({
                        "CSV Column": csv_col,
                        "→": "→",
                        "ClickUp Field": field_name
                    })
                
                st.dataframe(pd.DataFrame(mapping_data), use_container_width=True)
        
        else:
            st.markdown("""
            <div class="error-box">
                <h3>❌ Processing Failed</h3>
                <p>There was an issue processing your CSV. Check the logs below for details.</p>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
    
    finally:
        # Cleanup
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

# Information section
st.header("ℹ️ How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-box">
        <h4>🔍 Auto-Discovery</h4>
        <p>Automatically discovers your ClickUp board's field structure, types, and dropdown options.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-box">
        <h4>🧠 Intelligent Mapping</h4>
        <p>Smart pattern matching to map your CSV columns to ClickUp fields, even with different names.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-box">
        <h4>🚀 Universal Processing</h4>
        <p>Works with any ClickUp board structure and any CSV format. Handles phone numbers, dropdowns, and more!</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:  # Center column
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h3 style="color: #667eea; margin-bottom: 0.5rem;">🧪 Banyan Labs</h3>
        <p style="margin: 0; color: #666;">Universal CSV-to-ClickUp Processor v3</p>
        <p style="margin: 0; font-size: 0.8rem; color: #999;">Built with ❤️ using Python & Streamlit</p>
    </div>
    """, unsafe_allow_html=True)
