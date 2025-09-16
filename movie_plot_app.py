# movie_plot_app.py
import re
import streamlit as st
import wikipedia

st.set_page_config(page_title="Movie Plot Finder", layout="centered")
st.title("🎬 Movie Plot Finder")
st.write("Type a movie name and get its plot/summary from Wikipedia. (No extra inputs required.)")

# Sidebar options
with st.sidebar:
    st.header("Options")
    sentences = st.slider("Short summary length (sentences)", 1, 6, 3)
    show_matches = st.checkbox("Show top Wikipedia matches (choose if ambiguous)", value=True)
    show_full_plot = st.checkbox("Prefer full 'Plot' section when available", value=True)
    # language selection (optional)
    lang = st.selectbox("Wikipedia language", ["en"], index=0)

# set wikipedia language
wikipedia.set_lang(lang)

def clean_query(q: str) -> str:
    if not q:
        return ""
    q = q.strip()
    # remove trailing punctuation (comma, period, exclamation, question mark, semicolon, colon)
    q = re.sub(r"[.,;:!?]+$", "", q)
    return q

@st.cache_data(show_spinner=False)
def search_wikipedia(q: str, results: int = 10):
    try:
        return wikipedia.search(q, results=results)
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def get_wikipedia_page(title: str):
    """Return a wikipedia.page object or raise the underlying exception."""
    return wikipedia.page(title, auto_suggest=False)

def extract_plot_from_content(content: str) -> str:
    """Try to extract the 'Plot' section. If not found, return first paragraph."""
    # Search for an explicit "Plot" section (== Plot ==)
    m = re.search(r"==+\s*Plot\s*==+\s*(.*?)(\n==+|\Z)", content, flags=re.DOTALL | re.IGNORECASE)
    if m:
        plot = m.group(1).strip()
        # clean up many newlines to paragraphs
        paragraphs = [p.strip() for p in plot.split("\n\n") if p.strip()]
        return "\n\n".join(paragraphs).strip()
    # try "Synopsis" or "Plot summary"
    m2 = re.search(r"==+\s*(Synopsis|Plot summary)\s*==+\s*(.*?)(\n==+|\Z)",
                   content, flags=re.DOTALL | re.IGNORECASE)
    if m2:
        return m2.group(2).strip()
    # fallback: first non-empty paragraph
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else ""

def try_summary_or_fallback(title: str, sentences: int = 3, prefer_full_plot: bool = True):
    """Try wikipedia.summary() first. If it fails, fetch page and attempt to extract Plot."""
    try:
        s = wikipedia.summary(title, sentences=sentences)
        # If prefer_full_plot, still try to fetch plot section (better for long movie pages)
        if prefer_full_plot:
            try:
                page = get_wikipedia_page(title)
                plot_section = extract_plot_from_content(page.content)
                if plot_section and len(plot_section) > 120:  # sizable plot found
                    return plot_section, page.url
            except Exception:
                pass
        return s, wikipedia.page(title, auto_suggest=False).url
    except wikipedia.DisambiguationError as e:
        # bubble up the disambiguation options to the caller
        raise
    except Exception:
        # fallback to page content
        try:
            page = get_wikipedia_page(title)
            plot = extract_plot_from_content(page.content)
            return plot, page.url
        except Exception as e:
            # final fallback: return None and the page url if available
            try:
                page = wikipedia.page(title, auto_suggest=False)
                return None, page.url
            except Exception:
                return None, None

# --- UI ---
query = st.text_input("Enter a movie name (e.g. Inception, Avatar (2009 film))")

if st.button("Get Plot"):
    q = clean_query(query)
    if not q:
        st.warning("Please enter a movie name.")
        st.stop()

    st.info(f"Searching Wikipedia for: {q}")
    hits = search_wikipedia(q, results=10)

    if not hits:
        st.error(f"No Wikipedia results for \"{q}\". Try a different title or add the year: e.g. 'Avatar (2009 film)'.")
        st.stop()

    # pick a sensible default
    exact = next((h for h in hits if h.lower() == q.lower()), None)
    if exact:
        default_index = hits.index(exact)
    else:
        # prefer titles that contain 'film' or parentheses with a year
        default_index = 0
        for i, h in enumerate(hits):
            if "film" in h.lower() or re.search(r"\(\d{4}\)", h):
                default_index = i
                break

    chosen_title = hits[default_index]
    if show_matches and len(hits) > 1:
        chosen_title = st.selectbox("Choose the best match (top results)", options=hits, index=default_index)

    st.success(f"Using Wikipedia page: **{chosen_title}**")

    try:
        plot_text, page_url = try_summary_or_fallback(chosen_title, sentences=sentences, prefer_full_plot=show_full_plot)
    except wikipedia.DisambiguationError as de:
        st.warning(f"'{q}' is ambiguous. Please choose one of the options below:")
        choice = st.selectbox("Disambiguation options", options=de.options[:30])
        if st.button("Use selected option"):
            try:
                plot_text, page_url = try_summary_or_fallback(choice, sentences=sentences, prefer_full_plot=show_full_plot)
                chosen_title = choice
            except Exception as e:
                st.error(f"Failed to fetch page for {choice}: {e}")
                st.stop()
        else:
            st.stop()

    if not plot_text:
        st.error(f"Could not fetch a summary/plot for **{chosen_title}**. Try another match.")
        st.stop()

    st.markdown("### Plot / Summary")
    st.write(plot_text)

    if page_url:
        st.markdown(f"[Read full Wikipedia page →]({page_url})")

    # Provide a download button
    filename = f"{chosen_title.replace(' ', '_')}_plot.txt"
    st.download_button("Download plot (txt)", data=plot_text, file_name=filename, mime="text/plain")
