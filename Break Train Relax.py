import streamlit as st # type: ignore
import pandas as pd # type: ignore
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore
from datetime import datetime, timedelta
import random
import json
import os
from pathlib import Path
import uuid
import hashlib
import time
import requests 

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'mood_data' not in st.session_state:
    st.session_state.mood_data = []
if 'meditation_completed' not in st.session_state:
    st.session_state.meditation_completed = set()

# Set page config
st.set_page_config(
    page_title="Breath Track Heal",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        background-color: #7e57c2;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #673ab7;
    }
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    .mood-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

class UserManager:
    def __init__(self):  # Correct initialization method
        self.users_file = Path("users.json")
        self.load_users()

    def load_users(self):
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
            self.save_users()

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f)

    def register_user(self, username, password, display_name, anonymous=True):
        if username in self.users:
            return False, "Username already exists"
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user_id = str(uuid.uuid4())
        
        self.users[username] = {
            'id': user_id,
            'password': hashed_password,
            'display_name': display_name,
            'anonymous': anonymous,
            'mood_data': [],
            'meditation_minutes': 0,
            'joined_date': datetime.now().strftime('%Y-%m-%d')
        }
        self.save_users()
        return True, "Registration successful"

    def authenticate(self, username, password):
        if username not in self.users:
            return False
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Debugging: Verify password hash match
        if self.users[username]['password'] != hashed_password:
            print("Password mismatch!")  # Check server logs
        return self.users[username]['password'] == hashed_password


class MoodTracker:
    @staticmethod
    def add_mood_entry(username, mood, notes):
        user_manager.users[username]['mood_data'].append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mood': mood,
            'notes': notes
        })
        user_manager.save_users()

    @staticmethod
    def get_mood_history(username):
        return user_manager.users[username]['mood_data']

class MeditationGuide:
    exercises = {
        'Breathing Exercise': {
            'duration': 5,
            'description': 'Focus on your breath. Inhale for 4 counts, hold for 4, exhale for 4.',
            'steps': [
                'Find a comfortable position',
                'Close your eyes',
                'Breathe in through your nose for 4 counts',
                'Hold your breath for 4 counts',
                'Exhale through your mouth for 4 counts',
                'Repeat the cycle'
            ]
        },
        'Body Scan': {
            'duration': 10,
            'description': 'Progressively focus attention on different parts of your body.',
            'steps': [
                'Lie down comfortably',
                'Close your eyes',
                'Focus on your toes',
                'Gradually move attention upward',
                'Notice any tensions',
                'Release tension with each exhale'
            ]
        },
        'Loving-Kindness': {
            'duration': 7,
            'description': 'Direct positive thoughts and wishes to yourself and others.',
            'steps': [
                'Sit comfortably',
                'Think of yourself with kindness',
                'Extend wishes of peace and happiness',
                'Think of loved ones',
                'Extend wishes to them',
                'Gradually extend to all beings'
            ]
        }
    }

class CommunitySupport:
    @staticmethod
    def get_community_posts():
        posts = []
        for username, user_data in user_manager.users.items():
            if 'posts' in user_data:
                for post in user_data['posts']:
                    display_name = user_data['display_name'] if not user_data['anonymous'] else 'Anonymous'
                    posts.append({
                        'author': display_name,
                        'content': post['content'],
                        'date': post['date']
                    })
        return sorted(posts, key=lambda x: x['date'], reverse=True)

    @staticmethod
    def add_post(username, content):
        if 'posts' not in user_manager.users[username]:
            user_manager.users[username]['posts'] = []
        
        user_manager.users[username]['posts'].append({
            'content': content,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        user_manager.save_users()

def login_page():
    st.title("🌸 Welcome to Breath Track Heal")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if user_manager.authenticate(username, password):
                st.session_state.user = username
                st.success("Login successful!")
                st.rerun()  # Updated function to rerun the app
            else:
                st.error("Invalid username or password")
    
    with tab2:
        new_username = st.text_input("Choose Username", key="reg_username")
        new_password = st.text_input("Choose Password", type="password", key="reg_password")
        display_name = st.text_input("Display Name")
        anonymous = st.checkbox("Stay Anonymous", value=True)
        
        if st.button("Register"):
            success, message = user_manager.register_user(new_username, new_password, display_name, anonymous)
            if success:
                st.success(message)
            else:
                st.error(message)

def fetch_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random")
        if response.status_code == 200:
            quote_data = response.json()
            quote = quote_data[0]["q"]
            author = quote_data[0]["a"]
            return f'"{quote}" - {author}'
        else:
            return "Keep calm and carry on!"
    except Exception as e:
        return "Stay positive and happy!"

def main_app():
    st.sidebar.title("🌸 Welcome to Breath Track Heal")
    page = st.sidebar.radio("Navigate", 
        ["🏠 Home", "📊 Mood Tracker", "🧘 Meditation", "👥 Community", "🎯 Resources", "🎶 Music","📺 Entertainment"])
    
    user_data = user_manager.users[st.session_state.user]
    
    if page == "🏠 Home":
        st.title(f"Welcome, {user_data['display_name']}! 🌸")
        
        # Display a motivational quote
        st.subheader("Quote of the Day")
        st.markdown(f"> {fetch_quote()}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Meditation Minutes", user_data.get('meditation_minutes', 0))
        with col2:
            st.metric("Mood Entries", len(user_data.get('mood_data', [])))
        with col3:
            st.metric("Days Active", (datetime.now() - datetime.strptime(user_data['joined_date'], '%Y-%m-%d')).days)
        
        st.subheader("Quick Access")
        if st.button("🎯 Start Quick Meditation"):
            st.session_state.page = "meditation"
            st.rerun()
    
    elif page == "📊 Mood Tracker":
        st.title("Mood Tracker 📊")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            mood = st.select_slider(
                "How are you feeling?",
                options=["😢", "😕", "😐", "🙂", "😊"],
                value="😐"
            )
            notes = st.text_area("Any notes about your mood?")
            
            if st.button("Log Mood"):
                MoodTracker.add_mood_entry(st.session_state.user, mood, notes)
                st.success("Mood logged successfully!")
        
        with col2:
            mood_history = MoodTracker.get_mood_history(st.session_state.user)
            if mood_history:
                df = pd.DataFrame(mood_history)
                df['date'] = pd.to_datetime(df['date'])
                
                fig = px.line(df, x='date', y='mood',
                            title='Your Mood Over Time',
                            labels={'mood': 'Mood', 'date': 'Date'})
                st.plotly_chart(fig)
    
    elif page == "🧘 Meditation":
        st.title("Meditation Guide 🧘")
        
        exercise = st.selectbox("Choose an exercise", list(MeditationGuide.exercises.keys()))
        exercise_data = MeditationGuide.exercises[exercise]
        
        st.write(f"Duration: {exercise_data['duration']} minutes")
        st.write(exercise_data['description'])
        
        with st.expander("View Steps"):
            for step in exercise_data['steps']:
                st.write(f"• {step}")
        
        if st.button("Start Exercise"):
            st.write("🎵 Exercise in progress...")
            progress_bar = st.progress(0)
            
            # Simulate meditation progress
            for i in range(100):
                time.sleep(0.1)  # Reduced for demo
                progress_bar.progress(i + 1)
            
            user_manager.users[st.session_state.user]['meditation_minutes'] += exercise_data['duration']
            user_manager.save_users()
            st.success(f"Completed {exercise_data['duration']} minutes of meditation!")

    elif page == "🎶 Music":
        st.title("Relaxing Music 🎶")

         # Music playlist
        st.subheader("Relaxing Music 🎶")

        # Updated Spotify playlist links
        st.markdown("""
        Relax with music on Spotify. Here are some relaxing playlists:

        - [Chill Vibes](https://open.spotify.com/playlist/37i9dQZF1DX4WYpdgoIcn6)
        - [Relax & Unwind](https://open.spotify.com/playlist/37i9dQZF1DWU0ScTcjJBdj)
        - [Calm Vibes](https://open.spotify.com/playlist/37i9dQZF1DX1s9knjP51Oa)
        """)

        
    elif page == "👥 Community":
        st.title("Community Support 👥")
    
        # New post section
        st.subheader("Share Your Thoughts")
        post_content = st.text_area("What's on your mind?")
        if st.button("Share"):
            CommunitySupport.add_post(st.session_state.user, post_content)
            st.success("Posted successfully!")
    
         # View posts
        st.subheader("Community Posts")
        posts = CommunitySupport.get_community_posts()
        for post in posts:
             with st.container():
                 st.markdown(f"""
                     <div style="background-color: black; color: white; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                    <p><strong>{post['author']}</strong> • {post['date']}</p>
                    <p>{post['content']}</p>
                     </div>
                    """, unsafe_allow_html=True)


    
    elif page == "📺 Entertainment":
        st.title("Entertainment 📺")
        
        # Add options for Shows, Books, and Music
        entertainment_option = st.radio(
            "Choose an option:",
            ["Select an option", "📚 Books", "🎬 Shows", "🎶 Music"],
            index=0  # Default to the placeholder
        )

        # Handle selection
        if entertainment_option == "📚 Books":
            st.subheader("Read Books for Free 📚")
            st.markdown("""
                Explore a variety of books and read them online for free at [Project Gutenberg](https://www.gutenberg.org/).
                
                **Some popular books:**
                - *Pride and Prejudice* by Jane Austen
                - *Moby Dick* by Herman Melville
                - *The Adventures of Sherlock Holmes* by Arthur Conan Doyle
                
                **Visit the site**: [Project Gutenberg](https://www.gutenberg.org/)
            """)
        elif entertainment_option == "🎬 Shows":
            st.subheader("Watch Shows and Movies 🎬")
            st.markdown("""
                Check out movies and TV shows on [MyFlixer](https://dantv.tv/). Here are a few suggestions:

                **Top Movies:**
                - *The Shawshank Redemption*
                - *The Dark Knight*
                - *Inception*

                **Top TV Shows:**
                - *Breaking Bad*
                - *Stranger Things*
                - *The Crown*

                **Visit the website**: [MyFlixer](https://dantv.tv/)
            """)
        elif entertainment_option == "🎶 Music":
            st.subheader("Listen to Music on Spotify 🎶")

            # Embed the Spotify logo with a link
            st.markdown("""
             Relax with music on Spotify. You can explore various relaxing tunes by clicking the link below:

             [![Listen on Spotify](data:image/png;base64,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)](https://www.spotify.com/)
            """)


    
    elif page == "🎯 Resources":
        st.title("Mental Health Resources 🎯")
        
        st.markdown("""
        ### Emergency Contacts 🚨
        - *National Crisis Line*: 988
        - *Crisis Text Line*: Text HOME to 741741
        
        ### Self-Help Resources 📚
        - [National Institute of Mental Health](https://www.nimh.nih.gov)
        - [Mental Health America](https://www.mhanational.org)
        - [Psychology Today](https://www.psychologytoday.com)
        
        ### Recommended Reading 📖
        1. "The Happiness of Pursuit" by Chris Guillebeau
        2. "The Mindful Way Through Depression" by Mark Williams
        3. "The Body Keeps the Score" by Bessel van der Kolk
        
        ### Mobile Apps 📱
        - Headspace
        - Calm
        - Insight Timer
        """)
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

    if st.sidebar.button("Logout", key="sidebar_logout"):
        st.session_state.user = None
        st.rerun()


# Initialize user manager
user_manager = UserManager()

# Main app logic
if st.session_state.user is None:
    login_page()
else:
    main_app()
    