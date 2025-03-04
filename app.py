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
    page_title="CrossFit Form Analyzer - Get Workout Feedback",
    page_icon="🏋️",
    layout="wide"
)

# ------------------------------
# Utility Functions for Background (REMOVED)
# ------------------------------
# Background and custom CSS are being significantly simplified for clarity.

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
# Basic CSS styling - now much simpler
# ------------------------------
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .analysis-section {
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #e67e22; /* CrossFit orange accent */
        margin-top: 20px;
        background-color: #f9f9f9; /* Light background for analysis */
    }
    .stButton button {
        background-color: #e67e22; /* CrossFit orange button */
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
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# Header - Simplified - CrossFit Focused
# ------------------------------
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/CrossFit_Logo_Solid.svg/1200px-CrossFit_Logo_Solid.svg.png", width=150) # CrossFit logo
st.title("CrossFit Form Analyzer")
st.markdown("Get expert AI feedback on your CrossFit workout technique.") # Clear subtitle as CTA

# ------------------------------
# Sidebar content - Kept, but now CrossFit themed
# ------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/CrossFit_Logo_Solid.svg/1200px-CrossFit_Logo_Solid.svg.png", width=100) # Smaller sidebar logo
    st.header("About CrossFit Form Analysis", anchor=False) # anchor=False to remove streamlit warning
    st.write("""
    Improve your CrossFit workouts with AI-powered form analysis. Upload a video of your workout and receive personalized feedback to enhance your technique, prevent injuries, and maximize your performance.

    Get insights on your squats, cleans, snatches, and more!
    """)

    st.subheader("Connect with a Coach", anchor=False) # Example Contact info - adapt as needed
    st.write("""
    **Find a CrossFit Affiliate**: [CrossFit Affiliate Finder](https://map.crossfit.com/)

    **Learn more about CrossFit**: [CrossFit Official Website](https://www.crossfit.com/)
    """)

# ------------------------------
# Agent initialization
# ------------------------------
@st.cache_resource
def initialize_agent():
    """Initialize and cache the Phi Agent with Gemini model."""
    return Agent(
        name="CrossFit Form Analyzer",
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
# Main UI - Streamlined Landing and Video Analysis - CrossFit focused
# ------------------------------
st.write(" ") # Adding some whitespace
st.write("Upload a video of your CrossFit workout to get started.") # More direct instruction

video_file = st.file_uploader(
    "Upload CrossFit Workout Video", # Clearer label - CrossFit specific
    type=['mp4', 'mov', 'avi'],
    help="Upload a video of your CrossFit workout for form analysis." # Help text updated
)

if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        temp_video.write(video_file.read())
        video_path = temp_video.name

    st.video(video_path, format="video/mp4", start_time=0)

    user_query = st.text_area(
        "What aspect of your CrossFit form would you like analyzed?", # More user-focused question - CrossFit specific
        placeholder="e.g., 'Analyze my squat form', 'How's my snatch technique?', 'Check my push-up form'", # Placeholders updated
        height=80 # Reduced height for text area
    )
    analyze_button = st.button("Analyze My Form") # Stronger CTA button text - CrossFit specific

    if analyze_button:
        if not user_query:
            st.warning("Please enter a question about your form to analyze the video.") # Warning updated
        else:
            try:
                with st.spinner("Analyzing video and generating CrossFit form feedback..."): # Spinner text updated
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

                    analysis_prompt = f"""You are a highly experienced CrossFit Level 3 coach, known for your keen eye for detail and ability to break down complex movements. You are providing form analysis on a CrossFit workout video.  Analyze this video and address: {user_query}

Your analysis should be structured to provide clear, actionable feedback to help athletes improve their technique, prevent injury, and increase workout efficiency.

Focus on common CrossFit movement standards and biomechanics.

Structure your feedback rigorously, as follows:

## SKILL LEVEL & MOVEMENT EFFICIENCY
Assess the athlete's overall movement proficiency - from beginner to advanced. Comment on their efficiency of movement, fluidity, and understanding of basic CrossFit mechanics. *Example: "Intermediate: Shows understanding of basic movement patterns but some energy leaks are present, especially in transitions."*

## KEY STRENGTHS (Highlight 2-3 Areas of Good Form)
*   Identify elements performed with good technique and efficiency. Include timestamps for easy video review.
*   Explain *why* these elements are strong and contribute to good CrossFit performance and safety.

## AREAS FOR IMPROVEMENT (Prioritize 2-3 Key Corrections)
*   Pinpoint the most critical form errors that could lead to injury or reduced workout effectiveness. Provide timestamps.
*   Explain the biomechanical principles being violated and how these errors impact performance and safety.
*   Describe potential negative consequences if these form issues are not corrected in CrossFit workouts.

## DRILLS & SCALING OPTIONS (Recommend 1-2 Targeted Drills/Scaling)
*   Suggest specific drills or scaling options to address the identified weaknesses and improve technique.
*   Explain how these drills or scaling adjustments will help the athlete develop better movement patterns and reinforce correct form.

## COACHING CUE (The "Aha!" Moment)
Provide one key coaching cue or mental focus point that could immediately improve the athlete's understanding and execution of the movement. This should be a concise, memorable cue.

## WORKOUT STRATEGY INSIGHT (Beyond Form)
Offer a brief insight into how the athlete's current form might impact their workout strategy and overall WOD performance.  *Example: "Improving squat depth will allow for more efficient cycling in higher rep workouts."*

Deliver your analysis with the expertise of a seasoned CrossFit coach, providing clear, encouraging, and actionable advice. Use precise CrossFit terminology, but ensure it's understandable for athletes of all levels.  Be direct and honest, but always motivating. Keep your analysis concise and impactful – under 400 words.
"""
                    progress_bar.progress(80, text="Generating Form Insights...") # Progress text updated
                    response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
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
        st.subheader("CrossFit Form Analysis") # Subheader updated
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Analysis", # Clearer label
            data=st.session_state.analysis_result,
            file_name="crossfit_form_analysis.md", # Filename updated
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
                                Convert the following CrossFit form analysis into a natural, enthusiastic, and encouraging monologue script as if spoken by a seasoned CrossFit coach.

                                Remove all headings, bullet points, timestamps or any special characters.  The script should be plain text and flow naturally when read aloud.  Imagine you are a CrossFit Level 3 coach, speaking directly to your athlete, providing form feedback and motivation.

                                Maintain all the technical insights and recommendations from the analysis, but phrase them in a conversational, easy-to-listen manner. Inject energy, enthusiasm, and a positive coaching tone typical of CrossFit.

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
                                    file_name="crossfit_form_analysis_audio.mp3", # Filename updated
                                    mime="audio/mp3"
                                )
                        except Exception as e:
                            st.error(f"Audio generation error: {str(e)}") # Error message kept general
                    else:
                        st.error("ElevenLabs API key needed for audio.")

else:
    st.write("""
    Welcome to the CrossFit Form Analyzer! Upload a video of your workout to get started.
    """) # Welcome message updated
    st.info("🏋️ Upload a CrossFit workout video above to receive expert AI form analysis and personalized feedback.") # Info message as CTA - CrossFit specific
    st.subheader("Tips for Best Form Analysis") # Tips section - updated
    with st.expander("How to Get the Best CrossFit Form Analysis"): # Expander label updated
        st.markdown("""
        1. **Video Quality**: Ensure good lighting and a clear view of your full body during the movement.
        2. **Movement Focus**: Focus the video on a single exercise or movement pattern for targeted feedback.
        3. **Specific Questions**: Ask targeted questions about specific aspects of your form (e.g., squat depth, bar path, etc.).
        4. **Full Reps**: Include a few full repetitions of the movement in your video for comprehensive analysis.
        """)

    st.subheader("Explore CrossFit Movements") # Section header - updated
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Weightlifting") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Analyze your Olympic lifts like Cleans, Snatches, Jerks, and improve your power and technique.
        """)
    with col2:
        st.markdown("### Gymnastics") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Get feedback on bodyweight movements like Pull-ups, Push-ups, Handstand Push-ups, and more to refine your form.
        """)
    with col3:
        st.markdown("### Monostructural") # Sub-subheader for better visual hierarchy - updated
        st.write("""
        Even seemingly simple movements like Rowing, Running, and Jumping Rope can be optimized for efficiency - let's analyze them!
        """)

    st.markdown("---") # Divider for visual separation

    st.subheader("Athlete Success Stories") # Testimonials section - could be updated with CrossFit specific testimonials
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        "The CrossFit Form Analyzer helped me identify a critical flaw in my squat that I never noticed.  My coach was impressed with the AI feedback!" -  [Athlete Name], CrossFit Enthusiast
        """) # Example testimonial - needs to be updated
    with col2:
        st.info("""
        "I used to get shoulder pain during Snatches. This app pinpointed my bar path issue, and now I'm lifting pain-free! Amazing!" - [Athlete Name 2], CrossFit Competitor
        """) # Example testimonial - needs to be updated

    st.write("**Good form is the foundation of performance.**") # Motivational quote - CrossFit themed
