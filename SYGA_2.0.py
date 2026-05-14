import io
import os
import re
import utm
import yaml
import math
import folium
import pycountry
import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import streamlit as st
from textwrap import wrap
import statsmodels.api as sm
from fractions import Fraction
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import plotly.graph_objects as go
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from streamlit_pdf_viewer import pdf_viewer
from scipy.interpolate import griddata, Rbf
from scipy.ndimage import gaussian_filter1d
import streamlit.components.v1 as components
import matplotlib.patheffects as path_effects
from streamlit_js_eval import get_geolocation
from matplotlib.patches import Rectangle, Polygon
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea, VPacker

@st.cache_data(show_spinner=False)
def carregar_workbook(file_bytes):
    buffer = io.BytesIO(file_bytes)
    wb = load_workbook(buffer, data_only=True)
    return wb

#  Configurações da página web
logo = 'logo.png'
img_logo = Image.open(logo)
cab = 'logo_syng.png'
img_cab = Image.open(cab)
image = Image.open(logo)
PAGE_CONFIG = {"page_title": "SYGA",
               "page_icon": image,
               "layout": "wide",
               "initial_sidebar_state": "auto",
               }
st.set_page_config(**PAGE_CONFIG)
st.image(img_cab, width=2000)
st.markdown(
    "<div style='text-align: left; font-size: 16px; color: gray;'>"
    "Developed by Adriel Oliveira - 2025"
    "</div>",
    unsafe_allow_html=True
)

# hide_st_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             footer {visibility: hidden;}
#             header {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_st_style, unsafe_allow_html=True)

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = False

if "pdf_params_hash" not in st.session_state:
    st.session_state.pdf_params_hash = None

if "pdf_view_open" not in st.session_state:
    st.session_state.pdf_view_open = False

if "gn" not in st.session_state:
    st.session_state.gn = 8.5

paises = {
    "Afeganistão": "af",
    "África do Sul": "za",
    "Albânia": "al",
    "Alemanha": "de",
    "Andorra": "ad",
    "Angola": "ao",
    "Antígua e Barbuda": "ag",
    "Arábia Saudita": "sa",
    "Argélia": "dz",
    "Argentina": "ar",
    "Armênia": "am",
    "Austrália": "au",
    "Áustria": "at",
    "Azerbaijão": "az",
    "Bahamas": "bs",
    "Bahrein": "bh",
    "Bangladesh": "bd",
    "Barbados": "bb",
    "Bélgica": "be",
    "Belize": "bz",
    "Benim": "bj",
    "Bielorrússia": "by",
    "Bolívia": "bo",
    "Bósnia e Herzegovina": "ba",
    "Botsuana": "bw",
    "Brasil": "br",
    "Brunei": "bn",
    "Bulgária": "bg",
    "Burkina Faso": "bf",
    "Burundi": "bi",
    "Butão": "bt",
    "Cabo Verde": "cv",
    "Camarões": "cm",
    "Camboja": "kh",
    "Canadá": "ca",
    "Catar": "qa",
    "Cazaquistão": "kz",
    "Chade": "td",
    "Chile": "cl",
    "China": "cn",
    "Chipre": "cy",
    "Colômbia": "co",
    "Comores": "km",
    "Congo": "cg",
    "Coreia do Norte": "kp",
    "Coreia do Sul": "kr",
    "Costa do Marfim": "ci",
    "Costa Rica": "cr",
    "Croácia": "hr",
    "Cuba": "cu",
    "Dinamarca": "dk",
    "Djibuti": "dj",
    "Dominica": "dm",
    "Egito": "eg",
    "El Salvador": "sv",
    "Emirados Árabes Unidos": "ae",
    "Equador": "ec",
    "Eritreia": "er",
    "Eslováquia": "sk",
    "Eslovênia": "si",
    "Espanha": "es",
    "Estados Unidos": "us",
    "Estônia": "ee",
    "Etiópia": "et",
    "Fiji": "fj",
    "Filipinas": "ph",
    "Finlândia": "fi",
    "França": "fr",
    "Gabão": "ga",
    "Gâmbia": "gm",
    "Gana": "gh",
    "Geórgia": "ge",
    "Granada": "gd",
    "Grécia": "gr",
    "Guatemala": "gt",
    "Guiana": "gy",
    "Guiné": "gn",
    "Guiné-Bissau": "gw",
    "Guiné Equatorial": "gq",
    "Haiti": "ht",
    "Honduras": "hn",
    "Hungria": "hu",
    "Iêmen": "ye",
    "Ilhas Marshall": "mh",
    "Ilhas Salomão": "sb",
    "Índia": "in",
    "Indonésia": "id",
    "Irã": "ir",
    "Iraque": "iq",
    "Irlanda": "ie",
    "Islândia": "is",
    "Israel": "il",
    "Itália": "it",
    "Jamaica": "jm",
    "Japão": "jp",
    "Jordânia": "jo",
    "Kiribati": "ki",
    "Kuwait": "kw",
    "Laos": "la",
    "Lesoto": "ls",
    "Letônia": "lv",
    "Líbano": "lb",
    "Libéria": "lr",
    "Líbia": "ly",
    "Liechtenstein": "li",
    "Lituânia": "lt",
    "Luxemburgo": "lu",
    "Macedônia do Norte": "mk",
    "Madagascar": "mg",
    "Malásia": "my",
    "Malawi": "mw",
    "Maldivas": "mv",
    "Mali": "ml",
    "Malta": "mt",
    "Marrocos": "ma",
    "Maurício": "mu",
    "Mauritânia": "mr",
    "México": "mx",
    "Micronésia": "fm",
    "Moçambique": "mz",
    "Moldávia": "md",
    "Mônaco": "mc",
    "Mongólia": "mn",
    "Montenegro": "me",
    "Myanmar": "mm",
    "Namíbia": "na",
    "Nauru": "nr",
    "Nepal": "np",
    "Nicarágua": "ni",
    "Níger": "ne",
    "Nigéria": "ng",
    "Noruega": "no",
    "Nova Zelândia": "nz",
    "Omã": "om",
    "Países Baixos": "nl",
    "Palau": "pw",
    "Panamá": "pa",
    "Papua-Nova Guiné": "pg",
    "Paquistão": "pk",
    "Paraguai": "py",
    "Peru": "pe",
    "Polônia": "pl",
    "Portugal": "pt",
    "Quênia": "ke",
    "Quirguistão": "kg",
    "Reino Unido": "gb",
    "República Centro-Africana": "cf",
    "República Dominicana": "do",
    "Romênia": "ro",
    "Ruanda": "rw",
    "Rússia": "ru",
    "Samoa": "ws",
    "San Marino": "sm",
    "Santa Lúcia": "lc",
    "São Cristóvão e Nevis": "kn",
    "São Tomé e Príncipe": "st",
    "São Vicente e Granadinas": "vc",
    "Senegal": "sn",
    "Serra Leoa": "sl",
    "Sérvia": "rs",
    "Seychelles": "sc",
    "Singapura": "sg",
    "Síria": "sy",
    "Somália": "so",
    "Sri Lanka": "lk",
    "Sudão": "sd",
    "Sudão do Sul": "ss",
    "Suécia": "se",
    "Suíça": "ch",
    "Suriname": "sr",
    "Tailândia": "th",
    "Tajiquistão": "tj",
    "Tanzânia": "tz",
    "Timor-Leste": "tl",
    "Togo": "tg",
    "Tonga": "to",
    "Trinidad e Tobago": "tt",
    "Tunísia": "tn",
    "Turcomenistão": "tm",
    "Turquia": "tr",
    "Tuvalu": "tv",
    "Ucrânia": "ua",
    "Uganda": "ug",
    "Uruguai": "uy",
    "Uzbequistão": "uz",
    "Vanuatu": "vu",
    "Vaticano": "va",
    "Venezuela": "ve",
    "Vietnã": "vn",
    "Zâmbia": "zm",
    "Zimbábue": "zw"
}


def numpy_to_python(obj):
    # converte recursivamente numpy -> python nativos
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: numpy_to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [numpy_to_python(i) for i in obj]
    return obj


@st.dialog("Remove well")
def remove():
    st.markdown('##### Well removal')
    if st.session_state.pocos:
        w = st.session_state.pocos.keys()
        st.multiselect('Select well to remove', list(w), key='well_to_remove')
    else:
        st.markdown('##### No well founded')

    if st.button('Remove selected wells', key='selected_bt'):
        if st.session_state.well_to_remove:
            for j in st.session_state.well_to_remove:
                del st.session_state.pocos[j]
            st.rerun()
        else:
            st.warning('No well was selected to remove')


def highlight_active(val):
    if val == st.session_state.well_selected:
        return "font-weight: bold; color: green;"  # destaque
    return ""  # os outros ficam normais


def gerar_perfil_sintetico(poco_origem, poco_destino, s_logs):
    """
    Gera perfil sintético no poço destino com base nas formações do poço origem,
    usando regra de 3 para reescalar profundidades.
    """

    profundidades_origem = poco_origem["profundidade"]
    formacoes_origem = poco_origem["formation"]

    profundidades_destino = poco_destino["profundidade"]
    formacoes_destino = poco_destino["formation"]

    df_sintetico = pd.DataFrame()

    for logs in s_logs:
        sint_prof_dest = []
        sint_prof_orig = []
        sint_valor = []
        sint_fm = []

        # converter listas do dicionário de perfil em arrays NumPy
        prof_array = np.array(poco_origem["perfil"]["Profundidade"])

        val_array = np.array(poco_origem["perfil"][logs])

        for i, fm in enumerate(formacoes_destino):
            if i < len(profundidades_destino) - 1:
                z_top_dest = profundidades_destino[i]
                z_base_dest = profundidades_destino[i + 1]

                if fm in formacoes_origem:
                    idx = formacoes_origem.index(fm)
                    z_top_orig = profundidades_origem[idx]
                    z_base_orig = profundidades_origem[idx + 1]

                    # perfis no intervalo da formação no poço origem
                    mask = (prof_array >= z_top_orig) & (prof_array < z_base_orig)

                    prof_fm = prof_array[mask]
                    val_fm = val_array[mask]

                    # cálculo da fração dentro da formação (α)
                    frac = (prof_fm - z_top_orig) / (z_base_orig - z_top_orig)

                    # mapeamento para poço destino
                    prof_esc = z_top_dest + frac * (z_base_dest - z_top_dest)
                    sint_prof_dest.extend(prof_esc)
                    sint_prof_orig.extend(prof_fm)
                    sint_valor.extend(val_fm)
                    sint_fm.extend([fm] * len(prof_fm))

        # df_sintetico[f'Formation'] = sint_fm
        # df_sintetico[f'Depth Original log'] = sint_prof_orig
        df_sintetico[f'Depth synthetic log'] = sint_prof_dest
        df_sintetico[f'Synthetic {logs}'] = sint_valor

        # df_sintetico = pd.DataFrame({
        #     "Formação": sint_fm,
        #     "Depth Origin": sint_prof_orig,
        #     "Depth Correlation": sint_prof_dest,
        #     f"Synthetic {logs}": sint_valor
        # })

    return df_sintetico


def plot_correlacao_com_logs(pocos, logs, description, lines, v_selected, tvd_labels, escala=(30, 300)):
    """
    Plota correlação entre múltiplos poços, cada um com seu log track no estilo clássico.
    """
    fig = go.Figure()
    paleta = {
        "Argilito": {"bg": "#9ACD32", "simbol": "|"},
        "Folhelho": {"bg": "#9ACD32", "simbol": "-"},
        "Siltito": {"bg": "#A67B5B", "simbol": "-"},
        "Arenito": {"bg": "#FFD580", "simbol": "."},
        "Diamictito": {"bg": "#E97451", "simbol": "."},
        "Conglomerado": {"bg": "#CD853F", "simbol": "."},
        "Anidrita / Gipsita": {"bg": "#E6E6FA", "simbol": "/"},
        "Halita": {"bg": "#FFFFFF", "simbol": "."},
        "Calcário": {"bg": "#B0C4DE", "simbol": "."},
        "Carbonato": {"bg": "#cfe8f3", "simbol": "x"},
        "Calcissiltito": {"bg": "#D8BFD8", "simbol": "."},
        "Calcarenito": {"bg": "#F5DEB3", "simbol": "."},
        "Calcirrudito": {"bg": "#4682B4", "simbol": "."},
        "Coquina": {"bg": "#FFDEAD", "simbol": "."},
        "Dolomito": {"bg": "#C2B280", "simbol": "."},
        "Basalto": {"bg": "#2F4F4F", "simbol": "+"},
        "Diabásio": {"bg": "#556B2F", "simbol": "."}
    }

    nomes = list(pocos.keys())
    n_pocos = len(nomes)
    espacamento = 2  # espaço lateral entre poços

    for idx, nome in enumerate(nomes):
        if nome not in v_selected:
            pass
        else:
            x_center = idx * espacamento
            poco = pocos[nome]

            profundidade = poco["profundidade"]
            fm = poco['formation']
            litologias = poco["litologia"]
            perfil = pd.DataFrame(poco['perfil'])
            tvd = poco['tvd']
            syn = False
            if 'Syn Log' in poco:
                syn = True

            # === 1) Faixas de formation ===
            for i in range(len(profundidade)):
                if i + 1 == len(profundidade):
                    z_top, z_base = profundidade[i], tvd
                else:
                    z_top, z_base = profundidade[i], profundidade[i + 1]
                lit = litologias[i]

                fig.add_trace(go.Scatter(
                    x=[x_center - 0.5, x_center + 0.5, x_center + 0.5, x_center - 0.5, x_center - 0.5],
                    y=[z_top, z_top, z_base, z_base, z_top],
                    fill="toself",
                    line=dict(color="black", width=1),
                    fillpattern=dict(
                        shape=paleta[lit]["simbol"],  # padrão diagonal
                        fgcolor="black",  # cor do padrão
                        bgcolor=paleta[lit]["bg"],
                        size=4,  # <<< controla o tamanho/espacamento
                        solidity=0.05  # densidade do padrão (0 = ralo, 1 = cheio)
                    ),
                    showlegend=False
                ))

                if tvd_labels:
                    fig.add_annotation(
                        x=x_center + 0.6,  # posição no eixo x
                        y=z_top,  # posição no eixo y (topo da formação)
                        text=f'{profundidade[i]} m',  # nome da formação
                        showarrow=False,  # sem seta
                        font=dict(size=12, color="black", family="Arial"),
                        align="left",
                        bordercolor="black",
                        borderwidth=1,
                        borderpad=2,
                        bgcolor="white",  # fundo da caixa
                        opacity=0.8
                    )

                if description:
                    # nome da formation
                    fig.add_trace(go.Scatter(
                        x=[x_center],
                        y=[(z_top + z_base) / 2],
                        text=[f"<b>{fm[i]}</b> - {lit}"],  # <<< negrito com HTML
                        mode="text",
                        textfont=dict(size=12, color="black", family="Arial"),  # define a fonte
                        showlegend=False,
                        hoverinfo="skip"
                    ))

            if syn:
                k = poco['Syn Log'].keys()
                x = list(k)
                x.remove('Depth synthetic log')
                for line in range(3):
                    if logs[line]:
                        if line == 0:
                            log = 'Synthetic Sonic log'
                            color = 'red'
                            scale = st.session_state.s_scale
                        elif line == 1:
                            log = 'Synthetic Density log'
                            color = 'purple'
                            scale = st.session_state.d_scale
                        else:
                            log = 'Synthetic Gamma ray log'
                            color = 'black'
                            scale = st.session_state.g_scale
                        try:
                            # === 2) Curva de log ===
                            z_log = poco['Syn Log']["Depth synthetic log"]
                            valores = np.array(poco['Syn Log'][log])
                            # normalizar valores para caber dentro da faixa do poço
                            vmin = min(poco['Syn Log'][log])
                            vmax = max(poco['Syn Log'][log])
                            x_log = x_center - 0.5 + (valores - vmin) / (vmax - vmin) * 1.0

                            fig.add_trace(go.Scatter(
                                x=x_log,
                                y=z_log,
                                mode="lines",
                                line=dict(color=color, width=1),
                                name=f"Log {nome}",
                                showlegend=False,
                                opacity=st.session_state.op
                            ))
                            # ['Above', 'Below', 'Remove']
                            if scale == 'Above':
                                y_pos = -50
                                top = y_pos - 70
                            elif scale == 'Below':
                                y_pos = tvd + 50
                                top = y_pos + 70
                            else:
                                y_pos = False
                                top = False

                            if y_pos:
                                # === 3) Escala do log logo acima do topo (y=0) ===
                                for v in np.linspace(vmin, vmax, 6):
                                    xpos = x_center - 0.5 + (v - vmin) / (vmax - vmin) * 1.0
                                    fig.add_trace(go.Scatter(
                                        x=[xpos],
                                        y=[y_pos],
                                        text=[str(int(v))],
                                        mode="text",
                                        textfont=dict(size=9, color=color),
                                        showlegend=False,
                                        hoverinfo="skip"
                                    ))

                                    # título do perfil
                                    fig.add_trace(go.Scatter(
                                        x=[x_center],
                                        y=[top],
                                        text=log,
                                        mode="text",
                                        textfont=dict(size=11, color=color),
                                        showlegend=False,
                                        hoverinfo="skip"
                                    ))
                        except KeyError:
                            pass

            for line in range(3):
                if logs[line]:
                    if line == 0:
                        log = 'Sonic log'
                        color = 'red'
                        scale = st.session_state.s_scale
                    elif line == 1:
                        log = 'Density log'
                        color = 'purple'
                        scale = st.session_state.d_scale
                    else:
                        log = 'Gamma ray log'
                        color = 'black'
                        scale = st.session_state.g_scale

                    try:
                        # === 2) Curva de log ===
                        z_log = perfil["Profundidade"]
                        valores = perfil[log]
                        # normalizar valores para caber dentro da faixa do poço
                        vmin = min(perfil[log])
                        vmax = max(perfil[log])
                        x_log = x_center - 0.5 + (valores - vmin) / (vmax - vmin) * 1.0

                        fig.add_trace(go.Scatter(
                            x=x_log,
                            y=z_log,
                            mode="lines",
                            line=dict(color=color, width=1),
                            name=f"Log {nome}",
                            showlegend=False,
                            opacity=st.session_state.op
                        ))
                        # ['Above', 'Below', 'Remove']
                        if scale == 'Above':
                            y_pos = -50
                            top = y_pos - 70
                        elif scale == 'Below':
                            y_pos = tvd + 50
                            top = y_pos + 70
                        else:
                            y_pos = False
                            top = False

                        if y_pos:
                            # === 3) Escala do log logo acima do topo (y=0) ===
                            for v in np.linspace(vmin, vmax, 6):
                                xpos = x_center - 0.5 + (v - vmin) / (vmax - vmin) * 1.0
                                fig.add_trace(go.Scatter(
                                    x=[xpos],
                                    y=[y_pos],
                                    text=[str(int(v))],
                                    mode="text",
                                    textfont=dict(size=9, color=color),
                                    showlegend=False,
                                    hoverinfo="skip"
                                ))

                                # título do perfil
                                fig.add_trace(go.Scatter(
                                    x=[x_center],
                                    y=[top],
                                    text=log,
                                    mode="text",
                                    textfont=dict(size=11, color=color),
                                    showlegend=False,
                                    hoverinfo="skip"
                                ))
                    except KeyError:
                        pass

            if lines:
                if idx < n_pocos - 1:
                    prox = pocos[nomes[idx + 1]]
                    if nomes[idx + 1] in v_selected:
                        # cria dicionários formacao->profundidade
                        mapa_atual = dict(zip(pocos[nomes[idx]]["formation"], pocos[nomes[idx]]["profundidade"]))
                        mapa_prox = dict(zip(prox["formation"], prox["profundidade"]))

                        # percorre formações em comum
                        for formacao, z_top in mapa_atual.items():
                            if formacao in mapa_prox:
                                z_top_prox = mapa_prox[formacao]

                                # desenha linha tracejada
                                fig.add_trace(go.Scatter(
                                    x=[x_center + 0.5, (idx + 1) * espacamento - 0.5],
                                    y=[z_top, z_top_prox],
                                    mode="lines",
                                    line=dict(color="black", width=1, dash="dash"),
                                    showlegend=False
                                ))
                            if z_top == profundidade[-1]:
                                z_top = pocos[nomes[idx]]['tvd']
                                z_top_prox = prox['tvd']
                                fig.add_trace(go.Scatter(
                                    x=[x_center + 0.5, (idx + 1) * espacamento - 0.5],
                                    y=[z_top, z_top_prox],
                                    mode="lines",
                                    line=dict(color="black", width=1, dash="dash"),
                                    showlegend=False
                                ))

            # Well name above lithology layers
            fig.add_trace(go.Scatter(
                x=[x_center],
                y=[-250],
                text=[nome],
                mode="text",
                textfont=dict(size=14, color="blue"),
                showlegend=False,
                hoverinfo="skip"
            ))

    # === Ajustes ===
    fig.update_yaxes(dtick=200)  # passo da escala do eixo da profundidade

    fig.update_yaxes(
        autorange="reversed",
        title="Profundidade (m)",
        range=[0, max(max(p["profundidade"]) for p in pocos.values())]  # começa em 0
    )
    fig.update_xaxes(visible=False)  # remove eixo X

    fig.update_layout(
        title="Correlação estratigráfica",
        plot_bgcolor="white",
        width=1000,
        height=800,
    )

    return fig


@st.dialog("Parâmetros da Correlação de Miller")
def parametros_miller():
    st.write("Insira os parâmetros para a correlação de **Miller**:")

    st.number_input('Insira o valor da ***Porosidade a Grandes Profundidades***', help='Entre 0,3 e 0,4',
                    step=1.0, format='%f', key='pa', min_value=0.0)
    st.number_input('Insira o valor da ***Parâmetro de Ajuste***', help='Entre 0,3 e 0,5',
                    step=1.0, format='%f', key='pb', min_value=0.0)
    st.number_input('Insira o valor da ***Taxa de Declínio da Porosidade***', help='Entre 0,002 e 0,004',
                    step=1.0, format='%f', key='k', min_value=0.0)
    st.number_input('Insira o valor da ***Parâmetro de Curvatura***', help='Entre 1,0 e 1,3',
                    step=1.0, format='%f', key='n', min_value=0.0)
    st.number_input('Insira o valor da ***Densidade da Matriz***', help='Entre 2,0 e 3,0',
                    step=1.0, format='%f', key='dm', min_value=0.0)
    st.number_input('Insira o valor da ***Densidade da Água***', help='Entre 1,0 e 1,2',
                    step=1.0, format='%f', key='dw', min_value=0.0)

    if st.button("Salvar Parâmetros"):
        st.session_state.parametros_miller = {
            "Porosidade a Grandes Profundidades": st.session_state.pa,
            "Parâmetro de Ajuste": st.session_state.pb,
            "Taxa de Declínio da Porosidade": st.session_state.k,
            "Parâmetro de Curvatura": st.session_state.n,
            "Densidade da Matriz": st.session_state.dm,
            "Densidade da Água": st.session_state.dw,
        }
        st.success("Parâmetros salvos com sucesso!")
        return ()


def rft(fig):
    if "df_mud" in st.session_state and isinstance(st.session_state["df_mud"], pd.DataFrame):
        st.markdown("Dados importados da aba **Geopressões** (B/F/G).")
        st.dataframe(st.session_state["df_mud"], use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não foi possível importar o peso do fluido do Excel.")


@st.dialog("Direções das Tensões In Situ")
def tensoes():
    with st.container(border=True):
        # Dados iniciais vazios ou com exemplo
        tis = pd.DataFrame({
            "Profundidade (m)": [],
            "Direção SH": []
        })

        # Tabela editável
        st.session_state.tise = st.data_editor(
            tis,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )

        # Botão para confirmar e fechar a aba
        if st.button("Inserir Direção das Tensões In Situ", use_container_width=True, type="primary"):
            st.session_state.direct = True
            st.rerun()


def interpolar_direcao_sh(df_ref: pd.DataFrame, profundidades: pd.Series) -> pd.Series:
    df_ref = df_ref.copy()

    df_ref["Profundidade (m)"] = pd.to_numeric(df_ref["Profundidade (m)"], errors="coerce")
    df_ref["Direção SH"] = pd.to_numeric(df_ref["Direção SH"], errors="coerce")

    df_ref = (
        df_ref
        .dropna(subset=["Profundidade (m)", "Direção SH"])
        .sort_values("Profundidade (m)")
        .drop_duplicates(subset=["Profundidade (m)"], keep="last")
    )

    prof = pd.to_numeric(profundidades, errors="coerce").to_numpy(dtype=float)

    if df_ref.empty:
        return pd.Series(np.zeros(len(prof)), index=profundidades.index)

    if len(df_ref) == 1:
        valor = float(df_ref["Direção SH"].iloc[0]) % 360
        return pd.Series(np.full(len(prof), valor), index=profundidades.index)

    x = df_ref["Profundidade (m)"].to_numpy(dtype=float)
    ang = np.radians(df_ref["Direção SH"].to_numpy(dtype=float) % 360)

    sin_i = np.interp(prof, x, np.sin(ang))
    cos_i = np.interp(prof, x, np.cos(ang))

    direcao = np.degrees(np.arctan2(sin_i, cos_i)) % 360

    return pd.Series(direcao, index=profundidades.index)



@st.dialog("Relação das tensões horizontais", width="large")
def rel_hor():
    with st.container(border=True):
        tis = pd.DataFrame({
            "Profundidade (m)": [],
            "SH% Sobrecarga": [],
            "Sh% Sobrecarga": []
        })

        st.session_state.rel_hor_df = st.data_editor(
            tis,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="rel_hor_editor"
        )

        if st.button(
            "Inserir Relação das Tensões Horizontais",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.rel_hor = True
            st.rerun()

if "frac" not in st.session_state:
    st.session_state.frac = 0.1

if "gauss" not in st.session_state:
    st.session_state.gauss = 50

def suavizar(x, y):
    x = np.asarray(x)
    y = np.asarray(y)

    # Proteção básica
    if len(y) < 3:
        return y

    frac = st.session_state.frac
    sigma = st.session_state.gauss

    # Detecta patamar
    razao_unicos = np.unique(y).size / len(y)
    dy = np.abs(np.diff(y))
    patamar = np.mean(dy < 1e-3)

    if razao_unicos < 0.1 or patamar > 0.7:
        y_suav = gaussian_filter1d(y, sigma=sigma)
    else:
        y_suav = lowess(y, x, frac=frac, return_sorted=False)

    return y_suav

def suavizar_2(x, y, grad_medio, largura_transicao=100):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    y_out = y.copy()

    z_ini = float(st.session_state.anormal)

    # Parte rasa
    mask_raso = x < z_ini

    if np.isscalar(grad_medio):
        y_out[mask_raso] = grad_medio
        valor_ref = float(grad_medio)
    else:
        grad_medio = np.asarray(grad_medio, dtype=float)
        y_out[mask_raso] = grad_medio[mask_raso]

        if mask_raso.any():
            valor_ref = y_out[mask_raso][-1]
        else:
            valor_ref = grad_medio[0]

    # Parte profunda
    mask_prof = x >= z_ini

    if mask_prof.sum() < 3:
        return y_out

    x_seg = x[mask_prof]
    y_seg = y[mask_prof]

    frac = st.session_state.frac
    sigma = st.session_state.gauss

    razao_unicos = np.unique(y_seg).size / len(y_seg)
    dy = np.abs(np.diff(y_seg))
    patamar = np.mean(dy < 1e-3)

    if razao_unicos < 0.1 or patamar > 0.7:
        y_suav = gaussian_filter1d(y_seg, sigma=sigma)
    else:
        y_suav = lowess(
            y_seg,
            x_seg,
            frac=frac,
            return_sorted=False
        )

    # Corrige o início da curva suavizada para não gerar degrau
    offset = valor_ref - y_suav[0]

    dist = x_seg - z_ini

    peso_offset = 1 - (dist / largura_transicao)
    peso_offset = np.clip(peso_offset, 0, 1)

    y_suav_corrigido = y_suav + offset * peso_offset

    y_out[mask_prof] = y_suav_corrigido

    return y_out

# Constantes globais
RAIO = 1
ALTURA = 2
DESLOCAMENTO_TEXTO = 0.1
VETOR_TAU_LABEL = "τ_rθ"


def gerar_cilindro_inclinado(r=1, h=5, n_theta=50, n_z=50, incl=30, azi=45, angulo_central=0):
    theta = np.linspace(0, 2 * np.pi, n_theta)
    z = np.linspace(-h / 2, h / 2, n_z)
    theta, z = np.meshgrid(theta, z)
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    incl_rad = np.deg2rad(incl)
    azi_rad = np.deg2rad(azi + 180)

    azi_rad2 = np.deg2rad(azi + 180)

    # Vetor direção (unitário)
    u = np.array([
        np.sin(incl_rad) * np.cos(azi_rad),
        np.sin(incl_rad) * np.sin(azi_rad),
        np.cos(incl_rad)
    ])

    c = np.array([
        np.sin(incl_rad) * np.cos(azi_rad2),
        np.sin(incl_rad) * np.sin(azi_rad2),
        np.cos(incl_rad)
    ])

    v0 = np.array([0, 0, 1])
    v1 = u
    axis = np.cross(v0, v1)
    norm_axis = np.linalg.norm(axis)
    if norm_axis != 0:
        axis = axis / norm_axis
        angle = np.arccos(np.clip(np.dot(v0, v1), -1, 1))
        K = np.array([[0, -axis[2], axis[1]],
                      [axis[2], 0, -axis[0]],
                      [-axis[1], axis[0], 0]])
        R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
    else:
        R = np.eye(3)

    # Rotacionar cilindro
    xyz = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=0)
    xyz_rot = R @ xyz
    x_rot = xyz_rot[0].reshape(x.shape)
    y_rot = xyz_rot[1].reshape(y.shape)
    z_rot = xyz_rot[2].reshape(z.shape)

    # Diferença angular em relação ao ângulo central
    diff = np.angle(np.exp(1j * (theta - angulo_central)))  # entre -pi e pi
    diff = np.abs(diff)  # distância angular positiva

    # Normalizar (0 até 180 graus -> 0 até 1)
    norm_diff = diff / np.pi

    return x_rot, y_rot, z_rot, u, R, norm_diff


def curva_tau_rtheta():
    theta = np.linspace(0, np.pi / 2, 20)
    r = 1.0
    z = np.ones_like(theta)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y, z


def ponta_seta(xf, yf, zf):
    dx, dy = 0.1, 0.1
    x_v = [dx - 0.1, xf + 0.2, None, dx - 0.1, xf + 0.2]
    y_v = [yf, yf - dy, None, yf, yf + dy]
    z_v = [zf, zf, None, zf, zf]
    return x_v, y_v, z_v


def adicionar_linha(fig, x_linha, y_linha, z_linha):
    fig.add_trace(go.Scatter3d(
        x=x_linha, y=y_linha, z=z_linha,
        mode='lines',
        line=dict(color='black', width=3, dash='dash'),
        showlegend=False
    ))


def adicionar_setor_circular(fig, angulo, R, origem=(0, 0, 0)):
    """
    Adiciona um setor circular que acompanha a rotação do cilindro.

    - angulo: ângulo em radianos
    - R: matriz de rotação do cilindro
    - origem: ponto de onde o setor parte (ex: base ou centro do cilindro)
    """
    ox, oy, oz = origem

    # ----- Superfície do setor -----
    n = 50
    theta = np.linspace(0, angulo, n)
    r = 1
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    z = np.zeros_like(x)

    # fechar setor
    x = np.append(x, 0)
    y = np.append(y, 0)
    z = np.append(z, 0)

    # rotacionar pontos
    pts = np.vstack([x, y, z])  # (3, N)
    pts_rot = R @ pts  # aplicar rotação
    x_rot, y_rot, z_rot = pts_rot[0] + ox, pts_rot[1] + oy, pts_rot[2] + oz

    # mesh do setor
    i = list(range(n - 1))
    j = list(range(1, n))
    k = [n] * (n - 1)
    fig.add_trace(
        go.Mesh3d(x=x_rot, y=y_rot, z=z_rot,
                  i=i, j=j, k=k,
                  color='black', opacity=0.4,
                  name='Ângulo θ', showlegend=True)
    )

    # ----- Linha circular (raio interno) -----
    n = 100
    theta = np.linspace(0, angulo, n)
    x = 0.5 * np.cos(theta)
    y = 0.5 * np.sin(theta)
    z = np.zeros_like(x)

    pts = np.vstack([x, y, z])
    pts_rot = R @ pts
    x_rot, y_rot, z_rot = pts_rot[0] + ox, pts_rot[1] + oy, pts_rot[2] + oz

    fig.add_trace(go.Scatter3d(
        x=x_rot, y=y_rot, z=z_rot,
        mode="lines",
        line=dict(color="black", width=6),
        name="Dir. Tensões Principais",
        showlegend=True
    ))

    # ----- Label do ângulo -----
    theta_label = angulo / 2
    x = (0.5 + 0.05) * np.cos(theta_label)
    y = (0.5 + 0.05) * np.sin(theta_label)
    z = 0

    pts = np.array([[x], [y], [z]])
    pts_rot = R @ pts
    x_rot, y_rot, z_rot = pts_rot[0] + ox, pts_rot[1] + oy, pts_rot[2] + oz
    if st.session_state.show:
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="text",
            text=[f"θ = {np.rad2deg(angulo):.1f}º"],
            textfont=dict(size=16, color="black"),
            showlegend=False
        ))


def gerar_setor_fora_inclinado(fig, angulo, R, r_int=1, r_ext=2, origem=(0, 0, 0)):
    """
    Gera um setor circular externo que acompanha a rotação do poço/cilindro.

    - angulo: ângulo do setor (rad)
    - R: matriz de rotação do poço/cilindro
    - r_int: raio interno (normalmente o raio do cilindro)
    - r_ext: raio externo (até onde o setor se estende)
    - origem: posição da base do cilindro/poço
    """
    ox, oy, oz = origem
    n = 100
    theta = np.linspace(0, angulo, n)

    # Arco externo
    x_ext = r_ext * np.cos(theta)
    y_ext = r_ext * np.sin(theta)
    z_ext = np.zeros_like(x_ext)
    r_ext_arr = np.full_like(x_ext, r_ext)

    # Arco interno
    x_int = r_int * np.cos(theta)
    y_int = r_int * np.sin(theta)
    z_int = np.zeros_like(x_int)
    r_int_arr = np.full_like(x_int, r_int)

    # Junta arcos
    x = np.concatenate([x_ext, x_int])
    y = np.concatenate([y_ext, y_int])
    z = np.concatenate([z_ext, z_int])
    r = np.concatenate([r_ext_arr, r_int_arr])

    # --- aplica rotação ---
    pts = np.vstack([x, y, z])  # shape (3, 2*n)
    pts_rot = R @ pts
    x_rot = pts_rot[0] + ox
    y_rot = pts_rot[1] + oy
    z_rot = pts_rot[2] + oz

    # Triangulação
    i, j, k = [], [], []
    for t in range(n - 1):
        i.append(t)
        j.append(t + 1)
        k.append(n + t)

        i.append(t + 1)
        j.append(n + t + 1)
        k.append(n + t)

    # Mesh3D com escala de cor
    fig.add_trace(go.Mesh3d(
        x=x_rot, y=y_rot, z=z_rot,
        i=i, j=j, k=k,
        intensity=r,
        colorscale="Jet",
        reversescale=True,
        showscale=False,
        opacity=0.5,
        name="Setor sombreado externo"
    ))


def adicionar_eixos(fig):
    # Eixo X
    fig.add_trace(go.Scatter3d(
        x=[-2, 2], y=[0, 0], z=[0, 0],
        mode="lines",
        line=dict(color="red", width=4, dash="dot"),
        name="N/S"
    ))
    fig.add_trace(go.Scatter3d(
        x=[2, 2], y=[0, 0], z=[0, 0],
        mode="text",
        text=["N"],  # aqui você pode colocar 'θ', 'σθ' etc.
        textfont=dict(size=16, color="black"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[-2, -2], y=[0, 0], z=[0, 0],
        mode="text",
        text=["S"],  # aqui você pode colocar 'θ', 'σθ' etc.
        textfont=dict(size=16, color="black"),
        showlegend=False
    ))

    # Eixo Y
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-2, 2], z=[0, 0],
        mode="lines",
        line=dict(color="green", width=4, dash="dot"),
        name="E/W"
    ))

    # Eixo Z
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[-2, 2],
        mode="lines",
        line=dict(color="blue", width=4, dash="dot"),
        name="Eixo Z"
    ))

    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[2, 2], z=[0, 0],
        mode="text",
        text=["E"],  # aqui você pode colocar 'θ', 'σθ' etc.
        textfont=dict(size=16, color="black"),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[-2, -2], z=[0, 0],
        mode="text",
        text=["W"],  # aqui você pode colocar 'θ', 'σθ' etc.
        textfont=dict(size=16, color="black"),
        showlegend=False
    ))


def adicionar_cone_setor(fig, angulo_setor, R, z_local=0, r=1.0, orient='axial',color='Reds', size_ref=0.3, nome='Cone',desloc_radial=0.0, desloc_tang=0.0, desloc_axial=0.0, valor=0.0):
    """
    desloc_radial: empurra para fora/pra dentro do poço
    desloc_tang: gira tangencialmente (ao redor do eixo)
    desloc_axial: sobe/baixa ao longo do eixo do poço
    """

    th = angulo_setor
    # --- posição local antes da rotação ---
    x0 = (r + desloc_radial) * np.cos(th) - desloc_tang * np.sin(th)
    y0 = (r + desloc_radial) * np.sin(th) + desloc_tang * np.cos(th)
    z0 = z_local + desloc_axial

    pos_local = np.array([[x0], [y0], [z0]])
    pos_rot = R @ pos_local
    x_rot, y_rot, z_rot = pos_rot[:, 0]

    # --- direção ---
    radial = np.array([[np.cos(th)], [np.sin(th)], [0]])
    tangential = np.array([[-np.sin(th)], [np.cos(th)], [0]])
    axial = np.array([[0], [0], [1]])
    d = ''
    if orient.lower() in ['radial']:
        d = radial
    elif orient.lower() in ['tangential', 'tangencial']:
        d = tangential
    elif orient.lower() in ['axial', 'vertical']:
        d = axial

    d_rot = R @ d
    if orient == "axial":
        u, v, w = -d_rot[:, 0]
    else:
        u, v, w = d_rot[:, 0]

    # --- adiciona cone ---
    fig.add_trace(go.Cone(
        x=[x_rot], y=[y_rot], z=[z_rot],
        u=[u], v=[v], w=[w],
        sizemode="absolute", sizeref=size_ref,
        colorscale=color, showscale=False,
        name=nome, anchor="tail"
    ))

    if st.session_state.show:
        fig.add_trace(go.Scatter3d(
            x=[x_rot], y=[y_rot], z=[z_rot],
            mode="text",
            text=[f"<b><i>{nome}={valor:.1f} psi</i></b>"],  # HTML para negrito/itálico
            textposition="top center",
            textfont=dict(
                family="Arial, sans-serif",
                size=16,
                color="black"
            )
        ))


def adicionar_setas_parede(fig, raio, angulo, z, sig_h, sig_H, mostrar_texto=True):
    # Corpo da seta da esquerda (do ponto (0, 1.5, 1) até (0, 1, 1))
    # Base da seta (na parede do cilindro)
    x_base = raio * np.cos(angulo) + 0.5 * np.cos(angulo)
    y_base = raio * np.sin(angulo) + 0.5 * np.sin(angulo)

    # Ponta da seta (um pouco mais para dentro)
    x_ponta = (raio - 0.5) * np.cos(angulo) + 0.5 * np.cos(angulo)
    y_ponta = (raio - 0.5) * np.sin(angulo) + 0.5 * np.sin(angulo)

    # Corpo da seta
    fig.add_trace(go.Scatter3d(
        x=[x_base, x_ponta],
        y=[y_base, y_ponta],
        z=[z, z],
        mode="lines",
        line=dict(color="blue", width=6),
        showlegend=False
    ))

    # Ponta da seta (abertura)
    desloc = 0.1
    fig.add_trace(go.Scatter3d(
        x=[1.1 * x_ponta - desloc * np.sin(angulo),
           x_ponta,
           1.1 * x_ponta + desloc * np.sin(angulo)],
        y=[1.1 * y_ponta + desloc * np.cos(angulo),
           y_ponta,
           1.1 * y_ponta - desloc * np.cos(angulo)],
        z=[z, z, z],
        mode="lines",
        line=dict(color="blue", width=6),
        showlegend=mostrar_texto,
        name="σH" if mostrar_texto else None
    ))

    if st.session_state.show:
        fig.add_trace(go.Scatter3d(
            x=[x_base, x_ponta],
            y=[y_base, y_ponta],
            z=[z, z],
            mode="text",
            text=[f"<b><i>σH={sig_H:.1f} psi</i></b>"],  # HTML para negrito/itálico
            textposition="top center",
            textfont=dict(
                family="Arial, sans-serif",
                size=16,
                color="black"
            )
        ))

    x_base = raio * np.cos(angulo + np.pi / 2) + 0.5 * np.cos(angulo + np.pi / 2)
    y_base = raio * np.sin(angulo + np.pi / 2) + 0.5 * np.sin(angulo + np.pi / 2)

    # Ponta da seta (um pouco mais para dentro)
    x_ponta = (raio - 0.5) * np.cos(angulo + np.pi / 2) + 0.5 * np.cos(angulo + np.pi / 2)
    y_ponta = (raio - 0.5) * np.sin(angulo + np.pi / 2) + 0.5 * np.sin(angulo + np.pi / 2)

    # Corpo da seta 2
    fig.add_trace(go.Scatter3d(
        x=[x_base, x_ponta],
        y=[y_base, y_ponta],
        z=[z, z],
        mode="lines",
        line=dict(color="red", width=6),
        showlegend=False
    ))

    # Ponta da seta (abertura)
    desloc = 0.1
    fig.add_trace(go.Scatter3d(
        x=[1.1 * x_ponta - desloc * np.sin(angulo + np.pi / 2),
           x_ponta,
           1.1 * x_ponta + desloc * np.sin(angulo + np.pi / 2)],
        y=[1.1 * y_ponta + desloc * np.cos(angulo + np.pi / 2),
           y_ponta,
           1.1 * y_ponta - desloc * np.cos(angulo + np.pi / 2)],
        z=[z, z, z],
        mode="lines",
        line=dict(color="red", width=6),
        showlegend=mostrar_texto,
        name="σh" if mostrar_texto else None
    ))

    if st.session_state.show:
        fig.add_trace(go.Scatter3d(
            x=[x_base, x_ponta],
            y=[y_base, y_ponta],
            z=[z, z],
            mode="text",
            text=[f"<b><i>σh={sig_h:.1f} psi</i></b>"],  # HTML para negrito/itálico
            textposition="top center",
            textfont=dict(
                family="Arial, sans-serif",
                size=16,
                color="black"
            )
        ))


def criar_grafico(parametros, sr, sig_t, sig_a, sig_h, sig_H, ang_theta, tvd, ang_azi, ang_inc, ra, op, ang_horizontal, view, lg):
    fig = go.Figure()

    x, y, z, u, R, cont = gerar_cilindro_inclinado(r=1, h=2, incl=ang_inc, azi=ang_azi,
                                                   angulo_central=np.deg2rad(ang_theta))

    if st.session_state.ff:
        colorscale = [
            [0.0, "red"],  # no ponto central
            [0.15, "yellow"],
            [0.6, "green"],
            [0.85, "yellow"],
            [1.0, "red"]  # oposto
        ]

        fig.add_trace(go.Surface(
            x=x, y=y, z=z,
            surfacecolor=cont,
            colorscale=colorscale,
            opacity=op,
            showscale=False,
            hoverinfo="skip",
            name="Paredes do Poço"
        ))
    else:
        fig.add_trace(go.Surface(x=x, y=y, z=z,
                                 opacity=0.5,
                                 colorscale="Greys",
                                 showscale=False))

    if "Sistemas de coordenadas do poço" in parametros:
        eixos = np.eye(3)
        # Rotacionar eixos
        eixos_rot = R @ eixos.T

        cores = ["black", "black", "black"]
        nomes = ["x", "y", "z"]

        for i in range(3):
            fig.add_trace(go.Scatter3d(
                x=[0, eixos_rot[0, i]],
                y=[0, eixos_rot[1, i]],
                z=[0, eixos_rot[2, i]],
                mode="lines+text",
                line=dict(color=cores[i], width=6, dash="solid"),
                text=[None, nomes[i]],
                textfont=dict(size=12, color="black", family="Arial Black"),
                showlegend=False,
                textposition="top center",
                name=nomes[i]
            ))

    if st.session_state.arr:
        # Gera setor sombreado
        gerar_setor_fora_inclinado(fig, np.deg2rad(360), R=R, r_ext=ra)
    if "Profundidade" in parametros:
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[1, 0],
            mode="text",
            text=[f"TVD={tvd:.1f} m"],  # aqui você pode colocar 'θ', 'σθ' etc.
            textfont=dict(size=16, color="black"),
            showlegend=False
        ))
    if "σθ" in parametros:
        adicionar_cone_setor(fig, np.deg2rad(ang_theta), R=R, r=1.0,
                             orient='tangential', color='Blues', nome='σθ', desloc_tang=-0.3, valor=sig_t)
    if "σr" in parametros:
        adicionar_cone_setor(fig, np.deg2rad(ang_theta), R=R, r=1.0,
                             orient='radial', color='Reds', nome='σr', desloc_radial=-0.3, valor=sr)
    if "σa" in parametros:
        adicionar_cone_setor(fig, np.deg2rad(ang_theta), R=R, r=1.0,
                             orient='axial', color='Greens', nome='σa', desloc_axial=0.3, valor=sig_a)
    if "Direção do poço" in parametros:
        x_end, y_end = u[0] * 1, u[1] * 1
        fig.add_trace(go.Scatter3d(
            x=[0, -x_end],
            y=[0, -y_end],
            z=[0, 0],
            mode="lines",
            line=dict(color="brown", width=6),
            name="Azimute"
        ))

        desloc = 0.1
        fig.add_trace(go.Scatter3d(
            x=[(x_end + 1.3 * np.cos(np.deg2rad(ang_azi))) + desloc * u[1],
               -x_end,
               (x_end + 1.3 * np.cos(np.deg2rad(ang_azi))) - desloc * u[1]],
            y=[(y_end + 1.3 * np.sin(np.deg2rad(ang_azi))) - desloc * u[0],
               -y_end,
               (y_end + 1.3 * np.sin(np.deg2rad(ang_azi))) + desloc * u[0]],
            z=[0, 0, 0],
            mode="lines",
            line=dict(color="brown", width=6),
            showlegend=False,
            name="AZI"
        ))
        if ang_inc > 0:
            fig.add_trace(go.Scatter3d(
                x=[-x_end, -x_end],
                y=[-y_end, -y_end],
                z=[0, 0],
                mode="text",
                text=[F"AZI={ang_azi:.1f}º"],
                textfont=dict(size=16, color="black"),
                showlegend=False
            ))
    if "Coordenadas geográficas" in parametros:
        adicionar_eixos(fig)
    if "Tensões Horizontais" in parametros:
        adicionar_setas_parede(fig, 2, np.radians(ang_horizontal), 0, sig_h, sig_H)
    if "Dir. Tensões principais" in parametros:
        adicionar_setor_circular(fig, angulo=np.deg2rad(ang_theta), R=R, origem=(0, 0, 0))

    if lg == "Sim":
        ax = True
    else:
        ax = False
    if st.session_state.arr:
        margem = ra
    else:
        margem = 0

    fig.update_layout(
        showlegend=False,
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=0,
            yanchor='bottom'
        )
    )

    if view == "Vista de planta":
        fig.update_layout(
            scene_camera=dict(
                eye=dict(x=0, y=0, z=1),
                up=dict(x=-1, y=0, z=0)
            ),

        )
    elif view == "Vista de seção N/S":
        fig.update_layout(
            scene_camera=dict(
                eye=dict(x=0, y=1, z=0)  # posição do observador
            )
        )
    elif view == "Vista de seção E/W":
        fig.update_layout(

            scene_camera=dict(
                eye=dict(x=1, y=0, z=0)  # posição do observador
            )
        )
    elif view == "Vista axial do poço":
        L = 1
        fig.update_layout(
            scene_dragmode='turntable',
            scene_camera=dict(
                eye=dict(x=-u[0] * L, y=u[1] * L, z=u[2] * L),
                center=dict(x=0, y=0, z=0),  # centro da vista
                up=dict(x=-1, y=0, z=0)
            ),
        )

    elif view == "Dentro do Poço":
        fig.update_layout(
            scene_dragmode='turntable',
            scene_camera=dict(
                eye=dict(x=0.01, y=0, z=0.01),
                center=dict(x=0, y=0, z=0.01),  # centro da vista
                up=dict(x=0, y=0, z=0)
            )
        )

    fig.update_layout(
        scene=dict(xaxis=dict(range=[margem + 3, -margem - 3], visible=ax),  # inverte eixo X
                   yaxis=dict(range=[-margem - 3, margem + 3], visible=ax),  # inverte eixo Y
                   zaxis=dict(range=[-margem - 3, margem + 3], visible=ax),
                   aspectmode="cube"),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    return fig


def normal(df, df_pp=None):
    prof_ini = float(st.session_state.rtkb)
    prof_anormal = float(st.session_state.anormal)

    val_ini = 0.0
    val_fim = float(st.session_state.get("gn", 8.5))

    coluna_prof = "Profundidade (m)"
    coluna_pp = "Gradiente de Pressão de Poros Médio (lb/gal)"
    coluna_extrap = "Linha Extrapolada"

    # Usa df_pp se for passado. Se não for, usa o próprio df.
    df_ref = df_pp if df_pp is not None else df

    prof_fim = prof_anormal

    if (
        df_ref is not None
        and isinstance(df_ref, pd.DataFrame)
        and coluna_prof in df_ref.columns
    ):
        df_aux = df_ref.copy()

        df_aux[coluna_prof] = pd.to_numeric(
            df_aux[coluna_prof],
            errors="coerce"
        )

        df_aux = (
            df_aux
            .dropna(subset=[coluna_prof])
            .sort_values(coluna_prof)
            .reset_index(drop=True)
        )

        if not df_aux.empty:
            prof_primeira_df_pp = float(df_aux[coluna_prof].iloc[0])

            # Caso 1:
            # anormal está antes do início do df_pp.
            # Mantém a lógica antiga.
            if prof_anormal < prof_primeira_df_pp:
                prof_fim = prof_anormal

                if coluna_pp in df_aux.columns:
                    df_pp_val = df_aux[[coluna_prof, coluna_pp]].copy()

                    df_pp_val[coluna_pp] = pd.to_numeric(
                        df_pp_val[coluna_pp],
                        errors="coerce"
                    )

                    df_pp_val = df_pp_val.dropna(
                        subset=[coluna_prof, coluna_pp]
                    )

                    if not df_pp_val.empty:
                        idx = (df_pp_val[coluna_prof] - prof_fim).abs().idxmin()
                        prof_fim = float(df_pp_val.loc[idx, coluna_prof])
                        val_fim = float(df_pp_val.loc[idx, coluna_pp])

            # Caso 2:
            # anormal está depois do início do df_pp.
            # A curva deve crescer somente até o começo do dado real,
            # valendo gn nesse ponto.
            else:
                if coluna_extrap in df_aux.columns:
                    serie_extrap = df_aux[coluna_extrap]

                    if serie_extrap.dtype == bool:
                        mask_real = ~serie_extrap.fillna(False)

                    elif np.issubdtype(serie_extrap.dtype, np.number):
                        mask_real = ~(serie_extrap.fillna(0).astype(int).astype(bool))

                    else:
                        mask_extrap = (
                            serie_extrap
                            .fillna(False)
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            .isin(["true", "1", "sim", "yes", "verdadeiro"])
                        )
                        mask_real = ~mask_extrap

                    df_real = df_aux[mask_real].copy()

                    if not df_real.empty:
                        prof_fim = float(df_real[coluna_prof].iloc[0])
                    else:
                        prof_fim = prof_primeira_df_pp

                else:
                    prof_fim = prof_primeira_df_pp

                val_fim = float(st.session_state.get("gn", 8.5))

    alpha = float(st.session_state.get("alfa_pp", 10))

    n = len(df)
    profundidade = np.linspace(prof_ini, prof_fim, n)

    denom = prof_fim - prof_ini

    if denom == 0:
        valores = np.full(n, np.nan)
    else:
        t = (profundidade - prof_ini) / denom
        t = np.clip(t, 0.0, 1.0)

        valores = val_ini + (val_fim - val_ini) * (
            (1 - np.exp(-alpha * t)) / (1 - np.exp(-alpha))
        )

    df_gfs = pd.DataFrame({
        "Profundidade (m)": profundidade,
        "Gradiente de Pressão de Poros (lb/gal)": valores
    })

    if prof_fim > prof_ini:
        mask_none = df_gfs["Profundidade (m)"] <= prof_ini
    else:
        mask_none = df_gfs["Profundidade (m)"] >= prof_ini

    df_gfs.loc[
        mask_none,
        "Gradiente de Pressão de Poros (lb/gal)"
    ] = None

    st.session_state.df_gfs = df_gfs

    return df_gfs


def lito(ax1, df_pp, profundidades, litologias, bases):
    try:
        label = True
        line_w = 0.8

        tipo_coluna_lito = st.session_state.get(
            "tipo_coluna_litologica_graficos",
            "Permeável / Não permeável"
        )

        if "s_gr" not in st.session_state:
            st.session_state.s_gr = False

        coluna_gr = "Raio Gama Suavizado" if st.session_state.s_gr else "Perfil Raio Gama"

        pode_gerar_perm_nao_perm = (
            tipo_coluna_lito == "Permeável / Não permeável"
            and "LBF_calc" in df_pp.columns
            and coluna_gr in df_pp.columns
            and "Profundidade (m)" in df_pp.columns
        )

        if pode_gerar_perm_nao_perm:
            profundidades_plot = []
            litologias_plot = []
            curva = df_pp[coluna_gr]
        else:
            profundidades_plot = profundidades
            litologias_plot = litologias
            curva = None

        if pode_gerar_perm_nao_perm:
            prof = [0]
            lito_t = ['Fm. Permeável']

            if curva.iloc[0] >= df_pp['LBF_calc'].iloc[0]:
                aux = 'Fm. Permeável'
            else:
                aux = 'Folhelho'

            for i, line in enumerate(df_pp['Profundidade (m)']):
                if curva.iloc[i] >= df_pp['LBF_calc'].iloc[i] and aux == 'Fm. Permeável':
                    prof.append(line)
                    lito_t.append('Folhelho')
                    aux = 'Folhelho'

                elif curva.iloc[i] <= df_pp['LBF_calc'].iloc[i] and aux == 'Folhelho':
                    prof.append(line)
                    lito_t.append('Fm. Permeável')
                    aux = 'Fm. Permeável'

            litho_tops = [[x, y] for x, y in zip(prof, lito_t)]
            label = False
            line_w = 0

        else:
            if not profundidades_plot or not litologias_plot:
                return

            litho_tops = [[x, y] for x, y in zip(profundidades_plot, litologias_plot)]
            label = True
            line_w = 0.8

        litho_intervals = []
        for i, (top, lit) in enumerate(litho_tops):
            if i < len(litho_tops) - 1:
                base = litho_tops[i + 1][0]
            else:
                base = bases

            litho_intervals.append((top, base, lit))

        df_perm_nao_perm = pd.DataFrame(
            litho_intervals,
            columns=["Topo (m)", "Base (m)", "Classificação"]
        )

        st.session_state.df_perm_nao_perm = df_perm_nao_perm

        litho_styles = {
            "Argilito": {"color": "#9ACD32", "hatch": "|||", "edgecolor": "black"},
            "Arenito": {"color": "#fff7a1", "hatch": "...", "edgecolor": "black"},
            "Fm. Permeável": {"color": "#fff7a1", "hatch": "...", "edgecolor": "black"},
            "Folhelho": {"color": "#2f4f4f", "hatch": None, "edgecolor": "black"},
            "Siltito": {"color": "#8b4513", "hatch": None, "edgecolor": "black"},
            "Diamictito": {"color": "#E97451", "hatch": "..", "edgecolor": "black"},
            "Conglomerado": {"color": "#ffb347", "hatch": "oo", "edgecolor": "black"},
            "Anidrita / Gipsita": {"color": "#E6E6FA", "hatch": "///", "edgecolor": "black"},
            "Halita": {"color": "#ffffff", "hatch": None, "edgecolor": "black"},
            "Calcário": {"color": "#a7c7e7", "hatch": "///", "edgecolor": "#003366"},
            "Carbonato": {"color": "#cfe8f3", "hatch": "xx", "edgecolor": "#003366"},
            "Calcissiltito": {"color": "#D8BFD8", "hatch": "---", "edgecolor": "black"},
            "Calcarenito": {"color": "#F5DEB3", "hatch": "...", "edgecolor": "black"},
            "Calcirrudito": {"color": "#4682B4", "hatch": "oo", "edgecolor": "black"},
            "Coquina": {"color": "#FFDEAD", "hatch": "oo", "edgecolor": "black"},
            "Dolomito": {"color": "#C2B280", "hatch": "xx", "edgecolor": "black"},
            "Basalto": {"color": "#2b2b2b", "hatch": None, "edgecolor": "black"},
            "Diabásio": {"color": "#556B2F", "hatch": "++", "edgecolor": "black"},
        }

        ax1.set_xlim(0, 0.5)
        ax1.set_ylim(st.session_state.y_max_s, st.session_state.y_min_s)
        ax1.set_xticks([])
        ax1.tick_params(axis='y', which='both', left=False, labelleft=False)
        ax1.set_title("Litologia", fontsize=10, fontweight='bold')

        for top, base, lit in litho_intervals:
            style = litho_styles.get(
                lit,
                {"color": "gray", "hatch": None, "edgecolor": "black"}
            )

            rect = mpatches.Rectangle(
                (0, top),
                width=0.5,
                height=base - top,
                facecolor=style["color"],
                edgecolor=style["edgecolor"],
                hatch=style["hatch"],
                linewidth=line_w,
            )

            ax1.add_patch(rect)

            mid = (top + base) / 2

            if label:
                txt = ax1.text(
                    0.25,
                    mid,
                    lit,
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color="black",
                    zorder=5,
                    rotation=0
                )

                txt.set_path_effects([
                    path_effects.Stroke(linewidth=1.5, foreground='white'),
                    path_effects.Normal()
                ])

    except Exception as e:
        st.error(f"Erro em lito(): {e}")
        raise


def idade_formacao(ax, df_idade, y_max):

    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_ylim(y_max, 0)

    idades_unicas = df_idade["Idade"].unique()
    cmap = plt.cm.get_cmap("Accent", len(idades_unicas))

    cores = {
        idade: cmap(i)
        for i, idade in enumerate(idades_unicas)
    }

    for _, row in df_idade.iterrows():
        ax.fill_betweenx(
            [row["Topo (m)"], row["Base (m)"]],
            0, 1,
            color=cores[row["Idade"]],
            edgecolor="black"
        )

        ax.text(
            0.5,
            (row["Topo (m)"] + row["Base (m)"]) / 2,
            row["Idade"],
            ha="center",
            va="center",
            fontsize=8,
            rotation=90,
            fontweight="bold",
            color="black",
            path_effects=[
                pe.Stroke(linewidth=3, foreground="white"),
                pe.Normal()
            ]
        )

    ax.set_title("Período", fontsize=8, fontweight="bold")


def add_watermark(ax, logo_path="logo2.png", xy=(0.80, 0.25), zoom=0.20, alpha=0.10, zorder=0):
    """
    Marca d'água robusta:
    - NÃO distorce em eixo log (usa ax.transAxes)
    - transparência SEMPRE muda (ajusta canal alpha do RGBA)
    """
    if not os.path.exists(logo_path):
        return

    # lê com PIL e força RGBA
    im = Image.open(logo_path).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)

    # aplica alpha global multiplicando o canal A (0..255)
    arr[..., 3] = arr[..., 3] * float(alpha)
    arr[..., 3] = np.clip(arr[..., 3], 0, 255)

    arr = arr.astype(np.uint8)

    oi = OffsetImage(arr, zoom=zoom)  # aqui já vai com alpha aplicado
    ab = AnnotationBbox(
        oi,
        xy=xy,
        xycoords=ax.transAxes,   # independe de log/linear
        frameon=False,
        box_alignment=(0.5, 0.5),
        zorder=zorder
    )
    ax.add_artist(ab)


def draw_footer(c, width, footer_y):
    c.line(30, footer_y, width - 30, footer_y)


def salvar_fig_para_pdf(fig, path, dpi=200):
    # salva com boa resolução e recorte certinho (evita “distorção”/borrado)
    fig.savefig(
        path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )


def desenhar_imagem_no_pdf(c, img_path, left, right, top, bottom, titulo=None):
    img = Image.open(img_path)
    img_w_px, img_h_px = img.size

    available_width = right - left
    available_height = top - bottom

    scale = min(available_width / img_w_px, available_height / img_h_px)

    img_w = img_w_px * scale
    img_h = img_h_px * scale

    x_pos = left + (available_width - img_w) / 2
    y_pos = top - img_h

    if titulo:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(left + available_width / 2, top + 6, titulo)

    c.drawImage(
        img_path,
        x_pos,
        y_pos,
        width=img_w,
        height=img_h,
        preserveAspectRatio=True,
        mask="auto"
    )

    return y_pos - 20


def desenhar_fig_plotly_no_pdf(c, fig_plotly, left, right, top, bottom, titulo=None, scale=1.5):
    import io

    img_bytes = fig_plotly.to_image(format="png", scale=scale)
    img_buffer = io.BytesIO(img_bytes)
    img_reader = ImageReader(img_buffer)

    img_w_px, img_h_px = img_reader.getSize()
    available_width = right - left
    available_height = top - bottom

    scale_factor = min(available_width / img_w_px, available_height / img_h_px)

    img_w = img_w_px * scale_factor
    img_h = img_h_px * scale_factor

    x_pos = left + (available_width - img_w) / 2
    y_pos = top - img_h

    if titulo:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(left + available_width / 2, top + 6, titulo)

    c.drawImage(
        img_reader,
        x_pos,
        y_pos,
        width=img_w,
        height=img_h,
        preserveAspectRatio=True,
        mask="auto"
    )

    return y_pos - 20


def desenhar_fig_mpl_no_pdf(c, fig, left, right, top, bottom, titulo=None, dpi=130):
    import io
    from reportlab.lib.utils import ImageReader

    img_buffer = io.BytesIO()
    fig.savefig(
        img_buffer,
        format="png",
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight"
    )
    img_buffer.seek(0)

    img_reader = ImageReader(img_buffer)
    img_width_px, img_height_px = img_reader.getSize()

    available_width = right - left
    available_height = top - bottom

    scale = min(available_width / img_width_px, available_height / img_height_px)

    img_width = img_width_px * scale
    img_height = img_height_px * scale

    x_pos = left + (available_width - img_width) / 2
    y_pos = top - img_height

    if titulo:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(left + available_width / 2, top + 6, titulo)

    c.drawImage(
        img_reader,
        x_pos,
        y_pos,
        width=img_width,
        height=img_height,
        preserveAspectRatio=True,
        mask="auto"
    )

    return y_pos - 20


def draw_justified_line(c, line, x, y, max_width, font_name="Helvetica", font_size=10):
    words = line.split()

    # Se tiver só uma palavra, não tem como justificar
    if len(words) <= 1:
        c.drawString(x, y, line)
        return

    text_width = sum(c.stringWidth(w, font_name, font_size) for w in words)

    total_spaces = len(words) - 1
    extra_space = (max_width - text_width) / total_spaces

    x_atual = x

    for i, word in enumerate(words):
        c.drawString(x_atual, y, word)
        word_width = c.stringWidth(word, font_name, font_size)

        if i < len(words) - 1:
            x_atual += word_width + extra_space


def draw_wrapped_text(
    c,
    text,
    x,
    y,
    max_width,
    line_height=12,
    font_name="Helvetica",
    font_size=10,
    align="left"
):
    if not text:
        return y

    c.setFont(font_name, font_size)

    paragraphs = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for p in paragraphs:
        if p.strip() == "":
            y -= line_height
            continue

        words = p.split()
        line = ""
        linhas_paragrafo = []

        for w in words:
            test = (line + " " + w).strip()

            if c.stringWidth(test, font_name, font_size) <= max_width:
                line = test
            else:
                if line:
                    linhas_paragrafo.append(line)
                line = w

        if line:
            linhas_paragrafo.append(line)

        for i, linha in enumerate(linhas_paragrafo):
            ultima_linha = i == len(linhas_paragrafo) - 1

            if align == "justify" and not ultima_linha:
                draw_justified_line(
                    c=c,
                    line=linha,
                    x=x,
                    y=y,
                    max_width=max_width,
                    font_name=font_name,
                    font_size=font_size
                )
            else:
                c.drawString(x, y, linha)

            y -= line_height

    return y


def _aprox(a, b, tol=1e-2):
    try:
        if a is None or b is None:
            return False

        if pd.isna(a) or pd.isna(b):
            return False

        return abs(float(a) - float(b)) <= float(tol)

    except Exception:
        return False


def _classificar_falha_no_limite(row, ppg, lado):
    if row is None or ppg is None or pd.isna(ppg):
        return ""

    if lado == "inferior":
        ti = row.get("Tração Inferior", None)
        ciA = row.get("Comp Inferior σθA", None)
        ciB = row.get("Comp Inferior σθB", None)

        if _aprox(ppg, ti):
            return "Modo de falha no limite: Tração (limite inferior)"
        if _aprox(ppg, ciA):
            return "Modo de falha no limite: Colapso (σθA) – limite inferior"
        if _aprox(ppg, ciB):
            return "Modo de falha no limite: Colapso (σθB) – limite inferior"
        return "Modo de falha no limite: Limite inferior atingido"

    # superior
    tsA = row.get("Tração Superior (σθA)", None)
    tsB = row.get("Tração Superior (σθB)", None)
    csA = row.get("Comp Superior σθA", None)
    csB = row.get("Comp Superior σθB", None)

    if _aprox(ppg, tsA):
        return "Modo de falha no limite: Tração (σθA) – limite superior"
    if _aprox(ppg, tsB):
        return "Modo de falha no limite: Tração (σθB) – limite superior"
    if _aprox(ppg, csA):
        return "Modo de falha no limite: Compressão (σθA) – limite superior"
    if _aprox(ppg, csB):
        return "Modo de falha no limite: Compressão (σθB) – limite superior"
    return "Modo de falha no limite: Limite superior atingido"


def _ler_trajetoria_do_xlsm(wb, modo: str) -> pd.DataFrame:
    """
    Lê diretamente por célula:
    - Planejada: header em B5:C5:D5 e dados em B6:C6:D...
    - Executada: header em K5:L5:M5 e dados em K6:L6:M...
    Retorna DF padronizado com colunas MD, Inc, Azi.
    """

    if "Trajetória" not in wb.sheetnames:
        raise ValueError("A aba 'Trajetória' não existe no arquivo.")

    ws = wb["Trajetória"]

    if modo == "Executada":
        col_md, col_inc, col_azi = "K", "L", "M"
    else:
        col_md, col_inc, col_azi = "B", "C", "D"

    h_md = ws[f"{col_md}6"].value
    h_inc = ws[f"{col_inc}6"].value
    h_azi = ws[f"{col_azi}6"].value

    def _norm(x):
        return str(x).strip().lower() if x is not None else ""

    if not (
        "md" in _norm(h_md)
        and ("incl" in _norm(h_inc) or "inc" in _norm(h_inc))
        and ("az" in _norm(h_azi) or "azim" in _norm(h_azi))
    ):
        raise ValueError(
            f"Header não bate no esperado. Lido em {col_md}5:{col_azi}5 -> "
            f"{[h_md, h_inc, h_azi]}. "
            f"Confirme se o header está mesmo na linha 5 (Excel)."
        )

    rows = []
    r = 6
    while r <= ws.max_row:
        md = ws[f"{col_md}{r}"].value
        inc = ws[f"{col_inc}{r}"].value
        azi = ws[f"{col_azi}{r}"].value

        if md is None or md == "":
            break

        rows.append((md, inc, azi))
        r += 1

    df = pd.DataFrame(rows, columns=["MD", "Inc", "Azi"])

    df["MD"] = pd.to_numeric(df["MD"], errors="coerce")
    df["Inc"] = pd.to_numeric(df["Inc"], errors="coerce")
    df["Azi"] = pd.to_numeric(df["Azi"], errors="coerce")

    df = df.dropna(subset=["MD", "Inc", "Azi"]).sort_values("MD").reset_index(drop=True)

    if df.empty:
        raise ValueError(f"Nenhum dado direcional encontrado em {col_md}6:{col_azi}...")

    if (df["MD"].diff().fillna(1) <= 0).any():
        raise ValueError("Coluna MD deve ser estritamente crescente.")

    return df


def _calcular_trajetoria_min_curvatura(df_traj: pd.DataFrame) -> pd.DataFrame:
    df = df_traj.copy()

    df = df.rename(columns={
        "Profundidade": "MD",
        "Inc (°)": "Inc",
        "Azi (°)": "Azi"
    })

    colunas_req = ["MD", "Inc", "Azi"]
    faltantes = [c for c in colunas_req if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes na trajetória: {', '.join(faltantes)}")

    for c in colunas_req:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=colunas_req).sort_values("MD").reset_index(drop=True)

    if df.empty:
        raise ValueError("Trajetória vazia após limpeza dos dados.")

    if (df["MD"].diff().fillna(1) <= 0).any():
        raise ValueError("A coluna MD da trajetória deve ser estritamente crescente.")

    MD = df["MD"].to_numpy(dtype=float)
    Inc = np.radians(df["Inc"].to_numpy(dtype=float))
    Azi = np.radians(df["Azi"].to_numpy(dtype=float))

    Easting = [0.0]
    Northing = [0.0]
    TVD = [0.0]
    DLS_list = []

    for i in range(1, len(MD)):
        dMD = MD[i] - MD[i - 1]

        cosDL = (
            np.sin(Inc[i - 1]) * np.sin(Inc[i]) * np.cos(Azi[i] - Azi[i - 1])
            + np.cos(Inc[i - 1]) * np.cos(Inc[i])
        )
        cosDL = np.clip(cosDL, -1.0, 1.0)

        DL = np.arccos(cosDL)
        RF = 1.0 if DL < 1e-8 else (2.0 / DL) * np.tan(DL / 2.0)

        DLS = np.degrees(DL) * 30.0 / dMD if dMD != 0 else 0.0
        DLS_list.append(float(DLS))

        dN = 0.5 * dMD * (
            np.sin(Inc[i - 1]) * np.cos(Azi[i - 1])
            + np.sin(Inc[i]) * np.cos(Azi[i])
        ) * RF

        dE = 0.5 * dMD * (
            np.sin(Inc[i - 1]) * np.sin(Azi[i - 1])
            + np.sin(Inc[i]) * np.sin(Azi[i])
        ) * RF

        dTVD = 0.5 * dMD * (
            np.cos(Inc[i - 1]) + np.cos(Inc[i])
        ) * RF

        Easting.append(Easting[-1] + dE)
        Northing.append(Northing[-1] + dN)
        TVD.append(TVD[-1] + dTVD)

    East_arr = np.asarray(Easting, dtype=float)
    North_arr = np.asarray(Northing, dtype=float)
    afast_h = np.sqrt(East_arr ** 2 + North_arr ** 2)

    return pd.DataFrame({
        "MD": MD,
        "Inclinação (°)": np.degrees(Inc),
        "Azimute (°)": np.degrees(Azi),
        "Easting": Easting,
        "Northing": Northing,
        "TVD": TVD,
        "Dogleg Severity (°/30m)": [0.0] + DLS_list,
        "Afastamento Horizontal (m)": afast_h,
    })


def _limitar_perfilagem_ao_tvd_final(
    df_full: pd.DataFrame,
    tvd_final: float,
    col_tvd: str = "Profundidade"
) -> pd.DataFrame:
    df = df_full.copy()
    df.columns = [str(c).strip() for c in df.columns]

    if col_tvd not in df.columns:
        raise ValueError(f"A coluna '{col_tvd}' não existe na aba Perfilagens.")

    df[col_tvd] = pd.to_numeric(df[col_tvd], errors="coerce")
    df = df.dropna(subset=[col_tvd]).sort_values(col_tvd).reset_index(drop=True)

    if df.empty:
        raise ValueError("A aba Perfilagens ficou vazia após limpar a coluna de profundidade.")

    tvd_final = float(tvd_final)

    if tvd_final <= df[col_tvd].min():
        raise ValueError(
            f"O TVD final do poço ({tvd_final:.2f} m) é menor ou igual ao início da perfilagem "
            f"({df[col_tvd].min():.2f} m)."
        )

    # Se a perfilagem já termina antes do poço, não corta nada
    if df[col_tvd].max() <= tvd_final:
        return df.reset_index(drop=True)

    # Tenta converter colunas numéricas que vieram como texto
    for col in df.columns:
        if col == col_tvd:
            continue

        serie_num = pd.to_numeric(df[col], errors="coerce")

        # Só substitui se houver pelo menos algum valor numérico real
        if serie_num.notna().sum() > 0:
            df[col] = serie_num

    df_cortado = df[df[col_tvd] <= tvd_final].copy()

    # Garante uma linha exatamente no TVD final
    prof_ultima = float(df_cortado[col_tvd].iloc[-1])

    if not np.isclose(prof_ultima, tvd_final):
        linha_final = {}

        for col in df.columns:
            if col == col_tvd:
                linha_final[col] = tvd_final

            elif pd.api.types.is_numeric_dtype(df[col]):
                df_valid = df[[col_tvd, col]].dropna()

                if len(df_valid) >= 2:
                    linha_final[col] = float(np.interp(
                        tvd_final,
                        df_valid[col_tvd].to_numpy(dtype=float),
                        df_valid[col].to_numpy(dtype=float)
                    ))
                elif len(df_valid) == 1:
                    linha_final[col] = df_valid[col].iloc[0]
                else:
                    linha_final[col] = np.nan

            else:
                valores_anteriores = df.loc[df[col_tvd] <= tvd_final, col].dropna()
                linha_final[col] = (
                    valores_anteriores.iloc[-1]
                    if not valores_anteriores.empty
                    else np.nan
                )

        df_cortado = pd.concat(
            [df_cortado, pd.DataFrame([linha_final])],
            ignore_index=True
        )

    df_cortado = df_cortado.sort_values(col_tvd).reset_index(drop=True)

    return df_cortado


def _gerar_df_interp_a_partir_df1_df2(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Replica a lógica do seu direcional(): interpola Inc/Azi da df2 para as profundidades de df1.
    Usa a mesma regra de expandir do zero via st.session_state.ex == 'Ativada'
    """
    # mesma lógica que você já usa dentro do direcional() :contentReference[oaicite:2]{index=2}
    expand_from_zero = (st.session_state.get("ex", "Desativada") == "Ativada")

    col_md1 = [col for col in df1.columns if "md" in col.lower()]
    col_md2 = [col for col in df2.columns if "md" in col.lower()]

    if not col_md1 or not col_md2:
        raise ValueError("Colunas de profundidade MD não encontradas em df1 ou df2.")
    if "Inc" not in df2.columns or "Azi" not in df2.columns:
        raise ValueError("df2 precisa conter colunas 'Inc' e 'Azi'.")

    md1_col = col_md1[0]
    md2_col = col_md2[0]

    md2 = df2[md2_col].astype(float).values
    inc2 = df2["Inc"].astype(float).values
    azi2 = df2["Azi"].astype(float).values

    sort_idx = np.argsort(md2)
    md2_sorted = md2[sort_idx]
    inc2_sorted = inc2[sort_idx]
    azi2_sorted = azi2[sort_idx]

    md1_original = df1[md1_col].astype(float).values
    md1_original = np.sort(md1_original)

    if expand_from_zero:
        first_depth = md1_original[0]
        md1_extra = np.arange(0, first_depth, 1.0)
        md1 = np.concatenate((md1_extra, md1_original))
    else:
        md1 = md1_original.copy()

    inc_interp = np.interp(md1, md2_sorted, inc2_sorted)
    idx = np.searchsorted(md2_sorted, md1, side="right") - 1
    idx = np.clip(idx, 0, len(azi2_sorted) - 1)
    azi_interp = azi2_sorted[idx]

    df_interp = pd.DataFrame({
        "Profundidade": md1,
        "Inc (°)": inc_interp,
        "Azi (°)": azi_interp
    })
    return df_interp


def _ler_litologia_do_xlsm(wb) -> pd.DataFrame:
    if "Litologia" not in wb.sheetnames:
        raise ValueError("A aba 'Litologia' não existe no arquivo.")

    ws = wb["Litologia"]

    h_fm = ws["C3"].value
    h_lit = ws["E3"].value
    h_top = ws["F3"].value
    h_bas = ws["G3"].value

    def _norm(x):
        return str(x).strip().lower() if x is not None else ""

    if not any(k in _norm(h_fm) for k in ["forma", "formação", "formacao", "fm"]):
        raise ValueError(f"Header de Formação inválido em C3: {h_fm}")
    if "litolog" not in _norm(h_lit):
        raise ValueError(f"Header de Litologia inválido em E3: {h_lit}")
    if "top" not in _norm(h_top):
        raise ValueError(f"Header de Topo inválido em F3: {h_top}")
    if "bas" not in _norm(h_bas):
        raise ValueError(f"Header de Base inválido em G3: {h_bas}")

    rows = []
    r = 4
    while r <= ws.max_row:
        fm = ws[f"C{r}"].value
        lit = ws[f"E{r}"].value
        topo = ws[f"F{r}"].value
        base = ws[f"G{r}"].value

        if (fm in (None, "") and lit in (None, "") and topo in (None, "") and base in (None, "")):
            break

        rows.append((fm, lit, topo, base))
        r += 1

    df = pd.DataFrame(rows, columns=["Formação", "Litologia", "Topo", "Base"])

    df["Formação"] = df["Formação"].astype(str).str.strip()
    df["Litologia"] = df["Litologia"].astype(str).str.strip()
    df["Topo"] = pd.to_numeric(df["Topo"], errors="coerce")
    df["Base"] = pd.to_numeric(df["Base"], errors="coerce")

    df = df.dropna(subset=["Topo"]).reset_index(drop=True)
    df = df[(df["Litologia"] != "") | (df["Formação"] != "")].reset_index(drop=True)

    if df.empty:
        raise ValueError("Nenhuma linha válida encontrada na aba 'Litologia'.")

    return df


def _aplicar_litologia_no_state(poco_nome: str, df_lito: pd.DataFrame):
    if "pocos" not in st.session_state:
        st.session_state.pocos = {}
    if poco_nome not in st.session_state.pocos:
        st.session_state.pocos[poco_nome] = {}

    st.session_state.pocos[poco_nome]["profundidade"] = df_lito["Topo"].astype(float).tolist()
    st.session_state.pocos[poco_nome]["litologia"] = df_lito["Litologia"].astype(str).tolist()

    # ✅ agora vem do Excel
    st.session_state.pocos[poco_nome]["formation"] = df_lito["Formação"].astype(str).tolist()

    st.session_state.n_fm = len(df_lito)

    # Pré-preenche widgets
    for i in range(st.session_state.n_fm):
        st.session_state[f"prof_{i}"] = float(st.session_state.pocos[poco_nome]["profundidade"][i])
        st.session_state[f"fm_{i}"] = st.session_state.pocos[poco_nome]["formation"][i]

        lit = st.session_state.pocos[poco_nome]["litologia"][i]
        mapa_lit = {
            "argilito": "Argilito",
            "arenito": "Arenito",
            "folhelho": "Folhelho",
            "calcario": "Calcário",
            "calcário": "Calcário",
            "carbonato": "Carbonato",
            "siltito": "Siltito",
            "diamictito": "Diamictito",
            "conglomerado": "Conglomerado",
            "anidrita / gipsita": "Anidrita / Gipsita",
            "anidrita": "Anidrita / Gipsita",
            "gipsita": "Anidrita / Gipsita",
            "halita": "Halita",
            "calcissiltito": "Calcissiltito",
            "calcarenito": "Calcarenito",
            "calcirrudito": "Calcirrudito",
            "coquina": "Coquina",
            "dolomito": "Dolomito",
            "basalto": "Basalto",
            "diabásio": "Diabásio",
            "diabasio": "Diabásio",
        }
        st.session_state[f"lit_{i}"] = mapa_lit.get(str(lit).strip().lower(), "Arenito")


def _ler_inicio_do_xlsm(wb) -> dict:
    """
    Lê valores fixos na aba 'Início' via células:
      - D5  -> Nome do poço
      - D10 -> Objetivo (comments)
      - D7  -> Easting
      - D6  -> Northing
      - B9  -> Hemisfério
      - B8  -> Zona UTM
    """
    if "Início" not in wb.sheetnames and "Inicio" not in wb.sheetnames:
        raise ValueError("A aba 'Início' (ou 'Inicio') não existe no arquivo.")

    ws = wb["Início"] if "Início" in wb.sheetnames else wb["Inicio"]

    nome_poco = ws["D5"].value
    objetivo = ws["D10"].value
    easting = ws["D7"].value
    northing = ws["D6"].value
    zona = ws["D8"].value
    hem = ws["D9"].value

    def _to_float(v):
        try:
            if v is None or v == "":
                return None
            return float(v)
        except Exception:
            return None

    def _to_int(v):
        try:
            if v is None or v == "":
                return None
            return int(float(v))
        except Exception:
            return None

    def _to_str(v):
        if v is None or v == "":
            return None
        return str(v).strip()

    return {
        "poco": None if nome_poco in (None, "") else str(nome_poco).strip(),
        "comments": "" if objetivo in (None, "") else str(objetivo).strip(),
        "easting": _to_float(easting),
        "northing": _to_float(northing),
        "zona": _to_int(zona),
        "hem": _to_str(hem),
    }


def _ler_peso_fluido_do_xlsm(wb) -> pd.DataFrame:
    if "Fluido" in wb.sheetnames:
        ws = wb["Fluido"]
    elif "Geopressões" in wb.sheetnames:
        ws = wb["Geopressões"]
    elif "Geopressoes" in wb.sheetnames:
        ws = wb["Geopressoes"]
    else:
        raise ValueError("A aba 'Fluido' não existe no arquivo.")

    h_md = ws["B5"].value
    h_wp = ws["C5"].value
    h_we = ws["D5"].value

    def _norm(x):
        return str(x).strip().lower() if x is not None else ""

    if "prof" not in _norm(h_md):
        raise ValueError(f"Header inesperado em B5: {h_md}")
    if "planej" not in _norm(h_wp):
        raise ValueError(f"Header inesperado em C5: {h_wp}")
    if "execut" not in _norm(h_we):
        raise ValueError(f"Header inesperado em D5: {h_we}")

    rows = []
    vazio_seguidos = 0

    for md, wp, we in ws.iter_rows(
        min_row=6,
        max_row=min(ws.max_row, 10000),
        min_col=2,   # B
        max_col=4,   # D
        values_only=True
    ):
        if md in (None, ""):
            vazio_seguidos += 1
            if vazio_seguidos >= 3:
                break
            continue

        vazio_seguidos = 0
        rows.append((md, wp, we))

    if not rows:
        raise ValueError("Não encontrei dados de peso do fluido em B6/C6/D6...")

    df = pd.DataFrame(
        rows,
        columns=[
            "Profundidade (m)",
            "Peso do Fluido Planejado (lb/gal)",
            "Peso do Fluido Executado (lb/gal)",
        ],
    )

    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Profundidade (m)"]).sort_values("Profundidade (m)").reset_index(drop=True)

    if df.empty:
        raise ValueError("Não encontrei dados válidos de peso do fluido em B6/C6/D6...")

    return df


def _ler_sapatas_do_xlsm(wb) -> pd.DataFrame:
    """
    Lê as sapatas na aba 'Início' (ou 'Inicio').

    Células:
      - TVD: E13, E14, E15 e opcionalmente E16 e E17
      - OD : F13, F14, F15 e opcionalmente F16 e F17

    Retorna DataFrame com:
      - Ordem
      - Fase
      - Profundidade da sapata (m)
    """
    if "Início" not in wb.sheetnames and "Inicio" not in wb.sheetnames:
        raise ValueError("A aba 'Início' (ou 'Inicio') não existe no arquivo.")

    ws = wb["Início"] if "Início" in wb.sheetnames else wb["Inicio"]

    def _to_float(v):
        try:
            if v is None or str(v).strip() == "":
                return None
            return float(v)
        except Exception:
            return None

    rows = []

    for ordem, r in enumerate(range(13, 18), start=1):
        tvd = _to_float(ws[f"E{r}"].value)
        od = _to_float(ws[f"F{r}"].value)

        if tvd is not None and tvd > 0:
            rows.append((ordem, od, tvd))

    if not rows:
        raise ValueError("Nenhuma sapata válida foi encontrada em E13:E16 / F13:F16 da aba 'Início'.")

    sapatas_df = pd.DataFrame(
        rows,
        columns=["Ordem", "Fase", "Profundidade da sapata (m)"]
    )

    sapatas_df["Ordem"] = pd.to_numeric(sapatas_df["Ordem"], errors="coerce").astype(int)
    sapatas_df["Fase"] = pd.to_numeric(sapatas_df["Fase"], errors="coerce")
    sapatas_df["Profundidade da sapata (m)"] = pd.to_numeric(
        sapatas_df["Profundidade da sapata (m)"], errors="coerce"
    )

    sapatas_df = sapatas_df.dropna(subset=["Profundidade da sapata (m)"])
    sapatas_df = sapatas_df[sapatas_df["Profundidade da sapata (m)"] > 0].copy()

    sapatas_df["Fase"] = sapatas_df["Fase"].fillna(0).astype(float).round(3)
    sapatas_df["Profundidade da sapata (m)"] = sapatas_df["Profundidade da sapata (m)"].astype(float)

    return sapatas_df.reset_index(drop=True)


def _ler_fases_do_xlsm(wb) -> pd.DataFrame:
    """
    Lê as fases (diâmetro das brocas) na aba 'Início' (ou 'Inicio').

    Células:
      - C21, C22, C23, C24, C25

    Retorna DataFrame com:
      - Ordem
      - Fase
    """
    if "Início" not in wb.sheetnames and "Inicio" not in wb.sheetnames:
        raise ValueError("A aba 'Início' (ou 'Inicio') não existe no arquivo.")

    ws = wb["Início"] if "Início" in wb.sheetnames else wb["Inicio"]

    def _to_float(v):
        try:
            if v is None or str(v).strip() == "":
                return None
            return float(v)
        except Exception:
            return None

    rows = []

    for ordem, r in enumerate(range(21, 26), start=1):
        fase = _to_float(ws[f"C{r}"].value)

        if fase is not None and fase > 0:
            rows.append((ordem, fase))

    if not rows:
        raise ValueError("Nenhuma fase válida foi encontrada em C21:C24 da aba 'Início'.")

    fases_df = pd.DataFrame(rows, columns=["Ordem", "Fase"])
    fases_df["Ordem"] = pd.to_numeric(fases_df["Ordem"], errors="coerce").astype(int)
    fases_df["Fase"] = pd.to_numeric(fases_df["Fase"], errors="coerce")

    fases_df = fases_df.dropna(subset=["Fase"])
    fases_df = fases_df[fases_df["Fase"] > 0].copy()
    fases_df["Fase"] = fases_df["Fase"].astype(float).round(3)

    return fases_df.reset_index(drop=True)


def _fmt_polegada(v):
    try:
        if v is None or pd.isna(v):
            return "—"
        v = float(v)
        if v.is_integer():
            return f'{int(v)}"'
        return f'{v:g}"'
    except Exception:
        return str(v)


def _montar_paginas_fases(fases_df, sapatas_df):
    """
    Retorna uma lista de dicts, um por página.

    Regras:
    - associa por ordem
    - se houver sapata correspondente:
        'Fase de X, Revestimento de Y'
    - se não houver:
        'Fase de X, Poço aberto'
    """
    paginas = []

    if fases_df is None or fases_df.empty:
        return paginas

    sap_map = {}
    if sapatas_df is not None and not sapatas_df.empty:
        for _, row in sapatas_df.iterrows():
            ordem = int(row["Ordem"])
            sap_map[ordem] = {
                "fase_revestimento": row.get("Fase", None),
                "prof_sapata": row.get("Profundidade da sapata (m)", None),
            }

    for _, row in fases_df.iterrows():
        ordem = int(row["Ordem"])
        fase_broca = row.get("Fase", None)

        if ordem in sap_map:
            fase_revest = sap_map[ordem]["fase_revestimento"]
            prof_sapata = sap_map[ordem]["prof_sapata"]
            titulo = f'Análise da Fase de {_fmt_polegada(fase_broca)}, Revestimento de {_fmt_polegada(fase_revest)}'
        else:
            fase_revest = None
            prof_sapata = None
            titulo = f'Fase de {_fmt_polegada(fase_broca)}, Poço aberto'

        paginas.append({
            "ordem": ordem,
            "fase_broca": fase_broca,
            "fase_revestimento": fase_revest,
            "prof_sapata": prof_sapata,
            "titulo": titulo,
        })

    return paginas


def _to_num(s):
    return pd.to_numeric(s, errors="coerce")


def _fmt2(v, suf=""):
    return f"{float(v):.2f}{suf}" if v is not None and pd.notna(v) else "—"


def _filtrar_intervalo(df, col_prof, prof_ini, prof_fim, incluir_fim=False):
    if df is None or df.empty or col_prof not in df.columns:
        return pd.DataFrame()

    s = pd.to_numeric(df[col_prof], errors="coerce")

    if prof_ini is None or prof_fim is None or pd.isna(prof_ini) or pd.isna(prof_fim):
        return pd.DataFrame()

    if incluir_fim:
        mask = (s >= float(prof_ini)) & (s <= float(prof_fim))
    else:
        mask = (s >= float(prof_ini)) & (s < float(prof_fim))

    return df.loc[mask].copy()


def _seg_contiguos(df_base, mask_bool, col_prof, col_exec, col_req):
    segs = []
    if df_base.empty:
        return segs

    mask = mask_bool.fillna(False).astype(bool).values
    prof = df_base[col_prof].astype(float).values
    execv = df_base[col_exec].astype(float).values
    reqv = df_base[col_req].astype(float).values

    i = 0
    n = len(df_base)
    while i < n:
        if not mask[i]:
            i += 1
            continue

        j = i
        while j + 1 < n and mask[j + 1]:
            j += 1

        prof_ini = prof[i]
        prof_fim = prof[j]

        exec_seg = execv[i:j + 1]
        req_seg = reqv[i:j + 1]

        diffs = np.abs(req_seg - exec_seg)
        if np.isfinite(diffs).any():
            k_rel = int(np.nanargmax(diffs))
            k_abs = i + k_rel
            diff_max = float(np.nanmax(diffs))
            prof_pior = float(prof[k_abs])
        else:
            diff_max = np.nan
            prof_pior = np.nan

        segs.append({
            "pi": prof_ini,
            "pf": prof_fim,
            "prof_pior": prof_pior,
            "exec_min": np.nanmin(exec_seg) if np.isfinite(exec_seg).any() else np.nan,
            "exec_max": np.nanmax(exec_seg) if np.isfinite(exec_seg).any() else np.nan,
            "req_min": np.nanmin(req_seg) if np.isfinite(req_seg).any() else np.nan,
            "req_max": np.nanmax(req_seg) if np.isfinite(req_seg).any() else np.nan,
            "diff_max": diff_max
        })

        i = j + 1

    return segs


def _draw_centered_text(c, x_center, y, text, font_name="Helvetica", font_size=9):
    c.setFont(font_name, font_size)
    tw = c.stringWidth(str(text), font_name, font_size)
    c.drawString(x_center - tw / 2, y, str(text))


def desenhar_mapa_folium_no_pdf(c, mapa_folium, left, right, top, bottom):
    mapa_folium.save('filename.png')
    if mapa_folium is None:
        raise ValueError("Mapa Folium não informado.")

    largura = right - left
    altura = top - bottom

    if largura <= 0 or altura <= 0:
        raise ValueError("Área inválida para desenhar o mapa.")

    try:
        png_data = mapa_folium._to_png(2)
    except Exception as e:
        raise RuntimeError(
            "Falha ao converter o mapa Folium para PNG. "
            "O método _to_png depende de Selenium + Firefox headless + GeckoDriver. "
            f"Erro original: {e}"
        )

    img = ImageReader(BytesIO(png_data))

    c.drawImage(
        img,
        left,
        bottom,
        width=largura,
        height=altura,
        preserveAspectRatio=True,
        mask='auto'
    )


def _unir_intervalos_mesmo_problema(subtrechos, tol=1e-9):
    """
    Une intervalos consecutivos/contíguos que possuem o mesmo tipo de problema.
    Retorna lista no formato:
    [
        {"pi": ..., "pf": ..., "tipo": ...},
        ...
    ]
    """
    if not subtrechos:
        return []

    # ordena por profundidade inicial
    itens = sorted(
        [
            {
                "pi": float(x["pi"]),
                "pf": float(x["pf"]),
                "tipo": str(x["tipo"])
            }
            for x in subtrechos
            if x.get("pi") is not None and x.get("pf") is not None
        ],
        key=lambda z: (z["pi"], z["pf"])
    )

    if not itens:
        return []

    unidos = [itens[0].copy()]

    for atual in itens[1:]:
        ultimo = unidos[-1]

        mesmo_tipo = atual["tipo"] == ultimo["tipo"]
        contiguo_ou_sobreposto = atual["pi"] <= (ultimo["pf"] + tol)

        if mesmo_tipo and contiguo_ou_sobreposto:
            ultimo["pf"] = max(ultimo["pf"], atual["pf"])
        else:
            unidos.append(atual.copy())

    return unidos


def _montar_interpretacoes_syga(sub_under, sub_over):
    """
    Agrupa os subtrechos por tipo de problema, mesmo que estejam em
    profundidades separadas.

    Retorna lista de dicts no formato:
    [
        {
            "tipo": "...",
            "intervalos": ["150.00 m–200.00 m", "350.00 m–400.00 m"],
            "texto": "..."
        },
        ...
    ]
    """
    todos = []

    for item in (sub_under or []):
        todos.append({
            "pi": float(item["pi"]),
            "pf": float(item["pf"]),
            "tipo": str(item["tipo"])
        })

    for item in (sub_over or []):
        todos.append({
            "pi": float(item["pi"]),
            "pf": float(item["pf"]),
            "tipo": str(item["tipo"])
        })

    if not todos:
        return []

    # ordena por profundidade
    todos = sorted(todos, key=lambda x: (x["pi"], x["pf"]))

    agrupados = {}
    ordem_tipos = []

    for item in todos:
        tipo = item["tipo"]
        intervalo_txt = f'{_fmt2(item["pi"], " m")}–{_fmt2(item["pf"], " m")}'

        if tipo not in agrupados:
            agrupados[tipo] = []
            ordem_tipos.append(tipo)

        agrupados[tipo].append(intervalo_txt)

    interpretacoes = []
    for tipo in ordem_tipos:
        interpretacoes.append({
            "tipo": tipo,
            "intervalos": agrupados[tipo],
            "texto": f"[Texto para: {tipo}]"
        })

    return interpretacoes


def _fmt_range_lbgal(vmin, vmax):
    try:
        vmin = float(vmin)
        vmax = float(vmax)

        if pd.isna(vmin) and pd.isna(vmax):
            return "—"

        if pd.isna(vmin):
            return f"{vmax:.2f} lb/gal"

        if pd.isna(vmax):
            return f"{vmin:.2f} lb/gal"

        if np.isclose(vmin, vmax, atol=1e-9):
            return f"{vmin:.2f} lb/gal"

        return f"{vmin:.2f}–{vmax:.2f} lb/gal"

    except Exception:
        return "—"


def _desenhar_tabela_paginada(
    c,
    left_margin,
    right_margin,
    y_top,
    titulo,
    headers,
    rows,
    col_w,
    footer_y=None,
    nova_pagina_cb=None,
    linha_altura=15,
    header_h=18,
):
    """
    Desenha tabela quebrando automaticamente em novas páginas.

    nova_pagina_cb:
        função criada dentro de _desenhar_pagina_fase.
        Ela fecha a página atual, abre uma nova página e retorna o novo y.
    """

    if not rows:
        return y_top

    box_width = right_margin - left_margin
    box_x = left_margin

    pad_left = 6
    pad_right = 6

    inner_w = box_width - (pad_left + pad_right) * 2
    widths = [inner_w * w for w in col_w]

    x0 = box_x + pad_left
    xs = [x0]

    for w in widths:
        xs.append(xs[-1] + w)

    # Caso a função seja usada fora da análise por fase,
    # mantém comportamento seguro sem quebra de página.
    if footer_y is None or nova_pagina_cb is None:
        footer_y = -10000

        def nova_pagina_cb(y_atual, altura_necessaria=0, forcar=False):
            return y_atual

    page_bottom = footer_y + 35
    min_table_height = 30 + header_h + linha_altura

    i = 0
    primeiro_bloco = True

    while i < len(rows):
        y_top = nova_pagina_cb(
            y_top,
            altura_necessaria=min_table_height,
            forcar=False
        )

        altura_disponivel = y_top - page_bottom
        max_rows = int((altura_disponivel - 30 - header_h) // linha_altura)

        if max_rows < 1:
            y_top = nova_pagina_cb(
                y_top,
                altura_necessaria=min_table_height,
                forcar=True
            )

            altura_disponivel = y_top - page_bottom
            max_rows = int((altura_disponivel - 30 - header_h) // linha_altura)

            if max_rows < 1:
                max_rows = 1

        rows_bloco = rows[i:i + max_rows]

        titulo_bloco = titulo if primeiro_bloco else f"{titulo} (continuação)"

        box_height = 30 + header_h + len(rows_bloco) * linha_altura
        box_y = y_top - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(
            box_x,
            box_y + box_height - 18,
            box_x + box_width,
            box_y + box_height - 18
        )

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(
            box_x + 10,
            box_y + box_height - 14,
            titulo_bloco
        )

        texto_y = box_y + box_height - 32

        c.setLineWidth(0.5)
        c.line(
            box_x + 8,
            texto_y - 4,
            box_x + box_width - 8,
            texto_y - 4
        )

        for j, htxt in enumerate(headers):
            xc = (xs[j] + xs[j + 1]) / 2
            _draw_centered_text(
                c,
                xc,
                texto_y,
                htxt,
                font_name="Helvetica-Bold",
                font_size=10
            )

        texto_y -= header_h

        for row in rows_bloco:
            for j, txt in enumerate(row):
                xc = (xs[j] + xs[j + 1]) / 2
                _draw_centered_text(
                    c,
                    xc,
                    texto_y,
                    txt,
                    font_name="Helvetica",
                    font_size=10
                )

            texto_y -= linha_altura

        y_top = box_y - 14

        i += len(rows_bloco)
        primeiro_bloco = False

        if i < len(rows):
            y_top = nova_pagina_cb(
                y_top,
                altura_necessaria=min_table_height,
                forcar=True
            )

    return y_top


def desenhar_tabela_segmentos(
    c,
    left_margin,
    right_margin,
    y_top,
    titulo,
    segs,
    col_balanco_label,
    footer_y=None,
    nova_pagina_cb=None
):
    if not segs:
        return y_top

    headers = [
        "Prof. inicial",
        "Prof. final",
        "Peso aplicado",
        "Limite requerido",
        col_balanco_label
    ]

    rows = []

    for seg in segs:
        rows.append([
            _fmt2(seg.get("pi"), " m"),
            _fmt2(seg.get("pf"), " m"),
            _fmt_range_lbgal(seg.get("exec_min"), seg.get("exec_max")),
            _fmt_range_lbgal(seg.get("req_min"), seg.get("req_max")),
            _fmt2(seg.get("diff_max"), " lb/gal")
        ])

    return _desenhar_tabela_paginada(
        c=c,
        left_margin=left_margin,
        right_margin=right_margin,
        y_top=y_top,
        titulo=titulo,
        headers=headers,
        rows=rows,
        col_w=[0.20, 0.20, 0.21, 0.21, 0.18],
        footer_y=footer_y,
        nova_pagina_cb=nova_pagina_cb,
        linha_altura=15,
        header_h=18
    )


def desenhar_tabela_falhas_quebrada(
    c,
    left_margin,
    right_margin,
    y_top,
    titulo,
    subtrechos,
    footer_y=None,
    nova_pagina_cb=None
):
    if not subtrechos:
        return y_top

    headers = [
        "Prof. inicial",
        "Prof. final",
        "Tipo de falha"
    ]

    rows = []

    for stc in subtrechos:
        rows.append([
            _fmt2(stc.get("pi"), " m"),
            _fmt2(stc.get("pf"), " m"),
            str(stc.get("tipo", "—"))
        ])

    return _desenhar_tabela_paginada(
        c=c,
        left_margin=left_margin,
        right_margin=right_margin,
        y_top=y_top,
        titulo=titulo,
        headers=headers,
        rows=rows,
        col_w=[0.25, 0.25, 0.50],
        footer_y=footer_y,
        nova_pagina_cb=nova_pagina_cb,
        linha_altura=15,
        header_h=18
    )


def desenhar_tabela_interpretacoes_syga(
    c,
    left_margin,
    right_margin,
    y_top,
    interpretacoes,
    footer_y=None,
    nova_pagina_cb=None
):
    if not interpretacoes:
        return y_top

    headers = [
        "Tipo de problema",
        "Intervalo",
        "Interpretação"
    ]

    rows = []

    for item in interpretacoes:
        tipo = str(item.get("tipo", "—"))
        texto = str(item.get("texto", "—"))
        intervalos = item.get("intervalos", [])

        if not intervalos:
            intervalos = ["—"]

        for i, intervalo in enumerate(intervalos):
            rows.append([
                tipo if i == 0 else "",
                str(intervalo),
                texto if i == 0 else ""
            ])

    return _desenhar_tabela_paginada(
        c=c,
        left_margin=left_margin,
        right_margin=right_margin,
        y_top=y_top,
        titulo="Interpretação SYGA",
        headers=headers,
        rows=rows,
        col_w=[0.34, 0.28, 0.38],
        footer_y=footer_y,
        nova_pagina_cb=nova_pagina_cb,
        linha_altura=15,
        header_h=18
    )


def _desenhar_pagina_fase(c,width,height,logo,footer_y,titulo,fase_broca,fase_revestimento,prof_ini,prof_fim,df_cmp_global,draw_header,incluir_fim=False):
    # -------------------------------------------------
    # Validação ANTES de desenhar a página
    # -------------------------------------------------
    if (
        prof_ini is None
        or prof_fim is None
        or pd.isna(prof_ini)
        or pd.isna(prof_fim)
        or prof_fim <= prof_ini
    ):
        return

    if df_cmp_global is None or df_cmp_global.empty:
        return

    if "Profundidade (m)" not in df_cmp_global.columns:
        return

    df_cmp_fase = _filtrar_intervalo(
        df_cmp_global,
        "Profundidade (m)",
        prof_ini,
        prof_fim,
        incluir_fim=incluir_fim
    )

    # Se não houver dados na fase, não gera página
    if df_cmp_fase.empty:
        return

    df_cmp_fase = df_cmp_fase.copy()

    # -------------------------------------------------
    # Validação dos dados necessários para análise
    # -------------------------------------------------
    colunas_obrigatorias = [
        "Profundidade (m)",
        "Peso do Fluido (lb/gal)",
        "Max Inferior",
        "Min Superior",
    ]

    for col in colunas_obrigatorias:
        if col not in df_cmp_fase.columns:
            return

    for col in colunas_obrigatorias:
        df_cmp_fase[col] = pd.to_numeric(df_cmp_fase[col], errors="coerce")

    df_cmp_fase = df_cmp_fase.dropna(
        subset=[
            "Profundidade (m)",
            "Peso do Fluido (lb/gal)",
            "Max Inferior",
            "Min Superior",
        ]
    ).copy()

    if df_cmp_fase.empty:
        return

    # Recalcula as flags para garantir consistência
    df_cmp_fase["is_under"] = (
        df_cmp_fase["Peso do Fluido (lb/gal)"] < df_cmp_fase["Max Inferior"]
    )

    df_cmp_fase["is_over"] = (
        df_cmp_fase["Peso do Fluido (lb/gal)"] > df_cmp_fase["Min Superior"]
    )

    # -------------------------------------------------
    # Detecção dos trechos ANTES de desenhar a página
    # -------------------------------------------------
    segs_under = _seg_contiguos(
        df_base=df_cmp_fase,
        mask_bool=df_cmp_fase["is_under"],
        col_prof="Profundidade (m)",
        col_exec="Peso do Fluido (lb/gal)",
        col_req="Max Inferior"
    )

    segs_over = _seg_contiguos(
        df_base=df_cmp_fase,
        mask_bool=df_cmp_fase["is_over"],
        col_prof="Profundidade (m)",
        col_exec="Peso do Fluido (lb/gal)",
        col_req="Min Superior"
    )

    # Se não foi detectado nada, não gera página.
    # Isso evita página aparecendo apenas com "Diâmetro da fase".
    if not segs_under and not segs_over:
        return

    sub_under = _subtrechos_por_falha_cmp(
        df_cmp_fase,
        segs_under,
        lado="inferior"
    )

    sub_over = _subtrechos_por_falha_cmp(
        df_cmp_fase,
        segs_over,
        lado="superior"
    )

    interpretacoes_syga = _montar_interpretacoes_syga(
        sub_under,
        sub_over
    )

    # -------------------------------------------------
    # Começa a desenhar a página somente se houver detecção
    # -------------------------------------------------
    left_margin = 40
    right_margin = width - 40
    def abrir_pagina_fase(continua=False):
        y_local = draw_header(c, width, height, logo)

        c.setFont("Helvetica-Bold", 18)

        titulo_local = titulo
        if continua:
            titulo_local = f"{titulo} (continuação)"

        c.drawString(left_margin, y_local, titulo_local)
        y_local -= 10

        c.line(left_margin, y_local, right_margin, y_local)
        y_local -= 18

        return y_local
    def nova_pagina_fase(y_atual, altura_necessaria=0, forcar=False):
        limite_inferior = footer_y + 35

        if forcar or (y_atual - altura_necessaria < limite_inferior):
            draw_footer(c, width, footer_y)
            c.showPage()
            return abrir_pagina_fase(continua=True)

        return y_atual
    y = abrir_pagina_fase(continua=False)

    # -------------------------------------------------
    # Tabela-resumo da fase
    # -------------------------------------------------
    def desenhar_tabela_resumo_fase(y_top):
        y_top = nova_pagina_fase(
            y_top,
            altura_necessaria=70,
            forcar=False
        )
        box_width = right_margin - left_margin
        box_x = left_margin

        pad_left = 6
        pad_right = 6

        col_w = [0.28, 0.30, 0.42]
        inner_w = box_width - (pad_left + pad_right) * 2
        widths = [inner_w * w for w in col_w]

        x0 = box_x + pad_left
        xs = [x0]

        for w in widths:
            xs.append(xs[-1] + w)

        linha_altura = 18
        header_h = 18
        box_height = 30 + header_h + linha_altura
        box_y = y_top - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(
            box_x,
            box_y + box_height - 18,
            box_x + box_width,
            box_y + box_height - 18
        )

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(
            box_x + 10,
            box_y + box_height - 14,
            "Dados da Fase"
        )

        texto_y = box_y + box_height - 32

        headers = [
            "Diâmetro da fase",
            "Diâmetro do revestimento",
            "Intervalo analisado"
        ]

        c.setLineWidth(0.5)
        c.line(
            box_x + 8,
            texto_y - 4,
            box_x + box_width - 8,
            texto_y - 4
        )

        for i, htxt in enumerate(headers):
            xc = (xs[i] + xs[i + 1]) / 2
            _draw_centered_text(
                c,
                xc,
                texto_y,
                htxt,
                font_name="Helvetica-Bold",
                font_size=10
            )

        texto_y -= header_h

        diam_fase_txt = _fmt_polegada(fase_broca)

        diam_revest_txt = (
            _fmt_polegada(fase_revestimento)
            if fase_revestimento is not None and pd.notna(fase_revestimento)
            else "Poço aberto"
        )

        intervalo_txt = f'{_fmt2(prof_ini, " m")} até {_fmt2(prof_fim, " m")}'

        row = [
            diam_fase_txt,
            diam_revest_txt,
            intervalo_txt
        ]

        for i, txt in enumerate(row):
            xc = (xs[i] + xs[i + 1]) / 2
            _draw_centered_text(
                c,
                xc,
                texto_y,
                txt,
                font_name="Helvetica",
                font_size=10
            )

        return box_y - 14

    y = desenhar_tabela_resumo_fase(y)

    # -------------------------------------------------
    # Análise dos trechos
    # -------------------------------------------------
    if segs_under:
        y = desenhar_tabela_segmentos(
            c=c,
            left_margin=left_margin,
            right_margin=right_margin,
            y_top=y,
            titulo="Trechos em Underbalance (Peso do Fluido < Limite Inferior)",
            segs=segs_under,
            col_balanco_label="Underbalance máx.",
            footer_y=footer_y,
            nova_pagina_cb=nova_pagina_fase
        )

    if segs_over:
        y = desenhar_tabela_segmentos(
            c=c,
            left_margin=left_margin,
            right_margin=right_margin,
            y_top=y,
            titulo="Trechos em Overbalance (Peso do Fluido > Limite Superior)",
            segs=segs_over,
            col_balanco_label="Overbalance máx.",
            footer_y=footer_y,
            nova_pagina_cb=nova_pagina_fase
        )

    # -------------------------------------------------
    # Classificação do tipo de falha
    # -------------------------------------------------
    if sub_under:
        y = desenhar_tabela_falhas_quebrada(
            c=c,
            left_margin=left_margin,
            right_margin=right_margin,
            y_top=y,
            titulo="Classificação do Tipo de Falha (Trechos em Underbalance)",
            subtrechos=sub_under,
            footer_y=footer_y,
            nova_pagina_cb=nova_pagina_fase
        )

    if sub_over:
        y = desenhar_tabela_falhas_quebrada(
            c=c,
            left_margin=left_margin,
            right_margin=right_margin,
            y_top=y,
            titulo="Classificação do Tipo de Falha (Trechos Acima do Gradiente de Fratura)",
            subtrechos=sub_over,
            footer_y=footer_y,
            nova_pagina_cb=nova_pagina_fase
        )

    # -------------------------------------------------
    # Interpretações SYGA
    # -------------------------------------------------
    if interpretacoes_syga:
        y = desenhar_tabela_interpretacoes_syga(
            c=c,
            left_margin=left_margin,
            right_margin=right_margin,
            y_top=y,
            interpretacoes=interpretacoes_syga,
            footer_y=footer_y,
            nova_pagina_cb=nova_pagina_fase
        )

    draw_footer(c, width, footer_y)
    c.showPage()


def _montar_df_cmp_global(df_mud, df_suav):
    if not isinstance(df_mud, pd.DataFrame) or df_mud.empty:
        return pd.DataFrame()

    if not isinstance(df_suav, pd.DataFrame) or df_suav.empty:
        return pd.DataFrame()

    df_mud2 = df_mud.copy()
    df_suav2 = df_suav.copy()

    if "Profundidade (m)" not in df_mud2.columns:
        for alt in ["Profundidade", "MD", "MD(m)"]:
            if alt in df_mud2.columns:
                df_mud2 = df_mud2.rename(columns={alt: "Profundidade (m)"})
                break

    col_exec = "Peso do Fluido Executado (lb/gal)"
    if "Profundidade (m)" not in df_mud2.columns or col_exec not in df_mud2.columns:
        return pd.DataFrame()

    df_mud2["Profundidade (m)"] = pd.to_numeric(df_mud2["Profundidade (m)"], errors="coerce")
    df_mud2[col_exec] = pd.to_numeric(df_mud2[col_exec], errors="coerce")

    df_mud2 = (
        df_mud2.dropna(subset=["Profundidade (m)", col_exec])
        .sort_values("Profundidade (m)")
        .reset_index(drop=True)
    )

    if df_mud2.empty:
        return pd.DataFrame()

    col_prof_suav = "Profundidade (m)" if "Profundidade (m)" in df_suav2.columns else "MD"
    obrig = [col_prof_suav, "Max Inferior", "Min Superior"]

    if col_prof_suav not in df_suav2.columns or any(c not in df_suav2.columns for c in obrig[1:]):
        return pd.DataFrame()

    cols_falha = [
        col_prof_suav,
        "Max Inferior",
        "Min Superior",
        "Gradiente de Pressão de Poros (lb/gal)",
        "Tração Inferior",
        "Comp Inferior σθA",
        "Comp Inferior σθB",
        "Tração Superior (σθA)",
        "Tração Superior (σθB)",
        "Comp Superior σθA",
        "Comp Superior σθB",
    ]
    cols_exist = [c for c in cols_falha if c in df_suav2.columns]
    df_suav2 = df_suav2[cols_exist].copy()

    for ccol in [col_prof_suav, "Max Inferior", "Min Superior"]:
        df_suav2[ccol] = pd.to_numeric(df_suav2[ccol], errors="coerce")

    df_suav2 = (
        df_suav2.dropna(subset=[col_prof_suav, "Max Inferior", "Min Superior"])
        .sort_values(col_prof_suav)
        .reset_index(drop=True)
    )

    if df_suav2.empty:
        return pd.DataFrame()

    prof_s = df_suav2[col_prof_suav].astype(float)

    rows_ref = []
    for d in df_mud2["Profundidade (m)"].astype(float).values:
        idx = (prof_s - float(d)).abs().idxmin()
        rows_ref.append(df_suav2.loc[idx].to_dict())

    df_cmp = df_mud2[["Profundidade (m)", col_exec]].copy()
    df_cmp = df_cmp.rename(columns={col_exec: "Peso do Fluido (lb/gal)"})

    df_cmp["Prof (ref df_suav)"] = [float(r.get(col_prof_suav, np.nan)) for r in rows_ref]
    df_cmp["Max Inferior"] = pd.to_numeric([r.get("Max Inferior", np.nan) for r in rows_ref], errors="coerce")
    df_cmp["Min Superior"] = pd.to_numeric([r.get("Min Superior", np.nan) for r in rows_ref], errors="coerce")

    extras = [
        "Gradiente de Pressão de Poros (lb/gal)",
        "Tração Inferior",
        "Comp Inferior σθA",
        "Comp Inferior σθB",
        "Tração Superior (σθA)",
        "Tração Superior (σθB)",
        "Comp Superior σθA",
        "Comp Superior σθB",
    ]
    for col in extras:
        df_cmp[col] = pd.to_numeric([r.get(col, np.nan) for r in rows_ref], errors="coerce")

    df_cmp["is_under"] = df_cmp["Peso do Fluido (lb/gal)"] < df_cmp["Max Inferior"]
    df_cmp["is_over"] = df_cmp["Peso do Fluido (lb/gal)"] > df_cmp["Min Superior"]

    return df_cmp


def _classificar_falha_row(row, lado, nd=6):
    if row is None:
        return "Não identificado"

    try:
        if lado == "inferior":
            lim = round(float(row["Max Inferior"]), nd)
            candidatos = [
                ("Gradiente de Pressão de Poros (lb/gal)", "Limitado pela pressão de poros"),
                ("Tração Inferior", "Falha por tração inf."),
                ("Comp Inferior σθA", "Falha por comp. inf. em σθA"),
                ("Comp Inferior σθB", "Falha por comp. inf. em σθB"),
            ]
        else:
            lim = round(float(row["Min Superior"]), nd)
            candidatos = [
                ("Tração Superior (σθA)", "Falha por tração sup. em σθA"),
                ("Tração Superior (σθB)", "Falha por tração sup. em σθB"),
                ("Comp Superior σθA", "Falha por comp. sup. em σθA"),
                ("Comp Superior σθB", "Falha por comp. sup. em σθB"),
            ]
    except Exception:
        return "Não identificado"

    for col, label in candidatos:
        try:
            v = row.get(col, np.nan)
            if pd.isna(v):
                continue
            if round(float(v), nd) == lim:
                return label
        except Exception:
            continue

    return "Não identificado"


def _subtrechos_por_falha_cmp(df_cmp_fase, segs, lado, tol_prof=1e-9):
    out = []
    if df_cmp_fase is None or df_cmp_fase.empty or not segs:
        return out

    prof_cmp = df_cmp_fase["Profundidade (m)"].astype(float)

    for s in segs:
        pi = float(s["pi"])
        pf = float(s["pf"])

        m = (prof_cmp >= (pi - tol_prof)) & (prof_cmp <= (pf + tol_prof))
        df_int = df_cmp_fase.loc[m].copy()

        if df_int.empty:
            continue

        df_int = df_int.sort_values("Profundidade (m)").reset_index(drop=True)
        df_int["tipo"] = df_int.apply(lambda r: _classificar_falha_row(r, lado=lado), axis=1)

        tipo_atual = None
        ini = None
        prof_prev = None

        for _, r in df_int.iterrows():
            p = float(r["Profundidade (m)"])
            t = str(r["tipo"])

            if tipo_atual is None:
                tipo_atual = t
                ini = p
            elif t != tipo_atual:
                out.append({"pi": ini, "pf": prof_prev, "tipo": tipo_atual})
                tipo_atual = t
                ini = p

            prof_prev = p

        if tipo_atual is not None and ini is not None and prof_prev is not None:
            out.append({"pi": ini, "pf": prof_prev, "tipo": tipo_atual})

    return out


def calcular_altura_kick_por_bha(df_bha_kick, vk_bbl):
    df_kick = df_bha_kick.copy()

    for col in [
        "Cap. Anular (m3/m)",
        "Comprimento (m)",
        "Início do Trecho (m)",
        "Fim do Trecho (m)",
        "Comprimento Acumulado (m)",
        "Vol. Acum. (m3)",
        "Vol. Acum. (bbl)"
    ]:
        if col in df_kick.columns:
            df_kick[col] = pd.to_numeric(df_kick[col], errors="coerce").fillna(0.0)

    vk_m3 = float(vk_bbl) / 6.28981

    volume_restante = vk_m3
    altura_kick_local = 0.0
    elemento_topo_kick_local = "Não definido"
    intervalo_elemento_topo_kick_local = ""

    for _, row in df_kick.iterrows():
        cap = float(row["Cap. Anular (m3/m)"])
        comp = float(row["Comprimento (m)"])
        inicio = float(row["Início do Trecho (m)"])
        fim = float(row["Fim do Trecho (m)"])
        elem = str(row["Elemento do BHA"])

        if cap <= 0 or comp <= 0:
            continue

        vol_trecho = cap * comp

        if volume_restante <= vol_trecho:
            altura_no_trecho = volume_restante / cap
            altura_kick_local = inicio + altura_no_trecho
            elemento_topo_kick_local = elem
            intervalo_elemento_topo_kick_local = f"{inicio:.2f}–{fim:.2f} m"
            volume_restante = 0.0
            break
        else:
            volume_restante -= vol_trecho

    if volume_restante > 1e-9:
        altura_kick_local = float(df_kick["Comprimento Acumulado (m)"].max())
        elemento_topo_kick_local = "Acima do último elemento do BHA"
        intervalo_elemento_topo_kick_local = ""

    return altura_kick_local, elemento_topo_kick_local, intervalo_elemento_topo_kick_local


def obter_intervalo_litologico(prof_alvo, profundidades, litologias, base_final=None):
    try:
        if prof_alvo is None or pd.isna(prof_alvo):
            return None

        n = min(len(profundidades), len(litologias))
        if n == 0:
            return None

        for i in range(n):
            topo = float(profundidades[i])

            if i < n - 1:
                base = float(profundidades[i + 1])
            else:
                base = float(base_final) if base_final is not None else float("inf")

            if topo <= float(prof_alvo) < base or (i == n - 1 and float(prof_alvo) >= topo):
                return {
                    "idx": i,
                    "topo": topo,
                    "base": base,
                    "litologia": str(litologias[i]).strip()
                }

        return None

    except Exception:
        return None


def normalizar_texto_litologico(txt):
    txt = str(txt).strip().lower()

    trocas = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }

    for antigo, novo in trocas.items():
        txt = txt.replace(antigo, novo)

    txt = " ".join(txt.split())
    return txt


def classificar_perm_nao_perm(valor):
    txt = normalizar_texto_litologico(valor)

    if (
        "nao permeavel" in txt
        or "nao-permeavel" in txt
        or "impermeavel" in txt
        or "folhelho" in txt
        or "fm. nao permeavel" in txt
        or "fm nao permeavel" in txt
    ):
        return "nao_permeavel"

    if (
        "permeavel" in txt
        or "fm. permeavel" in txt
        or "fm permeavel" in txt
    ):
        return "permeavel"

    return "outro"


def chegou_na_profundidade_final(prof, base_final=None, df_sapata=None, tol=0.5):
    try:
        if prof is None or pd.isna(prof):
            return False

        prof = float(prof)

        if base_final is not None:
            prof_final = float(base_final)

        elif df_sapata is not None and isinstance(df_sapata, pd.DataFrame):
            prof_final = pd.to_numeric(
                df_sapata["Profundidade (m)"],
                errors="coerce"
            ).max()
            prof_final = float(prof_final)

        else:
            return False

        return prof >= prof_final - float(tol)

    except Exception:
        return False


def encontrar_folhelho_acima_do_arenito(
    prof_sapata,
    profundidades=None,
    litologias=None,
    base_final=None,
    margem=None
):
    """
    Mantém o nome antigo para não quebrar chamadas existentes.

    Nova lógica:
    - usa st.session_state.df_perm_nao_perm;
    - usa st.session_state.ef como espessura mínima da camada não permeável;
    - verifica se a sapata caiu em Formação Permeável;
    - verifica se caiu em Formação Não Permeável com espessura menor que ef;
    - se houver problema, procura acima uma Formação Não Permeável com espessura >= ef;
    - ajusta a sapata para base_da_formacao_nao_permeavel - ef.
    """

    try:
        if prof_sapata is None or pd.isna(prof_sapata):
            return None

        prof_sapata = float(prof_sapata)

        if chegou_na_profundidade_final(
                prof_sapata,
                base_final=base_final,
                tol=0.5
        ):
            return None

        if margem is None:
            esp_min_nao_perm = float(st.session_state.get("ef", 10.0))
        else:
            esp_min_nao_perm = float(margem)

        df_perm = st.session_state.get("df_perm_nao_perm", None)

        if not isinstance(df_perm, pd.DataFrame) or df_perm.empty:
            return None

        col_topo = "Topo (m)"
        col_base = "Base (m)"

        if "Classificação" in df_perm.columns:
            col_classe = "Classificação"
        elif "Classificacao" in df_perm.columns:
            col_classe = "Classificacao"
        else:
            return None

        if col_topo not in df_perm.columns or col_base not in df_perm.columns:
            return None

        df_aux = df_perm[[col_topo, col_base, col_classe]].copy()

        df_aux[col_topo] = pd.to_numeric(df_aux[col_topo], errors="coerce")
        df_aux[col_base] = pd.to_numeric(df_aux[col_base], errors="coerce")

        df_aux = df_aux.dropna(subset=[col_topo, col_base, col_classe])

        if df_aux.empty:
            return None

        df_aux = df_aux.sort_values(col_topo).reset_index(drop=True)

        df_aux["classe_norm"] = df_aux[col_classe].apply(classificar_perm_nao_perm)
        df_aux["espessura"] = df_aux[col_base] - df_aux[col_topo]

        mask_intervalo = (
            (df_aux[col_topo] <= prof_sapata)
            & (prof_sapata < df_aux[col_base])
        )

        if not mask_intervalo.any():
            mask_intervalo = (
                (df_aux[col_topo] <= prof_sapata)
                & (prof_sapata <= df_aux[col_base])
            )

        if not mask_intervalo.any():
            return None

        idx_intervalo = mask_intervalo[mask_intervalo].index[0]
        intervalo_sapata = df_aux.loc[idx_intervalo]

        classe_sapata = intervalo_sapata["classe_norm"]
        espessura_sapata = float(intervalo_sapata["espessura"])

        intervalo_atual = {
            "idx": int(idx_intervalo),
            "topo": float(intervalo_sapata[col_topo]),
            "base": float(intervalo_sapata[col_base]),
            "espessura": espessura_sapata,
            "classificacao": str(intervalo_sapata[col_classe]).strip(),
            "classe_norm": classe_sapata,
        }

        precisa_avisar = False
        motivo = None

        if classe_sapata == "permeavel":
            precisa_avisar = True
            motivo = "formacao_permeavel"

        elif classe_sapata == "nao_permeavel" and espessura_sapata < esp_min_nao_perm:
            precisa_avisar = True
            motivo = "nao_permeavel_espessura_insuficiente"

        else:
            return None

        # Procura acima uma Formação Não Permeável com espessura mínima definida pelo usuário
        for j in range(idx_intervalo - 1, -1, -1):
            row = df_aux.loc[j]

            if row["classe_norm"] != "nao_permeavel":
                continue

            topo_np = float(row[col_topo])
            base_np = float(row[col_base])
            espessura_np = float(row["espessura"])

            if espessura_np < esp_min_nao_perm:
                continue

            prof_ajustada = base_np - esp_min_nao_perm

            if prof_ajustada < topo_np:
                continue

            return {
                "precisa_avisar": precisa_avisar,
                "motivo": motivo,
                "ajuste_disponivel": True,

                "esp_min_nao_perm": float(esp_min_nao_perm),

                "idx_nao_permeavel": int(j),
                "topo_nao_permeavel": topo_np,
                "base_nao_permeavel": base_np,
                "espessura_nao_permeavel": espessura_np,

                # Compatibilidade com o código antigo
                "idx_folhelho": int(j),
                "topo_folhelho": topo_np,
                "base_folhelho": base_np,

                "prof_ajustada": float(prof_ajustada),
                "intervalo_atual": intervalo_atual,

                # Compatibilidade com nomes antigos
                "intervalo_arenito": intervalo_atual,
                "intervalo_permeavel": intervalo_atual,
            }

        return {
            "precisa_avisar": precisa_avisar,
            "motivo": motivo,
            "ajuste_disponivel": False,
            "prof_ajustada": None,
            "esp_min_nao_perm": float(esp_min_nao_perm),
            "intervalo_atual": intervalo_atual,

            # Compatibilidade
            "intervalo_arenito": intervalo_atual,
            "intervalo_permeavel": intervalo_atual,
        }

    except Exception as e:
        st.error(f"Erro ao analisar Formação Permeável / Não Permeável: {e}")
        return None

@st.dialog("Sapata em Formação Permeável")
def confirmar_ajuste_sapata_arenito():
    pend = st.session_state.get("pendencia_ajuste_arenito", None)

    if not pend:
        st.warning("Nenhuma pendência de ajuste encontrada.")
        return

    nome_sapata = pend["nome_sapata"]
    prof_original = float(pend["prof_original"])
    decision_id = pend["decision_id"]

    motivo = pend.get("motivo")
    ajuste_disponivel = bool(pend.get("ajuste_disponivel", False))
    prof_ajustada = pend.get("prof_ajustada", None)
    intervalo_atual = pend.get("intervalo_atual", {})
    esp_min_nao_perm = float(pend.get("esp_min_nao_perm", st.session_state.get("ef", 10.0)))

    topo_atual = intervalo_atual.get("topo", None)
    base_atual = intervalo_atual.get("base", None)
    esp_atual = intervalo_atual.get("espessura", None)
    classe_atual = intervalo_atual.get("classificacao", "Formação")

    if motivo == "formacao_permeavel":
        st.write(
            f'{nome_sapata} ficou em uma Formação Permeável na profundidade de '
            f'{prof_original:.2f} m.'
        )

    elif motivo == "nao_permeavel_espessura_insuficiente":
        st.write(
            f'{nome_sapata} ficou em uma Formação Não Permeável na profundidade de '
            f'{prof_original:.2f} m, porém esse intervalo possui espessura menor que '
            f'{esp_min_nao_perm:.2f} m.'
        )

    else:
        st.write(
            f'{nome_sapata} precisa de verificação litológica na profundidade de '
            f'{prof_original:.2f} m.'
        )

    if topo_atual is not None and base_atual is not None and esp_atual is not None:
        st.info(
            f"Intervalo atual: {classe_atual} | "
            f"Topo: {float(topo_atual):.2f} m | "
            f"Base: {float(base_atual):.2f} m | "
            f"Espessura: {float(esp_atual):.2f} m"
        )

    if ajuste_disponivel and prof_ajustada is not None:
        prof_ajustada = float(prof_ajustada)

        st.write(
            f'Deseja assentar a sapata na Formação Não Permeável acima, '
            f'em {prof_ajustada:.2f} m?'
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "Sim, ajustar",
                use_container_width=True,
                key=f"bt_confirma_ajuste_arenito_{decision_id}",
                type="primary"
            ):
                st.session_state.decisoes_ajuste_arenito[decision_id] = True
                st.session_state.pendencia_ajuste_arenito = None
                st.rerun()

        with c2:
            if st.button(
                "Não, manter",
                use_container_width=True,
                key=f"bt_ignora_ajuste_arenito_{decision_id}",
                type="primary"
            ):
                st.session_state.decisoes_ajuste_arenito[decision_id] = False
                st.session_state.pendencia_ajuste_arenito = None
                st.rerun()

    else:
        st.warning(
            f"Não foi encontrada acima uma Formação Não Permeável com espessura mínima de "
            f"{esp_min_nao_perm:.2f} m. "
            "A sapata será mantida na profundidade calculada, mas deve ser revisada."
        )

        if st.button(
            "Entendi, manter sapata",
            use_container_width=True,
            key=f"bt_sem_ajuste_arenito_{decision_id}",
            type="primary"
        ):
            st.session_state.decisoes_ajuste_arenito[decision_id] = False
            st.session_state.pendencia_ajuste_arenito = None
            st.rerun()


def calcular_bha(df_base, diametro_poco_m):
    df_bha = pd.DataFrame(df_base).copy()

    for col in ["Elemento do BHA", "OD (pol)", "Comprimento (m)"]:
        if col not in df_bha.columns:
            if col == "Elemento do BHA":
                df_bha[col] = ""
            else:
                df_bha[col] = 0.0

    df_bha["Elemento do BHA"] = df_bha["Elemento do BHA"].astype(str).fillna("")
    df_bha["OD (pol)"] = pd.to_numeric(df_bha["OD (pol)"], errors="coerce").fillna(
        0.0)
    df_bha["Comprimento (m)"] = pd.to_numeric(
        df_bha["Comprimento (m)"], errors="coerce"
    ).fillna(0.0)

    df_bha = df_bha.dropna(
        subset=["Elemento do BHA", "OD (pol)", "Comprimento (m)"],
        how="all"
    ).copy()

    df_bha["Elemento do BHA"] = df_bha["Elemento do BHA"].fillna("")
    df_bha["OD (pol)"] = df_bha["OD (pol)"].fillna(0.0)
    df_bha["Comprimento (m)"] = df_bha["Comprimento (m)"].fillna(0.0)

    df_bha["OD (m)"] = df_bha["OD (pol)"] * 0.0254
    df_bha["Comprimento Acumulado (m)"] = df_bha["Comprimento (m)"].cumsum()

    df_bha["Cap. Anular (m3/m)"] = (math.pi / 4) * (
            diametro_poco_m ** 2 - df_bha["OD (m)"] ** 2
    )
    df_bha["Cap. Anular (m3/m)"] = df_bha["Cap. Anular (m3/m)"].clip(lower=0)

    df_bha["Vol. (m3)"] = df_bha["Cap. Anular (m3/m)"] * df_bha["Comprimento (m)"]
    df_bha["Vol. Acum. (m3)"] = df_bha["Vol. (m3)"].cumsum()
    df_bha["Vol. Acum. (bbl)"] = df_bha["Vol. Acum. (m3)"] * 6.28981

    df_bha["Início do Trecho (m)"] = (
            df_bha["Comprimento Acumulado (m)"] - df_bha["Comprimento (m)"]
    )
    df_bha["Fim do Trecho (m)"] = df_bha["Comprimento Acumulado (m)"]

    return df_bha[
        [
            "Elemento do BHA",
            "OD (pol)",
            "OD (m)",
            "Comprimento (m)",
            "Comprimento Acumulado (m)",
            "Início do Trecho (m)",
            "Fim do Trecho (m)",
            "Cap. Anular (m3/m)",
            "Vol. (m3)",
            "Vol. Acum. (m3)",
            "Vol. Acum. (bbl)"
        ]
    ]


def calcular_altura_kick_por_bha(df_bha_local, vk_bbl_local):
    df_kick_local = df_bha_local.copy()

    for col in [
        "Comprimento (m)",
        "Comprimento Acumulado (m)",
        "Início do Trecho (m)",
        "Fim do Trecho (m)",
        "Cap. Anular (m3/m)",
        "Vol. (m3)",
        "Vol. Acum. (m3)",
        "Vol. Acum. (bbl)"
    ]:
        if col in df_kick_local.columns:
            df_kick_local[col] = pd.to_numeric(
                df_kick_local[col], errors="coerce"
            ).fillna(0.0)

    vk_m3_local = float(vk_bbl_local) / 6.28981
    volume_restante_local = vk_m3_local
    altura_kick_local = 0.0
    elemento_topo_kick_local = "Não definido"
    intervalo_elemento_topo_kick_local = ""

    for _, row in df_kick_local.iterrows():
        cap = float(row["Cap. Anular (m3/m)"])
        comp = float(row["Comprimento (m)"])
        inicio = float(row["Início do Trecho (m)"])
        fim = float(row["Fim do Trecho (m)"])
        elem = str(row["Elemento do BHA"])

        if cap <= 0 or comp <= 0:
            continue

        vol_trecho = cap * comp

        if volume_restante_local <= vol_trecho:
            altura_no_trecho = volume_restante_local / cap
            altura_kick_local = inicio + altura_no_trecho
            elemento_topo_kick_local = elem
            intervalo_elemento_topo_kick_local = f"{inicio:.2f}–{fim:.2f} m"
            volume_restante_local = 0.0
            break
        else:
            volume_restante_local -= vol_trecho

    if volume_restante_local > 1e-9:
        altura_kick_local = float(df_kick_local["Comprimento Acumulado (m)"].max())
        elemento_topo_kick_local = "Acima do último elemento do BHA"
        intervalo_elemento_topo_kick_local = ""

    return (
        altura_kick_local,
        elemento_topo_kick_local,
        intervalo_elemento_topo_kick_local
    )


def sapata_repetida(bha, mapa_sapata_por_bha, sapatas_existentes):
    return mapa_sapata_por_bha.get(bha, "") in sapatas_existentes


def _fmt_pdf_val(valor, sufixo="", casas=2):
    try:
        if valor is None or pd.isna(valor):
            return "—"
        if isinstance(valor, (int, float, np.integer, np.floating)):
            return f"{float(valor):.{casas}f}{sufixo}"
        txt = str(valor).strip()
        return txt if txt else "—"
    except Exception:
        return "—"


def _nova_pagina_pdf(c, width, height, logo, footer_y, draw_header, titulo_pagina):
    draw_footer(c, width, footer_y)
    c.showPage()

    y = draw_header(c, width, height, logo)
    left_margin = 40
    right_margin = width - 40

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(left_margin, y, titulo_pagina)
    y -= 8
    c.line(left_margin, y, right_margin, y)
    y -= 18

    return y


def desenhar_linhas_duplas_pdf(
    c,
    width,
    height,
    logo,
    footer_y,
    draw_header,
    left_margin,
    right_margin,
    y_top,
    titulo_secao,
    linhas,
    titulo_pagina
):
    """
    linhas = [
        (("Label esquerda", "Valor esquerda"), ("Label direita", "Valor direita")),
        ...
    ]
    """
    if not linhas:
        return y_top

    secao_h = 20
    linha_h = 18
    altura_total = secao_h + len(linhas) * linha_h + 12

    if y_top - altura_total < footer_y + 35:
        y_top = _nova_pagina_pdf(
            c, width, height, logo, footer_y, draw_header, titulo_pagina
        )

    box_x = left_margin
    box_w = right_margin - left_margin
    box_y = y_top - altura_total

    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(box_x, box_y, box_w, altura_total, fill=1, stroke=0)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(box_x, box_y, box_w, altura_total, fill=0, stroke=1)

    c.line(box_x, box_y + altura_total - 18, box_x + box_w, box_y + altura_total - 18)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(box_x + 10, box_y + altura_total - 14, titulo_secao)

    meio_x = (left_margin + right_margin) / 2
    y_txt = box_y + altura_total - 34

    for esq, dir_ in linhas:
        lab_e, val_e = esq
        lab_d, val_d = dir_

        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_margin + 8, y_txt, f"{lab_e}")
        c.drawString(meio_x + 8, y_txt, f"{lab_d}")

        c.setFont("Helvetica", 9)
        c.drawString(left_margin + 155, y_txt, f"{val_e}")
        c.drawString(meio_x + 155, y_txt, f"{val_d}")

        y_txt -= linha_h

    return box_y - 14


def desenhar_blocos_fluido_pdf(
    c,
    width,
    height,
    logo,
    footer_y,
    draw_header,
    left_margin,
    right_margin,
    y_top,
    df_intervalos,
    titulo_pagina
):
    """
    Espera colunas como:
    - Topo do Intervalo (m)
    - Base do Intervalo (m)
    - Margem do Intervalo (lb/gal)
    - Peso do Fluido (lb/gal)
    - Linha média do Intervalo (lb/gal)
    """
    if df_intervalos is None or not isinstance(df_intervalos, pd.DataFrame) or df_intervalos.empty:
        return y_top

    df_plot = df_intervalos.copy()

    col_topo = "Topo do Intervalo (m)"
    col_base = "Base do Intervalo (m)"
    col_min = "Margem do Intervalo (lb/gal)"
    col_ideal = "Peso do Fluido (lb/gal)"
    col_max = "Linha média do Intervalo (lb/gal)"

    cols_req = [col_topo, col_base, col_min, col_ideal, col_max]
    cols_exist = [c_ for c_ in cols_req if c_ in df_plot.columns]

    if len(cols_exist) < 5:
        return y_top

    bloco_h = 58

    for i, (_, row) in enumerate(df_plot.iterrows(), start=1):
        if y_top - bloco_h < footer_y + 35:
            y_top = _nova_pagina_pdf(
                c, width, height, logo, footer_y, draw_header, titulo_pagina
            )

        topo = _fmt_pdf_val(row[col_topo], " m")
        base = _fmt_pdf_val(row[col_base], " m")
        minimo = _fmt_pdf_val(row[col_min], " lb/gal")
        ideal = _fmt_pdf_val(row[col_ideal], " lb/gal")
        maximo = _fmt_pdf_val(row[col_max], " lb/gal")

        box_x = left_margin
        box_w = right_margin - left_margin
        box_y = y_top - bloco_h

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_w, bloco_h, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_w, bloco_h, fill=0, stroke=1)

        c.line(box_x, box_y + bloco_h - 18, box_x + box_w, box_y + bloco_h - 18)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(
            box_x + 10,
            box_y + bloco_h - 14,
            f"Fase {i} - {topo} a {base}"
        )

        y_linha1 = box_y + 20

        c.setFont("Helvetica-Bold", 10)
        c.drawString(box_x + 30, y_linha1 + 10, "Mínimo")
        c.drawString(box_x + 220, y_linha1 + 10, "Ideal")
        c.drawString(box_x + 410, y_linha1 + 10, "Máximo")

        c.setFont("Helvetica", 10)
        c.drawString(box_x + 30, y_linha1 - 4, minimo)
        c.drawString(box_x + 220, y_linha1 - 4, ideal)
        c.drawString(box_x + 410, y_linha1 - 4, maximo)

        y_top = box_y - 10

    return y_top

def _asp_pol_para_float(valor):
    """
    Converte polegadas em texto ou número para float.

    Exemplos:
    '13 3/8"' -> 13.375
    '9 5/8"'  -> 9.625
    '17 1/2"' -> 17.5
    12.25     -> 12.25
    """
    if valor is None or pd.isna(valor):
        return np.nan

    if isinstance(valor, (int, float, np.integer, np.floating)):
        return float(valor)

    s = str(valor).strip()
    s = s.replace("Sapata", "")
    s = s.replace('"', "")
    s = s.replace("pol", "")
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9/\.\s-]", "", s)
    s = " ".join(s.split())

    if not s:
        return np.nan

    try:
        if " " in s and "/" in s:
            inteiro, frac = s.split(" ", 1)
            num, den = frac.split("/")
            return float(inteiro) + float(num) / float(den)

        if "/" in s:
            num, den = s.split("/")
            return float(num) / float(den)

        return float(s)

    except Exception:
        return np.nan


def _asp_fmt_pol(valor, max_denominador=16):
    """
    Formata polegadas em fração.

    13.375 -> 13 3/8
    9.625  -> 9 5/8
    17.5   -> 17 1/2
    """
    if valor is None or pd.isna(valor):
        return ""

    valor = float(valor)
    inteiro = int(valor)
    decimal = valor - inteiro

    if abs(decimal) < 1e-6:
        return str(inteiro)

    frac = Fraction(decimal).limit_denominator(max_denominador)

    if frac.numerator == frac.denominator:
        return str(inteiro + 1)

    if inteiro == 0:
        return f"{frac.numerator}/{frac.denominator}"

    return f"{inteiro} {frac.numerator}/{frac.denominator}"


def _asp_diam_fase_por_revestimento(diam_rev):
    """
    Estima o diâmetro da fase perfurada a partir do revestimento.
    Usado para condutor e superfície, porque eles vêm de odrc/odrs.
    """
    mapa = {
        30.0: 36.0,
        20.0: 26.0,
        13.375: 17.5,
        9.625: 12.25,
        7.0: 8.5,
        5.5: 6.125,
    }

    if diam_rev is None or pd.isna(diam_rev):
        return np.nan

    diam_rev = float(diam_rev)

    chave = min(mapa.keys(), key=lambda x: abs(x - diam_rev))

    if abs(chave - diam_rev) <= 0.05:
        return mapa[chave]

    return diam_rev * 1.25


def _asp_profundidade_final_poco():
    """
    Procura a profundidade final do poço nos dataframes já existentes do SYGA.
    """
    candidatos = []

    for nome_df in ["df_sapata_kt", "df_suav", "df_pp", "df"]:
        obj = st.session_state.get(nome_df, None)

        if isinstance(obj, pd.DataFrame) and not obj.empty:
            for col in ["Profundidade (m)", "Profundidade"]:
                if col in obj.columns:
                    prof = pd.to_numeric(obj[col], errors="coerce").dropna()
                    if not prof.empty:
                        candidatos.append(float(prof.max()))

    if "y" in st.session_state:
        try:
            y = pd.to_numeric(pd.Series(st.session_state.y), errors="coerce").dropna()
            if not y.empty:
                candidatos.append(float(y.max()))
        except Exception:
            pass

    if not candidatos:
        return None

    return max(candidatos)


def _asp_preparar_dados(df):
    df = df.copy()

    colunas_necessarias = [
        "fase",
        "tipo_trecho",
        "diam_furo",
        "diam_rev",
        "profundidade"
    ]

    for c in colunas_necessarias:
        if c not in df.columns:
            raise ValueError(f"Coluna ausente: {c}")

    df["fase"] = df["fase"].astype(str)
    df["tipo_trecho"] = df["tipo_trecho"].fillna("Revestido").astype(str)

    for c in ["diam_furo", "diam_rev", "profundidade"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["diam_furo", "profundidade"])
    df = df[df["profundidade"] > 0].copy()

    df = df.sort_values("profundidade").reset_index(drop=True)

    if df.empty:
        return df

    tipo_norm = df["tipo_trecho"].str.lower().str.strip()
    mask_aberto = tipo_norm == "poço aberto"

    if mask_aberto.any():
        if mask_aberto.sum() > 1:
            raise ValueError("Só pode existir um trecho em poço aberto, e ele deve ser a última fase.")

        if not bool(mask_aberto.iloc[-1]):
            raise ValueError("O trecho em poço aberto só pode ser informado na última fase.")

    df.loc[mask_aberto, "diam_rev"] = np.nan

    mask_revestido = ~mask_aberto

    if mask_revestido.any():
        if df.loc[mask_revestido, "diam_rev"].isna().any():
            raise ValueError("Todo trecho revestido precisa ter diâmetro de revestimento.")

    profundidades = df["profundidade"].to_numpy(dtype=float)

    if len(profundidades) > 1 and not np.all(np.diff(profundidades) > 0):
        raise ValueError("As profundidades devem estar em ordem estritamente crescente.")

    topo = [0.0]

    for i in range(1, len(df)):
        topo.append(float(df.loc[i - 1, "profundidade"]))

    df["topo_intervalo"] = topo
    df["base_intervalo"] = df["profundidade"]

    return df


def _asp_montar_df_esquematico_kt():
    """
    Monta automaticamente o dataframe do esquemático usando como fonte principal
    as mesmas sapatas plotadas no gráfico de Kick Tolerance.

    Fonte de verdade:
    - st.session_state.sapatas_plot_kt

    Regra:
    - Se a sapata aparece no gráfico de KT, aparece no esquemático.
    - Se não aparece no gráfico de KT, não é adicionada manualmente aqui.
    - O trecho de poço aberto é criado apenas do último revestimento até o final do perfil.
    """

    rows = []

    mapa_sapata_por_bha = {
        '17 1/2"': '13 3/8"',
        '12 1/4"': '9 5/8"',
        '8 1/2"': '7"',
        '6 1/8"': '5 1/2"',
    }

    mapa_rev_para_bha_aberto = {
        30.0: '26"',
        20.0: '17 1/2"',
        13.375: '12 1/4"',
        9.625: '8 1/2"',
        7.0: '6 1/8"',
        5.5: None,
    }

    def add_revestido(nome_fase, diam_furo, diam_rev, prof):
        diam_furo = _asp_pol_para_float(diam_furo)
        diam_rev = _asp_pol_para_float(diam_rev)

        if prof is None or pd.isna(prof):
            return

        prof = float(prof)

        if prof <= 0:
            return

        if pd.isna(diam_furo) or pd.isna(diam_rev):
            return

        rows.append({
            "fase": nome_fase,
            "tipo_trecho": "Revestido",
            "diam_furo": float(diam_furo),
            "diam_rev": float(diam_rev),
            "profundidade": prof,
        })

    def add_poco_aberto(nome_fase, diam_furo, prof):
        diam_furo = _asp_pol_para_float(diam_furo)

        if prof is None or pd.isna(prof):
            return

        prof = float(prof)

        if prof <= 0 or pd.isna(diam_furo):
            return

        rows.append({
            "fase": nome_fase,
            "tipo_trecho": "Poço aberto",
            "diam_furo": float(diam_furo),
            "diam_rev": np.nan,
            "profundidade": prof,
        })

    def inferir_bha_aberto_por_ultimo_revestimento(df_auto_local):
        if df_auto_local.empty or "diam_rev" not in df_auto_local.columns:
            return None

        df_rev_local = df_auto_local.dropna(subset=["diam_rev"]).copy()

        if df_rev_local.empty:
            return None

        df_rev_local = (
            df_rev_local
            .sort_values("profundidade")
            .reset_index(drop=True)
        )

        ultimo_rev = float(df_rev_local.iloc[-1]["diam_rev"])

        chave = min(
            mapa_rev_para_bha_aberto.keys(),
            key=lambda x: abs(x - ultimo_rev)
        )

        if abs(chave - ultimo_rev) <= 0.05:
            return mapa_rev_para_bha_aberto[chave]

        return None

    def inferir_diametros_da_sapata(sapata):
        nome = str(sapata.get("nome", ""))
        tipo = str(sapata.get("tipo", "")).lower().strip()
        bha = sapata.get("bha", None)

        diam_rev = _asp_pol_para_float(nome)

        if pd.isna(diam_rev):
            if "condutor" in tipo or "condutor" in nome.lower():
                diam_rev = _asp_pol_para_float(st.session_state.get("odrc", None))

            elif "superficie" in tipo or "superfície" in tipo or "superfície" in nome.lower():
                diam_rev = _asp_pol_para_float(st.session_state.get("odrs", None))

        if pd.isna(diam_rev) and bha in mapa_sapata_por_bha:
            diam_rev = _asp_pol_para_float(mapa_sapata_por_bha[bha])

        diam_furo = _asp_pol_para_float(bha)

        if pd.isna(diam_furo) and not pd.isna(diam_rev):
            diam_furo = _asp_diam_fase_por_revestimento(diam_rev)

        return diam_furo, diam_rev

    # ======================================================
    # Fonte principal: mesmas sapatas usadas no gráfico do KT
    # ======================================================
    sapatas_plot = st.session_state.get("sapatas_plot_kt", [])

    if not isinstance(sapatas_plot, list):
        sapatas_plot = []

    for sapata in sapatas_plot:
        try:
            prof = sapata.get("prof", None)
        except AttributeError:
            continue

        if prof is None or pd.isna(prof):
            continue

        prof = float(prof)

        diam_furo, diam_rev = inferir_diametros_da_sapata(sapata)

        if pd.isna(diam_furo) or pd.isna(diam_rev):
            continue

        add_revestido(
            nome_fase=f"Fase {len(rows)}",
            diam_furo=diam_furo,
            diam_rev=diam_rev,
            prof=prof
        )

    df_auto = pd.DataFrame(rows)

    if df_auto.empty:
        return df_auto

    df_auto = (
        df_auto
        .sort_values("profundidade")
        .drop_duplicates(subset=["profundidade"], keep="first")
        .reset_index(drop=True)
    )

    df_auto["fase"] = [f"Fase {i}" for i in range(len(df_auto))]

    # ======================================================
    # Poço aberto final
    # ======================================================
    prof_final = _asp_profundidade_final_poco()

    if prof_final is not None and not df_auto.empty:
        prof_final = float(prof_final)
        prof_ultima_sapata = float(df_auto["profundidade"].max())

        if prof_final > prof_ultima_sapata:
            bha_aberto = inferir_bha_aberto_por_ultimo_revestimento(df_auto)

            if bha_aberto is None:
                curvas_kt = st.session_state.get("curvas_kt_plot", [])

                if not curvas_kt:
                    curvas_kt = st.session_state.get("curvas_kt_b2c", [])

                if curvas_kt:
                    bha_aberto = curvas_kt[-1].get("bha", None)

            add_poco_aberto(
                nome_fase=f"Fase {len(df_auto)}",
                diam_furo=bha_aberto,
                prof=prof_final
            )

    df_auto = pd.DataFrame(rows)

    if df_auto.empty:
        return df_auto

    df_auto = (
        df_auto
        .sort_values("profundidade")
        .reset_index(drop=True)
    )

    df_auto["fase"] = [f"Fase {i}" for i in range(len(df_auto))]

    return df_auto


def _asp_desenhar_cabecote(ax, x_lim, h_top):
    mesa_larg = x_lim * 1.20
    mesa_alt = h_top * 0.12

    mesa = Rectangle(
        (-mesa_larg / 2, -mesa_alt * 0.20),
        mesa_larg,
        mesa_alt,
        facecolor="#d9d9d9",
        edgecolor="black",
        linewidth=1.2,
        hatch="//////",
        zorder=20
    )
    ax.add_patch(mesa)

    n = 140
    xs = np.linspace(-mesa_larg / 2, mesa_larg / 2, n)

    for x in xs:
        y0 = -mesa_alt * 0.20
        y1 = y0 - np.random.uniform(h_top * 0.01, h_top * 0.045)
        ax.plot([x, x], [y0, y1], color="#77b255", lw=1.5, zorder=19)

    y0 = -h_top * 0.15
    larguras = [x_lim * 0.42, x_lim * 0.36, x_lim * 0.28, x_lim * 0.20]
    alturas = [h_top * 0.09, h_top * 0.08, h_top * 0.08, h_top * 0.07]
    offsets = [0.00, -h_top * 0.08, -h_top * 0.16, -h_top * 0.23]

    for w, h, off in zip(larguras, alturas, offsets):
        ax.add_patch(
            Rectangle(
                (-w / 2, y0 + off),
                w,
                h,
                facecolor="red",
                edgecolor="black",
                linewidth=1.1,
                zorder=21
            )
        )

    for side in [-1, 1]:
        for yy in [y0 - h_top * 0.08, y0]:
            ax.add_patch(
                Rectangle(
                    (side * x_lim * 0.12 - x_lim * 0.02, yy + h_top * 0.025),
                    x_lim * 0.04,
                    h_top * 0.02,
                    facecolor="black",
                    edgecolor="black",
                    zorder=22
                )
            )


def _asp_desenhar_sapata(ax, x_left, x_right, parede, y, dx, dy):
    """
    Sapata com base na profundidade correta e ponta para cima.
    """
    pol_esq = Polygon(
        [
            [x_left - dx, y],
            [x_left + parede, y],
            [x_left, y - dy],
        ],
        closed=True,
        facecolor="black",
        edgecolor="black",
        zorder=15
    )

    pol_dir = Polygon(
        [
            [x_right - parede, y],
            [x_right + dx, y],
            [x_right, y - dy],
        ],
        closed=True,
        facecolor="black",
        edgecolor="black",
        zorder=15
    )

    ax.add_patch(pol_esq)
    ax.add_patch(pol_dir)


def _asp_plotar_esquematico(df):
    df = _asp_preparar_dados(df)

    if df.empty:
        return None, None

    parede_padrao = 0.45

    prof_final = float(df["base_intervalo"].max())
    diam_max = float(df["diam_furo"].max())

    tipo_norm = df["tipo_trecho"].str.lower().str.strip()

    df_revestido = df[tipo_norm != "poço aberto"].copy()

    ultima_eh_poco_aberto = tipo_norm.iloc[-1] == "poço aberto"

    if ultima_eh_poco_aberto:
        df_aberto = df.tail(1).copy()
    else:
        df_aberto = df.iloc[0:0].copy()

    x_lim = diam_max * 0.95
    h_top = max(120.0, prof_final * 0.12)

    fig = plt.figure(figsize=(8, 10.4))
    ax = fig.add_subplot(111)

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    cor_interna = "#b8d5e5"
    cor_cimento = "#a6a6a6"
    cor_furo = "#d9d9d9"
    cor_poco_aberto = "#d8c3a5"

    # Marca d'água, se a função existir no teu código
    try:
        add_watermark(
            ax,
            logo_path="logo2.png",
            xy=(0.22, 0.13),
            zoom=0.16,
            alpha=1,
            zorder=0.5
        )
    except Exception:
        pass

    # 1) Cabeçote
    _asp_desenhar_cabecote(ax, x_lim, h_top)

    # 2) Hatch/fundo apenas no poço aberto
    for _, row in df_aberto.iterrows():
        topo_aberto = float(row["topo_intervalo"])
        base_aberto = float(row["base_intervalo"])
        diam_furo = float(row["diam_furo"])

        ax.add_patch(
            Rectangle(
                (-diam_furo / 2, topo_aberto),
                diam_furo,
                base_aberto - topo_aberto,
                facecolor=cor_poco_aberto,
                edgecolor="black",
                linewidth=0.0,
                hatch=".",
                zorder=1
            )
        )

    # 3) Cimento dos trechos revestidos
    if not df_revestido.empty:
        df_cimento = df_revestido.sort_values("base_intervalo").reset_index(drop=True)

        for i, row in df_cimento.iterrows():
            sapata = float(row["base_intervalo"])
            diam_rev = float(row["diam_rev"])

            topo_cimento = 0.0
            altura_cimento = sapata - topo_cimento

            x_left_rev_ext = -diam_rev / 2
            x_right_rev_ext = diam_rev / 2

            if i == 0:
                diam_furo = float(row["diam_furo"])
                x_left_lim = -diam_furo / 2
                x_right_lim = diam_furo / 2
            else:
                diam_rev_anterior = float(df_cimento.loc[i - 1, "diam_rev"])
                x_left_lim = -diam_rev_anterior / 2 + parede_padrao
                x_right_lim = diam_rev_anterior / 2 - parede_padrao

            if x_left_rev_ext > x_left_lim:
                ax.add_patch(
                    Rectangle(
                        (x_left_lim, topo_cimento),
                        x_left_rev_ext - x_left_lim,
                        altura_cimento,
                        facecolor=cor_cimento,
                        edgecolor="none",
                        alpha=0.95,
                        zorder=2
                    )
                )

            if x_right_lim > x_right_rev_ext:
                ax.add_patch(
                    Rectangle(
                        (x_right_rev_ext, topo_cimento),
                        x_right_lim - x_right_rev_ext,
                        altura_cimento,
                        facecolor=cor_cimento,
                        edgecolor="none",
                        alpha=0.95,
                        zorder=2
                    )
                )

    # 4) Revestimentos e sapatas
    dy_sapata = max(8.0, prof_final * 0.008)
    dx_sapata = max(0.6, diam_max * 0.06)

    if not df_revestido.empty:
        df_rev_plot = df_revestido.sort_values(
            "diam_rev",
            ascending=False
        ).reset_index(drop=True)

        for _, row in df_rev_plot.iterrows():
            diam_rev = float(row["diam_rev"])
            sapata = float(row["base_intervalo"])

            x_left = -diam_rev / 2
            x_right = diam_rev / 2
            parede = parede_padrao

            topo_revestimento = 0.0
            altura_revestimento = sapata - topo_revestimento

            ax.add_patch(
                Rectangle(
                    (x_left, topo_revestimento),
                    parede,
                    altura_revestimento,
                    facecolor="black",
                    edgecolor="black",
                    linewidth=0.8,
                    zorder=10
                )
            )

            ax.add_patch(
                Rectangle(
                    (x_right - parede, topo_revestimento),
                    parede,
                    altura_revestimento,
                    facecolor="black",
                    edgecolor="black",
                    linewidth=0.8,
                    zorder=10
                )
            )

            _asp_desenhar_sapata(
                ax=ax,
                x_left=x_left,
                x_right=x_right,
                parede=parede,
                y=sapata,
                dx=dx_sapata,
                dy=dy_sapata
            )

            texto = f'Sapata {_asp_fmt_pol(diam_rev)}"'

            ax.annotate(
                texto,
                xy=(x_left - dx_sapata * 0.15, sapata),
                xytext=(-x_lim * 0.72, sapata),
                ha="right",
                va="center",
                fontsize=11,
                fontweight="bold",
                arrowprops=dict(
                    arrowstyle="-",
                    linestyle=(0, (8, 4)),
                    color="black",
                    lw=1.0
                ),
                zorder=30
            )

    # 5) Borda do poço aberto sem linha no topo
    for _, row in df_aberto.iterrows():
        topo_aberto = float(row["topo_intervalo"])
        base_aberto = float(row["base_intervalo"])
        diam_furo = float(row["diam_furo"])

        x_left = -diam_furo / 2
        x_right = diam_furo / 2

        ax.plot(
            [x_left, x_left],
            [topo_aberto, base_aberto],
            color="black",
            linewidth=1.0,
            zorder=11
        )

        ax.plot(
            [x_right, x_right],
            [topo_aberto, base_aberto],
            color="black",
            linewidth=1.0,
            zorder=11
        )

        ax.plot(
            [x_left, x_right],
            [base_aberto, base_aberto],
            color="black",
            linewidth=1.0,
            zorder=11
        )

    # 6) Azul apenas dentro do último revestimento
    if not df_revestido.empty:
        ultimo_rev = df_revestido.sort_values("base_intervalo").iloc[-1]

        diam_rev = float(ultimo_rev["diam_rev"])
        sapata = float(ultimo_rev["base_intervalo"])

        x_left = -diam_rev / 2
        largura_interna = max(diam_rev - 2 * parede_padrao, 0.05)

        ax.add_patch(
            Rectangle(
                (x_left + parede_padrao, 0.0),
                largura_interna,
                sapata,
                facecolor=cor_interna,
                edgecolor="none",
                zorder=4
            )
        )

    # 7) Azul dentro do poço aberto
    for _, row in df_aberto.iterrows():
        topo_aberto = float(row["topo_intervalo"])
        base_aberto = float(row["base_intervalo"])
        diam_furo = float(row["diam_furo"])

        diam_aberto_interno = diam_furo * 0.52

        ax.add_patch(
            Rectangle(
                (-diam_aberto_interno / 2, topo_aberto),
                diam_aberto_interno,
                base_aberto - topo_aberto,
                facecolor=cor_interna,
                edgecolor="none",
                zorder=5
            )
        )

        # ax.text(
        #     diam_furo / 2 + diam_max * 0.04,
        #     (topo_aberto + base_aberto) / 2,
        #     "Poço aberto",
        #     ha="left",
        #     va="center",
        #     fontsize=10,
        #     fontweight="bold",
        #     bbox=dict(
        #         facecolor="white",
        #         edgecolor="red",
        #         boxstyle="round,pad=0.2"
        #     ),
        #     zorder=40
        # )

    # 8) Caixas laterais
    for i, (_, row) in enumerate(df.iterrows()):
        # Remove a primeira caixa, referente ao revestimento condutor / Fase 0
        if i == 0:
            continue

        tipo = row["tipo_trecho"].strip().lower()
        topo = float(row["topo_intervalo"])
        base = float(row["base_intervalo"])
        diam_furo = float(row["diam_furo"])

        if tipo == "poço aberto":
            txt = (
                f'{row["fase"]}\n'
                f"Poço aberto\n"
                f'Diâmetro da fase: {_asp_fmt_pol(diam_furo)}"\n'
                f"Fundo: {base:.1f} m"
            )
        else:
            txt = (
                f'{row["fase"]}\n'
                f'Rev.: {_asp_fmt_pol(row["diam_rev"])}"\n'
                f'Diâmetro da fase: {_asp_fmt_pol(diam_furo)}"\n'
                f"Sapata: {base:.1f} m"
            )

        ax.text(
            x_lim * 0.45,
            (topo + base) / 2,
            txt,
            ha="left",
            va="center",
            fontsize=11,
            bbox=dict(
                facecolor="white",
                edgecolor="black",
                boxstyle="round,pad=0.2"
            ),
            zorder=40
        )
    # 9) linhas pretas nas laterais do hatch do poço aberto
    for _, row in df_aberto.iterrows():
        topo_aberto = float(row["topo_intervalo"])
        base_aberto = float(row["base_intervalo"])
        diam_furo = float(row["diam_furo"])

        x_left = -diam_furo / 2
        x_right = diam_furo / 2

        # lateral esquerda do poço aberto
        ax.plot(
            [x_left, x_left],
            [topo_aberto, base_aberto],
            color="black",
            linewidth=1.2,
            zorder=50
        )

        # lateral direita do poço aberto
        ax.plot(
            [x_right, x_right],
            [topo_aberto, base_aberto],
            color="black",
            linewidth=1.2,
            zorder=50
        )

    ax.set_xlim(-x_lim * 1.38, x_lim * 1.22)
    ax.set_ylim(prof_final + prof_final * 0.04, -h_top * 0.35)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Esquemático do poço", fontsize=14, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color("black")

    ax.grid(False)
    plt.tight_layout()

    return fig, df


PAGINAS_PDF_OPCOES = {
    "dados_poco_elevacao": "Dados do Poço | Elevação e localização",
    "dados_poco_resumo": "Dados do Poço | Resumo dos dados",
    "analise_por_fase": "Análise por fase",
    "sobrecarga": "Sobrecarga",
    "pressao_poros_lbf": "Pressão de Poros | Dados e LBF",
    "pressao_poros_trending": "Pressão de Poros | Trending",
    "estabilidade_trajetoria": "Estabilidade de Poço e Trajetória",
    "janela_operacional": "Janela Operacional",
    "mohr_coulomb": "Critério de Falha de Mohr Coulomb",
    "sapatas_previsao": "Assentamento de Sapatas | Previsão",
    "esquematico_poco_previsao": "Esquemático do Poço | Previsão",
    "fluido_previsao": "Fluido de Perfuração | Previsão",
    "fratura_tensoes_minimas": "Gradiente de Fratura | Tensões Mínimas",
    "anotacoes": "Anotações",
    "trajetoria_eventos": "Eventos Operacionais",
}


def gerar_relatorio_pdf():
    hora_now = datetime.now() + timedelta(hours=0)
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    width, height = letter
    footer_y = 30

    paginas_pdf_selecionadas = set(
        st.session_state.get(
            "pdf_paginas_selecionadas",
            list(PAGINAS_PDF_OPCOES.keys())
        )
    )
    def pagina_pdf_ativa(chave):
        return chave in paginas_pdf_selecionadas

    # ==============================
    # Página 1
    # ==============================
    c.drawImage(logo, 230, height - 100, width=150, height=100)

    # --- Títulos principais ---
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(width / 2, height - 260, "Syngular Geopressure Analysis - SYGA")

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 295, "Relatório Final")

    # --- Informações do poço e responsável ---
    well_name = f"{st.session_state.poco}"
    user_name = f"{st.session_state.user_name}"

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 340, well_name)

    c.setFont("Helvetica", 15)
    c.drawCentredString(width / 2, height - 370, f"Responsável Técnico: {user_name}")

    # --- Rodapé ---
    c.setFont("Helvetica", 12)

    # Linha separadora
    c.line(30, 80, width - 30, 80)

    # Informações da empresa (lado esquerdo)
    c.drawString(40, 60, "Syngular Solutions")
    c.drawString(40, 45, "Houston, TX 77077")

    # Data e hora (lado direito)
    data_relatorio = datetime.today().strftime('%d/%m/%Y')
    hora_relatorio = hora_now.strftime('%H:%M')

    c.drawRightString(width - 40, 60, f"Data do Relatório: {data_relatorio} {hora_relatorio}")

    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(75, 90,"V-1.0")

    c.showPage()

    footer_y = 20  # valor único para toda a página

    def draw_header(c, width, height, logo):
        logo_width = 150
        logo_height = 100
        logo_y = height - 90

        c.drawImage(
            logo,
            (width - logo_width) / 2,
            logo_y,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        return logo_y - 10
    def _fmt_pdf_val(valor, sufixo="", casas=2):
        try:
            if valor is None or pd.isna(valor):
                return "—"

            if isinstance(valor, (int, float, np.integer, np.floating)):
                return f"{float(valor):.{casas}f}{sufixo}"

            txt = str(valor).strip()
            return txt if txt else "—"

        except Exception:
            return "—"
    def _draw_text_fit(c, x, y, txt, max_width, font_name="Helvetica", font_size=8):
        txt = str(txt)
        c.setFont(font_name, font_size)

        if c.stringWidth(txt, font_name, font_size) <= max_width:
            c.drawString(x, y, txt)
            return

        while txt and c.stringWidth(txt + "...", font_name, font_size) > max_width:
            txt = txt[:-1]

        c.drawString(x, y, txt + "...")
    def _abrir_pagina_pdf_com_titulo(titulo_pagina):
        draw_footer(c, width, footer_y)
        c.showPage()

        y_local = draw_header(c, width, height, logo)

        left_margin_local = 40
        right_margin_local = width - 40

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin_local, y_local, titulo_pagina)

        y_local -= 8
        c.line(left_margin_local, y_local, right_margin_local, y_local)
        y_local -= 18

        return y_local
    def desenhar_linhas_duplas_pdf(y_top,titulo_secao,linhas,titulo_pagina,left_margin=40,right_margin=None):
        """
        Desenha tabela no mesmo padrão da Página 11:
        - caixa cinza
        - borda preta
        - título superior
        - duas colunas
        - label em negrito
        - valor em fonte normal
        """

        if right_margin is None:
            right_margin = width - 40

        if not linhas:
            return y_top

        linha_altura = 15
        box_height = 30 + len(linhas) * linha_altura

        box_width = right_margin - left_margin
        box_x = left_margin

        if y_top - box_height < footer_y + 35:
            y_top = _abrir_pagina_pdf_com_titulo(titulo_pagina)

        y_top -= 14
        box_y = y_top - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(
            box_x,
            box_y + box_height - 18,
            box_x + box_width,
            box_y + box_height - 18
        )

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(
            box_x + 10,
            box_y + box_height - 14,
            titulo_secao
        )

        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box_y + box_height - 32

        col_width = box_width / 2 - 18
        def draw_label_valor(x, y, label, valor, max_width):
            label = str(label)
            valor = str(valor)

            c.setFont("Helvetica-Bold", 9)
            label_width = c.stringWidth(label, "Helvetica-Bold", 9)

            valor_x = x + label_width + 4
            valor_width = max_width - label_width - 4

            # Se o label ficar grande demais, reduz ele com reticências
            if valor_width < 45:
                label_reduzido = label
                while (
                        label_reduzido
                        and c.stringWidth(label_reduzido + "...", "Helvetica-Bold", 9) > max_width * 0.62
                ):
                    label_reduzido = label_reduzido[:-1]

                label = label_reduzido + "..."
                label_width = c.stringWidth(label, "Helvetica-Bold", 9)
                valor_x = x + label_width + 4
                valor_width = max_width - label_width - 4

            c.setFont("Helvetica-Bold", 9)
            c.drawString(x, y, label)

            c.setFont("Helvetica", 9)

            valor_reduzido = valor
            while (
                    valor_reduzido
                    and c.stringWidth(valor_reduzido + "...", "Helvetica", 9) > valor_width
            ):
                valor_reduzido = valor_reduzido[:-1]

            if valor_reduzido != valor:
                valor_reduzido += "..."

            c.drawString(valor_x, y, valor_reduzido)
        for par_esq, par_dir in linhas:
            label_esq, valor_esq = par_esq
            label_dir, valor_dir = par_dir

            draw_label_valor(
                col1_x,
                texto_y,
                label_esq,
                valor_esq,
                col_width
            )

            draw_label_valor(
                col2_x,
                texto_y,
                label_dir,
                valor_dir,
                col_width
            )

            texto_y -= linha_altura

        return box_y - 12
    def desenhar_blocos_fluido_pdf(y_top,df_intervalos,titulo_pagina,left_margin=40,right_margin=None):
        """
        Desenha a página de fluido como uma única tabela compacta,
        mantendo o padrão visual da Página 11.

        Colunas:
        Fase | Intervalo | Mínimo | Ideal | Máximo
        """

        if right_margin is None:
            right_margin = width - 40

        if (
            df_intervalos is None
            or not isinstance(df_intervalos, pd.DataFrame)
            or df_intervalos.empty
        ):
            return y_top

        col_topo = "Topo do Intervalo (m)"
        col_base = "Base do Intervalo (m)"
        col_min = "Margem do Intervalo (lb/gal)"
        col_ideal = "Peso do Fluido (lb/gal)"
        col_max = "Linha média do Intervalo (lb/gal)"

        cols_req = [
            col_topo,
            col_base,
            col_min,
            col_ideal,
            col_max
        ]

        if any(col not in df_intervalos.columns for col in cols_req):
            return y_top

        rows = []

        for i, (_, row) in enumerate(df_intervalos.iterrows(), start=1):
            topo = _fmt_pdf_val(row[col_topo], " m")
            base = _fmt_pdf_val(row[col_base], " m")
            minimo = _fmt_pdf_val(row[col_min], " lb/gal")
            ideal = _fmt_pdf_val(row[col_ideal], " lb/gal")
            maximo = _fmt_pdf_val(row[col_max], " lb/gal")

            rows.append([
                f"Fase {i}",
                f"{topo} a {base}",
                minimo,
                ideal,
                maximo
            ])

        if not rows:
            return y_top

        linha_altura = 15
        header_altura = 15
        titulo_altura = 18

        box_width = right_margin - left_margin
        box_x = left_margin

        col_fracs = [0.13, 0.31, 0.18, 0.18, 0.20]
        col_widths = [box_width * frac for frac in col_fracs]

        headers = [
            "Fase",
            "Intervalo",
            "Mínimo",
            "Ideal",
            "Máximo"
        ]

        def draw_text_fit_left(x, y, txt, max_width, font_name="Helvetica", font_size=8):
            txt = str(txt)
            c.setFont(font_name, font_size)

            if c.stringWidth(txt, font_name, font_size) <= max_width:
                c.drawString(x, y, txt)
                return

            txt_reduzido = txt
            while (
                txt_reduzido
                and c.stringWidth(txt_reduzido + "...", font_name, font_size) > max_width
            ):
                txt_reduzido = txt_reduzido[:-1]

            c.drawString(x, y, txt_reduzido + "...")

        i = 0
        primeiro_bloco = True

        while i < len(rows):
            # Altura disponível na página atual
            altura_disponivel = y_top - (footer_y + 35)

            max_linhas = int(
                (altura_disponivel - 30 - header_altura) // linha_altura
            )

            if max_linhas < 1:
                y_top = _abrir_pagina_pdf_com_titulo(titulo_pagina)
                altura_disponivel = y_top - (footer_y + 35)

                max_linhas = int(
                    (altura_disponivel - 30 - header_altura) // linha_altura
                )

            max_linhas = max(1, max_linhas)

            rows_bloco = rows[i:i + max_linhas]

            titulo_tabela = "Peso de fluido por fase"
            if not primeiro_bloco:
                titulo_tabela = "Peso de fluido por fase (continuação)"

            box_height = 30 + header_altura + len(rows_bloco) * linha_altura

            y_top -= 14
            box_y = y_top - box_height

            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

            c.line(
                box_x,
                box_y + box_height - 18,
                box_x + box_width,
                box_y + box_height - 18
            )

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(
                box_x + 10,
                box_y + box_height - 14,
                titulo_tabela
            )

            texto_y = box_y + box_height - 32

            x_cols = [box_x + 8]
            for w_col in col_widths[:-1]:
                x_cols.append(x_cols[-1] + w_col)

            # Cabeçalho da tabela
            for j, header in enumerate(headers):
                c.setFont("Helvetica-Bold", 8)
                draw_text_fit_left(
                    x_cols[j],
                    texto_y,
                    header,
                    col_widths[j] - 10,
                    font_name="Helvetica-Bold",
                    font_size=8
                )

            c.setLineWidth(0.5)
            c.line(
                box_x + 8,
                texto_y - 4,
                box_x + box_width - 8,
                texto_y - 4
            )

            texto_y -= header_altura

            # Linhas da tabela
            for row in rows_bloco:
                for j, txt in enumerate(row):
                    draw_text_fit_left(
                        x_cols[j],
                        texto_y,
                        txt,
                        col_widths[j] - 10,
                        font_name="Helvetica",
                        font_size=8
                    )

                texto_y -= linha_altura

            y_top = box_y - 12

            i += len(rows_bloco)
            primeiro_bloco = False

            if i < len(rows):
                y_top = _abrir_pagina_pdf_com_titulo(titulo_pagina)

        return y_top

    # ==============================
    # Página 2
    # ==============================
    if pagina_pdf_ativa("dados_poco_elevacao"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Dados do Poço")
        y -= 10
        c.line(left_margin, y, right_margin, y)

        # Espaço inicial
        y -= 14

        page_top = y
        page_bottom = footer_y + 20

        usable_h = page_top - page_bottom
        usable_w = right_margin - left_margin

        pad = 10
        mid_y = page_bottom + usable_h / 2

        def desenhar_caixa_padrao(titulo, x_left, x_right, y_top, y_bottom):
            box_x = x_left
            box_w = x_right - x_left
            box_y = y_bottom
            box_h = y_top - y_bottom

            if box_h < 40 or box_w < 80:
                return (x_left, x_right, y_top, y_bottom)

            # fundo
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)

            # borda
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)

            # linha do título
            c.line(box_x, box_y + box_h - 18, box_x + box_w, box_y + box_h - 18)

            # título
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(box_x + box_w / 2, box_y + box_h - 14, titulo)

            # área útil
            inner_left = box_x + 10
            inner_right = box_x + box_w - 10
            inner_top = box_y + box_h - 24
            inner_bottom = box_y + 10

            return inner_left, inner_right, inner_top, inner_bottom

        box_sup_left = left_margin
        box_sup_right = right_margin
        box_sup_top = page_top
        box_sup_bottom = mid_y + 8

        sup_left, sup_right, sup_top, sup_bottom = desenhar_caixa_padrao(
            titulo="Referência de Elevação",
            x_left=box_sup_left,
            x_right=box_sup_right,
            y_top=box_sup_top,
            y_bottom=box_sup_bottom
        )

        if st.session_state.onshore:
            img_path = "rig.png"
        else:
            img_path = "rig_offshore.png"

        img_height = 240
        img_width = img_height * 0.65

        img_offset_x = 80
        img_offset_y = 0

        img_x = sup_left + img_offset_x
        img_y = sup_top - img_height + img_offset_y

        if img_y < sup_bottom:
            img_y = sup_bottom + 5

        c.drawImage(
            img_path,
            img_x,
            img_y,
            width=img_width,
            height=img_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        texto_offset_x = 5
        texto_base_y = img_y + img_height
        texto_x = img_x + img_width + texto_offset_x

        pos_datum = -78
        pos_ele_datum = -108
        pos_airgap = -130
        pos_solo = -152
        pos_ele_solo = -190
        pos_nivel_mar = -228

        c.setFont("Helvetica-Bold", 12)

        c.drawString(
            texto_x,
            texto_base_y + pos_datum,
            f"DATUM: {st.session_state.datum}"
        )

        c.drawString(
            texto_x,
            texto_base_y + pos_airgap,
            f"Airgap: {st.session_state.rtkb:.2f} metros"
        )

        if st.session_state.onshore:
            c.drawString(
                texto_x,
                texto_base_y + pos_ele_datum,
                f"Elevação DATUM: {st.session_state.es:.2f} metros"
            )

            c.drawString(
                texto_x,
                texto_base_y + pos_solo,
                "Solo"
            )

            c.drawString(
                texto_x,
                texto_base_y + pos_ele_solo,
                f"Elevação do solo: {(st.session_state.es - st.session_state.rtkb):.2f} metros"
            )

            c.drawString(
                texto_x,
                texto_base_y + pos_nivel_mar,
                "Nível do mar"
            )
        else:
            pos_lamina = -160
            pos_leito = -230

            c.drawString(
                texto_x,
                texto_base_y + pos_lamina,
                f"Lâmina d'água: {st.session_state.lda:.2f} metros"
            )

            c.drawString(
                texto_x,
                texto_base_y + pos_leito,
                "Leito marinho"
            )

        box_map_left = left_margin
        box_map_right = right_margin
        box_map_top = mid_y - 10
        box_map_bottom = page_bottom

        nome_poco = st.session_state.get("poco", "Poço")

        map_left, map_right, map_top, map_bottom = desenhar_caixa_padrao(
            titulo=f'Localização do poço {nome_poco}',
            x_left=box_map_left,
            x_right=box_map_right,
            y_top=box_map_top,
            y_bottom=box_map_bottom
        )

        mapa_folium_pdf = st.session_state.get("mapa_folium_pdf", None)

        if mapa_folium_pdf is not None and map_top > map_bottom + 40:
            try:
                desenhar_mapa_folium_no_pdf(
                    c=c,
                    mapa_folium=mapa_folium_pdf,
                    left=map_left,
                    right=map_right,
                    top=map_top,
                    bottom=map_bottom
                )
            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(
                    map_left,
                    map_top - 15,
                    f"Não foi possível inserir o mapa: {e}"
                )
        else:
            c.setFont("Helvetica", 10)
            c.drawString(
                map_left,
                map_top - 15,
                "Mapa: Não informado"
            )

        # Rodapé
        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 3
    # ==============================
    if pagina_pdf_ativa("dados_poco_resumo"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Dados do Poço")
        y -= 10
        c.line(left_margin, y, right_margin, y)

        def _safe_str(v, default="Não informado"):
            if v is None or str(v).strip() == "":
                return default
            return str(v)

        def _fmt_coord(v, suf="", nd=2):
            try:
                if v is None or pd.isna(v):
                    return "Não informado"
                return f"{float(v):.{nd}f}{suf}"
            except Exception:
                return "Não informado"

        def _fmt_float(v, suf="", nd=0):
            try:
                if v is None or pd.isna(v):
                    return "—"
                return f"{float(v):.{nd}f}{suf}"
            except Exception:
                return "—"

        def desenhar_caixa_padrao(titulo, x_left, x_right, y_top, y_bottom):
            box_x = x_left
            box_w = x_right - x_left
            box_y = y_bottom
            box_h = y_top - y_bottom

            if box_h < 40 or box_w < 80:
                return (x_left, x_right, y_top, y_bottom)

            # fundo
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, box_y, box_w, box_h, fill=1, stroke=0)

            # borda
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)

            # linha do título
            c.line(box_x, box_y + box_h - 18, box_x + box_w, box_y + box_h - 18)

            # título centralizado
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(box_x + box_w / 2, box_y + box_h - 14, titulo)

            # área útil
            inner_left = box_x + 10
            inner_right = box_x + box_w - 10
            inner_top = box_y + box_h - 24
            inner_bottom = box_y + 10

            return inner_left, inner_right, inner_top, inner_bottom

        y -= 18

        comments = st.session_state.comments or ""
        comment_lines = wrap(comments, 95) if comments else ["Não informado"]

        info_linhas = [
            (
                "Usuário:", _safe_str(st.session_state.get("user_name", None)),
                "Companhia:", _safe_str(st.session_state.get("company_name", None))
            ),
            (
                "Poço:", _safe_str(st.session_state.get("poco", None)),
                "País:", _safe_str(st.session_state.get("country_name", None))
            ),
            (
                "Campo:", _safe_str(st.session_state.get("field_name", None)),
                "Zona UTM:", _safe_str(st.session_state.get("zona", None))
            ),
            (
                "Northing:", _fmt_coord(st.session_state.get("northing", None), " m", 2),
                "Easting:", _fmt_coord(st.session_state.get("easting", None), " m", 2)
            ),
            (
                "Hemisfério:", _safe_str(st.session_state.get("hem", None)),
                "", ""
            ),
        ]

        linha_altura = 16
        header_h = 28
        objetivo_h = 20 + len(comment_lines) * 14
        box_info_h = header_h + len(info_linhas) * linha_altura + 12 + objetivo_h + 8

        box_info_top = y
        box_info_bottom = y - box_info_h

        info_left, info_right, info_top, info_bottom = desenhar_caixa_padrao(
            titulo="Informações do Poço",
            x_left=left_margin,
            x_right=right_margin,
            y_top=box_info_top,
            y_bottom=box_info_bottom
        )

        col1_x = info_left + 2
        col2_x = info_left + (info_right - info_left) / 2 + 8
        texto_y = info_top - 8

        for label1, valor1, label2, valor2 in info_linhas:
            if label1:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label1)
                w1 = c.stringWidth(label1, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                c.drawString(col1_x + w1 + 5, texto_y, str(valor1))

            if label2:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col2_x, texto_y, label2)
                w2 = c.stringWidth(label2, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                txt_x = col2_x + w2 + 5
                c.drawString(txt_x, texto_y, str(valor2))

                if label2 == "País:":
                    codigo_pais = paises.get(str(valor2))
                    if codigo_pais:
                        flag_path = f"flag/{codigo_pais}.png"
                        try:
                            flag_x = txt_x + c.stringWidth(str(valor2), "Helvetica", 10) + 8
                            flag_y = texto_y - 2
                            c.drawImage(
                                flag_path,
                                flag_x,
                                flag_y,
                                width=18,
                                height=12,
                                preserveAspectRatio=True,
                                mask='auto'
                            )
                        except Exception:
                            pass

            texto_y -= linha_altura

        # separador
        c.line(info_left, texto_y + 4, info_right, texto_y + 4)

        # objetivo
        texto_y -= 12
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col1_x, texto_y, "Objetivo:")
        texto_y -= 14

        c.setFont("Helvetica", 10)
        for line in comment_lines:
            c.drawString(col1_x, texto_y, line)
            texto_y -= 14

        pocos_dict = st.session_state.get("pocos", {})
        well_selected = st.session_state.get("well_selected", None)

        if well_selected not in pocos_dict and isinstance(pocos_dict, dict) and pocos_dict:
            well_selected = list(pocos_dict.keys())[0]

        poco_ativo = pocos_dict.get(well_selected, {}) if isinstance(pocos_dict, dict) else {}

        profs = poco_ativo.get("profundidade", [])
        fms = poco_ativo.get("formation", [])
        lits = poco_ativo.get("litologia", [])

        camadas = []
        if isinstance(profs, list) and isinstance(fms, list) and isinstance(lits, list):
            n = min(len(profs), len(fms), len(lits))
            for i in range(n):
                topo = profs[i]
                fm = fms[i]
                lit = lits[i]

                if (topo is None or (isinstance(topo, (int, float)) and float(topo) == 0.0)) and i != 0:
                    continue

                camadas.append((topo, fm, lit))

        if not camadas:
            camadas = [(None, "Não informado", "—")]

        # usa TODAS as camadas
        camadas_visiveis = camadas

        y = box_info_bottom - 12

        linha_altura_lito = 11
        header_h_lito = 24
        margem_interna_lito = 8

        altura_tabela_lito = header_h_lito + (len(camadas_visiveis) + 1) * linha_altura_lito + margem_interna_lito

        box_lito_top = y
        box_lito_bottom = y - altura_tabela_lito

        lito_left, lito_right, lito_top, lito_bottom = desenhar_caixa_padrao(
            titulo="Litologia",
            x_left=left_margin,
            x_right=right_margin,
            y_top=box_lito_top,
            y_bottom=box_lito_bottom
        )

        x_topo = lito_left + 2
        x_fm = lito_left + (lito_right - lito_left) * 0.24
        x_lit = lito_left + (lito_right - lito_left) * 0.66

        yy = lito_top - 4
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_topo, yy, "Topo (m)")
        c.drawString(x_fm, yy, "Formação")
        c.drawString(x_lit, yy, "Litologia")

        c.setLineWidth(0.5)
        c.line(lito_left, yy - 3, lito_right, yy - 3)

        yy -= 12
        c.setFont("Helvetica", 8.5)

        for topo, fm, lit in camadas_visiveis:
            c.drawString(x_topo, yy, _fmt_float(topo, " m", nd=2))
            c.drawString(x_fm, yy, (str(fm)[:32] if fm is not None else "—"))
            c.drawString(x_lit, yy, (str(lit)[:18] if lit is not None else "—"))
            yy -= linha_altura_lito

        fig_coluna = st.session_state.get("fig_coluna_lito", None)

        graph_top = box_lito_bottom - 8
        graph_bottom = footer_y + 18

        # só desenha se sobrar espaço suficiente
        if fig_coluna is not None and graph_top > graph_bottom + 60:
            desenhar_fig_plotly_no_pdf(
                c=c,
                fig_plotly=fig_coluna,
                left=left_margin,
                right=right_margin,
                top=graph_top,
                bottom=graph_bottom,
                titulo=None,
                scale=1.5
            )

        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 4 em diante - Análise por fase
    # ==============================
    if pagina_pdf_ativa("analise_por_fase"):
        if st.session_state.option == "Retroanálise":
            fases_df = st.session_state.get("fases_df", None)
            sapatas_df = st.session_state.get("sapatas_df", None)
            df_suav = st.session_state.get("df_suav", None)
            df_mud = st.session_state.get("df_mud", None)

            df_cmp_global = _montar_df_cmp_global(df_mud, df_suav)

            # Profundidade final do poço
            td_final = None
            if isinstance(df_cmp_global, pd.DataFrame) and not df_cmp_global.empty:
                td_final = pd.to_numeric(
                    df_cmp_global["Profundidade (m)"],
                    errors="coerce"
                ).max()

            # Proteções básicas
            if not isinstance(fases_df, pd.DataFrame) or fases_df.empty:
                fases_df = pd.DataFrame(columns=["Ordem", "Fase"])

            if not isinstance(sapatas_df, pd.DataFrame) or sapatas_df.empty:
                sapatas_df = pd.DataFrame(
                    columns=["Ordem", "Fase", "Profundidade da sapata (m)"]
                )

            # Garante ordenação correta
            fases_df = fases_df.copy()
            sapatas_df = sapatas_df.copy()

            if "Ordem" in fases_df.columns:
                fases_df = fases_df.sort_values("Ordem")

            if "Ordem" in sapatas_df.columns:
                sapatas_df = sapatas_df.sort_values("Ordem")

            fases_df = fases_df.reset_index(drop=True)
            sapatas_df = sapatas_df.reset_index(drop=True)

            # Converte profundidades das sapatas
            if "Profundidade da sapata (m)" in sapatas_df.columns:
                sapatas_df["Profundidade da sapata (m)"] = pd.to_numeric(
                    sapatas_df["Profundidade da sapata (m)"],
                    errors="coerce"
                )

                sapatas_df = sapatas_df.dropna(
                    subset=["Profundidade da sapata (m)"]
                )

                sapatas_df = sapatas_df[
                    sapatas_df["Profundidade da sapata (m)"] > 0
                    ].copy()

                sapatas_df = sapatas_df.reset_index(drop=True)

            # Se não tiver TD final, não tem como desenhar fase em poço aberto
            if td_final is not None and pd.notna(td_final):
                td_final = float(td_final)
            else:
                td_final = None

            # ==============================
            # Geração automática por fase
            # ==============================
            for i, row_fase in fases_df.iterrows():
                fase_broca = row_fase.get("Fase", None)

                if fase_broca is None or pd.isna(fase_broca):
                    continue

                # Profundidade inicial:
                # - primeira fase começa em 0
                # - demais fases começam na sapata anterior
                if i == 0:
                    prof_ini = 0.0
                else:
                    if i - 1 < len(sapatas_df):
                        prof_ini = sapatas_df.iloc[i - 1]["Profundidade da sapata (m)"]
                    else:
                        # Não existe sapata anterior para delimitar o início dessa fase
                        continue

                # Verifica se existe sapata/revestimento correspondente à fase atual
                existe_sapata_da_fase = i < len(sapatas_df)

                if existe_sapata_da_fase:
                    fase_revestimento = sapatas_df.iloc[i]["Fase"]
                    prof_fim = sapatas_df.iloc[i]["Profundidade da sapata (m)"]

                    titulo = (
                        f"Análise da fase {_fmt_polegada(fase_broca)}, "
                        f"revestimento {_fmt_polegada(fase_revestimento)}"
                    )

                    incluir_fim = False

                else:
                    # Se existe fase, mas não existe revestimento/sapata,
                    # considera como fase em poço aberto até o TD final
                    if td_final is None:
                        continue

                    fase_revestimento = None
                    prof_fim = td_final

                    titulo = f"Análise da fase {_fmt_polegada(fase_broca)}, poço aberto"

                    incluir_fim = True

                # Proteções contra profundidades inválidas
                try:
                    prof_ini = float(prof_ini)
                    prof_fim = float(prof_fim)
                except Exception:
                    continue

                if pd.isna(prof_ini) or pd.isna(prof_fim):
                    continue

                if prof_fim <= prof_ini:
                    continue

                _desenhar_pagina_fase(
                    c, width, height, logo, footer_y,
                    titulo=titulo,
                    fase_broca=fase_broca,
                    fase_revestimento=fase_revestimento,
                    prof_ini=prof_ini,
                    prof_fim=prof_fim,
                    df_cmp_global=df_cmp_global,
                    draw_header=draw_header,
                    incluir_fim=incluir_fim
                )

    # ==============================
    # Página 5
    # ==============================
    if pagina_pdf_ativa("sobrecarga"):
        y = draw_header(c, width, height, logo)

        # Título da página
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Gradiente de Sobrecarga")
        y -= 10
        c.line(left_margin, y, right_margin, y)

        gard_sel = st.session_state.get("gard", [])
        ex_sel = st.session_state.get("ex", "")
        ds_val = st.session_state.get("ds", None)
        rtkb_val = st.session_state.get("rtkb", None)
        es_val = st.session_state.get("es", None)
        lda_val = st.session_state.get("lda", None)
        onshore = st.session_state.get("onshore", False)

        if isinstance(gard_sel, list):
            gard_sel = ", ".join(gard_sel) if gard_sel else "Nenhum"

        if not ex_sel:
            ex_sel = "Não informado"

        linhas_esq = [
            ("Densidade:", gard_sel),
            ("Extrapolação:", ex_sel),
        ]

        linhas_dir = []

        if ex_sel == "Ativada":
            ds_txt = f"{ds_val:.3f} g/cm³" if ds_val is not None else "Não informado"
            linhas_dir.append(("Densidade média camadas sup.:", ds_txt))

        airgap_txt = f"{rtkb_val:.2f} m" if rtkb_val is not None else "Não informado"
        linhas_dir.append(("Air Gap:", airgap_txt))

        if onshore:
            nf_txt = f"{es_val:.2f} m" if es_val is not None else "Não informado"
            linhas_dir.append(("Elevação DATUM:", nf_txt))
        else:
            lda_txt = f"{lda_val:.2f} m" if lda_val is not None else "Não informado"
            linhas_dir.append(("Lâmina d'água:", lda_txt))

        num_linhas = max(len(linhas_esq), len(linhas_dir))
        linha_altura = 16
        box_height = 40 + num_linhas * linha_altura

        box_width = right_margin - left_margin
        box_x = left_margin

        y -= 25
        box_y = y - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(box_x, box_y + box_height - 22, box_x + box_width, box_y + box_height - 22)

        c.setFillColorRGB(0, 0, 0)

        # título da caixa
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box_y + box_height - 16, "Parâmetros Utilizados no Cálculo")

        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box_y + box_height - 36

        for i in range(num_linhas):

            if i < len(linhas_esq):
                label, valor = linhas_esq[i]

                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label)

                lw = c.stringWidth(label, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                c.drawString(col1_x + lw + 4, texto_y, str(valor))

            if i < len(linhas_dir):
                label, valor = linhas_dir[i]

                c.setFont("Helvetica-Bold", 10)
                c.drawString(col2_x, texto_y, label)

                lw = c.stringWidth(label, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                c.drawString(col2_x + lw + 4, texto_y, str(valor))

            texto_y -= linha_altura

        y = box_y - 20

        fig = st.session_state.fig_gs

        if fig is not None:
            y = desenhar_fig_mpl_no_pdf(
                c=c,
                fig=fig,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None,
                dpi=200
            )

        # Rodapé
        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 6
    # ==============================
    if pagina_pdf_ativa("pressao_poros_lbf"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Gradiente de Pressão de Poros")

        y -= 10
        c.line(left_margin, y, right_margin, y)

        expoente = st.session_state.get("expoente", None)
        anormal = st.session_state.get("anormal", None)
        gn = st.session_state.get("gn", None)

        # suavizações
        spp = st.session_state.get("spp", False)
        s_gr = st.session_state.get("s_gr", False)
        suav_s = st.session_state.get("suav_s", False)

        # boyance / trending / lbf
        boyance_ativo = st.session_state.get("boyance", "Não")
        opcao_boyance = st.session_state.get("o_boyance", None)

        n_boyance = st.session_state.get("n_boyance", 0)
        n_trending = st.session_state.get("n_trending", 0)

        # Se você já separou LBF de Trending, usa n_lbf.
        # Se ainda não separou, usa n_trending como fallback.
        n_lbf = st.session_state.get("n_lbf", n_trending)
        def pegar_valor_state(*chaves, default=None):
            """
            Busca o primeiro valor existente no session_state.
            Serve para aceitar tanto as chaves antigas quanto as novas.
            """
            for chave in chaves:
                if chave in st.session_state:
                    valor = st.session_state.get(chave)
                    if valor is not None:
                        return valor
            return default
        def fmt_num(valor, casas=0):
            """
            Formata números sem quebrar caso venha None ou string.
            """
            if valor is None:
                return "Não informado"

            try:
                valor_float = float(valor)
                return f"{valor_float:.{casas}f}"
            except Exception:
                return str(valor)
        linhas_esq = []
        linhas_esq.append(("Expoente de Eaton:", f"{expoente}" if expoente is not None else "Não informado"))
        linhas_esq.append(("Prof. zona anormal:", f"{anormal:.2f} m" if anormal is not None else "Não informado"))
        linhas_esq.append(("Gradiente normal:", f"{gn:.2f} lb/gal" if gn is not None else "Não informado"))
        linhas_esq.append(("Pressão de poros suavizada:", "Sim" if spp else "Não"))
        linhas_esq.append(("Raio gama suavizado:", "Sim" if s_gr else "Não"))
        linhas_esq.append(("Sônico suavizado:", "Sim" if suav_s else "Não"))

        linhas_dir = []

        # --- Boyance ---
        if boyance_ativo == "Sim":
            linhas_dir.append(("Boyance aplicado:", "Sim"))

            if opcao_boyance:
                # garante que é lista
                if isinstance(opcao_boyance, (list, tuple)) and len(opcao_boyance) > 1:
                    # primeira linha com o label
                    linhas_dir.append(("Opção:", str(opcao_boyance[0])))

                    # demais linhas sem repetir o label
                    for extra in opcao_boyance[1:]:
                        linhas_dir.append(("", str(extra)))
                else:
                    # caso venha 1 opção só ou string
                    if isinstance(opcao_boyance, (list, tuple)):
                        linhas_dir.append(("Opção:", str(opcao_boyance[0]) if opcao_boyance else ""))
                    else:
                        linhas_dir.append(("Opção:", str(opcao_boyance)))

            for i in range(n_boyance):
                prof_ini = pegar_valor_state(
                    f"prof_inicial_{i}",
                    f"prof_ini_boyance_{i}",
                    f"prof_ini_{i}"
                )

                prof_fim = pegar_valor_state(
                    f"prof_final_{i}",
                    f"prof_fim_boyance_{i}",
                    f"prof_fim_{i}"
                )

                fpr = pegar_valor_state(f"fpr_{i}")

                texto = ""

                if prof_ini is not None and prof_fim is not None:
                    texto += f"{fmt_num(prof_ini, 0)}–{fmt_num(prof_fim, 0)} m  "

                if fpr is not None:
                    texto += f"Peso do fluido = {fmt_num(fpr, 2)} lb/gal"

                if texto:
                    linhas_dir.append((f"Boyance {i + 1}:", texto))
        else:
            linhas_dir.append(("Boyance aplicado:", "Não"))

        # --- Trending (parâmetros) ---
        for i in range(n_trending):
            pp1 = pegar_valor_state(
                f"trend_pp1_{i}",
                f"pp1_{i}"
            )

            pp2 = pegar_valor_state(
                f"trend_pp2_{i}",
                f"pp2_{i}"
            )

            s1 = pegar_valor_state(
                f"trend_s1_{i}",
                f"s1_{i}"
            )

            s2 = pegar_valor_state(
                f"trend_s2_{i}",
                f"s2_{i}"
            )

            prof_ini_trend = pegar_valor_state(
                f"trend_prof_ini_{i}",
                f"prof_ini_trending_{i}",
                f"prof_ini_{i}"
            )

            prof_fim_trend = pegar_valor_state(
                f"trend_prof_fim_{i}",
                f"prof_fim_trending_{i}",
                f"prof_fim_{i}"
            )

            if pp1 is not None and pp2 is not None and s1 is not None and s2 is not None:
                texto = (
                    f"{fmt_num(pp1, 0)}–{fmt_num(pp2, 0)} m"
                    f"  |  S1={fmt_num(s1, 2)}"
                    f"  S2={fmt_num(s2, 2)}"
                )

                if prof_ini_trend is not None and prof_fim_trend is not None:
                    try:
                        if float(prof_fim_trend) > float(prof_ini_trend):
                            texto += (
                                f"  |  Intervalo={fmt_num(prof_ini_trend, 0)}"
                                f"–{fmt_num(prof_fim_trend, 0)} m"
                            )
                    except Exception:
                        pass

                linhas_dir.append((f"Trending {i + 1}:", texto))

        # --- LBF (parâmetros) ---
        for i in range(n_lbf):
            lbf = pegar_valor_state(
                f"lbf_valor_{i}",
                f"lbf_{i}"
            )

            inclbf = pegar_valor_state(
                f"lbf_inclinacao_{i}",
                f"inclbf_{i}"
            )

            prof_ini_lbf = pegar_valor_state(
                f"lbf_prof_ini_{i}",
                f"prof_ini_lbf_{i}",
                f"prof_ini_{i}"
            )

            prof_fim_lbf = pegar_valor_state(
                f"lbf_prof_fim_{i}",
                f"prof_fim_lbf_{i}",
                f"prof_fim_{i}"
            )

            if lbf is not None and inclbf is not None:
                texto = (
                    f"Início={fmt_num(lbf, 2)}"
                    f"  Inclinação={fmt_num(inclbf, 2)}"
                )

                if prof_ini_lbf is not None and prof_fim_lbf is not None:
                    try:
                        if float(prof_fim_lbf) > float(prof_ini_lbf):
                            texto += (
                                f"  |  Intervalo={fmt_num(prof_ini_lbf, 0)}"
                                f"–{fmt_num(prof_fim_lbf, 0)} m"
                            )
                    except Exception:
                        pass

                linhas_dir.append((f"LBF {i + 1}:", texto))

        # ---- BOX ----
        num_linhas = max(len(linhas_esq), len(linhas_dir))
        linha_altura = 16
        box_height = 40 + num_linhas * linha_altura

        box_width = right_margin - left_margin
        box_x = left_margin

        y -= 25
        box_y = y - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(box_x, box_y + box_height - 22, box_x + box_width, box_y + box_height - 22)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box_y + box_height - 16, "Dados utilizados no cálculo")

        col1_x = box_x + 12
        col2_x = box_x + box_width * 0.34
        texto_y = box_y + box_height - 36

        for i in range(num_linhas):
            if i < len(linhas_esq):
                label, valor = linhas_esq[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label)

                lw = c.stringWidth(label, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                c.drawString(col1_x + lw + 4, texto_y, str(valor))

            if i < len(linhas_dir):
                label, valor = linhas_dir[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col2_x, texto_y, label)

                lw = c.stringWidth(label, "Helvetica-Bold", 10)

                c.setFont("Helvetica", 10)
                c.drawString(col2_x + lw + 4, texto_y, str(valor))

            texto_y -= linha_altura

        # ---- SUBTÍTULO LBF + LINHA ----
        y = box_y - 18

        c.setFont("Helvetica", 14)
        c.drawString(left_margin, y, "Linha Base de Folhelhos - LBF")

        y -= 8
        c.line(left_margin, y, right_margin, y)

        # espaço antes do gráfico
        y -= 12

        # ---- GRÁFICO (LBF = fig2) ----
        fig_lbf = st.session_state.get("fig2", None)

        if fig_lbf is not None and y > footer_y + 80:
            y = desenhar_fig_mpl_no_pdf(
                c=c,
                fig=fig_lbf,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None
            )

        # Rodapé Página 6
        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 7
    # ==============================
    if pagina_pdf_ativa("pressao_poros_trending"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título principal ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Gradiente de Pressão de Poros")

        y -= 10
        c.line(left_margin, y, right_margin, y)

        y -= 18
        c.setFont("Helvetica", 14)  # sem negrito
        c.drawString(left_margin, y, "Trending")
        y -= 8
        c.line(left_margin, y, right_margin, y)
        y -= 12

        fig_trending = st.session_state.get("fig1", None)
        if fig_trending is not None and y > footer_y + 80:
            y = desenhar_fig_mpl_no_pdf(
                c=c,
                fig=fig_trending,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None
            )

        y -= 10

        min_space_for_next_plot = 220  # altura mínima segura
        if y < footer_y + min_space_for_next_plot:
            draw_footer(c, width, footer_y)
            c.showPage()

            y = draw_header(c, width, height, logo)
            left_margin = 40
            right_margin = width - 40

            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, "Gradiente de Pressão de Poros")
            y -= 10
            c.line(left_margin, y, right_margin, y)
            y -= 18

        c.setFont("Helvetica", 14)  # sem negrito
        c.drawString(left_margin, y, "Gradiente de Pressão de Poros")
        y -= 8
        c.line(left_margin, y, right_margin, y)
        y -= 12

        fig_pp = st.session_state.get("fig_pp", None)
        if fig_pp is not None and y > footer_y + 80:
            y = desenhar_fig_mpl_no_pdf(
                c=c,
                fig=fig_pp,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None
            )

        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 8
    # ==============================
    if pagina_pdf_ativa("estabilidade_trajetoria"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Estabilidade de Poço – Tensões em volta do poço")

        y -= 10
        c.line(left_margin, y, right_margin, y)

        phi = st.session_state.get("phi", None)  # (°)
        lft = st.session_state.get("lft", None)  # (psi)
        m_input = st.session_state.get("m", None)  # profundidade digitada
        ucs = st.session_state.get("ucs", None)  # método UCS

        sapatas_df = st.session_state.get("sapatas_df", None)
        zona2 = st.session_state.get("zona2", None)
        prisoes_df = st.session_state.get("prisoes_coluna_df", None)
        dados_lito = st.session_state.get("dados_lito", None)

        profundidade_proxima = None
        try:
            y_series = st.session_state.get("y", None)
            if y_series is not None and m_input is not None:
                profundidade_proxima = y_series.loc[(y_series - m_input).abs().idxmin()]
        except Exception:
            profundidade_proxima = None

        linhas_esq = []
        linhas_dir = []

        # --- ESQUERDA: parâmetros principais ---
        linhas_esq.append(("Ângulo de fricção:", f"{phi}°" if phi is not None else "Não informado"))
        linhas_esq.append(("Limite falha por tração:", f"{lft} psi" if lft is not None else "Não informado"))
        linhas_esq.append((
            "Profundidade analisada:",
            f"{profundidade_proxima:.2f} m" if isinstance(profundidade_proxima,
                                                          (int, float)) else "Não informado"
        ))
        linhas_esq.append(("Correlação para cálculo do UCS:", str(ucs) if ucs else "Não informado"))

        # --- ESQUERDA: Pontos de prisão de coluna ---
        if prisoes_df is not None and hasattr(prisoes_df, "empty") and not prisoes_df.empty:
            linhas_esq.append(("Pontos de prisão de coluna (TVD):", ""))

            col_prof_pr = "Profundidade da prisão (m)"
            try:
                pr_ord = prisoes_df.sort_values(by=col_prof_pr, ascending=True)
            except Exception:
                pr_ord = prisoes_df

            for _, row in pr_ord.iterrows():
                prof_p = row.get(col_prof_pr, "—")
                linhas_esq.append(("", f"{prof_p} m"))
        else:
            linhas_esq.append(("Pontos de prisão de coluna (TVD):", "Não informado"))

        # --- ESQUERDA: Litologias consideradas + lista topo/base/lito/So ---
        considera_lito = (
                dados_lito is not None
                and hasattr(dados_lito, "empty")
                and not dados_lito.empty
        )

        linhas_esq.append(("Litologias consideradas:", "Sim" if considera_lito else "Não"))

        if considera_lito:
            # sem linha em branco para reduzir o "buraco"
            linhas_esq.append(("", "Topo–Base | Litologia | So (psi)"))

            try:
                dados_ord = dados_lito.sort_values(by="Topo (m)", ascending=True)
            except Exception:
                dados_ord = dados_lito

            for _, row in dados_ord.iterrows():
                topo = row.get("Topo (m)", "—")
                base = row.get("Base (m)", "—")
                lit = row.get("Litologia", "—")
                so = row.get("So (psi)", "—")
                linhas_esq.append(("", f"{topo}–{base} m | {lit} | {so} psi"))

        # --- DIREITA: Sapatas ---
        if sapatas_df is not None and hasattr(sapatas_df, "empty") and not sapatas_df.empty:
            linhas_dir.append(("Profundidade das sapatas (TVD):", ""))

            col_fase = "Fase"
            col_prof = "Profundidade da sapata (m)"

            try:
                sapatas_ord = sapatas_df.sort_values(by=col_prof, ascending=True)
            except Exception:
                sapatas_ord = sapatas_df

            for _, row in sapatas_ord.iterrows():
                fase = row.get(col_fase, "—")
                prof = row.get(col_prof, "—")
                linhas_dir.append(("", f"Sapata {fase}: {prof} m"))
        else:
            linhas_dir.append(("Profundidade das sapatas (TVD):", "Não informado"))

        # --- DIREITA: Zonas de perda ---
        if zona2 and isinstance(zona2, list) and len(zona2) > 0:
            linhas_dir.append(("Zonas de perda:", ""))

            try:
                zona2_ord = sorted(zona2, key=lambda x: float(x[0]))
            except Exception:
                zona2_ord = zona2

            for z in zona2_ord:
                try:
                    prof_z = z[0]
                    ppg_z = z[1]
                    linhas_dir.append(("", f"{prof_z} m | {ppg_z} lb/gal"))
                except Exception:
                    linhas_dir.append(("", str(z)))
        else:
            linhas_dir.append(("Zonas de perda:", "Não informado"))

        num_linhas = max(len(linhas_esq), len(linhas_dir))
        linha_altura = 16
        box_height = 40 + num_linhas * linha_altura

        box_width = right_margin - left_margin
        box_x = left_margin

        y -= 25
        box_y = y - box_height

        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        c.line(box_x, box_y + box_height - 22, box_x + box_width, box_y + box_height - 22)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box_y + box_height - 16, "Dados utilizados no cálculo")

        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box_y + box_height - 36

        for i in range(num_linhas):
            # --- coluna esquerda ---
            if i < len(linhas_esq):
                label, valor = linhas_esq[i]
                if str(label).strip():
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col1_x, texto_y, str(label))
                    lw = c.stringWidth(str(label), "Helvetica-Bold", 10)
                    c.setFont("Helvetica", 10)
                    c.drawString(col1_x + lw + 4, texto_y, str(valor))
                else:
                    c.setFont("Helvetica", 10)
                    c.drawString(col1_x + 12, texto_y, str(valor))

            # --- coluna direita ---
            if i < len(linhas_dir):
                label, valor = linhas_dir[i]
                if str(label).strip():
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col2_x, texto_y, str(label))
                    lw = c.stringWidth(str(label), "Helvetica-Bold", 10)
                    c.setFont("Helvetica", 10)
                    c.drawString(col2_x + lw + 4, texto_y, str(valor))
                else:
                    c.setFont("Helvetica", 10)
                    c.drawString(col2_x + 12, texto_y, str(valor))

            texto_y -= linha_altura

        y = box_y - 18

        c.setFont("Helvetica", 14)  # sem negrito
        c.drawString(left_margin, y, "Trajetória do poço")
        y -= 8
        c.line(left_margin, y, right_margin, y)
        y -= 12

        fig_traj = st.session_state.get("fig_traj", None)
        if fig_traj is not None and y > footer_y + 60:
            try:
                y = desenhar_fig_plotly_no_pdf(
                    c=c,
                    fig_plotly=fig_traj,
                    left=left_margin,
                    right=right_margin,
                    top=y,
                    bottom=footer_y,
                    titulo=None,
                    scale=1.5
                )
            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(left_margin, y - 10, f"Não foi possível exportar a trajetória para imagem: {e}")
        else:
            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y - 10, "Trajetória do poço: Não informado")

        # Rodapé
        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 9
    # ==============================
    if pagina_pdf_ativa("janela_operacional"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Janela operacional")

        y -= 10
        c.line(left_margin, y, right_margin, y)

        # espaço antes do gráfico
        y -= 20

        # --- Gráfico (Janela Operacional) ---
        fig_jo = st.session_state.get("fig_jo", None)
        if fig_jo is not None and y > footer_y + 80:
            y = desenhar_fig_mpl_no_pdf(
                c=c,
                fig=fig_jo,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None,
                dpi=200
            )
        else:
            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y - 10, "Gráfico da janela operacional: Não informado")

        # Rodapé Página 7
        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 10
    # ==============================
    if pagina_pdf_ativa("mohr_coulomb"):
        y = draw_header(c, width, height, logo)

        left_margin = 40
        right_margin = width - 40

        # --- Título da seção ---
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y, "Critério de falha de Mohr Coulomb")

        y -= 8
        c.line(left_margin, y, right_margin, y)

        def _fmt(v, suf=""):
            return f"{float(v):.2f}{suf}" if v is not None and pd.notna(v) else "Não informado"

        def _aprox(a, b, tol=1e-3):
            if a is None or b is None or (pd.isna(a) or pd.isna(b)):
                return False
            return abs(float(a) - float(b)) <= tol

        # >>>>>>>>>>>>>> TUDO AGORA USA df_suav <<<<<<<<<<<<<<
        df_suav = st.session_state.get("df_suav", None)
        df_tvp = st.session_state.get("df_tvp", None)

        ppg_val = st.session_state.get("ppg", None)
        ppg_txt = f"{ppg_val:.2f} lb/gal" if ppg_val is not None else "Não informado"

        prof_analisada = st.session_state.get("m", None)

        if isinstance(prof_analisada, pd.Series):
            prof_analisada = float(prof_analisada.iloc[0]) if not prof_analisada.empty else None

        prof_analisada_txt = (
            f"{float(prof_analisada):.2f} m"
            if prof_analisada is not None and pd.notna(prof_analisada)
            else "Não informado"
        )

        # coluna de profundidade usada para localizar a linha analisada
        coluna_ref = "Profundidade (m)"
        if st.session_state.get("t_prof", "TVD") != "TVD":
            coluna_ref = "MD"  # se df_suav tiver MD

        # linha da profundidade analisada (para janela/status/falha)
        row_s = None
        if (
                isinstance(df_suav, pd.DataFrame)
                and not df_suav.empty
                and prof_analisada is not None
                and coluna_ref in df_suav.columns
        ):
            idx = (df_suav[coluna_ref].astype(float) - float(prof_analisada)).abs().idxmin()
            row_s = df_suav.loc[idx]

        prof_crit_txt = "Não informado"
        pp_txt = "Não informado"
        tr_inf_txt = "Não informado"
        comp_inf_a_txt = "Não informado"
        comp_inf_b_txt = "Não informado"

        if isinstance(df_suav, pd.DataFrame) and not df_suav.empty:
            col_max = "Max Inferior"
            col_prof = "Profundidade (m)" if "Profundidade (m)" in df_suav.columns else coluna_ref

            cols_needed_inf = [
                col_max,
                col_prof,
                "Gradiente de Pressão de Poros (lb/gal)",
                "Tração Inferior",
                "Comp Inferior σθA",
                "Comp Inferior σθB",
            ]

            if all(cn in df_suav.columns for cn in cols_needed_inf):
                s_max = df_suav[col_max]
                if s_max.notna().any():
                    idx_crit = s_max.idxmax()
                    linha_crit = df_suav.loc[idx_crit]

                    prof_crit_txt = _fmt(linha_crit[col_prof], " m")
                    pp_txt = _fmt(linha_crit["Gradiente de Pressão de Poros (lb/gal)"], " lb/gal")
                    tr_inf_txt = _fmt(linha_crit["Tração Inferior"], " lb/gal")
                    comp_inf_a_txt = _fmt(linha_crit["Comp Inferior σθA"], " lb/gal")
                    comp_inf_b_txt = _fmt(linha_crit["Comp Inferior σθB"], " lb/gal")

        linhas_esq_1 = [
            ("Profundidade crítica:", prof_crit_txt),
            ("Peso do fluido atual:", ppg_txt),
            ("Pressão de poros:", pp_txt),
        ]
        linhas_dir_1 = [
            ("Limite de falha por tração inferior:", tr_inf_txt),
            ("Limite de falha compressão inferior (σθA):", comp_inf_a_txt),
            ("Limite de falha compressão inferior (σθB):", comp_inf_b_txt),
        ]

        num_linhas_1 = max(len(linhas_esq_1), len(linhas_dir_1))
        linha_altura_1 = 15
        box_height_1 = 30 + num_linhas_1 * linha_altura_1

        box_width = right_margin - left_margin
        box_x = left_margin

        y -= 14
        box1_y = y - box_height_1

        # fundo
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box1_y, box_width, box_height_1, fill=1, stroke=0)
        # borda
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box1_y, box_width, box_height_1, fill=0, stroke=1)
        # linha do título interno
        c.line(box_x, box1_y + box_height_1 - 18, box_x + box_width, box1_y + box_height_1 - 18)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box1_y + box_height_1 - 14, "Resumo do limite inferior da janela operacional")

        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box1_y + box_height_1 - 32

        for i in range(num_linhas_1):
            if i < len(linhas_esq_1):
                label, valor = linhas_esq_1[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label)
                lw = c.stringWidth(label, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                c.drawString(col1_x + lw + 4, texto_y, str(valor))

            if i < len(linhas_dir_1):
                label, valor = linhas_dir_1[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col2_x, texto_y, label)
                lw = c.stringWidth(label, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                c.drawString(col2_x + lw + 4, texto_y, str(valor))

            texto_y -= linha_altura_1

        # cursor abaixo da tabela 1
        y = box1_y - 18

        prof_crit2_txt = "Não informado"
        gs_txt = "Não informado"
        ts_a_txt = "Não informado"
        ts_b_txt = "Não informado"
        cs_a_txt = "Não informado"
        cs_b_txt = "Não informado"

        if isinstance(df_suav, pd.DataFrame) and not df_suav.empty:
            col_min = "Min Superior"
            col_prof = "Profundidade (m)" if "Profundidade (m)" in df_suav.columns else coluna_ref

            required_cols = [
                col_min,
                col_prof,
                "Gradiente de Sobrecarga (lb/gal)",
                "Tração Superior (σθA)",
                "Tração Superior (σθB)",
                "Comp Superior σθA",
                "Comp Superior σθB",
            ]

            if all(cn in df_suav.columns for cn in required_cols):
                serie_min = df_suav[col_min]
                if serie_min.notna().any():
                    idx_crit2 = serie_min.idxmin()
                    linha = df_suav.loc[idx_crit2]

                    prof_crit2_txt = _fmt(linha[col_prof], " m")
                    gs_txt = _fmt(linha["Gradiente de Sobrecarga (lb/gal)"], " lb/gal")
                    ts_a_txt = _fmt(linha["Tração Superior (σθA)"], " lb/gal")
                    ts_b_txt = _fmt(linha["Tração Superior (σθB)"], " lb/gal")
                    cs_a_txt = _fmt(linha["Comp Superior σθA"], " lb/gal")
                    cs_b_txt = _fmt(linha["Comp Superior σθB"], " lb/gal")

        linhas_esq_2 = [
            ("Profundidade crítica:", prof_crit2_txt),
            ("Peso do fluido atual:", ppg_txt),
            ("Gradiente de sobrecarga:", gs_txt),
        ]
        linhas_dir_2 = [
            ("Falha por tração superior (σθA):", ts_a_txt),
            ("Falha por tração superior (σθB):", ts_b_txt),
            ("Falha por compressão superior (σθA):", cs_a_txt),
            ("Falha por compressão superior (σθB):", cs_b_txt),
        ]

        num_linhas_2 = max(len(linhas_esq_2), len(linhas_dir_2))
        linha_altura_2 = 15
        box_height_2 = 30 + num_linhas_2 * linha_altura_2

        box2_y = y - box_height_2

        # fundo
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box2_y, box_width, box_height_2, fill=1, stroke=0)
        # borda
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box2_y, box_width, box_height_2, fill=0, stroke=1)
        # linha do título interno
        c.line(box_x, box2_y + box_height_2 - 18, box_x + box_width, box2_y + box_height_2 - 18)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box2_y + box_height_2 - 14, "Resumo do limite superior da janela operacional")

        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box2_y + box_height_2 - 32

        for i in range(num_linhas_2):
            if i < len(linhas_esq_2):
                label, valor = linhas_esq_2[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label)
                lw = c.stringWidth(label, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                c.drawString(col1_x + lw + 4, texto_y, str(valor))

            if i < len(linhas_dir_2):
                label, valor = linhas_dir_2[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col2_x, texto_y, label)
                lw = c.stringWidth(label, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                c.drawString(col2_x + lw + 4, texto_y, str(valor))

            texto_y -= linha_altura_2

        # cursor abaixo da tabela 2
        y = box2_y - 14

        max_inf = min_sup = None
        janela_txt = "Não informado"
        falha_txt = ""
        status_txt = "Poço instável"
        status_color = (1, 0, 0)  # vermelho

        fs_val = st.session_state.get("fs", 0)

        if isinstance(df_suav, pd.DataFrame) and not df_suav.empty:
            if row_s is not None:
                idx_linha = row_s.name

                col_max_inf = "Max Inferior"
                col_min_sup = "Min Superior"

                if col_max_inf in df_suav.columns and col_min_sup in df_suav.columns:
                    fs = float(fs_val)

                    # Limite inferior
                    # Mantém a mesma lógica da tela:
                    # se suav_max_inf estiver ativo, usa df_suav;
                    # caso contrário, usa df_tvp, se existir.
                    if (
                            not st.session_state.get("suav_max_inf", False)
                            and isinstance(df_tvp, pd.DataFrame)
                            and col_max_inf in df_tvp.columns
                    ):
                        x_max_inf = pd.Series(df_tvp[col_max_inf], index=df_tvp.index, dtype=float)
                    else:
                        x_max_inf = pd.Series(df_suav[col_max_inf], index=df_suav.index, dtype=float)

                    # Limite superior
                    if (
                            not st.session_state.get("suav_min_sup", False)
                            and isinstance(df_tvp, pd.DataFrame)
                            and col_min_sup in df_tvp.columns
                    ):
                        x_min_sup = pd.Series(df_tvp[col_min_sup], index=df_tvp.index, dtype=float)
                    else:
                        x_min_sup = pd.Series(df_suav[col_min_sup], index=df_suav.index, dtype=float)

                    # Aplica FS no limite inferior com máximo acumulado,
                    # igual à lógica da tela
                    x_fs_base_inf = x_max_inf + fs
                    x_fs_inf = pd.Series(np.nan, index=x_max_inf.index, dtype=float)

                    mask_fs = x_fs_base_inf.notna()

                    x_fs_inf.loc[mask_fs] = np.maximum.accumulate(
                        x_fs_base_inf.loc[mask_fs].to_numpy()
                    )

                    # Garante que o índice existe nas séries usadas
                    if idx_linha in x_fs_inf.index and idx_linha in x_min_sup.index:
                        lim_inf = x_fs_inf.loc[idx_linha]
                        lim_sup = x_min_sup.loc[idx_linha] - fs

                        if pd.notna(lim_inf) and pd.notna(lim_sup):
                            janela_txt = f"{lim_inf:.2f} < ρ < {lim_sup:.2f} lb/gal"

                            if ppg_val is not None and pd.notna(ppg_val):
                                ppg_float = float(ppg_val)

                                if lim_inf < ppg_float < lim_sup:
                                    status_txt = "Poço estável"
                                    status_color = (0, 0.6, 0)  # verde

                                else:
                                    status_txt = "Poço instável"
                                    status_color = (0.8, 0, 0)  # vermelho

                                    if ppg_float <= lim_inf:
                                        falha_txt = _classificar_falha_no_limite(
                                            row_s,
                                            ppg_float,
                                            "inferior"
                                        )

                                    elif ppg_float >= lim_sup:
                                        falha_txt = _classificar_falha_no_limite(
                                            row_s,
                                            ppg_float,
                                            "superior"
                                        )

                        else:
                            janela_txt = "Não avaliada nessa profundidade"
                            status_txt = "Não avaliado"
                            status_color = (0.4, 0.4, 0.4)
                    else:
                        janela_txt = "Não avaliada nessa profundidade"
                        status_txt = "Não avaliado"
                        status_color = (0.4, 0.4, 0.4)

        linhas_esq = [
            ("Profundidade analisada:", prof_analisada_txt),
            ("Janela operacional:", janela_txt),
        ]
        linhas_dir = [
            ("Estado do poço:", status_txt),
        ]
        if falha_txt:
            linhas_dir.append(("", falha_txt))

        num_linhas = max(len(linhas_esq), len(linhas_dir))
        linha_altura = 15
        box_height = 30 + num_linhas * linha_altura

        box_width = right_margin - left_margin
        box_x = left_margin

        y -= 6
        box_y = y - box_height

        # fundo
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

        # borda
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

        # linha título interno
        c.line(box_x, box_y + box_height - 18, box_x + box_width, box_y + box_height - 18)

        # título
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(box_x + 10, box_y + box_height - 14, "Avaliação na profundidade analisada")

        # conteúdo
        col1_x = box_x + 12
        col2_x = box_x + box_width / 2
        texto_y = box_y + box_height - 32

        for i in range(num_linhas):

            if i < len(linhas_esq):
                label, valor = linhas_esq[i]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(col1_x, texto_y, label)
                lw = c.stringWidth(label, "Helvetica-Bold", 10)
                c.setFont("Helvetica", 10)
                c.drawString(col1_x + lw + 4, texto_y, str(valor))

            if i < len(linhas_dir):
                label, valor = linhas_dir[i]

                if label:
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col2_x, texto_y, label)
                    lw = c.stringWidth(label, "Helvetica-Bold", 10)

                    if label == "Estado do poço:":
                        c.setFillColorRGB(*status_color)
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(col2_x + lw + 4, texto_y, str(valor))
                        c.setFillColorRGB(0, 0, 0)
                    else:
                        c.setFont("Helvetica", 10)
                        c.drawString(col2_x + lw + 4, texto_y, str(valor))

                else:
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col2_x, texto_y, str(valor))

            texto_y -= linha_altura

        # atualiza cursor para o gráfico
        y = box_y - 10

        fig_mohr = st.session_state.get("fig_mohr", None)

        if fig_mohr is not None and y > footer_y + 80:
            y = desenhar_fig_plotly_no_pdf(
                c=c,
                fig_plotly=fig_mohr,
                left=left_margin,
                right=right_margin,
                top=y,
                bottom=footer_y + 20,
                titulo=None,
                scale=1.2
            )

        draw_footer(c, width, footer_y)
        c.showPage()

    # ==============================
    # Página 11
    # ==============================
    if pagina_pdf_ativa("fratura_tensoes_minimas"):
        left_margin = 40
        right_margin = width - 40

        # --- coleta do session_state ---
        fig_fratura = st.session_state.get("fig_fratura", None)
        df_f = st.session_state.get("df_f", None)

        tt = st.session_state.get("tt", [])  # ["LOT"/"FIT"...]
        pp = st.session_state.get("pp", [])  # profundidades
        lt = st.session_state.get("lt", [])  # pesos equivalentes (lb/gal)

        # Condição: só gera a página se o gradiente de fratura foi plotado no gráfico
        tem_gradiente_fratura_plotado = (
                st.session_state.get("tem_gradiente_fratura_plotado", False)
                and fig_fratura is not None
                and isinstance(df_f, pd.DataFrame)
                and not df_f.empty
                and "Gradiente de Fratura (lb/gal)" in df_f.columns
                and pd.to_numeric(df_f["Gradiente de Fratura (lb/gal)"], errors="coerce").notna().any()
        )

        if tem_gradiente_fratura_plotado:
            y = draw_header(c, width, height, logo)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, "Gradiente de Fratura - Método das tensões mínimas")

            y -= 8
            c.line(left_margin, y, right_margin, y)

            origem_lots = "Inseridos pelo usuário" if st.session_state.get("lot", False) else "Base de dados"
            aux_flag = "Sim" if st.session_state.get("auxiliar", False) else "Não"

            n_lot = sum(1 for x in tt if str(x).upper() == "LOT")
            n_fit = sum(1 for x in tt if str(x).upper() == "FIT")

            linhas_pontos = []

            if tt and pp and lt and len(tt) == len(pp) == len(lt):
                linhas_pontos.append(("Origem dos LOT/FIT:", origem_lots))
                linhas_pontos.append(("Ponto auxiliar K:", aux_flag))

                for i, (tipo, prof, peso) in enumerate(zip(tt, pp, lt), start=1):
                    try:
                        prof_txt = f"{float(prof):.0f} m" if prof is not None and pd.notna(prof) else "—"
                        peso_txt = f"{float(peso):.2f} lb/gal" if peso is not None and pd.notna(peso) else "—"
                    except Exception:
                        prof_txt, peso_txt = "—", "—"

                    linhas_pontos.append((f"{str(tipo).upper()} {i}:", f"{prof_txt} | {peso_txt}"))
            else:
                linhas_pontos.append(("LOT/FIT:", "Não informado"))

            gf_min_txt = "Não informado"
            gf_max_txt = "Não informado"

            if isinstance(df_f, pd.DataFrame) and not df_f.empty:
                if "Gradiente de Fratura (lb/gal)" in df_f.columns:
                    gf_valida = pd.to_numeric(
                        df_f["Gradiente de Fratura (lb/gal)"],
                        errors="coerce"
                    ).dropna()

                    if not gf_valida.empty:
                        gf_min_txt = f"{float(gf_valida.min()):.2f} lb/gal"
                        gf_max_txt = f"{float(gf_valida.max()):.2f} lb/gal"

            linhas_esq = [
                ("Qtd. LOT:", str(n_lot)),
                ("Qtd. FIT:", str(n_fit)),
                ("G. Fratura (mín):", gf_min_txt),
                ("G. Fratura (máx):", gf_max_txt),
            ]

            linhas_dir = linhas_pontos

            num_linhas = max(len(linhas_esq), len(linhas_dir))
            linha_altura = 15
            box_height = 30 + num_linhas * linha_altura

            box_width = right_margin - left_margin
            box_x = left_margin

            y -= 14
            box_y = y - box_height

            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

            c.line(box_x, box_y + box_height - 18, box_x + box_width, box_y + box_height - 18)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(box_x + 10, box_y + box_height - 14, "Resumo dos dados utilizados")

            col1_x = box_x + 12
            col2_x = box_x + box_width / 2
            texto_y = box_y + box_height - 32

            for i in range(num_linhas):
                if i < len(linhas_esq):
                    label, valor = linhas_esq[i]
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col1_x, texto_y, label)
                    lw = c.stringWidth(label, "Helvetica-Bold", 10)
                    c.setFont("Helvetica", 10)
                    c.drawString(col1_x + lw + 4, texto_y, str(valor))

                if i < len(linhas_dir):
                    label, valor = linhas_dir[i]
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(col2_x, texto_y, label)
                    lw = c.stringWidth(label, "Helvetica-Bold", 10)
                    c.setFont("Helvetica", 10)
                    c.drawString(col2_x + lw + 4, texto_y, str(valor))

                texto_y -= linha_altura

            y = box_y - 12

            if fig_fratura is not None and y > footer_y + 80:
                y = desenhar_fig_mpl_no_pdf(
                    c=c,
                    fig=fig_fratura,
                    left=left_margin,
                    right=right_margin,
                    top=y,
                    bottom=footer_y + 20,
                    titulo=None,
                    dpi=180
                )

            draw_footer(c, width, footer_y)
            c.showPage()

        else:
            pass

    # ==============================
    # Página - Assentamento de Sapatas | Previsão
    # ==============================
    if (pagina_pdf_ativa("sapatas_previsao") and st.session_state.get("option") == "Previsão de Geopressões"):
        left_margin = 40
        right_margin = width - 40
        fig_asp = st.session_state.get("fig_asp", None)
        tem_dados_sapatas = fig_asp is not None
        if tem_dados_sapatas:
            titulo_pagina = "Assentamento de Sapatas - Previsão de Geopressões"

            y = draw_header(c, width, height, logo)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, titulo_pagina)

            y -= 8
            c.line(left_margin, y, right_margin, y)
            y -= 18

            linhas_sapatas = [
                (
                    ("Grad. de Frat. utilizado:",
                     _fmt_pdf_val(st.session_state.get("metodo_gradiente_fratura"))),
                    ("Kick Tolerance:", _fmt_pdf_val(st.session_state.get("metodo_kt")))
                ),
                (
                    ("Sapata rev. condutor:", _fmt_pdf_val(st.session_state.get("prc"), " m")),
                    ("OD rev. condutor:", _fmt_pdf_val(st.session_state.get("odrc")))
                ),
                (
                    ("Sapata rev superfície:", _fmt_pdf_val(st.session_state.get("prs"), " m")),
                    ("OD rev. superfície:", _fmt_pdf_val(st.session_state.get("odrs")))
                ),
                (
                    ("M.S. Gpp:",
                     _fmt_pdf_val(st.session_state.get("ms"), " lb/gal")),
                    ("M.S. Gf:",
                     _fmt_pdf_val(st.session_state.get("msf"), " lb/gal"))
                ),
                (
                    ("Volume do kick:", _fmt_pdf_val(st.session_state.get("vk"), " bbl")),
                    ("Densidade de kick:", _fmt_pdf_val(st.session_state.get("dk"), " lb/gal"))
                ),
                (
                    ("M.S. Kick tolerance:", _fmt_pdf_val(st.session_state.get("mskt"), " lb/gal")),
                    ("Comp. máx. de P.A:", _fmt_pdf_val(st.session_state.get("hk"), " m"))
                ),
            ]

            if st.session_state.get("metodo_kt") == "Baixo para Cima":
                linhas_sapatas.append(
                    (
                        ("Comp. mín.:", _fmt_pdf_val(st.session_state.get("cmf"), " m")),
                        ("Prof. da sapata final:", _fmt_pdf_val(st.session_state.get("suf"), " m"))
                    )
                )

            y = desenhar_linhas_duplas_pdf(
                y_top=y,
                titulo_secao="Dados para definição das sapatas",
                linhas=linhas_sapatas,
                titulo_pagina=titulo_pagina,
                left_margin=left_margin,
                right_margin=right_margin
            )

            if fig_asp is not None:
                if y < footer_y + 260:
                    y = _nova_pagina_pdf(
                        c, width, height, logo, footer_y, draw_header, titulo_pagina
                    )

                try:
                    y = desenhar_fig_mpl_no_pdf(
                        c=c,
                        fig=fig_asp,
                        left=left_margin,
                        right=right_margin,
                        top=y,
                        bottom=footer_y + 20,
                        titulo=None,
                        dpi=180
                    )
                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(left_margin, y - 15, f"Não foi possível inserir o gráfico: {e}")

            draw_footer(c, width, footer_y)
            c.showPage()

    # ==============================
    # Página - Esquemático do Poço | Previsão
    # ==============================
    if (pagina_pdf_ativa("esquematico_poco_previsao")and st.session_state.get("option") == "Previsão de Geopressões"):
        left_margin = 40
        right_margin = width - 40

        fig_esquematico = st.session_state.get("fig_esquematico_asp", None)
        df_esquematico = st.session_state.get("df_esquematico_asp", None)

        # Se a figura ainda não estiver salva no session_state,
        # tenta gerar automaticamente com os dados atuais do SYGA.
        if fig_esquematico is None:
            try:
                df_esquematico_auto = _asp_montar_df_esquematico_kt()

                if (
                    isinstance(df_esquematico_auto, pd.DataFrame)
                    and not df_esquematico_auto.empty
                ):
                    fig_esquematico, df_esquematico = _asp_plotar_esquematico(
                        df_esquematico_auto
                    )

                    st.session_state.fig_esquematico_asp = fig_esquematico
                    st.session_state.df_esquematico_asp = df_esquematico

            except Exception:
                fig_esquematico = None
                df_esquematico = None

        tem_esquematico = fig_esquematico is not None

        if tem_esquematico:
            titulo_pagina = "Esquemático do Poço"

            y = draw_header(c, width, height, logo)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, titulo_pagina)

            y -= 8
            c.line(left_margin, y, right_margin, y)
            # y -= 18
            #
            # c.setFont("Helvetica", 10)
            # c.drawString(
            #     left_margin,
            #     y,
            #     "Esquemático gerado automaticamente a partir dos dados de revestimentos, sapatas e condição final do poço."
            # )
            #
            # y -= 18

            # ==============================
            # Resumo dos dados usados
            # ==============================
            if isinstance(df_esquematico, pd.DataFrame) and not df_esquematico.empty:
                try:
                    df_pdf = df_esquematico.copy()

                    for col in ["diam_furo", "diam_rev", "profundidade"]:
                        if col in df_pdf.columns:
                            df_pdf[col] = pd.to_numeric(df_pdf[col], errors="coerce")

                    qtd_fases = len(df_pdf)
                    qtd_revestidas = int(
                        (df_pdf["tipo_trecho"].astype(str).str.lower().str.strip() != "poço aberto").sum()
                    )
                    tem_poco_aberto = bool(
                        (df_pdf["tipo_trecho"].astype(str).str.lower().str.strip() == "poço aberto").any()
                    )

                    prof_final_esq = pd.to_numeric(
                        df_pdf["profundidade"],
                        errors="coerce"
                    ).dropna().max()

                    linhas_esquematico = [
                        (
                            ("Nº de fases:", _fmt_pdf_val(qtd_fases, "", casas=0)),
                            ("Fases revestidas:", _fmt_pdf_val(qtd_revestidas, "", casas=0))
                        ),
                        (
                            ("Poço aberto:", "Sim" if tem_poco_aberto else "Não"),
                            ("Prof. final:", _fmt_pdf_val(prof_final_esq, " m"))
                        ),
                    ]

                    y = desenhar_linhas_duplas_pdf(
                        y_top=y,
                        titulo_secao="Resumo do esquemático",
                        linhas=linhas_esquematico,
                        titulo_pagina=titulo_pagina,
                        left_margin=left_margin,
                        right_margin=right_margin
                    )

                except Exception:
                    pass

            # ==============================
            # Figura do esquemático
            # ==============================
            if y < footer_y + 420:
                y = _nova_pagina_pdf(
                    c,
                    width,
                    height,
                    logo,
                    footer_y,
                    draw_header,
                    titulo_pagina
                )

            try:
                y = desenhar_fig_mpl_no_pdf(
                    c=c,
                    fig=fig_esquematico,
                    left=left_margin,
                    right=right_margin,
                    top=y,
                    bottom=footer_y + 20,
                    titulo=None,
                    dpi=180
                )

            except Exception as e:
                c.setFont("Helvetica", 10)
                c.drawString(
                    left_margin,
                    y - 15,
                    f"Não foi possível inserir o esquemático do poço: {e}"
                )

            draw_footer(c, width, footer_y)
            c.showPage()

    # ==============================
    # Página - Fluido de Perfuração | Previsão
    # ==============================
    if (pagina_pdf_ativa("fluido_previsao") and st.session_state.get("option") == "Previsão de Geopressões"):
        left_margin = 40
        right_margin = width - 40

        fig_fp = st.session_state.get("fig_fp", None)
        df_intervalos_fluido = st.session_state.get("df_intervalos_fluido", None)

        tem_dados_fluido = (
                fig_fp is not None
                or (
                        isinstance(df_intervalos_fluido, pd.DataFrame)
                        and not df_intervalos_fluido.empty
                )
        )

        if tem_dados_fluido:
            titulo_pagina = "Fluido de Perfuração - Previsão de Geopressões"

            y = draw_header(c, width, height, logo)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, titulo_pagina)

            y -= 8
            c.line(left_margin, y, right_margin, y)
            y -= 18

            y = desenhar_blocos_fluido_pdf(
                y_top=y,
                df_intervalos=df_intervalos_fluido,
                titulo_pagina=titulo_pagina,
                left_margin=left_margin,
                right_margin=right_margin
            )

            if fig_fp is not None:
                if y < footer_y + 260:
                    y = _abrir_pagina_pdf_com_titulo(titulo_pagina)

                try:
                    y = desenhar_fig_mpl_no_pdf(
                        c=c,
                        fig=fig_fp,
                        left=left_margin,
                        right=right_margin,
                        top=y,
                        bottom=footer_y + 20,
                        titulo=None,
                        dpi=180
                    )
                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(
                        left_margin,
                        y - 15,
                        f"Não foi possível inserir o gráfico de fluido: {e}"
                    )

            draw_footer(c, width, footer_y)
            c.showPage()

    # ==============================
    # Página 12
    # ==============================
    if pagina_pdf_ativa("anotacoes"):
        # texto das anotações
        anotacoes_txt = st.session_state.get("anotacoes", "")
        anotacoes_txt = anotacoes_txt.strip()

        if anotacoes_txt:

            y = draw_header(c, width, height, logo)

            left_margin = 40
            right_margin = width - 40

            # --- Título da seção ---
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, "Anotações")

            y -= 8
            c.line(left_margin, y, right_margin, y)

            y -= 18

            # Caixa padrão (cinza + borda)
            box_width = right_margin - left_margin
            box_x = left_margin

            # altura “máxima” disponível (até o rodapé)
            top = y
            bottom = footer_y + 20
            box_height = top - bottom

            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, bottom, box_width, box_height, fill=1, stroke=0)

            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, bottom, box_width, box_height, fill=0, stroke=1)

            # linha do título interno
            c.line(box_x, top - 22, box_x + box_width, top - 22)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(box_x + 10, top - 16, "Registro de anotações")

            # conteúdo
            text_x = box_x + 12
            text_y = top - 36
            max_width = box_width - 24
            line_height = 12

            c.setFillColorRGB(0, 0, 0)
            text_y = draw_wrapped_text(
                c=c,
                text=anotacoes_txt,
                x=text_x,
                y=text_y,
                max_width=max_width,
                line_height=line_height,
                font_name="Helvetica",
                font_size=10,
                align="justify"
            )

            c.showPage()

    # ==============================
    # Página 13
    # ==============================
    if pagina_pdf_ativa("trajetoria_eventos"):
        left_margin = 40
        right_margin = width - 40

        fig2d = st.session_state.get("fig2d", None)
        df_eventos = st.session_state.get("df_eventos", None)
        df_marks = st.session_state.get("traj_marks_calc", None)

        # Condição principal:
        # só gera esta página se existirem eventos lidos do Excel
        tem_eventos_excel = (
                isinstance(df_eventos, pd.DataFrame)
                and not df_eventos.empty
        )

        if tem_eventos_excel:
            y = draw_header(c, width, height, logo)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(left_margin, y, "Trajetória 2D com Eventos Operacionais")

            y -= 8
            c.line(left_margin, y, right_margin, y)

            # -------------------------------------------------
            # Tratamento dos dados de eventos
            # -------------------------------------------------
            df_evt = df_eventos.copy()

            if "MD Inicial" in df_evt.columns:
                df_evt["MD Inicial"] = pd.to_numeric(df_evt["MD Inicial"], errors="coerce")

            if "MD Final" in df_evt.columns:
                df_evt["MD Final"] = pd.to_numeric(df_evt["MD Final"], errors="coerce")
            else:
                df_evt["MD Final"] = np.nan

            if "Evento" in df_evt.columns:
                df_evt["Evento"] = (
                    df_evt["Evento"]
                    .astype("string")
                    .fillna("")
                    .str.strip()
                )
            else:
                df_evt["Evento"] = ""

            df_evt = df_evt.dropna(subset=["MD Inicial"])
            df_evt = df_evt[df_evt["Evento"] != ""].copy()

            n_eventos = len(df_evt)

            n_pontos = 0
            n_trechos = 0

            if not df_evt.empty:
                n_pontos = int(df_evt["MD Final"].isna().sum())
                n_trechos = int(df_evt["MD Final"].notna().sum())

            # -------------------------------------------------
            # Caixa de resumo
            # -------------------------------------------------
            resumo_eventos = [
                ("Total de eventos", str(n_eventos)),
                ("Eventos pontuais", str(n_pontos)),
                ("Eventos em trecho", str(n_trechos)),
            ]

            box_height = 68

            box_width = right_margin - left_margin
            box_x = left_margin

            y -= 14
            box_y = y - box_height

            # fundo
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(box_x, box_y, box_width, box_height, fill=1, stroke=0)

            # borda
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.8)
            c.rect(box_x, box_y, box_width, box_height, fill=0, stroke=1)

            # linha do título interno
            c.line(
                box_x,
                box_y + box_height - 18,
                box_x + box_width,
                box_y + box_height - 18
            )

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(
                box_x + 10,
                box_y + box_height - 14,
                "Resumo dos eventos importados"
            )

            col1_x = box_x + 12
            col2_x = box_x + box_width / 2
            texto_y = box_y + box_height - 32

            # Conteúdo em uma única linha, com 3 colunas
            inner_x = box_x + 12
            inner_w = box_width - 24
            col_w = inner_w / 3

            label_y = box_y + 28
            valor_y = box_y + 12

            for i, (label, valor) in enumerate(resumo_eventos):
                x_col = inner_x + i * col_w
                x_center = x_col + col_w / 2

                c.setFont("Helvetica-Bold", 10)
                _draw_centered_text(
                    c,
                    x_center,
                    label_y,
                    label,
                    font_name="Helvetica-Bold",
                    font_size=10
                )

                c.setFont("Helvetica", 11)
                _draw_centered_text(
                    c,
                    x_center,
                    valor_y,
                    valor,
                    font_name="Helvetica",
                    font_size=11
                )

                # Linha vertical separando as colunas
                if i > 0:
                    x_sep = x_col
                    c.setStrokeColorRGB(0.75, 0.75, 0.75)
                    c.setLineWidth(0.5)
                    c.line(
                        x_sep,
                        box_y + 6,
                        x_sep,
                        box_y + box_height - 24
                    )

            # -------------------------------------------------
            # Gráfico da trajetória 2D com eventos
            # -------------------------------------------------
            y = box_y - 12

            if fig2d is not None and y > footer_y + 80:
                try:
                    fig2d_pdf = fig2d

                    y = desenhar_fig_plotly_no_pdf(
                        c=c,
                        fig_plotly=fig2d_pdf,
                        left=left_margin,
                        right=right_margin,
                        top=y,
                        bottom=footer_y + 20,
                        titulo=None,
                        scale=1.5
                    )

                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(
                        left_margin,
                        y - 15,
                        f"Não foi possível inserir o gráfico de trajetória 2D: {e}"
                    )
            else:
                c.setFont("Helvetica", 10)
                c.drawString(
                    left_margin,
                    y - 15,
                    "Gráfico de trajetória 2D não disponível."
                )

            draw_footer(c, width, footer_y)
            c.showPage()

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def geo_page():
    st.title('Syngular Geopressure Analysis - SYGA')

    tabs = st.tabs(['Entrada de Dados', 'Coluna litológica', 'Gradiente de Sobrecarga',
                    'Gradiente de Pressão de Poros', 'Estabilidade de Poço', 'Assentamento de Sapatas', 'Fluido de Perfuração',
                    'Anotações', 'Relatório', 'Informações Sobre o SYGA'])

    # Carregar Dados
    with tabs[0]:
        c1, c2, c3 = st.columns((1, 1, 1))
        with c1:
            container = st.container(border=True)
            with container:
                st.markdown("### Upload de Arquivo Excel")

                col1, col2 = st.columns(2)
                with col1:
                    # Input para escolher o intervalo de linhas (step)
                    step = st.number_input("Intervalo entre linhas para leitura", min_value=1, value=1, step=1)
                traj_modo = st.selectbox(
                    "Trajetória utilizada para os cálculos",
                    ["Planejada", "Executada"],
                    index=0,
                    key="traj_modo"
                )
                st.selectbox("Objetivo do estudo", ["Retroanálise", "Previsão de Geopressões"], key="option", index=1)

                uploaded_file = st.file_uploader("***Envie o seu arquivo Excel***", type=["xlsx", "xls", "xlsm"])

                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()

                    st.session_state.main_xlsm = file_bytes
                    st.session_state.wb = carregar_workbook(file_bytes)
                    try:
                        # Selecionar a aba desejada
                        sheet_name = "Perfilagens"

                        # Carregar os dados da aba selecionada
                        df_full = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                        df_full.columns = [str(c).strip() for c in df_full.columns]

                        # Colunas obrigatórias
                        colunas_obrigatorias = [
                            "Profundidade",
                            "MD",
                            "Perfil de densidade",
                            "Perfil sônico",
                            "Perfil Raio Gama"
                        ]

                        colunas_faltantes = [c for c in colunas_obrigatorias if c not in df_full.columns]

                        if colunas_faltantes:
                            st.error(
                                "❌ O arquivo enviado não contém todas as colunas obrigatórias.\n\n"
                                f"**Colunas ausentes:** {', '.join(colunas_faltantes)}"
                            )
                            st.stop()

                        # Lê a trajetória antes de cortar a perfilagem
                        df2 = _ler_trajetoria_do_xlsm(
                            st.session_state.wb,
                            st.session_state.traj_modo
                        )
                        st.session_state.df2 = df2

                        # Calcula a trajetória por mínima curvatura
                        df_out_traj = _calcular_trajetoria_min_curvatura(df2)
                        st.session_state.df_out_traj = df_out_traj.copy()

                        # TVD final do poço
                        tvd_final_poco = float(df_out_traj["TVD"].iloc[-1])
                        st.session_state.tvd_final_poco = tvd_final_poco

                        linhas_antes = len(df_full)

                        # Limita a perfilagem ao TVD final do poço
                        df_full = _limitar_perfilagem_ao_tvd_final(
                            df_full,
                            tvd_final=tvd_final_poco,
                            col_tvd="Profundidade"
                        )

                        linhas_depois = len(df_full)

                        # Aplicar o intervalo step depois do corte
                        df = df_full.iloc[::step].reset_index(drop=True)

                        # Garantir que o último registro cortado está no df
                        if not df_full.iloc[-1].equals(df.iloc[-1]):
                            df = pd.concat([df, df_full.iloc[[-1]]], ignore_index=True)

                        st.session_state.df1 = df

                        with col2:
                            st.write("")
                            st.write("")
                            st.markdown(f"**Total de linhas carregadas:** {len(df)}")

                        st.write("Dados Importados:")
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Garantir que o último registro original está no df
                        if not df_full.iloc[-1].equals(df.iloc[-1]):
                            # Adiciona o último registro ao dataframe
                            df = pd.concat([df, df_full.iloc[[-1]]], ignore_index=True)

                        # Colunas obrigatórias
                        colunas_obrigatorias = [
                            "Profundidade",
                            "MD",
                            "Perfil de densidade",
                            "Perfil sônico",
                            "Perfil Raio Gama"
                        ]

                        # Verificação
                        colunas_faltantes = [c for c in colunas_obrigatorias if c not in df.columns]

                        if colunas_faltantes:
                            st.error(
                                "❌ O arquivo enviado não contém todas as colunas obrigatórias.\n\n"
                                f"**Colunas ausentes:** {', '.join(colunas_faltantes)}"
                            )
                            st.stop()
                        else:
                            st.session_state.df1 = df

                    except Exception as e:
                        st.error(f"Erro ao processar o arquivo: {e}")

                    # lê a aba Início e preenche session_state
                    try:
                        info_ini = _ler_inicio_do_xlsm(st.session_state.wb)

                        if info_ini["poco"] is not None:
                            st.session_state.poco = info_ini["poco"]

                        # Objetivo -> comments
                        st.session_state.comments = info_ini["comments"]

                        # Coordenadas
                        if info_ini["easting"] is not None:
                            st.session_state.easting = info_ini["easting"]

                        if info_ini["northing"] is not None:
                            st.session_state.northing = info_ini["northing"]

                        if info_ini["zona"] is not None:
                            st.session_state.zona = info_ini["zona"]

                        if info_ini["hem"] is not None:
                            st.session_state.hem = info_ini["hem"]

                    except Exception as e:
                        st.error(f"Não foi possível ler a aba 'Início' para preencher dados do poço: {e}")

                    try:
                        df_mud = _ler_peso_fluido_do_xlsm(st.session_state.wb)
                        st.session_state.df_mud = df_mud

                    except Exception as e:
                        if st.session_state.option == "Retroanálise":
                            st.error(f"Não foi possível ler pesos do fluido na aba 'Geopressões': {e}")
                        else:
                            pass

                    try:
                        df_eventos = pd.read_excel(uploaded_file, sheet_name="Eventos")

                        # limpa nomes de colunas (resolve "MD Final " com espaço)
                        df_eventos.columns = [str(c).strip() for c in df_eventos.columns]

                        # garante as colunas esperadas
                        col_req_evt = ["MD Inicial", "MD Final", "Evento"]
                        falt = [c for c in col_req_evt if c not in df_eventos.columns]
                        if falt:
                            st.warning(f"A aba 'Eventos' existe, mas faltam colunas: {', '.join(falt)}")
                            st.session_state.df_eventos = pd.DataFrame(columns=col_req_evt)
                        else:
                            # normaliza tipos e strings
                            df_eventos = df_eventos[col_req_evt].copy()
                            df_eventos["MD Inicial"] = pd.to_numeric(df_eventos["MD Inicial"], errors="coerce")
                            df_eventos["MD Final"] = pd.to_numeric(df_eventos["MD Final"], errors="coerce")
                            df_eventos["Evento"] = (
                                df_eventos["Evento"]
                                .astype("string")
                                .fillna("")
                                .str.strip()
                                .str.replace(r"[,\.;:]+$", "", regex=True)  # remove vírgula no final (ex: "Overpull,")
                            )

                            # remove linhas inválidas
                            df_eventos = df_eventos.dropna(subset=["MD Inicial"])
                            df_eventos = df_eventos[df_eventos["Evento"] != ""].reset_index(drop=True)

                            st.session_state.df_eventos = df_eventos

                    except Exception:
                        # se não tiver a aba, só deixa vazio
                        st.session_state.df_eventos = pd.DataFrame(columns=["MD Inicial", "MD Final", "Evento"])

                    try:
                        if "df2" not in st.session_state or not isinstance(st.session_state.df2, pd.DataFrame):
                            df2 = _ler_trajetoria_do_xlsm(
                                st.session_state.wb,
                                st.session_state.traj_modo
                            )
                            st.session_state.df2 = df2

                        st.session_state.df_interp = _gerar_df_interp_a_partir_df1_df2(
                            st.session_state.df1,
                            st.session_state.df2
                        )

                    except Exception as e:
                        st.error(f"Não foi possível carregar/interpolar trajetória pela aba 'Trajetória': {e}")

                    try:
                        sapatas_df = _ler_sapatas_do_xlsm(st.session_state.wb)
                        st.session_state.sapatas_df = sapatas_df
                    except Exception as e:
                        if st.session_state.option == "Retroanálise":
                            st.error(f"Não foi possível ler as sapatas do Excel: {e}")
                        else:
                            pass

                    try:
                        fases_df = _ler_fases_do_xlsm(st.session_state.wb)
                        st.session_state.fases_df = fases_df
                    except Exception as e:
                        if st.session_state.option == "Retroanálise":
                            st.error(f"Não foi possível ler as fases do Excel: {e}")
                        else:
                            pass

        with c2:
            container = st.container(border=True)  # Criando um container com borda
            with container:
                st.markdown('#### Informações básicas do poço')
                st.text_input('Nome do Usuário', max_chars=None, key='user_name', type="default")
                # st.text_input('País', max_chars=None, key='country_name', type="default")
                lista_paises = list(paises.keys())
                st.selectbox(
                    "País",
                    options=lista_paises,
                    index=lista_paises.index("Brasil"),
                    key="country_name"
                )
                codigo_pais = paises.get(st.session_state.country_name)
                flag_path = f"Flag/{codigo_pais}.png" if codigo_pais else None

                st.text_input('Nome da Companhia', max_chars=None, key='company_name', type="default")
                st.text_input('Nome do Campo', max_chars=None, key='field_name', type="default")

                col1, col2 = st.columns((1, 0.5))
                with col1:
                    st.text_input('Nome do Poço', max_chars=None, key='poco', type="default")
                with col2:
                    st.write('')
                    st.write('')
                    st.checkbox('Poço Onshore', key="onshore", value=True)
                st.text_input('Datum', key='datum', value='RTKB')
                st.text_area('Objetivo do Poço', max_chars=None, key='comments')

        with c3:
            with st.container(border=True, height=730):
                st.markdown("### Coordenadas do Poço")
                # Função para calcular distância geodésica (em metros) entre dois pontos lat/lon
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371000
                    phi1 = math.radians(lat1)
                    phi2 = math.radians(lat2)
                    dphi = math.radians(lat2 - lat1)
                    dlambda = math.radians(lon2 - lon1)
                    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    return R * c

                # --- CARREGAR POÇOS DO YAML ---
                with open("pocos.yaml", "r", encoding="utf-8") as f:
                    dados_yaml = yaml.safe_load(f)

                pocos = dados_yaml['pocos']

                # ------------------------------
                # GEOLOCALIZAÇÃO AUTOMÁTICA
                # ------------------------------
                if "geo_auto_ok" not in st.session_state:
                    st.session_state.geo_auto_ok = False

                if "geo_auto_tentado" not in st.session_state:
                    st.session_state.geo_auto_tentado = False

                if "zona" not in st.session_state:
                    st.session_state.zona = 24

                if "hem" not in st.session_state:
                    st.session_state.hem = "Sul"

                if "easting" not in st.session_state:
                    st.session_state.easting = 857718.96

                if "northing" not in st.session_state:
                    st.session_state.northing = 8933902.28

                if "raio" not in st.session_state:
                    st.session_state.raio = 0.1

                geo = get_geolocation()

                if geo is not None:
                    st.session_state.geo_auto_tentado = True

                    if isinstance(geo, dict) and "coords" in geo:
                        lat = geo["coords"].get("latitude")
                        lon = geo["coords"].get("longitude")

                        if lat is not None and lon is not None and not st.session_state.geo_auto_ok:
                            try:
                                easting_auto, northing_auto, zona_auto, _ = utm.from_latlon(float(lat), float(lon))

                                st.session_state.easting = float(easting_auto)
                                st.session_state.northing = float(northing_auto)
                                st.session_state.zona = int(zona_auto)
                                st.session_state.hem = "Norte" if float(lat) >= 0 else "Sul"
                                st.session_state.geo_auto_ok = True
                                st.rerun()
                            except Exception:
                                pass

                with st.expander(f'Coordenadas da cabeça do poço {st.session_state.poco}', expanded=False):
                    st.number_input("Zona UTM", min_value=1, max_value=60, key='zona')
                    st.radio("Hemisfério", ("Norte", "Sul"), index=1, key='hem')
                    st.number_input(
                        "Coordenada Leste (Easting)",
                        min_value=100000.0,
                        max_value=900000.0,
                        # value=857718.96,
                        format="%.2f",
                        key='easting'
                    )
                    st.number_input(
                        "Coordenada Norte (Northing)",
                        min_value=0.0,
                        max_value=10000000.0,
                        # value=8933902.28,
                        format="%.2f",
                        key='northing'
                    )
                    st.number_input("Raio de busca (km)", min_value=0.1, value=0.1, format="%.2f", key='raio')

                with st.expander("Inserir poços vizinhos", expanded=False):
                    if "pocos_adicionais" not in st.session_state:
                        st.session_state.pocos_adicionais = []

                    nome_poco_add = st.text_input(
                        "Nome do poço vizinho",
                        key="nome_poco_add"
                    )

                    easting_poco_add = st.number_input(
                        "Easting do poço vizinho",
                        min_value=100000.0,
                        max_value=900000.0,
                        value=100000.0,
                        format="%.2f",
                        key="easting_poco_add"
                    )

                    northing_poco_add = st.number_input(
                        "Northing do poço vizinho",
                        min_value=0.0,
                        max_value=10000000.0,
                        value=0.0,
                        format="%.2f",
                        key="northing_poco_add"
                    )

                    col_add, col_limpar = st.columns(2)

                    with col_add:
                        if st.button("Adicionar poço vizinho", use_container_width=True, type='primary'):
                            nome_limpo = nome_poco_add.strip()

                            if nome_limpo:
                                st.session_state.pocos_adicionais.append({
                                    "nome": nome_limpo,
                                    "easting": float(easting_poco_add),
                                    "northing": float(northing_poco_add)
                                })
                            else:
                                st.warning("Informe o nome do poço.")

                    with col_limpar:
                        if st.button("Limpar poços vizinhos", use_container_width=True, type='primary'):
                            st.session_state.pocos_adicionais = []

                    if st.session_state.pocos_adicionais:
                        st.markdown("**Poços vizinhos adicionados:**")
                        df_pocos_add = pd.DataFrame(st.session_state.pocos_adicionais)
                        st.dataframe(df_pocos_add, use_container_width=True, hide_index=True)

                lat_base, lon_base = utm.to_latlon(
                    st.session_state.easting,
                    st.session_state.northing,
                    st.session_state.zona,
                    northern=(st.session_state.hem == "Norte")
                )

                # --- CRIA MAPA COM POÇO BASE E CÍRCULO ---
                m = folium.Map(
                    location=[lat_base, lon_base],
                    zoom_start=17,
                    zoom_control=False,
                    attributionControl=False,
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri'
                )

                # folium.Marker(
                #     [lat_base, lon_base],
                #     popup=st.session_state.poco if st.session_state.poco else "Poço",
                #     icon=folium.CustomIcon('poço.png', icon_size=(50, 50))
                # ).add_to(m)

                folium.Circle(
                    location=[lat_base, lon_base],
                    radius=st.session_state.raio * 1000,
                    color='green',
                    fill=True,
                    fill_opacity=0.2,
                    popup=f"Raio: {st.session_state.raio:.2f} km"
                ).add_to(m)

                if uploaded_file:
                    st.session_state.profundidade_maxima = max(df['Profundidade'])

                profundidade_maxima = st.session_state.get('profundidade_maxima', None)

                if profundidade_maxima is not None:
                    pocos_filtrados = [
                        poco for poco in pocos
                        if poco.get("profundidade_vertical_m") is not None and
                           poco["profundidade_vertical_m"] <= profundidade_maxima
                    ]
                else:
                    pocos_filtrados = pocos

                # --- ADICIONAR POÇOS MANUAIS INFORMADOS PELO USUÁRIO ---
                pocos_manuais = []

                if st.session_state.pocos_adicionais:
                    for row in st.session_state.pocos_adicionais:
                        nome = row.get("nome")
                        e = row.get("easting")
                        n = row.get("northing")

                        if not nome or e is None or n is None:
                            continue

                        pocos_manuais.append({
                            "nome": str(nome),
                            "zona_utm": st.session_state.zona,
                            "hem": st.session_state.hem,
                            "coordenadas": {
                                "easting": float(e),
                                "northing": float(n)
                            },
                            "origem": "manual",
                            "profundidade_vertical_m": None,
                            "peso_eq_lb_gal": None
                        })

                # Junta os poços do YAML com os poços inseridos manualmente
                pocos_para_plotar = []

                for poco in pocos_filtrados:
                    poco_plot = poco.copy()
                    poco_plot["origem"] = "yaml"
                    pocos_para_plotar.append(poco_plot)

                pocos_para_plotar.extend(pocos_manuais)

                # --- PLOTAR POÇOS E CALCULAR DISTÂNCIAS ---
                dados_pontos = []

                def _hemisferio_norte(valor):
                    txt = str(valor).strip().lower()
                    return txt in ("n", "norte", "north")

                for poco in pocos_para_plotar:
                    e = poco['coordenadas']['easting']
                    n = poco['coordenadas']['northing']

                    hem_poco = poco.get("hem", "Sul")

                    lat_p, lon_p = utm.to_latlon(
                        e,
                        n,
                        poco['zona_utm'],
                        northern=_hemisferio_norte(hem_poco)
                    )

                    dist = haversine(lat_base, lon_base, lat_p, lon_p)
                    dentro_do_raio = dist <= (st.session_state.raio * 1000)

                    cor = "blue" if poco.get("origem") == "manual" else "red"
                    icone = "map-marker"

                    popup_text = f"{poco['nome']}<br>Distância: {dist / 1000:.2f} km"

                    folium.Marker(
                        location=[lat_p, lon_p],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color=cor, icon=icone)
                    ).add_to(m)

                    dados_pontos.append({
                        "Nome": poco['nome'],
                        "Origem": poco.get("origem", "yaml"),
                        "Easting": e,
                        "Northing": n,
                        "Distância (km)": round(dist / 1000, 2),
                        "Dentro do Raio": "Sim" if dentro_do_raio else "Não",
                        "Profundidade Vertical (m)": poco.get("profundidade_vertical_m", None),
                        "Peso Eq. (lb/gal)": poco.get("peso_eq_lb_gal", None)
                    })

                # --- PLOTAR POÇO PRINCIPAL POR CIMA DOS DEMAIS ---
                folium.Marker(
                    location=[lat_base, lon_base],
                    popup=st.session_state.poco if st.session_state.poco else "Poço",
                    icon=folium.CustomIcon('poço.png', icon_size=(30, 30)),
                    z_index_offset=10000
                ).add_to(m)

                # --- TABELA DE PONTOS DENTRO DO RAIO ---
                df_resultado = pd.DataFrame(dados_pontos)
                df_dentro = df_resultado[df_resultado["Dentro do Raio"] == "Sim"].sort_values(
                    by="Distância (km)"
                ).reset_index(drop=True)
                df_dentro_exibir = df_dentro.drop(columns=["Dentro do Raio"])

                with st.expander('Poços dentro do raio de busca', expanded=False):
                    st.markdown("### Poços dentro do raio de busca")
                    st.dataframe(df_dentro_exibir, use_container_width=True, hide_index=True)

                # --- MOSTRAR MAPA ---
                st.session_state["mapa_folium_pdf"] = m
                st_folium(m, use_container_width=True, height=400)
                m.save('filename.png')

    # Coluna Litológica
    with tabs[1]:

        st.title("Construção da coluna litológica")

        profundidades = []
        formacoes = []
        litologias = []
        st.session_state.well_name = st.session_state.poco

        with st.container(border=True):

            st.subheader("Idades geológicas")

            st.selectbox(
                "Inserir Idade Geológica",
                ['Não', 'Sim'],
                key="idg"
            )

            if st.session_state.idg == 'Sim':

                st.number_input(
                    "Quantidade de idades geológicas",
                    min_value=1,
                    step=1,
                    key="n_id"
                )

                prof_ini_id = []
                prof_fim_id = []
                idade_geo = []

                # profundidade máxima do poço
                try:
                    prof_max = df["Profundidade"].max()
                except:
                    prof_max = 0

                for i in range(int(st.session_state.n_id)):

                    col1, col2, col3 = st.columns(3)

                    # =============================
                    # PROFUNDIDADE INICIAL
                    # =============================

                    with col1:

                        if i == 0:

                            p_ini = st.number_input(
                                f"Profundidade inicial **Intervalo {i + 1}**",
                                step=1.0,
                                format="%f",
                                min_value=0.0,
                                key=f'prof_inicial_2_{i}'
                            )

                        else:

                            p_ini = st.number_input(
                                f"Profundidade inicial **Intervalo {i + 1}**",
                                value=st.session_state.get(f'prof_final_2_{i - 1}', 0.0),
                                disabled=True,
                                key=f'prof_inicial_2_{i}'
                            )

                    # =============================
                    # PROFUNDIDADE FINAL
                    # =============================

                    with col2:

                        if i == int(st.session_state.n_id) - 1:

                            p_fim = st.number_input(
                                f"Profundidade final **Intervalo {i + 1}**",
                                value=float(prof_max + 100),
                                disabled=True,
                                key=f'prof_final_2_{i}'
                            )

                        else:

                            p_fim = st.number_input(
                                f"Profundidade final **Intervalo {i + 1}**",
                                step=1.0,
                                format="%f",
                                min_value=0.0,
                                key=f'prof_final_2_{i}'
                            )

                    # =============================
                    # IDADE
                    # =============================

                    with col3:

                        idade = st.text_input(
                            f"Idade Geológica {i + 1}",
                            key=f'idg_{i}'
                        )

                    prof_ini_id.append(p_ini)
                    prof_fim_id.append(p_fim)
                    idade_geo.append(idade)

                # dataframe final (mesmo formato usado pela função idade_formacao)
                st.session_state.df_idade = pd.DataFrame({
                    "Topo (m)": prof_ini_id,
                    "Base (m)": prof_fim_id,
                    "Idade": idade_geo
                })

        with st.container(border=True):

            st.subheader("Descrição das camadas litológicas")

            if "pocos" not in st.session_state:
                st.session_state.pocos = {"Poço": {}}

            if "well_selected" not in st.session_state:
                st.session_state.well_selected = "Poço"

            pocos = st.session_state.pocos.keys()

            selected = st.session_state.well_selected

            # ===== AUTO-IMPORT LITOLOGIA DO XLSM (ABA "Litologia") =====
            try:
                if "main_xlsm" in st.session_state and st.session_state.main_xlsm is not None:

                    if st.session_state.get("lito_import_ok", False) is False:
                        df_lito_excel = _ler_litologia_do_xlsm(st.session_state.wb)

                        st.session_state.df_lito_excel = df_lito_excel

                        _aplicar_litologia_no_state(selected, df_lito_excel)

                        st.session_state.lito_import_ok = True

            except Exception as e:
                st.warning(f"Falha ao importar litologia do XLSM: {e}")

            try:
                if 'formation' in st.session_state.pocos[selected]:
                    n_fm = len(st.session_state.pocos[selected]['formation'])
                else:
                    n_fm = 5
            except (KeyError, IndexError):
                n_fm = 5

            excel_carregado = st.session_state.get("lito_import_ok", False)

            num_formacoes = st.number_input(
                "Número de formações:",
                min_value=1,
                max_value=20,
                key='n_fm',
                value=int(st.session_state.get("n_fm", 5)),
                disabled=excel_carregado
            )

            for i in range(st.session_state.n_fm):

                try:
                    if 'profundidade' in st.session_state.pocos[selected]:
                        p = st.session_state.pocos[selected]['profundidade'][i]
                    else:
                        p = 0.0

                    if 'formation' in st.session_state.pocos[selected]:
                        f = st.session_state.pocos[selected]['formation'][i]
                    else:
                        f = ''

                    if 'litologia' in st.session_state.pocos[selected]:
                        y = st.session_state.pocos[selected]['litologia'][i]
                    else:
                        y = 'Arenito'

                except (KeyError, IndexError):
                    p = 0.0
                    f = ''
                    y = 'Arenito'

                col1, col2, col3 = st.columns(3)

                with col1:
                    prof = st.number_input(
                        f"Topo da {i + 1}ª formação (TVD)",
                        key=f"prof_{i}",
                        value=p
                    )

                with col2:
                    fm = st.text_input(
                        f"Nome da {i + 1}ª formação",
                        key=f"fm_{i}",
                        value=f
                    )

                with col3:

                    lithology = [
                        "Argilito",
                        "Arenito",
                        "Folhelho",
                        "Calcário",
                        "Carbonato",
                        "Siltito",
                        "Diamictito",
                        "Conglomerado",
                        "Anidrita / Gipsita",
                        "Halita",
                        "Calcissiltito",
                        "Calcarenito",
                        "Calcirrudito",
                        "Coquina",
                        "Dolomito",
                        "Basalto",
                        "Diabásio"
                    ]

                    lit = st.selectbox(
                        f"Litologia da {i + 1}ª formação",
                        lithology,
                        key=f"lit_{i}",
                        index=lithology.index(y)
                    )

                profundidades.append(prof)
                formacoes.append(fm)
                litologias.append(lit)

            st.session_state.pocos[selected]["profundidade"] = profundidades
            st.session_state.pocos[selected]["formation"] = formacoes
            st.session_state.pocos[selected]["litologia"] = litologias

            if "perfil" not in st.session_state.pocos[selected]:
                st.session_state.pocos[selected]["perfil"] = {}

            if "df_idade" in st.session_state and not st.session_state.df_idade.empty:

                base_final = st.session_state.df_idade["Base (m)"].max()

            else:

                base_final = max(profundidades) if profundidades else 0

            # base da última litologia +100
            st.session_state.pocos[selected]["tvd"] = base_final + 100

        with st.container(border=True):

            st.markdown("### Visualização")

            fig = plot_correlacao_com_logs(
                st.session_state.pocos,
                [False, False, False],
                True,
                True,
                list(st.session_state.pocos.keys()),
                False,
                escala=(30, 300)
            )

            st.session_state.fig_coluna_lito = fig

            st.plotly_chart(fig)

    # Gradiente de Sobrecarga
    with tabs[2]:
        tb = st.tabs(['Gradiente de Sobrecarga', 'Tabela de Dados Calculados'])
        with tb[0]:
            if uploaded_file:
                col1, col2, col3 = st.columns((0.9, 0.9, 1))
                with col1:
                    # if st.session_state.s_gr:
                    df.insert(
                        loc=5,
                        column='Raio Gama Suavizado',
                        value=suavizar(
                            df['Profundidade'],
                            df['Perfil Raio Gama']
                        )
                    )
                    # ENTRADA DE DADOS
                    with st.container(border=True):
                        if st.session_state.onshore:
                            x = False
                        else:
                            x = True
                        st.segmented_control("***Correlação para estimativa da densidade da formação***",
                                             ['Perfil de Densidade', 'Gardner'],
                                             selection_mode="multi",
                                             default='Perfil de Densidade',
                                             key='gard',
                                             width="stretch")
                        # st.radio('***Correlação para estimativa da densidade da formação***',
                        #          ['Perfil de Densidade', 'Gardner'], key="gard", index=0,
                        #          disabled=False)
                        st.segmented_control("***Correlação para estimativa da densidade da formação***",
                                             ['Miller', 'Bourgoyne'],
                                             selection_mode="multi",
                                             default='Miller',
                                             key='gard_2',
                                             width="stretch",
                                             disabled=True)
                        # st.radio('',
                        #          ['Miller', 'Bourgoyne'], key="gard2", index=0,
                        #          disabled=True)
                        st.segmented_control("***Extrapolação***",
                                             ['Desativada', 'Ativada'],
                                             selection_mode="single",
                                             default='Desativada',
                                             key='ex',
                                             width="stretch",
                                             disabled=x)

                        # MÉDIA DAS DENSIDADES CASO FOR FAZER A EXTRAPOLAÇÃO
                        if st.session_state.ex == 'Ativada':
                            if st.session_state.onshore:
                                if not df['Perfil de densidade'].isnull().all():
                                    st.session_state.md = round(df['Perfil de densidade'].dropna().head(10).mean(), 2)
                                else:
                                    st.session_state.md = 2.0
                            else:
                                st.session_state.md = 2.0
                            st.number_input('Insira o ***Valor médio da densidade das camadas superiores***',
                                            step=0.1, format='%f', key='ds', min_value=0.0, value=st.session_state.md)

                        # CÁLCULOS
                        with st.form("gs_form", border=False):
                            # if st.session_state.gard == 'Miller':
                            #     parametros_miller()
                            # INSERIR DADOS
                            st.markdown('***Dados de elevação***')
                            st.number_input('***Air Gap***', step=1.0, format='%f', key='rtkb', min_value=0.0,
                                            value=9.4)
                            if st.session_state.onshore:
                                st.number_input('***Elevação do DATUM***', step=1.0, format='%f', key='es',
                                                min_value=0.0, value=110.0)
                                st.session_state.nf = st.session_state.rtkb + st.session_state.es

                            else:
                                st.number_input("Insira o valor da ***Lâmina D'água***", step=1.0, format='%f',
                                                key='lda', min_value=0.0)
                            float_sonic = df['Perfil sônico'].apply(lambda x: isinstance(x, float)).any()
                            float_dens = df['Perfil de densidade'].apply(lambda x: isinstance(x, float)).any()

                            if float_dens or float_sonic:
                                # OFFSHORE
                                if not st.session_state.onshore:
                                    if st.session_state.ex == 'Desativada':
                                        df_sup = pd.DataFrame({
                                            'Profundidade': [st.session_state.rtkb, st.session_state.lda],
                                            'Perfil de densidade': [0, 1.03],
                                            'Perfil sônico': [None, None]
                                        })
                                    else:
                                        prof_start = (st.session_state.rtkb + st.session_state.lda) + 1
                                        prof_end = df['Profundidade'].iloc[0]

                                        if prof_end > prof_start:
                                            prof = list(range(int(prof_start), int(prof_end) + 1))
                                        else:
                                            prof = []

                                        df_sup = pd.DataFrame({
                                            'Profundidade': [st.session_state.rtkb,
                                                             st.session_state.rtkb + st.session_state.lda] + prof,
                                            'Perfil de densidade': [None, 1.03] + [None] * len(prof),
                                            'Perfil sônico': [None, None] + [None] * len(prof)
                                        })
                                    # Concatena dataframe superior com o dataframe principal
                                    df = pd.concat([df_sup, df], ignore_index=True)

                                    dt = [0]
                                    dd, dm = [], []

                                    if 'Gardner' in st.session_state.gard:
                                        mask = df['Perfil de densidade'].isna()

                                        sonico = df.loc[mask, 'Perfil sônico']

                                        df.loc[mask, 'Perfil de densidade'] = (
                                                0.23 * ((1_000_000 / sonico) ** 0.25)
                                        )
                                    # # Cálculo da densidade total linha a linha
                                    # for index in range(1, len(df)):
                                    #     dens = df['Perfil de densidade'].iloc[index]
                                    #     sonic = df['Perfil sônico'].iloc[index]
                                    #
                                    #     if not pd.isnull(dens) and dens != 0:
                                    #         dt.append(dens)
                                    #     elif pd.isnull(dens) and not pd.isnull(sonic) and sonic != 0:
                                    #         dt.append(0.23 * ((10 ** 6 / sonic) ** 0.25))
                                    #     else:
                                    #         dt.append(st.session_state.md)
                                    #
                                    # df['Perfil de densidade'] = dt

                                    # Cálculo de ΔD (m)
                                    dd.append(df['Profundidade'].iloc[0])
                                    for i in range(1, len(df)):
                                        dd.append(
                                            df['Profundidade'].iloc[i] - df['Profundidade'].iloc[i - 1])
                                    df['ΔD (m)'] = dd

                                    # Cálculo de Densidade x ΔD x 1,422 (psi)
                                    for i in range(len(df)):
                                        dm.append(df['Perfil de densidade'].iloc[i] * df['ΔD (m)'].iloc[i] * 1.422)

                                    df['Densidade x ΔD x 1,422 (psi)'] = dm
                                    df['Pressão de Sobrecarga (psi)'] = df['Densidade x ΔD x 1,422 (psi)'].cumsum()

                                    gs = []
                                    for i in range(len(df)):
                                        if df['Profundidade'].iloc[i] <= st.session_state.rtkb:
                                            gs.append(None)
                                        else:
                                            gs.append(df['Pressão de Sobrecarga (psi)'].iloc[i] / (
                                                    0.1704 * df['Profundidade'].iloc[i]))

                                    df['Gradiente de Sobrecarga (lb/gal)'] = gs

                                # ONSHORE
                                if st.session_state.onshore:
                                    # SE EXTRAPOLAR E NÃO TIVER DADOS DE DENSIDADE, DENSIDADE DAS CAMADAS EXTRAPOLADAS IGUAL A 2
                                    # SE NÃO EXTRAPOLAR, NÃO FAZ NADA
                                    if st.session_state.ex == 'Ativada':
                                        prof_min = df['Profundidade'][0]
                                        ext = np.arange(0, prof_min, 1)
                                        ext_list = list(ext)
                                        prof_list = df['Profundidade'].tolist()
                                        dens_list = df['Perfil de densidade'].tolist()
                                        son_list = df['Perfil sônico'].tolist()
                                        gr_list = df['Perfil Raio Gama'].tolist()
                                        gr_list_s = df['Raio Gama Suavizado'].tolist()
                                        profundidade = ext_list + prof_list
                                        linha_extrapolada = [True] * len(ext_list) + [False] * len(prof_list)
                                        densidade = [st.session_state.ds if prof > st.session_state.rtkb else 0
                                                        for prof in ext_list
                                                    ] + dens_list

                                        sonico = [None] * len(ext_list) + son_list
                                        gr = [None] * len(ext_list) + gr_list
                                        gr_s = [None] * len(ext_list) + gr_list_s

                                    else:
                                        profundidade = df['Profundidade'].tolist()
                                        densidade = df['Perfil de densidade'].tolist()
                                        sonico = df['Perfil sônico'].tolist()
                                        gr = df['Perfil Raio Gama'].tolist()
                                        gr_s = df['Raio Gama Suavizado'].tolist()
                                        linha_extrapolada = [False] * len(profundidade)

                                    profundidade_solo = []
                                    for i in range(len(profundidade)):
                                        if st.session_state.ex == 'Ativada':
                                            if profundidade[i] <= st.session_state.rtkb:
                                                profundidade_solo.append(0)
                                            else:
                                                profundidade_solo.append(profundidade[i] - st.session_state.rtkb)
                                        else:
                                            profundidade_solo.append(profundidade[i])

                                    st.session_state.ext_df = pd.DataFrame({
                                        'Profundidade em relação a mesa rotativa (m)': profundidade,
                                        'Profundidade em relação ao solo (m)': profundidade_solo,
                                        'Densidade (g/cm³)': densidade,
                                        'Sônico (µs/pé)': sonico,
                                        'Perfil Raio Gama': gr,
                                        'Raio Gama Suavizado': gr_s,
                                        'Linha Extrapolada': linha_extrapolada
                                    })

                                    if st.session_state.ex == 'Ativada':
                                        st.session_state.ext_df.loc[0, 'Densidade (g/cm³)'] = 0

                                    if 'Gardner' in st.session_state.gard:
                                        mask = st.session_state.ext_df['Densidade (g/cm³)'].isna()

                                        sonico = st.session_state.ext_df.loc[mask, 'Sônico (µs/pé)']

                                        st.session_state.ext_df.loc[mask, 'Densidade (g/cm³)'] = (
                                                0.23 * ((1_000_000 / sonico) ** 0.25)
                                        )

                                    dd = []

                                    for i in range(len(st.session_state.ext_df)):
                                        if i == 0:
                                            if st.session_state.ex == 'Desativada':
                                                dd.append(st.session_state.ext_df[
                                                              'Profundidade em relação a mesa rotativa (m)'].iloc[0])
                                            else:
                                                dd.append(0)
                                        else:
                                            if st.session_state.ex == 'Ativada':
                                                if st.session_state.ext_df[
                                                    'Profundidade em relação a mesa rotativa (m)'].iloc[
                                                    i] <= st.session_state.rtkb:
                                                    dd.append(0)
                                                else:
                                                    dd.append(st.session_state.ext_df[
                                                                  'Profundidade em relação a mesa rotativa (m)'].iloc[
                                                                  i] - st.session_state.ext_df[
                                                                  'Profundidade em relação a mesa rotativa (m)'].iloc[
                                                                  i - 1])
                                            else:
                                                dd.append(st.session_state.ext_df[
                                                              'Profundidade em relação a mesa rotativa (m)'].iloc[i] -
                                                          st.session_state.ext_df[
                                                              'Profundidade em relação a mesa rotativa (m)'].iloc[
                                                              i - 1])
                                    st.session_state.ext_df['ΔD (m)'] = dd

                                    dm = []
                                    for i in range(len(st.session_state.ext_df)):
                                        if st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)'].iloc[
                                            i] <= st.session_state.rtkb:
                                            dm.append(0)
                                        else:
                                            dm.append(st.session_state.ext_df['Densidade (g/cm³)'].iloc[i] *
                                                      st.session_state.ext_df['ΔD (m)'].iloc[i] * 1.422)

                                    st.session_state.ext_df['Densidade (g/cm³) x ΔD x 1,422 (psi)'] = dm

                                    st.session_state.ext_df['Pressão de Sobrecarga (psi)'] = st.session_state.ext_df[
                                        'Densidade (g/cm³) x ΔD x 1,422 (psi)'].cumsum()

                                    gs = []
                                    for i in range(len(st.session_state.ext_df)):
                                        if st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)'].iloc[
                                            i] < st.session_state.rtkb:
                                            gs.append(0)
                                        else:
                                            gs.append(
                                                st.session_state.ext_df['Pressão de Sobrecarga (psi)'].iloc[i] /
                                                (0.1704 * st.session_state.ext_df[
                                                    'Profundidade em relação a mesa rotativa (m)'].iloc[i]))

                                    st.session_state.ext_df['Gradiente de Sobrecarga (lb/gal)'] = gs

                                # FALTA IMPLEMENTAR
                                # MILLER
                                # BOURGOYNE

                            else:
                                st.warning('Não foram encontrados dados válidos de perfilagem')

                            st.form_submit_button("Calcular Gradiente de Sobrecarga", use_container_width=True,
                                                  type='primary')

                # Gráfico do Gradiente de Sobrecarga
                with col3:
                    with st.container(border=True):
                        def reset_config():
                            if st.session_state.ogs == "Gradiente (lb/gal)":
                                st.session_state.x_min_s = 7
                                st.session_state.x_max_s = 23
                                st.session_state.x_step_s = 1

                            else:
                                st.session_state.x_min_s = 0
                                st.session_state.x_max_s = int(
                                    st.session_state.ext_df['Pressão de Sobrecarga (psi)'].max()) + 200
                                st.session_state.x_step_s = 500

                            st.session_state.y_min_s = 0
                            st.session_state.y_max_s = int(df['Profundidade'].max()) + 100
                            st.session_state.y_step_s = 200

                        with st.expander("Configurações do Gráfico", expanded=False):
                            st.segmented_control("***Opção de Gráfico***", ['Gradiente (lb/gal)',
                                                                            'Pressão (psi)'],
                                                 selection_mode="single",
                                                 default='Gradiente (lb/gal)', key='ogs', width="stretch")
                            # st.selectbox("Profundidade", ['TVD', 'MD'], key="t_prof_s")
                            st.number_input("Eixo X - mínimo", value=7, step=1, key="x_min_s")
                            st.number_input("Eixo X - máximo", value=23, step=1, key="x_max_s")
                            st.number_input("Passo do eixo X", value=1, step=1, key="x_step_s")

                            st.number_input("Eixo Y - mínimo", value=0,
                                            step=100, key="y_min_s")
                            st.number_input("Eixo Y - máximo", value=int(df['Profundidade'].max()) + 100,
                                            step=100, key="y_max_s")
                            st.number_input("Passo do eixo Y", value=200, step=50, key="y_step_s")
                            # Botão de reset com callback
                            st.button("Resetar Configurações Gráficas - Gradiente de Sobrecarga", on_click=reset_config,
                                      type="primary", use_container_width=True)
                        if st.session_state.ogs == "Gradiente (lb/gal)":
                            if st.session_state.onshore:
                                st.session_state.oes = st.session_state.ext_df['Gradiente de Sobrecarga (lb/gal)']
                                st.session_state.profs = st.session_state.ext_df[
                                    'Profundidade em relação a mesa rotativa (m)']
                            else:
                                st.session_state.oes = df['Gradiente de Sobrecarga (lb/gal)']
                                st.session_state.profs = df['Profundidade']
                            st.session_state.oesl = "G. de Sobrecarga"

                        else:
                            st.session_state.oes = st.session_state.ext_df['Pressão de Sobrecarga (psi)']
                            st.session_state.oesl = "P. de Sobrecarga"

                        # Ajuste da figura com coluna de idade + coluna litológica
                        st.session_state.fig_gs = plt.figure(figsize=(8, 10))

                        usar_coluna_idade = (
                                st.session_state.get("idg") == "Sim"
                                and "df_idade" in st.session_state
                                and isinstance(st.session_state.df_idade, pd.DataFrame)
                                and not st.session_state.df_idade.empty
                        )

                        if usar_coluna_idade:
                            # COM coluna de idade
                            gs = gridspec.GridSpec(
                                1, 4,
                                width_ratios=[0.10, 0.18, 0.21, 1],
                                wspace=0
                            )

                            ax_idade = st.session_state.fig_gs.add_subplot(gs[0])
                            ax1 = st.session_state.fig_gs.add_subplot(gs[1], sharey=ax_idade)

                            ax_gap = st.session_state.fig_gs.add_subplot(gs[2])
                            ax_gap.axis("off")

                            ax = st.session_state.fig_gs.add_subplot(gs[3], sharey=ax_idade)

                            idade_formacao(
                                ax_idade,
                                st.session_state.df_idade,
                                st.session_state.y_max_s
                            )

                            ax_idade.tick_params(
                                axis="y",
                                which="both",
                                left=False,
                                right=False,
                                labelleft=False,
                                labelright=False
                            )

                            ax_idade.set_ylabel("")

                            plt.setp(ax1.get_yticklabels(), visible=False)
                            plt.setp(ax.get_yticklabels(), visible=False)

                        else:
                            # SEM coluna de idade
                            gs = gridspec.GridSpec(
                                1, 3,
                                width_ratios=[0.18, 0.21, 1],
                                wspace=0
                            )

                            ax1 = st.session_state.fig_gs.add_subplot(gs[0])

                            ax_gap = st.session_state.fig_gs.add_subplot(gs[1])
                            ax_gap.axis("off")

                            ax = st.session_state.fig_gs.add_subplot(gs[2], sharey=ax1)

                            plt.setp(ax.get_yticklabels(), visible=False)

                        # DataFrame usado pela coluna litológica
                        # Se o usuário escolheu "Permeável / Não permeável", tenta usar o df_pp salvo.
                        # Se ainda não existir LBF_calc, cai automaticamente para a litologia do Excel.
                        df_lito_gs = df.copy()

                        if (
                                st.session_state.get("tipo_coluna_litologica_graficos") == "Permeável / Não permeável"
                                and "df_pp_lito" in st.session_state
                                and isinstance(st.session_state.df_pp_lito, pd.DataFrame)
                                and not st.session_state.df_pp_lito.empty
                        ):
                            df_lito_gs = st.session_state.df_pp_lito.copy()

                        # Garante compatibilidade caso o dataframe usado seja o df original
                        if "Profundidade (m)" not in df_lito_gs.columns and "Profundidade" in df_lito_gs.columns:
                            df_lito_gs["Profundidade (m)"] = df_lito_gs["Profundidade"]

                        lito(
                            ax1,
                            df_lito_gs,
                            profundidades,
                            litologias,
                            st.session_state.y_max_s
                        )

                        if st.session_state.onshore:
                            if st.session_state.rtkb and st.session_state.es != 0:
                                if st.session_state.ex == 'Desativada':
                                    ax.plot(st.session_state.oes, st.session_state.profs,
                                            color='black', linestyle='-', linewidth=2, label=st.session_state.oesl)
                                else:
                                    ax.plot(st.session_state.oes,
                                            st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)'],
                                            color='black', linestyle='-', linewidth=2, label=st.session_state.oesl)

                        else:
                            if st.session_state.rtkb and st.session_state.lda != 0:
                                ax.plot(st.session_state.oes, st.session_state.profs,
                                        color='black', linestyle='-', linewidth=2, label=st.session_state.oesl)

                        if st.session_state.ogs == "Gradiente (lb/gal)":
                            ax.set_title('Gradiente de Sobrecarga (lb/gal)', fontsize=14, fontweight='bold')
                            ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                            ax.set_ylabel('Profundidade em relação à mesa rotativa', fontsize=12)
                        else:
                            ax.set_title('Pressão de Sobrecarga (psi)', fontsize=14, fontweight='bold')
                            ax.set_xlabel('Pressão (psi)', fontsize=12)
                            ax.set_ylabel('Profundidade em relação à mesa rotativa', fontsize=12)
                        ax.set_ylabel('Profundidade em relação à mesa rotativa', fontsize=12)
                        ax.invert_yaxis()
                        max_depth = int(df['Profundidade'].max()) + 100
                        margin = 20
                        ax.set_yticks(
                            range(st.session_state.y_min_s, st.session_state.y_max_s, st.session_state.y_step_s))
                        ax.set_ylim(st.session_state.y_max_s, st.session_state.y_min_s)
                        ax.set_xticks(
                            range(st.session_state.x_min_s, st.session_state.x_max_s, st.session_state.x_step_s))
                        ax.set_xlim(st.session_state.x_min_s, st.session_state.x_max_s)
                        ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                        ax.grid(True, linestyle='--', alpha=0.5)
                        ax.legend(
                            loc='upper right',
                            fontsize=8,
                            frameon=True,
                            shadow=True,
                            fancybox=True,
                            framealpha=1,
                            facecolor='white',
                            edgecolor='gray'
                        )
                        add_watermark(
                            ax,
                            logo_path="logo2.png",
                            xy=(0.50, 0.5),
                            zoom=0.2,
                            alpha=0.2,
                            zorder=0
                        )

                        st.pyplot(st.session_state.fig_gs)

                # Imagem Datum
                with col2:
                    container = st.container(border=True)  # Criando um container com borda
                    with container:
                        if st.session_state.onshore:
                            image = Image.open("rig.png")
                            st.image(image, width=200)
                            st.markdown(
                                f"""
                                <div style='position: absolute; top: -240px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Datum: </strong> {st.session_state.datum} <br> 
                                </div>
                                <div style='position: absolute; top: -197px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Elevação DATUM: </strong> {st.session_state.es:.2f} m <br>
                                </div>
                                <div style='position: absolute; top: -170px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Air gap: </strong> {st.session_state.rtkb:.2f} m <br>
                                </div>
                                <div style='position: absolute; top: -140px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Solo <br>
                                </div>
                                <div style='position: absolute; top: -90px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Elevação do solo: </strong> {st.session_state.es - st.session_state.rtkb:.2f} m <br>
                                </div>
                                <div style='position: absolute; top: -43px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Nível do Mar </strong>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        else:
                            # if not st.session_state.bop:
                            image = Image.open("rig_offshore.png")
                            st.image(image, width=200)
                            st.markdown(
                                f"""
                                <div style='position: absolute; top: -240px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Datum: </strong> {st.session_state.datum} <br> 
                                </div>
                                <div style='position: absolute; top: -170px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Air gap: </strong> {st.session_state.rtkb:.2f} m <br>
                                </div>
                                <div style='position: absolute; top: -90px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Lâmina D'água: </strong> {st.session_state.lda:.2f} m <br>
                                </div>
                                <div style='position: absolute; top: -43px; left: 200px;
                                            padding: 10px; border-radius: 5px;'>
                                    <strong>Leito Marinho </strong>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            else:
                st.error('Por favor, insira um documento!', icon="🚨")

        # Ver Dataframes
        with tb[1]:
            if uploaded_file:
                if not st.session_state.onshore:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    if st.session_state.rtkb and st.session_state.es != 0:
                        st.dataframe(st.session_state.ext_df, use_container_width=True, hide_index=True)

    # Gradiente de Pressão de Poros
    with tabs[3]:
        tb = st.tabs(['Gradiente de Pressão de Poros', 'Tabela de Dados Calculados'])

        with tb[0]:
            if uploaded_file:
                if st.session_state.rtkb != 0:
                    coluna1, coluna2, coluna3 = st.columns((1, 1, 1))
                    # ENTRADA DE DADOS
                    with coluna1:
                        if "suav_s" not in st.session_state:
                            st.session_state.suav_s = False

                        if "fpp" not in st.session_state:
                            st.session_state.fpp = 0.01

                        with st.container(border=True):
                            st.segmented_control(
                                "***Mecanismo Gerador de Pressão de Poros***",
                                ['Subcompactação', 'Transferência Lateral'],
                                selection_mode="single",
                                default='Subcompactação',
                                key='mgpp',
                                width="stretch",
                                disabled=True
                            )

                            if st.session_state.onshore:
                                profundidade = st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)']
                                densidade = st.session_state.ext_df['Densidade (g/cm³)']
                                sonico = st.session_state.ext_df['Sônico (µs/pé)']
                                raio_gama = st.session_state.ext_df['Perfil Raio Gama']
                                raio_gama_s = st.session_state.ext_df['Raio Gama Suavizado']

                                linha_extrapolada_pp = st.session_state.ext_df.get(
                                    'Linha Extrapolada',
                                    pd.Series(False, index=st.session_state.ext_df.index)
                                )

                            else:
                                profundidade = df['Profundidade']
                                densidade = df['Perfil de densidade']
                                sonico = df['Perfil sônico']
                                raio_gama = df['Perfil Raio Gama']
                                raio_gama_s = df['Raio Gama Suavizado']

                                linha_extrapolada_pp = pd.Series(False, index=df.index)

                            df_pp = pd.DataFrame({
                                'Profundidade (m)': profundidade,
                                'Perfil de densidade (g/cm³)': densidade,
                                'Perfil sônico (µs/pé)': sonico,
                                'Perfil Raio Gama': raio_gama,
                                'Raio Gama Suavizado': raio_gama_s,
                                'Linha Extrapolada': linha_extrapolada_pp
                            })

                            if st.session_state.suav_s:
                                perfil_sonico_suav = suavizar(profundidade, sonico)

                                if 'Perfil sônico suavizado (µs/pé)' not in df_pp.columns:
                                    df_pp.insert(
                                        3,
                                        'Perfil sônico suavizado (µs/pé)',
                                        perfil_sonico_suav
                                    )
                                else:
                                    df_pp['Perfil sônico suavizado (µs/pé)'] = perfil_sonico_suav

                            df_pp['Perfil sônico (µs/pé) Reta Normal'] = np.nan
                            df_pp['LBF_calc'] = np.nan

                            if 'boyance' not in st.session_state:
                                st.session_state.boyance = 'Não'

                            if st.session_state.boyance == 'Sim':
                                with st.expander("Boyance", expanded=True):
                                    if 'n_boyance' not in st.session_state:
                                        st.session_state.n_boyance = 1

                                    col_add_2, col_rem_2 = st.columns(2)

                                    with col_add_2:
                                        if st.button(
                                                "Adicionar Intervalo Boyance",
                                                type="primary",
                                                use_container_width=True,
                                                key="b_add_boyance"
                                        ):
                                            st.session_state.n_boyance += 1

                                    with col_rem_2:
                                        if st.button(
                                                "Remover Intervalo Boyance",
                                                type="primary",
                                                use_container_width=True,
                                                key="b_rem_boyance"
                                        ):
                                            if st.session_state.n_boyance > 1:
                                                st.session_state.n_boyance -= 1

                                    st.segmented_control(
                                        "***Pressão***",
                                        [
                                            'Base do arenito = Topo do Folhelho',
                                            'Topo do arenito = Base do Folhelho'
                                        ],
                                        selection_mode="multi",
                                        default='Base do arenito = Topo do Folhelho',
                                        key='o_boyance',
                                        width="stretch"
                                    )

                                    for i in range(st.session_state.n_boyance):
                                        with st.expander(f"### Boyance - Intervalo {i + 1}", expanded=True):
                                            st.markdown(f"### Boyance - Intervalo {i + 1}")

                                            if st.session_state.n_boyance > 1:
                                                colun1, colun2 = st.columns(2)

                                                with colun1:
                                                    if i == 0:
                                                        st.number_input(
                                                            "Profundidade inicial",
                                                            step=1.0,
                                                            format="%f",
                                                            min_value=0.0,
                                                            key=f'prof_inicial_{i}'
                                                        )
                                                    else:
                                                        st.number_input(
                                                            "Profundidade inicial",
                                                            value=st.session_state.get(f'prof_final_{i - 1}', 0.0),
                                                            disabled=True,
                                                            key=f'prof_inicial_{i}'
                                                        )

                                                with colun2:
                                                    if i == st.session_state.n_boyance - 1:
                                                        st.number_input(
                                                            "Profundidade final",
                                                            value=df_pp['Profundidade (m)'].max() + 100,
                                                            disabled=True,
                                                            key=f'prof_final_{i}'
                                                        )
                                                    else:
                                                        st.number_input(
                                                            "Profundidade final",
                                                            step=1.0,
                                                            format="%f",
                                                            min_value=0.0,
                                                            key=f'prof_final_{i}'
                                                        )

                                            if f"fpr_{i}" not in st.session_state:
                                                st.session_state[f"fpr_{i}"] = 8.5

                                            st.number_input(
                                                "Peso do Fluido Contido nos Poros das Rochas",
                                                min_value=1.,
                                                format='%1f',
                                                key=f'fpr_{i}',
                                                step=0.5,
                                                value=8.5
                                            )

                                    boyances = []

                                    for i in range(st.session_state.n_boyance):
                                        if f'fpr_{i}' in st.session_state:
                                            boyances.append({
                                                'fpr': st.session_state.get(f'fpr_{i}'),
                                                'prof_inicial': st.session_state.get(f'prof_inicial_{i}', None),
                                                'prof_final': st.session_state.get(f'prof_final_{i}', None)
                                            })

                            if 'n_trending' not in st.session_state:
                                st.session_state.n_trending = 1
                                # st.session_state.n_trending = 3

                            if 'n_lbf' not in st.session_state:
                                st.session_state.n_lbf = 1
                                # st.session_state.n_lbf = 5

                            col_add_tr, col_rem_tr, col_add_lbf, col_rem_lbf = st.columns(4)

                            with col_add_tr:
                                if st.button(
                                        "➕ Trending",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_add_trending"
                                ):
                                    st.session_state.n_trending += 1

                            with col_rem_tr:
                                if st.button(
                                        "➖ Trending",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_rem_trending"
                                ):
                                    if st.session_state.n_trending > 1:
                                        idx = st.session_state.n_trending - 1

                                        keys_to_remove = [
                                            f'trend_pp1_{idx}',
                                            f'trend_pp2_{idx}',
                                            f'trend_s1_{idx}',
                                            f'trend_s2_{idx}',
                                            f'trend_prof_ini_{idx}',
                                            f'trend_prof_fim_{idx}',
                                        ]

                                        for k in keys_to_remove:
                                            if k in st.session_state:
                                                del st.session_state[k]

                                        st.session_state.n_trending -= 1

                            with col_add_lbf:
                                if st.button(
                                        "➕ LBF",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_add_lbf"
                                ):
                                    st.session_state.n_lbf += 1

                            with col_rem_lbf:
                                if st.button(
                                        "➖ LBF",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_rem_lbf"
                                ):
                                    if st.session_state.n_lbf > 1:
                                        idx = st.session_state.n_lbf - 1

                                        keys_to_remove = [
                                            f'lbf_valor_{idx}',
                                            f'lbf_inclinacao_{idx}',
                                            f'lbf_prof_ini_{idx}',
                                            f'lbf_prof_fim_{idx}',
                                        ]

                                        for k in keys_to_remove:
                                            if k in st.session_state:
                                                del st.session_state[k]

                                        st.session_state.n_lbf -= 1

                            with st.form("p_poros", border=False):
                                if st.session_state.mgpp == 'Subcompactação':
                                    with st.expander("Informações Gerais", expanded=True):
                                        st.number_input(
                                            'Expoente de Eaton',
                                            step=1.0,
                                            format='%f',
                                            key='expoente',
                                            value=3.0
                                        )

                                        st.number_input(
                                            'Profundidade da zona normal',
                                            step=100.0,
                                            format='%f',
                                            key='anormal',
                                            value=400.0
                                        )

                                        st.number_input(
                                            'Gradiente Normal',
                                            step=1.0,
                                            format='%f',
                                            key='gn',
                                            value=8.5
                                        )

                                    st.markdown("### Trendings")

                                    for i in range(st.session_state.n_trending):
                                        with st.expander(f"### Trending {i + 1}", expanded=True):
                                            if st.session_state.n_trending > 1:
                                                colun1, colun2 = st.columns(2)

                                                with colun1:
                                                    st.number_input(
                                                        "Profundidade inicial",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'trend_prof_ini_{i}'
                                                    )

                                                with colun2:
                                                    st.number_input(
                                                        "Profundidade final",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'trend_prof_fim_{i}'
                                                    )

                                            col1, col2 = st.columns((1, 1))

                                            with col1:
                                                st.number_input(
                                                    'Profundidade 1',
                                                    step=1.0,
                                                    format='%f',
                                                    min_value=0.0,
                                                    value=400.0,
                                                    key=f'trend_pp1_{i}'
                                                )

                                                st.number_input(
                                                    'Profundidade 2',
                                                    step=1.0,
                                                    format='%f',
                                                    min_value=0.0,
                                                    value=1000.0,
                                                    key=f'trend_pp2_{i}'
                                                )

                                            with col2:
                                                st.number_input(
                                                    'Leitura 1 do Sônico',
                                                    step=1.0,
                                                    format='%f',
                                                    min_value=0.0,
                                                    value=110.0,
                                                    key=f'trend_s1_{i}'
                                                )

                                                st.number_input(
                                                    'Leitura 2 do Sônico',
                                                    step=1.0,
                                                    format='%f',
                                                    min_value=0.0,
                                                    value=87.0,
                                                    key=f'trend_s2_{i}'
                                                )

                                    st.markdown("### Linhas Base de Folhelhos")

                                    for i in range(st.session_state.n_lbf):
                                        with st.expander(f"### LBF {i + 1}", expanded=True):
                                            if st.session_state.n_lbf > 1:
                                                colun1, colun2 = st.columns(2)

                                                with colun1:
                                                    st.number_input(
                                                        "Profundidade inicial da LBF",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'lbf_prof_ini_{i}'
                                                    )

                                                with colun2:
                                                    st.number_input(
                                                        "Profundidade final da LBF",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'lbf_prof_fim_{i}'
                                                    )

                                            st.number_input(
                                                'Ponto inicial da LBF',
                                                step=10.0,
                                                format='%f',
                                                min_value=1.0,
                                                value=111.0,
                                                key=f'lbf_valor_{i}',
                                                help=(
                                                    "Linha Base de Folhelhos (LBF)\n\n"
                                                    "- Representa o comportamento esperado dos folhelhos normalmente compactados.\n"
                                                    "- Traçada no registro raio gama (GAPI) × profundidade (m)."
                                                )
                                            )

                                            st.number_input(
                                                'Inclinação da LBF',
                                                step=0.1,
                                                format='%f',
                                                value=0.0,
                                                key=f'lbf_inclinacao_{i}'
                                            )

                                    trendings = []

                                    for i in range(st.session_state.n_trending):
                                        if f'trend_pp1_{i}' in st.session_state:
                                            trendings.append({
                                                'pp1': st.session_state.get(f'trend_pp1_{i}'),
                                                'pp2': st.session_state.get(f'trend_pp2_{i}'),
                                                's1': st.session_state.get(f'trend_s1_{i}'),
                                                's2': st.session_state.get(f'trend_s2_{i}'),
                                                'prof_ini': st.session_state.get(f'trend_prof_ini_{i}', None),
                                                'prof_fim': st.session_state.get(f'trend_prof_fim_{i}', None),
                                            })

                                    prof = df_pp['Profundidade (m)']

                                    df_pp['Perfil sônico (µs/pé) Reta Normal'] = np.nan

                                    for idx, tr in enumerate(trendings):
                                        try:
                                            pp1 = tr['pp1']
                                            pp2 = tr['pp2']
                                            s1 = tr['s1']
                                            s2 = tr['s2']

                                            if (
                                                    pp1 is None or pp2 is None or
                                                    s1 is None or s2 is None or
                                                    pp1 == pp2 or
                                                    s1 <= 0 or s2 <= 0
                                            ):
                                                continue

                                            if st.session_state.onshore:
                                                m = np.log10(s2 / s1) / (pp2 - pp1)
                                                s_normal = s1 * 10 ** (m * (prof - pp1))
                                            else:
                                                m = (pp2 - pp1) / (s2 - s1)

                                                if m == 0:
                                                    continue

                                                b = -(m * s2) + pp2
                                                s_normal = (prof - b) / m

                                            mask_base = prof.notna()

                                            if not st.session_state.onshore:
                                                mask_base = mask_base & (prof > st.session_state.lda)

                                            prof_ini = tr.get('prof_ini')
                                            prof_fim = tr.get('prof_fim')

                                            if (
                                                    prof_ini is not None and
                                                    prof_fim is not None and
                                                    prof_fim > prof_ini
                                            ):
                                                mask_intervalo = (prof >= prof_ini) & (prof <= prof_fim)
                                                mask_final = mask_base & mask_intervalo
                                            else:
                                                mask_final = mask_base

                                            df_pp.loc[
                                                mask_final,
                                                'Perfil sônico (µs/pé) Reta Normal'
                                            ] = s_normal[mask_final]

                                        except Exception as e:
                                            st.warning(f"Erro ao calcular Trending {idx + 1}: {e}")

                                    if df_pp['Perfil sônico (µs/pé) Reta Normal'].isna().any() and trendings:
                                        try:
                                            tr0 = trendings[0]

                                            pp1 = tr0['pp1']
                                            pp2 = tr0['pp2']
                                            s1 = tr0['s1']
                                            s2 = tr0['s2']

                                            if (
                                                    pp1 is not None and pp2 is not None and
                                                    s1 is not None and s2 is not None and
                                                    pp1 != pp2 and
                                                    s1 > 0 and s2 > 0
                                            ):
                                                if st.session_state.onshore:
                                                    m = np.log10(s2 / s1) / (pp2 - pp1)
                                                    s_normal_padrao = s1 * 10 ** (m * (prof - pp1))
                                                else:
                                                    m = (pp2 - pp1) / (s2 - s1)

                                                    if m != 0:
                                                        b = -(m * s2) + pp2
                                                        s_normal_padrao = (prof - b) / m
                                                    else:
                                                        s_normal_padrao = np.nan

                                                df_pp['Perfil sônico (µs/pé) Reta Normal'] = (
                                                    df_pp['Perfil sônico (µs/pé) Reta Normal']
                                                    .fillna(s_normal_padrao)
                                                )

                                        except Exception as e:
                                            st.warning(f"Erro no preenchimento padrão da reta normal: {e}")

                                    lbfs = []

                                    for i in range(st.session_state.n_lbf):
                                        if f'lbf_valor_{i}' in st.session_state:
                                            lbfs.append({
                                                'lbf': st.session_state.get(f'lbf_valor_{i}'),
                                                'inclbf': st.session_state.get(f'lbf_inclinacao_{i}'),
                                                'prof_ini': st.session_state.get(f'lbf_prof_ini_{i}', None),
                                                'prof_fim': st.session_state.get(f'lbf_prof_fim_{i}', None),
                                            })

                                    df_pp['LBF_calc'] = np.nan

                                    for idx, lbf in enumerate(lbfs):
                                        try:
                                            prof_ref = (
                                                lbf['prof_ini']
                                                if lbf['prof_ini'] is not None
                                                else prof.min()
                                            )

                                            lbf_line = lbf['inclbf'] * (prof - prof_ref) + lbf['lbf']

                                            if st.session_state.onshore:
                                                mask_base = prof.notna()
                                            else:
                                                mask_base = prof > st.session_state.lda

                                            if lbf['prof_ini'] is not None and lbf['prof_fim'] is not None:
                                                mask_intervalo = (prof >= lbf['prof_ini']) & (prof <= lbf['prof_fim'])
                                                mask_final = mask_base & mask_intervalo
                                            else:
                                                mask_final = mask_base

                                            df_pp.loc[mask_final, 'LBF_calc'] = lbf_line[mask_final]

                                        except Exception as e:
                                            st.warning(f"Erro ao calcular LBF {idx + 1}: {e}")

                                    if df_pp['LBF_calc'].isna().any() and lbfs:
                                        try:
                                            primeira_lbf = lbfs[0]

                                            prof_ref = (
                                                primeira_lbf['prof_ini']
                                                if primeira_lbf['prof_ini'] is not None
                                                else prof.min()
                                            )

                                            lbf_padrao = (
                                                    primeira_lbf['inclbf'] * (prof - prof_ref)
                                                    + primeira_lbf['lbf']
                                            )

                                            df_pp['LBF_calc'] = df_pp['LBF_calc'].fillna(lbf_padrao)

                                        except Exception as e:
                                            st.warning(f"Erro no preenchimento padrão da LBF: {e}")

                                    if st.session_state.onshore:
                                        df_pp['Gradiente de Sobrecarga (lb/gal)'] = st.session_state.ext_df[
                                            'Gradiente de Sobrecarga (lb/gal)'
                                        ]
                                    else:
                                        df_pp['Gradiente de Sobrecarga (lb/gal)'] = df[
                                            'Gradiente de Sobrecarga (lb/gal)'
                                        ]

                                    gp = []
                                    prof_min = df["Profundidade"].min()
                                    base_grad = st.session_state.gn

                                    if not st.session_state.suav_s:
                                        s = df_pp['Perfil sônico (µs/pé)']
                                    else:
                                        s = df_pp['Perfil sônico suavizado (µs/pé)']

                                    if st.session_state.onshore:
                                        normal(df_pp)

                                        col_pp_normal = "Gradiente de Pressão de Poros Normal (lb/gal)"

                                        df_gfs_aux = st.session_state.df_gfs.copy()

                                        df_gfs_aux["Profundidade (m)"] = pd.to_numeric(
                                            df_gfs_aux["Profundidade (m)"],
                                            errors="coerce"
                                        )

                                        df_gfs_aux["Gradiente de Pressão de Poros (lb/gal)"] = pd.to_numeric(
                                            df_gfs_aux["Gradiente de Pressão de Poros (lb/gal)"],
                                            errors="coerce"
                                        )

                                        df_gfs_aux = df_gfs_aux.dropna(
                                            subset=[
                                                "Profundidade (m)",
                                                "Gradiente de Pressão de Poros (lb/gal)"
                                            ]
                                        )

                                        df_gfs_aux = (
                                            df_gfs_aux
                                            .sort_values("Profundidade (m)")
                                            .drop_duplicates(subset=["Profundidade (m)"])
                                        )

                                        if not df_gfs_aux.empty:
                                            df_pp[col_pp_normal] = np.interp(
                                                df_pp["Profundidade (m)"].astype(float),
                                                df_gfs_aux["Profundidade (m)"].astype(float),
                                                df_gfs_aux["Gradiente de Pressão de Poros (lb/gal)"].astype(float),
                                                left=np.nan,
                                                right=np.nan
                                            )
                                        else:
                                            df_pp[col_pp_normal] = np.nan

                                    else:
                                        col_pp_normal = "Gradiente de Pressão de Poros Normal (lb/gal)"
                                        df_pp[col_pp_normal] = np.nan

                                    for i in range(len(df_pp)):
                                        perfil_sonico = s.iloc[i]

                                        if pd.isna(perfil_sonico):
                                            perfil_sonico = df_pp['Perfil sônico (µs/pé) Reta Normal'].iloc[i]

                                        perfil = perfil_sonico
                                        reta_normal = df_pp['Perfil sônico (µs/pé) Reta Normal'].iloc[i]

                                        if pd.isna(perfil) or pd.isna(reta_normal) or reta_normal == 0:
                                            if gp:
                                                gp.append(gp[-1])
                                            else:
                                                gp.append(base_grad)
                                            continue

                                        if st.session_state.onshore:
                                            x = (
                                                    df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[i]
                                                    - (
                                                            (
                                                                    df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[i]
                                                                    - base_grad
                                                            )
                                                            * ((perfil / reta_normal) ** (-st.session_state.expoente))
                                                    )
                                            )

                                            profundidade_atual = df_pp['Profundidade (m)'].iloc[i]

                                            if profundidade_atual < prof_min:
                                                if profundidade_atual < st.session_state.anormal:
                                                    gp.append(np.nan)

                                                else:
                                                    if x < st.session_state.gn:
                                                        gp.append(base_grad)
                                                    else:
                                                        gp.append(x)

                                            else:
                                                if "s_gr" not in st.session_state:
                                                    curva = df_pp['Perfil Raio Gama']
                                                else:
                                                    if not st.session_state.s_gr:
                                                        curva = df_pp['Perfil Raio Gama']
                                                    else:
                                                        curva = df_pp['Raio Gama Suavizado']

                                                if curva.iloc[i] >= df_pp['LBF_calc'].iloc[i]:
                                                    if profundidade_atual < st.session_state.anormal:
                                                        gp.append(np.nan)

                                                    else:
                                                        if x < st.session_state.gn:
                                                            gp.append(base_grad)
                                                        else:
                                                            gp.append(x)
                                                else:
                                                    if gp:
                                                        gp.append(gp[-1])
                                                    else:
                                                        gp.append(base_grad)

                                        else:
                                            x = (
                                                    df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[i]
                                                    - (
                                                            (
                                                                    df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[i]
                                                                    - st.session_state.gn
                                                            )
                                                            * ((perfil / reta_normal) ** (-st.session_state.expoente))
                                                    )
                                            )

                                            if df_pp['Profundidade (m)'].iloc[i] <= st.session_state.lda:
                                                gp.append(None)
                                            elif (
                                                    df_pp['Profundidade (m)'].iloc[i] < st.session_state.anormal
                                                    or x < st.session_state.gn
                                            ):
                                                gp.append(st.session_state.gn)
                                            else:
                                                gp.append(x)

                                    df_pp['Gradiente de Pressão de Poros (lb/gal)'] = pd.to_numeric(
                                        gp,
                                        errors="coerce"
                                    )

                                    if st.session_state.onshore:
                                        col_pp = "Gradiente de Pressão de Poros (lb/gal)"
                                        col_pp_normal = "Gradiente de Pressão de Poros Normal (lb/gal)"

                                        prof_fim_normal = float(
                                            st.session_state.df_gfs["Profundidade (m)"].max()
                                        )

                                        prof_anormal = float(st.session_state.anormal)
                                        gn = float(st.session_state.gn)

                                        mask_normal = df_pp["Profundidade (m)"] <= prof_fim_normal

                                        df_pp.loc[mask_normal, col_pp] = (
                                            df_pp.loc[mask_normal, col_pp_normal]
                                            .combine_first(df_pp.loc[mask_normal, col_pp])
                                        )

                                        mask_ate_anormal = (
                                                (df_pp["Profundidade (m)"] > prof_fim_normal)
                                                & (df_pp["Profundidade (m)"] < prof_anormal)
                                        )

                                        df_pp.loc[mask_ate_anormal, col_pp] = (
                                            df_pp.loc[mask_ate_anormal, col_pp]
                                            .fillna(gn)
                                        )

                                    df_pp['Gradiente de Pressão de Poros Médio (lb/gal)'] = (
                                        df_pp['Gradiente de Pressão de Poros (lb/gal)']
                                        .rolling(window=20, min_periods=1)
                                        .mean()
                                    )

                                    for i in range(1, len(df_pp)):
                                        if df_pp.loc[i, 'Profundidade (m)'] >= st.session_state.anormal:
                                            anterior = df_pp.loc[
                                                i - 1,
                                                'Gradiente de Pressão de Poros Médio (lb/gal)'
                                            ]

                                            atual = df_pp.loc[
                                                i,
                                                'Gradiente de Pressão de Poros Médio (lb/gal)'
                                            ]

                                            if atual > anterior + st.session_state.fpp:
                                                df_pp.loc[
                                                    i,
                                                    'Gradiente de Pressão de Poros Médio (lb/gal)'
                                                ] = anterior + st.session_state.fpp

                                    if "spp" not in st.session_state:
                                        st.session_state.spp = True

                                    try:
                                        if st.session_state.spp:
                                            df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)'] = suavizar_2(
                                                df_pp['Profundidade (m)'],
                                                df_pp['Gradiente de Pressão de Poros Médio (lb/gal)'],
                                                df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                                            )
                                    except Exception as e:
                                        st.warning(f"Erro ao suavizar pressão de poros: {e}")

                                    df_pp.insert(
                                        loc=9,
                                        column='Pressão de Poros (psi)',
                                        value=(
                                                0.1704
                                                * df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                                                * df_pp['Profundidade (m)']
                                        )
                                    )

                                    df_pp.insert(
                                        loc=10,
                                        column='Pressão de Poros Suavizado (psi)',
                                        value=suavizar_2(
                                            df_pp['Profundidade (m)'],
                                            df_pp['Pressão de Poros (psi)'],
                                            df_pp['Pressão de Poros (psi)']
                                        )
                                    )

                                    if st.session_state.boyance == 'Sim':
                                        df_pp["FPR_efetivo"] = np.nan

                                        if st.session_state.n_boyance == 1:
                                            df_pp["FPR_efetivo"] = st.session_state.get("fpr_0")
                                        else:
                                            for i in range(st.session_state.n_boyance):
                                                fpr = st.session_state.get(f"fpr_{i}")
                                                prof_ini = st.session_state.get(f"prof_inicial_{i}")
                                                prof_fim = st.session_state.get(f"prof_final_{i}")

                                                if fpr is None:
                                                    continue

                                                if prof_ini is None or prof_fim is None:
                                                    continue

                                                mask = (
                                                        (df_pp["Profundidade (m)"] >= prof_ini) &
                                                        (df_pp["Profundidade (m)"] <= prof_fim)
                                                )

                                                df_pp.loc[mask, "FPR_efetivo"] = fpr

                                        df_pp["FPR_efetivo"] = (
                                            df_pp["FPR_efetivo"]
                                            .ffill()
                                            .fillna(st.session_state.get("fpr_0"))
                                        )

                                        incremento = (
                                                0.1704
                                                * df_pp["FPR_efetivo"]
                                                * (
                                                        df_pp["Profundidade (m)"]
                                                        - df_pp["Profundidade (m)"].shift(1)
                                                )
                                        )

                                        if not st.session_state.s_gr:
                                            x = df_pp["Perfil Raio Gama"]
                                        else:
                                            x = df_pp["Raio Gama Suavizado"]

                                        df_pp.insert(
                                            loc=12,
                                            column='Formação',
                                            value=np.where(
                                                x < df_pp["LBF_calc"],
                                                "Formação Permeável",
                                                "Formação Impermeável"
                                            )
                                        )

                                        topo_permeavel = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(1) != "Formação Permeável")
                                        )

                                        df_pp.insert(
                                            loc=13,
                                            column='Pressão Boyance (TA = BF)',
                                            value=np.nan
                                        )

                                        if not st.session_state.spp:
                                            y = df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                                        else:
                                            y = df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)']

                                        df_pp.loc[topo_permeavel, 'Pressão Boyance (TA = BF)'] = (
                                                y.shift(1)
                                                * 0.1704
                                                * df_pp["Profundidade (m)"]
                                        )

                                        id_camada = topo_permeavel.cumsum()
                                        mask_perm = df_pp["Formação"] == "Formação Permeável"

                                        serie_ta_bf = (
                                            df_pp.loc[mask_perm]
                                            .groupby(id_camada[mask_perm], group_keys=False)
                                            .apply(
                                                lambda g: (
                                                        g['Pressão Boyance (TA = BF)'].iloc[0]
                                                        + incremento.loc[g.index].cumsum()
                                                )
                                            )
                                        )

                                        serie_ta_bf = serie_ta_bf.sort_index()
                                        df_pp.loc[serie_ta_bf.index, 'Pressão Boyance (TA = BF)'] = serie_ta_bf

                                        boyance_calc = np.where(
                                            df_pp["Formação"] == "Formação Impermeável",
                                            y,
                                            df_pp["Pressão Boyance (TA = BF)"]
                                            / (0.1704 * df_pp["Profundidade (m)"])
                                        )

                                        boyance_calc = pd.Series(boyance_calc, index=df_pp.index)
                                        boyance_calc = boyance_calc.fillna(y)

                                        df_pp.insert(
                                            loc=14,
                                            column='Boyance (lb/gal) (TA = BF)',
                                            value=boyance_calc
                                        )

                                        df_pp.insert(
                                            loc=15,
                                            column='Pressão Boyance (BA = TF)',
                                            value=np.nan
                                        )

                                        base_permeavel = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(-1) != "Formação Permeável")
                                        )

                                        idx = df_pp.index[base_permeavel]

                                        df_pp.loc[idx, 'Pressão Boyance (BA = TF)'] = np.where(
                                            df_pp.loc[idx, "Formação"].shift(-1) == "Formação Impermeável",
                                            df_pp.loc[idx, 'Pressão de Poros (psi)'].shift(-1),
                                            df_pp.loc[idx, 'Pressão de Poros (psi)']
                                        )

                                        id_camada = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(1) != "Formação Permeável")
                                        ).cumsum()

                                        mask_perm = df_pp["Formação"] == "Formação Permeável"

                                        serie_ba_tf = (
                                            df_pp.loc[mask_perm]
                                            .groupby(id_camada[mask_perm], group_keys=False)
                                            .apply(
                                                lambda g: (
                                                        g['Pressão Boyance (BA = TF)'].iloc[-1]
                                                        - incremento.loc[g.index][::-1].cumsum()[::-1]
                                                )
                                            )
                                        )

                                        serie_ba_tf = serie_ba_tf.sort_index()
                                        df_pp.loc[serie_ba_tf.index, 'Pressão Boyance (BA = TF)'] = serie_ba_tf

                                        df_pp = df_pp.sort_values("Profundidade (m)").reset_index(drop=True)

                                        impermeavel = df_pp["Formação"] == "Formação Impermeável"
                                        impermeavel_acima = impermeavel.shift(fill_value=False).cumsum() > 0

                                        df_pp.insert(
                                            loc=16,
                                            column='Boyance (lb/gal) (BA = TF)',
                                            value=np.where(
                                                (~impermeavel) & (impermeavel_acima),
                                                df_pp["Pressão Boyance (BA = TF)"]
                                                / (0.1704 * df_pp["Profundidade (m)"]),
                                                y
                                            )
                                        )

                                else:
                                    st.warning('Funcionalidade ainda não disponível', icon="⚠️")

                                st.form_submit_button(
                                    "Calcular Gradiente de Pessão de Poros",
                                    use_container_width=True,
                                    type='primary'
                                )

                    st.session_state.df_pp_lito = df_pp.copy()

                    # GRÁFICO DO GRADIENTE DE PRESSÃO DE POROS
                    with coluna3:
                        with st.container(border=True):
                            if "idg" not in st.session_state:
                                st.session_state.idg = 'Não'

                            st.session_state.fig_pp = plt.figure(figsize=(8, 10))

                            if st.session_state.idg == 'Sim':
                                # === COM coluna de idade ===
                                gs = gridspec.GridSpec(
                                    1, 4,
                                    width_ratios=[0.1, 0.2, 0.21, 1],
                                    wspace=0
                                )

                                ax_idade = st.session_state.fig_pp.add_subplot(gs[0])
                                ax1 = st.session_state.fig_pp.add_subplot(gs[1], sharey=ax_idade)

                                ax_gap = st.session_state.fig_pp.add_subplot(gs[2])
                                ax_gap.axis('off')

                                ax = st.session_state.fig_pp.add_subplot(gs[3], sharey=ax_idade)

                                idade_formacao(ax_idade, st.session_state.df_idade,
                                               df_pp['Profundidade (m)'].max() + 100)

                                idade_formacao(
                                    ax_idade,
                                    st.session_state.df_idade,
                                    df_pp['Profundidade (m)'].max() + 100
                                )

                                # remove ticks e labels da coluna de idade
                                ax_idade.tick_params(
                                    axis='y',
                                    which='both',
                                    left=False,
                                    right=False,
                                    labelleft=False,
                                    labelright=False
                                )

                                ax_idade.set_ylabel("")

                                # evita duplicar rótulos de profundidade
                                plt.setp(ax1.get_yticklabels(), visible=False)
                                plt.setp(ax.get_yticklabels(), visible=False)

                            else:
                                # === SEM coluna de idade ===
                                gs = gridspec.GridSpec(
                                    1, 3,
                                    width_ratios=[0.2, 0.21, 1],
                                    wspace=0
                                )

                                ax1 = st.session_state.fig_pp.add_subplot(gs[0])
                                ax_gap = st.session_state.fig_pp.add_subplot(gs[1])
                                ax_gap.axis('off')

                                ax = st.session_state.fig_pp.add_subplot(gs[2], sharey=ax1)

                                plt.setp(ax.get_yticklabels(), visible=False)

                            x = len(df_pp['Profundidade (m)']) - len(df['Profundidade'])
                            st.write("")

                            def reset_config():
                                if st.session_state.ogp == "Gradiente (lb/gal)":
                                    st.session_state.x_min_pp = 7
                                    st.session_state.x_max_pp = 23
                                    st.session_state.x_step = 1
                                else:
                                    st.session_state.x_min_pp = 0
                                    st.session_state.x_max_pp = int(
                                        st.session_state.ext_df['Pressão de Sobrecarga (psi)'].max()) + 200
                                    st.session_state.x_step = 500
                                st.session_state.y_min_pp = 0
                                st.session_state.y_max_pp = int(df_pp['Profundidade (m)'].max()) + 100

                                st.session_state.y_step = 200

                            with st.expander("Configurações do Gráfico", expanded=False):
                                st.segmented_control("***Opção de Gráfico***",
                                                     ['Gradiente (lb/gal)', 'Pressão (psi)'],
                                                     selection_mode="single",
                                                     default='Gradiente (lb/gal)', key='ogp',
                                                     width="stretch")
                                with st.expander('Testes de Formação',expanded=False):
                                    st.markdown("##### Pontos de RFT")

                                    if "rft_pontos_pp" not in st.session_state:
                                        st.session_state.rft_pontos_pp = pd.DataFrame({
                                            "Profundidade (m)": [],
                                            "Teste RFT (lb/gal)": []
                                        })

                                    rft_pontos_editado = st.data_editor(
                                        st.session_state.rft_pontos_pp,
                                        num_rows="dynamic",
                                        use_container_width=True,
                                        hide_index=True,
                                        key="editor_rft_pontos_pp",
                                        column_config={
                                            "Profundidade (m)": st.column_config.NumberColumn(
                                                "Profundidade (m)",
                                                min_value=0.0,
                                                format="%.2f"
                                            ),
                                            "Teste RFT (lb/gal)": st.column_config.NumberColumn(
                                                "Teste RFT (lb/gal)",
                                                min_value=0.0,
                                                format="%.4f"
                                            ),
                                        }
                                    )

                                    col_rft1, col_rft2 = st.columns(2)

                                    with col_rft1:
                                        if st.button(
                                                "Atualizar pontos RFT",
                                                use_container_width=True,
                                                type="primary",
                                                key="btn_atualizar_rft_pp"
                                        ):
                                            st.session_state.rft_pontos_pp = rft_pontos_editado.copy()

                                    with col_rft2:
                                        if st.button(
                                                "Limpar pontos RFT",
                                                use_container_width=True,
                                                type="primary",
                                                key="btn_limpar_rft_pp"
                                        ):
                                            st.session_state.rft_pontos_pp = pd.DataFrame({
                                                "Profundidade (m)": [],
                                                "Teste RFT (lb/gal)": []
                                            })
                                            st.rerun()
                                colu1, colu2 = st.columns(2)
                                with colu1:
                                    st.checkbox('Suavizar Pressão de Poros', key="spp", value=True)
                                    st.checkbox('Suavizar Sônico', key="suav_s", value=False)
                                with colu2:
                                    st.checkbox('Sobrecarga', key="grafpp", value=True)
                                    st.checkbox('Suavizar Raio Gama', key="s_gr", value=False)
                                    st.session_state.ss = True

                                if st.session_state.option == "Previsão de Geopressões":
                                    i = 0
                                    d = True
                                else:
                                    i = 1
                                    d = False
                                st.selectbox(
                                    "Coluna litológica dos gráficos",
                                    ["Permeável / Não permeável", "Litologia do Excel"],
                                    key="tipo_coluna_litologica_graficos",
                                    index=0
                                )
                                st.selectbox("Visualizar peso do fluido planejado", ['Não', 'Sim'], key='fpl', index=i)
                                st.selectbox("Visualizar peso do fluido executado", ['Não', 'Sim'], key='fex', index=i, disabled=d)
                                st.number_input('Alfa', step=1., format='%f',
                                                key='alfa_pp',
                                                value=4., min_value=1., max_value=20.)
                                st.selectbox("Boyance Ativado", ['Não', 'Sim'], key='boyance')
                                st.number_input('Filtro da Pressão de Poros', step=0.01, format='%f',
                                                key='fpp',
                                                value=0.01, min_value=0.001, max_value=1.0)
                                st.number_input('Nível de suavização', step=0.1, format='%f', key='frac', value=0.1)
                                st.number_input('Gaussiano', step=1., format='%f', key='gauss', value=50.)
                                st.number_input("Eixo X - mínimo", value=7, step=1, key="x_min_pp")
                                st.number_input("Eixo X - máximo", value=23, step=1, key="x_max_pp")
                                st.number_input("Passo do eixo X", value=1, step=1, key="x_step")

                                st.number_input("Eixo Y - mínimo", value=0,
                                                step=100, key="y_min_pp")
                                st.number_input("Eixo Y - máximo",
                                                value=int(df_pp['Profundidade (m)'].max()) + 100,
                                                step=100, key="y_max_pp")
                                st.number_input("Passo do eixo Y", value=200, step=50, key="y_step")
                                # Botão de reset com callback
                                st.button("Resetar Eixos - Gradiente de Pressão de Poros",
                                          on_click=reset_config,
                                          type="primary", use_container_width=True)
                            try:
                                if st.session_state.ogp == "Gradiente (lb/gal)":
                                    st.session_state.oep = df_pp[
                                        'Gradiente de Pressão de Poros Médio (lb/gal)']
                                    st.session_state.oepl = 'G. de Pressão de Poros'
                                else:
                                    st.session_state.oep = df_pp['Pressão de Poros (psi)']
                                    st.session_state.oepl = 'P. de Poros'
                            except Exception as e:
                                pass

                            # idx = df_pp.index[df_pp["Profundidade (m)"] > st.session_state.es][0]
                            if not st.session_state.spp:
                                try:
                                    ax.plot(st.session_state.oep, df_pp['Profundidade (m)'], color='orange',
                                            linestyle='-',
                                            linewidth=2, label=st.session_state.oepl)

                                except Exception as e:
                                    pass

                            else:
                                if st.session_state.ogp == "Gradiente (lb/gal)":
                                    ax.plot(df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)'],
                                            df_pp['Profundidade (m)'], color='blue', linestyle='-',
                                            linewidth=2,
                                            label=st.session_state.oepl)
                                else:
                                    ax.plot(df_pp['Pressão de Poros Suavizado (psi)'],
                                            df_pp['Profundidade (m)'],
                                            color='blue',
                                            linestyle='-',
                                            linewidth=2, label=st.session_state.oepl)

                            if st.session_state.boyance == 'Sim':
                                try:
                                    selecoes = st.session_state.o_boyance

                                    if 'Topo do arenito = Base do Folhelho' in selecoes:
                                        ax.plot(
                                            df_pp['Boyance (lb/gal) (TA = BF)'],
                                            df_pp['Profundidade (m)'],
                                            color='red',
                                            linestyle='-',
                                            linewidth=2,
                                            label='Boyance (lb/gal) (TA = BF)'
                                        )

                                    if 'Base do arenito = Topo do Folhelho' in selecoes:
                                        ax.plot(
                                            df_pp['Boyance (lb/gal) (BA = TF)'],
                                            df_pp['Profundidade (m)'],
                                            color='green',
                                            linestyle='-',
                                            linewidth=2,
                                            label='Boyance (lb/gal) (BA = TF)'
                                        )
                                except Exception as e:
                                    st.error(f"Erro: {e}")

                            if st.session_state.grafpp:
                                if st.session_state.ogp == "Gradiente (lb/gal)":
                                    ax.plot(df_pp['Gradiente de Sobrecarga (lb/gal)'][1:],
                                            df_pp['Profundidade (m)'][1:], color='black', linestyle='-',
                                            linewidth=2,
                                            label=st.session_state.oesl)
                                else:
                                    ax.plot(st.session_state.ext_df['Pressão de Sobrecarga (psi)'][1:],
                                            st.session_state.ext_df[
                                                'Profundidade em relação a mesa rotativa (m)'][1:],
                                            color='black', linestyle='-', linewidth=2,
                                            label=st.session_state.oesl)

                            if "df_mud" in st.session_state and isinstance(st.session_state["df_mud"], pd.DataFrame):
                                df_mud = st.session_state["df_mud"].copy()

                                mostrar_planejado = st.session_state.get("fpl", "Não") == "Sim"
                                mostrar_executado = st.session_state.get("fex", "Não") == "Sim"

                                # Planejado
                                if mostrar_planejado and df_mud["Peso do Fluido Planejado (lb/gal)"].notna().any():
                                    ax.plot(
                                        df_mud["Peso do Fluido Planejado (lb/gal)"],
                                        df_mud["Profundidade (m)"],
                                        linestyle="-",
                                        color="green",
                                        linewidth=2,
                                        label="Peso do Fluido (Planejado)",
                                        zorder=5
                                    )

                                # Executado
                                if mostrar_executado and df_mud["Peso do Fluido Executado (lb/gal)"].notna().any():
                                    ax.plot(
                                        df_mud["Peso do Fluido Executado (lb/gal)"],
                                        df_mud["Profundidade (m)"],
                                        linestyle="-",
                                        color="mediumvioletred",
                                        linewidth=2,
                                        label="Peso do Fluido (Executado)",
                                        zorder=5
                                    )

                            if (
                                    "rft_pontos_pp" in st.session_state
                                    and isinstance(st.session_state.rft_pontos_pp, pd.DataFrame)
                                    and not st.session_state.rft_pontos_pp.empty
                            ):
                                df_rft_plot = st.session_state.rft_pontos_pp.copy()

                                df_rft_plot["Profundidade (m)"] = pd.to_numeric(
                                    df_rft_plot["Profundidade (m)"],
                                    errors="coerce"
                                )

                                df_rft_plot["Teste RFT (lb/gal)"] = pd.to_numeric(
                                    df_rft_plot["Teste RFT (lb/gal)"],
                                    errors="coerce"
                                )

                                df_rft_plot = df_rft_plot.dropna(
                                    subset=["Profundidade (m)", "Teste RFT (lb/gal)"]
                                )

                                if not df_rft_plot.empty:
                                    if st.session_state.ogp == "Gradiente (lb/gal)":
                                        ax.scatter(
                                            df_rft_plot["Teste RFT (lb/gal)"],
                                            df_rft_plot["Profundidade (m)"],
                                            color="limegreen",
                                            edgecolors="black",
                                            marker="o",
                                            s=70,
                                            label="Teste RFT",
                                            zorder=10
                                        )
                                    else:
                                        ax.scatter(
                                            df_rft_plot["Teste RFT (lb/gal)"] * 0.1704 * df_rft_plot[
                                                "Profundidade (m)"],
                                            df_rft_plot["Profundidade (m)"],
                                            color="limegreen",
                                            edgecolors="black",
                                            marker="o",
                                            s=70,
                                            label="Teste RFT",
                                            zorder=10
                                        )

                            tipo_coluna_lito_pp = st.session_state.get(
                                "tipo_coluna_lito_pp",
                                "Permeável / Não permeável"
                            )

                            lito(
                                ax1,
                                df_pp,
                                profundidades,
                                litologias,
                                st.session_state.y_max_pp
                            )

                            # Configurações do gráfico
                            if st.session_state.ogp == "Gradiente (lb/gal)":
                                ax.set_title('Gradiente de Pressão de Poros (lb/gal)', fontsize=14,
                                             fontweight='bold')
                                ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                            else:
                                ax.set_title('Pressão de Poros (psi)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Pressão (psi)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                            ax.invert_yaxis()
                            ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                            ax.set_yticks(range(st.session_state.y_min_pp, st.session_state.y_max_pp,
                                                st.session_state.y_step))
                            ax.set_ylim(st.session_state.y_max_pp, st.session_state.y_min_pp)
                            ax.set_xticks(range(st.session_state.x_min_pp, st.session_state.x_max_pp,
                                                st.session_state.x_step))
                            ax.set_xlim(st.session_state.x_min_pp, st.session_state.x_max_pp)
                            ax.grid(True, linestyle='--', alpha=0.5)
                            ax.legend(
                                loc='upper right',
                                fontsize=8,
                                frameon=True,
                                shadow=True,
                                fancybox=True,
                                framealpha=1,
                                facecolor='white',
                                edgecolor='gray'
                            )
                            add_watermark(
                                ax,
                                logo_path="logo2.png",
                                xy=(0.50, 0.5),
                                zoom=0.2,
                                alpha=0.2,
                                zorder=0
                            )

                            # Exibe o gráfico no Streamlit
                            st.pyplot(st.session_state.fig_pp)

                    # TRENDING E LBF
                    with coluna2:
                        with st.container(border=True):
                            st.segmented_control("Gráficos", ['LBF', 'Trending'], selection_mode="single",
                                                 default='LBF',
                                                 key='graf', width="stretch")

                            TRENDING_COLORS = [
                                "#0072B2",  # azul forte
                                "#009E73",  # verde-azulado
                                "#56B4E9",  # azul claro
                                "#00BFC4",  # ciano
                                "#1F78B4",  # azul médio
                            ]

                            if st.session_state.graf == 'Trending':
                                fig = plt.figure(figsize=(8, 10))

                                if st.session_state.idg == 'Sim':
                                    # ===== COM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 4,
                                        width_ratios=[0.1, 0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax_idade = fig.add_subplot(gs[0])
                                    ax1 = fig.add_subplot(gs[1], sharey=ax_idade)

                                    ax_gap = fig.add_subplot(gs[2])
                                    ax_gap.axis('off')

                                    ax = fig.add_subplot(gs[3], sharey=ax_idade)

                                    idade_formacao(ax_idade, st.session_state.df_idade, st.session_state.y_max_pp)

                                    # remove ticks e labels da coluna de idade
                                    ax_idade.tick_params(
                                        axis='y',
                                        which='both',
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                        labelright=False
                                    )

                                    ax_idade.set_ylabel("")

                                    # Evita duplicar rótulos de profundidade
                                    plt.setp(ax1.get_yticklabels(), visible=False)
                                    plt.setp(ax.get_yticklabels(), visible=False)

                                else:
                                    # ===== SEM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 3,
                                        width_ratios=[0.18, 0.21, 1],
                                        wspace=0
                                    )

                                    ax1 = fig.add_subplot(gs[0])
                                    ax_gap = fig.add_subplot(gs[1])
                                    ax_gap.axis('off')

                                    ax = fig.add_subplot(gs[2], sharey=ax1)

                                    plt.setp(ax.get_yticklabels(), visible=False)

                                # salva a figura no session_state
                                st.session_state.fig1 = fig

                                lito(
                                    ax1,
                                    df_pp,
                                    profundidades,
                                    litologias,
                                    st.session_state.y_max_pp
                                )

                                # Perfil sônico (vermelho)
                                ax.semilogx(
                                    df_pp['Perfil sônico (µs/pé)'],
                                    df_pp['Profundidade (m)'],
                                    color='red',
                                    linewidth=2,
                                    label="Sônico"
                                )

                                if st.session_state.suav_s:
                                    ax.semilogx(df_pp['Perfil sônico suavizado (µs/pé)'],
                                                df_pp['Profundidade (m)'],
                                                color='blue', linestyle='-', linewidth=2,
                                                label="Sônico Suavizado")

                                if not st.session_state.s_gr:
                                    mask = df_pp['Perfil Raio Gama'] >= df_pp['LBF_calc']
                                    df_rg = df_pp[mask]
                                    ax.semilogx(df_rg['Perfil sônico (µs/pé)'],
                                                df_rg['Profundidade (m)'],
                                                marker='o', linestyle='None',
                                                color='cyan', markersize=1,
                                                label="Sônico ≥ LBF")
                                else:
                                    mask = df_pp['Raio Gama Suavizado'] >= df_pp['LBF_calc']
                                    df_rg = df_pp[mask]
                                    ax.semilogx(df_rg['Perfil sônico (µs/pé)'],
                                                df_rg['Profundidade (m)'],
                                                marker='o', linestyle='None',
                                                color='cyan', markersize=1,
                                                label="Sônico ≥ LBF")

                                # Loop em todos os Trendings
                                for idx, tr in enumerate(trendings):
                                    try:
                                        color = TRENDING_COLORS[idx % len(TRENDING_COLORS)]

                                        m = (np.log10(tr['s2'] / tr['s1'])) / (tr['pp2'] - tr['pp1'])
                                        prof = df_pp['Profundidade (m)']
                                        s_normal = tr['s1'] * 10 ** (m * (prof - tr['pp1']))

                                        if st.session_state.onshore:
                                            prof_ini_df = float(df["Profundidade"].iloc[0])
                                            mask_base = prof >= prof_ini_df
                                        else:
                                            mask_base = prof > st.session_state.lda

                                        if tr['prof_ini'] is not None and tr['prof_fim'] is not None:
                                            mask_tr = (prof >= tr['prof_ini']) & (prof <= tr['prof_fim'])
                                            mask_final = mask_base & mask_tr
                                        else:
                                            mask_final = mask_base

                                        ax.semilogx(
                                            s_normal[mask_final],
                                            prof[mask_final],
                                            linestyle='--',
                                            linewidth=3,
                                            color=color,
                                            label=f'Trending {idx + 1}'
                                        )

                                    except Exception:
                                        pass

                                ax.set_title('Sônico x Profundidade (m)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Perfil sônico (µs/pé)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                # Ticks do eixo X
                                xticks = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                                          200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100]
                                ax.set_xticks(xticks)
                                from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter

                                # Major ticks → apenas potências de 10
                                ax.xaxis.set_major_locator(LogLocator(base=10.0))
                                ax.xaxis.set_major_formatter(ScalarFormatter())

                                # Minor ticks → subdivisões (20–90, 200–900)
                                ax.xaxis.set_minor_locator(
                                    LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1)
                                )
                                ax.xaxis.set_minor_formatter(NullFormatter())  # sem números nos minors

                                # Grid
                                ax.grid(True, which='major', linestyle='--', alpha=0.6)
                                ax.grid(True, which='minor', linestyle=':', alpha=0.4)

                                # Limites do eixo Y
                                if st.session_state.onshore:
                                    x = len(df_pp) - len(df)
                                    if 0 <= x < len(df_pp):
                                        min_depth = df_pp['Profundidade (m)'].iloc[x] - 50
                                    else:
                                        min_depth = df_pp['Profundidade (m)'].iloc[0] - 50
                                else:
                                    if len(df_pp) > 2:
                                        min_depth = df_pp['Profundidade (m)'].iloc[2] - 50
                                    else:
                                        min_depth = df_pp['Profundidade (m)'].iloc[0] - 50

                                ax.invert_yaxis()
                                ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                ax.set_yticks(range(st.session_state.y_min_pp, st.session_state.y_max_pp,
                                                    st.session_state.y_step))
                                ax.set_ylim(st.session_state.y_max_pp, st.session_state.y_min_pp)
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.legend(
                                    loc='upper right',
                                    fontsize=8,
                                    frameon=True,
                                    shadow=True,
                                    fancybox=True,
                                    framealpha=1,
                                    facecolor='white',
                                    edgecolor='gray'
                                )
                                add_watermark(
                                    ax,
                                    logo_path="logo2.png",
                                    xy=(0.50, 0.5),
                                    zoom=0.2,
                                    alpha=0.2,
                                    zorder=0
                                )

                                plt.subplots_adjust(wspace=0.3)
                                st.pyplot(st.session_state.fig1)

                            else:
                                # Figura e eixos
                                fig = plt.figure(figsize=(8, 10))

                                if st.session_state.idg == 'Sim':
                                    # ===== COM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 4,
                                        width_ratios=[0.1, 0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax_idade = fig.add_subplot(gs[0])
                                    ax1 = fig.add_subplot(gs[1], sharey=ax_idade)

                                    ax_gap = fig.add_subplot(gs[2])
                                    ax_gap.axis('off')

                                    ax = fig.add_subplot(gs[3], sharey=ax_idade)

                                    idade_formacao(ax_idade, st.session_state.df_idade, st.session_state.y_max_pp)

                                    # remove ticks e labels da coluna de idade
                                    ax_idade.tick_params(
                                        axis='y',
                                        which='both',
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                        labelright=False
                                    )

                                    ax_idade.set_ylabel("")

                                    plt.setp(ax1.get_yticklabels(), visible=False)
                                    plt.setp(ax.get_yticklabels(), visible=False)

                                else:
                                    # ===== SEM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 3,
                                        width_ratios=[0.18, 0.21, 1],
                                        wspace=0
                                    )

                                    ax1 = fig.add_subplot(gs[0])
                                    ax_gap = fig.add_subplot(gs[1])
                                    ax_gap.axis('off')

                                    ax = fig.add_subplot(gs[2], sharey=ax1)

                                    plt.setp(ax.get_yticklabels(), visible=False)

                                # salva no session_state
                                st.session_state.fig2 = fig

                                lito(
                                    ax1,
                                    df_pp,
                                    profundidades,
                                    litologias,
                                    st.session_state.y_max_pp
                                )

                                # Perfil Raio Gama (vermelho)
                                ax.plot(
                                    df['Perfil Raio Gama'],
                                    df['Profundidade'],
                                    color='red',
                                    linewidth=2,
                                    label="Perfil Raio Gama"
                                )

                                for idx, lbf in enumerate(lbfs):
                                    try:
                                        color = TRENDING_COLORS[idx % len(TRENDING_COLORS)]

                                        prof = df_pp['Profundidade (m)']

                                        prof_ref = (
                                            lbf['prof_ini']
                                            if lbf['prof_ini'] is not None
                                            else prof.min()
                                        )

                                        lbf_line = lbf['inclbf'] * (prof - prof_ref) + lbf['lbf']

                                        if st.session_state.onshore:
                                            prof_ini_df = float(df["Profundidade"].iloc[0])
                                            mask_base = prof >= prof_ini_df
                                        else:
                                            mask_base = prof > st.session_state.lda

                                        if lbf['prof_ini'] is not None and lbf['prof_fim'] is not None:
                                            mask_lbf = (prof >= lbf['prof_ini']) & (prof <= lbf['prof_fim'])
                                            mask_final = mask_base & mask_lbf
                                        else:
                                            mask_final = mask_base

                                        ax.plot(
                                            lbf_line[mask_final],
                                            prof[mask_final],
                                            linewidth=3,
                                            color=color,
                                            label=f'LBF {idx + 1}'
                                        )

                                    except Exception:
                                        pass

                                x = len(df_pp) - len(df)
                                if st.session_state.s_gr:
                                    if st.session_state.ex == 'Desativada':
                                        ax.plot(df_pp['Raio Gama Suavizado'], df_pp['Profundidade (m)'], color='blue',
                                                linestyle='-', linewidth=2, label="Perfil Raio Gama")
                                    else:
                                        ax.plot(df_pp['Raio Gama Suavizado'][x:], df_pp['Profundidade (m)'][x:],
                                                color='blue',
                                                linestyle='-', linewidth=2, label="Perfil Raio Gama")
                                ax.set_title('GR x Profundidade (m)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Perfil Raio Gama (GAPI)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)

                                ax.set_xlim(0, df_pp["Perfil Raio Gama"].max() + 20)

                                ax.invert_yaxis()
                                ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                ax.set_yticks(range(st.session_state.y_min_pp, st.session_state.y_max_pp,
                                                    st.session_state.y_step))
                                ax.set_ylim(st.session_state.y_max_pp, st.session_state.y_min_pp)
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.legend(
                                    loc='upper right',
                                    fontsize=8,
                                    frameon=True,
                                    shadow=True,
                                    fancybox=True,
                                    framealpha=1,
                                    facecolor='white',
                                    edgecolor='gray'
                                )
                                add_watermark(
                                    ax,
                                    logo_path="logo2.png",
                                    xy=(0.50, 0.5),
                                    zoom=0.2,
                                    alpha=0.2,
                                    zorder=0
                                )

                                st.pyplot(st.session_state.fig2)

                else:
                    st.error('Preencha corretamente a aba "Gradiente de Sobrecarga"', icon="🚨")
            else:
                st.error('Por favor, insira um documento!', icon="🚨")

        # Ver Dataframes
        with tb[1]:
            if uploaded_file:
                try:
                    st.dataframe(df_pp, use_container_width=True, hide_index=True)
                    st.dataframe(st.session_state.df_perm_nao_perm, use_container_width=True)
                except Exception as e:
                    pass

    # Estabilidade de Poço
    with tabs[4]:
        tabss = st.tabs(['Tensões em Volta do Poço', 'Gradiente de Fratura'])
        # Gradiente de Fratura
        with tabss[1]:
            tb = st.tabs(['Gradiente de Fratura', 'Tabela de Dados Calculados'])
            with tb[0]:
                if uploaded_file:
                    if "tvp" not in st.session_state:
                        st.session_state.tvp = False
                    # try:
                    if all(value != 0 for value in [st.session_state.rtkb]) and all(value != 0 for value in [st.session_state.gn,
                                                             st.session_state.anormal, st.session_state.expoente]):
                        colu1, colu2, colu3 = st.columns((1, 1, 1))
                        with colu1:
                            with st.container(border=True):
                                with st.expander('Leak Off Test', expanded=True):
                                    colun1, colun2 = st.columns(2)
                                    with colun1:
                                        st.checkbox('Inserir LOTs', key='lot', value=False)
                                    with colun2:
                                        st.checkbox(
                                            'K auxiliar',
                                            key='auxiliar',
                                            value=False,
                                            help=(
                                                "**Ponto Auxiliar (K=0.01)** \n\n"
                                                "- Adiciona um ponto inicial em **1 m de profundidade** com um valor de K muito baixo (0.01).\n"
                                                "- Útil quando há apenas **um dado de LOT**, garantindo que os cálculos de gradiente de fratura e interpolação comecem desde o topo do poço.\n"
                                                "- Serve como **referência inicial**, evitando lacunas nos gráficos e melhorando a consistência dos resultados.\n"
                                                "- Não altera os dados reais; é apenas um ponto de apoio para os cálculos."
                                            )
                                        )

                                    if st.session_state.lot:
                                        if 'add' not in st.session_state:
                                            st.session_state.add = []
                                        c1, c2 = st.columns(2)
                                        with c1:
                                            if st.button('Add :heavy_plus_sign:', key='add_bt',
                                                         use_container_width=True):
                                                st.session_state.add.append(1)
                                        with c2:
                                            if st.button('Delete :x:', key='delete_bt', use_container_width=True):
                                                if st.session_state.add:
                                                    st.session_state.add.pop(-1)
                                                else:
                                                    st.toast('There are no action to delete!')

                                        col1, col2, col3 = st.columns((1, 1, 1))
                                        with col1:
                                            st.selectbox('LOT ou FIT 1', ('LOT', 'FIT'), key='r1_tipo')
                                            st.selectbox('LOT ou FIT 2', ('LOT', 'FIT'), key='r2_tipo')
                                            for i in range(len(st.session_state.add)):
                                                st.selectbox(f'LOT ou FIT {i + 3}', ('LOT', 'FIT'),
                                                             key=f'r_{i + 3}_tipo')
                                        with col2:
                                            st.number_input('Profundidade 1', step=1.0, format='%f', key='p1_proff',
                                                            min_value=0.0)
                                            st.number_input('Profundidade 2', step=1.0, format='%f', key='p2_proff',
                                                            min_value=0.0)
                                            for i in range(len(st.session_state.add)):
                                                st.number_input(f'Profundidade {i + 3}', step=1.0, format='%f',
                                                                min_value=0.0, key=f'p{i + 3}_proff')
                                        with col3:
                                            st.number_input('Peso Equivalente 1', step=1.0, format='%f', key='l1_leak',
                                                            min_value=0.0)
                                            st.number_input('Peso Equivalente 2', step=1.0, format='%f', key='l2_leak',
                                                            min_value=0.0)
                                            for i in range(len(st.session_state.add)):
                                                st.number_input(f'Peso Equivalente {i + 3}', step=1.0, format='%f',
                                                                min_value=0.0,
                                                                key=f'l{i + 3}_leak')

                                        # ---- Captura e ordena as chaves corretamente ----

                                        tipo_keys = [k for k in st.session_state.keys() if k.endswith('_tipo')]
                                        tipo_keys = sorted(tipo_keys, key=lambda x: int(re.search(r'\d+', x).group()))
                                        tt = [st.session_state[k] for k in tipo_keys]

                                        prof_keys = [k for k in st.session_state.keys() if k.endswith('_proff')]
                                        prof_keys = sorted(prof_keys, key=lambda x: int(re.search(r'\d+', x).group()))
                                        pp = [st.session_state[k] for k in prof_keys]

                                        leak_keys = [k for k in st.session_state.keys() if k.endswith('_leak')]
                                        leak_keys = sorted(leak_keys, key=lambda x: int(re.search(r'\d+', x).group()))
                                        lt = [st.session_state[k] for k in leak_keys]

                                        st.session_state.tt = tt
                                        st.session_state.pp = pp
                                        st.session_state.lt = lt

                                    else:
                                        colunas_para_exibir = ["Nome", "Distância (km)", "Profundidade Vertical (m)",
                                                               "Peso Eq. (lb/gal)"]
                                        df_filtrado = df_dentro_exibir[colunas_para_exibir]
                                        st.markdown("### LOTs de poços próximos")
                                        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                                        pp = df_filtrado['Profundidade Vertical (m)'].tolist()
                                        lt = df_filtrado['Peso Eq. (lb/gal)'].tolist()
                                        st.session_state.pp = pp
                                        st.session_state.lt = lt
                                        tt = ["LOT"] * len(st.session_state.pp)
                                        st.session_state.tt = tt

                                    # ---- Funções auxiliares ----
                                    def get_closest_depth(df, target_depth):
                                        closest_index = (df['Profundidade (m)'] - target_depth).abs().idxmin()
                                        return df.iloc[closest_index]['Gradiente de Pressão de Poros Médio (lb/gal)']

                                    def get_closest_depth_value(target_depth):
                                        if st.session_state.onshore:
                                            df_ext = st.session_state.ext_df
                                            closest_index = (df_ext[
                                                                 'Profundidade em relação a mesa rotativa (m)'] - target_depth).abs().idxmin()
                                        else:
                                            df_ext = df
                                            closest_index = (df_ext['Profundidade'] - target_depth).abs().idxmin()
                                        return df_ext.iloc[closest_index]['Pressão de Sobrecarga (psi)']

                                    # --- Botão para gerar o DataFrame ---
                                    if st.button('Calibrar curva de K', use_container_width=True,
                                                 type='primary'):
                                        # Lista de profundidades e valores de LOT/FIT ajustados
                                        pp_all = st.session_state.pp
                                        lt_all_adjusted = [
                                            st.session_state.lt[i] + 0.5 if st.session_state.tt[i] == "FIT" else
                                            st.session_state.lt[i]
                                            for i in range(len(st.session_state.tt))
                                        ]

                                        # Monta DataFrame com todos os pontos (LOT e FIT ajustado)
                                        gf = pd.DataFrame({'Profundidade (m)': pp_all})
                                        gf['Gradiente de P. de poros (psi)'] = [get_closest_depth(df_pp, d) for d in
                                                                                pp_all]
                                        gf['P. Poros (psi)'] = 0.1704 * gf['Profundidade (m)'] * gf[
                                            'Gradiente de P. de poros (psi)']
                                        gf['P. Absorção (psi)'] = 0.1704 * gf['Profundidade (m)'] * lt_all_adjusted
                                        gf['P. Sobrecarga (psi)'] = [get_closest_depth_value(d) for d in pp_all]
                                        gf['K'] = (gf['P. Absorção (psi)'] - gf['P. Poros (psi)']) / (
                                                gf['P. Sobrecarga (psi)'] - gf['P. Poros (psi)'])

                                        # Se o usuário marcou o ponto auxiliar
                                        if st.session_state.auxiliar:
                                            nova_linha = pd.DataFrame([{
                                                'Profundidade (m)': 1,
                                                'Gradiente de P. de poros (psi)': None,
                                                'P. Poros (psi)': None,
                                                'P. Absorção (psi)': None,
                                                'P. Sobrecarga (psi)': None,
                                                'K': 0.01
                                            }])
                                            gf = pd.concat([nova_linha, gf], ignore_index=True)

                                        # Ordena e salva no session_state
                                        gf = gf.sort_values(by='Profundidade (m)').reset_index(drop=True)
                                        st.session_state.gf = gf
                                        st.session_state.edited_gf = gf.copy()

                                with st.expander('Relação das tensões', expanded=True):
                                    st.markdown("### Variação de K com a Profundidade")

                                    # Inicializa edited_gf se não existir
                                    if 'edited_gf' not in st.session_state:
                                        # Se gf existir, copia, senão cria um DataFrame vazio com as colunas necessárias
                                        if 'gf' in st.session_state:
                                            st.session_state.edited_gf = st.session_state.gf.copy()
                                        else:
                                            st.session_state.edited_gf = pd.DataFrame(columns=['Profundidade (m)', 'K'])

                                    # --- Atualização automática do DataFrame de edição ---
                                    if 'gf' in st.session_state:
                                        if not st.session_state.edited_gf.equals(st.session_state.gf):
                                            st.session_state.edited_gf = st.session_state.gf.copy()

                                    # Editor de tabela
                                    st.session_state.edited_gf = st.data_editor(
                                        st.session_state.edited_gf[['Profundidade (m)', 'K']],
                                        use_container_width=True,
                                        hide_index=True
                                    )

                                    # Atualiza o DataFrame base temporariamente para os cálculos
                                    gf = st.session_state.edited_gf.copy()

                                    # Só calcula se houver dados válidos
                                    if gf.empty:
                                        a = None
                                        b = None
                                    else:
                                        try:
                                            b, log_a = np.polyfit(gf['K'], np.log(gf['Profundidade (m)']), 1)
                                            a = np.exp(log_a)
                                        except Exception:
                                            a = None
                                            b = None

                                    st.session_state['a'] = a
                                    st.session_state['b'] = b

                        if st.session_state.spp:
                            df_f = pd.DataFrame({
                                'Profundidade (m)': df_pp['Profundidade (m)'],
                                'MD': df['MD'],
                                'Gradiente de Sobrecarga (lb/gal)': df_pp['Gradiente de Sobrecarga (lb/gal)'],
                                'Gradiente de Pressão de Poros (lb/gal)': df_pp[
                                    'Gradiente de Pressão de Poros Suavizado (lb/gal)']
                            })

                        else:
                            df_f = pd.DataFrame({
                                'Profundidade (m)': df_pp['Profundidade (m)'],
                                'MD': df['MD'],
                                'Gradiente de Sobrecarga (lb/gal)': df_pp['Gradiente de Sobrecarga (lb/gal)'],
                                'Gradiente de Pressão de Poros (lb/gal)': df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                            })

                        try:
                            # Cálculo de K
                            df_f['K'] = (np.log(df_f['Profundidade (m)']) - np.log(a)) / b


                            df_f['Gradiente de Fratura (lb/gal)'] = df_f.apply(
                                lambda row: row['Gradiente de Pressão de Poros (lb/gal)']
                                            + row['K'] * (row['Gradiente de Sobrecarga (lb/gal)'] - row[
                                    'Gradiente de Pressão de Poros (lb/gal)']),
                                axis=1
                            )

                            # Substitui valores negativos por 0
                            df_f['Gradiente de Fratura (lb/gal)'] = np.where(df_f['Gradiente de Fratura (lb/gal)'] < 0, 0,
                                                                             df_f['Gradiente de Fratura (lb/gal)'])

                            df_f.insert(
                                loc=4,
                                column='Pressão de Fratura (psi)',
                                value=0.1704 * df_f['Gradiente de Fratura (lb/gal)'] * df_f['Profundidade (m)']
                            )

                            for i in st.session_state.zonas:
                                index = (df_f['Profundidade (m)'] - i[0]).abs().idxmin()
                                df_f.loc[index, 'Gradiente de Fratura (lb/gal)'] = i[1]

                        except Exception as e:
                            pass

                        with colu3:
                            with st.container(border=True):
                                fig1 = plt.figure(figsize=(8, 10))

                                if st.session_state.idg == 'Sim':
                                    # ===== COM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 4,
                                        width_ratios=[0.1, 0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax_idade = fig1.add_subplot(gs[0])
                                    ax1 = fig1.add_subplot(gs[1], sharey=ax_idade)

                                    ax_gap = fig1.add_subplot(gs[2])
                                    ax_gap.axis('off')

                                    ax = fig1.add_subplot(gs[3], sharey=ax_idade)

                                    idade_formacao(ax_idade, st.session_state.df_idade, st.session_state.y_max_pp)

                                    # remove ticks e labels da coluna de idade
                                    ax_idade.tick_params(
                                        axis='y',
                                        which='both',
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                        labelright=False
                                    )

                                    ax_idade.set_ylabel("")

                                    # evita duplicar rótulos de profundidade
                                    plt.setp(ax1.get_yticklabels(), visible=False)
                                    plt.setp(ax.get_yticklabels(), visible=False)

                                else:
                                    # ===== SEM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 3,
                                        width_ratios=[0.18, 0.21, 1],
                                        wspace=0
                                    )

                                    ax1 = fig1.add_subplot(gs[0])
                                    ax_gap = fig1.add_subplot(gs[1])
                                    ax_gap.axis('off')

                                    ax = fig1.add_subplot(gs[2], sharey=ax1)

                                    plt.setp(ax.get_yticklabels(), visible=False)

                                with st.form("form_gradiente_fratura", border=False):
                                    submitted = st.form_submit_button("Calcular Gradiente de Fratura",
                                                                      use_container_width=True, type='primary')
                                    if submitted:
                                        st.session_state.fratura_calculada = True
                                        st.session_state.tvp = True

                                def reset_config():
                                    if st.session_state.ogf == "Gradiente (lb/gal)":
                                        st.session_state.x_min_f = 7
                                        st.session_state.x_max_f = 23
                                        st.session_state.x_step_f = 1
                                    else:
                                        st.session_state.x_min_f = 0
                                        st.session_state.x_max_f = int(
                                            st.session_state.ext_df['Pressão de Sobrecarga (psi)'].max()) + 200
                                        st.session_state.x_step_f = 500
                                    st.session_state.y_min_f = 0
                                    st.session_state.y_max_f = int(df_f['Profundidade (m)'].max()) + 100
                                    st.session_state.y_step_f = 200

                                lito(
                                    ax1,
                                    df_pp,
                                    profundidades,
                                    litologias,
                                    st.session_state.y_max_pp
                                )
                                # profundidades=st.session_state.get("profundidades", None),
                                # litologias=st.session_state.get("litologias", None)

                                with st.expander("Configurações do Gráfico", expanded=False):
                                    st.segmented_control("***Opção de Gráfico***", ['Gradiente (lb/gal)',
                                                                                    'Pressão (psi)'],
                                                         selection_mode="single",
                                                         default='Gradiente (lb/gal)', key='ogf', width="stretch")
                                    col1, col2 = st.columns((1, 1))
                                    with col1:
                                        st.checkbox('Sobrecarga', key="gras", value=False)
                                    with col2:
                                        st.checkbox('Pressão de Poros', key="grap", value=False)
                                    st.number_input("Eixo X - mínimo", value=7, step=1, key="x_min_f")
                                    st.number_input("Eixo X - máximo", value=23, step=1, key="x_max_f")
                                    st.number_input("Passo do eixo X", value=1, step=1, key="x_step_f")
                                    st.number_input("Eixo Y - mínimo", value=0,
                                                    step=100, key="y_min_f")
                                    st.number_input("Eixo Y - máximo", value=int(df_f['Profundidade (m)'].max()) + 100,
                                                    step=100, key="y_max_f")
                                    st.number_input("Passo do eixo Y", value=200, step=50, key="y_step_f")
                                    # Botão de reset com callback
                                    st.button("Resetar Eixos - Gradiente de Fratura", on_click=reset_config,
                                              type="primary",
                                              use_container_width=True)
                                try:
                                    if st.session_state.ogf == "Gradiente (lb/gal)":
                                        st.session_state.oef = df_f['Gradiente de Fratura (lb/gal)']
                                        st.session_state.oefl = 'G. de Pressão de Poros'
                                    else:
                                        st.session_state.oef = df_f['Pressão de Fratura (psi)']
                                        st.session_state.oefl = 'P. de Fratura'
                                except Exception as e:
                                    pass

                                if st.session_state.get("fratura_calculada", False):
                                    # if st.session_state.lot:
                                    if st.session_state.onshore:
                                        if st.session_state.ogf == "Gradiente (lb/gal)":
                                            ax.plot(st.session_state.oef, df_f['Profundidade (m)'],
                                                    color='brown', linestyle='-', linewidth=2,
                                                    label=st.session_state.oefl)
                                        else:
                                            ax.plot(st.session_state.oef, df_f['Profundidade (m)'],
                                                    color='brown', linestyle='-', linewidth=2,
                                                    label=st.session_state.oefl)

                                    else:
                                        if st.session_state.ogf == "Gradiente (lb/gal)":
                                            ax.plot(st.session_state.oef[x:],
                                                    df_f['Profundidade (m)'][x:], color='brown', linestyle='-',
                                                    linewidth=2, label=st.session_state.oefl)
                                        else:
                                            ax.plot(st.session_state.oef[x:],
                                                    df_f['Profundidade (m)'][x:], color='brown', linestyle='-',
                                                    linewidth=2, label=st.session_state.oefl)

                                    if st.session_state.gras:
                                        if st.session_state.ogf == "Gradiente (lb/gal)":
                                            if st.session_state.onshore:
                                                ax.plot(df_f['Gradiente de Sobrecarga (lb/gal)'],
                                                        df_f['Profundidade (m)'],
                                                        color='black', linestyle='-', linewidth=2,
                                                        label="G. Sobrecarga")
                                            else:
                                                ax.plot(df_f['Gradiente de Sobrecarga (lb/gal)'][2:],
                                                        df_f['Profundidade (m)'][2:], color='black', linestyle='-',
                                                        linewidth=2, label="G. Sobrecarga")
                                        else:
                                            if st.session_state.onshore:
                                                ax.plot(st.session_state.ext_df['Pressão de Sobrecarga (psi)'],
                                                        st.session_state.ext_df[
                                                            'Profundidade em relação a mesa rotativa (m)'],
                                                        color='black', linestyle='-', linewidth=2,
                                                        label="P. Sobrecarga")
                                            else:
                                                ax.plot(st.session_state.ext_df['Pressão Sobrecarga (lb/gal)'][2:],
                                                        st.session_state.ext_df['Profundidade (m)'][2:], color='black',
                                                        linestyle='-',
                                                        linewidth=2, label="P. Sobrecarga")

                                    if st.session_state.grap:
                                        if st.session_state.ogf == "Gradiente (lb/gal)":
                                            if st.session_state.onshore:
                                                if not st.session_state.spp:
                                                    ax.plot(df_f['Gradiente de Pressão de Poros (lb/gal)'],
                                                            df_f['Profundidade (m)'], color='orange', linestyle='-',
                                                            linewidth=2, label="G. Pressão de Poros")
                                                else:
                                                    ax.plot(df_f['Gradiente de Pressão de Poros (lb/gal)'],
                                                            df_f['Profundidade (m)'], color='orange', linestyle='-',
                                                            linewidth=2, label="G. Pressão de Poros")
                                            else:
                                                ax.plot(df_f['Gradiente de Pressão de Poros (lb/gal)'][x:],
                                                        df_f['Profundidade (m)'][x:], color='orange', linestyle='-',
                                                        linewidth=2, label="G. Pressão de Poros")
                                        else:
                                            if st.session_state.onshore:
                                                if not st.session_state.spp:
                                                    ax.plot(df_pp['Pressão de Poros (psi)'],
                                                            df_pp['Profundidade (m)'], color='orange', linestyle='-',
                                                            linewidth=2, label="P. de Poros")
                                                else:
                                                    ax.plot(df_pp['Pressão de Poros Suavizado (psi)'],
                                                            df_pp['Profundidade (m)'], color='orange', linestyle='-',
                                                            linewidth=2, label="P. de Poros")
                                            else:
                                                ax.plot(df_pp['Pressão de Poros (lb/gal)'][x:],
                                                        df_pp['Profundidade (m)'][x:], color='orange', linestyle='-',
                                                        linewidth=2, label="P. de Poros")

                                        if "df_mud" in st.session_state and isinstance(st.session_state["df_mud"],
                                                                                       pd.DataFrame):
                                            df_mud = st.session_state["df_mud"].copy()

                                            # Executado
                                            if mostrar_executado and df_mud[
                                                "Peso do Fluido Executado (lb/gal)"].notna().any():
                                                ax.plot(
                                                    df_mud["Peso do Fluido Executado (lb/gal)"],
                                                    df_mud["Profundidade (m)"],
                                                    linestyle="-",
                                                    color="mediumvioletred",
                                                    linewidth=2,
                                                    label="Peso do Fluido (Executado)",
                                                    zorder=5
                                                )

                                    if st.session_state.ogf == "Gradiente (lb/gal)":
                                        # Mantém os valores originais
                                        lot_x = [lt[i] for i in range(len(tt)) if tt[i] == "LOT"]
                                        lot_y = [pp[i] for i in range(len(tt)) if tt[i] == "LOT"]

                                    else:
                                        # Faz o cálculo com multiplicação
                                        lot_x = [lt[i] * 0.1704 * pp[i] for i in range(len(tt)) if tt[i] == "LOT"]
                                        lot_y = [pp[i] for i in range(len(tt)) if tt[i] == "LOT"]

                                    fit_x = [lt[i] for i in range(len(tt)) if tt[i] == "FIT"]
                                    fit_y = [pp[i] for i in range(len(tt)) if tt[i] == "FIT"]

                                    if lot_x and lot_y:
                                        ax.scatter(lot_x, lot_y, color='red', label="LOT's", zorder=5, marker='D', s=50)

                                    if fit_x and fit_y:
                                        ax.scatter(fit_x, fit_y, color='blue', label="FIT's", zorder=5, marker='^',
                                                   s=50)

                                    # Janela Operacional: Preenchimento entre pressão de poros e fratura
                                    if st.session_state.ogf == "Gradiente (lb/gal)":
                                        if st.session_state.grap:
                                            if st.session_state.onshore:
                                                x1 = df_f['Gradiente de Pressão de Poros (lb/gal)']
                                                x2 = df_f['Gradiente de Fratura (lb/gal)']
                                                y = df_f['Profundidade (m)']
                                            else:
                                                x1 = df_f['Gradiente de Pressão de Poros (lb/gal)'][x:]
                                                x2 = df_f['Gradiente de Fratura (lb/gal)'][x:]
                                                y = df_f['Profundidade (m)'][x:]

                                            ax.fill_betweenx(
                                                y,
                                                x1,
                                                x2,
                                                where=(x2 > x1),
                                                color='lightgreen',
                                                alpha=0.2,
                                                label='Janela Operacional',
                                                interpolate=True
                                            )

                                    else:
                                        # Usa curvas de pressão (psi)
                                        if st.session_state.spp:
                                            x1 = df_pp['Pressão de Poros Suavizado (psi)']
                                        else:
                                            x1 = df_pp['Pressão de Poros (psi)']
                                        x2 = df_f['Pressão de Fratura (psi)']
                                        y = df_f['Profundidade (m)']

                                        ax.fill_betweenx(
                                            y,
                                            x1,
                                            x2,
                                            where=(x2 > x1),
                                            color='lightgreen',
                                            alpha=0.2,
                                            label='Janela Operacional',
                                            interpolate=True
                                        )

                                ax.set_title('Geopressões (lb/gal)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                ax.invert_yaxis()
                                ax.set_ylim(st.session_state.y_max_f, st.session_state.y_min_f)
                                ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                ax.set_yticks(range(st.session_state.y_min_f, st.session_state.y_max_f,
                                                    st.session_state.y_step_f))
                                ax.set_xticks(range(st.session_state.x_min_f, st.session_state.x_max_f,
                                                    st.session_state.x_step_f))
                                ax.set_xlim(st.session_state.x_min_f, st.session_state.x_max_f)
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.legend(
                                    loc='upper right',
                                    fontsize=8,
                                    frameon=True,
                                    shadow=True,
                                    fancybox=True,
                                    framealpha=1,
                                    facecolor='white',
                                    edgecolor='gray'
                                )
                                add_watermark(
                                    ax,
                                    logo_path="logo2.png",
                                    xy=(0.50, 0.5),
                                    zoom=0.2,
                                    alpha=0.2,
                                    zorder=0
                                )

                                st.pyplot(fig1)

                        with colu2:
                            with st.container(border=True):

                                # Botão de limpar dados e restaurar o DataFrame original
                                if st.button('🔄 Limpar Dados - Gradiente de Fratura', use_container_width=True,
                                             type='primary'):
                                    # Limpa variáveis específicas
                                    for key in list(st.session_state.keys()):
                                        if key.startswith(('r', 'p', 'l')) and key.endswith(
                                                ('_prof', '_leak')) or key in ['add', 'gras', 'grap',
                                                                               'fratura_calculada', 'tvp']:
                                            del st.session_state[key]

                                    # Restaura o DataFrame editável para os dados originais
                                    st.session_state.edited_gf = st.session_state.gf.copy()

                                    # Recarrega a página para refletir a limpeza
                                    st.rerun()

                                st.markdown("### Método das Tensões Mínimas")

                                fig2 = plt.figure(figsize=(8, 10))

                                if st.session_state.idg == 'Sim':
                                    # ===== COM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 4,
                                        width_ratios=[0.1, 0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax_idade = fig2.add_subplot(gs[0])
                                    ax1 = fig2.add_subplot(gs[1], sharey=ax_idade)

                                    ax_gap = fig2.add_subplot(gs[2])
                                    ax_gap.axis('off')

                                    ax = fig2.add_subplot(gs[3], sharey=ax_idade)

                                    idade_formacao(ax_idade, st.session_state.df_idade, st.session_state.y_max_pp)

                                    # remove ticks e labels da coluna de idade
                                    ax_idade.tick_params(
                                        axis='y',
                                        which='both',
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                        labelright=False
                                    )

                                    ax_idade.set_ylabel("")

                                    # evita duplicar rótulos de profundidade
                                    plt.setp(ax1.get_yticklabels(), visible=False)
                                    plt.setp(ax.get_yticklabels(), visible=False)

                                else:
                                    # ===== SEM coluna de idade =====
                                    gs = gridspec.GridSpec(
                                        1, 3,
                                        width_ratios=[0.18, 0.21, 1],
                                        wspace=0
                                    )

                                    ax1 = fig2.add_subplot(gs[0])
                                    ax_gap = fig2.add_subplot(gs[1])
                                    ax_gap.axis('off')

                                    ax = fig2.add_subplot(gs[2], sharey=ax1)

                                    plt.setp(ax.get_yticklabels(), visible=False)

                                lito(
                                    ax1,
                                    df_pp,
                                    profundidades,
                                    litologias,
                                    st.session_state.y_max_pp

                                )

                                ax.plot(
                                    gf['K'], gf['Profundidade (m)'],
                                    color='blue', linestyle='None', linewidth=2,
                                    marker='o', markersize=10,
                                    markerfacecolor='black', markeredgecolor='red',
                                    label="K"
                                )
                                k_values = np.linspace(gf['K'].min(), gf['K'].max(), 200)
                                try:
                                    depth_trend = a * np.exp(b * k_values)

                                    ax.plot(k_values, depth_trend, color='red', linestyle='--', linewidth=2,
                                        label='Linha de Tendência Exponencial de K')

                                except Exception as e:
                                    pass

                                ax.set_title('K x Profundidade', fontsize=14, fontweight='bold')
                                ax.set_xlabel('K', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                ax.invert_yaxis()

                                max_depth = int(st.session_state.df1['Profundidade'].max())
                                ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                ax.set_ylim(st.session_state.y_max_f, st.session_state.y_min_f)
                                ax.set_yticks(range(st.session_state.y_min_f, st.session_state.y_max_f,
                                                    st.session_state.y_step_f))
                                ax.grid(True, linestyle='--', alpha=0.5)
                                ax.legend(
                                    loc='upper right',
                                    fontsize=8,
                                    frameon=True,
                                    shadow=True,
                                    fancybox=True,
                                    framealpha=1,
                                    facecolor='white',
                                    edgecolor='gray'
                                )
                                add_watermark(
                                    ax,
                                    logo_path="logo2.png",
                                    xy=(0.50, 0.5),
                                    zoom=0.2,
                                    alpha=0.2,
                                    zorder=0
                                )

                                st.pyplot(fig2)

                        # depois de st.pyplot(fig1)
                        st.session_state.fig_fratura = fig1
                        st.session_state.df_f = df_f.copy()
                        st.session_state.tem_gradiente_fratura_plotado = True

                        # guarde também os parâmetros e flags importantes
                        st.session_state.gf = gf.copy()  # tabela K x profundidade (editada)
                        st.session_state.a_k = float(a) if a is not None else None
                        st.session_state.b_k = float(b) if b is not None else None
                        st.session_state.tt = tt
                        st.session_state.pp = pp
                        st.session_state.lt = lt
                        st.session_state.zonas_perda = st.session_state.get("zonas", [])

                        # depois de st.pyplot(fig2)
                        st.session_state.fig_k_prof = fig2

                        def salvar_matplotlib_para_pdf(fig, path, dpi=200):
                            fig.savefig(
                                path,
                                dpi=dpi,
                                bbox_inches="tight",
                                facecolor="white"
                            )

                    # except Exception as e:
                    else:
                        st.error('Preencha corretamente a aba "Gradiente de Pressão de Poros"', icon="🚨")

                else:
                    st.error('Por favor, insira um documento!', icon="🚨")

            # Ver Dataframes
            with tb[1]:
                if uploaded_file:
                    if all(value != 0 for value in [st.session_state.rtkb]):
                        if all(value != 0 for value in
                               [st.session_state.gn, st.session_state.anormal, st.session_state.expoente]):
                            st.dataframe(df_f, use_container_width=True, hide_index=True)

        # Tensões em Volta do Poço
        with tabss[0]:
            if uploaded_file:
                if st.session_state.rtkb != 0:
                    if "fs" not in st.session_state:
                        st.session_state.fs = 0.5

                    if all(value != 0 for value in [st.session_state.rtkb]) and all(
                            value != 0 for value in [st.session_state.gn,
                                                     st.session_state.anormal, st.session_state.expoente]):
                        tb = st.tabs(
                            ['Critério de Falha - Mohr Coulomb', 'Visualização 3D das Tensões', 'Configurações',
                             'Dados Calculados'])
                        if st.session_state.onshore:
                            profundidade = df_pp['Profundidade (m)']
                            md = df['MD']
                            densidade = df_pp['Perfil de densidade (g/cm³)']
                            sonico = df_pp['Perfil sônico (µs/pé)']
                            grad_sobrecarga = df_pp['Gradiente de Sobrecarga (lb/gal)']
                            linha_extrapolada = df_pp.get(
                                'Linha Extrapolada',
                                pd.Series(False, index=df_pp.index)
                            )
                        else:
                            profundidade = df['Profundidade']
                            md = df['MD']
                            densidade = df['Perfil de densidade']
                            sonico = df['Perfil sônico']
                            grad_sobrecarga = df['Gradiente de Sobrecarga (lb/gal)']
                            linha_extrapolada = pd.Series(False, index=df.index)

                        if "suavi_s" not in st.session_state:
                            st.session_state.suavi_s = True
                        if st.session_state.suavi_s:
                            sonico = suavizar(profundidade, sonico)
                            densidade = suavizar(profundidade, densidade)

                        df_tvp = pd.DataFrame({
                            'Profundidade (m)': profundidade,
                            'MD': md,
                            'Perfil de densidade (g/cm³)': densidade,
                            'Perfil sônico (µs/pé)': sonico,
                            'Gradiente de Sobrecarga (lb/gal)': grad_sobrecarga,
                            'Linha Extrapolada': linha_extrapolada
                        })

                        df_tvp['Linha Extrapolada'] = df_tvp['Linha Extrapolada'].fillna(False).astype(bool)

                        mask_extrap = (
                                st.session_state.onshore
                                and st.session_state.ex == 'Ativada'
                                and df_tvp['Linha Extrapolada']
                        )

                        mask_calculo_valido = (
                                ~df_tvp['Linha Extrapolada']
                                & df_tvp['Perfil sônico (µs/pé)'].notna()
                                & (df_tvp['Perfil sônico (µs/pé)'] > 0)
                        )

                        # ABA DE CONFIGURAÇÕES
                        with tb[2]:
                            # if uploaded_file:
                            c1, c2 = st.columns(2)
                            with c1:
                                with st.container(border=True):
                                    coluna1, coluna2 = st.columns(2)
                                    st.markdown('### Configurações dos Cálculos')
                                    with coluna1:
                                        st.button("Inserir direções das tensões in situ", key="tis",
                                                  use_container_width=True, type='primary', on_click=tensoes)
                                    with coluna2:
                                        if st.button("Resetar direções das tensões in situ", key="resd",
                                                     use_container_width=True, type='primary'):
                                            st.session_state.direct = False
                                            dir_H = 0
                                            dir_h = 90
                                    if "direct" not in st.session_state:
                                        st.session_state.direct = False
                                    if st.session_state.direct:
                                        df_pp = pd.merge_asof(
                                            df_pp,
                                            st.session_state.tise,
                                            on="Profundidade (m)",
                                            direction="backward"
                                        )
                                        dir_H = df_pp['Direção SH']
                                        dir_h = df_pp['Direção SH'] + 90

                                    else:
                                        dir_H = 0
                                        dir_h = 90

                                    with coluna1:
                                        st.button(
                                            "Inserir relação das tensões horizontais",
                                            key="rel_tens_btn",
                                            use_container_width=True,
                                            type="primary",
                                            on_click=rel_hor
                                        )

                                    with coluna2:
                                        if st.button(
                                                "Resetar relação das tensões horizontais",
                                                key="reset_rel_tens",
                                                use_container_width=True,
                                                type="primary"
                                        ):
                                            st.session_state.rel_hor = False
                                            st.session_state.SH = 0.61
                                            st.session_state.Sh = 0.6

                                            if "rel_hor_df" in st.session_state:
                                                del st.session_state.rel_hor_df

                                            st.rerun()

                                    st.write("")
                                    st.number_input("Raio do poço", value=1, step=1, key='rw')
                                    st.write("")
                                    st.number_input("Raio de investigação", value=1, step=1, key='r')
                            # =========================
                            # Configuração dos grupos
                            # =========================
                            PLOT_DEFAULTS_ORIGINAIS = {
                                "jo": True,
                                "suav_max_inf": True,
                                "suav_min_sup": True,
                                "ijo": True,
                                "sjo": True,
                                "li": False,
                                "ls": False,
                                "show_pp": False,
                                "gs": False,
                                "ti": False,
                                "cia": False,
                                "cib": False,
                                "tsa": False,
                                "tsb": False,
                                "csa": False,
                                "csb": False,
                                "suav_cia": False,
                                "suav_cib": False,
                                "suav_tsa": False,
                                "suav_tsb": False,
                                "suav_csa": False,
                                "suav_csb": False,
                                "suavi_s": True,
                            }

                            PLOT_ALL_TRUE = {
                                "jo": True,
                                "li": False,
                                "ls": False,
                                "show_pp": True,
                                "gs": True,
                                "ti": True,
                                "cia": True,
                                "cib": True,
                                "tsa": True,
                                "tsb": True,
                                "csa": True,
                                "csb": True,
                                "ijo": True,
                                "sjo": True,
                            }

                            SMOOTH_ALL_TRUE = {
                                "suav_max_inf": True,
                                "suav_min_sup": True,
                                "suav_cia": True,
                                "suav_cib": True,
                                "suav_tsa": True,
                                "suav_tsb": True,
                                "suav_csa": True,
                                "suav_csb": True,
                            }

                            def set_session_defaults(defaults: dict):
                                for key, value in defaults.items():
                                    st.session_state[key] = value

                            def init_session_defaults(defaults: dict):
                                for key, value in defaults.items():
                                    if key not in st.session_state:
                                        st.session_state[key] = value

                            CHECKBOX_GROUPS_COL1 = [
                                (
                                    "##### Janela Operacional",
                                    [
                                        ("Janela Operacional", "jo", True),
                                        ("Limite Inferior da Janela Operacional", "li", False),
                                        ("Limite Superior da Janela Operacional", "ls", False),
                                        ("FS Inferior da Janela Operacional", "ijo", True),
                                        ("FS Superior da Janela Operacional", "sjo", True),
                                    ],
                                ),
                                (
                                    "##### Limites Inferiores",
                                    [
                                        ("Pressão de Poros", "show_pp", False),
                                        ("Gradiente de Sobrecarga", "gs", False),
                                        ("Tração Inferior", "ti", False),
                                        ("Comp Inferior σθA", "cia", False),
                                        ("Comp Inferior σθB", "cib", False),
                                    ],
                                ),
                                (
                                    "##### Limites Superiores",
                                    [
                                        ("Tração Superior (σθA)", "tsa", False),
                                        ("Tração Superior (σθB)", "tsb", False),
                                        ("Comp Superior σθA", "csa", False),
                                        ("Comp Superior σθB", "csb", False),
                                    ],
                                ),
                                (
                                    "##### Suavizar Perfilagens",
                                    [
                                        ("Perfis suavizados", "suavi_s", True),
                                    ],
                                ),
                            ]

                            CHECKBOX_GROUPS_COL2 = [
                                (
                                    "##### Janela Operacional Suavizada",
                                    [
                                        ("Suavizar Limite Inferior da Janela Operacional", "suav_max_inf",
                                         True),
                                        ("Suavizar Limite Superior da Janela Operacional", "suav_min_sup",
                                         True),
                                    ],
                                ),
                                (
                                    "##### Limites Inferiores Suavizados",
                                    [
                                        ("Suavizar Comp Inferior σθA", "suav_cia", False),
                                        ("Suavizar Comp Inferior σθB", "suav_cib", False),
                                    ],
                                ),
                                (
                                    "##### Limites Superiores Suavizados",
                                    [
                                        ("Suavizar Tração Superior σθA", "suav_tsa", False),
                                        ("Suavizar Tração Superior σθB", "suav_tsb", False),
                                        ("Suavizar Comp Superior σθA", "suav_csa", False),
                                        ("Suavizar Comp Superior σθB", "suav_csb", False),
                                    ],
                                ),
                                (
                                    "##### Testes de Absorção (FIT/LOT)",
                                    [
                                        ("Testes de Absorção", "tab", True),
                                    ],
                                ),
                            ]

                            def render_checkbox_groups(groups):
                                for titulo, items in groups:
                                    with st.expander(titulo, expanded=False):
                                        for label, key, default in items:
                                            if key not in st.session_state:
                                                st.session_state[key] = default
                                            st.checkbox(label, key=key)

                            # =========================
                            # Bloco c2 reescrito
                            # =========================
                            with c2:
                                with st.container(border=True):
                                    st.markdown("### Curvas Plotadas no Gráfico")

                                    # inicialização segura dos estados
                                    init_session_defaults(PLOT_DEFAULTS_ORIGINAIS)
                                    init_session_defaults({
                                        "suav_max_inf": True,
                                        "suav_min_sup": True,
                                        "tab": True,
                                        "suavi_s": False,
                                    })

                                    if st.button(
                                            "Restaurar Padrões Originais",
                                            key="plot_all_o",
                                            use_container_width=True,
                                            type="primary"
                                    ):
                                        set_session_defaults(PLOT_DEFAULTS_ORIGINAIS)

                                    col1, col2 = st.columns(2)

                                    with col1:
                                        if st.button(
                                                "Plotar todas as curvas",
                                                key="plot_all",
                                                use_container_width=True,
                                                type="primary"
                                        ):
                                            set_session_defaults(PLOT_ALL_TRUE)

                                        render_checkbox_groups(CHECKBOX_GROUPS_COL1)

                                    with col2:
                                        if st.button(
                                                "Suavizar todas as curvas",
                                                key="smooth_all",
                                                use_container_width=True,
                                                type="primary"
                                        ):
                                            set_session_defaults(SMOOTH_ALL_TRUE)

                                        render_checkbox_groups(CHECKBOX_GROUPS_COL2)

                        def carregar_coesao():
                            with open("coesao.yaml", "r") as f:
                                return yaml.safe_load(f)["Coesao"]

                        @st.dialog("Litologias")
                        def coe_lito():

                            # Carrega o YAML
                            coesao_dict = carregar_coesao()

                            # Inicializa o dataframe no session_state se não existir
                            if "dados_lito" not in st.session_state:
                                st.session_state.dados_lito = pd.DataFrame({
                                    "Topo (m)": [],
                                    "Base (m)": [],
                                    "Litologia": [],
                                    "So (psi)": []
                                })

                            st.markdown("### Adicionar Intervalos de Litologia")

                            col1, col2 = st.columns(2)

                            with col1:
                                topo = st.number_input(
                                    "Profundidade Topo (m)",
                                    min_value=0.0,
                                    step=0.5,
                                    format="%.2f"
                                )

                            with col2:
                                base = st.number_input(
                                    "Profundidade Base (m)",
                                    min_value=0.0,
                                    step=0.5,
                                    format="%.2f"
                                )

                            litologia = st.selectbox(
                                "Litologia",
                                [
                                    "Arenito",
                                    "Folhelho",
                                    "Calcário",
                                    "Siltito",
                                    "Conglomerado",
                                    "Halita",
                                ]
                            )

                            # Converter acentuados → YAML keys
                            chave_yaml = (
                                litologia
                                .replace("á", "a").replace("Á", "A")
                                .replace("í", "i").replace("Í", "I")
                                .replace("ó", "o").replace("Ó", "O")
                                .replace("ç", "c").replace("Ç", "C")
                            )

                            so_lito = coesao_dict[chave_yaml]

                            # Botão para adicionar intervalo
                            if st.button("Adicionar Intervalo", key="add_lito", use_container_width=True,
                                         type="primary"):
                                if base <= topo:
                                    st.warning("⚠ A Base deve ser maior que o Topo!")
                                else:
                                    nova_linha = pd.DataFrame({
                                        "Topo (m)": [topo],
                                        "Base (m)": [base],
                                        "Litologia": [litologia],
                                        "So (psi)": [so_lito]
                                    })

                                    st.session_state.dados_lito = pd.concat(
                                        [st.session_state.dados_lito, nova_linha],
                                        ignore_index=True
                                    )

                            st.markdown("---")
                            st.markdown("### Intervalos Inseridos")

                            # Botão limpar tudo
                            if st.button("Limpar tudo", key="clear_lito", use_container_width=True, type="primary"):
                                st.session_state.dados_lito = pd.DataFrame({
                                    "Topo (m)": [],
                                    "Base (m)": [],
                                    "Litologia": [],
                                    "So (psi)": []
                                })

                            # Exibe tabela
                            st.dataframe(
                                st.session_state.dados_lito,
                                use_container_width=True,
                                hide_index=True
                            )

                            # Botão para finalizar inserção
                            if st.button("Inserir valores", type="primary", use_container_width=True):
                                st.rerun()

                        # ABA CRITÉRIO DE FALHA
                        with tb[0]:
                            c1, c2, c3 = st.columns((0.8, 1, 1))
                            #ENTRADA DE DADOS
                            with c1:
                                with ((st.container(border=True))):
                                    with st.expander("Entrada de Dados", expanded=True):
                                        st.markdown('### Entrada de Dados')
                                        if "ts" not in st.session_state:
                                            st.session_state.ts = False

                                        if st.button("Considerar Litologia das Formações", use_container_width=True,
                                                     type="primary", key="lito_button"):
                                            coe_lito()

                                        with st.form("jop", border=False):
                                            col1, col2 = st.columns((0.8, 1))
                                            with col1:
                                                st.number_input('Ângulo de fricção (Φ)', key='phi', value=30)
                                                st.number_input('Limite de falha por tração', key='lft', value=0,
                                                                disabled=True)
                                                st.number_input('Profundidade (m)', key='m', value=893.00,
                                                                format="%.2f")
                                                st.number_input('Peso do fluido (lb/gal)', key='ppg', value=9.,
                                                                format="%.2f", step=0.5)
                                            st.selectbox('Método de cálculo do UCS', ['Lacy', 'Mechpro'], key='ucs',
                                                         index=1)
                                            st.selectbox("Profundidade", ['TVD', 'MD'], key="t_prof")

                                            if st.session_state.t_prof == "TVD":
                                                st.session_state.y = df_tvp['Profundidade (m)']
                                                prof_final = st.session_state.y_max_pp
                                            else:
                                                st.session_state.y = df_tvp['MD']
                                                prof_final = df_tvp['MD'].max() + 100

                                            profundidade_proxima = st.session_state.y.loc[
                                                (st.session_state.y - st.session_state.m).abs().idxmin()
                                            ]

                                            if not st.session_state.spp:
                                                gpo = df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                                            else:
                                                gpo = df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)']

                                            df_tvp.insert(
                                                loc=4,
                                                column='Gradiente de Pressão de Poros (lb/gal)',
                                                value=gpo
                                            )

                                            if "df_interp" in st.session_state:
                                                df_tvp["Inc"] = np.interp(st.session_state.y,
                                                                          st.session_state.df_interp["Profundidade"],
                                                                          st.session_state.df_interp["Inc (°)"])
                                                df_tvp["Azi"] = np.interp(st.session_state.y,
                                                                          st.session_state.df_interp["Profundidade"],
                                                                          st.session_state.df_interp["Azi (°)"])

                                            else:
                                                if "Inc" not in df_tvp.columns:
                                                    df_tvp.insert(loc=5, column="Inc", value=0)
                                                if "Azi" not in df_tvp.columns:
                                                    df_tvp.insert(loc=6, column="Azi", value=0)

                                            if st.form_submit_button("Gerar Janela Operacional", use_container_width=True,
                                                                     type='primary'):
                                                st.session_state.ts = True

                                    # ZONAS DE PERDA
                                    with st.expander('Zonas de perda', expanded=False):
                                        with st.form('los_form', border=False):
                                            st.markdown("### Perdas de Circulação")
                                            z = pd.DataFrame({
                                                'Profundidade da zona de perda (m)': [0.0],
                                                'Peso do fluido (lb/gal)': [0.0]
                                            })
                                            if 'zona2' not in st.session_state:
                                                st.session_state.zona2 = []
                                            cols_to_check = ["Profundidade da zona de perda (m)",
                                                             "Peso do fluido (lb/gal)"]
                                            st.session_state.edited_z2 = st.data_editor(z, hide_index=True,
                                                                                        num_rows='dynamic',
                                                                                        key='edited2')
                                            if st.form_submit_button('Inserir Zonas de Perda', use_container_width=True,
                                                                     type='primary'):
                                                st.session_state.zona2.clear()
                                                if (st.session_state.edited_z2[cols_to_check] != 0).all(axis=1).any():
                                                    for i, value in enumerate(
                                                            st.session_state.edited_z2[
                                                                "Profundidade da zona de perda (m)"]):
                                                        st.session_state.zona2.append(
                                                            [value, st.session_state.edited_z2[
                                                                "Peso do fluido (lb/gal)"][i]])

                                    # PROFUNDIDADE DAS PRISÕES DE COLUNA
                                    with st.expander('Prisões de Coluna', expanded=False):
                                        with st.form('prisoes_coluna_form', clear_on_submit=False, border=False):
                                            st.markdown("### Prisões de Coluna (TVD)")

                                            # DataFrame inicial
                                            z_prisao = pd.DataFrame({
                                                'Profundidade da prisão (m)': [0.0]
                                            })

                                            # Editor de dados dinâmico
                                            edited_prisoes = st.data_editor(
                                                z_prisao,
                                                hide_index=True,
                                                num_rows='dynamic',
                                                key='edited_prisoes_coluna'
                                            )

                                            # Botão de envio
                                            submitted_prisoes = st.form_submit_button(
                                                'Inserir Prisões de Coluna',
                                                use_container_width=True,
                                                type='primary'
                                            )

                                            if submitted_prisoes:
                                                # Garante que a coluna exista
                                                if 'Profundidade da prisão (m)' not in edited_prisoes.columns:
                                                    edited_prisoes['Profundidade da prisão (m)'] = 0.0

                                                # Filtra apenas profundidades válidas
                                                prisoes_df = edited_prisoes[
                                                    edited_prisoes['Profundidade da prisão (m)'] > 0
                                                    ].copy()

                                                # Converte tipo
                                                prisoes_df['Profundidade da prisão (m)'] = prisoes_df[
                                                    'Profundidade da prisão (m)'
                                                ].astype(float)

                                                # Salva no session_state
                                                st.session_state.prisoes_coluna_df = prisoes_df

                                    # ===== Cálculos iniciais =====
                                    if st.session_state.ts:
                                        df_tvp.insert(
                                            loc=7,
                                            column='DTS',
                                            value=round(((1 / (((0.8042 * (
                                                    ((1000000 / df_tvp['Perfil sônico (µs/pé)']) / 3.281) / 1000)) -
                                                          0.8559) * 1000)) * 1000000) / 3.281,2)
                                        )

                                        df_tvp.insert(
                                            loc=8,
                                            column='Poisson',
                                            value=round((0.5 * (df_tvp['DTS'] / df_tvp['Perfil sônico (µs/pé)']) ** 2 - 1) / (
                                                    (df_tvp['DTS'] / df_tvp['Perfil sônico (µs/pé)']) ** 2 - 1),2)
                                        )
                                        if st.session_state.ucs == 'Lacy':
                                            df_tvp.insert(
                                                loc=9,
                                                column='G dinam (MMpsi)',
                                                value=round((1.34 * 10 ** 10 * df_tvp['Perfil de densidade (g/cm³)'] / (
                                                        df_tvp['DTS'] ** 2)) / 10 ** 6,2)
                                            )
                                            df_tvp.insert(
                                                loc=10,
                                                column='E dinâmico (MMpsi)',
                                                value=round(2 * df_tvp['G dinam (MMpsi)'] * (1 + df_tvp['Poisson']),2)
                                            )
                                            df_tvp.insert(
                                                loc=11,
                                                column='E estático (MMpsi)',
                                                value=round(0.018 * (df_tvp['E dinâmico (MMpsi)'] ** 2) + 0.422 * df_tvp[
                                                    'E dinâmico (MMpsi)'],2)
                                            )
                                            df_tvp.insert(
                                                loc=12,
                                                column='UCS (psi)',
                                                value=round((0.2787 * df_tvp['E estático (MMpsi)'] ** 2 + 2.458 * df_tvp[
                                                    'E estático (MMpsi)']) * 1000,2)
                                            )
                                        else:
                                            df_tvp.insert(
                                                loc=9,
                                                column='Vsh',
                                                value=0.5
                                            )
                                            df_tvp.insert(
                                                loc=10,
                                                column='UCS (psi)',
                                                value=round(145.0377 * 1.9e-20 * (
                                                        1000 * df_tvp['Perfil de densidade (g/cm³)']) ** 2 * (
                                                              304800 / df_tvp['Perfil sônico (µs/pé)']) ** 4 *
                                                      ((1 + df_tvp['Poisson']) / (1 - df_tvp['Poisson'])) ** 2 * (
                                                              1 - 2 * df_tvp['Poisson']) * (
                                                              1 + 0.79 * df_tvp['Vsh']),2)
                                            )
                                        # Calcula So original
                                        #PRECISA SER EM RADIANOS ?
                                        df_tvp["So (psi)"] = (df_tvp['UCS (psi)'] *
                                                              (1 - np.sin(np.radians(st.session_state.phi)))) / (2 * np.cos(np.radians(st.session_state.phi)))

                                        # Se existir dados de litologia, substitui intervalos
                                        if "dados_lito" in st.session_state and not st.session_state.dados_lito.empty:

                                            lito_df = st.session_state.dados_lito.copy()

                                            # Copia coluna original
                                            so = df_tvp["So (psi)"].copy()

                                            # Aplica intervalos topo–base
                                            for _, row in lito_df.iterrows():
                                                topo = row["Topo (m)"]
                                                base = row["Base (m)"]
                                                so_val = row["So (psi)"]

                                                mascara = (df_tvp["Profundidade (m)"] >= topo) & (
                                                            df_tvp["Profundidade (m)"] < base)
                                                so.loc[mascara] = so_val

                                            df_tvp["So (psi)"] = so


                                        if "rel_hor_df" in st.session_state and not st.session_state.rel_hor_df.empty:
                                            df_tvp = pd.merge_asof(
                                                df_tvp.sort_values("Profundidade (m)"),
                                                st.session_state.rel_hor_df.sort_values("Profundidade (m)"),
                                                on="Profundidade (m)",
                                                direction="backward"
                                            )

                                            rel_sh = df_tvp["SH% Sobrecarga"].fillna(0.61)
                                            rel_shmin = df_tvp["Sh% Sobrecarga"].fillna(0.6)

                                            r1 = rel_sh * df_tvp['Gradiente de Sobrecarga (lb/gal)'] * 0.1704 * df_tvp["Profundidade (m)"]
                                            r2 = rel_shmin * df_tvp['Gradiente de Sobrecarga (lb/gal)'] * 0.1704 * df_tvp["Profundidade (m)"]
                                        else:
                                            r1 = 0.61 * df_tvp['Gradiente de Sobrecarga (lb/gal)'] * 0.1704 * df_tvp["Profundidade (m)"]
                                            r2 = 0.6 * df_tvp['Gradiente de Sobrecarga (lb/gal)'] * 0.1704 * df_tvp["Profundidade (m)"]

                                        # Inserindo a coluna no DataFrame
                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('So (psi)') + 1,
                                            column='SH (psi)',
                                            value=round(r1,2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('SH (psi)') + 1,
                                            column='Direção SH',
                                            value=dir_H
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Direção SH') + 1,
                                            column='Sh (psi)',
                                            value=round(r2,2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Sh (psi)') + 1,
                                            column='Direção Sh',
                                            value=dir_h
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Direção Sh') + 1,
                                            column='Sv (psi)',
                                            value=df_tvp['Gradiente de Sobrecarga (lb/gal)'] * 0.1704 * df_tvp['Profundidade (m)']
                                        )

                                        #Eixos invertidos, por isso foi somado 90°

                                        lxxl = np.cos(np.radians(df_tvp['Azi']- df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc']))
                                        lyxl = -np.sin(np.radians(df_tvp['Azi']- df_tvp['Direção SH']))
                                        lzxl = np.cos(np.radians(df_tvp['Azi']- df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc']))

                                        lxyl = np.sin(np.radians(df_tvp['Azi']- df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc']))
                                        lyyl = np.cos(np.radians(df_tvp['Azi']- df_tvp['Direção SH']))
                                        lzyl = np.sin(np.radians(df_tvp['Azi']- df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc']))

                                        lxzl = -np.sin(np.radians(df_tvp['Inc']))
                                        lyzl = 0
                                        lzzl = np.cos(np.radians(df_tvp['Inc']))

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Sv (psi)') + 1,
                                            column='τxy',
                                            value=round((lxxl * lyxl * df_tvp['SH (psi)']) + (lxyl * lyyl * df_tvp['Sh (psi)']) + (lxzl * lyzl * df_tvp['Sv (psi)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('τxy') + 1,
                                            column='τyz',
                                            value=round((lyxl * lzxl * df_tvp['SH (psi)']) + (lyyl * lzyl * df_tvp['Sh (psi)']) + (lyzl * lzzl * df_tvp['Sv (psi)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('τyz') + 1,
                                            column='τzx',
                                            value=round((lzxl * lxxl * df_tvp['SH (psi)']) + (lzyl * lxyl * df_tvp['Sh (psi)']) + (lzzl * lxzl * df_tvp['Sv (psi)']),2)
                                        )

                                        thetaA = np.degrees(np.arctan(df_tvp['τyz'] / df_tvp['τzx']))
                                        thetaA[df_tvp['τzx'] == 0] = np.nan

                                        df_tvp.insert(
                                            df_tvp.columns.get_loc('τzx') + 1,
                                            'θA (°)',
                                            thetaA.ffill().fillna(0)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('θA (°)') + 1,
                                            column='θB (°)',
                                            value=df_tvp['θA (°)'] + 90
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('θB (°)') + 1,
                                            column='τθa',
                                            value=round(2 * (df_tvp['τyz'] * np.cos(np.radians(df_tvp['θA (°)'])) - df_tvp[
                                                'τzx'] * np.sin(np.radians(df_tvp['θA (°)']))),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('τθa') + 1,
                                            column='Pw',
                                            value=round(st.session_state.ppg * 0.1704 * df_tvp['Profundidade (m)'],2)
                                        )
                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Pw') + 1,
                                            column='rw',
                                            value=st.session_state.rw
                                        )
                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('rw') + 1,
                                            column='r',
                                            value=st.session_state.r
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('r') + 1,
                                            column='σx',
                                            value=round(((lxxl**2)*df_tvp['SH (psi)']) + ((lxyl**2)*df_tvp['Sh (psi)']) + ((lxzl**2)*df_tvp['Sv (psi)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σx') + 1,
                                            column='σy',
                                            value=round(((lyxl**2)*df_tvp['SH (psi)']) + ((lyyl**2)*df_tvp['Sh (psi)']) + ((lyzl**2)*df_tvp['Sv (psi)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σy') + 1,
                                            column='σz',
                                            value=round(((lzxl**2)*df_tvp['SH (psi)']) + ((lzyl**2)*df_tvp['Sh (psi)']) + ((lzzl**2)*df_tvp['Sv (psi)']),2)
                                        )

                                        C1 = (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)
                                        C2 = (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4)

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σz') + 1,
                                            column='σr',
                                            value=round((((((df_tvp['σx'] + df_tvp['σy']) / 2) * ( 1 - C1)) + (((df_tvp['σx'] + df_tvp['σy']) / 2)*(1 +
                                                (3 * C2) - (4 * C1))*(np.cos(np.radians(2*df_tvp['θA (°)']))))+((df_tvp['τxy'])*((1 + (3 * C2) - (4 *
                                                C1)))*(np.sin(np.radians(2*df_tvp['θA (°)'])))) + (df_tvp['Pw']*C1)))/(0.1704* df_tvp['Profundidade (m)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σr') + 1,
                                            column='σθA',
                                            value=round((((df_tvp['σx'] + df_tvp['σy']) / 2)*(1+C1)-(((df_tvp['σx'] - df_tvp['σy']) / 2)*(1+(3*C2))*(np.cos(
                                                np.radians(2*df_tvp['θA (°)']))))-((df_tvp['τxy'])*((1 + (3 * C2) - (4 * C1)))*(np.sin(np.radians(2*df_tvp['θA (°)']))))-
                                                   (df_tvp['Pw']*C1))/(0.1704* df_tvp['Profundidade (m)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σθA') + 1,
                                            column='σθB',
                                            value=round((((df_tvp['σx'] + df_tvp['σy']) / 2)*(1+C1)-(((df_tvp['σx'] - df_tvp['σy']) / 2)*(1+(3*C2))*(np.cos(
                                                np.radians(2*df_tvp['θB (°)']))))-((df_tvp['τxy'])*((1 + (3 * C2) - (4 * C1)))*(np.sin(np.radians(2*df_tvp['θB (°)']))))-
                                                   (df_tvp['Pw']*C1))/(0.1704* df_tvp['Profundidade (m)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σθB') + 1,
                                            column='σa',
                                            value=round(((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc'])))**2 *
                                                   df_tvp['SH (psi)'] + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                   np.sin(np.radians(df_tvp['Inc'])))**2 * df_tvp['Sh (psi)'] +
                                                   (np.cos(np.radians(df_tvp['Inc'])))**2 * df_tvp['Gradiente de Sobrecarga (lb/gal)']),2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σa') + 1,
                                            column='σr efetivo (psi)',
                                            value=round((df_tvp['σr'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σr efetivo (psi)') + 1,
                                            column='σθA efetivo (psi)',
                                            value=round((df_tvp['σθA'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('σθA efetivo (psi)') + 1,
                                            column='σθB efetivo (psi)',
                                            value=round((df_tvp['σθB'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)
                                        )

                                        # ==== Pw que zera cada tensão efetiva ====
                                        k = 0.1704 * df_tvp['Profundidade (m)']
                                        C1 = (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)

                                        coef_ok = np.where(C1 != 0, C1, np.nan)

                                        sigma_r_sem_pw = df_tvp['σr'] - (C1 / k) * df_tvp['Pw']
                                        sigma_ta_sem_pw = df_tvp['σθA'] + (C1 / k) * df_tvp['Pw']
                                        sigma_tb_sem_pw = df_tvp['σθB'] + (C1 / k) * df_tvp['Pw']

                                        Pp = df_tvp['Gradiente de Pressão de Poros (lb/gal)']

                                        df_tvp['Tração Inferior'] = np.round(
                                            (Pp - sigma_r_sem_pw) / coef_ok,
                                            2
                                        )

                                        df_tvp['Tração Superior (σθA)'] = np.round(
                                            (sigma_ta_sem_pw - Pp) / coef_ok,
                                            2
                                        )

                                        df_tvp['Tração Superior (σθB)'] = np.round(
                                            (sigma_tb_sem_pw - Pp) / coef_ok,
                                            2
                                        )

                                        # ================== Pw na falha por compressão ==================
                                        phi_rad = np.radians(st.session_state.phi)
                                        m = np.tan(phi_rad)

                                        Kdepth = 0.1704 * df_tvp['Profundidade (m)']
                                        Pp_grad = df_tvp['Gradiente de Pressão de Poros (lb/gal)']
                                        Pp_psi = Pp_grad * Kdepth
                                        S0 = df_tvp['So (psi)']
                                        def sigma_r_sem_pw(theta_deg):
                                            th = np.radians(2 * theta_deg)
                                            return (
                                                    ((df_tvp['σx'] + df_tvp['σy']) / 2) * (1 - C1)
                                                    + ((df_tvp['σx'] - df_tvp['σy']) / 2) * (
                                                                1 + 3 * C2 - 4 * C1) * np.cos(th)
                                                    + df_tvp['τxy'] * (1 + 3 * C2 - 4 * C1) * np.sin(th)
                                            )
                                        def sigma_t_sem_pw(theta_deg):
                                            th = np.radians(2 * theta_deg)
                                            return (
                                                    ((df_tvp['σx'] + df_tvp['σy']) / 2) * (1 + C1)
                                                    - ((df_tvp['σx'] - df_tvp['σy']) / 2) * (1 + 3 * C2) * np.cos(th)
                                                    - df_tvp['τxy'] * (1 + 3 * C2 - 4 * C1) * np.sin(th)
                                            )
                                        def calcular_pesos_tangencia(theta_deg):
                                            Ar = sigma_r_sem_pw(theta_deg)
                                            At = sigma_t_sem_pw(theta_deg)

                                            centro = 0.5 * (At + Ar) - Pp_psi
                                            raio_sem_pw = 0.5 * (At - Ar)

                                            distancia_reta = np.abs(m * centro + S0) / np.sqrt(m ** 2 + 1)

                                            den = C1 * Kdepth
                                            den = np.where(den != 0, den, np.nan)

                                            peso_1 = (raio_sem_pw - distancia_reta) / den
                                            peso_2 = (raio_sem_pw + distancia_reta) / den

                                            peso_inf = np.minimum(peso_1, peso_2)
                                            peso_sup = np.maximum(peso_1, peso_2)

                                            return peso_inf, peso_sup
                                        Pw_A_inf, Pw_A_sup = calcular_pesos_tangencia(df_tvp['θA (°)'])
                                        Pw_B_inf, Pw_B_sup = calcular_pesos_tangencia(df_tvp['θB (°)'])

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Tração Superior (σθB)') + 1,
                                            column='Comp Inferior σθA',
                                            value=np.round(Pw_A_inf, 2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Comp Inferior σθA') + 1,
                                            column='Comp Superior σθA',
                                            value=np.round(Pw_A_sup, 2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Comp Superior σθA') + 1,
                                            column='Comp Inferior σθB',
                                            value=np.round(Pw_B_inf, 2)
                                        )

                                        df_tvp.insert(
                                            loc=df_tvp.columns.get_loc('Comp Inferior σθB') + 1,
                                            column='Comp Superior σθB',
                                            value=np.round(Pw_B_sup, 2)
                                        )

                                        cols_tracao = [
                                            'Tração Inferior',
                                            'Tração Superior (σθA)',
                                            'Tração Superior (σθB)'
                                        ]

                                        cols_compressao = [
                                            'Comp Inferior σθA',
                                            'Comp Superior σθA',
                                            'Comp Inferior σθB',
                                            'Comp Superior σθB'
                                        ]

                                        df_tvp.loc[~mask_calculo_valido, cols_tracao + cols_compressao] = np.nan
                                        # ==================================================================
                                        with col2:
                                            opcao_tracao = st.radio(
                                                "Selecione o tipo de falha:",
                                                (
                                                    "Peso de Fluido Escolhido",
                                                    "Tração Inferior",
                                                    "Tração Superior σθA",
                                                    "Tração Superior σθB",
                                                    "Comp Inferior σθA",
                                                    "Comp Superior σθA",
                                                    "Comp Inferior σθB",
                                                    "Comp Superior σθB"
                                                ), key='op'
                                            )

                                            if opcao_tracao == "Peso de Fluido Escolhido":
                                                peso_fluido = st.session_state.ppg
                                            else:
                                                coluna_ref = 'Profundidade (m)' if st.session_state.t_prof == "TVD" else 'MD'
                                                linha = df_tvp.loc[df_tvp[coluna_ref] == profundidade_proxima].iloc[0]
                                                if opcao_tracao == "Tração Inferior":
                                                    peso_fluido = linha['Tração Inferior']
                                                elif opcao_tracao == "Tração Superior σθA":
                                                    peso_fluido = linha['Tração Superior (σθA)']
                                                elif opcao_tracao == "Tração Superior σθB":
                                                    peso_fluido = linha['Tração Superior (σθB)']
                                                elif opcao_tracao == "Comp Inferior σθA":
                                                    peso_fluido = linha['Comp Inferior σθA']
                                                elif opcao_tracao == "Comp Superior σθA":
                                                    peso_fluido = linha['Comp Superior σθA']
                                                elif opcao_tracao == "Comp Inferior σθB":
                                                    peso_fluido = linha['Comp Inferior σθB']
                                                elif opcao_tracao == "Comp Superior σθB":
                                                    peso_fluido = linha['Comp Superior σθB']

                                                # Atualiza Pw no dataframe
                                                df_tvp['Pw'] = peso_fluido*0.1704*df_tvp['Profundidade (m)']

                                                # ==== Recalcular todas as tensões com o novo Pw ====
                                                # σr
                                                df_tvp['σr'] = round((((((df_tvp['σx'] + df_tvp['σy']) / 2) * ( 1 - C1)) + (((df_tvp['σx'] + df_tvp['σy']) / 2)*(1 +
                                                (3 * C2) - (4 * C1))*(np.cos(np.radians(2*df_tvp['θA (°)']))))+((df_tvp['τxy'])*((1 + (3 * C2) - (4 *
                                                C1)))*(np.sin(np.radians(2*df_tvp['θA (°)'])))) + (df_tvp['Pw']*C1)))/(0.1704* df_tvp['Profundidade (m)']),2)

                                                # σθA
                                                df_tvp['σθA'] = round((((df_tvp['σx'] + df_tvp['σy']) / 2)*(1+C1)-(((df_tvp['σx'] - df_tvp['σy']) / 2)*(1+(3*C2))*(np.cos(
                                                np.radians(2*df_tvp['θA (°)']))))-((df_tvp['τxy'])*((1 + (3 * C2) - (4 * C1)))*(np.sin(np.radians(2*df_tvp['θA (°)']))))-
                                                   (df_tvp['Pw']*C1))/(0.1704* df_tvp['Profundidade (m)']),2)

                                                # σθB
                                                df_tvp['σθB'] = round((((df_tvp['σx'] + df_tvp['σy']) / 2)*(1+C1)-(((df_tvp['σx'] - df_tvp['σy']) / 2)*(1+(3*C2))*(np.cos(
                                                np.radians(2*df_tvp['θB (°)']))))-((df_tvp['τxy'])*((1 + (3 * C2) - (4 * C1)))*(np.sin(np.radians(2*df_tvp['θB (°)']))))-
                                                   (df_tvp['Pw']*C1))/(0.1704* df_tvp['Profundidade (m)']),2)

                                                # σa
                                                df_tvp['σa'] = ((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc'])))**2 *
                                                   df_tvp['SH (psi)'] + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                   np.sin(np.radians(df_tvp['Inc'])))**2 * df_tvp['Sh (psi)'] +
                                                   (np.cos(np.radians(df_tvp['Inc'])))**2 * df_tvp['Gradiente de Sobrecarga (lb/gal)'])

                                                # Recalcular tensões efetivas
                                                df_tvp['σr efetivo (psi)'] = round((df_tvp['σr'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)
                                                df_tvp['σθA efetivo (psi)'] = round((df_tvp['σθA'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)
                                                df_tvp['σθB efetivo (psi)'] = round((df_tvp['σθB'] - df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                  df_tvp['Profundidade (m)'],2)

                                            # Atualiza as variáveis para uso posterior
                                            linha = df_tvp.loc[st.session_state.y == profundidade_proxima].iloc[0]
                                            sr_ef = linha['σr efetivo (psi)']
                                            sta_ef = linha['σθA efetivo (psi)']
                                            stb_ef = linha['σθB efetivo (psi)']
                                            S0 = linha['So (psi)']

                                            phi_rad = np.radians(st.session_state.phi)
                                            t = np.tan(phi_rad)

                                            # Pontos A
                                            ra = abs(sr_ef - sta_ef) / 2
                                            Ca = (sr_ef + sta_ef) / 2
                                            Ra = abs(-np.radians(st.session_state.phi) * Ca - S0) / (
                                                np.sqrt(np.radians(st.session_state.phi) ** 2 + 1 ** 2))

                                            # Pontos B
                                            Rb = abs(sr_ef - stb_ef) / 2
                                            Cb = (sr_ef + stb_ef) / 2
                                            Ra = abs(-np.radians(st.session_state.phi) * Cb - S0) / (
                                                np.sqrt(np.radians(st.session_state.phi) ** 2 + 1 ** 2))

                                            df_tvp['Max Inferior'] = np.nan
                                            df_tvp['Min Superior'] = np.nan

                                            cols_max_inf = [
                                                'Gradiente de Pressão de Poros (lb/gal)',
                                                'Tração Inferior',
                                                'Comp Inferior σθA',
                                                'Comp Inferior σθB'
                                            ]

                                            cols_min_sup = [
                                                'Tração Superior (σθA)',
                                                'Tração Superior (σθB)',
                                                'Comp Superior σθA',
                                                'Comp Superior σθB'
                                            ]

                                            df_tvp.loc[mask_calculo_valido, 'Max Inferior'] = (
                                                df_tvp.loc[mask_calculo_valido, cols_max_inf].max(axis=1, skipna=True)
                                            )

                                            df_tvp.loc[mask_calculo_valido, 'Min Superior'] = (
                                                df_tvp.loc[mask_calculo_valido, cols_min_sup].min(axis=1, skipna=True)
                                            )

                                            st.session_state.df_tvp = df_tvp

                            def criterio_disponivel(df):
                                colunas = [
                                    'Tração Inferior',
                                    'Comp Inferior σθA',
                                    'Comp Inferior σθB',
                                    'Tração Superior (σθA)',
                                    'Tração Superior (σθB)',
                                    'Comp Superior σθA',
                                    'Comp Superior σθB'
                                ]
                                return all(c in df.columns for c in colunas)

                            # GRÁFICO - MOHR
                            with c2:
                                with st.container(border=True):
                                    with st.expander('Critério de Falha - Mohr Coulomb', expanded=True):
                                        def suavizar_somente_validos(x, y, mask_validos):
                                            x_num = pd.to_numeric(x, errors='coerce')
                                            y_num = pd.to_numeric(y, errors='coerce')

                                            saida = pd.Series(np.nan, index=y.index, dtype=float)

                                            mask = (
                                                    mask_validos
                                                    & x_num.notna()
                                                    & y_num.notna()
                                            )

                                            if mask.sum() >= 3:
                                                saida.loc[mask] = suavizar(x_num.loc[mask], y_num.loc[mask])
                                            else:
                                                saida.loc[mask] = y_num.loc[mask]

                                            return saida
                                        st.markdown('### Critério de Falha - Mohr Coulomb')
                                        if not criterio_disponivel(df_tvp):
                                            st.warning(
                                                "⚠️ Calcule as tensões antes de avaliar o critério de falha.")

                                        if criterio_disponivel(df_tvp):
                                            df_suav = pd.DataFrame()
                                            df_suav['Profundidade (m)'] = df_tvp['Profundidade (m)']
                                            df_suav['MD'] = df_tvp['MD']
                                            df_suav['Gradiente de Sobrecarga (lb/gal)'] = df_tvp[
                                                'Gradiente de Sobrecarga (lb/gal)']
                                            df_suav['Gradiente de Pressão de Poros (lb/gal)'] = df_tvp[
                                                'Gradiente de Pressão de Poros (lb/gal)']
                                            df_suav['Tração Inferior'] = suavizar(df_tvp['Profundidade (m)'],
                                                                                  df_tvp['Tração Inferior'])
                                            df_suav['Comp Inferior σθA'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Comp Inferior σθA'],
                                                mask_calculo_valido
                                            )

                                            df_suav['Comp Inferior σθB'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Comp Inferior σθB'],
                                                mask_calculo_valido
                                            )

                                            df_suav['Tração Superior (σθA)'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Tração Superior (σθA)'],
                                                mask_calculo_valido
                                            )

                                            df_suav['Tração Superior (σθB)'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Tração Superior (σθB)'],
                                                mask_calculo_valido
                                            )

                                            df_suav['Comp Superior σθA'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Comp Superior σθA'],
                                                mask_calculo_valido
                                            )

                                            df_suav['Comp Superior σθB'] = suavizar_somente_validos(
                                                df_tvp['Profundidade (m)'],
                                                df_tvp['Comp Superior σθB'],
                                                mask_calculo_valido
                                            )
                                            df_suav['Max Inferior'] = np.nan
                                            df_suav['Min Superior'] = np.nan

                                            df_suav.loc[mask_calculo_valido, 'Max Inferior'] = (
                                                df_suav.loc[mask_calculo_valido, [
                                                    'Gradiente de Pressão de Poros (lb/gal)',
                                                    'Tração Inferior',
                                                    'Comp Inferior σθA',
                                                    'Comp Inferior σθB'
                                                ]].max(axis=1, skipna=True)
                                            )

                                            df_suav.loc[mask_calculo_valido, 'Min Superior'] = (
                                                df_suav.loc[mask_calculo_valido, [
                                                    'Tração Superior (σθA)',
                                                    'Tração Superior (σθB)',
                                                    'Comp Superior σθA',
                                                    'Comp Superior σθB'
                                                ]].min(axis=1, skipna=True)
                                            )
                                            st.session_state.df_suav = df_suav

                                            colu1, colu2, colu3 = st.columns(3)
                                            with colu1:
                                                if opcao_tracao == "Peso de Fluido Escolhido":
                                                    linha = df_tvp.loc[st.session_state.y == profundidade_proxima].iloc[
                                                        0]

                                                    # Limites da Janela Operacional
                                                    x_max_inf = np.asarray(
                                                        df_suav['Max Inferior'] if st.session_state.suav_max_inf else
                                                        df_tvp['Max Inferior'],
                                                        dtype=float
                                                    )

                                                    x_min_sup = np.asarray(
                                                        df_suav['Min Superior'] if st.session_state.suav_min_sup else
                                                        df_tvp['Min Superior'],
                                                        dtype=float
                                                    )

                                                    # Fator de segurança
                                                    fs = float(st.session_state.fs)

                                                    x_max_inf = pd.Series(
                                                        df_tvp['Max Inferior'] if st.session_state.suav_max_inf else
                                                        df_tvp['Max Inferior'],
                                                        index=df_tvp.index,
                                                        dtype=float
                                                    )

                                                    x_min_sup = pd.Series(
                                                        df_tvp['Min Superior'] if st.session_state.suav_min_sup else
                                                        df_tvp['Min Superior'],
                                                        index=df_tvp.index,
                                                        dtype=float
                                                    )

                                                    fs = float(st.session_state.fs)

                                                    x_fs_base_inf = x_max_inf + fs
                                                    x_fs_inf = pd.Series(np.nan, index=df_tvp.index, dtype=float)

                                                    mask_fs = x_fs_base_inf.notna()

                                                    x_fs_inf.loc[mask_fs] = np.maximum.accumulate(
                                                        x_fs_base_inf.loc[mask_fs].to_numpy()
                                                    )

                                                    idx_linha = linha.name

                                                    max_inferior = x_fs_inf.loc[idx_linha]
                                                    min_superior = x_min_sup.loc[idx_linha] - fs

                                                    if pd.isna(max_inferior) or pd.isna(min_superior):
                                                        st.info(
                                                            "A profundidade selecionada está no trecho extrapolado ou sem sônico válido. "
                                                            "A janela operacional e o fator de segurança não serão avaliados nesse ponto."
                                                        )
                                                    else:
                                                        if max_inferior < peso_fluido < min_superior:
                                                            st.markdown(
                                                                """
                                                                <div style="
                                                                    display: flex;
                                                                    justify-content: center;
                                                                    margin-top: 0px;
                                                                ">
                                                                    <div style="
                                                                        color: green;
                                                                        font-weight: bold;
                                                                        border: 2px solid black;
                                                                        border-radius: 10px;
                                                                        padding: 10px 10px;
                                                                    ">
                                                                        Poço Estável
                                                                    </div>
                                                                </div>
                                                                """,
                                                                unsafe_allow_html=True
                                                            )
                                                        else:
                                                            st.markdown(
                                                                """
                                                                <div style="
                                                                    display: flex;
                                                                    justify-content: center;
                                                                    margin-top: 3px;
                                                                ">
                                                                    <div style="
                                                                        color: red;
                                                                        font-weight: bold;
                                                                        border: 2px solid black;
                                                                        border-radius: 10px;
                                                                        padding: 10px 10px;
                                                                    ">
                                                                        Poço Instável
                                                                    </div>
                                                                </div>
                                                                """,
                                                                unsafe_allow_html=True
                                                            )

                                            mapa_colunas_falha = {
                                                "Tração Inferior": "Tração Inferior",
                                                "Tração Superior σθA": "Tração Superior (σθA)",
                                                "Tração Superior σθB": "Tração Superior (σθB)",
                                                "Comp Inferior σθA": "Comp Inferior σθA",
                                                "Comp Superior σθA": "Comp Superior σθA",
                                                "Comp Inferior σθB": "Comp Inferior σθB",
                                                "Comp Superior σθB": "Comp Superior σθB",
                                            }
                                            def valor_na_curva(df_plot, coluna, profundidade):
                                                base = df_plot[["Profundidade (m)", coluna]].dropna().sort_values(
                                                    "Profundidade (m)")

                                                if base.empty:
                                                    return np.nan

                                                return np.interp(
                                                    profundidade,
                                                    base["Profundidade (m)"],
                                                    base[coluna]
                                                )
                                            with colu2:
                                                titulo_peso = (
                                                    "Peso do Fluido:"
                                                    if opcao_tracao == "Peso de Fluido Escolhido"
                                                    else f"Falha por {opcao_tracao.lower()}"
                                                )

                                                coluna_ponto = mapa_colunas_falha.get(opcao_tracao)

                                                if coluna_ponto is not None and coluna_ponto in df_tvp.columns:
                                                    peso_card = valor_na_curva(
                                                        df_tvp,
                                                        coluna_ponto,
                                                        profundidade_proxima
                                                    )
                                                else:
                                                    peso_card = peso_fluido

                                                if pd.isna(peso_card):
                                                    peso_card = peso_fluido

                                                st.markdown(
                                                    f"""
                                                    <div style="
                                                        display: flex;
                                                        justify-content: center;
                                                        margin-top: 0px;
                                                    ">
                                                        <div style="
                                                            color: black;
                                                            font-weight: bold;
                                                            border: 2px solid black;
                                                            border-radius: 10px;
                                                            padding: 6px 10px;
                                                            text-align: center;
                                                            line-height: 1.2;
                                                            font-size: 13px;
                                                            min-width: 200px;
                                                        ">
                                                            {titulo_peso}<br>
                                                            <span style="color: red; font-size: 16px;">{float(peso_card):.2f}</span> lb/gal
                                                        </div>
                                                    </div>
                                                    """,
                                                    unsafe_allow_html=True
                                                )

                                            centro_A = (sr_ef + sta_ef) / 2
                                            raio_A = abs(sta_ef - sr_ef) / 2
                                            centro_B = (sr_ef + stb_ef) / 2
                                            raio_B = abs(stb_ef - sr_ef) / 2

                                            ang = np.linspace(0, np.pi, 200)
                                            x_A = centro_A + raio_A * np.cos(ang)
                                            y_A = raio_A * np.sin(ang)
                                            x_B = centro_B + raio_B * np.cos(ang)
                                            y_B = raio_B * np.sin(ang)

                                            # Figura
                                            fig = go.Figure()
                                            if raio_A >= raio_B:
                                                fig.add_trace(
                                                    go.Scatter(x=x_A, y=y_A, fill='toself',
                                                               fillcolor='lightblue',
                                                               line=dict(color='black', width=3),
                                                               name='Círculo A'))
                                                fig.add_trace(
                                                    go.Scatter(x=x_B, y=y_B, fill='toself', fillcolor='gold',
                                                               line=dict(color='black', width=3),
                                                               name='Círculo B'))
                                            else:
                                                fig.add_trace(
                                                    go.Scatter(x=x_B, y=y_B, fill='toself', fillcolor='gold',
                                                               line=dict(color='black', width=3),
                                                               name='Círculo B'))
                                                fig.add_trace(
                                                    go.Scatter(x=x_A, y=y_A, fill='toself',
                                                               fillcolor='lightblue',
                                                               line=dict(color='black', width=3),
                                                               name='Círculo A'))

                                            # Pontos de tensões
                                            fig.add_trace(
                                                go.Scatter(x=[sr_ef], y=[0], mode='markers+text', text=["σ'r"],
                                                           textposition='bottom center',
                                                           marker=dict(color='black', size=8),
                                                           showlegend=False))
                                            fig.add_trace(
                                                go.Scatter(x=[sta_ef], y=[0], mode='markers+text',
                                                           text=["σ'θ A"],
                                                           textposition='bottom center',
                                                           marker=dict(color='black', size=8),
                                                           showlegend=False))
                                            fig.add_trace(
                                                go.Scatter(x=[stb_ef], y=[0], mode='markers+text',
                                                           text=["σ'θ B"],
                                                           textposition='bottom center',
                                                           marker=dict(color='black', size=8),
                                                           showlegend=False))

                                            # Rótulos
                                            fig.add_trace(
                                                go.Scatter(x=[centro_A], y=[raio_A / 2], mode='text',
                                                           text=['A'],
                                                           textposition="middle center",
                                                           textfont=dict(size=14, color='black'),
                                                           showlegend=False))
                                            fig.add_trace(
                                                go.Scatter(x=[centro_B], y=[raio_B / 2], mode='text',
                                                           text=['B'],
                                                           textposition="middle center",
                                                           textfont=dict(size=14, color='black'),
                                                           showlegend=False))

                                            # Linha de critério de falha por tração
                                            y_tracao_inicio = 0
                                            y_tracao_fim = df_tvp.loc[
                                                st.session_state.y == profundidade_proxima, 'So (psi)'
                                            ].values[0]
                                            # Limites do gráfico
                                            x_min = min(sr_ef, sta_ef, stb_ef) - 0.1 * max(raio_A, raio_B)
                                            x_max = max(sr_ef, sta_ef, stb_ef) + 0.1 * max(raio_A, raio_B)

                                            fig.add_shape(
                                                type="line", x0=0, y0=y_tracao_inicio,
                                                x1=0, y1=y_tracao_fim,
                                                line=dict(color="red", width=3),
                                                name='Critério de Falha por Tração',
                                                showlegend=True
                                            )

                                            # Linha de critério de falha por compressão, começa onde termina a linha vermelha
                                            x_compressao_inicio = 0
                                            y_compressao_inicio = y_tracao_fim  # toca a linha de tração
                                            phi_rad = np.radians(st.session_state.phi)
                                            m = np.tan(phi_rad)

                                            x_reta = np.linspace(x_compressao_inicio, x_max, 100)
                                            y_reta = m * (x_reta - x_compressao_inicio) + y_compressao_inicio

                                            fig.add_trace(go.Scatter(
                                                x=x_reta,
                                                y=y_reta,
                                                mode='lines',
                                                line=dict(color='green', width=3),
                                                name='Critério de Falha por Compressão',
                                                showlegend=True
                                            ))

                                            def projecao_ponto_na_reta(px, py, m, x0, y0):
                                                # reta: y = m(x - x0) + y0
                                                # forma geral: mx - y + (y0 - m*x0) = 0
                                                a = m
                                                b = -1
                                                c = y0 - m * x0

                                                denom = a * a + b * b
                                                x_proj = px - a * (a * px + b * py + c) / denom
                                                y_proj = py - b * (a * px + b * py + c) / denom
                                                return x_proj, y_proj

                                            def intersecao_circulo_reta(centro, raio, m, x0, y0, tol=1e-9):
                                                xc, yc = centro

                                                # reta parametrizada:
                                                # x = x0 + t
                                                # y = y0 + m*t

                                                a = 1 + m ** 2
                                                b = 2 * ((x0 - xc) + m * (y0 - yc))
                                                c = (x0 - xc) ** 2 + (y0 - yc) ** 2 - raio ** 2

                                                delta = b ** 2 - 4 * a * c

                                                if delta < -tol:
                                                    return []

                                                if abs(delta) <= tol:
                                                    t = -b / (2 * a)
                                                    x = x0 + t
                                                    y = y0 + m * t
                                                    return [(x, y)]

                                                sqrt_delta = math.sqrt(delta)

                                                t1 = (-b + sqrt_delta) / (2 * a)
                                                t2 = (-b - sqrt_delta) / (2 * a)

                                                p1 = (x0 + t1, y0 + m * t1)
                                                p2 = (x0 + t2, y0 + m * t2)

                                                return [p1, p2]

                                            # Parâmetros da reta
                                            m = np.tan(np.radians(st.session_state.phi))
                                            x0, y0 = x_compressao_inicio, y_compressao_inicio

                                            # Interseções com A e B (pega o ponto de maior x se existir)
                                            st.session_state.pop('xa', None)
                                            st.session_state.pop('ya', None)
                                            st.session_state.pop('xb', None)
                                            st.session_state.pop('yb', None)

                                            # Pontos de tangência com A e B
                                            st.session_state.pop('xa', None)
                                            st.session_state.pop('ya', None)
                                            st.session_state.pop('xb', None)
                                            st.session_state.pop('yb', None)

                                            for nome, centro_x, raio in [('A', centro_A, raio_A),
                                                                         ('B', centro_B, raio_B)]:
                                                x, y = projecao_ponto_na_reta(centro_x, 0.0, m, x0, y0)

                                                st.session_state[f'x{nome.lower()}'] = x
                                                st.session_state[f'y{nome.lower()}'] = y

                                            # Adiciona pontos no gráfico, se aplicável
                                            if st.session_state.op in ['Comp Inferior σθA',
                                                                       'Comp Superior σθA'] and 'xa' in st.session_state:
                                                fig.add_trace(go.Scatter(
                                                    x=[st.session_state.xa], y=[st.session_state.ya],
                                                    mode='markers',
                                                    marker=dict(color='red', size=10, symbol='circle'),
                                                    name='Falha por Compressão em A'
                                                ))

                                            if st.session_state.op in ['Comp Inferior σθB',
                                                                       'Comp Superior σθB'] and 'xb' in st.session_state:
                                                fig.add_trace(go.Scatter(
                                                    x=[st.session_state.xb], y=[st.session_state.yb],
                                                    mode='markers',
                                                    marker=dict(color='red', size=10, symbol='circle'),
                                                    name='Falha por Compressão em B'
                                                ))

                                            fig.update_layout(
                                                xaxis_title="Tensão normal σ (psi)",
                                                yaxis_title="Tensão cisalhante τ (psi)",
                                                xaxis=dict(autorange=True),
                                                yaxis=dict(autorange=True, scaleanchor="x", scaleratio=1),
                                                margin=dict(l=50, r=50, t=50, b=100),
                                                legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.25,
                                                            yanchor='top')
                                            )

                                            st.session_state.fig_mohr = fig
                                            st.plotly_chart(st.session_state.fig_mohr, use_container_width=True)

                                    with st.expander('Trajetória do Poço', expanded=False):
                                        st.markdown('### Trajetória do Poço')
                                        try:
                                            def find_directional_columns(df):
                                                md_col = inc_col = azi_col = None
                                                for c in df.columns:
                                                    cl = c.lower()
                                                    if md_col is None and any(k in cl for k in
                                                                              ["md", "measured depth",
                                                                               "profund",
                                                                               "profundidade"]):
                                                        md_col = c
                                                    if inc_col is None and any(k in cl for k in
                                                                               ["inc", "incl", "inclinação",
                                                                                "inclination"]):
                                                        inc_col = c
                                                    if azi_col is None and any(
                                                            k in cl for k in
                                                            ["azi", "azim", "azimuth", "azimute"]):
                                                        azi_col = c
                                                return md_col, inc_col, azi_col

                                            def standardize_directional(df):
                                                md_col, inc_col, azi_col = find_directional_columns(df)
                                                if md_col is None or inc_col is None or azi_col is None:
                                                    raise ValueError(
                                                        "Não foram encontradas colunas MD / Inc / Azi na tabela.")
                                                df2 = df[[md_col, inc_col, azi_col]].rename(
                                                    columns={md_col: "MD", inc_col: "Inc", azi_col: "Azi"}
                                                )
                                                df2 = df2.dropna().astype(float).sort_values(
                                                    "MD").reset_index(
                                                    drop=True)
                                                if any(df2["MD"].diff().fillna(1) <= 0):
                                                    raise ValueError(
                                                        "Coluna MD deve ser estritamente crescente.")
                                                return df2

                                            def minimum_curvature(df, x0=0.0, y0=0.0, tvd0=0.0,
                                                                  vsec_azimute_ref_graus=None):
                                                MD = df["MD"].to_numpy(dtype=float)
                                                Inc = np.radians(df["Inc"].to_numpy(dtype=float))
                                                Azi = np.radians(df["Azi"].to_numpy(dtype=float))

                                                Easting = [float(x0)]
                                                Northing = [float(y0)]
                                                TVD = [float(tvd0)]
                                                DLS_list = []

                                                for i in range(1, len(MD)):
                                                    dMD = MD[i] - MD[i - 1]
                                                    cosDL = (
                                                            np.sin(Inc[i - 1]) * np.sin(Inc[i]) * np.cos(
                                                        Azi[i] - Azi[i - 1])
                                                            + np.cos(Inc[i - 1]) * np.cos(Inc[i])
                                                    )
                                                    cosDL = np.clip(cosDL, -1.0, 1.0)
                                                    DL = np.arccos(cosDL)

                                                    DLS = np.degrees(DL) * 30.0 / dMD
                                                    DLS_list.append(float(DLS))

                                                    RF = 1.0 if DL < 1e-8 else (2.0 / DL) * np.tan(DL / 2.0)

                                                    dN = 0.5 * dMD * (
                                                            np.sin(Inc[i - 1]) * np.cos(Azi[i - 1]) +
                                                            np.sin(Inc[i]) * np.cos(Azi[i])
                                                    ) * RF
                                                    dE = 0.5 * dMD * (
                                                            np.sin(Inc[i - 1]) * np.sin(Azi[i - 1]) +
                                                            np.sin(Inc[i]) * np.sin(Azi[i])
                                                    ) * RF
                                                    dTVD = 0.5 * dMD * (np.cos(Inc[i - 1]) + np.cos(Inc[i])) * RF

                                                    Easting.append(Easting[-1] + dE)
                                                    Northing.append(Northing[-1] + dN)
                                                    TVD.append(TVD[-1] + dTVD)

                                                # --- Afastamento horizontal absoluto (Departure / HD) ---
                                                East_arr = np.asarray(Easting, dtype=float)
                                                North_arr = np.asarray(Northing, dtype=float)
                                                afast_h = np.sqrt(East_arr ** 2 + North_arr ** 2)

                                                # --- VSEC: projeção numa direção de referência ---
                                                # Se você não passar referência, uso o azimute do 1º ponto (padrão simples)
                                                if vsec_azimute_ref_graus is None:
                                                    az_ref = float(np.degrees(Azi[0])) if len(Azi) else 0.0
                                                else:
                                                    az_ref = float(vsec_azimute_ref_graus)

                                                az_ref_rad = np.radians(az_ref)
                                                vsec = East_arr * np.sin(az_ref_rad) + North_arr * np.cos(
                                                    az_ref_rad)

                                                return pd.DataFrame({
                                                    "MD": MD,
                                                    "Inclinação (°)": np.degrees(Inc),
                                                    "Azimute (°)": np.degrees(Azi),
                                                    "Easting": Easting,
                                                    "Northing": Northing,
                                                    "TVD": TVD,
                                                    "Dogleg Severity (°/30m)": [0.0] + DLS_list,
                                                    "Afastamento Horizontal (m)": afast_h,
                                                    "VSEC (m)": vsec,
                                                })

                                            df_to_use = None

                                            # 1) Prioridade: df2 (trajetória escolhida no tabs[0]) -> é o "dado real"
                                            if "df2" in st.session_state and isinstance(st.session_state["df2"],
                                                                                        pd.DataFrame):
                                                df_to_use = st.session_state["df2"].copy()

                                            # 2) Se você quiser permitir usar df_interp (interpolada para coincidir com df1),
                                            # mantenha como alternativa — mas para minimum curvature, df2 já é suficiente.
                                            elif "df_interp" in st.session_state and isinstance(
                                                    st.session_state["df_interp"], pd.DataFrame):
                                                df_to_use = st.session_state["df_interp"].copy()

                                            if df_to_use is None or df_to_use.empty:
                                                st.info(
                                                    "Trajetória não encontrada. Verifique se o XLSM possui a aba 'Trajetória' e se foi lida no upload.")
                                                st.stop()

                                            if df_to_use is None:
                                                st.info(
                                                    "Nenhum arquivo direcional disponível. Carregue ou insira uma planilha.")
                                                st.stop()

                                            # Ajustar nomes de colunas comuns
                                            rename_map = {"Profundidade": "MD", "Inc (°)": "Inc",
                                                          "Azi (°)": "Azi"}
                                            df_to_use = df_to_use.rename(
                                                columns={k: v for k, v in rename_map.items() if
                                                         k in df_to_use.columns})

                                            # Padronizar e validar
                                            df_proc = standardize_directional(df_to_use)

                                            # Interpolar até a superfície com base nos dados reais de df2, se disponível
                                            # Se o usuário quiser expandir até o zero (ou até o menor MD), faça aqui
                                            if st.session_state.get("ex", "Desativada") == "Ativada":
                                                first_md = float(df_proc["MD"].iloc[0])
                                                if first_md > 0:
                                                    md_extra = np.arange(0.0, first_md, 1.0)
                                                    df_extra = pd.DataFrame({
                                                        "MD(m)": md_extra,
                                                        "Incl": np.interp(md_extra, df_proc["MD"], df_proc["Inc"]),
                                                        "Azimute": np.interp(md_extra, df_proc["MD"], df_proc["Azi"]),
                                                    })
                                                    df_proc = pd.concat([df_extra, df_proc],
                                                                        ignore_index=True).drop_duplicates(
                                                        "MD").sort_values("MD")

                                            df_out = minimum_curvature(df_proc, x0=0.0, y0=0.0, tvd0=0.0)
                                            st.session_state.df_out_traj = df_out.copy()

                                            fig = go.Figure()

                                            nx, ny = 80, 80
                                            x_min, x_max = df_out["Easting"].min() - 50, df_out[
                                                "Easting"].max() + 50
                                            y_min, y_max = df_out["Northing"].min() - 50, df_out[
                                                "Northing"].max() + 50
                                            xg, yg = np.meshgrid(np.linspace(x_min, x_max, nx),
                                                                 np.linspace(y_min, y_max, ny))
                                            z_superficie = np.zeros_like(xg)

                                            fig.add_trace(go.Surface(
                                                x=xg, y=yg, z=z_superficie,
                                                colorscale=[[0, "#aaaaaa"], [1, "#aaaaaa"]],
                                                showscale=False, opacity=0.6, name="Solo", showlegend=True
                                            ))

                                            z_plot = df_out["TVD"]
                                            fig.add_trace(go.Scatter3d(
                                                x=df_out["Easting"], y=df_out["Northing"], z=z_plot,
                                                mode="lines", line=dict(color="red", width=5),
                                                name="Trajetória"
                                            ))

                                            fig.add_trace(go.Scatter3d(
                                                x=[df_out["Easting"].iloc[0]],
                                                y=[df_out["Northing"].iloc[0]],
                                                z=[z_plot.iloc[0]],
                                                mode="markers",
                                                marker=dict(size=8, color="blue", symbol="circle"),
                                                name="Cabeça do poço"
                                            ))

                                            fig.add_trace(go.Scatter3d(
                                                x=[df_out["Easting"].iloc[-1]],
                                                y=[df_out["Northing"].iloc[-1]],
                                                z=[z_plot.iloc[-1]],
                                                mode="markers+text",
                                                marker=dict(size=8, color="green", symbol="circle"),
                                                textposition="top center",
                                                name="Alvo"
                                            ))

                                            ponto_idx = (
                                                        df_out["TVD"] - profundidade_proxima).abs().idxmin()
                                            ponto_x = df_out.loc[ponto_idx, "Easting"]
                                            ponto_y = df_out.loc[ponto_idx, "Northing"]
                                            ponto_z = df_out.loc[ponto_idx, "TVD"]

                                            fig.add_trace(go.Scatter3d(
                                                x=[ponto_x],
                                                y=[ponto_y],
                                                z=[ponto_z],
                                                mode="markers+text",
                                                marker=dict(size=8, color="orange", symbol="diamond"),
                                                text=f"Profundidade: {profundidade_proxima:.1f} m",
                                                textposition="top center",
                                                name="Profundidade Analisada"
                                            ))

                                            fig.update_layout(
                                                height=800,
                                                width=600,
                                                scene=dict(
                                                    xaxis=dict(title="Easting"),
                                                    yaxis=dict(title="Northing"),
                                                    zaxis=dict(title="TVD (m)", autorange="reversed"),
                                                    camera=dict(
                                                        eye=dict(x=2., y=2., z=1.6)
                                                    )
                                                ),
                                                legend=dict(
                                                    font=dict(size=10, color="black"),
                                                    bgcolor="rgba(255,255,255,0.7)",
                                                    bordercolor="gray",
                                                    borderwidth=1,
                                                    x=1,
                                                    y=-0.15,
                                                    xanchor="right",
                                                    yanchor="top",
                                                )
                                            )

                                            st.session_state.fig_traj = fig

                                            st.plotly_chart(fig, use_container_width=True)

                                        except Exception as e:
                                            st.warning(f"Erro ao calcular/plotar trajetória: {e}")
                                            pass

                                    with st.expander('Tabela de Dados da Trajetória', expanded=False):
                                        st.markdown('### Tabela de Dados da Trajetória')
                                        try:
                                            st.dataframe(df_out, use_container_width=True)
                                        except Exception as e:
                                            st.warning(f"Erro ao calcular/plotar trajetória: {e}")
                                            pass

                            # GRÁFICO JANELA OPERACIONAL
                            with c3:
                                with st.container(border=True):
                                    st.markdown('### Janela Operacional')
                                    if not criterio_disponivel(df_tvp):
                                        st.warning(
                                            "⚠️ Calcule as tensões antes de avaliar o critério de falha.")
                                    if criterio_disponivel(df_tvp):
                                        with colu3:
                                            df_tvp['Max Inferior'] = df_tvp[
                                                ['Tração Inferior', 'Comp Inferior σθA', 'Comp Inferior σθB']
                                            ].max(axis=1)

                                            df_tvp['Min Superior'] = df_tvp[
                                                ['Tração Superior (σθA)', 'Tração Superior (σθB)',
                                                 'Comp Superior σθA', 'Comp Superior σθB']
                                            ].min(axis=1)

                                            linha = df_tvp.loc[st.session_state.y == profundidade_proxima].iloc[0]

                                            x_max_inf = pd.Series(
                                                df_tvp['Max Inferior'] if st.session_state.suav_max_inf else df_tvp[
                                                    'Max Inferior'],
                                                index=df_tvp.index,
                                                dtype=float
                                            )

                                            x_min_sup = pd.Series(
                                                df_tvp['Min Superior'] if st.session_state.suav_min_sup else df_tvp[
                                                    'Min Superior'],
                                                index=df_tvp.index,
                                                dtype=float
                                            )

                                            fs = float(st.session_state.fs)

                                            x_fs_base_inf = x_max_inf + fs
                                            x_fs_inf = pd.Series(np.nan, index=df_tvp.index, dtype=float)

                                            mask_fs = x_fs_base_inf.notna()
                                            x_fs_inf.loc[mask_fs] = np.maximum.accumulate(
                                                x_fs_base_inf.loc[mask_fs].to_numpy()
                                            )

                                            idx_linha = linha.name

                                            max_inferior = x_fs_inf.loc[idx_linha]
                                            min_superior = x_min_sup.loc[idx_linha] - fs

                                            if pd.isna(max_inferior) or pd.isna(min_superior):
                                                st.info(
                                                    "A profundidade selecionada está no trecho extrapolado ou sem sônico válido. "
                                                    "A janela operacional não será exibida nesse ponto."
                                                )
                                            else:
                                                st.markdown(
                                                    f"""
                                                    <div style="
                                                        display: flex;
                                                        justify-content: center;
                                                        margin-top: 0px;
                                                    ">
                                                        <div style="
                                                            color: black;
                                                            font-weight: bold;
                                                            border: 2px solid black;
                                                            border-radius: 10px;
                                                            padding: 6px 10px;
                                                            text-align: center;
                                                            font-size: 15px;
                                                            line-height: 1.2;
                                                        ">
                                                            Janela Op.<br>
                                                            <span style="color: red; font-size: 15px;">{max_inferior:.2f}</span>
                                                            <span style="font-size: 15px;">&lt; ρ &lt;</span>
                                                            <span style="color: red; font-size: 15px;">{min_superior:.2f}</span>
                                                        </div>
                                                    </div>
                                                    """,
                                                    unsafe_allow_html=True
                                                )
                                        def _normalizar_angulo_360(ang, default=np.nan):
                                            try:
                                                if pd.isna(ang):
                                                    return default
                                                return float(ang) % 360
                                            except Exception:
                                                return default
                                        def _seta_polar(ax_polar, angulo, r_ini, r_fim, cor, lw=2.0, ms=12,linestyle="-"):
                                            theta = np.deg2rad(_normalizar_angulo_360(angulo, 0))

                                            ax_polar.annotate(
                                                "",
                                                xy=(theta, r_fim),
                                                xytext=(theta, r_ini),
                                                arrowprops=dict(
                                                    arrowstyle="-|>",
                                                    color=cor,
                                                    linewidth=lw,
                                                    linestyle=linestyle,
                                                    mutation_scale=ms,
                                                    shrinkA=0,
                                                    shrinkB=0
                                                ),
                                                zorder=10
                                            )
                                        def _plotar_eixo_tensao_inset(ax_polar,angulo,cor,label,r_ini,r_fim,lw,ms,r_texto,deslocamento_lateral=8):
                                            angulo = _normalizar_angulo_360(angulo, 0)
                                            angulo_oposto = _normalizar_angulo_360(angulo + 180, 0)

                                            # plota as duas setas do eixo de tensão
                                            for ang in [angulo, angulo_oposto]:
                                                _seta_polar(
                                                    ax_polar,
                                                    angulo=ang,
                                                    r_ini=r_ini,
                                                    r_fim=r_fim,
                                                    cor=cor,
                                                    lw=lw,
                                                    ms=ms
                                                )

                                            # escreve o nome apenas uma vez, deslocado lateralmente
                                            theta_texto = np.deg2rad(
                                                _normalizar_angulo_360(angulo + deslocamento_lateral, 0)
                                            )

                                            ax_polar.text(
                                                theta_texto,
                                                r_texto,
                                                label,
                                                color=cor,
                                                fontsize=6,
                                                ha="center",
                                                va="center",
                                                zorder=20
                                            )
                                        def plotar_rosa_dos_ventos_inset_jo(
                                                ax,
                                                direcao_shmax,
                                                direcao_shmin,
                                                azimute_poco=np.nan,
                                                posicao=(0.02, 0.735, 0.27, 0.27)
                                        ):

                                            direcao_shmax = _normalizar_angulo_360(direcao_shmax, 0)
                                            direcao_shmin = _normalizar_angulo_360(direcao_shmin, direcao_shmax + 90)
                                            azimute_poco = _normalizar_angulo_360(azimute_poco, np.nan)

                                            ax_rosa = ax.inset_axes(
                                                posicao,
                                                projection="polar",
                                                zorder=30
                                            )

                                            ax_rosa.set_facecolor((1, 1, 1, 0.88))

                                            # Convenção de rosa dos ventos
                                            ax_rosa.set_theta_zero_location("N")
                                            ax_rosa.set_theta_direction(-1)

                                            ax_rosa.set_ylim(0, 1.12)
                                            ax_rosa.set_yticks([])

                                            ax_rosa.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))

                                            ax_rosa.set_xticklabels(
                                                ["N", "NE", "E", "SE", "S", "SO", "O", "NO"],
                                                fontsize=6,
                                                fontweight="bold"
                                            )

                                            ax_rosa.tick_params(axis='x', pad=-6)
                                            ax_rosa.grid(True, linestyle="--", alpha=0.35, linewidth=0.6)

                                            # Poço central
                                            theta = np.linspace(0, 2 * np.pi, 200)
                                            raio_poco = np.full_like(theta, 0.18)

                                            ax_rosa.fill(
                                                theta,
                                                raio_poco,
                                                facecolor="#9ecae1",
                                                edgecolor="black",
                                                linewidth=0.8,
                                                alpha=0.95,
                                                zorder=5
                                            )

                                            # SH maior, vermelho
                                            _plotar_eixo_tensao_inset(
                                                ax_polar=ax_rosa,
                                                angulo=direcao_shmax,
                                                cor="red",
                                                label="SH",
                                                r_ini=1.00,
                                                r_fim=0.22,
                                                lw=2.4,
                                                ms=14,
                                                r_texto=0.8,
                                                deslocamento_lateral=15
                                            )

                                            # Sh menor, verde
                                            _plotar_eixo_tensao_inset(
                                                ax_polar=ax_rosa,
                                                angulo=direcao_shmin,
                                                cor="green",
                                                label="Sh",
                                                r_ini=0.82,
                                                r_fim=0.22,
                                                lw=1.8,
                                                ms=11,
                                                r_texto=0.8,
                                                deslocamento_lateral=15
                                            )

                                            # Azimute final do poço
                                            if pd.notna(azimute_poco):
                                                theta_azi = np.deg2rad(azimute_poco)

                                                ax_rosa.annotate(
                                                    "",
                                                    xy=(theta_azi, 0.98),
                                                    xytext=(theta_azi, 0.20),
                                                    arrowprops=dict(
                                                        arrowstyle="->",
                                                        color="black",
                                                        linewidth=1.5,
                                                        linestyle="--",
                                                        mutation_scale=10,
                                                        shrinkA=0,
                                                        shrinkB=0
                                                    ),
                                                    zorder=15
                                                )

                                                deslocamento_lateral = 20
                                                theta_texto = np.deg2rad(
                                                    _normalizar_angulo_360(azimute_poco + deslocamento_lateral, 0))

                                                ax_rosa.text(
                                                    theta_texto,
                                                    0.62,
                                                    "Azi",
                                                    color="black",
                                                    fontsize=6,
                                                    ha="center",
                                                    va="center",
                                                    zorder=20
                                                )

                                            for spine in ax_rosa.spines.values():
                                                spine.set_edgecolor("black")
                                                spine.set_linewidth(0.8)

                                            return ax_rosa

                                        st.session_state.fig_jo = plt.figure(figsize=(8, 10))

                                        if st.session_state.idg == 'Sim':
                                            # ===== COM coluna de idade =====
                                            gs = gridspec.GridSpec(
                                                1, 4,
                                                width_ratios=[0.1, 0.2, 0.21, 1],
                                                wspace=0
                                            )

                                            ax_idade = st.session_state.fig_jo.add_subplot(gs[0])
                                            ax1 = st.session_state.fig_jo.add_subplot(gs[1], sharey=ax_idade)

                                            ax_gap = st.session_state.fig_jo.add_subplot(gs[2])
                                            ax_gap.axis('off')

                                            ax = st.session_state.fig_jo.add_subplot(gs[3], sharey=ax_idade)

                                            idade_formacao(ax_idade, st.session_state.df_idade, st.session_state.y_max_pp)

                                            # remove ticks e labels da coluna de idade
                                            ax_idade.tick_params(
                                                axis='y',
                                                which='both',
                                                left=False,
                                                right=False,
                                                labelleft=False,
                                                labelright=False
                                            )

                                            ax_idade.set_ylabel("")

                                            # evita duplicar rótulos de profundidade
                                            plt.setp(ax1.get_yticklabels(), visible=False)
                                            plt.setp(ax.get_yticklabels(), visible=False)

                                        else:
                                            # ===== SEM coluna de idade =====
                                            gs = gridspec.GridSpec(
                                                1, 3,
                                                width_ratios=[0.18, 0.21, 1],
                                                wspace=0
                                            )

                                            ax1 = st.session_state.fig_jo.add_subplot(gs[0])
                                            ax_gap = st.session_state.fig_jo.add_subplot(gs[1])
                                            ax_gap.axis('off')

                                            ax = st.session_state.fig_jo.add_subplot(gs[2], sharey=ax1)

                                            plt.setp(ax.get_yticklabels(), visible=False)

                                        # Limites da Janela Operacional
                                        x_max_inf = df_suav[
                                            'Max Inferior'] if st.session_state.suav_max_inf else \
                                            df_tvp['Max Inferior']
                                        x_min_sup = df_suav[
                                            'Min Superior'] if st.session_state.suav_min_sup else \
                                            df_tvp['Min Superior']

                                        # ZONAS DE PERDA DIMINUEM LIMITE SUPERIOR
                                        for i in st.session_state.zona2:
                                            profundidade_zona = i[0]
                                            peso_zona = i[1]

                                            if st.session_state.suav_min_sup:

                                                if st.session_state.t_prof == "TVD":
                                                    coluna_profundidade = df_suav['Profundidade (m)']
                                                else:
                                                    coluna_profundidade = df_suav['MD']

                                                index = (
                                                            coluna_profundidade - profundidade_zona).abs().idxmin()
                                                df_suav.loc[index, 'Min Superior'] = peso_zona

                                            else:

                                                if st.session_state.t_prof == "MD":
                                                    coluna_profundidade = df_tvp['Profundidade (m)']
                                                else:
                                                    coluna_profundidade = df_tvp['MD']

                                                index = (
                                                            coluna_profundidade - profundidade_zona).abs().idxmin()
                                                df_tvp.loc[index, 'Min Superior'] = peso_zona

                                        if "ponto_a"not in st.session_state:
                                            st.session_state.ponto_a = 'Não'
                                        def valor_na_curva(df_plot, coluna, profundidade):
                                            base = df_plot[['Profundidade (m)', coluna]].dropna().sort_values(
                                                'Profundidade (m)')

                                            if base.empty:
                                                return np.nan

                                            return np.interp(
                                                profundidade,
                                                base['Profundidade (m)'],
                                                base[coluna]
                                            )
                                        mapa_colunas_falha = {
                                            'Tração Inferior': 'Tração Inferior',
                                            'Tração Superior σθA': 'Tração Superior (σθA)',
                                            'Tração Superior σθB': 'Tração Superior (σθB)',
                                            'Comp Inferior σθA': 'Comp Inferior σθA',
                                            'Comp Superior σθA': 'Comp Superior σθA',
                                            'Comp Inferior σθB': 'Comp Inferior σθB',
                                            'Comp Superior σθB': 'Comp Superior σθB',
                                        }

                                        if st.session_state.ponto_a == 'Sim':
                                            if st.session_state.ppg is not None and st.session_state.m is not None:
                                                coluna_ponto = mapa_colunas_falha.get(st.session_state.op)

                                                if coluna_ponto is not None and coluna_ponto in df_suav.columns:
                                                    peso_ponto = valor_na_curva(
                                                        df_suav,
                                                        coluna_ponto,
                                                        profundidade_proxima
                                                    )
                                                else:
                                                    peso_ponto = peso_fluido

                                                ax.scatter(
                                                    peso_ponto,
                                                    profundidade_proxima,
                                                    color='red',
                                                    edgecolor='black',
                                                    s=80,
                                                    zorder=10,
                                                    label='Peso do Fluido Selecionado'
                                                )

                                        # Janela Operacional completa
                                        if st.session_state.jo:
                                            ax.plot(x_max_inf, st.session_state.y, color='blue',
                                                    linestyle='-', linewidth=2,
                                                    label="Limite Inferior da Janela Operacional")
                                            ax.plot(x_min_sup, st.session_state.y, color='red',
                                                    linestyle='-', linewidth=2,
                                                    label="Limite Superior da Janela Operacional")

                                        colunas_texto = [
                                            'Profundidade (m)',
                                            'Gradiente de Sobrecarga (lb/gal)',
                                            'SH (psi)',
                                            'Sh (psi)',
                                            'Direção SH',
                                            'Direção Sh'
                                        ]

                                        def ajustar_angulo_360(ang):
                                            if pd.isna(ang):
                                                return ang
                                            while ang > 360:
                                                ang -= 360
                                            return ang

                                        if "ctjo" not in st.session_state:
                                            st.session_state.ctjo = "Sim"

                                        if st.session_state.ctjo == "Sim":
                                            if all(col in df_tvp.columns for col in colunas_texto):
                                                try:
                                                    # Sempre usa a profundidade_proxima
                                                    idx_tensoes = (df_tvp[
                                                                       'Profundidade (m)'] - profundidade_proxima).abs().idxmin()
                                                    linha_t = df_tvp.loc[idx_tensoes]

                                                    sv = linha_t['Gradiente de Sobrecarga (lb/gal)']
                                                    dir_shmax = ajustar_angulo_360(linha_t['Direção SH'])
                                                    dir_shmin = ajustar_angulo_360(linha_t['Direção Sh'])
                                                    prof = linha_t['Profundidade (m)']

                                                    azimute_poco = np.nan

                                                    fontes_azimute = [
                                                        st.session_state.get("df2", None),
                                                        st.session_state.get("df_out_traj", None),
                                                        st.session_state.get("df_interp", None),
                                                        df_tvp
                                                    ]

                                                    for df_azi in fontes_azimute:
                                                        if isinstance(df_azi, pd.DataFrame) and not df_azi.empty:
                                                            for col_azi in ["Azi", "Azimute", "Azimuth", "Azimute (°)"]:
                                                                if col_azi in df_azi.columns:
                                                                    serie_azi = pd.to_numeric(df_azi[col_azi],
                                                                                              errors="coerce").dropna()

                                                                    if not serie_azi.empty:
                                                                        azimute_poco = ajustar_angulo_360(
                                                                            float(serie_azi.iloc[-1]))
                                                                        break

                                                        if pd.notna(azimute_poco):
                                                            break

                                                    if pd.notna(sv) and sv != 0:
                                                        if 'SH% Sobrecarga' in df_tvp.columns and pd.notna(
                                                                linha_t.get('SH% Sobrecarga', np.nan)):
                                                            rel_shmax = linha_t['SH% Sobrecarga']
                                                        else:
                                                            rel_shmax = (linha_t['SH (psi)'] / (0.1704 * prof)) / sv

                                                        if 'Sh% Sobrecarga' in df_tvp.columns and pd.notna(
                                                                linha_t.get('Sh% Sobrecarga', np.nan)):
                                                            rel_shmin = linha_t['Sh% Sobrecarga']
                                                        else:
                                                            rel_shmin = (linha_t['Sh (psi)'] / (0.1704 * prof)) / sv

                                                        from matplotlib.offsetbox import AnchoredOffsetbox, VPacker, \
                                                            TextArea
                                                        linha_SH = TextArea(
                                                            f"SH = {rel_shmax:.2f}·σv | Dir. SH = {dir_shmax:.1f}°",
                                                            textprops=dict(
                                                                color="red",
                                                                fontsize=9,
                                                                fontweight="bold"
                                                            )
                                                        )

                                                        linha_Sh = TextArea(
                                                            f"Sh = {rel_shmin:.2f}·σv | Dir. Sh = {dir_shmin:.1f}°",
                                                            textprops=dict(
                                                                color="green",
                                                                fontsize=9,
                                                                fontweight="bold"
                                                            )
                                                        )

                                                        linhas_caixa = [linha_SH, linha_Sh]

                                                        if pd.notna(azimute_poco):
                                                            linha_azi = TextArea(
                                                                f"Azimute final do poço = {azimute_poco:.1f}°",
                                                                textprops=dict(
                                                                    color="black",
                                                                    fontsize=9,
                                                                    fontweight="bold"
                                                                )
                                                            )

                                                            linhas_caixa.append(linha_azi)

                                                        if st.session_state.get("rosa_jo", "Sim") == "Sim":
                                                            plotar_rosa_dos_ventos_inset_jo(
                                                                ax=ax,
                                                                direcao_shmax=dir_shmax,
                                                                direcao_shmin=dir_shmin,
                                                                azimute_poco=azimute_poco,
                                                                posicao=(0.025, 0.828, 0.2, 0.2)
                                                            )

                                                        caixa_texto = VPacker(
                                                            children=linhas_caixa,
                                                            align="right",
                                                            pad=0,
                                                            sep=2
                                                        )

                                                        caixa_ancorada = AnchoredOffsetbox(
                                                            loc="upper right",
                                                            child=caixa_texto,
                                                            pad=0.25,
                                                            frameon=True,
                                                            bbox_to_anchor=(0.98, 0.99),
                                                            bbox_transform=ax.transAxes,
                                                            borderpad=0.45
                                                        )

                                                        caixa_ancorada.patch.set_boxstyle("round,pad=0.35")
                                                        caixa_ancorada.patch.set_facecolor("white")
                                                        caixa_ancorada.patch.set_alpha(0.85)
                                                        caixa_ancorada.patch.set_edgecolor("black")
                                                        caixa_ancorada.set_zorder(20)

                                                        ax.add_artist(caixa_ancorada)
                                                except Exception:
                                                    pass

                                        y_vals = np.asarray(st.session_state.y, dtype=float)

                                        # FS inferior com sua lógica:
                                        if st.session_state.ijo:
                                            ax.plot(
                                                x_fs_inf,
                                                y_vals,
                                                color='gold',
                                                linestyle='--',
                                                linewidth=2,
                                                label="FS Inferior da Janela Operacional"
                                            )
                                        else:
                                            x_fs_inf = np.asarray(x_max_inf, dtype=float).copy()

                                        # FS superior
                                        if st.session_state.sjo:
                                            x_fs_sup = np.asarray(x_min_sup, dtype=float) - float(
                                                st.session_state.fs)

                                            ax.plot(
                                                x_fs_sup,
                                                y_vals,
                                                color='tomato',
                                                linestyle='--',
                                                linewidth=2,
                                                label="FS Superior da Janela Operacional"
                                            )
                                        else:
                                            x_fs_sup = np.asarray(x_min_sup, dtype=float).copy()

                                        # Janela útil (verde)
                                        if st.session_state.jo:
                                            mascara_janela = x_fs_sup > x_fs_inf
                                            if np.any(mascara_janela):
                                                ax.fill_betweenx(
                                                    y_vals,
                                                    x_fs_inf,
                                                    x_fs_sup,
                                                    where=mascara_janela,
                                                    interpolate=True,
                                                    color='lightgreen',
                                                    alpha=0.25,
                                                    label='Janela Operacional'
                                                )

                                        # Faixa consumida pelo FS inferior (vermelho)
                                        if st.session_state.ijo:
                                            mascara_inf = x_fs_inf > x_max_inf
                                            if np.any(mascara_inf):
                                                ax.fill_betweenx(
                                                    y_vals,
                                                    x_max_inf,
                                                    x_fs_inf,
                                                    where=mascara_inf,
                                                    interpolate=True,
                                                    color='lightcoral',
                                                    alpha=0.25,
                                                )

                                        # Faixa consumida pelo FS superior (vermelho)
                                        if st.session_state.sjo:
                                            mascara_sup = x_min_sup > x_fs_sup
                                            if np.any(mascara_sup):
                                                ax.fill_betweenx(
                                                    y_vals,
                                                    x_fs_sup,
                                                    x_min_sup,
                                                    where=mascara_sup,
                                                    interpolate=True,
                                                    color='lightcoral',
                                                    alpha=0.25,
                                                )

                                        # Apenas limite inferior
                                        if st.session_state.li and not st.session_state.jo:
                                            ax.plot(x_max_inf, st.session_state.y, color='blue',
                                                    linestyle='-', linewidth=2,
                                                    label="Limite Inferior da Janela Operacional")

                                        # Apenas limite superior
                                        if st.session_state.ls and not st.session_state.jo:
                                            ax.plot(x_min_sup, st.session_state.y, color='red',
                                                    linestyle='-', linewidth=2,
                                                    label="Limite Superior da Janela Operacional")

                                        # Tração e Compressão com lógica de suavização
                                        if st.session_state.tsa:
                                            if st.session_state.suav_tsa:
                                                ax.plot(df_suav['Tração Superior (σθA)'],
                                                        st.session_state.y, color='green',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Tração Superior σθA")
                                            else:
                                                ax.plot(df_tvp['Tração Superior (σθA)'], st.session_state.y,
                                                        color='green',
                                                        linestyle='-', linewidth=2,
                                                        label="Tração Superior σθA")

                                        if st.session_state.tsb:
                                            if st.session_state.suav_tsb:
                                                ax.plot(df_suav['Tração Superior (σθB)'],
                                                        st.session_state.y, color='purple',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Tração Superior σθB")
                                            else:
                                                ax.plot(df_tvp['Tração Superior (σθB)'], st.session_state.y,
                                                        color='purple',
                                                        linestyle='-', linewidth=2,
                                                        label="Tração Superior σθB")

                                        if st.session_state.cia:
                                            if st.session_state.suav_cia:
                                                ax.plot(df_suav['Comp Inferior σθA'], st.session_state.y,
                                                        color='turquoise',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Comp Inferior σθA")
                                            else:
                                                ax.plot(df_tvp['Comp Inferior σθA'], st.session_state.y,
                                                        color='turquoise',
                                                        linestyle='-', linewidth=2,
                                                        label="Comp Inferior σθA")

                                        if st.session_state.csa:
                                            if st.session_state.suav_csa:
                                                ax.plot(df_suav['Comp Superior σθA'], st.session_state.y,
                                                        color='lime',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Comp Superior σθA")
                                            else:
                                                ax.plot(df_tvp['Comp Superior σθA'], st.session_state.y,
                                                        color='lime',
                                                        linestyle='-', linewidth=2,
                                                        label="Comp Superior σθA")

                                        if st.session_state.cib:
                                            if st.session_state.suav_cib:
                                                ax.plot(df_suav['Comp Inferior σθB'], st.session_state.y,
                                                        color='brown',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Comp Inferior σθB")
                                            else:
                                                ax.plot(df_tvp['Comp Inferior σθB'], st.session_state.y,
                                                        color='brown',
                                                        linestyle='-', linewidth=2,
                                                        label="Comp Inferior σθB")

                                        if st.session_state.csb:
                                            if st.session_state.suav_csb:
                                                ax.plot(df_suav['Comp Superior σθB'], st.session_state.y,
                                                        color='gray',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Comp Superior σθB")
                                            else:
                                                ax.plot(df_tvp['Comp Superior σθB'], st.session_state.y,
                                                        color='gray',
                                                        linestyle='-', linewidth=2,
                                                        label="Comp Superior σθB")

                                        # Pressão de poros e Tração Inferior (sempre originais)
                                        if st.session_state.gs:
                                            ax.plot(df_tvp['Gradiente de Sobrecarga (lb/gal)'],
                                                    st.session_state.y,
                                                    color='black', linestyle='-', linewidth=2,
                                                    label="Gradiente de Sobrecarga")
                                        if st.session_state.show_pp:
                                            ax.plot(df_tvp['Gradiente de Pressão de Poros (lb/gal)'],
                                                    st.session_state.y,
                                                    color='orange', linestyle='-', linewidth=2,
                                                    label="Pressão de Poros")
                                        if st.session_state.ti:
                                            ax.plot(df_tvp['Tração Inferior'], st.session_state.y,
                                                    color='teal', linestyle='-',
                                                    linewidth=2,
                                                    label="Tração Inferior")

                                        if st.session_state.ponto_a == 'Sim':
                                            # Linha horizontal indicando a profundidade analisada
                                            ax.axhline(
                                                y=profundidade_proxima,
                                                color='dodgerblue',
                                                linestyle='--',
                                                linewidth=1,
                                            )

                                            if "x_max" not in st.session_state:
                                                st.session_state.x_max = 23
                                            if "x_min" not in st.session_state:
                                                st.session_state.x_min = 7

                                            # Texto acima e à direita da linha
                                            ax.text(
                                                st.session_state.x_max - (
                                                        st.session_state.x_max - st.session_state.x_min) * 0.01,
                                                profundidade_proxima - 3,
                                                f"Profundidade Analisada ({profundidade_proxima:.1f} m)",
                                                color='black',
                                                fontsize=10,
                                                verticalalignment='bottom',
                                                horizontalalignment='right',
                                                zorder=8
                                            )

                                        if st.session_state.get("spt", "Não") == "Sim":
                                            if 'sapatas_df' in st.session_state and not st.session_state.sapatas_df.empty:
                                                plotted_label = False

                                                # Proteções básicas
                                                df_tvp_local = None
                                                if 'df_tvp' in locals():
                                                    df_tvp_local = df_tvp
                                                elif 'df_tvp' in globals():
                                                    df_tvp_local = globals().get('df_tvp')
                                                elif 'df_tvp' in st.session_state:
                                                    df_tvp_local = st.session_state.df_tvp

                                                for _, row in st.session_state.sapatas_df.iloc[1:].iterrows():
                                                    fase = float(row['Fase'])
                                                    tvd_informada = float(row['Profundidade da sapata (m)'])

                                                    # Decide profundidade a plotar (y_plot)
                                                    y_plot = tvd_informada
                                                    tvd_display = tvd_informada
                                                    md_display = None

                                                    try:
                                                        if st.session_state.t_prof == "TVD":
                                                            y_plot = tvd_informada
                                                        else:
                                                            # visualizar por MD → converter TVD informado para MD buscando o registro mais próximo em df_tvp
                                                            if (
                                                                    df_tvp_local is not None
                                                                    and 'Profundidade (m)' in df_tvp_local.columns
                                                                    and 'MD' in df_tvp_local.columns
                                                            ):
                                                                idx_closest = (df_tvp_local[
                                                                                   'Profundidade (m)'] - tvd_informada).abs().idxmin()
                                                                md_val = float(df_tvp_local.loc[idx_closest, 'MD'])
                                                                y_plot = md_val
                                                                md_display = md_val
                                                            else:
                                                                y_plot = tvd_informada
                                                    except Exception:
                                                        y_plot = tvd_informada

                                                    # Triângulo / marcador na posição calculada
                                                    ax.scatter(
                                                        st.session_state.x_min + 0.5,
                                                        y_plot - 12,
                                                        color='black',
                                                        marker='v',
                                                        s=100,
                                                        label='Sapatas' if not plotted_label else "",
                                                        zorder=7
                                                    )

                                                    # Linha horizontal na posição calculada
                                                    ax.hlines(
                                                        y=y_plot,
                                                        xmin=st.session_state.x_min,
                                                        xmax=st.session_state.x_max,
                                                        colors='black',
                                                        linestyles='--',
                                                        linewidth=1,
                                                        zorder=5
                                                    )

                                                    # Texto à direita
                                                    if md_display is None:
                                                        text_str = f"Sapata {fase:.3f}, {tvd_display:.2f} m"
                                                    else:
                                                        text_str = f"Sapata {fase:.3f}, TVD {tvd_display:.2f} m (MD {md_display:.2f} m)"

                                                    ax.text(
                                                        st.session_state.x_max - (
                                                                    st.session_state.x_max - st.session_state.x_min) * 0.01,
                                                        y_plot - 3,
                                                        text_str,
                                                        color='black',
                                                        fontsize=10,
                                                        verticalalignment='bottom',
                                                        horizontalalignment='right',
                                                        zorder=8
                                                    )

                                                    plotted_label = True

                                        # ===== PLOT DAS PRISÕES DE COLUNA (SOMENTE MARCADOR + LINHA) =====
                                        if 'prisoes_coluna_df' in st.session_state and not st.session_state.prisoes_coluna_df.empty:
                                            plotted_label = False

                                            # Proteção para df_tvp
                                            df_tvp_local = None
                                            if 'df_tvp' in locals():
                                                df_tvp_local = df_tvp
                                            elif 'df_tvp' in globals():
                                                df_tvp_local = globals().get('df_tvp')
                                            elif 'df_tvp' in st.session_state:
                                                df_tvp_local = st.session_state.df_tvp

                                            for _, row in st.session_state.prisoes_coluna_df.iterrows():
                                                tvd_informada = float(row['Profundidade da prisão (m)'])

                                                y_plot = tvd_informada

                                                try:
                                                    if st.session_state.t_prof == "TVD":
                                                        y_plot = tvd_informada
                                                    else:
                                                        if (
                                                                df_tvp_local is not None
                                                                and 'Profundidade (m)' in df_tvp_local.columns
                                                                and 'MD' in df_tvp_local.columns
                                                        ):
                                                            idx_closest = (
                                                                    df_tvp_local[
                                                                        'Profundidade (m)'] - tvd_informada
                                                            ).abs().idxmin()

                                                            y_plot = float(
                                                                df_tvp_local.loc[idx_closest, 'MD'])
                                                except Exception:
                                                    y_plot = tvd_informada

                                                # Marcador
                                                ax.scatter(
                                                    st.session_state.x_min + 0.5,
                                                    y_plot,
                                                    color='red',
                                                    marker='X',
                                                    s=90,
                                                    label='Prisão de Coluna' if not plotted_label else "",
                                                    zorder=7
                                                )

                                                # Linha horizontal
                                                ax.hlines(
                                                    y=y_plot,
                                                    xmin=st.session_state.x_min,
                                                    xmax=st.session_state.x_max,
                                                    colors='red',
                                                    linestyles='--',
                                                    linewidth=1,
                                                    zorder=5
                                                )

                                                plotted_label = True

                                        if 'edited_z2' in st.session_state:
                                            # pega os valores das colunas
                                            x_vals = st.session_state.edited_z2["Peso do fluido (lb/gal)"]
                                            y_vals = st.session_state.edited_z2[
                                                "Profundidade da zona de perda (m)"]

                                            mask = (x_vals != 0) & (y_vals != 0)
                                            if mask.any():
                                                ax.scatter(
                                                    x_vals[mask],
                                                    y_vals[mask],
                                                    facecolors='brown',
                                                    edgecolors='black',
                                                    marker='o',
                                                    s=80,
                                                    label="Perdas de Circulação",
                                                    zorder=6
                                                )

                                        # Separa LOT e FIT de acordo com tt
                                        lot_x = [lt[i] for i in range(len(tt)) if tt[i] == "LOT"]
                                        lot_y = [pp[i] for i in range(len(tt)) if tt[i] == "LOT"]

                                        fit_x = [lt[i] for i in range(len(tt)) if tt[i] == "FIT"]
                                        fit_y = [pp[i] for i in range(len(tt)) if tt[i] == "FIT"]

                                        if st.session_state.tab:
                                            if lot_x and lot_y:
                                                ax.scatter(lot_x, lot_y, color='red', label="LOT's",
                                                           zorder=5,
                                                           marker='D', s=50)
                                            else:
                                                pass

                                            if fit_x and fit_y:
                                                ax.scatter(fit_x, fit_y, color='blue', label="FIT's",
                                                           zorder=5,
                                                           marker='^', s=50)
                                            else:
                                                pass
                                        if "df_mud" in st.session_state and isinstance(st.session_state["df_mud"],
                                                                                       pd.DataFrame):
                                            df_mud = st.session_state["df_mud"].copy()

                                            # Executado
                                            if mostrar_executado and df_mud[
                                                "Peso do Fluido Executado (lb/gal)"].notna().any():
                                                ax.plot(
                                                    df_mud["Peso do Fluido Executado (lb/gal)"],
                                                    df_mud["Profundidade (m)"],
                                                    linestyle="-",
                                                    color="mediumvioletred",
                                                    linewidth=2,
                                                    label="Peso do Fluido (Executado)",
                                                    zorder=5
                                                )

                                        def reset_config():
                                            st.session_state.x_min = 7
                                            st.session_state.x_max = 23
                                            st.session_state.x_step_tvp = 1
                                            st.session_state.y_min = 0
                                            st.session_state.y_max = int(st.session_state.y.max()) + 100
                                            st.session_state.y_step_tvp = 200
                                            st.session_state.fs = 0.5

                                        lito(
                                            ax1,
                                            df_pp,
                                            profundidades,
                                            litologias,
                                            prof_final
                                        )

                                        with st.expander("Configurações do Gráfico", expanded=False):
                                            with st.expander("Configurações dos Eixos", expanded=False):
                                                st.selectbox("Inserir ponto analisado", ['Não', 'Sim'], key="ponto_a",index=0)
                                                if st.session_state.option == "Previsão de Geopressões":
                                                    i = 0
                                                    d = True
                                                else:
                                                    i = 1
                                                    d = False
                                                st.selectbox("Visualizar Sapatas", ['Não', 'Sim'], key="spt", index=i, disabled=d)
                                                st.number_input("Eixo X - mínimo", value=7, step=1,
                                                                key="x_min")
                                                st.number_input("Eixo X - máximo", value=23, step=1,
                                                                key="x_max")
                                                st.number_input("Passo do eixo X", value=1, step=1,
                                                                key="x_step_tvp")

                                                st.number_input("Eixo Y - mínimo", value=0, step=100,
                                                                key="y_min")
                                                st.number_input(
                                                    "Eixo Y - máximo",
                                                    value=int(st.session_state.y.max()) + 100,
                                                    step=100,
                                                    key="y_max"
                                                )
                                                st.number_input(
                                                    "Passo do eixo Y",
                                                    value=200,
                                                    step=50,
                                                    key="y_step_tvp"
                                                )

                                                st.number_input(
                                                    "Fator de Segurança da Janela Operacional",
                                                    value=0.5,
                                                    step=0.1,
                                                    key='fs',
                                                    help=(
                                                        "**Fator de Segurança (FS)** ⚠️\n\n"
                                                        "- Coeficiente que reduz a **janela operacional**.\n"
                                                        "- Introduz uma margem de segurança contra **kick** ou **fratura**.\n"
                                                        "- Essencial para o planejamento seguro da perfuração."
                                                    )
                                                )

                                                st.button(
                                                    "Resetar Eixos - Tensões em Volta do Poço",
                                                    on_click=reset_config,
                                                    type="primary",
                                                    use_container_width=True
                                                )

                                            with st.expander("Configurações da Legenda", expanded=False):
                                                st.selectbox("Exibir configuração das tensões", ['Sim', 'Não'],key="ctjo")
                                                st.selectbox(
                                                    "Exibir rosa dos ventos",
                                                    ['Sim', 'Não'],
                                                    key="rosa_jo",
                                                    index=0
                                                )
                                                st.selectbox("Exibir legendas", ['Sim', 'Não'], key="leg", index=1)

                                                if st.session_state.leg == "Sim":
                                                    legendas_pt = {
                                                        "Inferior direito": "lower right",
                                                        "Melhor posição": "best",
                                                        "Superior direito": "upper right",
                                                        "Superior esquerdo": "upper left",
                                                        "Inferior esquerdo": "lower left",
                                                        "Direita": "right",
                                                        "Centro esquerdo": "center left",
                                                        "Centro direito": "center right",
                                                        "Inferior central": "lower center",
                                                        "Superior central": "upper center",
                                                        "Central": "center",
                                                    }

                                                    escolha_legenda = st.selectbox(
                                                        "Posição da legenda",
                                                        list(legendas_pt.keys()),
                                                        index=0
                                                    )

                                                    fontsize_legenda = st.number_input(
                                                        "Tamanho da fonte da legenda",
                                                        min_value=4,
                                                        max_value=40,
                                                        step=1,
                                                        value=6
                                                    )


                                        # Configurações do gráfico
                                        ax.set_title('Janela Operacional (lb/gal)', fontsize=14,
                                                     fontweight='bold')
                                        ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                        ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                        ax.invert_yaxis()
                                        ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                        ax.set_ylim(st.session_state.y_max, st.session_state.y_min)
                                        ax.set_yticks(range(st.session_state.y_min, st.session_state.y_max,
                                                            st.session_state.y_step_tvp))
                                        ax.set_xticks(
                                            range(int(st.session_state.x_min), int(st.session_state.x_max),
                                                  int(st.session_state.x_step_tvp)))
                                        ax.set_xlim(st.session_state.x_min, st.session_state.x_max)
                                        ax.grid(True, linestyle='--', alpha=0.5)

                                        if st.session_state.leg == "Sim":
                                            loc_legenda = legendas_pt[escolha_legenda]
                                            ax.legend(
                                                loc=loc_legenda,
                                                fontsize=fontsize_legenda,
                                                frameon=True,
                                                shadow=True,
                                                fancybox=True,
                                                framealpha=1,
                                                facecolor='white',
                                                edgecolor='gray'
                                            )

                                        add_watermark(
                                            ax,
                                            logo_path="logo2.png",
                                            xy=(0.50, 0.5),
                                            zoom=0.2,
                                            alpha=0.2,
                                            zorder=0
                                        )
                                        plt.subplots_adjust(wspace=0.3)
                                        st.pyplot(st.session_state.fig_jo)

                        # VIZUALIZAÇÃO 3D DAS TENSÕES
                        with tb[1]:
                            if criterio_disponivel(df_tvp):
                                colun1, colun2, colun3 = st.columns(3)
                                with colun1:
                                    todos_parametros = ["σr", "σθ", "σa", "Dir. Tensões principais",
                                                        "Tensões Horizontais", "Coordenadas geográficas",
                                                        "Profundidade", "Direção do poço",
                                                        "Sistemas de coordenadas do poço"]
                                    with st.container(border=True, height=536):
                                        st.markdown('#### Opções de visualização')
                                        vistas = ["Selecione a vista", "Vista de planta",
                                                  "Vista de seção N/S",
                                                  "Vista de seção E/W", "Vista axial do poço",
                                                  "Dentro do Poço"]
                                        view = st.selectbox("Selecione o ponto de visualização", vistas)
                                        st.number_input('Profundidade (m)', key='m2', value=0.00,
                                                        format="%.2f")
                                        mostrar_todos = st.checkbox("Exibir todas as tensões",
                                                                    value=True)
                                        if not mostrar_todos:
                                            selecionados = st.multiselect("Escolha parâmetros a exibir:",
                                                                          todos_parametros)
                                        else:
                                            selecionados = todos_parametros
                                        show_t = st.checkbox('Exibir descrição', value=False,
                                                             key='show_t')
                                        failure = st.checkbox('Mapa de falha na parede do poço',
                                                              value=False, key='fail')
                                        around = st.checkbox('Influência ao redor do poço', value=False,
                                                             key='around')

                                if show_t:
                                    st.session_state.show = True
                                else:
                                    st.session_state.show = False

                                if failure:
                                    st.session_state.ff = True
                                else:
                                    st.session_state.ff = False

                                if around:
                                    st.session_state.arr = True
                                else:
                                    st.session_state.arr = False

                                with colun3:
                                    with st.container(border=True, height=536):
                                        st.markdown('### Configurações')
                                        ra = st.number_input('Raio de investigação', min_value=2)
                                        options = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
                                        op = st.selectbox('Opacidade do mapa de falha', options,
                                                          key='opacity', index=7)
                                        lg = st.selectbox('Exibir linhas de grade', ["Sim", "Não"])

                                # Pega o índice da profundidade mais próxima de m2
                                idx = (df_tvp['Profundidade (m)'] - st.session_state.m2).abs().idxmin()

                                # Seleciona a linha correspondente
                                linha = df_tvp.loc[idx]

                                # Extrai os valores
                                sr = linha['σr efetivo (psi)']
                                sig_t = linha['σθA efetivo (psi)']
                                sa = linha['σa']
                                tvd = linha['Profundidade (m)']
                                pressure = linha['Gradiente de Pressão de Poros (lb/gal)']
                                sig_a = sa * 0.1704 * tvd - pressure * 0.1704 * tvd
                                sig_h = linha['Sh (psi)']
                                sig_H = linha['SH (psi)']
                                ang_theta = linha['θA (°)']
                                ang_azi = linha['Azi']
                                ang_inc = linha['Inc']
                                ang_horizontal = linha['Direção SH']
                                # Criação do gráfico
                                figura = criar_grafico(selecionados, sr, sig_t, sig_a, sig_h, sig_H,
                                                       ang_theta, tvd, ang_azi, ang_inc, ra, op,
                                                       ang_horizontal, view, lg)

                                with colun2:
                                    with st.container(border=True):
                                        st.markdown('#### Visualização 3D das Tensões')
                                        st.plotly_chart(figura, use_container_width=True)

                        # DATAFRAMES
                        with tb[3]:
                            if criterio_disponivel(df_tvp):
                                if uploaded_file:
                                    with st.container(border=True):
                                        try:
                                            st.dataframe(
                                                st.session_state.dados_lito,
                                                use_container_width=True,
                                                hide_index=True
                                            )
                                        except Exception:
                                            pass
                                    with st.container(border=True):
                                        st.dataframe(df_tvp, use_container_width=True, hide_index=True)
                                    with st.container(border=True):
                                        st.dataframe(df_suav, use_container_width=True, hide_index=True)

                    else:
                        st.error('Preencha corretamente a aba "Gradiente de Pressão de Poros"', icon="🚨")
                else:
                    st.error('Preencha corretamente a aba "Gradiente de Sobrecarga"', icon="🚨")
            else:
                st.error('Por favor, insira um documento!', icon="🚨")

    # Critério de Assentamento de Sapatas
    with tabs[5]:
        if uploaded_file:
            if st.session_state.option == "Previsão de Geopressões":
                tab = st.tabs(['Kick Tolerance', 'Dados Calculados'])
                if "recalcular_sapatas" not in st.session_state:
                    st.session_state.recalcular_sapatas = False

                with tab[0]:
                    if "df_suav" in st.session_state:
                        df_suav = st.session_state.df_suav.copy()

                        col1, col2 = st.columns((0.7,1))

                        with col1:
                            with st.container(border=True):
                                coluna1, coluna2 = st.columns(2)

                                with coluna1:
                                    st.segmented_control(
                                        "***Método do Gradiente de Fratura a ser utilizado***",
                                        ["Mohr Coulomb", "Método das Tensões Mínimas"],
                                        selection_mode="single",
                                        default="Mohr Coulomb",
                                        key="metodo_gradiente_fratura",
                                        width="stretch"
                                    )

                                with coluna2:
                                    st.segmented_control(
                                        "***Método de Cálculo do Kick Tolerance a ser utilizado***",
                                        ["Cima para Baixo", "Baixo para Cima"],
                                        selection_mode="single",
                                        default="Cima para Baixo",
                                        key="metodo_kt",
                                        width="stretch"
                                    )

                                st.markdown("### Critério de Assentamento de Sapatas - Kick Tolerance")

                                submitted_sapatas = False

                                with st.form("spt_form", border=False):
                                    with st.expander("Dados", expanded=True):
                                        c1, c2 = st.columns(2)
                                        with c1:
                                            st.number_input(
                                                'Sapata do revestimento condutor',
                                                step=10.0,
                                                format='%.2f',
                                                key='prc',
                                                min_value=0.0,
                                                value=50.
                                            )
                                            st.number_input(
                                                'Sapata do revestimento de superfície',
                                                step=100.0,
                                                format='%.2f',
                                                key='prs',
                                                min_value=0.0,
                                                value=500.
                                            )
                                            st.number_input(
                                                'Margem do Gradiente de Pressão de Poros',
                                                step=.1,
                                                format='%.2f',
                                                key='ms',
                                                min_value=0.0,
                                                value=0.
                                            )
                                            st.number_input(
                                                'Volume do kick',
                                                step=10.,
                                                format='%.2f',
                                                key='vk',
                                                min_value=0.0,
                                                value=10.
                                            )
                                            st.number_input(
                                                'Margem de segurança do Kick Tolerance',
                                                step=.1,
                                                format='%.2f',
                                                key='mskt',
                                                min_value=0.0,
                                                value=.5
                                            )
                                            st.number_input(
                                                'Espessura da camada não permeável',
                                                step=1.,
                                                format='%.2f',
                                                key='ef',
                                                min_value=1.,
                                                value=10.
                                            )

                                        with c2:
                                            st.selectbox(
                                                'OD do revestimento condutor',
                                                ['30"', '20"', '13 3/8"', '9 5/8"'],
                                                key='odrc'
                                            )
                                            st.selectbox(
                                                'OD do revestimento de superfície',
                                                ['30"', '20"', '13 3/8"', '9 5/8"'],
                                                key='odrs',
                                                index=1
                                            )
                                            st.number_input(
                                                'Margem do Gradente de Fratura',
                                                step=.1,
                                                format='%.2f',
                                                key='msf',
                                                min_value=0.0,
                                                value=.0
                                            )
                                            st.number_input(
                                                'Densidade do kick',
                                                step=.5,
                                                format='%.2f',
                                                key='dk',
                                                min_value=0.0,
                                                value=2.
                                            )
                                            st.number_input(
                                                'Comprimento máximo de poço aberto',
                                                step=100.0,
                                                format='%.2f',
                                                key='hk',
                                                min_value=0.0,
                                                value=round((df["Profundidade"].iloc[-1] / 3.) / 50.) * 50.
                                            )

                                        if st.session_state.metodo_kt == "Baixo para Cima":
                                            with c1:
                                                st.number_input(
                                                    'Comprimento mínimo da fase',
                                                    step=100.0,
                                                    format='%.2f',
                                                    key='cmf',
                                                    min_value=0.0,
                                                    value=200.
                                                )

                                            with c2:
                                                st.segmented_control(
                                                    "Condição da última fase",
                                                    ["Sapata definida", "Poço aberto"],
                                                    selection_mode="single",
                                                    default="Sapata definida",
                                                    key="condicao_ultima_fase_b2c",
                                                    width="stretch"
                                                )

                                                if st.session_state.condicao_ultima_fase_b2c == "Sapata definida":
                                                    st.number_input(
                                                        'Profundidade da sapata da última fase',
                                                        step=100.0,
                                                        format='%.2f',
                                                        key='suf',
                                                        min_value=0.0,
                                                        value=df["Profundidade"].iloc[-1]
                                                    )
                                                else:
                                                    st.session_state.suf = float(df["Profundidade"].iloc[-1])

                                        else:
                                            with c2:
                                                st.segmented_control(
                                                    "Condição da última fase",
                                                    ["Sapata definida", "Poço aberto"],
                                                    selection_mode="single",
                                                    default="Poço aberto",
                                                    key="condicao_ultima_fase_c2b",
                                                    width="stretch"
                                                )

                                                if st.session_state.condicao_ultima_fase_c2b == "Sapata definida":
                                                    st.number_input(
                                                        'Profundidade da sapata da última fase',
                                                        step=100.0,
                                                        format='%.2f',
                                                        key='suf_c2b',
                                                        min_value=0.0,
                                                        value=df["Profundidade"].iloc[-1]
                                                    )
                                                else:
                                                    st.session_state.suf_c2b = float(df["Profundidade"].iloc[-1])

                                        st.session_state.pf = df["Profundidade"].iloc[-1]

                                    with st.expander("BHA", expanded=True):
                                        bha_17_5 = pd.DataFrame({
                                            "Elemento do BHA": [
                                                "Broca", "STB", "NMDC", "NMDC", "xBolt", "Gap Sub",
                                                "Pulser Sub xBolt", "UBHO", "NMDC", "DC", "XO",
                                                "DC", "HWDP", "Jar", "HWDP"
                                            ],
                                            "OD (pol)": [
                                                17.5, 9.63, 8.25, 8.25, 8.25, 7.88, 8.0, 7.88,
                                                8.31, 8.0, 8.0, 6.5, 5.0, 6.5, 5.0
                                            ],
                                            "Comprimento (m)": [
                                                0.44, 10.45, 2.91, 2.84, 9.09, 1.12, 1.78, 0.79,
                                                9.21, 18.72, 1.06, 36.86, 55.37, 9.79, 82.37
                                            ]
                                        })

                                        bha_12_25 = pd.DataFrame({
                                            "Elemento do BHA": [
                                                "Broca", "MF", "NMDC", "Telescope", "NMDC", "UBHO",
                                                "DC", "XO", "DC", "HWDP", "Jar", "HWDP"
                                            ],
                                            "OD (pol)": [
                                                12.25, 9.625, 8.00, 8.375, 8.00, 7.875,
                                                8.00, 8.00, 6.75, 5.00, 6.50, 5.00
                                            ],
                                            "Comprimento (m)": [
                                                0.32, 10.55, 5.66, 8.55, 9.22, 0.62,
                                                18.00, 1.10, 35.91, 54.83, 9.50, 81.98
                                            ]
                                        })

                                        bha_8_5 = pd.DataFrame({
                                            "Elemento do BHA": [
                                                "Broca", "MF", "STB", "Monel Curto", "TeleScope",
                                                "Monel", "UBHO", "DC", "HWDP", "Jar", "HWDP"
                                            ],
                                            "OD (pol)": [
                                                8.50, 6.75, 6.75, 6.69, 6.75, 6.75,
                                                6.75, 6.75, 5.00, 6.50, 5.00
                                            ],
                                            "Comprimento (m)": [
                                                0.24, 8.2, 1.3, 5.86, 7.93, 9.02,
                                                0.91, 53.97, 27.36, 9.4, 119.38
                                            ]
                                        })

                                        bha_6_125 = pd.DataFrame({
                                            "Elemento do BHA": [
                                                "Broca", "MF", "STB", "Monel Curto", "TeleScope",
                                                "Monel", "UBHO", "DC", "HWDP", "Jar", "HWDP"
                                            ],
                                            "OD (pol)": [
                                                6.125, 4.75, 4.75, 4.75, 4.75, 4.75,
                                                4.75, 4.75, 4.50, 4.75, 4.50
                                            ],
                                            "Comprimento (m)": [
                                                0.24, 8.2, 1.3, 5.86, 7.93, 9.02,
                                                0.91, 53.97, 27.36, 9.4, 119.38
                                            ]
                                        })

                                        bha_opcoes = {
                                            '17 1/2"': bha_17_5.copy(),
                                            '12 1/4"': bha_12_25.copy(),
                                            '8 1/2"': bha_8_5.copy(),
                                            '6 1/8"': bha_6_125.copy(),
                                        }

                                        if "bha_escolhido" not in st.session_state:
                                            st.session_state.bha_escolhido = '17 1/2"'

                                        coluna1, coluna2 = st.columns(2)

                                        if st.session_state.metodo_kt == "Cima para Baixo":
                                            x = "BHA da fase após o revestimento de superfície"
                                        else:
                                            x = "BHA para a fase final"

                                        with coluna1:
                                            st.markdown(
                                                f"""
                                                <div style="margin-top: 32px;">
                                                    <h5 style="margin-bottom: 0;">
                                                        {x}
                                                    </h5>
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                            )

                                        with coluna2:
                                            with st.container(border=True):
                                                opcoes_bha = ['17 1/2"', '12 1/4"', '8 1/2"', '6 1/8"']
                                                opcoes_bha_disponiveis = opcoes_bha.copy()
                                                od_revest_superficie = str(st.session_state.get("odrs", "")).strip()

                                                if st.session_state.metodo_kt == "Baixo para Cima":
                                                    titulo_bha = "Selecione o BHA da última fase"

                                                    if od_revest_superficie == '13 3/8"':
                                                        opcoes_bha_disponiveis = [
                                                            bha for bha in opcoes_bha_disponiveis if bha != '17 1/2"'
                                                        ]
                                                else:
                                                    titulo_bha = "Selecione o BHA"

                                                if not opcoes_bha_disponiveis:
                                                    st.error("Nenhum BHA disponível para a configuração atual.")
                                                    bha_selecionado = None
                                                else:
                                                    bha_atual = st.session_state.get("bha_escolhido", '12 1/4"')

                                                    if bha_atual not in opcoes_bha_disponiveis:
                                                        bha_atual = opcoes_bha_disponiveis[0]
                                                        st.session_state.bha_escolhido = bha_atual

                                                    bha_selecionado = st.radio(
                                                        titulo_bha,
                                                        options=opcoes_bha_disponiveis,
                                                        index=opcoes_bha_disponiveis.index(bha_atual),
                                                        horizontal=True,
                                                        key="bha_escolhido",
                                                        disabled=False
                                                    )

                                                if bha_selecionado is not None:
                                                    st.session_state.bha_selecionado = bha_selecionado

                                        diametro_poco_por_bha = {
                                            '17 1/2"': 17.5,
                                            '12 1/4"': 12.25,
                                            '8 1/2"': 8.5,
                                            '6 1/8"': 6.125,
                                        }

                                        if bha_selecionado is None:
                                            st.stop()

                                        diametro_poco_pol = diametro_poco_por_bha[bha_selecionado]
                                        diametro_poco_m = diametro_poco_pol * 0.0254

                                        df_bha_padrao = bha_opcoes[bha_selecionado].copy()

                                        chave_edit = f"df_bha_edit_{bha_selecionado}"
                                        chave_final = f"df_bha_final_{bha_selecionado}"

                                        if chave_edit not in st.session_state:
                                            st.session_state[chave_edit] = df_bha_padrao.copy()

                                        df_bha_editado = st.data_editor(
                                            st.session_state[chave_edit],
                                            use_container_width=True,
                                            hide_index=True,
                                            num_rows="dynamic",
                                            key=f"bha_editor_{bha_selecionado}",
                                            column_config={
                                                "Elemento do BHA": st.column_config.TextColumn("Elemento do BHA"),
                                                "OD (pol)": st.column_config.NumberColumn("OD (pol)", format="%.2f"),
                                                "Comprimento (m)": st.column_config.NumberColumn(
                                                    "Comprimento (m)", format="%.2f"
                                                ),
                                            }
                                        )

                                    submitted_sapatas = st.form_submit_button(
                                        "Definir Sapatas",
                                        use_container_width=True,
                                        type="primary"
                                    )

                                    if submitted_sapatas:
                                        st.session_state.recalcular_sapatas = True

                                df_sapata = st.session_state.get("df_sapata_kt", pd.DataFrame()).copy()
                                sapatas_plot = st.session_state.get("sapatas_plot_kt", []).copy()

                                if submitted_sapatas or st.session_state.get("recalcular_sapatas", False):
                                    st.session_state[chave_edit] = pd.DataFrame(df_bha_editado).copy()
                                    st.session_state[chave_final] = calcular_bha(
                                        st.session_state[chave_edit],
                                        diametro_poco_m
                                    )

                                    st.session_state.df_bha_edit = st.session_state[chave_edit].copy()
                                    st.session_state.df_bha_final = st.session_state[chave_final].copy()

                                    df_kick = st.session_state.df_bha_final.copy()

                                    for col in [
                                        "Comprimento (m)",
                                        "Comprimento Acumulado (m)",
                                        "Início do Trecho (m)",
                                        "Fim do Trecho (m)",
                                        "Cap. Anular (m3/m)",
                                        "Vol. (m3)",
                                        "Vol. Acum. (m3)",
                                        "Vol. Acum. (bbl)"
                                    ]:
                                        if col in df_kick.columns:
                                            df_kick[col] = pd.to_numeric(df_kick[col], errors="coerce").fillna(0.0)

                                    vk_bbl = float(st.session_state.vk)
                                    vk_m3 = vk_bbl / 6.28981

                                    volume_restante = vk_m3
                                    altura_kick = 0.0
                                    elemento_topo_kick = "Não definido"
                                    intervalo_elemento_topo_kick = ""

                                    for _, row in df_kick.iterrows():
                                        cap = float(row["Cap. Anular (m3/m)"])
                                        comp = float(row["Comprimento (m)"])
                                        inicio = float(row["Início do Trecho (m)"])
                                        fim = float(row["Fim do Trecho (m)"])
                                        elem = str(row["Elemento do BHA"])

                                        if cap <= 0 or comp <= 0:
                                            continue

                                        vol_trecho = cap * comp

                                        if volume_restante <= vol_trecho:
                                            altura_no_trecho = volume_restante / cap
                                            altura_kick = inicio + altura_no_trecho
                                            elemento_topo_kick = elem
                                            intervalo_elemento_topo_kick = f"{inicio:.2f}–{fim:.2f} m"
                                            volume_restante = 0.0
                                            break
                                        else:
                                            volume_restante -= vol_trecho

                                    if volume_restante > 1e-9:
                                        altura_kick = float(df_kick["Comprimento Acumulado (m)"].max())
                                        elemento_topo_kick = "Acima do último elemento do BHA"
                                        intervalo_elemento_topo_kick = ""

                                    st.session_state.altura_kick_calculada = altura_kick
                                    st.session_state.volume_kick_bbl = vk_bbl
                                    st.session_state.volume_kick_m3 = vk_m3
                                    st.session_state.elemento_topo_kick = elemento_topo_kick
                                    st.session_state.intervalo_elemento_topo_kick = intervalo_elemento_topo_kick

                                    st.session_state.df_sapata_kt = pd.DataFrame()
                                    st.session_state.historico_fases_c2b = []
                                    st.session_state.historico_fases_b2c = []
                                    st.session_state.sapatas_kick_c2b = []
                                    st.session_state.sapatas_kick_b2c = []
                                    st.session_state.curvas_kt_plot = []
                                    st.session_state.curvas_kt_b2c = []
                                    st.session_state.sapatas_plot_kt = []
                                    st.session_state.intervalos_sem_sapata_b2c = []
                                    st.session_state.intervalos_fase_curta_b2c = []

                                    metodo_fratura = st.session_state.get(
                                        "metodo_gradiente_fratura",
                                        "Mohr Coulomb"
                                    )

                                    grad_fratura_mohr = pd.to_numeric(
                                        df_tvp[["Tração Superior (σθA)", "Tração Superior (σθB)"]].min(axis=1),
                                        errors="coerce"
                                    ).reset_index(drop=True)

                                    if metodo_fratura == "Método das Tensões Mínimas":
                                        if (
                                                "df_f" in st.session_state
                                                and isinstance(st.session_state.df_f, pd.DataFrame)
                                                and not st.session_state.df_f.empty
                                                and "Gradiente de Fratura (lb/gal)" in st.session_state.df_f.columns
                                        ):
                                            grad_fratura_sapata = pd.to_numeric(
                                                st.session_state.df_f["Gradiente de Fratura (lb/gal)"],
                                                errors="coerce"
                                            ).reset_index(drop=True)
                                        else:
                                            st.warning(
                                                "O Gradiente de Fratura pelo Método das Tensões Mínimas ainda não foi calculado. "
                                                "Foi utilizado o Gradiente de Fratura por Mohr Coulomb."
                                            )
                                            grad_fratura_sapata = grad_fratura_mohr.copy()

                                    else:
                                        grad_fratura_sapata = grad_fratura_mohr.copy()

                                    df_sapata = pd.DataFrame({
                                        "Profundidade (m)": pd.to_numeric(
                                            df_tvp["Profundidade (m)"], errors="coerce"
                                        ).reset_index(drop=True),
                                        "Gradiente de Pressão de Poros (lb/gal)": pd.to_numeric(
                                            df_tvp["Gradiente de Pressão de Poros (lb/gal)"], errors="coerce"
                                        ).reset_index(drop=True),
                                        "Gradiente de Fratura (lb/gal)": grad_fratura_sapata
                                    }).copy()

                                    df_sapata["Gradiente de Pressão de Poros + Margem (lb/gal)"] = (
                                            df_sapata["Gradiente de Pressão de Poros (lb/gal)"] + float(st.session_state.ms)
                                    )

                                    df_sapata["Gradiente de Fratura - Margem (lb/gal)"] = (
                                            df_sapata["Gradiente de Fratura (lb/gal)"] - float(st.session_state.msf)
                                    )

                                    df_sapata = (
                                        df_sapata
                                        .dropna(subset=[
                                            "Profundidade (m)",
                                            "Gradiente de Pressão de Poros (lb/gal)",
                                            "Gradiente de Fratura (lb/gal)"
                                        ])
                                        .sort_values("Profundidade (m)")
                                        .reset_index(drop=True)
                                    )

                                    df_sapata = df_sapata[
                                        [
                                            "Profundidade (m)",
                                            "Gradiente de Pressão de Poros (lb/gal)",
                                            "Gradiente de Pressão de Poros + Margem (lb/gal)",
                                            "Gradiente de Fratura - Margem (lb/gal)",
                                            "Gradiente de Fratura (lb/gal)"
                                        ]
                                    ]

                                    df_sapata["Gradiente de Fratura (lb/gal)"] = pd.to_numeric(
                                        df_sapata["Gradiente de Fratura (lb/gal)"], errors="coerce"
                                    )

                                    df_sapata = df_sapata.dropna(
                                        subset=["Profundidade (m)", "Gradiente de Fratura (lb/gal)"]
                                    ).sort_values("Profundidade (m)").reset_index(drop=True)

                                    if "decisoes_ajuste_arenito" not in st.session_state:
                                        st.session_state.decisoes_ajuste_arenito = {}

                                    if "pendencia_ajuste_arenito" not in st.session_state:
                                        st.session_state.pendencia_ajuste_arenito = None

                                    if st.session_state.metodo_kt == "Cima para Baixo":
                                        prof_sapata_superficie = float(st.session_state.prs)

                                        idx_mais_proximo = (
                                                df_sapata["Profundidade (m)"] - prof_sapata_superficie
                                        ).abs().idxmin()

                                        prof_ref_fratura = float(df_sapata.loc[idx_mais_proximo, "Profundidade (m)"])
                                        grad_fratura_ref = float(
                                            df_sapata.loc[idx_mais_proximo, "Gradiente de Fratura (lb/gal)"]
                                        )

                                        st.session_state.prof_ref_fratura_sapata = prof_ref_fratura
                                        st.session_state.grad_fratura_sapata_superficie = grad_fratura_ref

                                        prof_ref_fratura = float(st.session_state.prs)

                                        idx_ref_fratura = (df_sapata["Profundidade (m)"] - prof_ref_fratura).abs().idxmin()
                                        prof_ref_fratura = float(df_sapata.loc[idx_ref_fratura, "Profundidade (m)"])
                                        grad_fratura_ref = float(
                                            df_sapata.loc[idx_ref_fratura, "Gradiente de Fratura (lb/gal)"]
                                        )

                                        mask_calculo_kt = df_sapata["Profundidade (m)"] >= prof_ref_fratura

                                        rho_kt = pd.Series(index=df_sapata.index, dtype=float)

                                        rho_kt.loc[mask_calculo_kt] = (
                                                ((prof_ref_fratura / df_sapata.loc[mask_calculo_kt, "Profundidade (m)"]) *
                                                 ((grad_fratura_ref - st.session_state.msf) -
                                                  df_sapata.loc[
                                                      mask_calculo_kt, "Gradiente de Pressão de Poros + Margem (lb/gal)"]))
                                                -
                                                ((altura_kick / df_sapata.loc[mask_calculo_kt, "Profundidade (m)"]) *
                                                 (df_sapata.loc[
                                                      mask_calculo_kt, "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                                  - st.session_state.dk))
                                                +
                                                df_sapata.loc[
                                                    mask_calculo_kt, "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                        )

                                        delta_rho_kt = pd.Series(index=df_sapata.index, dtype=float)

                                        delta_rho_kt.loc[mask_calculo_kt] = (
                                                rho_kt.loc[mask_calculo_kt]
                                                - df_sapata.loc[
                                                    mask_calculo_kt, "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                        )

                                        mask_kt_limite = (
                                                delta_rho_kt.notna() &
                                                (delta_rho_kt <= st.session_state.mskt)
                                        )

                                        idx_kt_limite = None
                                        prof_kt_limite = None
                                        if mask_kt_limite.any():
                                            idx_kt_limite = mask_kt_limite[mask_kt_limite].index[0]
                                            prof_kt_limite = float(df_sapata.loc[idx_kt_limite, "Profundidade (m)"])

                                        mapa_sapata_por_bha = {
                                            '17 1/2"': '13 3/8"',
                                            '12 1/4"': '9 5/8"',
                                            '8 1/2"': '7"',
                                            '6 1/8"': '5 1/2"'
                                        }

                                        ordem_bhas = ['17 1/2"', '12 1/4"', '8 1/2"', '6 1/8"']

                                        bha_inicial = st.session_state.get("bha_selecionado", '12 1/4"')
                                        if bha_inicial not in ordem_bhas:
                                            bha_inicial = '12 1/4"'

                                        idx_bha_inicial = ordem_bhas.index(bha_inicial)
                                        bhas_restantes = ordem_bhas[idx_bha_inicial:]

                                        prof_final_poco = float(df_sapata["Profundidade (m)"].max())

                                        condicao_ultima_fase_c2b = st.session_state.get(
                                            "condicao_ultima_fase_c2b",
                                            "Poço aberto"
                                        )

                                        prof_sapata_manual_c2b = None
                                        manual_c2b_ativa = False
                                        manual_c2b_assentada = False
                                        tol_sapata_manual_c2b = 0.5

                                        if condicao_ultima_fase_c2b == "Sapata definida":
                                            try:
                                                prof_sapata_manual_c2b = float(
                                                    st.session_state.get("suf_c2b", prof_final_poco)
                                                )
                                            except (TypeError, ValueError):
                                                prof_sapata_manual_c2b = prof_final_poco

                                            # limita a sapata manual ao intervalo válido do poço
                                            prof_sapata_manual_c2b = max(
                                                float(prof_sapata_superficie),
                                                min(float(prof_sapata_manual_c2b), float(prof_final_poco))
                                            )

                                            manual_c2b_ativa = (
                                                    prof_sapata_manual_c2b > float(
                                                prof_sapata_superficie) + tol_sapata_manual_c2b
                                                    and prof_sapata_manual_c2b <= float(
                                                prof_final_poco) + tol_sapata_manual_c2b
                                            )

                                        sapatas_calculadas = []
                                        historico_fases = []
                                        curvas_kt_plot = []

                                        prof_sapata_atual = float(prof_sapata_superficie)

                                        rho_kt_acumulado = pd.Series(np.nan, index=df_sapata.index, dtype=float)
                                        delta_rho_kt_acumulado = pd.Series(np.nan, index=df_sapata.index, dtype=float)

                                        for fase_idx, bha_fase in enumerate(bhas_restantes, start=1):
                                            if prof_sapata_atual >= prof_final_poco:
                                                break

                                            chave_final_fase = f"df_bha_final_{bha_fase}"

                                            if chave_final_fase in st.session_state and isinstance(
                                                    st.session_state[chave_final_fase], pd.DataFrame
                                            ):
                                                df_bha_fase = st.session_state[chave_final_fase].copy()
                                            else:
                                                diametro_poco_por_bha_fase = {
                                                    '17 1/2"': 17.5,
                                                    '12 1/4"': 12.25,
                                                    '8 1/2"': 8.5,
                                                    '6 1/8"': 6.125,
                                                }
                                                diametro_poco_m_fase = diametro_poco_por_bha_fase[bha_fase] * 0.0254
                                                df_bha_fase = calcular_bha(
                                                    bha_opcoes[bha_fase].copy(),
                                                    diametro_poco_m_fase
                                                )

                                            (
                                                altura_kick_fase,
                                                elemento_topo_kick_fase,
                                                intervalo_topo_kick_fase
                                            ) = calcular_altura_kick_por_bha(
                                                df_bha_fase,
                                                st.session_state.vk
                                            )

                                            idx_ref_fratura = (
                                                    df_sapata["Profundidade (m)"] - prof_sapata_atual
                                            ).abs().idxmin()
                                            prof_ref_fratura_fase = float(
                                                df_sapata.loc[idx_ref_fratura, "Profundidade (m)"]
                                            )
                                            grad_fratura_ref_fase = float(
                                                df_sapata.loc[idx_ref_fratura, "Gradiente de Fratura (lb/gal)"]
                                            )

                                            mask_calculo_fase = df_sapata["Profundidade (m)"] >= prof_ref_fratura_fase

                                            rho_kt = pd.Series(np.nan, index=df_sapata.index, dtype=float)
                                            delta_rho_kt = pd.Series(np.nan, index=df_sapata.index, dtype=float)

                                            rho_kt.loc[mask_calculo_fase] = (
                                                    ((prof_ref_fratura_fase / df_sapata.loc[
                                                        mask_calculo_fase, "Profundidade (m)"]) *
                                                     ((grad_fratura_ref_fase - st.session_state.msf) -
                                                      df_sapata.loc[
                                                          mask_calculo_fase,
                                                          "Gradiente de Pressão de Poros + Margem (lb/gal)"]))
                                                    -
                                                    ((altura_kick_fase / df_sapata.loc[
                                                        mask_calculo_fase, "Profundidade (m)"]) *
                                                     (df_sapata.loc[
                                                          mask_calculo_fase,
                                                          "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                                      - st.session_state.dk))
                                                    +
                                                    df_sapata.loc[
                                                        mask_calculo_fase, "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                            )

                                            delta_rho_kt.loc[mask_calculo_fase] = (
                                                    rho_kt.loc[mask_calculo_fase]
                                                    - df_sapata.loc[
                                                        mask_calculo_fase,
                                                        "Gradiente de Pressão de Poros + Margem (lb/gal)"]
                                            )

                                            if manual_c2b_assentada:
                                                mask_preencher = rho_kt.notna()

                                                rho_kt_acumulado.loc[mask_preencher] = rho_kt.loc[mask_preencher]
                                                delta_rho_kt_acumulado.loc[mask_preencher] = delta_rho_kt.loc[
                                                    mask_preencher]

                                                curvas_kt_plot.append({
                                                    "bha": bha_fase,
                                                    "prof": df_sapata.loc[
                                                        mask_preencher, "Profundidade (m)"
                                                    ].to_numpy(dtype=float),
                                                    "rho_kt": rho_kt.loc[mask_preencher].to_numpy(dtype=float)
                                                })

                                                historico_fases.append({
                                                    "bha": bha_fase,
                                                    "prof_sapata_informada": float(prof_sapata_atual),
                                                    "prof_ref_fratura": float(prof_ref_fratura_fase),
                                                    "grad_fratura_ref": float(grad_fratura_ref_fase),
                                                    "altura_kick": float(altura_kick_fase),
                                                    "elemento_topo_kick": elemento_topo_kick_fase,
                                                    "intervalo_topo_kick": intervalo_topo_kick_fase,
                                                    "prof_sapata_calc": None,
                                                    "criterio": "Trecho final em poço aberto após sapata definida pelo usuário."
                                                })

                                                break

                                            mask_kt_limite = (
                                                    delta_rho_kt.notna() &
                                                    (delta_rho_kt <= st.session_state.mskt)
                                            )

                                            idx_kt_limite = None
                                            prof_kt_limite = None
                                            if mask_kt_limite.any():
                                                idx_kt_limite = mask_kt_limite[mask_kt_limite].index[0]
                                                prof_kt_limite = float(df_sapata.loc[idx_kt_limite, "Profundidade (m)"])

                                            prof_alvo_hk = float(prof_sapata_atual) + float(st.session_state.hk)

                                            mask_hk = df_sapata["Profundidade (m)"] >= prof_alvo_hk

                                            idx_hk = None
                                            prof_hk = None
                                            if mask_hk.any():
                                                idx_hk = mask_hk[mask_hk].index[0]
                                                prof_hk = float(df_sapata.loc[idx_hk, "Profundidade (m)"])

                                            idx_sapata_manual_c2b = None
                                            prof_sapata_manual_calc_c2b = None

                                            if (
                                                    manual_c2b_ativa
                                                    and not manual_c2b_assentada
                                                    and prof_sapata_manual_c2b is not None
                                                    and float(prof_sapata_atual) < float(
                                                prof_sapata_manual_c2b) <= float(
                                                prof_final_poco) + tol_sapata_manual_c2b
                                            ):
                                                if chegou_na_profundidade_final(
                                                        prof_sapata_manual_c2b,
                                                        base_final=prof_final_poco,
                                                        tol=tol_sapata_manual_c2b
                                                ):
                                                    prof_sapata_manual_calc_c2b = float(prof_final_poco)
                                                    idx_sapata_manual_c2b = df_sapata["Profundidade (m)"].idxmax()
                                                else:
                                                    prof_sapata_manual_calc_c2b = float(prof_sapata_manual_c2b)
                                                    idx_sapata_manual_c2b = (
                                                            df_sapata["Profundidade (m)"] - float(
                                                        prof_sapata_manual_calc_c2b)
                                                    ).abs().idxmin()

                                            candidatos = []

                                            if idx_kt_limite is not None:
                                                candidatos.append(
                                                    (idx_kt_limite, prof_kt_limite, "Kick tolerance atingido.")
                                                )

                                            if idx_hk is not None:
                                                candidatos.append(
                                                    (idx_hk, prof_hk, "Comprimento máximo de poço aberto.")
                                                )

                                            if idx_sapata_manual_c2b is not None:
                                                candidatos.append(
                                                    (
                                                        idx_sapata_manual_c2b,
                                                        prof_sapata_manual_calc_c2b,
                                                        "Sapata definida pelo usuário para a última fase."
                                                    )
                                                )

                                            if not candidatos:
                                                mask_preencher = rho_kt.notna()
                                                rho_kt_acumulado.loc[mask_preencher] = rho_kt.loc[mask_preencher]
                                                delta_rho_kt_acumulado.loc[mask_preencher] = (
                                                    delta_rho_kt.loc[mask_preencher]
                                                )

                                                curvas_kt_plot.append({
                                                    "bha": bha_fase,
                                                    "prof": df_sapata.loc[
                                                        mask_preencher, "Profundidade (m)"
                                                    ].to_numpy(dtype=float),
                                                    "rho_kt": rho_kt.loc[mask_preencher].to_numpy(dtype=float)
                                                })

                                                historico_fases.append({
                                                    "bha": bha_fase,
                                                    "prof_sapata_informada": float(prof_sapata_atual),
                                                    "prof_ref_fratura": float(prof_ref_fratura_fase),
                                                    "grad_fratura_ref": float(grad_fratura_ref_fase),
                                                    "altura_kick": float(altura_kick_fase),
                                                    "elemento_topo_kick": elemento_topo_kick_fase,
                                                    "intervalo_topo_kick": intervalo_topo_kick_fase,
                                                    "prof_sapata_calc": None,
                                                    "criterio": "Não atingido até o fim dos dados de perfilagem."
                                                })
                                                break

                                            idx_stop, prof_sapata_nova, criterio_sapata = min(
                                                candidatos, key=lambda x: x[1]
                                            )

                                            eh_sapata_manual_c2b = criterio_sapata.startswith(
                                                "Sapata definida pelo usuário"
                                            )

                                            if (
                                                    chegou_na_profundidade_final(
                                                        prof_sapata_nova,
                                                        base_final=prof_final_poco,
                                                        tol=0.5
                                                    )
                                                    and not eh_sapata_manual_c2b
                                            ):
                                                mask_preencher = rho_kt.notna()

                                                rho_kt_acumulado.loc[mask_preencher] = rho_kt.loc[mask_preencher]
                                                delta_rho_kt_acumulado.loc[mask_preencher] = (
                                                    delta_rho_kt.loc[mask_preencher]
                                                )

                                                curvas_kt_plot.append({
                                                    "bha": bha_fase,
                                                    "prof": df_sapata.loc[
                                                        mask_preencher, "Profundidade (m)"
                                                    ].to_numpy(dtype=float),
                                                    "rho_kt": rho_kt.loc[mask_preencher].to_numpy(dtype=float)
                                                })

                                                historico_fases.append({
                                                    "bha": bha_fase,
                                                    "prof_sapata_informada": float(prof_sapata_atual),
                                                    "prof_ref_fratura": float(prof_ref_fratura_fase),
                                                    "grad_fratura_ref": float(grad_fratura_ref_fase),
                                                    "altura_kick": float(altura_kick_fase),
                                                    "elemento_topo_kick": elemento_topo_kick_fase,
                                                    "intervalo_topo_kick": intervalo_topo_kick_fase,
                                                    "prof_sapata_calc": None,
                                                    "criterio": "Não atingido até o fim dos dados de perfilagem."
                                                })

                                                break

                                            diametro_sapata = mapa_sapata_por_bha.get(bha_fase)
                                            nome_sapata = (
                                                f'Sapata {diametro_sapata}'
                                                if diametro_sapata is not None
                                                else "Sapata"
                                            )

                                            prof_sapata_original = float(prof_sapata_nova)

                                            info_folhelho = encontrar_folhelho_acima_do_arenito(
                                                prof_sapata=prof_sapata_original,
                                                profundidades=profundidades,
                                                litologias=litologias,
                                                base_final=float(df_sapata["Profundidade (m)"].max())
                                            )

                                            if info_folhelho is not None:
                                                decision_id = (
                                                    f"fase_{fase_idx}"
                                                    f"|bha_{bha_fase}"
                                                    f"|sapata_atual_{float(prof_sapata_atual):.2f}"
                                                    f"|sapata_calc_{float(prof_sapata_original):.2f}"
                                                )

                                                decisoes = st.session_state.get("decisoes_ajuste_arenito", {})

                                                if decision_id not in decisoes:
                                                    st.session_state.pendencia_ajuste_arenito = {
                                                        "decision_id": decision_id,
                                                        "fase_idx": fase_idx,
                                                        "bha": bha_fase,
                                                        "nome_sapata": nome_sapata,
                                                        "prof_original": float(prof_sapata_original),
                                                        "prof_ajustada": (
                                                            float(info_folhelho["prof_ajustada"])
                                                            if info_folhelho.get("prof_ajustada") is not None
                                                            else None
                                                        ),
                                                        "motivo": info_folhelho.get("motivo"),
                                                        "ajuste_disponivel": info_folhelho.get("ajuste_disponivel",
                                                                                               False),
                                                        "intervalo_atual": info_folhelho.get("intervalo_atual", {}),
                                                        "esp_min_nao_perm": info_folhelho.get(
                                                            "esp_min_nao_perm",
                                                            st.session_state.get("ef", 10.0)
                                                        ),
                                                    }

                                                    confirmar_ajuste_sapata_arenito()
                                                    st.stop()

                                                if decisoes.get(decision_id, False) and info_folhelho.get(
                                                        "ajuste_disponivel", False):
                                                    prof_sapata_nova = float(info_folhelho["prof_ajustada"])

                                                    if prof_sapata_nova > float(prof_sapata_atual):
                                                        esp_min_nao_perm = float(
                                                            info_folhelho.get("esp_min_nao_perm",
                                                                              st.session_state.get("ef", 10.0))
                                                        )

                                                        criterio_sapata = (
                                                            f"{criterio_sapata} Ajustada para Formação Não Permeável "
                                                            f"com espessura mínima de {esp_min_nao_perm:.2f} m acima."
                                                        )

                                            if float(prof_sapata_nova) <= float(prof_sapata_atual):
                                                prof_sapata_nova = prof_sapata_original

                                            idx_stop = (
                                                    df_sapata["Profundidade (m)"] - float(prof_sapata_nova)
                                            ).abs().idxmin()

                                            rho_kt.loc[idx_stop:] = np.nan
                                            delta_rho_kt.loc[idx_stop:] = np.nan

                                            mask_preencher = rho_kt.notna()
                                            rho_kt_acumulado.loc[mask_preencher] = rho_kt.loc[mask_preencher]
                                            delta_rho_kt_acumulado.loc[mask_preencher] = delta_rho_kt.loc[mask_preencher]

                                            curvas_kt_plot.append({
                                                "bha": bha_fase,
                                                "prof": df_sapata.loc[
                                                    mask_preencher, "Profundidade (m)"
                                                ].to_numpy(dtype=float),
                                                "rho_kt": rho_kt.loc[mask_preencher].to_numpy(dtype=float)
                                            })

                                            sapatas_calculadas.append({
                                                "prof": float(prof_sapata_nova),
                                                "nome": nome_sapata,
                                                "cor": "black",
                                                "bha": bha_fase,
                                                "criterio": criterio_sapata,
                                                "prof_ref_fratura": float(prof_ref_fratura_fase),
                                                "grad_fratura_ref": float(grad_fratura_ref_fase),
                                                "prof_sapata_informada": float(prof_sapata_atual),
                                                "altura_kick": float(altura_kick_fase),
                                                "elemento_topo_kick": elemento_topo_kick_fase,
                                                "intervalo_topo_kick": intervalo_topo_kick_fase
                                            })

                                            historico_fases.append({
                                                "bha": bha_fase,
                                                "prof_sapata_informada": float(prof_sapata_atual),
                                                "prof_ref_fratura": float(prof_ref_fratura_fase),
                                                "grad_fratura_ref": float(grad_fratura_ref_fase),
                                                "altura_kick": float(altura_kick_fase),
                                                "elemento_topo_kick": elemento_topo_kick_fase,
                                                "intervalo_topo_kick": intervalo_topo_kick_fase,
                                                "prof_sapata_calc": float(prof_sapata_nova),
                                                "criterio": criterio_sapata
                                            })

                                            prof_sapata_atual = float(prof_sapata_nova)

                                            if eh_sapata_manual_c2b:
                                                manual_c2b_assentada = True
                                                continue

                                            if prof_sapata_atual >= prof_final_poco:
                                                break

                                        for col_drop in ["ρkt", "Δρkt"]:
                                            if col_drop in df_sapata.columns:
                                                df_sapata.drop(columns=[col_drop], inplace=True)

                                        df_sapata.insert(
                                            loc=df_sapata.columns.get_loc('Gradiente de Fratura (lb/gal)') + 1,
                                            column='ρkt',
                                            value=rho_kt_acumulado
                                        )

                                        df_sapata.insert(
                                            loc=df_sapata.columns.get_loc('ρkt') + 1,
                                            column='Δρkt',
                                            value=delta_rho_kt_acumulado
                                        )

                                        sapatas_plot = []

                                        if "prc" in st.session_state and pd.notna(st.session_state.prc):
                                            od_revest_condutor = st.session_state.get("odrc", '20"')
                                            sapatas_plot.append({
                                                "prof": float(st.session_state.prc),
                                                "nome": f"Sapata {od_revest_condutor}",
                                                "cor": "black"
                                            })

                                        if prof_sapata_superficie is not None and pd.notna(prof_sapata_superficie):
                                            od_revest_superficie = st.session_state.get("odrs", '13 3/8"')
                                            sapatas_plot.append({
                                                "prof": float(prof_sapata_superficie),
                                                "nome": f"Sapata {od_revest_superficie}",
                                                "cor": "black",
                                                "tipo": "superficie"
                                            })

                                        for sap in sapatas_calculadas:
                                            if sap["prof"] is not None and pd.notna(sap["prof"]):
                                                sapatas_plot.append({
                                                    "prof": float(sap["prof"]),
                                                    "nome": sap.get("nome", "Sapata"),
                                                    "cor": sap.get("cor", "black"),
                                                    "bha": sap.get("bha", None),
                                                    "criterio": sap.get("criterio", ""),
                                                    "tipo": "calculada"
                                                })

                                        st.session_state.sapatas_kick_c2b = sapatas_calculadas
                                        st.session_state.historico_fases_c2b = historico_fases
                                        st.session_state.curvas_kt_plot = curvas_kt_plot
                                        st.session_state.df_sapata_kt = df_sapata.copy()
                                        st.session_state.sapatas_plot_kt = sapatas_plot
                                        st.session_state.fig_esquematico_asp = None
                                        st.session_state.df_esquematico_asp = None
                                        st.session_state.pendencia_ajuste_arenito = None
                                        st.session_state.recalcular_sapatas = False

                                    else:
                                        df_sapata = df_sapata.copy()
                                        df_sapata["gf_kt (lb/gal)"] = np.nan

                                        mapa_sapata_por_bha = {
                                            '17 1/2"': '13 3/8"',
                                            '12 1/4"': '9 5/8"',
                                            '8 1/2"': '7"',
                                            '6 1/8"': '5 1/2"'
                                        }

                                        diametro_poco_por_bha = {
                                            '17 1/2"': 17.5,
                                            '12 1/4"': 12.25,
                                            '8 1/2"': 8.5,
                                            '6 1/8"': 6.125,
                                        }

                                        ordem_bha_baixo_cima = ['6 1/8"', '8 1/2"', '12 1/4"', '17 1/2"']

                                        bha_inicial_b2c = st.session_state.bha_escolhido

                                        if bha_inicial_b2c not in ordem_bha_baixo_cima:
                                            st.warning("BHA inicial inválido para o cálculo Baixo para Cima.")
                                            st.session_state.sapatas_kick_b2c = []
                                            st.session_state.curvas_kt_b2c = []
                                            st.session_state.historico_fases_b2c = []
                                            st.session_state.df_sapata_kt = df_sapata.copy()
                                        else:
                                            idx_inicio = ordem_bha_baixo_cima.index(bha_inicial_b2c)
                                            ordem_filtrada = ordem_bha_baixo_cima[idx_inicio:]
                                            bhas_disponiveis = [bha for bha in ordem_filtrada if bha in bha_opcoes]

                                        od_revest_condutor = str(st.session_state.get("odrc", "")).strip()
                                        od_revest_superficie = str(st.session_state.get("odrs", "")).strip()

                                        sapatas_existentes = {od_revest_condutor, od_revest_superficie}

                                        if not bhas_disponiveis:
                                            st.warning("Nenhum BHA válido encontrado para o cálculo Baixo para Cima.")
                                            st.session_state.sapatas_kick_b2c = []
                                            st.session_state.curvas_kt_b2c = []
                                            st.session_state.historico_fases_b2c = []
                                            st.session_state.df_sapata_kt = df_sapata.copy()

                                        else:
                                            sapatas_calculadas = []
                                            historico_fases = []
                                            curvas_kt_plot = []
                                            intervalos_sem_sapata = []
                                            intervalos_fase_curta = []

                                            prof_col = pd.to_numeric(df_sapata["Profundidade (m)"], errors="coerce")
                                            profundidade_minima_sapata = float(st.session_state.prs)

                                            profundidade_maxima_perfil = float(prof_col.max())

                                            ultima_fase_poco_aberto = (
                                                    st.session_state.get("condicao_ultima_fase_b2c", "Sapata definida")
                                                    == "Poço aberto"
                                            )

                                            if ultima_fase_poco_aberto:
                                                profundidade_ultima_sapata = profundidade_maxima_perfil
                                            else:
                                                profundidade_ultima_sapata = float(st.session_state.suf)

                                            profundidade_ultima_sapata = max(
                                                profundidade_minima_sapata,
                                                min(profundidade_ultima_sapata, profundidade_maxima_perfil)
                                            )

                                            idx_inicio_b2c = prof_col.sub(profundidade_ultima_sapata).abs().idxmin()
                                            prof_fundo = float(df_sapata.loc[idx_inicio_b2c, "Profundidade (m)"])

                                            profundidade_limite_superior = prof_fundo

                                            idx_sapata_anterior = idx_inicio_b2c

                                            for i_bha, bha_fase in enumerate(bhas_disponiveis):
                                                if profundidade_limite_superior <= profundidade_minima_sapata:
                                                    break

                                                chave_final_fase = f"df_bha_final_{bha_fase}"
                                                if (
                                                        chave_final_fase in st.session_state
                                                        and isinstance(st.session_state[chave_final_fase], pd.DataFrame)
                                                ):
                                                    df_bha_fase = st.session_state[chave_final_fase].copy()
                                                else:
                                                    if bha_fase not in diametro_poco_por_bha:
                                                        st.warning(f"Diâmetro do poço não mapeado para o BHA {bha_fase}.")
                                                        continue

                                                    diametro_poco_m_fase = diametro_poco_por_bha[bha_fase] * 0.0254

                                                    df_bha_fase = calcular_bha(
                                                        bha_opcoes[bha_fase].copy(),
                                                        diametro_poco_m_fase
                                                    )

                                                try:
                                                    (
                                                        altura_kick_fase,
                                                        elemento_topo_kick_fase,
                                                        intervalo_topo_kick_fase
                                                    ) = calcular_altura_kick_por_bha(
                                                        df_bha_fase,
                                                        st.session_state.vk
                                                    )
                                                except Exception as e:
                                                    st.warning(
                                                        f"Não foi possível calcular a altura do kick para o BHA {bha_fase}: {e}"
                                                    )
                                                    continue

                                                mask_intervalo = (
                                                        (prof_col >= profundidade_minima_sapata) &
                                                        (prof_col <= profundidade_limite_superior)
                                                )

                                                df_intervalo = df_sapata.loc[mask_intervalo].copy()

                                                if df_intervalo.empty or len(df_intervalo) < 2:
                                                    break

                                                df_intervalo = df_intervalo.sort_values("Profundidade (m)").copy()

                                                prof_intervalo = pd.to_numeric(
                                                    df_intervalo["Profundidade (m)"], errors="coerce"
                                                )

                                                gf_limite = pd.to_numeric(
                                                    df_intervalo["Gradiente de Fratura - Margem (lb/gal)"],
                                                    errors="coerce"
                                                )

                                                idx_ref = idx_sapata_anterior

                                                prof_ref = float(df_sapata.loc[idx_ref, "Profundidade (m)"])
                                                gpp_ref = float(
                                                    df_sapata.loc[
                                                        idx_ref, "Gradiente de Pressão de Poros + Margem (lb/gal)"
                                                    ]
                                                )

                                                gf_kt = (
                                                        ((prof_ref / prof_intervalo) * (
                                                                float(st.session_state.mskt) + float(st.session_state.ms)))
                                                        + ((float(altura_kick_fase) / prof_intervalo) * (
                                                        gpp_ref - float(st.session_state.dk)))
                                                        + gpp_ref
                                                )

                                                df_intervalo["gf_kt (lb/gal)"] = gf_kt
                                                df_sapata.loc[df_intervalo.index, "gf_kt (lb/gal)"] = df_intervalo[
                                                    "gf_kt (lb/gal)"
                                                ]

                                                cond_critica = gf_kt >= gf_limite - st.session_state.mskt

                                                profundidade_sapata_nova = None
                                                idx_sapata = None

                                                if cond_critica.any():
                                                    idx_critico = cond_critica[cond_critica].index[-1]
                                                    pos_critico = df_intervalo.index.get_loc(idx_critico)

                                                    if pos_critico < len(df_intervalo.index) - 1:
                                                        idx_sapata = df_intervalo.index[pos_critico + 1]
                                                    else:
                                                        idx_sapata = idx_critico

                                                    profundidade_sapata_nova = float(
                                                        df_sapata.loc[idx_sapata, "Profundidade (m)"]
                                                    )
                                                    criterio_sapata = "Kick tolerance atingido."
                                                else:
                                                    profundidade_sapata_nova = profundidade_minima_sapata
                                                    idx_sapata = prof_col.sub(profundidade_sapata_nova).abs().idxmin()
                                                    criterio_sapata = "Não atingido até o revestimento de superfície."

                                                prof_alvo_hk_b2c = (
                                                        profundidade_limite_superior - float(st.session_state.hk)
                                                )

                                                if (
                                                        prof_alvo_hk_b2c > profundidade_minima_sapata
                                                        and profundidade_sapata_nova < prof_alvo_hk_b2c
                                                ):
                                                    profundidade_sapata_nova = prof_alvo_hk_b2c
                                                    idx_sapata = prof_col.sub(profundidade_sapata_nova).abs().idxmin()
                                                    criterio_sapata = "Comprimento máximo de poço aberto."

                                                if profundidade_sapata_nova < profundidade_minima_sapata:
                                                    profundidade_sapata_nova = profundidade_minima_sapata
                                                    idx_sapata = prof_col.sub(profundidade_sapata_nova).abs().idxmin()

                                                # Validação litológica da sapata no método Baixo para Cima
                                                deve_validar_litologia_b2c = False
                                                bha_sapata_b2c = None
                                                nome_sapata_b2c = None

                                                if i_bha < len(bhas_disponiveis) - 1:
                                                    bha_sapata_b2c = bhas_disponiveis[i_bha + 1]

                                                    if not sapata_repetida(
                                                            bha_sapata_b2c,
                                                            mapa_sapata_por_bha,
                                                            sapatas_existentes
                                                    ):
                                                        deve_validar_litologia_b2c = True
                                                        diametro_sapata_b2c = mapa_sapata_por_bha.get(
                                                            bha_sapata_b2c,
                                                            "Revestimento"
                                                        )
                                                        nome_sapata_b2c = f"Sapata {diametro_sapata_b2c}"

                                                if deve_validar_litologia_b2c:
                                                    info_folhelho = encontrar_folhelho_acima_do_arenito(
                                                        prof_sapata=float(profundidade_sapata_nova),
                                                        profundidades=profundidades,
                                                        litologias=litologias,
                                                        base_final=float(df_sapata["Profundidade (m)"].max())
                                                    )

                                                    if info_folhelho is not None:
                                                        esp_min_id = float(
                                                            info_folhelho.get(
                                                                "esp_min_nao_perm",
                                                                st.session_state.get("ef", 10.0)
                                                            )
                                                        )

                                                        decision_id = (
                                                            f"b2c"
                                                            f"|i_bha_{i_bha}"
                                                            f"|bha_atual_{bha_fase}"
                                                            f"|bha_sapata_{bha_sapata_b2c}"
                                                            f"|sapata_calc_{float(profundidade_sapata_nova):.2f}"
                                                            f"|ef_{esp_min_id:.2f}"
                                                        )

                                                        decisoes = st.session_state.get("decisoes_ajuste_arenito", {})

                                                        if decision_id not in decisoes:
                                                            st.session_state.pendencia_ajuste_arenito = {
                                                                "decision_id": decision_id,
                                                                "fase_idx": i_bha,
                                                                "bha": bha_sapata_b2c,
                                                                "nome_sapata": nome_sapata_b2c,
                                                                "prof_original": float(profundidade_sapata_nova),
                                                                "prof_ajustada": (
                                                                    float(info_folhelho["prof_ajustada"])
                                                                    if info_folhelho.get("prof_ajustada") is not None
                                                                    else None
                                                                ),
                                                                "motivo": info_folhelho.get("motivo"),
                                                                "ajuste_disponivel": info_folhelho.get(
                                                                    "ajuste_disponivel",
                                                                    False
                                                                ),
                                                                "intervalo_atual": info_folhelho.get("intervalo_atual",
                                                                                                     {}),
                                                                "esp_min_nao_perm": esp_min_id,
                                                            }

                                                            confirmar_ajuste_sapata_arenito()
                                                            st.stop()

                                                        if (
                                                                decisoes.get(decision_id, False)
                                                                and info_folhelho.get("ajuste_disponivel", False)
                                                        ):
                                                            prof_sapata_ajustada = float(info_folhelho["prof_ajustada"])

                                                            if (
                                                                    prof_sapata_ajustada < float(
                                                                profundidade_sapata_nova)
                                                                    and prof_sapata_ajustada >= float(
                                                                profundidade_minima_sapata)
                                                            ):
                                                                profundidade_sapata_nova = prof_sapata_ajustada
                                                                idx_sapata = prof_col.sub(
                                                                    profundidade_sapata_nova
                                                                ).abs().idxmin()

                                                                criterio_sapata = (
                                                                    f"{criterio_sapata} Ajustada para Formação Não Permeável "
                                                                    f"com espessura mínima de {esp_min_id:.2f} m acima."
                                                                )

                                                mask_plot_fase = (
                                                        (prof_intervalo >= profundidade_sapata_nova) &
                                                        (prof_intervalo <= profundidade_limite_superior)
                                                )

                                                df_plot_fase = df_intervalo.loc[mask_plot_fase].copy()

                                                comprimento_minimo_fase = st.session_state.cmf
                                                comprimento_fase = float(
                                                    profundidade_limite_superior - profundidade_sapata_nova
                                                )

                                                if comprimento_fase < comprimento_minimo_fase:
                                                    y1 = min(profundidade_sapata_nova, profundidade_limite_superior)
                                                    y2 = max(profundidade_sapata_nova, profundidade_limite_superior)

                                                    intervalos_fase_curta.append({
                                                        "bha": bha_fase,
                                                        "topo": y1,
                                                        "base": y2,
                                                        "comprimento": comprimento_fase,
                                                        "comprimento_minimo_fase": comprimento_minimo_fase
                                                    })

                                                curvas_kt_plot.append({
                                                    "bha": bha_fase,
                                                    "prof": df_plot_fase["Profundidade (m)"].tolist(),
                                                    "gf_kt": df_plot_fase["gf_kt (lb/gal)"].tolist(),
                                                })

                                                grad_fratura_ref = float(
                                                    df_sapata.loc[idx_sapata, "Gradiente de Fratura - Margem (lb/gal)"]
                                                )

                                                if (
                                                        not ultima_fase_poco_aberto
                                                        and i_bha == 0
                                                        and not sapata_repetida(
                                                    bha_fase,
                                                    mapa_sapata_por_bha,
                                                    sapatas_existentes
                                                )
                                                ):
                                                    sapatas_calculadas.append({
                                                        "prof": prof_fundo,
                                                        "label": mapa_sapata_por_bha.get(bha_fase, "Revestimento"),
                                                        "bha": bha_fase,
                                                        "criterio": "Profundidade definida para a última sapata."
                                                    })

                                                encerrar_por_intervalo_sem_sapata = False

                                                if i_bha < len(bhas_disponiveis) - 1:
                                                    bha_proximo = bhas_disponiveis[i_bha + 1]

                                                    if not sapata_repetida(
                                                            bha_proximo, mapa_sapata_por_bha, sapatas_existentes
                                                    ):
                                                        sapatas_calculadas.append({
                                                            "prof": profundidade_sapata_nova,
                                                            "label": mapa_sapata_por_bha.get(
                                                                bha_proximo, "Revestimento"
                                                            ),
                                                            "bha": bha_proximo,
                                                            "criterio": criterio_sapata,
                                                        })
                                                    else:
                                                        sapata_repetida_label = mapa_sapata_por_bha.get(bha_proximo, "")

                                                        if sapata_repetida_label == str(
                                                                st.session_state.get("odrs", "")
                                                        ).strip():
                                                            prof_revest_existente = float(st.session_state.prs)
                                                            motivo = "superfície"
                                                        elif sapata_repetida_label == str(
                                                                st.session_state.get("odrc", "")
                                                        ).strip():
                                                            prof_revest_existente = float(st.session_state.prc)
                                                            motivo = "condutor"
                                                        else:
                                                            prof_revest_existente = None
                                                            motivo = "existente"

                                                        if prof_revest_existente is not None:
                                                            y1 = min(profundidade_sapata_nova, prof_revest_existente)
                                                            y2 = max(profundidade_sapata_nova, prof_revest_existente)

                                                            intervalos_sem_sapata.append({
                                                                "bha": bha_proximo,
                                                                "topo": y1,
                                                                "base": y2,
                                                                "motivo": motivo,
                                                                "sapata": sapata_repetida_label
                                                            })

                                                            encerrar_por_intervalo_sem_sapata = True

                                                historico_fases.append({
                                                    "bha": bha_fase,
                                                    "prof_sapata_calc": profundidade_sapata_nova,
                                                    "grad_fratura_ref": grad_fratura_ref,
                                                    "altura_kick": float(altura_kick_fase),
                                                    "elemento_topo_kick": elemento_topo_kick_fase,
                                                    "intervalo_topo_kick": intervalo_topo_kick_fase,
                                                    "criterio": criterio_sapata,
                                                    "prof_ref": prof_ref,
                                                    "gpp_ref": gpp_ref,
                                                    "ultima_fase_poco_aberto": bool(ultima_fase_poco_aberto),
                                                })

                                                if encerrar_por_intervalo_sem_sapata:
                                                    break

                                                idx_sapata_anterior = idx_sapata

                                                if profundidade_sapata_nova <= profundidade_minima_sapata:
                                                    break

                                                profundidade_limite_superior = profundidade_sapata_nova

                                            st.session_state.sapatas_kick_b2c = sapatas_calculadas
                                            st.session_state.curvas_kt_b2c = curvas_kt_plot
                                            st.session_state.historico_fases_b2c = historico_fases
                                            st.session_state.intervalos_sem_sapata_b2c = intervalos_sem_sapata
                                            st.session_state.intervalos_fase_curta_b2c = intervalos_fase_curta
                                            st.session_state.df_sapata_kt = df_sapata.copy()

                                            sapatas_plot = []

                                            if "prc" in st.session_state and pd.notna(st.session_state.prc):
                                                od_revest_condutor = st.session_state.get("odrc", '20"')
                                                sapatas_plot.append({
                                                    "prof": float(st.session_state.prc),
                                                    "nome": f"Sapata {od_revest_condutor}",
                                                    "cor": "black"
                                                })

                                            if "prs" in st.session_state and pd.notna(st.session_state.prs):
                                                od_revest_superficie = st.session_state.get("odrs", '13 3/8"')
                                                sapatas_plot.append({
                                                    "prof": float(st.session_state.prs),
                                                    "nome": f"Sapata {od_revest_superficie}",
                                                    "cor": "black",
                                                    "tipo": "superficie"
                                                })

                                            sapatas_calc_b2c = st.session_state.get("sapatas_kick_b2c", [])

                                            for i, s_calc in enumerate(sapatas_calc_b2c):
                                                prof = s_calc.get("prof", None)
                                                label_sapata = s_calc.get("label", f"Fase {i + 1}")

                                                if prof is None or pd.isna(prof):
                                                    continue

                                                sapatas_plot.append({
                                                    "prof": float(prof),
                                                    "nome": f"Sapata {label_sapata}",
                                                    "cor": "black",
                                                    "bha": s_calc.get("bha", None),
                                                    "criterio": s_calc.get("criterio", ""),
                                                    "tipo": "calculada"
                                                })

                                            st.session_state.sapatas_plot_kt = sapatas_plot
                                            st.session_state.pendencia_ajuste_arenito = None
                                            st.session_state.recalcular_sapatas = False

                                if "df_bha_final" in st.session_state and not st.session_state.df_bha_final.empty:
                                    ultrapassou_bha = (
                                            st.session_state.elemento_topo_kick == "Acima do último elemento do BHA"
                                    )

                                    if ultrapassou_bha:
                                        texto_topo_kick = "Ultrapassou o comprimento acumulado do BHA"
                                    else:
                                        texto_topo_kick = (
                                            f'{st.session_state.elemento_topo_kick} '
                                            f'({st.session_state.intervalo_elemento_topo_kick})'
                                        )

                                    c1, c2, c3 = st.columns([1, 1, 1.35])

                                    with c1:
                                        st.metric(
                                            label="Volume do kick",
                                            value=f'{st.session_state.volume_kick_bbl:.2f} bbl',
                                            border=True
                                        )

                                    with c2:
                                        st.metric(
                                            label="Altura do kick",
                                            value=f'{st.session_state.altura_kick_calculada:.2f} m',
                                            border=True
                                        )

                                    cor_texto_topo_kick = "red" if ultrapassou_bha else "black"

                                    with c3:
                                        st.markdown(
                                            f"""
                                            <div style="
                                                border: 1px solid rgba(49, 51, 63, 0.2);
                                                border-radius: 0.5rem;
                                                padding: 0.6rem 1rem 0.75rem 1rem;
                                                min-height: 108px;
                                                display: flex;
                                                flex-direction: column;
                                                justify-content: flex-start;
                                                background: transparent;
                                            ">
                                                <div style="
                                                    font-size: 0.875rem;
                                                    color: black;
                                                    margin-top: 0.35rem;
                                                    margin-bottom: 0.15rem;
                                                    font-weight: 400;
                                                ">
                                                    Topo do kick
                                                </div>
                                                <div style="
                                                    font-size: 1.1rem;
                                                    font-weight: 600;
                                                    color: {cor_texto_topo_kick};
                                                    line-height: 1.25;
                                                    word-break: break-word;
                                                    overflow-wrap: break-word;
                                                    margin-top: 0.35rem;
                                                ">
                                                    {texto_topo_kick}
                                                </div>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                    if st.session_state.get("metodo_kt") == "Cima para Baixo":
                                        historico_fases = st.session_state.get("historico_fases_c2b", [])

                                        if historico_fases:
                                            st.markdown("#### Resumo das fases")

                                            for fase in historico_fases:
                                                prof_calc_txt = (
                                                    f'{fase["prof_sapata_calc"]:.2f} m'
                                                    if fase["prof_sapata_calc"] is not None and pd.notna(
                                                        fase["prof_sapata_calc"]
                                                    )
                                                    else "Não atingido até o fim dos dados de perfilagem."
                                                )

                                                intervalo_topo_txt = (
                                                    f' · {fase["intervalo_topo_kick"]}'
                                                    if fase["intervalo_topo_kick"]
                                                    else ""
                                                )

                                                with st.expander(f'Fase {fase["bha"]}', expanded=True):
                                                    cc1, cc2 = st.columns(2)

                                                    with cc1:
                                                        st.caption("Profundidade da sapata")
                                                        st.write(prof_calc_txt)

                                                        st.caption("Gradiente de fratura na sapata")
                                                        st.write(f'{fase["grad_fratura_ref"]:.2f} lb/gal')

                                                    with cc2:
                                                        st.caption("Altura do kick")
                                                        st.write(f'{fase["altura_kick"]:.2f} m')

                                                        st.caption("Topo do kick")
                                                        st.write(
                                                            f'{fase["elemento_topo_kick"]}{intervalo_topo_txt}'
                                                        )

                                                    st.markdown(
                                                        f"""
                                                        <span>
                                                            <b>Critério:</b>
                                                            <span style="color: red;">{fase["criterio"]}</span>
                                                        </span>
                                                        """,
                                                        unsafe_allow_html=True
                                                    )
                                    else:
                                        historico_fases = st.session_state.get("historico_fases_b2c", [])

                                        if historico_fases:
                                            st.markdown("#### Resumo das fases")

                                            for fase in historico_fases:
                                                prof_calc_txt = (
                                                    f'{fase["prof_sapata_calc"]:.2f} m'
                                                    if fase["prof_sapata_calc"] is not None and pd.notna(
                                                        fase["prof_sapata_calc"]
                                                    )
                                                    else "Não calculado"
                                                )

                                                intervalo_topo_txt = (
                                                    f' · {fase["intervalo_topo_kick"]}'
                                                    if fase["intervalo_topo_kick"]
                                                    else ""
                                                )

                                                with st.expander(f'Fase {fase["bha"]}', expanded=True):
                                                    cc1, cc2 = st.columns(2)

                                                    with cc1:
                                                        st.caption("Profundidade da sapata")
                                                        st.write(prof_calc_txt)

                                                        st.caption("Gradiente de fratura")
                                                        st.write(f'{fase["grad_fratura_ref"]:.2f} lb/gal')

                                                        st.caption("Profundidade de referência")
                                                        st.write(f'{fase["prof_ref"]:.2f} m')

                                                    with cc2:
                                                        st.caption("Altura do kick")
                                                        st.write(f'{fase["altura_kick"]:.2f} m')

                                                        st.caption("Gradiente de Pressão de Poros")
                                                        st.write(f'{fase["gpp_ref"]:.2f} lb/gal')

                                                        st.caption("Topo do kick")
                                                        st.write(
                                                            f'{fase["elemento_topo_kick"]}{intervalo_topo_txt}'
                                                        )

                                                    st.markdown(
                                                        f"""
                                                        <span>
                                                            <b>Critério:</b>
                                                            <span style="color: red;">{fase["criterio"]}</span>
                                                        </span>
                                                        """,
                                                        unsafe_allow_html=True
                                                    )

                        with col2:
                            with st.container(border=True):
                                if "x_max_sa" not in st.session_state:
                                    st.session_state.x_max_sa = 23
                                if "x_min_sa" not in st.session_state:
                                    st.session_state.x_min_sa = 7
                                def reset_config():
                                    st.session_state.x_min_sa = 7
                                    st.session_state.x_max_sa = 23
                                    st.session_state.x_step_sa = 1
                                    st.session_state.y_min_sa = 0
                                    st.session_state.y_max_sa = int(st.session_state.y.max()) + 100
                                    st.session_state.y_step_sa = 50
                                with st.expander("Configurações do Gráfico", expanded=False):
                                    st.checkbox('Exibir Legendas', key='leg_sa', value=False)
                                    st.number_input("Eixo X - mínimo", value=7, step=1,
                                                    key="x_min_sa")
                                    st.number_input("Eixo X - máximo", value=23, step=1,
                                                    key="x_max_sa")
                                    st.number_input("Passo do eixo X", value=1, step=1,
                                                    key="x_step_sa")

                                    st.number_input("Eixo Y - mínimo", value=0, step=100,
                                                    key="y_min_sa")
                                    st.number_input(
                                        "Eixo Y - máximo",
                                        value=int(st.session_state.y.max()) + 100,
                                        step=100,
                                        key="y_max_sa"
                                    )
                                    st.number_input(
                                        "Passo do eixo Y",
                                        value=200,
                                        step=50,
                                        key="y_step_sa"
                                    )

                                    st.button(
                                        "Resetar Eixos - Kick Tolerance",
                                        on_click=reset_config,
                                        type="primary",
                                        use_container_width=True
                                    )
                                c1,c2 = st.columns(2)
                                with c1:
                                # with st.container(border=True):
                                    st.markdown("### Sapatas")
                                    st.session_state.fig_asp = plt.figure(figsize=(8, 10))
                                    if st.session_state.idg == 'Sim':
                                        # === COM coluna de idade ===
                                        gs = gridspec.GridSpec(
                                            1, 4,
                                            width_ratios=[0.1, 0.2, 0.21, 1],
                                            wspace=0
                                        )

                                        ax_idade = st.session_state.fig_asp.add_subplot(gs[0])
                                        ax1 = st.session_state.fig_asp.add_subplot(gs[1], sharey=ax_idade)

                                        ax_gap = st.session_state.fig_asp.add_subplot(gs[2])
                                        ax_gap.axis('off')

                                        ax = st.session_state.fig_asp.add_subplot(gs[3], sharey=ax_idade)

                                        idade_formacao(ax_idade, st.session_state.df_idade,
                                                       df_pp['Profundidade (m)'].max() + 100)

                                        # remove ticks e labels da coluna de idade
                                        ax_idade.tick_params(
                                            axis='y',
                                            which='both',
                                            left=False,
                                            right=False,
                                            labelleft=False,
                                            labelright=False
                                        )

                                        ax_idade.set_ylabel("")

                                        # evita duplicar rótulos de profundidade
                                        plt.setp(ax1.get_yticklabels(), visible=False)
                                        plt.setp(ax.get_yticklabels(), visible=False)

                                    else:
                                        # === SEM coluna de idade ===
                                        gs = gridspec.GridSpec(
                                            1, 3,
                                            width_ratios=[0.2, 0.21, 1],
                                            wspace=0
                                        )

                                        ax1 = st.session_state.fig_asp.add_subplot(gs[0])
                                        ax_gap = st.session_state.fig_asp.add_subplot(gs[1])
                                        ax_gap.axis('off')

                                        ax = st.session_state.fig_asp.add_subplot(gs[2], sharey=ax1)

                                        plt.setp(ax.get_yticklabels(), visible=False)

                                    lito(
                                        ax1,
                                        df_pp,
                                        profundidades,
                                        litologias,
                                        st.session_state.y_max_pp
                                    )

                                    try:
                                        if st.session_state.ms != 0.:
                                            ax.plot(
                                                df_sapata["Gradiente de Pressão de Poros (lb/gal)"],
                                                df_sapata["Profundidade (m)"],
                                                linestyle="-",
                                                color="red",
                                                linewidth=2,
                                                label="Gradiente de Pressão de Poros (lb/gal)",
                                                zorder=5
                                            )

                                        ax.plot(
                                            df_sapata["Gradiente de Pressão de Poros + Margem (lb/gal)"],
                                            df_sapata["Profundidade (m)"],
                                            linestyle="-",
                                            color="orange",
                                            linewidth=2,
                                            label="Gradiente de Pressão de Poros + Margem (lb/gal)",
                                            zorder=5
                                        )

                                        if st.session_state.msf != 0.:
                                            ax.plot(
                                                df_sapata["Gradiente de Fratura (lb/gal)"],
                                                df_sapata["Profundidade (m)"],
                                                linestyle="-",
                                                color="blue",
                                                linewidth=2,
                                                label="Gradiente de Fratura (lb/gal)",
                                                zorder=5
                                            )

                                        ax.plot(
                                            df_sapata["Gradiente de Fratura - Margem (lb/gal)"],
                                            df_sapata["Profundidade (m)"],
                                            linestyle="-",
                                            color="green",
                                            linewidth=2,
                                            label="Gradiente de Fratura (lb/gal) - Margem",
                                            zorder=5
                                        )

                                        if st.session_state.metodo_kt == "Cima para Baixo":
                                            curvas_kt_plot = st.session_state.get("curvas_kt_plot", [])
                                            for curva in curvas_kt_plot:
                                                bha_curva = curva["bha"]
                                                prof_plot = pd.to_numeric(pd.Series(curva["prof"]), errors="coerce")
                                                rho_plot = pd.to_numeric(pd.Series(curva["rho_kt"]), errors="coerce")
                                                mask_ok = prof_plot.notna() & rho_plot.notna()

                                                if mask_ok.any():
                                                    ax.plot(
                                                        rho_plot[mask_ok],
                                                        prof_plot[mask_ok],
                                                        linestyle="-",
                                                        color="purple",
                                                        linewidth=2,
                                                        label=f"Kick Tolerance - {bha_curva}",
                                                        zorder=5
                                                    )


                                        else:
                                            curvas_kt_plot = st.session_state.get("curvas_kt_b2c", [])
                                            for i, curva in enumerate(curvas_kt_plot):
                                                bha_curva = curva.get("bha", f"Fase {i + 1}")
                                                prof_plot = pd.to_numeric(pd.Series(curva.get("prof", [])), errors="coerce")
                                                rho_plot = pd.to_numeric(pd.Series(curva.get("gf_kt", [])), errors="coerce")
                                                mask_ok = prof_plot.notna() & rho_plot.notna()

                                                if mask_ok.any():
                                                    ax.plot(
                                                        rho_plot[mask_ok],
                                                        prof_plot[mask_ok],
                                                        linestyle="-",
                                                        color="purple",
                                                        linewidth=2,
                                                        label=f"Kick Tolerance - {bha_curva}",
                                                        zorder=5
                                                    )

                                    except Exception:
                                        pass

                                    # Configurações do gráfico
                                    ax.set_title('Kick Tolerance', fontsize=14, fontweight='bold')
                                    ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                    ax.invert_yaxis()
                                    ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                    ax.tick_params(axis='y', which='both', left=True, labelleft=True)
                                    ax.set_yticks(range(
                                        st.session_state.y_min_sa,
                                        st.session_state.y_max_sa,
                                        st.session_state.y_step_sa
                                    ))
                                    ax.set_ylim(st.session_state.y_max_sa, st.session_state.y_min_sa)
                                    ax.set_xticks(range(
                                        st.session_state.x_min_sa,
                                        st.session_state.x_max_sa,
                                        st.session_state.x_step_sa
                                    ))
                                    ax.set_xlim(st.session_state.x_min_sa, st.session_state.x_max_sa)
                                    ax.grid(True, linestyle='--', alpha=0.5)

                                    if st.session_state.metodo_kt == "Cima para Baixo":
                                        curvas_kt_plot = st.session_state.get("curvas_kt_plot", [])

                                        if curvas_kt_plot:
                                            prof_final_perfil = pd.to_numeric(
                                                df_sapata["Profundidade (m)"], errors="coerce"
                                            ).dropna().max()

                                            ultima_curva = curvas_kt_plot[-1]
                                            prof_ultima_curva = pd.to_numeric(
                                                pd.Series(ultima_curva.get("prof", [])), errors="coerce"
                                            ).dropna()

                                            if not prof_ultima_curva.empty:
                                                prof_ultimo_trecho = prof_ultima_curva.max()

                                                if pd.notna(prof_final_perfil) and not np.isclose(prof_ultimo_trecho,
                                                                                                  prof_final_perfil):
                                                    topo = float(prof_ultimo_trecho)
                                                    base = float(prof_final_perfil)

                                                    if base > topo:
                                                        x_left, x_right_fill = ax.get_xlim()
                                                        x_texto = (x_left + x_right_fill) / 2
                                                        y_texto = (topo + base) / 2
                                                        altura_intervalo = abs(base - topo)

                                                        ax.fill_betweenx(
                                                            y=[topo, base],
                                                            x1=x_left,
                                                            x2=x_right_fill,
                                                            color="red",
                                                            alpha=0.12,
                                                            zorder=1
                                                        )

                                                        if altura_intervalo >= 40:
                                                            ax.text(
                                                                x_texto,
                                                                y_texto,
                                                                # "Trecho sem sapata!\nAumente o OD do BHA,\no comp. máx. OH\nou aprofunde o rev. de superfície.",
                                                                "Trecho sem sapata!",
                                                                color="black",
                                                                fontsize=9,
                                                                ha="center",
                                                                va="center",
                                                                bbox=dict(
                                                                    boxstyle="round,pad=0.25",
                                                                    facecolor="white",
                                                                    edgecolor="red",
                                                                    alpha=0.85
                                                                ),
                                                                zorder=2
                                                            )

                                    if st.session_state.metodo_kt == "Baixo para Cima":
                                        intervalos_sem_sapata = st.session_state.get("intervalos_sem_sapata_b2c", [])
                                        intervalos_fase_curta = st.session_state.get("intervalos_fase_curta_b2c", [])

                                        x_left, x_right_fill = ax.get_xlim()
                                        x_texto = (x_left + x_right_fill) / 2

                                        for item in intervalos_sem_sapata:
                                            topo = item.get("topo", None)
                                            base = item.get("base", None)

                                            if topo is None or base is None:
                                                continue

                                            ax.fill_betweenx(
                                                y=[topo, base],
                                                x1=x_left,
                                                x2=x_right_fill,
                                                color="red",
                                                alpha=0.12,
                                                zorder=1
                                            )

                                            y_texto = (topo + base) / 2
                                            altura_intervalo = abs(base - topo)

                                            if altura_intervalo >= 40:
                                                ax.text(
                                                    x_texto,
                                                    y_texto,
                                                    "Trecho sem sapata!\nReduza o OD do BHA final,\no comp. máx. OH\nou aprofunde o rev. de superfície.",
                                                    color="black",
                                                    fontsize=9,
                                                    ha="center",
                                                    va="center",
                                                    bbox=dict(
                                                        boxstyle="round,pad=0.25",
                                                        facecolor="white",
                                                        edgecolor="red",
                                                        alpha=0.85
                                                    ),
                                                    zorder=2
                                                )
                                        for item in intervalos_fase_curta:
                                            topo = item.get("topo", None)
                                            base = item.get("base", None)
                                            comprimento_minimo_fase = item.get("comprimento_minimo_fase", 200.0)

                                            if topo is None or base is None:
                                                continue

                                            ax.fill_betweenx(
                                                y=[topo, base],
                                                x1=x_left,
                                                x2=x_right_fill,
                                                color="yellow",
                                                alpha=0.18,
                                                zorder=1
                                            )

                                            x_texto = (x_left + x_right_fill) / 2
                                            y_texto = (topo + base) / 2
                                            altura_intervalo = abs(base - topo)

                                            if altura_intervalo >= 40:
                                                ax.text(
                                                    x_texto,
                                                    y_texto,
                                                    f'Fase com comprimento inferior a {comprimento_minimo_fase:.0f} metros',
                                                    color="black",
                                                    fontsize=9,
                                                    ha="center",
                                                    va="center",
                                                    bbox=dict(
                                                        boxstyle="round,pad=0.25",
                                                        facecolor="white",
                                                        edgecolor="goldenrod",
                                                        alpha=0.9
                                                    ),
                                                    zorder=2
                                                )

                                    # =========================
                                    # Sapatas: plotar AQUI
                                    # =========================
                                    x_right = ax.get_xlim()[1] - 0.01 * (ax.get_xlim()[1] - ax.get_xlim()[0])

                                    try:
                                        for s in sapatas_plot:
                                            nome_sapata = s.get("nome", "Sapata")
                                            cor_sapata = s.get("cor", "black")

                                            prof_superficie = st.session_state.get("prs", None)
                                            tipo_sapata = s.get("tipo", "calculada")

                                            if (
                                                    st.session_state.metodo_kt == "Baixo para Cima"
                                                    and prof_superficie is not None
                                                    and np.isclose(float(s["prof"]), float(prof_superficie), atol=1e-6)
                                                    and tipo_sapata != "superficie"
                                            ):
                                                cor_box = "red"
                                            else:
                                                cor_box = cor_sapata

                                            ax.axhline(
                                                y=s["prof"],
                                                color=cor_sapata,
                                                linestyle="--",
                                                linewidth=2,
                                                zorder=6,
                                                label="_nolegend_"
                                            )

                                            ax.text(
                                                x=x_right,
                                                y=s["prof"] - 18,
                                                s=f'{nome_sapata}: {s["prof"]:.2f} m',
                                                color=cor_box,
                                                fontsize=9,
                                                va="center",
                                                ha="right",
                                                bbox=dict(
                                                    boxstyle="round,pad=0.2",
                                                    facecolor="white",
                                                    edgecolor=cor_box,
                                                    alpha=0.9
                                                ),
                                                zorder=7
                                            )

                                    except Exception:
                                        pass

                                    if st.session_state.leg_sa:
                                        ax.legend(
                                            loc='upper right',
                                            fontsize=8,
                                            frameon=True,
                                            shadow=True,
                                            fancybox=True,
                                            framealpha=1,
                                            facecolor='white',
                                            edgecolor='gray'
                                        )

                                    add_watermark(
                                        ax,
                                        logo_path="logo2.png",
                                        xy=(0.50, 0.5),
                                        zoom=0.2,
                                        alpha=0.2,
                                        zorder=0
                                    )

                                    st.pyplot(st.session_state.fig_asp, use_container_width=True)

                                with c2:
                                # with st.container(border=True):
                                    st.markdown("### Esquemático do Poço")

                                    try:
                                        df_esquematico_asp = _asp_montar_df_esquematico_kt()

                                        if not isinstance(df_esquematico_asp, pd.DataFrame) or df_esquematico_asp.empty:
                                            st.info("Calcule as sapatas para gerar o esquemático do poço.")
                                        else:
                                            fig_asp, df_esquematico_limpo = _asp_plotar_esquematico(df_esquematico_asp)

                                            if fig_asp is None:
                                                st.info("Não foi possível gerar o esquemático com os dados atuais.")
                                            else:
                                                st.session_state.fig_esquematico_asp = fig_asp
                                                st.session_state.df_esquematico_asp = df_esquematico_limpo
                                                st.pyplot(st.session_state.fig_esquematico_asp,use_container_width=True)

                                    except Exception as e:
                                        st.warning(f"Não foi possível gerar o esquemático do poço: {e}")

                    else:
                        st.error('Gere a Janela Operacional na aba "Estabilidade de Poço"', icon="🚨")

                with tab[1]:
                    with st.container(border=True):
                        if "df_sapata_kt" in st.session_state and not st.session_state.df_sapata_kt.empty:
                            st.markdown("### Dados calculados do Kick Tolerance")
                            st.dataframe(
                                st.session_state.df_sapata_kt,
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.warning("Nenhum dado de Kick Tolerance foi calculado.")

                    with st.container(border=True):
                        try:
                            st.markdown("### Volumes BHA")
                            st.dataframe(
                                st.session_state.df_bha_final,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Elemento do BHA": st.column_config.TextColumn("Elemento do BHA"),
                                    "OD (pol)": st.column_config.NumberColumn("OD (pol)", format="%.2f"),
                                    "OD (m)": st.column_config.NumberColumn("OD (m)", format="%.2f"),
                                    "Comprimento (m)": st.column_config.NumberColumn(
                                        "Comprimento (m)", format="%.2f"
                                    ),
                                    "Comprimento Acumulado (m)": st.column_config.NumberColumn(
                                        "Comprimento Acumulado (m)", format="%.2f"
                                    ),
                                    "Início do Trecho (m)": st.column_config.NumberColumn(
                                        "Início do Trecho (m)", format="%.2f"
                                    ),
                                    "Fim do Trecho (m)": st.column_config.NumberColumn(
                                        "Fim do Trecho (m)", format="%.2f"
                                    ),
                                    "Cap. Anular (m3/m)": st.column_config.NumberColumn(
                                        "Cap. Anular (m3/m)", format="%.2f"
                                    ),
                                    "Vol. (m3)": st.column_config.NumberColumn(
                                        "Vol. (m3)", format="%.2f"
                                    ),
                                    "Vol. Acum. (m3)": st.column_config.NumberColumn(
                                        "Vol. Acum. (m3)", format="%.2f"
                                    ),
                                    "Vol. Acum. (bbl)": st.column_config.NumberColumn(
                                        "Vol. Acum. (bbl)", format="%.2f"
                                    ),
                                }
                            )
                        except Exception:
                            st.warning("Nenhum volume do BHA foi calculado.")
            else:
                st.error('Função não disponível para "Retroanálise"', icon="🚨")

        else:
            st.error('Por favor, insira um documento!', icon="🚨")

    # Fluido de Perfuração
    with tabs[6]:
        if uploaded_file:
            if st.session_state.option == "Previsão de Geopressões":
                tab = st.tabs(['Fluido de Perfuração', 'Dados Calculados'])
                with tab[0]:
                    if "df_sapata_kt" in st.session_state:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            with st.container(border=True):
                                st.markdown("### Janela Operacional")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.pyplot(st.session_state.fig_jo, use_container_width=True)

                        with c2:
                            with st.container(border=True):
                                st.markdown("### Sapatas")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")
                                st.pyplot(st.session_state.fig_asp, use_container_width=True)

                        with c3:
                            df_suav = st.session_state.df_suav.copy()
                            df_sapata_kt = st.session_state.df_sapata_kt.copy()

                            # Base do dataframe do fluido
                            df_fluido = pd.DataFrame({
                                "Profundidade (m)": pd.to_numeric(df_suav["Profundidade (m)"], errors="coerce"),
                                "Max Inferior": pd.to_numeric(df_suav["Max Inferior"], errors="coerce"),
                            })

                            # Mesma lógica da margem usada na Janela Operacional
                            x_max_inf = np.asarray(df_fluido["Max Inferior"], dtype=float)
                            x_fs_base_inf = x_max_inf + float(st.session_state.fs)
                            x_fs_inf = np.maximum.accumulate(np.nan_to_num(x_fs_base_inf, nan=-np.inf))
                            x_fs_inf[np.isneginf(x_fs_inf)] = np.nan

                            df_fluido["Margem"] = x_fs_inf

                            df_fluido = (
                                df_fluido
                                .dropna(subset=["Profundidade (m)"])
                                .sort_values("Profundidade (m)")
                                .reset_index(drop=True)
                            )

                            # Junta todas as infos do df_sapata_kt ao longo da profundidade
                            if not df_sapata_kt.empty:
                                df_sapata_kt = df_sapata_kt.copy()

                                # tenta localizar a coluna de profundidade do df_sapata_kt
                                col_prof_sapata = next(
                                    (
                                        c for c in [
                                        "Profundidade da sapata (m)",
                                        "Profundidade (m)",
                                        "Profundidade",
                                        "Prof. Sapata (m)"
                                    ]
                                        if c in df_sapata_kt.columns
                                    ),
                                    None
                                )

                                if col_prof_sapata is not None:
                                    df_sapata_kt[col_prof_sapata] = pd.to_numeric(
                                        df_sapata_kt[col_prof_sapata], errors="coerce"
                                    )

                                    df_sapata_kt = (
                                        df_sapata_kt
                                        .dropna(subset=[col_prof_sapata])
                                        .sort_values(col_prof_sapata)
                                        .reset_index(drop=True)
                                    )

                                    # cada profundidade herda a última sapata acima dela
                                    df_fluido = pd.merge_asof(
                                        df_fluido,
                                        df_sapata_kt,
                                        left_on="Profundidade (m)",
                                        right_on=col_prof_sapata,
                                        direction="backward"
                                    )

                                df_fluido.insert(
                                    loc=len(df_fluido.columns),
                                    column='Linha média (lb/gal)',
                                    value=(df_fluido["Margem"] + df_fluido["Gradiente de Fratura - Margem (lb/gal)"]) / 2
                                )

                            sapatas_plot = st.session_state.get("sapatas_plot_kt", [])

                            # Peso do fluido por intervalo entre sapatas
                            sapatas_plot = st.session_state.get("sapatas_plot_kt", [])

                            intervalos_fluido = []
                            df_fluido["Peso do Fluido (lb/gal)"] = np.nan

                            sapatas_validas = []
                            for s in sapatas_plot:
                                try:
                                    sapatas_validas.append({
                                        "nome": s.get("nome", "Sapata"),
                                        "prof": float(s["prof"])
                                    })
                                except (TypeError, ValueError, KeyError):
                                    pass

                            sapatas_validas = sorted(sapatas_validas, key=lambda x: x["prof"])

                            prof_sapatas = []
                            for s in sapatas_validas:
                                if not prof_sapatas or not np.isclose(s["prof"], prof_sapatas[-1], atol=1e-6):
                                    prof_sapatas.append(s["prof"])

                            for i in range(len(prof_sapatas) - 1):
                                topo = prof_sapatas[i]
                                base = prof_sapatas[i + 1]

                                mask_intervalo = (
                                        (df_fluido["Profundidade (m)"] > topo) &
                                        (df_fluido["Profundidade (m)"] <= base)
                                )

                                if mask_intervalo.any():
                                    margem_intervalo = df_fluido.loc[mask_intervalo, "Margem"].max()
                                    linha_media_intervalo = df_fluido.loc[mask_intervalo, "Linha média (lb/gal)"].min()

                                    peso_plot = np.ceil(margem_intervalo * 2) / 2
                                    if np.isclose(peso_plot, margem_intervalo, atol=1e-9):
                                        peso_plot += 0.5
                                    peso_plot = round(peso_plot, 2)

                                    df_fluido.loc[
                                        mask_intervalo,
                                        "Peso do Fluido (lb/gal)"
                                    ] = peso_plot

                                    intervalos_fluido.append({
                                        "Topo do Intervalo (m)": topo,
                                        "Base do Intervalo (m)": base,
                                        "Margem do Intervalo (lb/gal)": round(margem_intervalo, 2),
                                        "Peso do Fluido (lb/gal)": round(peso_plot, 2),
                                        "Linha média do Intervalo (lb/gal)": round(linha_media_intervalo, 2),
                                    })

                            if prof_sapatas:
                                topo_final = prof_sapatas[-1]
                                mask_final = df_fluido["Profundidade (m)"] > topo_final

                                if mask_final.any():
                                    margem_final = df_fluido.loc[mask_final, "Margem"].max()
                                    linha_media_final = df_fluido.loc[mask_final, "Linha média (lb/gal)"].min()

                                    peso_plot = np.ceil(margem_final * 2) / 2
                                    if np.isclose(peso_plot, margem_final, atol=1e-9):
                                        peso_plot += 0.5
                                    peso_plot = round(peso_plot, 2)

                                    df_fluido.loc[
                                        mask_final,
                                        "Peso do Fluido (lb/gal)"
                                    ] = peso_plot

                                    intervalos_fluido.append({
                                        "Topo do Intervalo (m)": topo_final,
                                        "Base do Intervalo (m)": float(df_fluido["Profundidade (m)"].max()),
                                        "Margem do Intervalo (lb/gal)": round(margem_final, 2),
                                        "Peso do Fluido (lb/gal)": round(peso_plot, 2),
                                        "Linha média do Intervalo (lb/gal)": round(linha_media_final, 2),
                                    })

                            st.session_state.df_intervalos_fluido = pd.DataFrame(intervalos_fluido)

                            st.session_state.df_fluido = df_fluido.copy()

                            with st.container(border=True):
                                st.markdown("### Fluido de Perfuração")
                                st.session_state.fig_fp = plt.figure(figsize=(8, 10))
                                if st.session_state.idg == 'Sim':
                                    # === COM coluna de idade ===
                                    gs = gridspec.GridSpec(
                                        1, 4,
                                        width_ratios=[0.1, 0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax_idade = st.session_state.fig_fp.add_subplot(gs[0])
                                    ax1 = st.session_state.fig_fp.add_subplot(gs[1], sharey=ax_idade)

                                    ax_gap = st.session_state.fig_fp.add_subplot(gs[2])
                                    ax_gap.axis('off')

                                    ax = st.session_state.fig_fp.add_subplot(gs[3], sharey=ax_idade)

                                    idade_formacao(ax_idade, st.session_state.df_idade,
                                                   df_pp['Profundidade (m)'].max() + 100)

                                    # remove ticks e labels da coluna de idade
                                    ax_idade.tick_params(
                                        axis='y',
                                        which='both',
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                        labelright=False
                                    )

                                    ax_idade.set_ylabel("")

                                    # evita duplicar rótulos de profundidade
                                    plt.setp(ax1.get_yticklabels(), visible=False)
                                    plt.setp(ax.get_yticklabels(), visible=False)

                                else:
                                    # === SEM coluna de idade ===
                                    gs = gridspec.GridSpec(
                                        1, 3,
                                        width_ratios=[0.2, 0.21, 1],
                                        wspace=0
                                    )

                                    ax1 = st.session_state.fig_fp.add_subplot(gs[0])
                                    ax_gap = st.session_state.fig_fp.add_subplot(gs[1])
                                    ax_gap.axis('off')

                                    ax = st.session_state.fig_fp.add_subplot(gs[2], sharey=ax1)

                                    plt.setp(ax.get_yticklabels(), visible=False)

                                lito(
                                    ax1,
                                    df_pp,
                                    profundidades,
                                    litologias,
                                    st.session_state.y_max
                                )

                                if "x_max_fp" not in st.session_state:
                                    st.session_state.x_max_fp = 23
                                if "x_min_fp" not in st.session_state:
                                    st.session_state.x_min_fp = 7
                                def reset_config_fp():
                                    st.session_state.x_min_fp = 7
                                    st.session_state.x_max_fp = 23
                                    st.session_state.x_step_fp = 1
                                    st.session_state.y_min_fp = 0
                                    st.session_state.y_max_fp = int(st.session_state.y.max()) + 100
                                    st.session_state.y_step_fp = 50

                                with st.expander("Configurações do Gráfico", expanded=False):
                                    st.checkbox('Exibir Legendas', key='leg_fp', value=False)
                                    st.number_input("Eixo X - mínimo", value=7, step=1, key="x_min_fp")
                                    st.number_input("Eixo X - máximo", value=23, step=1, key="x_max_fp")
                                    st.number_input("Passo do eixo X", value=1, step=1, key="x_step_fp")

                                    st.number_input("Eixo Y - mínimo", value=0, step=100, key="y_min_fp")
                                    st.number_input(
                                        "Eixo Y - máximo",
                                        value=int(st.session_state.y.max()) + 100,
                                        step=100,
                                        key="y_max_fp"
                                    )
                                    st.number_input(
                                        "Passo do eixo Y",
                                        value=200,
                                        step=50,
                                        key="y_step_fp"
                                    )

                                    curvas_disponiveis_fp = [
                                        "Faixa vermelha",
                                        "Max Inferior",
                                        "Margem",
                                        "Gradiente de Pressão de Poros (lb/gal)",
                                        "Gradiente de Pressão de Poros + Margem (lb/gal)",
                                        "Gradiente de Fratura (lb/gal)",
                                        "Gradiente de Fratura - Margem (lb/gal)",
                                        "Linha média (lb/gal)",
                                        "Peso do Fluido (lb/gal)",
                                        "Kick Tolerance",
                                        "Sapatas",
                                    ]

                                    curvas_default_fp = [
                                        "Faixa vermelha",
                                        "Max Inferior",
                                        "Margem",
                                        "Gradiente de Fratura - Margem (lb/gal)",
                                        "Peso do Fluido (lb/gal)",
                                        "Linha média (lb/gal)",
                                        "Sapatas",
                                    ]

                                    curvas_default_fp_validas = []
                                    for curva in curvas_default_fp:
                                        if curva == "Gradiente de Fratura (lb/gal)" and st.session_state.msf == 0.:
                                            continue
                                        curvas_default_fp_validas.append(curva)

                                    st.multiselect(
                                        "Selecione as curvas para plotar",
                                        options=curvas_disponiveis_fp,
                                        default=curvas_default_fp_validas,
                                        key="curvas_fp_visiveis"
                                    )

                                    st.button(
                                        "Resetar Eixos - Fluido de Perfuração",
                                        on_click=reset_config_fp,
                                        type="primary",
                                        use_container_width=True
                                    )

                                curvas_visiveis = st.session_state.get("curvas_fp_visiveis", curvas_default_fp_validas)

                                # Faixa vermelha entre Max Inferior e Margem
                                mask_faixa = (
                                        df_fluido["Max Inferior"].notna() &
                                        df_fluido["Margem"].notna()
                                )

                                if "Faixa vermelha" in curvas_visiveis:
                                    ax.fill_betweenx(
                                        df_fluido.loc[mask_faixa, "Profundidade (m)"],
                                        df_fluido.loc[mask_faixa, "Max Inferior"],
                                        df_fluido.loc[mask_faixa, "Margem"],
                                        color="red",
                                        alpha=0.18,
                                        zorder=1,
                                        label="_nolegend_"
                                    )

                                if "Max Inferior" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Max Inferior"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="red",
                                        linewidth=2,
                                        label="Max Inferior",
                                    )

                                if "Margem" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Margem"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="blue",
                                        linewidth=2,
                                        label="Margem",
                                    )

                                if (
                                        "Gradiente de Pressão de Poros (lb/gal)" in curvas_visiveis
                                        and st.session_state.ms != 0.
                                ):
                                    ax.plot(
                                        df_fluido["Gradiente de Pressão de Poros (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="tomato",
                                        linewidth=2,
                                        label="Gradiente de Pressão de Poros (lb/gal)",
                                        zorder=5
                                    )

                                if "Gradiente de Pressão de Poros + Margem (lb/gal)" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Gradiente de Pressão de Poros + Margem (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="orange",
                                        linewidth=2,
                                        label="Gradiente de Pressão de Poros + Margem (lb/gal)",
                                        zorder=5
                                    )

                                if (
                                        "Gradiente de Fratura (lb/gal)" in curvas_visiveis
                                        and st.session_state.msf != 0.
                                ):
                                    ax.plot(
                                        df_fluido["Gradiente de Fratura (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="blue",
                                        linewidth=2,
                                        label="Gradiente de Fratura (lb/gal)",
                                        zorder=5
                                    )

                                if "Gradiente de Fratura - Margem (lb/gal)" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Gradiente de Fratura - Margem (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="green",
                                        linewidth=2,
                                        label="Gradiente de Fratura (lb/gal) - Margem",
                                        zorder=5
                                    )

                                if "Linha média (lb/gal)" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Linha média (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="--",
                                        color="black",
                                        linewidth=2,
                                        label="Linha média (lb/gal)",
                                    )

                                if "Kick Tolerance" in curvas_visiveis:
                                    if st.session_state.metodo_kt == "Cima para Baixo":
                                        curvas_kt_plot = st.session_state.get("curvas_kt_plot", [])

                                        for curva in curvas_kt_plot:
                                            bha_curva = curva["bha"]
                                            prof_plot = pd.to_numeric(pd.Series(curva["prof"]), errors="coerce")
                                            rho_plot = pd.to_numeric(pd.Series(curva["rho_kt"]), errors="coerce")
                                            mask_ok = prof_plot.notna() & rho_plot.notna()

                                            if mask_ok.any():
                                                ax.plot(
                                                    rho_plot[mask_ok],
                                                    prof_plot[mask_ok],
                                                    linestyle="-",
                                                    color="purple",
                                                    linewidth=2,
                                                    label=f"Kick Tolerance - {bha_curva}",
                                                    zorder=5
                                                )
                                    else:
                                        curvas_kt_plot = st.session_state.get("curvas_kt_b2c", [])

                                        for i, curva in enumerate(curvas_kt_plot):
                                            bha_curva = curva.get("bha", f"Fase {i + 1}")
                                            prof_plot = pd.to_numeric(pd.Series(curva.get("prof", [])), errors="coerce")
                                            rho_plot = pd.to_numeric(pd.Series(curva.get("gf_kt", [])), errors="coerce")
                                            mask_ok = prof_plot.notna() & rho_plot.notna()

                                            if mask_ok.any():
                                                ax.plot(
                                                    rho_plot[mask_ok],
                                                    prof_plot[mask_ok],
                                                    linestyle="-",
                                                    color="purple",
                                                    linewidth=2,
                                                    label=f"Kick Tolerance - {bha_curva}",
                                                    zorder=5
                                                )

                                if "Peso do Fluido (lb/gal)" in curvas_visiveis:
                                    ax.plot(
                                        df_fluido["Peso do Fluido (lb/gal)"],
                                        df_fluido["Profundidade (m)"],
                                        linestyle="-",
                                        color="mediumvioletred",
                                        linewidth=2,
                                        label="Peso do Fluido (lb/gal)",
                                        zorder=5
                                    )

                                # Configurações do gráfico
                                ax.set_title('Fluido de Perfuração', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                ax.set_ylabel('Profundidade TVD (m)', fontsize=12)
                                ax.invert_yaxis()
                                ax.tick_params(axis='y', which='both', left=True, labelleft=True)

                                ax.set_yticks(range(
                                    st.session_state.y_min_fp,
                                    st.session_state.y_max_fp,
                                    st.session_state.y_step_fp
                                ))
                                ax.set_ylim(st.session_state.y_max_fp, st.session_state.y_min_fp)

                                ax.set_xticks(range(
                                    st.session_state.x_min_fp,
                                    st.session_state.x_max_fp,
                                    st.session_state.x_step_fp
                                ))
                                ax.set_xlim(st.session_state.x_min_fp, st.session_state.x_max_fp)

                                ax.grid(True, linestyle='--', alpha=0.5)

                                # Sapatas no mesmo padrão da aba de Assentamento
                                if "Sapatas" in curvas_visiveis:
                                    x_right = ax.get_xlim()[1] - 0.02 * (ax.get_xlim()[1] - ax.get_xlim()[0])

                                    try:
                                        for s in sapatas_plot:
                                            nome_sapata = s.get("nome", "Sapata")
                                            cor_sapata = s.get("cor", "black")

                                            prof_superficie = st.session_state.get("prs", None)
                                            tipo_sapata = s.get("tipo", "calculada")

                                            if (
                                                    st.session_state.metodo_kt == "Baixo para Cima"
                                                    and prof_superficie is not None
                                                    and np.isclose(float(s["prof"]), float(prof_superficie), atol=1e-6)
                                                    and tipo_sapata != "superficie"
                                            ):
                                                cor_box = "red"
                                            else:
                                                cor_box = cor_sapata

                                            ax.axhline(
                                                y=s["prof"],
                                                color=cor_sapata,
                                                linestyle="--",
                                                linewidth=2,
                                                zorder=6,
                                                label="_nolegend_"
                                            )

                                            ax.text(
                                                x=x_right,
                                                y=s["prof"] - 18,
                                                s=f'{nome_sapata}: {s["prof"]:.2f} m',
                                                color=cor_box,
                                                fontsize=9,
                                                va="center",
                                                ha="right",
                                                bbox=dict(
                                                    boxstyle="round,pad=0.2",
                                                    facecolor="white",
                                                    edgecolor=cor_box,
                                                    alpha=0.9
                                                ),
                                                zorder=7
                                            )
                                    except Exception:
                                        pass

                                if "Peso do Fluido (lb/gal)" in curvas_visiveis:
                                    try:
                                        df_intervalos_plot = st.session_state.get("df_intervalos_fluido", pd.DataFrame())

                                        if not df_intervalos_plot.empty:
                                            x_right = ax.get_xlim()[1] - 0.02 * (ax.get_xlim()[1] - ax.get_xlim()[0])

                                            for _, row in df_intervalos_plot.iterrows():
                                                y_meio = (row["Topo do Intervalo (m)"] + row["Base do Intervalo (m)"]) / 2

                                                txt_margem = TextArea(
                                                    f'Mínimo: {row["Margem do Intervalo (lb/gal)"]:.2f}',
                                                    textprops=dict(color="red", fontsize=9)
                                                )

                                                txt_pf = TextArea(
                                                    f'Ideal: {row["Peso do Fluido (lb/gal)"]:.2f}',
                                                    textprops=dict(color="green", fontsize=9)
                                                )

                                                txt_lm = TextArea(
                                                    f'Máximo: {row["Linha média do Intervalo (lb/gal)"]:.2f}',
                                                    textprops=dict(color="goldenrod", fontsize=9)
                                                )

                                                box = VPacker(
                                                    children=[txt_margem, txt_pf, txt_lm],
                                                    align="right",
                                                    pad=0,
                                                    sep=1
                                                )

                                                ab = AnnotationBbox(
                                                    box,
                                                    (x_right, y_meio),
                                                    xycoords='data',
                                                    box_alignment=(1, 0.5),
                                                    frameon=True,
                                                    bboxprops=dict(
                                                        boxstyle="round,pad=0.25",
                                                        facecolor="white",
                                                        edgecolor="black",
                                                        alpha=0.9
                                                    ),
                                                    zorder=8
                                                )

                                                ax.add_artist(ab)

                                    except Exception:
                                        pass

                                if st.session_state.leg_fp:
                                    ax.legend(
                                        loc='upper right',
                                        fontsize=8,
                                        frameon=True,
                                        shadow=True,
                                        fancybox=True,
                                        framealpha=1,
                                        facecolor='white',
                                        edgecolor='gray'
                                    )

                                add_watermark(
                                    ax,
                                    logo_path="logo2.png",
                                    xy=(0.50, 0.5),
                                    zoom=0.2,
                                    alpha=0.2,
                                    zorder=0
                                )

                                st.pyplot(st.session_state.fig_fp, use_container_width=True)

                    else:
                        st.error('Defina a profundidade de assentamento das sapatas na aba "Assentamento de Sapatas"', icon="🚨")

                with tab[1]:
                    if "df_fluido" in st.session_state and not st.session_state.df_fluido.empty:
                        st.dataframe(st.session_state.df_fluido, use_container_width=True, hide_index=True)
            else:
                st.error('Função não disponível para "Retroanálise"', icon="🚨")

        else:
            st.error('Por favor, insira um documento!', icon="🚨")

    #Anotações
    with tabs[7]:
        if "anotacoes" not in st.session_state:
            st.session_state.anotacoes = ""

        with st.container(border=True):
            def _interp_em_tvd(df_traj: pd.DataFrame, tvd_alvo: float):
                tvd = df_traj["TVD"].to_numpy(dtype=float)
                md = df_traj["MD"].to_numpy(dtype=float)

                if "Afastamento Horizontal (m)" in df_traj.columns:
                    hd = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                else:
                    e = df_traj["Easting"].to_numpy(dtype=float)
                    n = df_traj["Northing"].to_numpy(dtype=float)
                    hd = np.sqrt(e ** 2 + n ** 2)

                # ordena por TVD para garantir interp correta
                order = np.argsort(tvd)
                tvd = tvd[order]
                md = md[order]
                hd = hd[order]

                if tvd_alvo < tvd.min() or tvd_alvo > tvd.max():
                    raise ValueError(f"TVD fora do intervalo da trajetória ({tvd.min():.2f} a {tvd.max():.2f}).")

                md_i = float(np.interp(tvd_alvo, tvd, md))
                hd_i = float(np.interp(tvd_alvo, tvd, hd))
                return md_i, hd_i

            def _segmento_traj_por_tvd(df_traj: pd.DataFrame, tvd_ini: float, tvd_fim: float):
                if tvd_fim < tvd_ini:
                    tvd_ini, tvd_fim = tvd_fim, tvd_ini

                md_all = df_traj["MD"].to_numpy(dtype=float)
                tvd_all = df_traj["TVD"].to_numpy(dtype=float)

                if "Afastamento Horizontal (m)" in df_traj.columns:
                    hd_all = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                else:
                    e = df_traj["Easting"].to_numpy(dtype=float)
                    n = df_traj["Northing"].to_numpy(dtype=float)
                    hd_all = np.sqrt(e ** 2 + n ** 2)

                # ordena por TVD
                order = np.argsort(tvd_all)
                md_all = md_all[order]
                tvd_all = tvd_all[order]
                hd_all = hd_all[order]

                if tvd_ini < tvd_all.min() or tvd_fim > tvd_all.max():
                    raise ValueError(
                        f"Trecho fora do intervalo da trajetória em TVD ({tvd_all.min():.2f} a {tvd_all.max():.2f})."
                    )

                mask = (tvd_all >= tvd_ini) & (tvd_all <= tvd_fim)
                md_seg = md_all[mask]
                tvd_seg = tvd_all[mask]
                hd_seg = hd_all[mask]

                md_i = float(np.interp(tvd_ini, tvd_all, md_all))
                hd_i = float(np.interp(tvd_ini, tvd_all, hd_all))

                md_f = float(np.interp(tvd_fim, tvd_all, md_all))
                hd_f = float(np.interp(tvd_fim, tvd_all, hd_all))

                if md_seg.size == 0 or tvd_seg[0] != tvd_ini:
                    md_seg = np.insert(md_seg, 0, md_i)
                    tvd_seg = np.insert(tvd_seg, 0, tvd_ini)
                    hd_seg = np.insert(hd_seg, 0, hd_i)

                if tvd_seg[-1] != tvd_fim:
                    md_seg = np.append(md_seg, md_f)
                    tvd_seg = np.append(tvd_seg, tvd_fim)
                    hd_seg = np.append(hd_seg, hd_f)

                return hd_seg, tvd_seg, md_seg

            def _interp_em_md(df_traj: pd.DataFrame, md_alvo: float):
                md = df_traj["MD"].to_numpy(dtype=float)
                tvd = df_traj["TVD"].to_numpy(dtype=float)

                if "Afastamento Horizontal (m)" in df_traj.columns:
                    hd = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                else:
                    e = df_traj["Easting"].to_numpy(dtype=float)
                    n = df_traj["Northing"].to_numpy(dtype=float)
                    hd = np.sqrt(e ** 2 + n ** 2)

                order = np.argsort(md)
                md = md[order]
                tvd = tvd[order]
                hd = hd[order]

                if md_alvo < md.min() or md_alvo > md.max():
                    raise ValueError(
                        f"MD fora do intervalo da trajetória ({md.min():.2f} a {md.max():.2f})."
                    )

                tvd_i = float(np.interp(md_alvo, md, tvd))
                hd_i = float(np.interp(md_alvo, md, hd))

                return tvd_i, hd_i

            def _segmento_traj_por_md(df_traj: pd.DataFrame, md_ini: float, md_fim: float):
                if md_fim < md_ini:
                    md_ini, md_fim = md_fim, md_ini

                md_all = df_traj["MD"].to_numpy(dtype=float)
                tvd_all = df_traj["TVD"].to_numpy(dtype=float)

                if "Afastamento Horizontal (m)" in df_traj.columns:
                    hd_all = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                else:
                    e = df_traj["Easting"].to_numpy(dtype=float)
                    n = df_traj["Northing"].to_numpy(dtype=float)
                    hd_all = np.sqrt(e ** 2 + n ** 2)

                order = np.argsort(md_all)
                md_all = md_all[order]
                tvd_all = tvd_all[order]
                hd_all = hd_all[order]

                if md_ini < md_all.min() or md_fim > md_all.max():
                    raise ValueError(
                        f"Trecho fora do intervalo da trajetória em MD ({md_all.min():.2f} a {md_all.max():.2f})."
                    )

                mask = (md_all >= md_ini) & (md_all <= md_fim)

                md_seg = md_all[mask]
                tvd_seg = tvd_all[mask]
                hd_seg = hd_all[mask]

                tvd_i = float(np.interp(md_ini, md_all, tvd_all))
                hd_i = float(np.interp(md_ini, md_all, hd_all))

                tvd_f = float(np.interp(md_fim, md_all, tvd_all))
                hd_f = float(np.interp(md_fim, md_all, hd_all))

                if md_seg.size == 0 or not np.isclose(md_seg[0], md_ini):
                    md_seg = np.insert(md_seg, 0, md_ini)
                    tvd_seg = np.insert(tvd_seg, 0, tvd_i)
                    hd_seg = np.insert(hd_seg, 0, hd_i)

                if not np.isclose(md_seg[-1], md_fim):
                    md_seg = np.append(md_seg, md_fim)
                    tvd_seg = np.append(tvd_seg, tvd_f)
                    hd_seg = np.append(hd_seg, hd_f)

                return hd_seg, tvd_seg, md_seg

            st.markdown("### Trajetória 2D (TVD x Afastamento Horizontal)")

            if "df_out_traj" not in st.session_state or not isinstance(st.session_state.df_out_traj, pd.DataFrame):
                st.info(
                    "A trajetória ainda não foi calculada.")
            else:
                df_traj = st.session_state.df_out_traj.copy()

                # =========================
                # EVENTOS (opções)
                # =========================
                EVENTOS = [
                    "Drag",
                    "Overpull",
                    "Pescaria",
                    "Repasse",
                    "Coluna presa",
                    "Ameaça de prisão",
                    "Coluna topou",
                    "Ferramenta de perfilagem topou",
                    "Perda parcial de circulação",
                    "Perda severa de circulação",
                ]

                # =========================
                # Estilo por evento (cor + símbolo)
                # =========================
                MAPA_EVENTO_ESTILO = {
                    "Drag": {"cor": "orange", "simbolo": "triangle-up"},
                    "Overpull": {"cor": "black", "simbolo": "square"},
                    "Repasse": {"cor": "blue", "simbolo": "circle"},
                    "Coluna presa": {"cor": "red", "simbolo": "x"},
                    "Ameaça de prisão": {"cor": "purple", "simbolo": "star-square"},
                    "Coluna topou": {"cor": "gray", "simbolo": "diamond"},
                    "Ferramenta de perfilagem topou": {"cor": "black", "simbolo": "diamond-open-dot"},
                    "Perda parcial de circulação": {"cor": "orange", "simbolo": "triangle-down"},
                    "Perda severa de circulação": {"cor": "red", "simbolo": "triangle-down"},
                    "Pescaria": {"cor": "brown", "simbolo": "bowtie"},
                }

                # =========================
                # Estados (somente o calculado)
                # =========================
                if "traj_marks_calc" not in st.session_state:
                    st.session_state.traj_marks_calc = pd.DataFrame(columns=[
                        "Tipo", "MD Inicial", "MD Final",
                        "TVD Inicial", "TVD Final",
                        "HD Inicial", "HD Final",
                        "Evento", "_cor_plot", "_simbolo"
                    ])

                # Layout
                col_left, col_right = st.columns((1, 0.75))

                with col_left:
                    df_eventos = st.session_state.get("df_eventos", None)

                    if not isinstance(df_eventos, pd.DataFrame) or df_eventos.empty:
                        st.info("Nenhum evento encontrado na aba **Eventos** do Excel.")
                        st.session_state.traj_marks_calc = pd.DataFrame(columns=[
                            "Tipo", "MD Inicial", "MD Final",
                            "TVD Inicial", "TVD Final",
                            "HD Inicial", "HD Final",
                            "Evento", "_cor_plot", "_simbolo"
                        ])
                    else:
                        with st.expander("Ver eventos lidos do Excel", expanded=True):
                            st.dataframe(df_eventos, use_container_width=True, hide_index=True)

                        df_in = df_eventos.copy()

                        # normaliza colunas esperadas
                        if "MD Inicial" in df_in.columns:
                            df_in["MD Inicial"] = pd.to_numeric(df_in["MD Inicial"], errors="coerce")
                        else:
                            df_in["MD Inicial"] = np.nan

                        if "MD Final" in df_in.columns:
                            df_in["MD Final"] = pd.to_numeric(df_in["MD Final"], errors="coerce")
                        else:
                            df_in["MD Final"] = np.nan

                        if "Evento" not in df_in.columns:
                            df_in["Evento"] = ""

                        df_in["Evento"] = df_in["Evento"].astype("string").fillna("").str.strip()

                        df_in = df_in.dropna(subset=["MD Inicial"])
                        df_in = df_in[df_in["Evento"] != ""]

                        rows = []
                        linhas_com_erro = []

                        for _, r in df_in.iterrows():
                            try:
                                md_i = float(r["MD Inicial"])
                                md_f = r["MD Final"]
                                evento = str(r["Evento"]).strip()

                                estilo = MAPA_EVENTO_ESTILO.get(evento, {"cor": "red", "simbolo": "diamond"})
                                cor_plot = estilo["cor"]
                                simbolo = estilo["simbolo"]

                                # PONTO
                                if pd.isna(md_f):
                                    tvd_i, hd_i = _interp_em_md(df_traj, md_i)
                                    rows.append({
                                        "Tipo": "Ponto",
                                        "MD Inicial": md_i,
                                        "MD Final": np.nan,
                                        "TVD Inicial": tvd_i,
                                        "TVD Final": np.nan,
                                        "HD Inicial": hd_i,
                                        "HD Final": np.nan,
                                        "Evento": evento,
                                        "_cor_plot": cor_plot,
                                        "_simbolo": simbolo
                                    })

                                # TRECHO
                                else:
                                    md_f = float(md_f)
                                    md_a, md_b = (md_i, md_f) if md_f >= md_i else (md_f, md_i)

                                    tvd_a, hd_a = _interp_em_md(df_traj, md_a)
                                    tvd_b, hd_b = _interp_em_md(df_traj, md_b)

                                    rows.append({
                                        "Tipo": "Trecho",
                                        "MD Inicial": md_a,
                                        "MD Final": md_b,
                                        "TVD Inicial": tvd_a,
                                        "TVD Final": tvd_b,
                                        "HD Inicial": hd_a,
                                        "HD Final": hd_b,
                                        "Evento": evento,
                                        "_cor_plot": cor_plot,
                                        "_simbolo": simbolo
                                    })


                            except Exception as e:
                                linhas_com_erro.append({"MD Inicial": r.get("MD Inicial"),"MD Final": r.get("MD Final"),
                                                        "Evento": r.get("Evento"),"Erro": str(e)})

                        df_calc = pd.DataFrame(rows)
                        if not df_calc.empty:
                            df_calc = df_calc.sort_values(["Tipo", "MD Inicial"]).reset_index(drop=True)

                        st.session_state.traj_marks_calc = df_calc

                        if linhas_com_erro:
                            st.warning("Alguns eventos foram ignorados.")

                            df_erros = pd.DataFrame(linhas_com_erro)

                            st.dataframe(
                                df_erros,
                                use_container_width=True,
                                hide_index=True
                            )

                with col_right:
                    with st.container(border=True):
                        if "Afastamento Horizontal (m)" in df_traj.columns:
                            hd_traj = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                        else:
                            hd_traj = np.sqrt(
                                df_traj["Easting"].to_numpy(float) ** 2 +
                                df_traj["Northing"].to_numpy(float) ** 2
                            )

                        tvd_traj_plot = df_traj["TVD"].to_numpy(dtype=float)

                        hd_min = float(np.nanmin(hd_traj)) if len(hd_traj) else 0.0
                        hd_max = float(np.nanmax(hd_traj)) if len(hd_traj) else 0.0
                        hd_span = max(hd_max - hd_min, 1.0)

                        margem_traj = max(10.0, 0.03 * hd_span)
                        x_left_traj = hd_min - margem_traj
                        x_right_traj = hd_max + margem_traj

                        altura_fig = int(min(1400, max(700, 0.10 * float(st.session_state.y_max_pp))))

                        fig2d = make_subplots(
                            rows=1,
                            cols=2,
                            shared_yaxes=True,
                            horizontal_spacing=0.03,
                            column_widths=[0.2, 0.8]
                        )

                        # Trajetória principal
                        fig2d.add_trace(
                            go.Scatter(
                                x=hd_traj,
                                y=df_traj["TVD"],
                                mode="lines",
                                line=dict(color="red", width=4),
                                name="Trajetória",
                                showlegend=False
                            ),
                            row=1, col=2
                        )

                        df_notes = st.session_state.traj_marks_calc

                        if isinstance(df_notes, pd.DataFrame) and not df_notes.empty:
                            # TRECHOS
                            df_trechos = df_notes[df_notes["Tipo"] == "Trecho"].copy()

                            for _, r in df_trechos.iterrows():
                                cor_plot = r["_cor_plot"]
                                simbolo = r["_simbolo"]

                                md_a = float(r["MD Inicial"])
                                md_b = float(r["MD Final"])

                                try:
                                    hd_seg, tvd_seg, md_seg = _segmento_traj_por_md(df_traj, md_a, md_b)

                                    # Linha do trecho
                                    fig2d.add_trace(
                                        go.Scatter(
                                            x=hd_seg,
                                            y=tvd_seg,
                                            mode="lines",
                                            line=dict(width=6, color=cor_plot),
                                            showlegend=False,
                                            hovertemplate=(
                                                "Trecho<br>"
                                                f"Evento: {r['Evento']}<br>"
                                                "MD: %{customdata[0]:.1f} m<br>"
                                                "TVD: %{y:.1f} m<br>"
                                                "HD: %{x:.1f} m<extra></extra>"
                                            ),
                                            customdata=np.c_[md_seg]
                                        ),
                                        row=1,
                                        col=2
                                    )

                                    # Marcador no centro do trecho
                                    md_centro = (md_a + md_b) / 2.0

                                    tvd_centro, hd_centro = _interp_em_md(df_traj, md_centro)

                                    fig2d.add_trace(
                                        go.Scatter(
                                            x=[hd_centro],
                                            y=[tvd_centro],
                                            mode="markers",
                                            marker=dict(
                                                size=14,
                                                color=cor_plot,
                                                symbol=simbolo,
                                                line=dict(color="black", width=1.5)
                                            ),
                                            showlegend=False,
                                            hovertemplate=(
                                                "Trecho<br>"
                                                f"Evento: {r['Evento']}<br>"
                                                f"MD inicial: {md_a:.1f} m<br>"
                                                f"MD final: {md_b:.1f} m<br>"
                                                f"MD centro: {md_centro:.1f} m<br>"
                                                f"TVD centro: {tvd_centro:.1f} m<br>"
                                                f"HD centro: {hd_centro:.1f} m<extra></extra>"
                                            )
                                        ),
                                        row=1,
                                        col=2
                                    )

                                except Exception as e:
                                    st.warning(f"Erro ao plotar trecho {r.get('Evento', '')}: {e}")

                            # PONTOS
                            df_pontos = df_notes[df_notes["Tipo"] == "Ponto"].copy()
                            for _, r in df_pontos.iterrows():
                                cor_plot = r["_cor_plot"]
                                simbolo = r["_simbolo"]

                                fig2d.add_trace(
                                    go.Scatter(
                                        x=[float(r["HD Inicial"])],
                                        y=[float(r["TVD Inicial"])],
                                        mode="markers",
                                        marker=dict(
                                            size=12,
                                            color=cor_plot,
                                            symbol=simbolo,
                                            line=dict(color="black", width=1.5)
                                        ),
                                        showlegend=False,
                                        hovertemplate=(
                                            "Ponto<br>"
                                            f"Evento: {r['Evento']}<br>"
                                            f"MD: {float(r['MD Inicial']):.1f} m<br>"
                                            f"TVD: {float(r['TVD Inicial']):.1f} m<br>"
                                            f"HD: {float(r['HD Inicial']):.1f} m<extra></extra>"
                                        )
                                    ),
                                    row=1, col=2
                                )

                            # Legenda dos eventos
                            eventos_unicos = []
                            if "Evento" in df_notes.columns:
                                eventos_unicos = [
                                    e for e in df_notes["Evento"].dropna().astype(str).unique().tolist()
                                    if e in MAPA_EVENTO_ESTILO
                                ]

                            for evento in eventos_unicos:
                                estilo = MAPA_EVENTO_ESTILO[evento]
                                nome_legenda = evento

                                fig2d.add_trace(
                                    go.Scatter(
                                        x=[None],
                                        y=[None],
                                        mode="markers",
                                        name=nome_legenda,
                                        showlegend=True,
                                        marker=dict(
                                            size=12,
                                            symbol=estilo["simbolo"],
                                            color=estilo["cor"],
                                            line=dict(color="black", width=1.5)
                                        ),
                                        hoverinfo="skip"
                                    ),
                                    row=1, col=2
                                )

                        # Rig no painel da trajetória
                        rig_sizex = max(150.0, 0.06 * hd_span)
                        rig_sizey = max(190.0, 0.06 * hd_span)

                        rig_img = Image.open("rig_t.png")
                        fig2d.add_layout_image(
                            dict(
                                source=rig_img,
                                xref="x2",
                                yref="y2",
                                x=0,
                                y=0,
                                sizex=rig_sizex,
                                sizey=rig_sizey,
                                xanchor="center",
                                yanchor="bottom",
                                layer="above"
                            )
                        )
                        # -------------------------
                        # Litologia em subplot próprio
                        # -------------------------
                        def get_paleta_lito():
                            return {
                                "Argilito": {"bg": "#9ACD32", "simbol": "|"},
                                "Folhelho": {"bg": "#2f4f4f", "simbol": "-"},
                                "Siltito": {"bg": "#A67B5B", "simbol": "-"},
                                "Arenito": {"bg": "#FFD580", "simbol": "."},
                                "Fm. Permeável": {"bg": "#FFD580", "simbol": "."},
                                "Diamictito": {"bg": "#E97451", "simbol": "."},
                                "Conglomerado": {"bg": "#CD853F", "simbol": "."},
                                "Calcário": {"bg": "#B0C4DE", "simbol": "."},
                                "Carbonato": {"bg": "#cfe8f3", "simbol": "x"},
                                "Anidrita / Gipsita": {"bg": "#E6E6FA", "simbol": "/"},
                                "Halita": {"bg": "#FFFFFF", "simbol": "."},
                                "Calcissiltito": {"bg": "#D8BFD8", "simbol": "."},
                                "Calcarenito": {"bg": "#F5DEB3", "simbol": "."},
                                "Calcirrudito": {"bg": "#4682B4", "simbol": "."},
                                "Coquina": {"bg": "#FFDEAD", "simbol": "."},
                                "Dolomito": {"bg": "#C2B280", "simbol": "."},
                                "Basalto": {"bg": "#2F4F4F", "simbol": "+"},
                                "Diabásio": {"bg": "#556B2F", "simbol": "."},
                            }
                        def add_lito_track_plotly(
                                fig,
                                profundidades,
                                litologias,
                                base_final,
                                show_labels=False
                        ):
                            paleta = get_paleta_lito()
                            x0, x1 = 0.0, 1.0

                            for i in range(len(profundidades)):
                                z_top = float(profundidades[i])
                                z_base = float(profundidades[i + 1]) if i < len(profundidades) - 1 else float(
                                    base_final)

                                lit = litologias[i]
                                estilo = paleta.get(lit, {"bg": "#CCCCCC", "simbol": "."})

                                fig.add_trace(
                                    go.Scatter(
                                        x=[x0, x1, x1, x0, x0],
                                        y=[z_top, z_top, z_base, z_base, z_top],
                                        fill="toself",
                                        mode="lines",
                                        line=dict(color="black", width=1),
                                        fillpattern=dict(
                                            shape=estilo["simbol"],
                                            fgcolor="black",
                                            bgcolor=estilo["bg"],
                                            size=4,
                                            solidity=0.05
                                        ),
                                        showlegend=False,
                                        hoverinfo="skip"
                                    ),
                                    row=1, col=1
                                )

                                if show_labels:
                                    altura_intervalo = abs(z_base - z_top)

                                    if altura_intervalo >= 30:
                                        font_size = 11
                                    elif altura_intervalo >= 15:
                                        font_size = 10
                                    elif altura_intervalo >= 8:
                                        font_size = 9
                                    else:
                                        font_size = 8

                                    if altura_intervalo >= 6:
                                        fig.add_annotation(
                                            x=0.5,
                                            y=(z_top + z_base) / 2,
                                            text=lit,
                                            showarrow=False,
                                            xanchor="center",
                                            yanchor="middle",
                                            font=dict(size=font_size, color="black"),
                                            xref="x",
                                            yref="y",
                                            align="center"
                                        )
                        add_lito_track_plotly(
                            fig2d,
                            profundidades=profundidades,
                            litologias=litologias,
                            base_final=st.session_state.y_max_pp,
                            show_labels=True
                        )

                        # -------------------------
                        # Sapatas na trajetória
                        # -------------------------
                        sapatas_df = st.session_state.get("sapatas_df", None)
                        sapatas_plot = []

                        if sapatas_df is not None and not sapatas_df.empty:
                            tvd_traj = df_traj["TVD"].to_numpy(dtype=float)

                            if "Afastamento Horizontal (m)" in df_traj.columns:
                                afast_traj = df_traj["Afastamento Horizontal (m)"].to_numpy(dtype=float)
                            else:
                                afast_traj = np.sqrt(
                                    df_traj["Easting"].to_numpy(float) ** 2 +
                                    df_traj["Northing"].to_numpy(float) ** 2
                                )

                            ordem = np.argsort(tvd_traj)
                            tvd_traj = tvd_traj[ordem]
                            afast_traj = afast_traj[ordem]

                            for _, row in sapatas_df.iterrows():
                                prof_sapata = row.get("Profundidade da sapata (m)", None)
                                fase = row.get("Fase", "")

                                if prof_sapata is None or pd.isna(prof_sapata):
                                    continue

                                prof_sapata = float(prof_sapata)

                                if prof_sapata < tvd_traj.min() or prof_sapata > tvd_traj.max():
                                    continue

                                x_sapata = float(np.interp(prof_sapata, tvd_traj, afast_traj))

                                sapatas_plot.append({
                                    "prof": prof_sapata,
                                    "fase": fase,
                                    "x": x_sapata
                                })

                            sapatas_plot = sorted(sapatas_plot, key=lambda s: s["prof"])

                            linha_half = max(30.0, 0.015 * hd_span)

                            cores_sapatas = [
                                "#000000",
                                "#1f77b4",
                                "#2ca02c",
                                "#ff7f0e",
                                "#d62728",
                                "#9467bd",
                                "#8c564b",
                                "#e377c2",
                            ]

                            for i, s in enumerate(sapatas_plot):
                                prof_sapata = s["prof"]
                                fase = s["fase"]
                                x_sapata = s["x"]
                                cor_sapata = cores_sapatas[i % len(cores_sapatas)]

                                fig2d.add_trace(
                                    go.Scatter(
                                        x=[x_sapata - linha_half, x_sapata + linha_half],
                                        y=[prof_sapata, prof_sapata],
                                        mode="lines",
                                        line=dict(
                                            color=cor_sapata,
                                            width=3,
                                            dash="dot"
                                        ),
                                        showlegend=False,
                                        hovertemplate=(
                                            f"Sapata {fase}<br>"
                                            f"Profundidade: {prof_sapata:.0f} m<extra></extra>"
                                        )
                                    ),
                                    row=1, col=2
                                )

                                fig2d.add_trace(
                                    go.Scatter(
                                        x=[None],
                                        y=[None],
                                        mode="lines",
                                        line=dict(
                                            color=cor_sapata,
                                            width=3,
                                            dash="dot"
                                        ),
                                        name=f"Sapata {fase} - {prof_sapata:.2f} m",
                                        showlegend=True,
                                        hoverinfo="skip"
                                    ),
                                    row=1, col=2
                                )

                        fig2d.update_layout(
                            title=dict(
                                # text="Vista lateral + Eventos",
                                x=0.5,
                                xanchor="center"
                            ),
                            height=altura_fig,
                            margin=dict(l=100, r=90, t=80, b=100),
                            showlegend=True,
                            legend=dict(
                                orientation="v",
                                yanchor="top",
                                y=1,
                                xanchor="left",
                                x=1.02
                            )
                        )

                        # eixo X da litologia
                        fig2d.update_xaxes(
                            range=[0, 1],
                            visible=False,
                            row=1, col=1
                        )

                        fig2d.update_xaxes(
                            title_text="Afastamento Horizontal (m)",
                            title_standoff=25,
                            automargin=True,
                            tickfont=dict(size=10),
                            row=1,
                            col=2
                        )

                        fig2d.update_yaxes(
                            title_text="TVD (m)",
                            title_standoff=25,
                            automargin=True,
                            tickfont=dict(size=10),
                            autorange="reversed",
                            row=1,
                            col=1
                        )

                        fig2d.update_yaxes(
                            title_standoff=25,
                            automargin=True,
                            tickfont=dict(size=10),
                            autorange="reversed",
                            row=1,
                            col=2
                        )

                        st.session_state.fig2d = fig2d
                        st.plotly_chart(fig2d, use_container_width=True)

        with st.container(border=True):
            st.markdown("## Anotações")
            with st.expander("Anotações do usuário", expanded=True):
                st.session_state.anotacoes = st.text_area(
                    "Registre aqui observações, decisões e pendências do estudo:",
                    value=st.session_state.anotacoes,
                    height=260,
                    placeholder="Ex.: Ajustar coesão na formação X; revisar LOT do poço Y; confirmar densidade do fluido na fase Z..."
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar anotações", use_container_width=True, type="primary"):
                        st.toast("Anotações salvas.")
                with col2:
                    if st.button("🗑️ Limpar", use_container_width=True):
                        st.session_state.anotacoes = ""
                        st.rerun()

    # Relatório
    with tabs[8]:
        col_pdf1, col_pdf2, col_pdf3, col_pdf4 = st.columns((0.6, 0.8, 0.2, 0.3))

        with col_pdf1:
            if st.session_state.well_name == '':
                report_name = 'Relatorio_Final.pdf'
            else:
                report_name = f'{st.session_state.well_name}.pdf'

            with st.container(border=True):
                st.markdown("### Páginas do relatório")

                if "pdf_paginas_selecionadas" not in st.session_state:
                    st.session_state.pdf_paginas_selecionadas = list(PAGINAS_PDF_OPCOES.keys())

                col_sel1, col_sel2 = st.columns(2)

                with col_sel1:
                    if st.button("Selecionar todas", use_container_width=True, type="primary"):
                        st.session_state.pdf_paginas_selecionadas = list(PAGINAS_PDF_OPCOES.keys())
                        st.session_state.pdf_bytes = None
                        st.session_state.pdf_ready = False
                        st.session_state.pdf_view_open = False
                        st.rerun()

                with col_sel2:
                    if st.button("Limpar", use_container_width=True, type="primary"):
                        st.session_state.pdf_paginas_selecionadas = []
                        st.session_state.pdf_bytes = None
                        st.session_state.pdf_ready = False
                        st.session_state.pdf_view_open = False
                        st.rerun()

                selecao_anterior = st.session_state.get(
                    "_pdf_paginas_selecionadas_anterior",
                    list(PAGINAS_PDF_OPCOES.keys())
                )

                paginas_escolhidas = st.multiselect(
                    "Escolha quais páginas devem aparecer no PDF:",
                    options=list(PAGINAS_PDF_OPCOES.keys()),
                    default=st.session_state.pdf_paginas_selecionadas,
                    format_func=lambda x: PAGINAS_PDF_OPCOES.get(x, x),
                    key="pdf_paginas_multiselect"
                )

                st.session_state.pdf_paginas_selecionadas = paginas_escolhidas

                if paginas_escolhidas != selecao_anterior:
                    st.session_state.pdf_bytes = None
                    st.session_state.pdf_ready = False
                    st.session_state.pdf_view_open = False

                st.session_state._pdf_paginas_selecionadas_anterior = paginas_escolhidas.copy()

                if not paginas_escolhidas:
                    st.warning("Selecione pelo menos uma página para gerar o relatório.")

                view = st.button(
                    ':bookmark_tabs: Ver Relatório',
                    key='pdf_view_bt',
                    use_container_width=True,
                    disabled=not st.session_state.pdf_paginas_selecionadas,
                    type="primary"
                )

                if view:
                    with st.spinner("Gerando relatório."):
                        st.session_state.pdf_bytes = gerar_relatorio_pdf()
                        st.session_state.pdf_ready = True
                        st.session_state.pdf_view_open = True

                if st.session_state.pdf_ready and st.session_state.pdf_bytes is not None:
                    st.download_button(
                        label="⬇️ Baixar Relatório",
                        data=st.session_state.pdf_bytes,
                        file_name=report_name,
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )

        with col_pdf2:
            if st.session_state.pdf_view_open and st.session_state.pdf_bytes is not None:
                container_pdf = st.container(border=True, height=900)
                with container_pdf:
                    pdf_viewer(
                        input=st.session_state.pdf_bytes,
                        width=700,
                        pages_vertical_spacing=20
                    )

    # Informações Gerais
    with tabs[9]:
        st.title("📘 Informações Gerais do SYGA")

        # --- Dicionário com informações dos perfis ---
        parameters = {
            "Curvas de geopressões": {
                "Gradiente": {
                    "Sigla": ["Gradiente"],
                    "Nome": [
                        "Variação de pressão ao longo de um intervalo de profundidade, medido com base em um determinado referencial (Datum)"],
                    "Unidade": "massa/volume"
                },
                "Sobrecarga": {
                    "Sigla": ["Sobrecarga"],
                    "Nome": ["Pressão gerada em uma certa porfundidade devido ao"
                             " peso das camadass de rochas sobrepostas (pode ser expressa em gradiente)"],
                    "Unidade": "pressão ou massa/volume"
                },

                "Pressão de poros": {
                    "Sigla": ["Pressão de poros"],
                    "Nome": ["Pressão contida nos poros da rocha (normalmente expressada em gradiente)"],
                    "Unidade": "pressão ou massa/volume"
                },

                "Pressão de fratura": {
                    "Sigla": ["Pressão de fratura"],
                    "Nome": ["Pressão necessária para levar a falha da formação por tração,"
                             " podendo ser fratura superior ou inferior (normalmente expressada em gradiente)"],
                    "Unidade": "pressão ou massa/volume"
                },

                "Pressão de colapso": {
                    "Sigla": ["Pressão de colpaso"],
                    "Nome": ["Pressão necessária para levar a falha da formação por cisalhamento"
                             " podendo ser colapso superior ou inferior (pode ser expressa em gradiente)"],
                    "Unidade": "pressão ou massa/volume"
                },
            },
            "Perfil": {
                "Sônico compressional": {
                    "Sigla": ["DT", "DTCO"],
                    "Nome": ["Delta-T Compressional"],
                    "Unidade": "µs/ft"
                },
                "Sônico cisalhante": {
                    "Sigla": ["DTS", "DTSM"],
                    "Nome": ["Compressional Wave Transit Time", "Sonic Transit Time"],
                    "Unidade": "µs/ft"
                },
                "Densidade": {
                    "Sigla": ["RHOB", "DEN"],
                    "Nome": ["Standard Resolution Formation Density", "Bulk density"],
                    "Unidade": "g/cm³"
                },
                "Gamma-Ray": {
                    "Sigla": ["GR"],
                    "Nome": ["Gamma Ray"],
                    "Unidade": "gAPI"
                }
            }
        }

        # --- Layout com colunas ---
        col1, col2 = st.columns([1, 2])

        with col1:
            cat = st.selectbox(
                "Selecione a categoria:",
                options=list(parameters.keys())
            )
            perfil_selecionado = st.selectbox(
                "Selecione um perfil:",
                options=list(parameters[cat].keys())
            )

        with col2:
            dados = parameters[cat][perfil_selecionado]

            # Converte listas em string separada por vírgula

            if cat == "Curvas de geopressões":
                op1 = 'Nome'
                op2 = 'Definição'
                t = 'Curvas de Geopressões'
            else:
                op1 = 'Sigla(s)'
                op2 = 'Nome(s)'
                t = 'Perfil'
            siglas = ", ".join(dados["Sigla"])
            nomes = ", ".join(dados["Nome"])

            st.markdown(
                f"""
                ### ℹ️ {t} - **{perfil_selecionado}**

                - **{op1}:** `{siglas}`
                - **{op2}:** {nomes}
                - **Unidade:** *{dados['Unidade']}*
                """,
                unsafe_allow_html=True
            )

        # Um toque estético extra (barra de separação)
        st.markdown("---")
        st.info("💡 Dica: selecione um perfil na caixa à esquerda para visualizar os detalhes.")

geo_page()
