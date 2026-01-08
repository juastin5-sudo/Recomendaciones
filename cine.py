import streamlit as st
import streamlit.components.v1 as components
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Juastin Stream Pro", page_icon="🎬", layout="wide")

# --- CONTROL DE ESTILOS (DEGRADADO OSCURO Y AJUSTES) ---
st.markdown("""
    <style>
        /* FONDO DEGRADADO OSCURO PROFUNDO */
        .stApp {
            background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%);
            color: white;
        }

        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        
        /* ESTILO PARA LAS TARJETAS */
        .img-clicable:hover {
            transform: scale(1.02);
            transition: 0.3s;
            cursor: pointer;
        }

        /* AJUSTE DEL BOTÓN DE FILTROS: Bajado y con estilo Netflix */
        div.stForm submit_button > button {
            margin-top: 40px !important; 
            background-color: #E50914 !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
            height: 45px;
        }

        /* PERSONALIZACIÓN DE LA BARRA LATERAL OSCURA */
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.7) !important;
        }
        
        .valoracion-container {
            margin-top: 15px;
            margin-bottom: 12px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 5px;
            color: #FFD700;
        }

        .resumen-inferior {
            font-size: 12px; 
            color: #bbbbbb; 
            line-height: 1.3; 
            margin-top: 8px;
            height: 85px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE API ---
API_KEY = "d47891b58f979b4677c9697556247e06" 
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/original"
POSTER_URL = "https://image.tmdb.org/t/p/w500"
LOGO_URL = "https://image.tmdb.org/t/p/original"

def obtener_datos(ruta, extra_params={}):
    url = f"{BASE_URL}/{ruta}"
    params = {"api_key": API_KEY, "language": "es-ES", **extra_params}
    try:
        response = requests.get(url, params=params)
        return response.json().get('results', [])
    except: return []

def obtener_detalles_extras(item_id, tipo, titulo_item):
    params = {"api_key": API_KEY, "language": "es-ES", "append_to_response": "videos,watch/providers"}
    url = f"{BASE_URL}/{tipo}/{item_id}"
    try:
        res = requests.get(url, params=params).json()
        trailer = None
        videos = res.get('videos', {}).get('results', [])
        for v in videos:
            if v['type'] in ['Trailer', 'Opening'] and v['site'] == 'YouTube':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break
        
        region = res.get('watch/providers', {}).get('results', {}).get('ES', {})
        raw_providers = region.get('flatrate', [])
        vistos = set()
        providers_unicos = []
        
        link_final = f"https://www.google.com/search?q=ver+{titulo_item.replace(' ', '+')}+online"
        links_plataformas = {
            "netflix": "https://www.netflix.com/search?q=",
            "disney": "https://www.disneyplus.com/",
            "hbo": "https://www.max.com/",
            "amazon": "https://www.primevideo.com/",
            "apple": "https://tv.apple.com/",
            "crunchyroll": "https://www.crunchyroll.com/search?q="
        }

        for p in raw_providers:
            nombre = p['provider_name'].lower()
            nombre_base = nombre.split(' ')[0]
            if nombre_base not in vistos:
                providers_unicos.append(p)
                vistos.add(nombre_base)
                for clave, url_base in links_plataformas.items():
                    if clave in nombre:
                        link_final = url_base + (titulo_item.replace(' ', '%20') if clave in ["netflix", "crunchyroll"] else "")
        
        return trailer, providers_unicos, link_final
    except: return None, [], None

# --- 2. CARRUSEL DE ESTRENOS (GRANDE) ---
estrenos_raw = obtener_datos("trending/all/day")[:5]

if estrenos_raw:
    slides_html = ""
    for i, item in enumerate(estrenos_raw):
        titulo_slide = (item.get('title') or item.get('name')).replace("'", "")
        _, _, url_estreno = obtener_detalles_extras(item['id'], item.get('media_type', 'movie'), titulo_slide)
        fondo = f"{IMAGE_URL}{item.get('backdrop_path')}"
        sinopsis_slide = (item.get('overview')[:300] + "...").replace("'", "")
        
        slides_html += f"""
        <div class="mySlides fade">
            <a href="{url_estreno}" target="_blank" style="text-decoration: none;">
                <div class="hero-container" style="background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)), url('{fondo}');">
                    <div class="hero-content">
                        <span class="badge">ESTRENO TOP #{i+1}</span>
                        <h1 style="font-family: sans-serif; font-size: 50px; margin: 15px 0; color: white;">{titulo_slide}</h1>
                        <p style="font-family: sans-serif; font-size: 18px; color: white; max-width: 700px;">{sinopsis_slide}</p>
                    </div>
                </div>
            </a>
        </div>
        """
    carousel_code = f"""<style>.hero-container {{ height: 450px; background-size: cover; background-position: center; border-radius: 20px; display: flex; align-items: center; padding: 50px; color: white; margin: 0; }}.badge {{ background: #E50914; padding: 5px 12px; border-radius: 4px; font-weight: bold; font-family: sans-serif; font-size: 14px; }}.fade {{ animation: fade 1.5s; }}@keyframes fade {{ from {{opacity: .4}} to {{opacity: 1}} }}.mySlides {{display: none;}}</style><div class="slideshow-container">{slides_html}</div><script>var slideIndex = 0;function showSlides() {{var slides = document.getElementsByClassName("mySlides");for (var i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }}slideIndex++;if (slideIndex > slides.length) {{slideIndex = 1}}if (slides[slideIndex-1]) {{ slides[slideIndex-1].style.display = "block"; }}setTimeout(showSlides, 5000);}}showSlides();</script>"""
    components.html(carousel_code, height=470)

# --- 3. BARRA LATERAL CON FORMULARIO ---
with st.sidebar.form("formulario_filtros"):
    st.write("### ⚙️ FILTROS ⚙️ ")
    tipo_contenido = st.radio("#### 📺 Ver:", ["Películas", "Series"])
    tipo_api = "movie" if tipo_contenido == "Películas" else "tv"

    st.markdown("---")
    st.write("#### 🍳 Menú")
    dict_menu = {"☕ Desayuno": "28,12", "🍲 Almuerzo": "99,18", "🍰 Merienda": "35,10751", "🌙 Cena": "53,80"}
    menu_sel = [dict_menu[m] for m in dict_menu if st.checkbox(m)]

    st.markdown("---")
    st.write("#### 🎭 Humor")
    dict_humor = {"😂 Reír": "35", "😱 Tensión": "53,27", "🎭 Drama": "18", "🚀 Futuro": "878"}
    humor_sel = [dict_humor[h] for h in dict_humor if st.checkbox(h)]

    st.markdown("---")
    st.write("#### 📺 Tus Plataformas")
    dict_plataformas = {"Netflix": 8, "Disney+": 337, "HBO Max": 1899, "Amazon Prime": 119, "Crunchyroll": 283}
    plataformas_sel = [dict_plataformas[p] for p in dict_plataformas if st.checkbox(p)]

    st.markdown("---")
    min_rating = st.slider("Valoración ⭐ mínima", 0, 10, 6)

    # Botón con margen superior para no chocar
    enviar = st.form_submit_button("🔍 APLICAR FILTROS", use_container_width=True)

# --- 4. CUERPO PRINCIPAL ---
st.write("")
busqueda = st.text_input("", placeholder="Busca tu película o serie favorita aquí...")

todos_generos = ",".join(menu_sel + humor_sel)
params = {"sort_by": "popularity.desc", "vote_average.gte": min_rating, "with_genres": todos_generos}
if plataformas_sel:
    params["with_watch_providers"] = "|".join(map(str, plataformas_sel))
    params["watch_region"] = "ES"

if busqueda:
    resultados = obtener_datos(f"search/{tipo_api}", {"query": busqueda})
else:
    resultados = obtener_datos(f"discover/{tipo_api}", params)

if resultados:
    st.markdown("---")
    cols = st.columns(4)
    for i, item in enumerate(resultados[:12]):
        with cols[i % 4]:
            titulo = item.get('title') if tipo_api == "movie" else item.get('name')
            trailer, donde_ver, url_final = obtener_detalles_extras(item['id'], tipo_api, titulo)
            
            if item.get('poster_path'):
                st.markdown(f'<a href="{url_final}" target="_blank"><img src="{POSTER_URL}{item["poster_path"]}" class="img-clicable" style="width:100%; border-radius:10px; margin-bottom:10px;"></a>', unsafe_allow_html=True)
            
            with st.container(height=250, border=False):
                st.markdown(f"**{titulo}**")
                if trailer:
                    with st.expander("🎬 TRÁILER"): st.video(trailer)
                if donde_ver:
                    st.caption("Ver en:")
                    html_logos = '<div style="display: flex; gap: 8px; margin-bottom: 10px;">'
                    for prov in donde_ver[:4]:
                        html_logos += f'<a href="{url_final}" target="_blank"><img src="{LOGO_URL}{prov["logo_path"]}" width="28" style="border-radius:5px;" class="img-clicable"></a>'
                    html_logos += '</div>'
                    st.markdown(html_logos, unsafe_allow_html=True)
                
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)