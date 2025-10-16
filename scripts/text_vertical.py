# scripts/text_vertical.py
from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components

# ========= Configuración de página (debe ser lo PRIMERO en la página) =========


def page_config_once_vertical(
    title: str = "Detector de asbesto",
    icon: str = "🌍",
    layout: str = "centered",
    initial_sidebar_state: str = "collapsed",
) -> None:
    """
    Llama a st.set_page_config UNA sola vez por página.
    Debe ejecutarse ANTES de cualquier otra llamada a st.* en la página.
    """
    key_flag = "_page_config_done_vertical"
    if not st.session_state.get(key_flag, False):
        st.set_page_config(
            page_title=title,
            page_icon=icon,
            layout=layout,
            initial_sidebar_state=initial_sidebar_state,
        )
        st.session_state[key_flag] = True


# ========= Estilos/CSS (SEGURO de llamar en cualquier momento) =========
def style_vertical() -> None:
    """
    Inyecta estilos y el script de Clarity.
    NO llama set_page_config (seguro de usar en cualquier orden).
    """
    # Script de Microsoft Clarity (opcional; puedes quitarlo si no lo usas)
    components.html(
        """
        <script type="text/javascript">
            (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window, document, "clarity", "script", "o0m4wpyj67");
        </script>
        """,
        height=0,
    )

    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap');

            .stImage { width: 200px; }

            .styled-text {
                font-family: 'Inter', sans-serif;
                font-size: 50px;
            }

            .stButton { display: flex; justify-content: center; }
            .stButton>button {
                background-color: black;
                width: 50%;
                color: white;
                border-radius: 20px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
                transform: scale(1.05);
                background-color: white;
                color: black;
            }
            .stButton>button:active {
                color: black;
                background-color: white;
            }

            .main { text-align: center; }
            .body { text-align: center; }
            .container { display: flex; justify-content: center; }

            @media (max-width: 768px) {
                .stColumns { flex-direction: row !important; width: 50% !important; }
                .stColumn  { flex-direction: row !important; width: 50% !important; }
            }

            .stApp a:first-child { display: none; }

            /* Ocultar algunos selectores antiguos (opcional) */
            .css-15zrgzn { display: none }
            .css-eczf16 { display: none }
            .css-jn99sy { display: none }

            /* Ajustes tipográficos comunes */
            .text-justify { text-align: justify; }
            .text-center { text-align: center; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ========= Helpers con sufijo _v para evitar colisiones =========
def pasos_v(texto: str) -> None:
    st.markdown(
        f"""
        <div style="color:#989DA3; text-align:center;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )


def h1_v(texto: str) -> None:
    st.markdown(
        f"""
        <h1 style="text-align:center; padding-top:0; font-size:40px;">{texto}</h1>
        """,
        unsafe_allow_html=True,
    )


def text_v(texto: str) -> None:
    st.text("")
    st.markdown(
        f"""
        <div class="text-justify" style="font-size:1rem; font-weight:400; font-family:'Source Sans Pro', sans-serif;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text("")


def text_resultados_v(texto: str) -> None:
    st.text("")
    st.markdown(
        f"""
        <div class="text-justify" style="font-size:1rem; font-weight:400; font-family:'Source Sans Pro', sans-serif;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text("")


def text_center_v(texto: str) -> None:
    st.text("")
    st.markdown(
        f"""
        <div class="text-center" style="font-size:1rem; font-weight:400; font-family:'Source Sans Pro', sans-serif;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text("")


def titulo_subrayado_v(texto: str) -> None:
    st.markdown(
        f"""
        <h1 style="font-size:55px; text-decoration:underline; text-align:center;">{texto}</h1>
        """,
        unsafe_allow_html=True,
    )
