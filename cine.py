import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Juastin Stream Pro", page_icon="🎬", layout="wide")

# --- CONEXIÓN A BASE DE DATOS (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILOS CSS (DISEÑO ORIGINAL SIN ERRORES) ---
st.markdown("""
    <style>
        html, body, [class*="st-"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; }
        .stApp { background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%); color: white; }
        .block-container {padding-top: 1rem;}
        .img-clicable:hover { transform: scale(1.02); transition: 0.3s; cursor: pointer; }
        
        /* Limpiar botones de trailer */
        .stExpander { border: none !important; background: transparent !important; }
        
        div.stForm submit_button > button { 
            margin-top: 20px !important; 
            background-color: #E50914 !important; color: white !important; 
            font-weight: bold !important; border: none !important; width: 100%;
        }

        /* Espaciado Valoración vs Raya */
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

# --- USUARIOS Y FAVORITOS ---
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'favoritos' not in st.session_state: st.session_state.favoritos = []

# --- SIDEBAR (LOGIN + FILTROS COMPLETOS) ---
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
                else: st.error("No registrado.")
        with t2:
            n_reg = st.text_input("Nombre único", key="r").lower().strip()
            if st.button("Validar y Crear"):
                if n_reg in lista_nombres: st.error("❌ En uso.")
                elif n_reg == "": st.warning("Escribe un nombre.")
                else:
                    df_f = pd.concat([df_usuarios, pd.DataFrame([{"usuario": n_reg}])], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_f)
                    st.session_state.usuario = n_reg
                    st.rerun()
    else:
        st.success(f"Hola, {st.session_state.usuario.capitalize()}")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    # Filtros avanzados bloqueados hasta login
    if st.session_state.usuario:
        with st.form("filtros_completos"):
            st.write("### ⚙️ Filtros")
            solo_favs = st.checkbox("❤️ Ver mis Favoritos")
            tipo_sel = st.radio("Ver:", ["Películas", "Series"])
            tipo_api = "movie" if tipo_sel == "Películas" else "tv"
            
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
            st.form_submit_button("🔍 APLICAR")
    else:
        st.info("🔓 Inicia sesión para usar filtros y guardar favoritos.")
        tipo_api, min_rating, solo_favs, menu_sel, humor_sel, p_sel = "movie", 0, False, [], [], []

# --- CONTENIDO PRINCIPAL ---
# Carrusel
estrenos = obtener_datos("trending/all/day")[:5]
if estrenos:
    slides = ""
    for i, item in enumerate(estrenos):
        tit = (item.get('title') or item.get('name')).replace("'", "")
        res = item.get('overview', '')[:220] + "..."
        _, _, url_e = obtener_detalles_extras(item['id'], item.get('media_type', 'movie'), tit)
        slides += f"""
        <div class="mySlides fade">
            <a href="{url_e}" target="_blank" style="text-decoration: none;">
                <div style="background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)), url('{IMAGE_URL}{item.get('backdrop_path')}'); height: 420px; background-size: cover; border-radius: 20px; display: flex; align-items: center; padding: 40px; color: white;">
                    <div>
                        <span style="background: #E50914; padding: 5px 12px; border-radius: 4px; font-weight: bold;">TOP #{i+1}</span>
                        <h1 style="font-size: 45px; margin: 15px 0;">{tit}</h1>
                        <p style="max-width: 650px; font-size: 18px;">{res}</p>
                    </div>
                </div>
            </a>
        </div>"""
    components.html(f'<div class="slideshow-container">{slides}</div><script>var slideIndex = 0; function showSlides() {{ var slides = document.getElementsByClassName("mySlides"); for (var i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }} slideIndex++; if (slideIndex > slides.length) {{slideIndex = 1}} slides[slideIndex-1].style.display = "block"; setTimeout(showSlides, 5000); }} showSlides();</script>', height=430)

busqueda = st.text_input("", placeholder="Busca tu película favorita aquí...")

# Lógica de datos
if solo_favs:
    resultados = st.session_state.favoritos
else:
    todos_gen = ",".join(menu_sel + humor_sel)
    params = {"sort_by": "popularity.desc", "vote_average.gte": min_rating, "with_genres": todos_gen}
    if p_sel: params["with_watch_providers"] = "|".join(map(str, p_sel)); params["watch_region"] = "ES"
    resultados = obtener_datos(f"search/{tipo_api}", {"query": busqueda}) if busqueda else obtener_datos(f"discover/{tipo_api}", params)

if resultados:
    st.markdown("---")
    cols = st.columns(4)
    for i, item in enumerate(resultados[:12]):
        with cols[i % 4]:
            t_item = item.get('title') or item.get('name')
            tra, provs, url_f = obtener_detalles_extras(item['id'], tipo_api, t_item)
            if item.get('poster_path'):
                st.markdown(f'<a href="{url_f}" target="_blank"><img src="{POSTER_URL}{item["poster_path"]}" class="img-clicable" style="width:100%; border-radius:10px;"></a>', unsafe_allow_html=True)
            
            with st.container(height=360, border=False):
                st.markdown(f"**{t_item}**")
                
                if st.session_state.usuario:
                    es_fav = any(f['id'] == item['id'] for f in st.session_state.favoritos)
                    if st.button("❤️ Quitar" if es_fav else "🤍 Guardar", key=f"f_{item['id']}"):
                        if es_fav: st.session_state.favoritos = [f for f in st.session_state.favoritos if f['id'] != item['id']]
                        else: st.session_state.favoritos.append(item)
                        st.rerun()
                
                # Logos de plataformas restaurados
                if provs:
                    html_p = '<div style="display: flex; gap: 5px; margin-top: 5px; margin-bottom: 5px;">'
                    for p in provs[:4]: html_p += f'<img src="{LOGO_URL}{p["logo_path"]}" width="26" style="border-radius:5px;">'
                    st.markdown(html_p + '</div>', unsafe_allow_html=True)
                
                if tra:
                    with st.expander("🎬 TRÁILER"): st.video(tra)
                
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)

