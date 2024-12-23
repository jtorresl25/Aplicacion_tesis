import datetime
from urllib.parse import urlparse
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components
from scripts.text import *
import streamlit.components.v1 as components


def style():
    st.set_page_config(
        page_title="Detector de asbesto",
        page_icon="🌍",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    components.html("""
    <script type="text/javascript">
        (function(c,l,a,r,i,t,y){
            c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
        })(window, document, "clarity", "script", "o0m4wpyj67");
    </script>
        """, height=0)

    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap');

            .stImage {
                width: 200px;
            }
            .styled-text {
                font-family: 'Inter', sans-serif;
                font-size: 50px;
            }
            .stButton {
                display: flex;
                justify-content: center;
            }
            .stButton>button {
                background-color: black;
                width: 50%;
                color: white;
                border-radius: 20px;
                transition: all 0.3s ease; /* Agrega una transición suave */
            }
            .stButton>button:hover {
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3); /* Agrega sombra al pasar el cursor */
                transform: scale(1.05); /* Escala el botón ligeramente */
                background-color: white;
            }
            .stButton>button:active {
                color: black;
                background-color: white;
            }
            /* Centrar contenido */
            .main {
                text-align: center;

            }
            .body {
                text-align: center;
            }
            .container {
                display: flex;
                justify-content: center;
            }
            @media (max-width: 768px) {
                .stColumns {
                    flex-direction: row !important;
                    width: 50% !important;
                }
                .stColumn {
                    flex-direction: row !important;
                    width: 50% !important;
                }
            }
            .stApp a:first-child {
                display: none;
            }

            .css-15zrgzn {display: none}
            .css-eczf16 {display: none}
            .css-jn99sy {display: none}
            /* Estilo para el input de URL */
        </style>
        """,
        unsafe_allow_html=True
    )


def pasos(texto):
    st.markdown(
        f"""
            <div style="color: #989DA3;text-align: center;">
                {texto}
            </div>
        """, unsafe_allow_html=True
    )


def h1(texto):
    st.markdown(
        f"""
            <h1 style="text-align: center; padding-top: 0; font-size:40px;">{texto}</h1>
        """, unsafe_allow_html=True
    )


def text(texto):
    st.text("")
    st.markdown(
        f"""
        <div style="font-size: 1rem; font-weight: 400;text-align: justify; font-family: ""Source Sans Pro", sans-serif">
            {texto}
        </div>
        """, unsafe_allow_html=True
    )
    st.text("")


def text_resultados(texto):
    st.text("")
    st.markdown(
        f"""
        <div style="font-size: 1rem; font-weight: 400;text-align: justify; font-family: ""Source Sans Pro", sans-serif", >
            {texto}
        </div>
        """, unsafe_allow_html=True
    )
    st.text("")


def text_center(texto):
    st.text("")
    st.markdown(
        f"""
        <div style="font-size: 1rem; font-weight: 400;text-align: center; font-family: ""Source Sans Pro", sans-serif">
            {texto}
        </div>
        """, unsafe_allow_html=True
    )
    st.text("")


def titulo_subrayado(texto):
    st.markdown(
        f"""<h1 style="font-size: 55px;text-decoration: underline; text-align: center;">{texto}</h1>""",
        unsafe_allow_html=True
    )
