import streamlit as slt
import pandas as pd
import pickle
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import time

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Create a session with retry
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))


def fetch_poster(movie_id):
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=ac80edcd0c242ab5983f77702dc9049a&language=en-US'
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    except requests.exceptions.RequestException as e:
        slt.warning(f"Couldn't fetch poster for movie ID {movie_id}: {str(e)}")
        return None  # or return a default poster URL


def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distance = similarity[movie_index]
        movies_list = sorted(list(enumerate(distance)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        recommended_movies_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movies.append(movies.iloc[i[0]].title)

            # Fetch poster with error handling
            poster = fetch_poster(movie_id)
            if poster:  # Only add if we got a poster
                recommended_movies_posters.append(poster)
            else:
                # Add a placeholder or skip this movie
                recommended_movies_posters.append("https://via.placeholder.com/500x750?text=Poster+Not+Available")

            # Be gentle with the API - add a small delay
            time.sleep(0.1)

        return recommended_movies, recommended_movies_posters
    except Exception as e:
        slt.error(f"Recommendation failed: {str(e)}")
        return [], []


# Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

slt.title('Movie Recommendation System')

selected_movie_name = slt.selectbox(
    "Select a movie to get recommendations:",
    movies['title'].values)

if slt.button("Recommend"):
    names, posters = recommend(selected_movie_name)

    if not names:
        slt.warning("Couldn't generate recommendations. Please try again.")
    else:
        cols = slt.columns(5)
        for i, (col, name, poster) in enumerate(zip(cols, names, posters)):
            with col:
                slt.text(name)
                slt.image(poster)