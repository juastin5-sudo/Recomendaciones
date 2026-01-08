import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import streamlit.components.v1 as components

# 1. Configuración de página - Oculta la barra lateral al inicio
st.set_page_config(
    page_title="Juastin Stream Pro", 
    page_icon="🎬", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CONEXIÓN A BASE DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILOS CSS (LIMPIEZA DE ERRORES Y DISEÑO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
        .stApp { background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%); color: white; }
    
    /* Arreglo para el botón de la barra lateral */
    [data-testid="stSidebarCollapsedControl"] {
        font-family: 'Material Icons' !important;
        background-color: #E50914 !important;
        color: white !important;
        border-radius: 0 10px 10px 0 !important;
    }

    /* Ocultar iconos internos que causan errores de texto */
    [data-testid="stExpanderIcon"], .stExpander svg { display: none !important; }

    .img-clicable:hover { transform: scale(1.02); transition: 0.3s; cursor: pointer; }
    
    div.stForm submit_button > button { 
        background-color: #E50914 !important; color: white !important; 
        font-weight: bold !important; border: none !important; width: 100%; 
    }

    .valoracion-container { 
        margin-top: 15px; margin-bottom: 18px; font-weight: bold; 
        display: flex; align-items: center; gap: 5px; color: #FFD700; 
    }

    .resumen-inferior { 
        font-size: 12px; color: #bbbbbb; line-height: 1.4; margin-top: 8px; 
        height: 85px; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; 
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN API ---
API_KEY = "d47891b58f979b4677c9697556247e06" 
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/original"
POSTER_URL = "https://image.tmdb.org/t/p/w500"
LOGO_URL = "https://image.tmdb.org/t/p/original"

def obtener_detalles_completos(item_id, tipo, titulo_item):
    params = {"api_key": API_KEY, "language": "es-ES", "append_to_response": "videos,watch/providers"}
    url = f"{BASE_URL}/{tipo}/{item_id}"
    try:
        res = requests.get(url, params=params).json()
        trailer = None
        for v in res.get('videos', {}).get('results', []):
            if v['type'] in ['Trailer', 'Opening'] and v['site'] == 'YouTube':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break
        
        region = res.get('watch/providers', {}).get('results', {}).get('ES', {})
        providers = region.get('flatrate', [])
        vistos = set()
        providers_unicos = []
        for p in providers:
            if p['provider_name'] not in vistos:
                providers_unicos.append(p)
                vistos.add(p['provider_name'])
        
        link_ver = region.get('link') if providers else f"https://www.google.com/search?q=ver+{titulo_item.replace(' ', '+')}+online"
        return trailer, providers_unicos, link_ver
    except:
        return None, [], f"https://www.google.com/search?q={titulo_item}"

# --- LÓGICA DE SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'favoritos' not in st.session_state:
    st.session_state.favoritos = []

with st.sidebar:
    st.title("👤 Acceso")
    try:
        df_u = conn.read(worksheet="Usuarios", ttl=0)
        nombres = df_u['usuario'].astype(str).str.lower().tolist()
    except:
        nombres = []
        df_u = pd.DataFrame(columns=['usuario'])

    if not st.session_state.usuario:
        t1, t2 = st.tabs(["Entrar", "Registrarse"])
        with t1:
            n_l = st.text_input("Nombre", key="l").lower().strip()
            if st.button("Iniciar Sesión"):
                if n_l in nombres:
                    st.session_state.usuario = n_l
                    st.rerun()
                else:
                    st.error("No registrado.")
        with t2:
            n_r = st.text_input("Nombre único", key="r").lower().strip()
            if st.button("Validar y Crear"):
                if n_r in nombres:
                    st.error("❌ En uso.")
                elif n_r == "":
                    st.warning("Escribe algo.")
                else:
                    df_u = pd.concat([df_u, pd.DataFrame([{"usuario": n_r}])], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_u)
                    st.session_state.usuario = n_r
                    st.rerun()
    else:
        st.success(f"Hola, {st.session_state.usuario.capitalize()}")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    if st.session_state.usuario:
        with st.form("filtros_pro"):
            st.write("### ⚙️ Panel de Control")
            solo_favs = st.checkbox("❤️ Mis Favoritos")
            tipo_sel = st.radio("Ver:", ["Películas", "Series"])
            tipo_api = "movie" if tipo_sel == "Películas" else "tv"
            
            st.write("#### 🍳 Menú")
            dict_m = {"☕ Desayuno": "28,12", "🍲 Almuerzo": "99,18", "🍰 Merienda": "35,10751", "🌙 Cena": "53,80"}
            menu_sel = [dict_m[m] for m in dict_m if st.checkbox(m)]
            
            st.write("#### 🎭 Humor")
            dict_h = {"😂 Reír": "35", "😱 Tensión": "53,27", "🎭 Drama": "18", "🚀 Futuro": "878"}
            humor_sel = [dict_h[h] for h in dict_h if st.checkbox(h)]

            st.write("#### 📺 Plataformas")
            dict_p = {"Netflix": 8, "Disney+": 337, "HBO Max": 1899, "Amazon": 119, "Crunchyroll": 283}
            p_sel = [dict_p[p] for p in dict_p if st.checkbox(p)]

            min_rating = st.slider("Valoración ⭐", 0, 10, 6)
            st.form_submit_button("🔍 APLICAR")
    else:
        tipo_api, min_rating, solo_favs, menu_sel, humor_sel, p_sel = "movie", 0, False, [], [], []

# --- CARRUSEL ANIMADO ---
estrenos = requests.get(f"{BASE_URL}/trending/all/day?api_key={API_KEY}&language=es-ES").json().get('results', [])[:5]
if estrenos:
    slides = ""
    for i, item in enumerate(estrenos):
        tit = (item.get('title') or item.get('name')).replace("'", "")
        res = item.get('overview', '')[:220] + "..."
        _, _, link_e = obtener_detalles_completos(item['id'], item.get('media_type', 'movie'), tit)
        slides += f"""
        <div class="mySlides fade">
            <a href="{link_e}" target="_blank" style="text-decoration: none;">
                <div style="background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)), url('{IMAGE_URL}{item.get('backdrop_path')}'); height: 420px; background-size: cover; border-radius: 20px; display: flex; align-items: center; padding: 40px; color: white;">
                    <div>
                        <span style="background: #E50914; padding: 5px 12px; border-radius: 4px; font-weight: bold;">TOP #{i+1}</span>
                        <h1 style="font-size: 45px; margin: 15px 0; font-weight: 800;">{tit}</h1>
                        <p style="max-width: 650px; font-size: 18px; line-height: 1.5;">{res}</p>
                    </div>
                </div>
            </a>
        </div>"""
    components.html(f'<div class="slideshow-container">{slides}</div><script>var sI = 0; function sS() {{ var s = document.getElementsByClassName("mySlides"); for (var i = 0; i < s.length; i++) {{ s[i].style.display = "none"; }} sI++; if (sI > s.length) {{sI = 1}} s[sI-1].style.display = "block"; setTimeout(sS, 5000); }} sS();</script>', height=430)

# --- RESULTADOS ---
busqueda = st.text_input("", placeholder="Busca tu película favorita aquí...")
if solo_favs:
    resultados = st.session_state.favoritos
else:
    gen_filt = ",".join(menu_sel + humor_sel)
    params = {"api_key": API_KEY, "language": "es-ES", "sort_by": "popularity.desc", "vote_average.gte": min_rating, "with_genres": gen_filt}
    if p_sel: params["with_watch_providers"] = "|".join(map(str, p_sel)); params["watch_region"] = "ES"
    resultados = requests.get(f"{BASE_URL}/search/{tipo_api}" if busqueda else f"{BASE_URL}/discover/{tipo_api}", params={**params, "query": busqueda}).json().get('results', [])

if resultados:
    st.markdown("---")
    cols = st.columns(4)
    for i, item in enumerate(resultados[:12]):
        with cols[i % 4]:
            tit_i = item.get('title') or item.get('name')
            tra, provs, link_p = obtener_detalles_completos(item['id'], tipo_api, tit_i)
            if item.get('poster_path'):
                st.markdown(f'<a href="{link_p}" target="_blank"><img src="{POSTER_URL}{item["poster_path"]}" class="img-clicable" style="width:100%; border-radius:10px;"></a>', unsafe_allow_html=True)
            
            with st.container(height=380, border=False):
                st.markdown(f"**{tit_i}**")
                if st.session_state.usuario:
                    es_f = any(f['id'] == item['id'] for f in st.session_state.favoritos)
                    if st.button("❤️" if es_f else "🤍", key=f"f_{item['id']}"):
                        if es_f: st.session_state.favoritos = [f for f in st.session_state.favoritos if f['id'] != item['id']]
                        else: st.session_state.favoritos.append(item)
                        st.rerun()
                
                if provs:
                    h_p = '<div style="display: flex; gap: 5px; margin-top: 5px; margin-bottom: 5px;">'
                    for p in provs[:4]: h_p += f'<img src="{LOGO_URL}{p["logo_path"]}" width="26" style="border-radius:5px;">'
                    st.markdown(h_p + '</div>', unsafe_allow_html=True)
                
                if tra:
                    with st.expander("VER TRÁILER"): st.video(tra)
                
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "...")}</div>', unsafe_allow_html=True)
