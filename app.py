import streamlit as st
import os
import tempfile
import base64
import requests
import re
from datetime import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Basic page config without custom styling
st.set_page_config(page_title="Phi-4 Multimodal Chat", layout="wide", page_icon="🤖")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("AZURE_INFERENCE_CREDENTIAL", "")
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful AI assistant that can analyze images, audio and text."
if "pending_files" not in st.session_state:
    st.session_state.pending_files = []
if "is_sending" not in st.session_state:
    st.session_state.is_sending = False

# Helper Functions
def file_to_base64(file_path):
    try:
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        st.error(f"Failed to convert file to base64: {str(e)}")
        return None

def save_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    
    try:
        # Get file extension
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        # Create temp file with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            
        # Determine file type
        file_type = None
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            file_type = 'image'
        elif file_extension in ['mp3', 'wav', 'ogg', 'm4a']:
            file_type = 'audio'
            
        if not file_type:
            os.unlink(temp_file.name)
            return None
            
        return {
            "path": temp_file.name,
            "type": file_type,
            "name": file_name
        }
    except Exception as e:
        st.error(f"Error saving uploaded file: {str(e)}")
        return None

def extract_urls(text):
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

def download_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, f"Failed to download from URL: {response.status_code}"
            
        # Determine file type
        content_type = response.headers.get('content-type', '')
        lower_url = url.lower()
        
        if 'image' in content_type or any(ext in lower_url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            file_type = 'image'
            extension = lower_url.split('.')[-1] if '.' in lower_url.split('/')[-1] else "jpg"
        elif 'audio' in content_type or any(ext in lower_url for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            file_type = 'audio'
            extension = lower_url.split('.')[-1] if '.' in lower_url.split('/')[-1] else "mp3"
        else:
            return None, "URL does not appear to be an image or audio file"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp_file:
            temp_file.write(response.content)
            file_name = url.split('/')[-1] if '/' in url else f"download.{extension}"
            
            return {
                'type': file_type,
                'path': temp_file.name,
                'name': file_name
            }, None
            
    except Exception as e:
        return None, f"Error processing URL: {str(e)}"

def process_with_api(messages):
    try:
        client = ChatCompletionsClient(
            endpoint='https://Phi-4-multimodal-instruct-friil.eastus.models.ai.azure.com',
            credential=AzureKeyCredential(st.session_state.api_key)
        )
        
        api_messages = []
        
        # Add system message
        if st.session_state.system_prompt:
            api_messages.append({"role": "system", "content": st.session_state.system_prompt})
        
        # Process messages for API
        for msg in messages:
            if msg["role"] == "user":
                # Start with text content (ensure it's a string)
                content_items = [{"type": "text", "text": str(msg["content"])}]
                
                # Add images if available
                if "images" in msg and msg["images"]:
                    for img in msg["images"]:
                        img_b64 = file_to_base64(img["path"])
                        if img_b64:
                            content_items.append({
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            })
                
                # Add audio files if available
                if "audio_files" in msg and msg["audio_files"]:
                    for audio in msg["audio_files"]:
                        audio_b64 = file_to_base64(audio["path"])
                        if audio_b64:
                            audio_ext = audio["path"].split(".")[-1]
                            content_items.append({
                                "type": "audio_url",
                                "audio_url": {"url": f"data:audio/{audio_ext};base64,{audio_b64}"}
                            })
                
                api_messages.append({"role": "user", "content": content_items})
            else:
                # Assistant messages are simple text
                api_messages.append({"role": "assistant", "content": msg["content"]})
        
        # Call the API
        response = client.complete({
            "messages": api_messages,
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 800
        })
            
        return response.choices[0].message.content
            
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}"

# Sidebar with settings
with st.sidebar:
    st.title("Phi-4 Chat Settings")
    
    # API key input
    api_key = st.text_input("Azure API Key", type="password", value=st.session_state.api_key)
    if api_key:
        st.session_state.api_key = api_key
    
    # System prompt
    system_prompt = st.text_area("System Prompt", value=st.session_state.system_prompt, height=100)
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt
    
    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.pending_files = []
        st.rerun()

# Main content area
st.title("Phi-4 Multimodal Chat")

# Check for API key
if not st.session_state.api_key:
    st.warning("⚠️ Please enter your Azure API Key in the sidebar to get started.")
    st.info("💡 This app allows you to chat with Microsoft's Phi-4 multimodal model, which can understand text, images, and audio.")
    st.stop()

# Display chat messages using default Streamlit styling
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Display text content with default styling
        st.write(message["content"])
        
        # Display images if any
        if message["role"] == "user" and "images" in message and message["images"]:
            for img in message["images"]:
                st.image(img["path"], caption=img.get("name", ""), width=300)
        
        # Display audio files if any
        if message["role"] == "user" and "audio_files" in message and message["audio_files"]:
            for audio in message["audio_files"]:
                st.audio(audio["path"])

# File upload area
st.subheader("Add Media")
tab1, tab2 = st.tabs(["Upload Files", "From URL"])

# Define a key for the session to track file uploads
if "file_upload_key" not in st.session_state:
    st.session_state.file_upload_key = 0

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Add a unique key to force re-render after sending message
        uploaded_images = st.file_uploader("Upload Images", 
                                          type=["jpg", "jpeg", "png", "gif", "webp"],
                                          accept_multiple_files=True,
                                          key=f"img_upload_{st.session_state.file_upload_key}")
    
    with col2:
        uploaded_audio = st.file_uploader("Upload Audio", 
                                         type=["mp3", "wav", "ogg", "m4a"],
                                         accept_multiple_files=True,
                                         key=f"audio_upload_{st.session_state.file_upload_key}")
    
    # Clear pending files at the beginning to avoid keeping old uploads
    st.session_state.pending_files = []
    
    # Process uploaded files for this specific message only
    if uploaded_images:
        for img in uploaded_images:
            file_info = save_uploaded_file(img)
            if file_info:
                st.session_state.pending_files.append(file_info)
                # Preview the image
                st.image(file_info["path"], caption=file_info["name"], width=150)
    
    if uploaded_audio:
        for audio in uploaded_audio:
            file_info = save_uploaded_file(audio)
            if file_info:
                st.session_state.pending_files.append(file_info)
                # Preview the audio
                st.audio(file_info["path"])

with tab2:
    url_input = st.text_input("Enter URL to image or audio", 
                           placeholder="https://example.com/image.jpg",
                           key=f"url_input_{st.session_state.file_upload_key}")
    
    if url_input and st.button("Add from URL", key=f"url_button_{st.session_state.file_upload_key}"):
        with st.spinner("Processing URL..."):
            file_data, error = download_from_url(url_input)
            if file_data:
                st.session_state.pending_files.append(file_data)
                st.success(f"Successfully added {file_data['type']} from URL")
                
                # Preview the file
                if file_data['type'] == 'image':
                    st.image(file_data['path'], caption=file_data['name'], width=300)
                else:
                    st.audio(file_data['path'])
            else:
                st.error(error)

# User input area
user_input = st.chat_input("Type your message here...", disabled=st.session_state.is_sending)

# Handle user input
if user_input:
    st.session_state.is_sending = True
    
    # Process the user input for this specific message
    images = [f for f in st.session_state.pending_files if f['type'] == 'image']
    audio_files = [f for f in st.session_state.pending_files if f['type'] == 'audio']
    
    # Create user message
    user_message = {
        "role": "user",
        "content": user_input
    }
    
    # Add media if available
    if images:
        user_message["images"] = images
    if audio_files:
        user_message["audio_files"] = audio_files
    
    # Add message to history
    st.session_state.messages.append(user_message)
    
    # Show user message immediately
    with st.chat_message("user"):
        st.write(user_input)
        
        if "images" in user_message:
            for img in user_message["images"]:
                st.image(img["path"], caption=img.get("name", ""), width=300)
        
        if "audio_files" in user_message:
            for audio in user_message["audio_files"]:
                st.audio(audio["path"])
    
    # Show thinking indicator
    with st.chat_message("assistant"):
        with st.empty():
            st.write("Thinking...")
            
            # Get AI response
            assistant_response = process_with_api(st.session_state.messages)
            
            # Add to message history
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Update with actual response
            st.write(assistant_response)
    
    # IMPORTANT: Clear pending files after message is sent
    st.session_state.pending_files = []
    
    # Update file upload key to force re-render of file uploaders
    st.session_state.file_upload_key += 1
    
    # Reset sending state
    st.session_state.is_sending = False
    
    # Rerun to refresh UI
    st.rerun()

# Footer
st.markdown("---")
st.markdown("Powered by Microsoft Phi-4 Multimodal Model")
