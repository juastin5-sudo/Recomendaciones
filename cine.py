import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Juastin Stream Pro", page_icon="🎬", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILOS CSS (Diseño original restaurado) ---
st.markdown("""
    <style>
        html, body, [class*="st-"] { font-family: sans-serif !important; }
        .stApp { background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%); color: white; }
        .img-clicable:hover { transform: scale(1.02); transition: 0.3s; cursor: pointer; }
        div.stForm submit_button > button { 
            margin-top: 20px !important; 
            background-color: #E50914 !important; color: white !important; 
            font-weight: bold !important; border: none !important; width: 100%;
        }
        .valoracion-container { 
            margin-top: 15px; margin-bottom: 15px; font-weight: bold; 
            display: flex; align-items: center; gap: 5px; color: #FFD700; 
        }
        .resumen-inferior { 
            font-size: 12px; color: #bbbbbb; line-height: 1.3; margin-top: 8px; 
            height: 85px; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px; 
        }
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

# --- INICIALIZACIÓN DE ESTADOS ---
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'favoritos' not in st.session_state: st.session_state.favoritos = []

# --- BARRA LATERAL (ACCESO + FILTROS BLOQUEADOS) ---
with st.sidebar:
    st.title("👤 Mi Cuenta")
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
                if n_reg in lista_nombres: st.error("❌ Nombre en uso.")
                elif n_reg == "": st.warning("Escribe un nombre.")
                else:
                    nuevo_u = pd.DataFrame([{"usuario": n_reg}])
                    df_f = pd.concat([df_usuarios, nuevo_u], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_f)
                    st.session_state.usuario = n_reg
                    st.success("¡Bienvenido!")
                    st.rerun()
    else:
        st.success(f"Hola, {st.session_state.usuario.capitalize()}!")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    if st.session_state.usuario:
        with st.form("filtros"):
            st.write("### ⚙️ Filtros Avanzados")
            solo_favs = st.checkbox("❤️ Ver mis Favoritos")
            tipo_sel = st.radio("Contenido:", ["Películas", "Series"])
            tipo_api = "movie" if tipo_sel == "Películas" else "tv"
            min_rating = st.slider("Valoración ⭐", 0, 10, 6)
            aplicar = st.form_submit_button("🔍 APLICAR")
    else:
        st.warning("🔒 Inicia sesión para usar filtros y guardar favoritos.")
        tipo_api = "movie"
        min_rating = 0
        solo_favs = False

# --- CONTENIDO PRINCIPAL ---
# 1. Carrusel de Estrenos (Siempre visible)
estrenos = obtener_datos("trending/all/day")[:5]
if estrenos:
    slides_html = ""
    for i, item in enumerate(estrenos):
        tit = (item.get('title') or item.get('name')).replace("'", "")
        _, _, url_e = obtener_detalles_extras(item['id'], item.get('media_type', 'movie'), tit)
        slides_html += f"""
        <div class="mySlides fade">
            <a href="{url_e}" target="_blank" style="text-decoration: none;">
                <div class="hero-container" style="background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)), url('{IMAGE_URL}{item.get('backdrop_path')}'); height: 380px; background-size: cover; background-position: center; border-radius: 20px; display: flex; align-items: center; padding: 40px; color: white;">
                    <div>
                        <span style="background: #E50914; padding: 5px 10px; border-radius: 4px; font-weight: bold;">ESTRENO</span>
                        <h1 style="font-size: 40px; margin: 10px 0;">{tit}</h1>
                    </div>
                </div>
            </a>
        </div>"""
    carousel_js = f"""<div class="slideshow-container">{slides_html}</div><script>var slideIndex = 0; function showSlides() {{ var slides = document.getElementsByClassName("mySlides"); for (var i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }} slideIndex++; if (slideIndex > slides.length) {{slideIndex = 1}} slides[slideIndex-1].style.display = "block"; setTimeout(showSlides, 4000); }} showSlides();</script>"""
    components.html(carousel_js, height=400)

# 2. Buscador y Resultados
busqueda = st.text_input("", placeholder="Busca tu película favorita...")

if solo_favs and st.session_state.usuario:
    res = st.session_state.favoritos
else:
    params = {"sort_by": "popularity.desc", "vote_average.gte": min_rating}
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
            
            with st.container(height=320, border=False):
                st.markdown(f"**{t_item}**")
                
                # Botón Favoritos (Solo si está logueado)
                if st.session_state.usuario:
                    es_fav = any(f['id'] == item['id'] for f in st.session_state.favoritos)
                    btn_txt = "❤️ Quitar" if es_fav else "🤍 Guardar"
                    if st.button(btn_txt, key=f"fav_{item['id']}"):
                        if es_fav: st.session_state.favoritos = [f for f in st.session_state.favoritos if f['id'] != item['id']]
                        else: st.session_state.favoritos.append(item)
                        st.rerun()
                
                if tra:
                    with st.expander("🎬 VER TRAILER"): st.video(tra)
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)

