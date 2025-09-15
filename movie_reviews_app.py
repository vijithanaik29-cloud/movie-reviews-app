import streamlit as st
import wikipedia
from transformers import pipeline

st.title("Movie Review Generator")

movie_name = st.text_input("Enter a movie name:")

if movie_name:
    try:
        summary = wikipedia.summary(movie_name, sentences=3)
        st.write("### Movie Summary")
        st.write(summary)

        # Example: sentiment analysis
        classifier = pipeline("sentiment-analysis")
        review = classifier(summary)[0]
        st.write("### Sentiment")
        st.write(review)

    except Exception as e:
        st.error(f"Error: {e}")
