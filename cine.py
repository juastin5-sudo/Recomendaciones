import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Conexión con Google Sheets (Configurada en los Secrets de Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LÓGICA DE USUARIOS ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

with st.sidebar:
    st.title("👤 Acceso")
    
    if not st.session_state.usuario:
        # Leemos los usuarios actuales de la columna 'usuario'
        try:
            df_usuarios = conn.read(worksheet="Usuarios")
            lista_usuarios = df_usuarios['usuario'].astype(str).str.lower().tolist()
        except:
            lista_usuarios = []

        tab1, tab2 = st.tabs(["Entrar", "Registrarse"])

        with tab1:
            nombre_login = st.text_input("Tu nombre", key="login").lower().strip()
            if st.button("Iniciar Sesión"):
                if nombre_login in lista_usuarios:
                    st.session_state.usuario = nombre_login
                    st.rerun()
                else:
                    st.error("Este usuario no existe. ¡Regístrate!")

        with tab2:
            nombre_registro = st.text_input("Crea tu nombre único", key="registro").lower().strip()
            if st.button("Validar y Crear"):
                if nombre_registro == "":
                    st.warning("Escribe un nombre.")
                elif nombre_registro in lista_usuarios:
                    # VALIDACIÓN QUE PEDISTE
                    st.error("❌ Ese nombre ya está en uso, por favor elige otro.")
                else:
                    # GUARDAR EN GOOGLE SHEETS
                    nuevo_df = pd.DataFrame([{"usuario": nombre_registro}])
                    # Actualizamos la hoja añadiendo el nuevo usuario
                    df_final = pd.concat([df_usuarios, nuevo_df], ignore_index=True)
                    conn.update(worksheet="Usuarios", data=df_final)
                    
                    st.session_state.usuario = nombre_registro
                    st.success("¡Nombre registrado con éxito!")
                    st.rerun()
    else:
        st.write(f"Hola, **{st.session_state.usuario}**")
        if st.button("Cerrar Sesión"):
            st.session_state.usuario = None
            st.rerun()
