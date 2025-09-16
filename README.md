# 🎬 Movie Plot Finder

A Streamlit web app that fetches **movie plots** directly from Wikipedia.  
Users can search for any movie and instantly read its full **Plot** section or a short summary if the plot is not available.  

👉 **Live Demo:** [Try it on Streamlit Cloud](YOUR-STREAMLIT-LINK-HERE)  

---

## ✨ Features
- 🔎 **Movie Search** — enter any movie name (e.g., *The Dark Knight*, *Avatar (2009 film)*).  
- 📖 **Plot Extraction** — fetches the full *Plot* section from Wikipedia.  
- 🔄 **Smart Fallback** — if no Plot section is available, it returns a short summary.  
- ⚡ **Disambiguation Handling** — helps choose the right match when multiple results exist.  
- 📥 **Download Option** — download the plot as a `.txt` file.  
- 🌐 **Deployed** on Streamlit Cloud with pinned Python and requirements for stability.  

---

## 🛠️ Tech Stack
- **Python 3.10**  
- [Streamlit](https://streamlit.io/) — interactive UI framework  
- [wikipedia-api](https://pypi.org/project/wikipedia-api/) — extract structured content from Wikipedia  
- [wikipedia](https://pypi.org/project/wikipedia/) — summaries and search  

---

## 📂 Project Structure
