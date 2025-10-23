🍹 Cocktail Explorer

A small Streamlit app that finds cocktail recipes using **TheCocktailDB** API.  
Search by **name** or **ingredient**, view full recipe details (ingredients, measures, instructions), save favorites locally, and jump to YouTube how-to videos.

## Features

- Search cocktails by **Name** or **Ingredient**
- Ingredient searches fetch multiple full recipes (uses `filter.php` → `lookup.php`)
- View recipe image, ingredients & measures, and instructions
- Save favorites locally (saved to `favorites.json`)
- Shopping list helper: paste what you have and see missing ingredients
- "I'm feeling curious" random cocktail button
- YouTube search link for each recipe (no API key required)


## Tech stack

- Python 3.8+
- Streamlit (UI)
- requests (HTTP)
- TheCocktailDB API (free public endpoints)

1. Activate your virtual environment:
   
    source .venv/bin/activate
   
2. Install dependencies:
   
   pip install -r requirements.txt

3. Run the app:

    streamlit run app.py