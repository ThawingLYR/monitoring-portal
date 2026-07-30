from streamlit import iframe


def embed_folium_map(m, height=700):
    # Render HTML from folium map in memory
    html = m.get_root().render()

    try:
        # Try to embed using srcdoc
        iframe(srcdoc=html, height=height)
    except TypeError:
        # Fallback: create a base64 data URL and pass it as src
        # b64 = b64encode(html.encode("utf-8")).decode("utf-8")
        # data_url = f"data:text/html;base64,{b64}"
        # iframe(data_url, height=height)
        iframe(html, height=height)
