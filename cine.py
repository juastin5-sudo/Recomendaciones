import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Juastin Stream Pro", page_icon="🎬", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILOS CSS (Modo Cine + Corrección de espacios) ---
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%); color: white; }
        .block-container {padding-top: 1rem;}
        .img-clicable:hover { transform: scale(1.02); transition: 0.3s; cursor: pointer; }
        .hero-container { cursor: pointer; transition: 0.3s; border-radius: 20px;}
        .hero-container:hover { filter: brightness(1.1); }
        div.stForm submit_button > button { margin-top: 20px !important; background-color: #E50914 !important; color: white !important; font-weight: bold !important; border: none !important; width: 100%; }
        .valoracion-container { margin-top: 15px; margin-bottom: 15px; font-weight: bold; display: flex; align-items: center; gap: 5px; color: #FFD700; }
        .resumen-inferior { font-size: 12px; color: #bbbbbb; line-height: 1.3; margin-top: 8px; height: 85px; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE API TMDB ---
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
        url_final = f"https://www.google.com/search?q=ver+{titulo_item.replace(' ', '+')}+online"
        for p in raw_providers:
            if p['provider_name'] not in vistos:
                providers_unicos.append(p)
                vistos.add(p['provider_name'])
        return trailer, providers_unicos, url_final
    except: return None, [], None

# --- LÓGICA DE USUARIOS (BARRA LATERAL) ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

with st.sidebar:
    st.title("👤 Acceso")
    try:
        df_usuarios = conn.read(worksheet="Usuarios", ttl=0)
        lista_nombres = df_usuarios['usuario'].astype(str).str.lower().tolist()
    except:
        lista_nombres = []
        df_usuarios = pd.DataFrame(columns=['usuario'])

    if not st.session_state.usuario:
        t1, t2 = st.tabs(["Entrar", "Registrarse"])
        with t1:
            n_login = st.text_input("Tu nombre", key="l").lower().strip()
            if st.button("Iniciar Sesión"):
                if n_login in lista_nombres:
                    st.session_state.usuario = n_login
                    st.rerun()
                else: st.error("Usuario no encontrado.")
        with t2:
            n_reg = st.text_input("Nombre único", key="r").lower().strip()
            if st.button("Validar y Crear"):
                if n_reg in lista_nombres:
                    st.error("❌ Ese nombre ya está en uso.")
                elif n_reg == "":
                    st.warning("Escribe un nombre.")
                else:
                    nuevo_u = pd.DataFrame([{"usuario": n_reg}])
                    df_f = pd.concat([df_usuarios, nuevo_u], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_f)
                    st.session_state.usuario = n_reg
                    st.success("¡Registrado!")
                    st.rerun()
    else:
        st.write(f"Hola, **{st.session_state.usuario.capitalize()}**")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    # --- FILTROS (Solo visibles si está logueado) ---
    if st.session_state.usuario:
        st.markdown("---")
        with st.form("filtros"):
            st.write("### ⚙️ Filtros")
            tipo_api = st.radio("Ver:", ["Películas", "Series"])
            tipo_api = "movie" if tipo_api == "Películas" else "tv"
            
            st.write("#### 🍳 Menú")
            dict_menu = {"☕ Desayuno": "28,12", "🍲 Almuerzo": "99,18", "🍰 Merienda": "35,10751", "🌙 Cena": "53,80"}
            menu_sel = [dict_menu[m] for m in dict_menu if st.checkbox(m)]
            
            st.write("#### 🎭 Humor")
            dict_humor = {"😂 Reír": "35", "😱 Tensión": "53,27", "🎭 Drama": "18", "🚀 Futuro": "878"}
            humor_sel = [dict_humor[h] for h in dict_humor if st.checkbox(h)]

            st.write("#### 📺 Plataformas")
            dict_p = {"Netflix": 8, "Disney+": 337, "HBO Max": 1899, "Amazon": 119, "Crunchyroll": 283}
            p_sel = [dict_p[p] for p in dict_p if st.checkbox(p)]

            min_rating = st.slider("Valoración ⭐", 0, 10, 6)
            aplicar = st.form_submit_button("🔍 APLICAR FILTROS")

# --- CONTENIDO PRINCIPAL (Solo si está logueado) ---
if st.session_state.usuario:
    # 1. Carrusel de Estrenos
    estrenos = obtener_datos("trending/all/day")[:5]
    if estrenos:
        slides_html = ""
        for i, item in enumerate(estrenos):
            tit = (item.get('title') or item.get('name')).replace("'", "")
            _, _, url_e = obtener_detalles_extras(item['id'], item.get('media_type', 'movie'), tit)
            slides_html += f"""
            <div class="mySlides fade">
                <a href="{url_e}" target="_blank" style="text-decoration: none;">
                    <div class="hero-container" style="background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)), url('{IMAGE_URL}{item.get('backdrop_path')}'); height: 400px; background-size: cover; background-position: center; display: flex; align-items: center; padding: 40px; color: white;">
                        <div>
                            <span style="background: #E50914; padding: 5px 10px; border-radius: 4px; font-weight: bold;">TOP #{i+1}</span>
                            <h1 style="font-size: 40px; margin: 10px 0;">{tit}</h1>
                            <p style="max-width: 600px;">{item.get('overview', '')[:200]}...</p>
                        </div>
                    </div>
                </a>
            </div>"""
        carousel_js = f"""<div class="slideshow-container">{slides_html}</div><script>var slideIndex = 0; function showSlides() {{ var slides = document.getElementsByClassName("mySlides"); for (var i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }} slideIndex++; if (slideIndex > slides.length) {{slideIndex = 1}} slides[slideIndex-1].style.display = "block"; setTimeout(showSlides, 4000); }} showSlides();</script>"""
        components.html(carousel_js, height=420)

    # 2. Buscador
    busqueda = st.text_input("", placeholder="Busca tu película o serie favorita...")

    # 3. Lógica de resultados
    todos_gen = ",".join(menu_sel + humor_sel)
    params = {"sort_by": "popularity.desc", "vote_average.gte": min_rating, "with_genres": todos_gen}
    if p_sel: params["with_watch_providers"] = "|".join(map(str, p_sel)); params["watch_region"] = "ES"

    res = obtener_datos(f"search/{tipo_api}", {"query": busqueda}) if busqueda else obtener_datos(f"discover/{tipo_api}", params)

    if res:
        st.markdown("---")
        cols = st.columns(4)
        for i, item in enumerate(res[:12]):
            with cols[i % 4]:
                t_item = item.get('title') or item.get('name')
                tra, provs, url_f = obtener_detalles_extras(item['id'], tipo_api, t_item)
                if item.get('poster_path'):
                    st.markdown(f'<a href="{url_f}" target="_blank"><img src="{POSTER_URL}{item["poster_path"]}" class="img-clicable" style="width:100%; border-radius:10px;"></a>', unsafe_allow_html=True)
                with st.container(height=260, border=False):
                    st.markdown(f"**{t_item}**")
                    if tra:
                        with st.expander("🎬 TRÁILER"): st.video(tra)
                    if provs:
                        html_p = '<div style="display: flex; gap: 5px; margin-top: 5px;">'
                        for p in provs[:3]: html_p += f'<img src="{LOGO_URL}{p["logo_path"]}" width="25" style="border-radius:5px;">'
                        st.markdown(html_p + '</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)
else:
    st.info("Por favor, Inicia Sesión o Regístrate en la barra lateral para ver el contenido.")
