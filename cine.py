import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# Conectamos con tu Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LÓGICA DE USUARIOS ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

with st.sidebar:
    st.title("👤 Acceso")
    
    if not st.session_state.usuario:
        # Cargamos los usuarios actuales desde la hoja "Usuarios"
        try:
            df_existente = conn.read(worksheet="Usuarios")
            # Convertimos la columna a una lista para comparar fácil
            nombres_registrados = df_existente['usuario'].astype(str).str.lower().tolist()
        except:
            nombres_registrados = []
            df_existente = pd.DataFrame(columns=['usuario'])

        tab1, tab2 = st.tabs(["Entrar", "Registrarse"])

        with tab1:
            nombre_login = st.text_input("Tu nombre", key="l").lower().strip()
            if st.button("Iniciar Sesión"):
                if nombre_login in nombres_registrados:
                    st.session_state.usuario = nombre_login
                    st.rerun()
                else:
                    st.error("Este nombre no está registrado.")

        with tab2:
            nombre_reg = st.text_input("Elige un nombre único", key="r").lower().strip()
            if st.button("Validar y Crear"):
                if nombre_reg == "":
                    st.warning("Escribe algo...")
                elif nombre_reg in nombres_registrados:
                    # AQUÍ ESTÁ TU VALIDACIÓN
                    st.error("❌ Ese nombre ya está en uso, elige otro.")
                else:
                    # GUARDAR EN EL EXCEL
                    nuevo_usuario = pd.DataFrame([{"usuario": nombre_reg}])
                    df_actualizado = pd.concat([df_existente, nuevo_usuario], ignore_index=True)
                    
                    # Esta función sube los datos a tu Google Sheet
                    conn.update(worksheet="Usuarios", data=df_actualizado)
                    
                    st.session_state.usuario = nombre_reg
                    st.success("¡Nombre guardado! Ya puedes entrar.")
                    st.rerun()
    else:
        st.write(f"Conectado como: **{st.session_state.usuario.capitalize()}**")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()

