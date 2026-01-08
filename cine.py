import streamlit as st
import streamlit.components.v1 as components
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Juastin Stream Pro", page_icon="🎬", layout="wide")

# --- INICIALIZACIÓN DE ESTADOS (Para Favoritos y Usuario) ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'favoritos' not in st.session_state:
    st.session_state.favoritos = []

# --- CONTROL DE ESTILOS (CSS) ---
st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #050505 0%, #0a0a1a 50%, #150a1e 100%); color: white; }
        .img-clicable:hover { transform: scale(1.02); transition: 0.3s; cursor: pointer; }
        div.stForm submit_button > button { margin-top: 40px !important; background-color: #E50914 !important; color: white !important; font-weight: bold !important; border: none !important; }
        [data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.7) !important; }
        .valoracion-container { margin-top: 15px; margin-bottom: 12px; font-weight: bold; display: flex; align-items: center; gap: 5px; color: #FFD700; }
        .resumen-inferior { font-size: 12px; color: #bbbbbb; line-height: 1.3; margin-top: 8px; height: 85px; overflow: hidden; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 5px; }
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
        url_final = f"https://www.google.com/search?q=ver+{titulo_item.replace(' ', '+')}+online"
        for p in raw_providers:
            if p['provider_name'] not in vistos:
                providers_unicos.append(p)
                vistos.add(p['provider_name'])
        return trailer, providers_unicos, url_final
    except: return None, [], None

# --- SIDEBAR: LOGIN Y FILTROS ---
with st.sidebar:
    st.title("👤 Usuario")
    if not st.session_state.usuario:
        nombre = st.text_input("Ingresa tu nombre para empezar:")
        if st.button("Iniciar Sesión"):
            st.session_state.usuario = nombre
            st.rerun()
    else:
        st.success(f"Bienvenido, {st.session_state.usuario}!")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

    st.markdown("---")
    with st.form("formulario_filtros"):
        st.write("### ⚙️ Panel de Control")
        solo_favoritos = st.checkbox("❤️ Ver mis Favoritos")
        tipo_contenido = st.radio("#### 📺 Ver:", ["Películas", "Series"])
        tipo_api = "movie" if tipo_contenido == "Películas" else "tv"
        
        st.markdown("---")
        st.write("#### 🍳 Menú")
        dict_menu = {"☕ Desayuno": "28,12", "🍲 Almuerzo": "99,18", "🍰 Merienda": "35,10751", "🌙 Cena": "53,80"}
        menu_sel = [dict_menu[m] for m in dict_menu if st.checkbox(m)]
        
        st.markdown("---")
        min_rating = st.slider("Valoración ⭐ mínima", 0, 10, 6)
        enviar = st.form_submit_button("🔍 APLICAR FILTROS")

# --- CUERPO PRINCIPAL ---
st.write("")
busqueda = st.text_input("", placeholder="Busca tu película o serie favorita aquí...")

# Lógica de obtención de resultados
if solo_favoritos:
    resultados = [fav for fav in st.session_state.favoritos if tipo_api in fav.get('media_type', tipo_api)]
else:
    params = {"sort_by": "popularity.desc", "vote_average.gte": min_rating, "with_genres": ",".join(menu_sel)}
    resultados = obtener_datos(f"search/{tipo_api}", {"query": busqueda}) if busqueda else obtener_datos(f"discover/{tipo_api}", params)

# --- MOSTRAR RESULTADOS ---
if resultados:
    st.markdown("---")
    cols = st.columns(4)
    for i, item in enumerate(resultados[:12]):
        with cols[i % 4]:
            titulo = item.get('title') or item.get('name')
            trailer, donde_ver, url_final = obtener_detalles_extras(item['id'], tipo_api, titulo)
            
            if item.get('poster_path'):
                st.markdown(f'<a href="{url_final}" target="_blank"><img src="{POSTER_URL}{item["poster_path"]}" class="img-clicable" style="width:100%; border-radius:10px; margin-bottom:10px;"></a>', unsafe_allow_html=True)
            
            with st.container(height=320, border=False):
                st.markdown(f"**{titulo}**")
                
                # BOTÓN DE FAVORITOS
                es_fav = any(f['id'] == item['id'] for f in st.session_state.favoritos)
                btn_label = "❤️ Quitar" if es_fav else "🤍 Guardar"
                if st.button(btn_label, key=f"fav_{item['id']}"):
                    if es_fav:
                        st.session_state.favoritos = [f for f in st.session_state.favoritos if f['id'] != item['id']]
                    else:
                        st.session_state.favoritos.append(item)
                    st.rerun()

                if trailer:
                    with st.expander("🎬 TRÁILER"): st.video(trailer)
                
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="valoracion-container">⭐ {item["vote_average"]}</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="resumen-inferior">{item.get("overview", "Sin descripción.")}</div>', unsafe_allow_html=True)
