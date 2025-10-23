# app.py (fixed)
import streamlit as st
import requests
from urllib.parse import quote_plus
import json, os
from typing import List, Dict, Any

st.set_page_config(page_title="Cocktail Explorer", layout="wide")

BASE = "https://www.thecocktaildb.com/api/json/v1/1"

# ----------------------
# Helper functions (defined first so they exist when called)
# ----------------------
def youtube_search_link(title: str) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(f"{title} recipe")

# Favorites helpers
FAV_FILE = "favorites.json"
def load_favs():
    if os.path.exists(FAV_FILE):
        try:
            return json.load(open(FAV_FILE, "r", encoding="utf-8"))
        except Exception:
            return []
    return []

def save_favs(favs):
    json.dump(favs, open(FAV_FILE, "w", encoding="utf-8"), indent=2)

# Network helpers with caching
@st.cache_data(ttl=60*60)  # cache results for 1 hour
def fetch_json(url: str, params: dict = None) -> dict:
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"__error__": str(e)}

def search_by_name_full(name: str) -> List[Dict[str, Any]]:
    url = f"{BASE}/search.php"
    data = fetch_json(url, {"s": name})
    if "__error__" in data:
        st.error(f"API error: {data['__error__']}")
        return []
    return data.get("drinks") or []

def search_by_ingredient_ids(ingredient: str, number: int = 8) -> List[Dict[str, Any]]:
    url = f"{BASE}/filter.php"
    data = fetch_json(url, {"i": ingredient})
    if "__error__" in data:
        st.error(f"API error: {data['__error__']}")
        return []
    items = data.get("drinks") or []
    return items[:number]

@st.cache_data(ttl=60*60)
def lookup_full_by_id(drink_id: str) -> Dict[str, Any]:
    url = f"{BASE}/lookup.php"
    data = fetch_json(url, {"i": drink_id})
    if "__error__" in data:
        return {"__error__": data["__error__"]}
    drinks = data.get("drinks")
    return (drinks[0] if drinks else None) if drinks else None

def display_full_recipe_card(details: dict):
    """Render a full recipe card for a given details dict."""
    if not details:
        return
    cols = st.columns([1,3,1])
    with cols[0]:
        if details.get("strDrinkThumb"):
            st.image(details.get("strDrinkThumb"), width=120)
        else:
            st.write("🍸")
    with cols[1]:
        st.subheader(details.get("strDrink"))
        st.write(f"Category: {details.get('strCategory')} • {details.get('strAlcoholic')}")
        st.write("**Ingredients:**")
        for i in range(1, 16):
            ing = details.get(f"strIngredient{i}")
            amt = details.get(f"strMeasure{i}") or ""
            if ing:
                st.write(f"- {ing} {amt}")
        st.write("**Instructions (short):**")
        instr = details.get("strInstructions") or "No instructions"
        st.write(instr if len(instr) < 500 else instr[:500] + "...")
        # action buttons
        btn_view = st.button(f"View full ({details.get('idDrink')})", key=f"view_{details.get('idDrink')}")
        btn_fav = st.button(f"Save favorite ({details.get('idDrink')})", key=f"fav_{details.get('idDrink')}")
        if btn_view:
            st.session_state["selected"] = details
        if btn_fav:
            favs = load_favs()
            already = any(f.get("id") == details.get("idDrink") for f in favs)
            if not already:
                favs.append({"id": details.get("idDrink"), "title": details.get("strDrink")})
                save_favs(favs)
                st.success("Saved to favorites!")
            else:
                st.info("Already in favorites.")
    with cols[2]:
        st.markdown(f"[YouTube how-to]({youtube_search_link(details.get('strDrink'))})")
        if details.get("strGlass"):
            st.write(f"Glass: {details.get('strGlass')}")
        if details.get("strIBA"):
            st.write(f"IBA: {details.get('strIBA')}")

# ----------------------
# UI starts here
# ----------------------
st.title("🍹 Cocktail Explorer")
st.write("Search cocktails by name or ingredient. Ingredient searches fetch full recipes for the top results.")

# ensure session state
if "selected" not in st.session_state:
    st.session_state["selected"] = None

# sidebar controls
with st.sidebar:
    st.header("Search options")
    mode = st.radio("Search mode", ["Name", "Ingredient"])
    max_results = st.slider("Max recipes to fetch (ingredient search)", 1, 12, 8)
    allow_random = st.checkbox("Show random cocktail button", True)
    show_favs = st.checkbox("Show saved favorites", False)
    st.markdown("---")
    st.write("Tip: Ingredient search uses `filter.php` then `lookup.php` for each result.")

query = st.text_input("Enter search term (e.g., 'margarita' or 'gin')")

if st.button("Search") and query.strip():
    q = query.strip()
    with st.spinner("Searching..."):
        if mode == "Name":
            results = search_by_name_full(q)
            if not results:
                st.info("No results found for that name.")
            else:
                st.success(f"Found {len(results)} result(s).")
                for details in results:
                    display_full_recipe_card(details)
        else:  # Ingredient mode
            ids = search_by_ingredient_ids(q, number=max_results)
            if not ids:
                st.info("No cocktails found for that ingredient.")
            else:
                st.success(f"Found {len(ids)} candidate(s). Loading full recipes (this may take a moment)...")
                # progress indicator
                progress_bar = st.progress(0)
                fulls = []
                total = len(ids)
                for idx, it in enumerate(ids, start=1):
                    d_id = it.get("idDrink")
                    if not d_id:
                        progress_bar.progress(int((idx/total)*100))
                        continue
                    details = lookup_full_by_id(d_id)
                    if details and not details.get("__error__"):
                        fulls.append(details)
                    progress_bar.progress(int((idx/total)*100))
                progress_bar.empty()
                if not fulls:
                    st.warning("Could not retrieve detailed recipes (API or network issue).")
                else:
                    for details in fulls:
                        display_full_recipe_card(details)

# Random cocktail
if allow_random and st.button("I'm feeling curious — show a random cocktail"):
    with st.spinner("Fetching random cocktail..."):
        data = fetch_json(f"{BASE}/random.php")
        if data and not data.get("__error__"):
            r = data.get("drinks")[0]
            st.session_state["selected"] = r
        else:
            st.error("Random fetch failed.")

# Show favorites
if show_favs:
    favs = load_favs()
    st.markdown("### ⭐ Your favorites")
    if not favs:
        st.write("No favorites yet.")
    else:
        for f in favs:
            st.write(f"- {f.get('title')} (ID: {f.get('id')}) — [YouTube]("+youtube_search_link(f.get('title'))+")")

# Selected recipe viewer
sel = st.session_state.get("selected")
if sel:
    st.markdown("---")
    st.header(sel.get("strDrink") or sel.get("title") or "Recipe")
    left, right = st.columns([1,2])
    with left:
        if sel.get("strDrinkThumb") or sel.get("image"):
            st.image(sel.get("strDrinkThumb") or sel.get("image"), width=300)
        st.write(f"**Category:** {sel.get('strCategory')}")
        st.write(f"**Alcoholic:** {sel.get('strAlcoholic')}")
        favs = load_favs()
        already = any(f.get("id") == (sel.get("idDrink") or sel.get("id")) for f in favs)
        if st.button("Save to favorites" if not already else "Remove from favorites"):
            if not already:
                favs.append({"id": sel.get("idDrink") or sel.get("id"), "title": sel.get("strDrink") or sel.get("title")})
                save_favs(favs)
                st.success("Saved!")
            else:
                favs = [f for f in favs if f.get("id") != (sel.get("idDrink") or sel.get("id"))]
                save_favs(favs)
                st.info("Removed from favorites.")
        st.markdown("**Shopping list helper**")
        have = st.text_input("List what you have (comma separated)", value="")
        needed = []
        for i in range(1, 16):
            ing = sel.get(f"strIngredient{i}")
            if ing:
                needed.append(ing)
        have_set = set([h.strip().lower() for h in have.split(",") if h.strip()])
        missing = [n for n in needed if n.strip().lower() not in have_set]
        st.write("Missing ingredients:")
        if missing:
            for m in missing:
                st.write("- " + m)
        else:
            st.write("You're set — no missing ingredients!")

    with right:
        st.subheader("Ingredients & Measures")
        for i in range(1, 16):
            ing = sel.get(f"strIngredient{i}")
            amt = sel.get(f"strMeasure{i}") or ""
            if ing:
                st.write(f"- {ing} — {amt}")
        st.subheader("Instructions")
        instr = sel.get("strInstructions") or sel.get("instructions") or "No instructions available."
        st.write(instr)
        st.markdown(f"[Search video on YouTube]({youtube_search_link(sel.get('strDrink') or sel.get('title'))})")
