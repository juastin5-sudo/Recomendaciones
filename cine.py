import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Conexión mejorada
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_usuarios():
    try:
        # Intentamos leer la hoja "Usuarios"
        return conn.read(worksheet="Usuarios", ttl=0) # ttl=0 para datos frescos
    except:
        return pd.DataFrame(columns=['usuario'])

# --- LÓGICA DE USUARIOS ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

with st.sidebar:
    st.title("👤 Acceso")
    
    if not st.session_state.usuario:
        df_existente = cargar_usuarios()
        nombres_registrados = df_existente['usuario'].astype(str).str.lower().tolist()

        tab1, tab2 = st.tabs(["Entrar", "Registrarse"])

        with tab1:
            nombre_login = st.text_input("Tu nombre", key="l").lower().strip()
            if st.button("Iniciar Sesión"):
                if nombre_login in nombres_registrados:
                    st.session_state.usuario = nombre_login
                    st.rerun()
                else:
                    st.error("Este nombre no existe.")

        with tab2:
            nombre_reg = st.text_input("Nombre único", key="r").lower().strip()
            if st.button("Validar y Crear"):
                if nombre_reg in nombres_registrados:
                    st.error("❌ Ese nombre ya está en uso.")
                elif nombre_reg == "":
                    st.warning("Escribe un nombre.")
                else:
                    try:
                        # Creamos el nuevo registro
                        nuevo_u = pd.DataFrame([{"usuario": nombre_reg}])
                        df_final = pd.concat([df_existente, nuevo_u], ignore_index=True)
                        
                        # ACTUALIZACIÓN: Guardamos en la nube
                        conn.update(worksheet="Usuarios", data=df_final)
                        
                        st.session_state.usuario = nombre_reg
                        st.success("¡Registrado!")
                        st.rerun()
                    except Exception as e:
                        st.error("Error de permisos en Google Sheets. Asegúrate de que el enlace permita EDITAR.")
    else:
        st.write(f"Hola, **{st.session_state.usuario.capitalize()}**")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()
