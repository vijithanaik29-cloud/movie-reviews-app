# movie_plot_app.py
"""
ATS score analysis — Movie Plot Finder (Streamlit)
This version uses `wikipediaapi` to fetch structured sections (Plot, Synopsis),
and falls back to the wikipedia.summary when necessary.
"""

import re
import streamlit as st
import wikipedia
import wikipediaapi

# App meta
st.set_page_config(page_title=" Movie Plot Finder", layout="centered")
st.title("🎬  Movie Plot Finder")
st.write("Type a movie name and get its plot/summary from Wikipedia. (No extra inputs required.)")

# Sidebar options
with st.sidebar:
    st.header("Options")
    sentences = st.slider("Short summary length (sentences)", 1, 6, 3)
    show_matches = st.checkbox("Show top Wikipedia matches (choose if ambiguous)", value=True)
    prefer_full_plot = st.checkbox("Prefer full 'Plot' section when available", value=True)
    lang = st.selectbox("Wikipedia language", ["en"], index=0)

# set wikipedia language
wikipedia.set_lang(lang)
wiki_api = wikipediaapi.Wikipedia(language=lang)

def clean_query(q: str) -> str:
    if not q:
        return ""
    q = q.strip()
    q = re.sub(r"[.,;:!?]+$", "", q)
    return q

@st.cache_data(show_spinner=False)
def search_wikipedia(q: str, results: int = 10):
    try:
        return wikipedia.search(q, results=results)
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

@st.cache_data(show_spinner=False)
def get_wikipedia_page_via_api(title: str):
    return wiki_api.page(title)

def get_section_text_by_title(section, title):
    """Recursive search for a given section title (case-insensitive)."""
    if section.title.strip().lower() == title.strip().lower():
        return section.text
    for s in section.sections:
        res = get_section_text_by_title(s, title)
        if res:
            return res
    return None

def extract_plot_from_api_page(page):
    """Try common section names in order."""
    if not page or not page.exists():
        return None
    for candidate in ["Plot", "Plot summary", "Synopsis", "Synopsis and plot", "Plot and synopsis"]:
        t = get_section_text_by_title(page, candidate)
        if t and len(t.strip()) > 80:
            return t.strip()
    # If no suitable section found, fallback to first paragraphs of the page text
    txt = page.text or ""
    paragraphs = [p.strip() for p in txt.split("\n\n") if p.strip()]
    return paragraphs[0].strip() if paragraphs else None

def try_summary_or_fallback(title: str, sentences: int = 3, prefer_plot: bool = True):
    """Try to return (text, url). Uses structured Plot via wikipediaapi first if prefer_plot."""
    try:
        # If prefer_plot is True, attempt to fetch structured plot first
        if prefer_plot:
            api_page = get_wikipedia_page_via_api(title)
            if api_page.exists():
                plot_text = extract_plot_from_api_page(api_page)
                if plot_text and len(plot_text) > 120:
                    return plot_text, api_page.fullurl
        # Next try wikipedia.summary (short)
        s = wikipedia.summary(title, sentences=sentences, auto_suggest=False)
        # Also try to get page url
        try:
            page_obj = wikipedia.page(title, auto_suggest=False)
            return s, page_obj.url
        except Exception:
            # fallback: if we have an api_page, return its url
            api_page = get_wikipedia_page_via_api(title)
            return s, (api_page.fullurl if api_page and api_page.exists() else None)
    except wikipedia.DisambiguationError as de:
        # propagate so UI can handle options
        raise
    except Exception:
        # last-resort: fetch api page and extract something
        try:
            api_page = get_wikipedia_page_via_api(title)
            if api_page.exists():
                plot_text = extract_plot_from_api_page(api_page)
                return plot_text, api_page.fullurl
        except Exception:
            pass
    return None, None

# --- UI ---
query = st.text_input("Enter a movie name (e.g. Inception, Avatar (2009 film))")

# Debug / Cache clear helper (optional)
if st.sidebar.button("Clear cache & rerun (debug)"):
    try:
        st.cache_data.clear()
    except Exception:
        pass
    st.experimental_rerun()

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

    exact = next((h for h in hits if h.lower() == q.lower()), None)
    if exact:
        default_index = hits.index(exact)
    else:
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
        plot_text, page_url = try_summary_or_fallback(chosen_title, sentences=sentences, prefer_plot=prefer_full_plot)
    except wikipedia.DisambiguationError as de:
        st.warning(f"'{q}' is ambiguous. Please choose one of the options below:")
        choice = st.selectbox("Disambiguation options", options=de.options[:30])
        if st.button("Use selected option"):
            try:
                plot_text, page_url = try_summary_or_fallback(choice, sentences=sentences, prefer_plot=prefer_full_plot)
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

    filename = f"{chosen_title.replace(' ', '_')}_plot.txt"
    st.download_button("Download plot (txt)", data=plot_text, file_name=filename, mime="text/plain")
