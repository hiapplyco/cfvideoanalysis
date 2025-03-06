import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file
from elevenlabs.client import ElevenLabs

import time
import os
import tempfile
from pathlib import Path
import base64

# Set page configuration
st.set_page_config(
    page_title="Exercise Form Analyzer - Get Workout Feedback",
    page_icon="💪",
    layout="wide"
)

# ------------------------------
# Utility Functions for Background
# ------------------------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white; /* Set default text color to white for better contrast */
    }}
    .analysis-section {{
        background-color: rgba(249, 249, 249, 0.85); /* Slightly transparent white for analysis section */
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #e67e22; /* Accent color */
        margin-top: 20px;
        color: black; /* Set text color in analysis section to black */
    }}
    .stButton button {
        background-color: #e67e22; /*  button color */
        color: white;
    }
    .stDownloadButton button {
        background-color: #4CAF50; /* Example: Green for download */
        color: white;
    }

    /* Centralize elements for cleaner look on larger screens */
    .stFileUploader, .stTextArea, .stButton, .stDownloadButton, .stAudio, .stVideo {
        max-width: 800px; /* Adjust as needed */
        margin-left: auto;
        margin-right: auto;
    }
    h1, h2, h3, h4, h5, h6 {{
        color: white; /* Ensure headers are white for contrast */
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Set background image if available
background_image = "image_fx_ (19).jpg"
if os.path.exists(background_image):
    set_background(background_image)

# ------------------------------
# Retrieve API keys from secrets
# ------------------------------
API_KEY_GOOGLE = st.secrets["google"]["api_key"]
API_KEY_ELEVENLABS = st.secrets.get("elevenlabs", {}).get("api_key", None)

# ------------------------------
# Configure Google Generative AI
# ------------------------------
if API_KEY_GOOGLE:
    os.environ["GOOGLE_API_KEY"] = API_KEY_GOOGLE
    genai.configure(api_key=API_KEY_GOOGLE)
else:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY in Streamlit secrets.")
    st.stop()


# ------------------------------
# Header - No image in header, background image handles visual
# ------------------------------
st.title("Exercise Form Analyzer")
st.markdown("Get expert AI feedback on your exercise technique.") # Clear subtitle as CTA

# ------------------------------
# Sidebar content - Kept, but now generic exercise themed
# ------------------------------
with st.sidebar:
    st.header("About Exercise Form Analysis", anchor=False) # anchor=False to remove streamlit warning
    st.write("""
    Improve your exercise form with AI-powered analysis. Upload a video of your workout and receive personalized feedback to enhance your technique, prevent injuries, and maximize your performance.

    Get insights on various exercises, from weightlifting to bodyweight movements!
    """)

    st.subheader("Connect with a Fitness Professional", anchor=False) # Example Contact info - adapt as needed
    st.write("""
    Consider consulting a certified personal trainer or fitness coach for personalized guidance.
    """)

# ------------------------------
# Agent initialization
# ------------------------------
@st.cache_resource
def initialize_agent():
    """Initialize and cache the Phi Agent with Gemini model."""
    return Agent(
        name="Exercise Form Analyzer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()
script_agent = initialize_agent() # Initialize a second agent for script generation

# ------------------------------
# Session state initialization
# ------------------------------
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'audio_script' not in st.session_state: # New session state for audio script
    st.session_state.audio_script = None

if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False

if 'show_audio_options' not in st.session_state:
    st.session_state.show_audio_options = False

# ------------------------------
# Main UI - Streamlined Landing and Video Analysis - generic exercise focused
# ------------------------------
st.write(" ") # Adding some whitespace

st.write("Upload a video of your exercise to get started.") # More direct instruction

video_file = st.file_uploader(
    "Upload Exercise Video", # Clearer label - generic exercise specific
    type=['mp4', 'mov', 'avi'],
    help="Upload a video of your exercise for form analysis." # Help text updated
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format="video/mp4", start_time=0)

    user_query = st.text_area(
        "What aspect of your exercise form would you like analyzed?", # More user-focused question - generic exercise specific
        placeholder="e.g., 'Analyze my squat form', 'How's my bicep curl technique?', 'Check my plank form'", # Placeholders updated
        height=80 # Reduced height for text area
    )
    analyze_button = st.button("Analyze My Form") # Stronger CTA button text - generic exercise specific

    if analyze_button:
        if not user_query:
            st.warning("Please enter a question about your form to analyze the video.") # Warning updated
        else:
            try:
                with st.spinner("Analyzing video and generating exercise form feedback..."): # Spinner text updated
                    progress_bar = st.progress(0)
                    progress_bar.progress(10, text="Uploading...")
                    processed_video = upload_file(video_path)

                    progress_bar.progress(30, text="Processing...")
                    processing_start = time.time()
                    while processed_video.state.name == "PROCESSING":
                        if time.time() - processing_start > 60:
                            st.warning("Video processing is taking longer than expected. Please be patient.")
                        time.sleep(1)
                        processed_video = get_file(processed_video.name)

                    progress_bar.progress(60, text="Analyzing Form...") # Progress text updated

                    analysis_prompt = f"""You are a highly experienced fitness coach, known for your keen eye for detail and ability to break down complex movements for various fitness disciplines. You are providing form analysis on a workout video. Analyze this video and address: {user_query}

Your analysis should be structured to provide clear, actionable feedback to help individuals improve their technique, prevent injury, and increase workout effectiveness across different exercise types (weightlifting, calisthenics, bodybuilding, functional fitness, etc.).

Focus on common exercise movement standards and biomechanics relevant to the exercise shown in the video.

Structure your feedback rigorously, as follows:

## SKILL LEVEL & MOVEMENT EFFICIENCY
Assess the athlete's overall movement proficiency - from beginner to advanced. Comment on their efficiency of movement, fluidity, and understanding of basic exercise mechanics. *Example: "Intermediate: Shows understanding of basic movement patterns but some energy leaks are present, especially in core stabilization."*

## KEY STRENGTHS (Highlight 2-3 Areas of Good Form)
*   Identify elements performed with good technique and efficiency. Include timestamps for easy video review.
*   Explain *why* these elements are strong and contribute to good exercise performance and safety.

## AREAS FOR IMPROVEMENT (Prioritize 2-3 Key Corrections)
*   Pinpoint the most critical form errors that could lead to injury or reduced workout effectiveness. Provide timestamps.
*   Explain the biomechanical principles being violated and how these errors impact performance and safety.
*   Describe potential negative consequences if these form issues are not corrected during exercise.

## DRILLS & MODIFICATIONS (Recommend 1-2 Targeted Drills/Modifications)
*   Suggest specific drills or modifications to address the identified weaknesses and improve technique.
*   Explain how these drills or modifications will help the individual develop better movement patterns and reinforce correct form.

## COACHING CUE (The "Aha!" Moment)
Provide one key coaching cue or mental focus point that could immediately improve the athlete's understanding and execution of the movement. This should be a concise, memorable cue.

## TRAINING INSIGHT (Beyond Form)
Offer a brief insight into how the athlete's current form might impact their training progress and overall fitness goals.  *Example: "Improving squat depth will lead to better glute and quad activation for lower body strength gains."*

Deliver your analysis with the expertise of a seasoned fitness coach, providing clear, encouraging, and actionable advice. Use precise exercise terminology, but ensure it's understandable for individuals of all fitness levels. Be direct and honest, but always motivating. Keep your analysis concise and impactful – under 400 words.
"""
                    progress_bar.progress(80, text="Generating Form Insights...") # Progress text updated
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video], user_query=user_query)
                    progress_bar.progress(100, text="Complete!")
                    time.sleep(0.5)
                    progress_bar.empty()

                    st.session_state.analysis_result = response.content
                    st.session_state.audio_generated = False
                    st.session_state.show_audio_options = False
                    st.session_state.audio_script = None # Reset audio script when new analysis is generated

            except Exception as error:
                st.error(f"Analysis error: {error}") # Error message kept general
                st.info("Try uploading a shorter video or check your internet connection.") # Info message kept general
            finally:
                Path(video_path).unlink(missing_ok=True)

    # Analysis Section - Displayed regardless of audio options
    if st.session_state.analysis_result:
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.subheader("Exercise Form Analysis") # Subheader updated
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Analysis", # Clearer label
            data=st.session_state.analysis_result,
            file_name="exercise_form_analysis.md", # Filename updated
            mime="text/markdown"
        )

        # Audio Options Section - Now consistently below analysis
        if st.button("Listen to Analysis (Audio Options)"): # More informative button
            st.session_state.show_audio_options = True

        if st.session_state.show_audio_options:
            with st.expander("Audio Voice Settings", expanded=True): # Clearer expander title
                st.subheader("Voice Options")

                elevenlabs_api_key = API_KEY_ELEVENLABS
                selected_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
                if elevenlabs_api_key:
                    try:
                        client = ElevenLabs(api_key=elevenlabs_api_key)
                        voice_data = client.voices.get_all()
                        voices_list = [v.name for v in voice_data.voices]
                        selected_voice_name = st.selectbox("Choose Voice", options=voices_list, index=0)
                        selected_voice_id = next((v.voice_id for v in voice_data.voices if v.name == selected_voice_name), None)
                        if not selected_voice_id:
                            st.warning("Voice selection issue. Using default voice.")
                            selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                    except Exception as e:
                        st.warning(f"Could not retrieve voices: {e}. Using default voice.") # Include error in warning
                        selected_voice_id = "21m00Tcm4TlvDq8ikWAM"
                else:
                    st.error("ElevenLabs API key missing.")

                if st.button("Generate Audio Analysis"): # Clear CTA for audio generation
                    if elevenlabs_api_key:
                        try:
                            with st.spinner("Preparing audio script..."): # New spinner for script generation
                                script_prompt = f"""
                                Convert the following exercise form analysis into a natural, enthusiastic, and encouraging monologue script as if spoken by a seasoned fitness coach.

                                Remove all headings, bullet points, timestamps or any special characters.  The script should be plain text and flow naturally when read aloud.  Imagine you are a fitness coach, speaking directly to your client, providing form feedback and motivation.

                                Maintain all the technical insights and recommendations from the analysis, but phrase them in a conversational, easy-to-listen manner. Inject energy, enthusiasm, and a positive coaching tone typical of fitness instruction.

                                **Analysis to convert:**
                                ```
                                {st.session_state.analysis_result}
                                ```
                                """
                                script_response = script_agent.run(script_prompt) # Use script_agent
                                st.session_state.audio_script = script_response.content # Store the script

                            with st.spinner("Generating audio..."):
                                clean_text = st.session_state.audio_script # Use audio_script for TTS
                                client = ElevenLabs(api_key=elevenlabs_api_key)
                                # **Modified Audio Generation Code:**
                                audio_generator = client.text_to_speech.convert(
                                    text=clean_text,
                                    voice_id=selected_voice_id,
                                    model_id="eleven_multilingual_v2"
                                )
                                audio_bytes = b"" # Initialize empty bytes
                                for chunk in audio_generator:
                                    audio_bytes += chunk # Accumulate audio chunks
                                st.session_state.audio = audio_bytes # Store audio bytes in session state
                                st.session_state.audio_generated = True

                                st.audio(st.session_state.audio, format="audio/mp3") # Play audio from bytes
                                st.download_button(
                                    label="Download Audio Analysis", # Clearer label
                                    data=st.session_state.audio, # Download audio from bytes
                                    file_name="exercise_form_analysis_audio.mp3", # Filename updated
                                    mime="audio/mp3"
                                )
                        except Exception as e:
                            st.error(f"Audio generation error: {str(e)}") # Error message kept general
                    else:
                        st.error("ElevenLabs API key needed for audio.")

else:
    st.write("""
    Welcome to the Exercise Form Analyzer! Upload a video of your workout to get started.
    """) # Welcome message updated
    st.info("🏋️ Upload an exercise video above to receive expert AI form analysis and personalized feedback.") # Info message as CTA - generic exercise specific
    st.subheader("Tips for Best Form Analysis") # Tips section - updated
    with st.expander("How to Get the Best Exercise Form Analysis"): # Expander label updated
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of your full body during the movement.
        2. **Movement Focus**: Focus the video on a single exercise or movement pattern for targeted feedback.
        3. **Specific Questions**: Ask targeted questions about specific aspects of your form (e.g., squat depth, elbow position, etc.).
        4. **Full Reps**: Include a few full repetitions of the movement in your video for comprehensive analysis.
        """)

    st.subheader("Explore Different Exercise Types") # Section header - updated
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Weightlifting") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Analyze your form on lifts like squats, deadlifts, bench press, and overhead press.
        """)
    with col2:
        st.markdown("### Bodyweight Training") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Get feedback on exercises like push-ups, pull-ups, lunges, planks, and more.
        """)
    with col3:
        st.markdown("### Functional Fitness") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Analyze compound movements and exercises designed to improve everyday functional strength and movement.
        """)

    st.markdown("---") # Divider for visual separation

    st.write("**Good form is key to safe and effective workouts.**") # Motivational quote - generic exercise themed
