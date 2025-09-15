import streamlit as st
import wikipedia

st.set_page_config(page_title="Movie Plot Finder", layout="centered")
st.title("🎬 Movie Plot Finder")
st.write("Type a movie name and get its plot/summary from Wikipedia.")

# Sidebar options
with st.sidebar:
    st.header("Options")
    sentences = st.slider("Summary length (sentences)", 1, 6, 3)
    show_all_hits = st.checkbox("Show top Wikipedia matches", value=True)

# User input
query = st.text_input("Enter a movie name (e.g. Inception, Avatar (2009 film))")

def search_wikipedia(q):
    try:
        return wikipedia.search(q, results=10)
    except Exception:
        return []

def get_summary(title, sentences=3):
    try:
        return wikipedia.summary(title, sentences=sentences)
    except wikipedia.DisambiguationError as e:
        raise
    except wikipedia.PageError:
        return None
    except Exception:
        return None

if st.button("Get Plot"):
    q = (query or "").strip()
    if not q:
        st.warning("Please enter a movie name.")
        st.stop()

    st.info(f"Searching Wikipedia for: {q}")
    hits = search_wikipedia(q)

    if not hits:
        st.error(f"No results for \"{q}\". Try adding the year (e.g. 'Avatar (2009 film)').")
        st.stop()

    # Pick best match
    chosen = None
    for h in hits:
        if h.lower() == q.lower():
            chosen = h
            break
    if not chosen:
        for h in hits:
            if "film" in h.lower() or any(str(y) in h for y in range(1900, 2031)):
                chosen = h
                break
    if not chosen:
        chosen = hits[0]

    st.success(f"Using Wikipedia page: **{chosen}**")

    if show_all_hits:
        with st.expander("Other possible matches"):
            for i, h in enumerate(hits, 1):
                st.write(f"{i}. {h}")

    try:
        summary = get_summary(chosen, sentences=sentences)
    except wikipedia.DisambiguationError as de:
        st.warning(f"'{q}' is ambiguous. Possible matches:")
        with st.expander("Disambiguation options", expanded=True):
            for i, opt in enumerate(de.options[:20], 1):
                st.write(f"{i}. {opt}")
        st.stop()

    if not summary:
        st.error(f"Could not fetch a summary for {chosen}. Try another match.")
        st.stop()

    st.markdown("### Plot / Summary")
    st.write(summary)

    url = "https://en.wikipedia.org/wiki/" + chosen.replace(" ", "_")
    st.markdown(f"[Read full Wikipedia page →]({url})")
