# movie_reviews_app.py
import streamlit as st
import wikipedia
import time
from transformers import pipeline

st.set_page_config(page_title="Movie Review Generator", layout="centered")
st.title("🎬 Movie Review Generator (Synthetic IMDb-style)")
st.write("Type a movie name (try exact title like 'Inception' or 'Avatar (2009 film)').")

with st.sidebar:
    n_reviews = st.slider("Number of reviews", 1, 5, 3)
    model_choice = st.selectbox("Model", ["google/flan-t5-small", "google/flan-t5-base"], index=0)
    max_length = st.slider("Max tokens per review", 20, 120, 70)
    do_sample = st.checkbox("Use sampling (more variety)", value=True)
    top_p = st.slider("top_p (nucleus sampling)", 0.1, 1.0, 0.9)

movie_name_raw = st.text_input("Enter a movie name (e.g. Inception)")
use_custom = st.checkbox("Paste custom short plot (use if wiki fails)")
custom_plot = ""
if use_custom:
    custom_plot = st.text_area("Paste a short plot/description (3-6 sentences)")

def find_wiki_page(query):
    """Return (chosen_title, top_hits_list) or (None, []) if not found."""
    if not query or not query.strip():
        return None, []
    q = query.strip()
    hits = wikipedia.search(q)
    if not hits:
        return None, []
    return hits[0], hits[:6]

def safe_get_summary(title):
    """Try to get summary for a title; handle Disambiguation and PageError."""
    try:
        return wikipedia.summary(title, sentences=3)
    except wikipedia.DisambiguationError as e:
        # return suggestion list (handled by caller)
        raise
    except wikipedia.PageError:
        return None
    except Exception as ex:
        # other wiki errors
        return None

# ---- Main flow ----
if st.button("Generate reviews"):
    query = movie_name_raw.strip()
    if use_custom and custom_plot.strip():
        context = custom_plot.strip()
        st.info("Using your provided plot as context.")
    else:
        if not query:
            st.warning("Please enter a movie name or provide a custom plot.")
            st.stop()
        # Normalize simple typos: show suggestions if search returns hits
        chosen, hits = find_wiki_page(query)
        if not chosen:
            st.error(f"No Wikipedia pages found for \"{query}\". Try a different title or paste a short plot.")
            st.stop()
        # If first hit isn't the exact query, show options to user
        if chosen.lower() != query.lower():
            st.warning(f"Top match on Wikipedia is: **{chosen}** (you searched: {query}).")
            with st.expander("Top Wikipedia matches (click to view)"):
                for i, h in enumerate(hits, 1):
                    st.write(f"{i}. {h}")
        # Try to fetch summary, handle disambiguation
        try:
            context = safe_get_summary(chosen)
            if context is None:
                st.warning(f"Could not fetch a clean summary for {chosen}. Try another match or paste a short plot.")
                st.stop()
        except wikipedia.DisambiguationError as e:
            st.warning(f"'{query}' is ambiguous. Here are suggestions; choose one or paste a short plot.")
            with st.expander("Disambiguation options", expanded=True):
                for i, opt in enumerate(e.options[:12], 1):
                    st.write(f"{i}. {opt}")
            st.stop()

    # show context to user
    with st.expander("Context used for generation (click to view)", expanded=True):
        st.write(context)

    # load generator (cached across Streamlit session)
    @st.cache_resource
    def get_generator(model_name):
        return pipeline("text2text-generation", model=model_name, device=-1)

    st.info("Loading model (first run will download weights; may take a minute)...")
    try:
        generator = get_generator(model_choice)
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        st.stop()

    # generation prompt and loop
    prompt_template = (
        "Write a short IMDb-style user review (1-2 sentences). Tone: concise, honest and varied.\n"
        "Context: {context}\nMovie: {movie}\nReview {i} of {n}:"
    )

    reviews = []
    for i in range(1, n_reviews + 1):
        prompt = prompt_template.format(context=context, movie=movie_name_raw or "this movie", i=i, n=n_reviews)
        out = generator(prompt, max_length=max_length, do_sample=do_sample, top_p=top_p, num_return_sequences=1)
        text = out[0].get("generated_text", "").replace("\n", " ").strip()
        reviews.append(text)
        st.write(f"**Review {i}:** {text}")
        time.sleep(0.2)

    st.success("Generated reviews (synthetic). Remember: these are examples, not real IMDb reviews.")
    st.download_button("Download reviews (txt)", "\n\n".join([f"Review {i+1}: {r}" for i, r in enumerate(reviews)]),
                       file_name=f"{(movie_name_raw or 'movie').replace(' ', '_')}_reviews.txt")
