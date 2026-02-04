import os
import re
import utm
import yaml
import math
import folium
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from streamlit_folium import st_folium
from scipy.interpolate import griddata, Rbf
from scipy.ndimage import gaussian_filter1d
import matplotlib.patheffects as path_effects
from statsmodels.nonparametric.smoothers_lowess import lowess

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
st.image(img_cab, width=1500)


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
        "Marga": {"bg": "#EEE8AA", "simbol": "-"},
        "Calcário": {"bg": "#B0C4DE", "simbol": "."},
        "Calcissiltito": "#D8BFD8",
        "Calcarenito": "#F5DEB3",
        "Calcirrudito": "#4682B4",
        "Coquina": "#FFDEAD",
        "Dolomito": "#C2B280",
        "Silexito": "#808080",
        "Basalto": {"bg": "#2F4F4F", "simbol": "+"},
        "Diabásio": "#556B2F",
        "Ígnea Ácida": "#CD5C5C",
        "Ígnea Alcalina": "#B22222",
        "Ígnea Não Especificada": "#A9A9A9",
        "Metamórfica Não Especificada": "#696969",
        "SDR": "#FF7F50",
        "Crosta Oceânica": "#000080"
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


@st.dialog("Adicionar Testes de Formação")
def rft(fig):
    # Dados iniciais vazios
    dados_iniciais = pd.DataFrame({
        "Profundidade (m)": [],
        "Peso do Fluido (lb/gal)": [],
        "Teste RFT (lb/gal)": []

    })

    # Tabela editável
    st.session_state.dados_rft = st.data_editor(
        dados_iniciais,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    # Botão para confirmar e fechar a aba
    if st.button("Inserir valores", type="primary", use_container_width=True):
        st.rerun()


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

def suavizar_2(x, y, grad_medio):

    x = np.asarray(x)
    y = np.asarray(y)

    # Array de saída
    y_out = y.copy()

    z_ini = st.session_state.anormal

    # --- parte rasa: valor constante ---
    mask_raso = x < z_ini

    if np.isscalar(grad_medio):
        y_out[mask_raso] = grad_medio
    else:
        grad_medio = np.asarray(grad_medio)
        y_out[mask_raso] = grad_medio[mask_raso]

    # --- parte profunda: suavização ---
    mask_prof = x >= z_ini

    # Proteção
    if mask_prof.sum() < 3:
        return y_out

    x_seg = x[mask_prof]
    y_seg = y[mask_prof]

    frac = st.session_state.frac
    sigma = st.session_state.gauss

    # Detecta patamar (mesma lógica da sua suavizar)
    razao_unicos = np.unique(y_seg).size / len(y_seg)
    dy = np.abs(np.diff(y_seg))
    patamar = np.mean(dy < 1e-3)

    if razao_unicos < 0.1 or patamar > 0.7:
        y_out[mask_prof] = gaussian_filter1d(y_seg, sigma=sigma)
    else:
        y_out[mask_prof] = lowess(
            y_seg,
            x_seg,
            frac=frac,
            return_sorted=False
        )

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


# def normal(prof, gn):
#     max_depth = prof
#     depths = list(range(0, int(max_depth) + 1))
#     df_gfs = pd.DataFrame({'Profundidade (m)': depths})
#
#     # 1. Valor alvo da pressão final
#     p_alvo = 0.1704 * max_depth * gn
#
#     # 2. Determinar profundidade de transição
#     z_min = st.session_state.rtkb + st.session_state.es
#     z_max = prof
#
#     # 3. Calcular densidade média necessária no intervalo ajustável
#     # Parte inferior: profundidade acima de 400 até anormal → densidade = 8.5
#     prof_adicional = max(0, max_depth - z_max)
#     p_adicional = 0.1704 * st.session_state.gn * prof_adicional
#
#     # Parte de transição: z_min até z_max (densidade será ajustada)
#     prof_transicao = z_max - z_min
#     p_transicao = p_alvo - p_adicional  # pressão que deve ser acumulada nessa faixa
#
#     # Densidade média necessária na faixa z_min a z_max:
#     if prof_transicao > 0:
#         dens_media_transicao = p_transicao / (0.1704 * prof_transicao)
#     else:
#         dens_media_transicao = st.session_state.gn  # fallback se faixa inválida
#
#     # 4. Construir o perfil de densidade do fluido
#     ff = []
#     for i in df_gfs['Profundidade (m)']:
#         if i < z_min:
#             ff.append(0)
#         elif i <= z_max:
#             ff.append(dens_media_transicao)
#         else:
#             ff.append(st.session_state.gn)
#
#     df_gfs['Fluido da formação (ppg)'] = ff
#
#     # 5. Calcular pressão
#     pp = [0]
#     for i in range(1, len(df_gfs)):
#         incremento = df_gfs['Profundidade (m)'][i] - df_gfs['Profundidade (m)'][
#             i - 1]
#         dens = df_gfs['Fluido da formação (ppg)'][i]
#         pressao = pp[-1] + 0.1704 * dens * incremento
#         pp.append(pressao)
#
#     df_gfs['Pressão (psi)'] = pp
#
#     # 6. Calcular gradiente
#     gpp = []
#     for i in range(len(df_gfs)):
#         profundidade = df_gfs['Profundidade (m)'][i]
#         if profundidade == 0:
#             gpp.append(0)
#         else:
#             g = df_gfs['Pressão (psi)'][i] / (0.1704 * profundidade)
#             gpp.append(g)
#
#     df_gfs['Gradiente de Pressão de Poros (lb/gal)'] = gpp
#
#     st.session_state.df_gfs = df_gfs

def normal(df):
    prof_ini = st.session_state.nf
    val_ini = 0.

    prof_fim = df["Profundidade"].min()
    val_fim = st.session_state.gn

    alpha = 4
    n = len(df)

    profundidade = np.linspace(prof_ini, prof_fim, n)

    t = (profundidade - prof_ini) / (prof_fim - prof_ini)

    valores = val_ini + (val_fim - val_ini) * (
        (1 - np.exp(-alpha * t)) / (1 - np.exp(-alpha))
    )

    df_gfs = pd.DataFrame({
        "Profundidade (m)": profundidade,
        "Gradiente de Pressão de Poros (lb/gal)": valores
    })

    # 🔹 AQUI está o ajuste solicitado
    df_gfs.loc[
        df_gfs["Profundidade (m)"] < st.session_state.nf,
        "Gradiente de Pressão de Poros (lb/gal)"
    ] = None

    st.session_state.df_gfs = df_gfs

    return df_gfs


def lito(ax1, df_pp, profundidades, litologias, bases):
    try:
        label = True
        line_w = 0.8
        if "s_gr" not in st.session_state:
            st.session_state.s_gr = False
        if not st.session_state.s_gr:
            curva = df_pp['Perfil Raio Gama']
        else:
            curva = df_pp['Raio Gama Suavizado']
        # Define apenas os topos e os nomes das litologias
        if not profundidades:
            prof = [0]
            lito_t = ['Fm. Permeável']
            if curva.iloc[0] >= df_pp['LBF_calc'].iloc[0]:
                aux = 'Fm. Permeável'
            else:
                aux = 'Folhelho'

            for i, line in enumerate(df_pp['Profundidade (m)']):
                if curva.iloc[i] >= df_pp['LBF_calc'].iloc[
                    i] and aux == 'Fm. Permeável':
                    prof.append(line)
                    lito_t.append('Folhelho')
                    aux = 'Folhelho'
                elif curva.iloc[i] <= df_pp['LBF_calc'].iloc[
                    i] and aux == 'Folhelho':
                    prof.append(line)
                    lito_t.append('Fm. Permeável')
                    aux = 'Fm. Permeável'

            litho_tops = [[x, y] for x, y in zip(prof, lito_t)]
            label = False
            line_w = 0

        else:
            litho_tops = [[x, y] for x, y in zip(profundidades, litologias)]
            label = True
            line_w = 0.8

        # Calcula as bases automaticamente
        litho_intervals = []
        for i, (top, lit) in enumerate(litho_tops):
            if i < len(litho_tops) - 1:
                base = litho_tops[i + 1][0]  # base = topo da próxima
            else:
                base = bases  # última formação vai até o fundo
            litho_intervals.append((top, base, lit))

        # Estilos de preenchimento
        litho_styles = {
            "Arenito": {"color": "#fff7a1", "hatch": "...", "edgecolor": "black"},
            "Fm. Permeável": {"color": "#fff7a1", "hatch": "...", "edgecolor": "black"},
            "Folhelho": {"color": "#2f4f4f", "hatch": None, "edgecolor": "black"},
            "Calcário": {"color": "#a7c7e7", "hatch": "///", "edgecolor": "#003366"},
            "Carbonato": {"color": "#cfe8f3", "hatch": "xx", "edgecolor": "#003366"},
            "Siltito": {"color": "#8b4513", "hatch": None, "edgecolor": "black"},
            "Basalto": {"color": "#2b2b2b", "hatch": None, "edgecolor": "black"},
            "Conglomerado": {"color": "#ffb347", "hatch": "oo", "edgecolor": "black"},
            "Halita": {"color": "#ffffff", "hatch": None, "edgecolor": "black"},
        }

        # Configurações do eixo da litologia
        ax1.set_xlim(0, 0.5)
        ax1.set_ylim(st.session_state.y_max_pp, st.session_state.y_min_pp)
        ax1.set_xticks([])
        ax1.tick_params(axis='y', which='both', left=False, labelleft=False)
        ax1.set_title("Litologia", fontsize=10, fontweight='bold')

        # Desenha as camadas automaticamente
        for top, base, lit in litho_intervals:
            style = litho_styles.get(lit,
                                     {"color": "gray", "hatch": None, "edgecolor": "black"})
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
                    0.25, mid, lit,
                    ha="center", va="center",
                    fontsize=9, fontweight="bold", color="black",
                    zorder=5,
                    rotation = 0
                )
                txt.set_path_effects([
                    path_effects.Stroke(linewidth=1.5, foreground='white'),
                    path_effects.Normal()
                ])
    except Exception as e:
        pass


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

    ax.set_title("Idade", fontsize=10, fontweight="bold")


def geo_page():
    st.title('Syngular Geopressure Analysis - SYGA')

    tabs = st.tabs(['Entrada de Dados', 'Coluna litológica', 'Gradiente de Sobrecarga',
                    'Gradiente de Pressão de Poros', 'Estabilidade de Poço', 'Informações Sobre o SYGA'])

    # Carregar Dados
    with tabs[0]:
        c1, c2, c3 = st.columns((1, 1, 1))
        with c1:
            container = st.container(border=True)  # Criando um container com borda
            with container:
                st.markdown('#### Informações básicas do poço')
                st.text_input('Nome do Usuário', max_chars=None, key='user_name', type="default")
                st.text_input('País', max_chars=None, key='country_name', type="default")
                st.text_input('Nome da Companhia', max_chars=None, key='company_name', type="default")
                st.text_input('Nome do Campo', max_chars=None, key='field_name', type="default")

                col1, col2 = st.columns((1, 0.5))
                with col1:
                    st.text_input('Nome do Poço', max_chars=None, key='poco', type="default")
                with col2:
                    st.write('')
                    st.write('')
                    st.checkbox('Poço Onshore', key="onshore", value=True)
                st.text_input('Datum', key='datum')
                st.text_area('Objetivo do Poço', max_chars=None, key='comments')

        with c3:
            container = st.container(border=True)
            with container:
                st.markdown("### Upload de Arquivo Excel")

                col1, col2 = st.columns(2)
                with col1:
                    # Input para escolher o intervalo de linhas (step)
                    step = st.number_input("Intervalo entre linhas para leitura", min_value=1, value=1, step=1)

                uploaded_file = st.file_uploader("***Envie o seu arquivo Excel***", type=["xlsx", "xls"])
                if uploaded_file:
                    try:
                        # Lê o arquivo Excel e mostra uma lista de abas
                        excel_data = pd.ExcelFile(uploaded_file)

                        # Selecionar a aba desejada
                        sheet_name = st.selectbox("Selecione a aba com os dados", excel_data.sheet_names)

                        # Carregar os dados da aba selecionada
                        df_full = pd.read_excel(uploaded_file, sheet_name=sheet_name)

                        # Aplicar o intervalo (step)
                        df = df_full.iloc[::step].reset_index(drop=True)

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

                        # Atualiza a segunda coluna com a contagem de linhas
                        with col2:
                            st.write("")
                            st.write("")
                            st.markdown(f"**Total de linhas carregadas:** {len(df)}")

                        # Mostrar a tabela resultante
                        st.write("Dados Importados:")
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    except Exception as e:
                        st.error(f"Erro ao processar o arquivo: {e}")

        with c2:
            with st.container(border=True):
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

                # --- INPUT MANUAL DO POÇO BASE ---
                st.markdown("### Coordenadas do Poço")
                st.number_input("Zona UTM", min_value=1, max_value=60, value=25, key='zona')
                st.radio("Hemisfério", ("Norte", "Sul"), index=1, key='hem')
                st.number_input("Coordenada Leste (Easting)", min_value=100000.0, max_value=900000.0, value=201781.78,
                                format="%.2f", key='easting')
                st.number_input("Coordenada Norte (Northing)", min_value=0.0, max_value=10000000.0, value=8932304.27,
                                format="%.2f", key='northing')
                st.number_input("Raio de busca (km)", min_value=0.1, value=0.1, format="%.2f", key='raio')

                lat_base, lon_base = utm.to_latlon(
                    st.session_state.easting,
                    st.session_state.northing,
                    st.session_state.zona,
                    northern=(st.session_state.hem == "Norte")
                )

                # --- CRIA MAPA COM POÇO BASE E CÍRCULO ---
                m = folium.Map(
                    location=[lat_base, lon_base],
                    zoom_start=13,
                    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    attr='Esri'
                )

                folium.Marker(
                    [lat_base, lon_base],
                    popup=st.session_state.poco if st.session_state.poco else "Poço",
                    icon=folium.CustomIcon('poço.png', icon_size=(30, 30))
                ).add_to(m)

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

                # --- PLOTAR POÇOS E CALCULAR DISTÂNCIAS ---
                dados_pontos = []
                for poco in pocos_filtrados:
                    e = poco['coordenadas']['easting']
                    n = poco['coordenadas']['northing']
                    lat_p, lon_p = utm.to_latlon(e, n, poco['zona_utm'], northern=(st.session_state.hem == "Norte"))
                    dist = haversine(lat_base, lon_base, lat_p, lon_p)
                    dentro_do_raio = dist <= (st.session_state.raio * 1000)

                    cor = 'green' if dentro_do_raio else 'red'
                    popup_text = f"{poco['nome']}<br>Distância: {dist / 1000:.2f} km"
                    # popup_text = f"{poco['nome']}<br>E: {e:.2f}, N: {n:.2f}<br>Distância: {dist / 1000:.2f} km"

                    folium.Marker(
                        location=[lat_p, lon_p],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color=cor, icon='map-marker')
                    ).add_to(m)

                    dados_pontos.append({
                        "Nome": poco['nome'],
                        "Easting": e,
                        "Northing": n,
                        "Distância (km)": round(dist / 1000, 2),
                        "Dentro do Raio": "Sim" if dentro_do_raio else "Não",
                        "Profundidade Medida (m)": poco.get("profundidade_medida_m", None),
                        "Profundidade Vertical (m)": poco.get("profundidade_vertical_m", None),
                        "Peso Eq. (lb/gal)": poco.get("peso_eq_lb_gal", None)
                    })

                # --- MOSTRAR MAPA ---
                st_folium(m, width=800, height=400)

                # --- TABELA DE PONTOS DENTRO DO RAIO ---
                df_resultado = pd.DataFrame(dados_pontos)
                df_dentro = df_resultado[df_resultado["Dentro do Raio"] == "Sim"].sort_values(
                    by="Distância (km)").reset_index(drop=True)
                df_dentro_exibir = df_dentro.drop(columns=["Dentro do Raio"])



    # Coluna Litológica
    with tabs[1]:
        # l1, l2, l3 = st.columns((0.2, 1, 0.1))
        pocos = {}

        st.title("Construção da coluna litológica")
        # Complete dict
        if "pocos" not in st.session_state:
            st.session_state.pocos = {}

        # Well description container
        with st.container(border=True):
            st.subheader("Descrição do poço")
            co1, co2 = st.columns(2)
            with co1:
                # Nome do poço
                nome_poco = st.text_input("Nome do poço:", key="well_name")
            with co2:
                tvd = st.number_input('TVD', min_value=0, key='prof')

            if st.button('Adicionar novo poço', type='primary'):
                if nome_poco == '':
                    st.warning('Insira o nome do poço')
                if tvd == 0:
                    st.warning('Inisira a TVD do poço')
                else:
                    st.session_state.pocos[nome_poco] = {
                        'tvd': tvd
                    }
                    st.info("💡 Lembre-se de selecionar o poço a ser editado na seção abaixo")
                    st.info("💡 Garanta que as profundidades das formação estão com o mesmo referencial (Datum)")

        profundidades = []
        formacoes = []
        litologias = []

        if "logs_imported" not in st.session_state:
            st.session_state.logs_imported = {
                "sonic_log": {
                    'imported': 'No',
                    'column': None
                },
                "density_log": {
                    'imported': 'No',
                    'column': None
                },
                "gamma_log": {
                    'imported': 'No',
                    'column': None
                },
            }

        if 'log_file' not in st.session_state:
            st.session_state.dataframe = {}

        if 'df' not in st.session_state:
            st.session_state.df = pd.DataFrame()

        if 's_log' not in st.session_state:
            st.session_state.s_log = False

        if 'd_log' not in st.session_state:
            st.session_state.d_log = False

        if 'g_log' not in st.session_state:
            st.session_state.g_log = False

        if 'uploaded' not in st.session_state:
            st.session_state.uploaded = False

        if 'wells_log' not in st.session_state:
            st.session_state.wells_log = {}

        if 'n_fm' not in st.session_state:
            st.session_state.n_fm = 5

        if st.session_state.pocos:
            # Formation description container
            with (st.container(border=True)):
                st.subheader("Descrição das camadas litológicas")
                pocos = st.session_state.pocos.keys()
                st.selectbox(
                    "Inserir Idade Geológica",
                    ['Não', 'Sim'],
                    key="idg"
                )
                if st.session_state.idg == 'Sim':
                    if 'n_id' not in st.session_state:
                        st.session_state.n_id = 1
                    col_add_2, col_rem_2 = st.columns(2)
                    with col_add_2:
                        if st.button(
                                "Adicionar Idade Geológica",
                                type="primary",
                                use_container_width=True,
                                key="b_add_idg"
                        ):
                            st.session_state.n_id += 1

                    with col_rem_2:
                        if st.button(
                                "Remover Idade Geológica",
                                type="primary",
                                use_container_width=True,
                                key="b_rem_idg"
                        ):
                            if st.session_state.n_id > 1:
                                st.session_state.n_id -= 1

                    for i in range(st.session_state.n_id):
                        with st.expander(f"### Idade Geológica {i + 1}", expanded=True):
                            st.markdown(f"### Idade Geológica - Intervalo {i + 1}")

                            # ===== INTERVALO DE PROFUNDIDADE (SÓ SE > 1 BLOCO) =====
                            colun1, colun2 = st.columns(2)
                            with colun1:
                                if i == 0:
                                    st.number_input(
                                        "Profundidade inicial",
                                        step=1.0,
                                        format="%f",
                                        min_value=0.0,
                                        key=f'prof_inicial_2_{i}'
                                    )
                                else:
                                    st.number_input(
                                        "Profundidade inicial",
                                        value=st.session_state.get(f'prof_final_2_{i - 1}', 0.0),
                                        disabled=True,
                                        key=f'prof_inicial_2_{i}'
                                    )

                            with colun2:
                                if i == st.session_state.n_id - 1:
                                    st.number_input(
                                        "Profundidade final",
                                        value=df['Profundidade'].max()+100,
                                        disabled=True,
                                        key=f'prof_final_2_{i}'
                                    )
                                else:
                                    st.number_input(
                                        "Profundidade final",
                                        step=1.0,
                                        format="%f",
                                        min_value=0.0,
                                        key=f'prof_final_2_{i}'
                                    )

                            st.text_input(
                                "Idade Geológica",
                                key=f'idg_{i}',
                            )

                    idades = []

                    for i in range(st.session_state.n_id):
                        if f'idg_{i}' in st.session_state:
                            idades.append({
                                'idg': st.session_state.get(f'idg_{i}'),
                                'prof_inicial': st.session_state.get(f'prof_inicial_2_{i}', None),
                                'prof_final': st.session_state.get(f'prof_final_2_{i}', None)
                            })

                    df_idade = (
                        pd.DataFrame(idades)
                        .rename(columns={
                            'prof_inicial': 'Topo (m)',
                            'prof_final': 'Base (m)',
                            'idg': 'Idade'
                        })
                    )

                l1, l2 = st.columns((1, 0.3))
                with l1:
                    st.selectbox('Selecione o poço', pocos, key='well_selected')
                with l2:
                    st.number_input('TVD', key='tvd',
                                    value=st.session_state.pocos[st.session_state.well_selected]['tvd'],
                                    disabled=True)

                if len(pocos) > 1:
                    x = list(pocos)
                    x.remove(st.session_state.well_selected)
                    s = st.selectbox('Copiar camadas litológicas de...', ['não copiar'] + x, key='copy')
                    if s != 'não copiar':
                        selected = s
                    else:
                        selected = st.session_state.well_selected
                else:
                    selected = st.session_state.well_selected
                try:
                    if 'formation' in st.session_state.pocos[selected]:
                        n_fm = len(st.session_state.pocos[selected]['formation'])
                    else:
                        n_fm = 5
                except (KeyError, IndexError):
                    n_fm = 5

                num_formacoes = st.number_input("Número de formações:", min_value=1, max_value=20, key='n_fm',
                                                value=n_fm)

                for i in range(st.session_state.n_fm):

                    if i == 0:
                        disabled = True
                    else:
                        disabled = False
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
                        prof = st.number_input(f"Topo da {i + 1}ª formação (TVD)", key=f"prof_{i}", disabled=disabled,
                                               value=p)
                    with col2:
                        fm = st.text_input(f"Nome da {i + 1}ª formação", key=f"fm_{i}", value=f)

                    with col3:
                        lithology = [
                            "Arenito",
                            "Folhelho",
                            "Calcário",
                            "Carbonato",
                            "Siltito",
                            "Conglomerado",
                            "Halita",
                            "Basalto"
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
                if profundidades != sorted(profundidades) and profundidades[-1] != 0:
                    st.warning('Formações superiores com profundidade maior que as inferiores!')

            # Well log container
            with st.container(border=True):
                st.subheader(f"{st.session_state.well_selected} - Perfilagens")
                log_file = st.file_uploader('Importe o perfil do poço', type=['xlsx'])
                if log_file:
                    # st.session_state.uploaded = True
                    # st.session_state.wells_log[st.session_state.well_name] = log_file
                    df_lito = pd.read_excel(log_file)
                    # if isinstance(st.session_state.wells_log[st.session_state.well_name], dict):
                    #     df_lito = pd.DataFrame(st.session_state.wells_log[st.session_state.well_name])
                    # else:
                    #     df_lito = pd.read_excel(st.session_state.wells_log[st.session_state.well_name])

                    st.session_state.wells_log[st.session_state.well_name] = df_lito.to_dict(orient='list')
                    st.dataframe(df_lito.head(), hide_index=True)
                    n_cols = np.arange(1, len(df_lito.columns) + 1, 1)
                    n_cols = list(n_cols)
                    n_cols = ["Selecione..."] + n_cols
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.session_state.logs_imported['sonic_log']['column'] = st.selectbox(
                            'Indique a coluna do perfil sônico',
                            n_cols, key='sonic_col')

                    with col2:
                        st.session_state.logs_imported['density_log']['column'] = st.selectbox(
                            'Indique a coluna do perfil de densidade',
                            n_cols, key='density_col')

                    with col3:
                        st.session_state.logs_imported['gamma_log']['column'] = st.selectbox(
                            'Indique a coluna do perfil Gamma Ray',
                            n_cols, key='gamma_col')

            # Synthetic log container
            if len(pocos) > 1:
                with st.expander('Gerar perfilagem sintética'):
                    bt = False
                    synthetic_col1, synthetic_col2, synthetic_col3 = st.columns(3)

                    well_w_logs = []
                    logs_available = []
                    for i in pocos:
                        if "perfil" in st.session_state.pocos[i]:
                            if st.session_state.pocos[i]["perfil"]:
                                well_w_logs.append(i)
                                for j in st.session_state.pocos[i]["perfil"]:
                                    if j != 'Profundidade':
                                        logs_available.append(j)

                    if not well_w_logs:
                        st.warning('Não foi encontrado nenhum poço com perfil')
                        bt = True

                    options = list(pocos)

                    with synthetic_col1:
                        source = st.selectbox('Selecione o poço de origem', ['Selecione'] + well_w_logs)

                    if source != 'Selecione':
                        options.remove(source)
                        enable = False

                    else:
                        enable = True
                        bt = True

                    with synthetic_col2:
                        s_logs = st.multiselect('Selecione o tipo de perfil', logs_available, disabled=enable)

                    with synthetic_col3:
                        destiny = st.selectbox('Selecione o poço para gerar o perfil sintético',
                                               ['Selecione'] + options, disabled=enable)

                    if st.button('Gerar perfil sintético', type='secondary', disabled=bt):
                        if source == 'Selecione':
                            st.warning('Selecione o poço de progem e poço destino')
                        elif not s_logs:
                            st.warning(f'Selecione o perfil para gerar a versão sintética')
                        elif destiny == 'Selecione':
                            st.warning('Selecione o poço destiono')
                        else:
                            synthetic_log = gerar_perfil_sintetico(st.session_state.pocos[source],
                                                                   st.session_state.pocos[destiny], s_logs)
                            st.session_state.pocos[destiny]['Syn Log'] = synthetic_log.to_dict(orient="list")
                            st.success(f'Os seguintes perfis sintético foram gerado para o '
                                       f'poço {destiny}: {", ".join(s_logs)}')
                            if 'Sonic log' in s_logs:
                                st.session_state.logs_imported['sonic_log']['imported'] = 'Yes (Synthetic)'
                            elif "Density log" in s_logs:
                                st.session_state.logs_imported['density_log']['imported'] = 'Yes (Synthetic)'
                            elif "Gamma ray log" in s_logs:
                                st.session_state.logs_imported['gamma_log']['imported'] = 'Yes (Synthetic)'
            # Save button
            c1, c2 = st.columns(2)
            with (c1):
                # Botão para salvar no dicionário
                if st.button(f"Salvar poço {st.session_state.well_selected}", use_container_width=True, type="primary",
                             key='s_bt'):
                    if log_file:
                        if st.session_state.logs_imported['sonic_log']['column'] != "Selecione...":
                            st.session_state.logs_imported['sonic_log']['imported'] = 'Yes'
                            st.session_state.df['Profundidade'] = df_lito.iloc[:, 0]
                            st.session_state.df['Sonic log'] = df_lito.iloc[:,
                                                               st.session_state.logs_imported['sonic_log'][
                                                                   'column'] - 1]
                        else:
                            st.session_state.df = st.session_state.df.drop(columns=["Sonic log"], errors="ignore")

                        if st.session_state.logs_imported['density_log']['column'] != "Selecione...":
                            st.session_state.logs_imported['density_log']['imported'] = 'Yes'
                            st.session_state.df['Profundidade'] = df_lito.iloc[:, 0]
                            st.session_state.df['Density log'] = df_lito.iloc[:,
                                                                 st.session_state.logs_imported['density_log'][
                                                                     'column'] - 1]
                        else:
                            st.session_state.df_lito = st.session_state.df.drop(columns=["Density log"],
                                                                                errors="ignore")

                        if st.session_state.logs_imported['gamma_log']['column'] != "Selecione...":
                            st.session_state.logs_imported['gamma_log']['imported'] = 'Yes'
                            st.session_state.df['Profundidade'] = df_lito.iloc[:, 0]
                            st.session_state.df['Gamma ray log'] = df_lito.iloc[:,
                                                                   st.session_state.logs_imported['gamma_log'][
                                                                       'column'] - 1]

                        else:
                            st.session_state.df = st.session_state.df.drop(columns=["Gamma ray log"], errors="ignore")

                        if st.session_state.df.empty:
                            st.warning('Selecione pelo menos um perfil')

                    if any(v > st.session_state.tvd for v in profundidades):
                        st.warning('Profundidade da formação maior que a TVD do poço')

                    elif st.session_state.well_selected is None:
                        st.warning('Selecione um poço.')

                    else:
                        if st.session_state.df.empty:
                            st.toast(f'Poço {st.session_state.well_selected} não tem perfilagem', icon="⚠️")
                        st.session_state.pocos[st.session_state.well_selected]["profundidade"] = profundidades
                        st.session_state.pocos[st.session_state.well_selected]["formation"] = formacoes
                        st.session_state.pocos[st.session_state.well_selected]["litologia"] = litologias
                        st.session_state.pocos[st.session_state.well_selected]["perfil"] = st.session_state.df.to_dict(
                            orient="list")

                        # = {
                        #     "profundidade": profundidades,
                        #     "formation": formacoes,
                        #     "litologia": litologias,
                        #     "perfil": st.session_state.df.to_dict(orient="list"),
                        # }

                        st.success(f"Poço '{st.session_state.well_selected}' importado com sucesso!")
                        # st.json(st.session_state.pocos)

            # Delete button
            with c2:
                if st.button('Remover poço', key='ren_bt', use_container_width=True, type="secondary"):
                    remove()

            try:
                wells = []
                fms = []
                litis = []
                sonics = []
                densitys = []
                gammas = []
                logs = {}
                # Verify if the well has logs
                for j, i in enumerate(st.session_state.pocos):
                    df_log = pd.DataFrame()
                    if 'perfil' in st.session_state.pocos[i]:
                        if 'Profundidade' in st.session_state.pocos[i]['perfil']:
                            df_log['profundidade'] = st.session_state.pocos[i]['perfil']['Profundidade']
                            if 'Sonic log' in st.session_state.pocos[i]['perfil']:
                                df_log['Sonic log'] = st.session_state.pocos[i]['perfil']['Sonic log']
                                st.session_state.logs_imported['sonic_log']['imported'] = 'Yes'
                                sonics.append('Yes')
                            else:
                                sonics.append('No')
                            if 'Density log' in st.session_state.pocos[i]['perfil']:
                                df_log['Density log'] = st.session_state.pocos[i]['perfil']['Density log']
                                st.session_state.logs_imported['density_log']['imported'] = 'Yes'
                                densitys.append('Yes')
                            else:
                                densitys.append('No')
                            if 'Gamma ray log' in st.session_state.pocos[i]['perfil']:
                                df_log['Gamma ray log'] = st.session_state.pocos[i]['perfil']['Gamma ray log']
                                st.session_state.logs_imported['gamma_log']['imported'] = 'Yes'
                                gammas.append('Yes')
                            else:
                                gammas.append('No')

                            logs[i] = df_log
                        else:
                            sonics.append('No')
                            densitys.append('No')
                            gammas.append('No')

                    else:
                        sonics.append('No')
                        densitys.append('No')
                        gammas.append('No')

                    wells.append(i)
                    fms.append(str(st.session_state.pocos[i]["formation"]))
                    litis.append(str(st.session_state.pocos[i]["litologia"]))

                st.markdown(f'### Poços adicionados -  Poço ativo: {st.session_state.well_selected}')
                df_lit = pd.DataFrame(
                    {
                        "Well": wells,
                        "Formation": fms,
                        "Lithology": litis,
                        "Sonic log": sonics,
                        "Density log": densitys,
                        "Gamma-Ray log": gammas,
                    }
                )

                styled_df = df_lit.style.applymap(highlight_active, subset=["Well"])

                # mostrar a tabela estilizada
                st.dataframe(styled_df, hide_index=True,
                             column_config={"Well": st.column_config.TextColumn(width=100),
                                            # "small", "medium", "large"
                                            "Lithology": st.column_config.TextColumn(width=100),
                                            # Fixed width in pixels
                                            "Formation": st.column_config.TextColumn(width=100),
                                            # Fixed width in pixels
                                            }
                             )

                # Graphic visualization
                with st.container(border=True):
                    st.markdown("### Visualização")
                    c1, c2 = st.columns((1, 1))

                    # Log visualization config
                    with c2:
                        with st.expander('Visualização da perfilagem'):
                            log1, log2 = st.columns((0.6, 1))
                            scale_options = ['Above', 'Below', 'Do not show']
                            with log1:
                                st.write('Logs available')
                            with log2:
                                st.write('Escale position')

                            exist = False
                            if st.session_state.logs_imported['sonic_log']['imported'] == 'Yes':
                                exist = True
                                with log1:
                                    st.checkbox('Sonic log', key='s_log')

                                with log2:
                                    st.markdown(
                                        """
                                        <style>
                                        div[data-testid="stHorizontalBlock"] div[role="radiogroup"] {
                                            margin-top: -18px;
                                        }
                                        </style>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    st.radio('Sonic scale position', scale_options, key='s_scale',
                                             horizontal=True, label_visibility="collapsed")

                            if st.session_state.logs_imported['density_log']['imported'] == 'Yes':
                                exist = True
                                with log1:
                                    st.checkbox('Density log', key='d_log')
                                with log2:
                                    st.radio('Density scale position', scale_options, key='d_scale',
                                             horizontal=True, label_visibility="collapsed")

                            if st.session_state.logs_imported['gamma_log']['imported'] == 'Yes':
                                exist = True
                                with log1:
                                    st.checkbox('Gamma ray log', key='g_log')
                                with log2:
                                    st.radio('Gamma ray scale position', scale_options, key='g_scale',
                                             horizontal=True, label_visibility="collapsed")

                            if exist:
                                st.number_input('Log curve opacity', min_value=0.1, max_value=1.0, value=0.6, key='op',
                                                step=0.1)

                    # Well visualization config
                    with c1:
                        with st.expander('Configurações de visualização'):
                            description = st.checkbox('Descrição das formações', key='desc_bt', value=True)
                            tvd_label = st.checkbox('Profundidades', key='labels_bt', value=False)
                            lines = st.checkbox('Linha de correlação', key='lin_bt', value=True)
                            view = st.checkbox('Exibir todos os poços', value=True, key='all')
                            if not view:
                                v_selected = st.multiselect('Selecione os poços para visualizar',
                                                            st.session_state.pocos.keys())
                            else:
                                v_selected = list(st.session_state.pocos.keys())

                    fig = plot_correlacao_com_logs(st.session_state.pocos,
                                                   [st.session_state.s_log, st.session_state.d_log,
                                                    st.session_state.g_log], description, lines, v_selected, tvd_label,
                                                   escala=(30, 300))

                    st.plotly_chart(fig)

            except KeyError as e:
                pass
                # st.write(e)

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
                        # st.checkbox('Extrapolação', key="ex", value=False)
                        # if st.session_state.onshore:
                            # st.segmented_control("***Correlação para estimativa da densidade da formação***",
                            #                      ['Perfil de Densidade', 'Gardner'],
                            #                      selection_mode="multi",
                            #                      default='Perfil de Densidade',
                            #                      key='gard',
                            #                      width="stretch")
                            # # st.radio('***Correlação para estimativa da densidade da formação***',
                            # #          ['Perfil de Densidade', 'Gardner'], key="gard", index=0,
                            # #          disabled=False)
                            # st.segmented_control("***Correlação para estimativa da densidade da formação***",
                            #                      ['Miller', 'Bourgoyne'],
                            #                      selection_mode="multi",
                            #                      default='Miller',
                            #                      key='gard_2',
                            #                      width="stretch",
                            #                      disabled=True)
                            # # st.radio('',
                            # #          ['Miller', 'Bourgoyne'], key="gard2", index=0,
                            # #          disabled=True)
                            # st.segmented_control("***Extrapolação***",
                            #                      ['Desativada', 'Ativada'],
                            #                      selection_mode="single",
                            #                      default='Desativada',
                            #                      key='ex',
                            #                      width="stretch")
                            # # st.checkbox('Extrapolação', key="ex", value=False)

                        # else:
                        #     c1, c2 = st.columns((1, 1))
                        #     st.radio('***Correlação para estimativa da densidade da formação***',
                        #              ['Perfil de Densidade', 'Gardner', 'Miller', 'Bourgoye'], key="gard", index=1,
                        #              disabled=True)
                        #     with c1:
                        #         st.checkbox('Extrapolação', key="ex", value=False)
                        #     with c2:
                        #         st.checkbox('BOP molhado', key="bop", value=False, disabled=True)

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
                            st.number_input('***Air Gap***', step=1.0, format='%f', key='rtkb', min_value=0.0)
                            if st.session_state.onshore:
                                st.number_input('***Nível Freático***', step=1.0, format='%f', key='es', min_value=0.0)
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
                                        densidade = [
                                                        st.session_state.ds if prof > st.session_state.rtkb else 0
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
                                        'Raio Gama Suavizado': gr_s
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
                    # Gráfico de Gradiente de Sobrecarga
                    container = st.container(border=True)  # Criando um container com borda
                    with container:
                        if st.button('🔄 Limpar Dados - Gradiente de Sobrecarga', use_container_width=True,
                                     type='primary'):
                            keys_to_clear = [
                                'gard', 'ex', 'bop', 'ds', 'rtkb', 'lda', 'es', 'md',
                                'nf', 'datum', 'ext_df'
                            ]
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()

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
                            st.selectbox("Profundidade", ['TVD', 'MD'], key="t_prof_s")
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
                                st.session_state.profs = st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)']
                            else:
                                st.session_state.oes = df['Gradiente de Sobrecarga (lb/gal)']
                                st.session_state.profs = df['Profundidade']
                            st.session_state.oesl = "G. de Sobrecarga"



                        else:
                            st.session_state.oes = st.session_state.ext_df['Pressão de Sobrecarga (psi)']
                            st.session_state.oesl = "P. de Sobrecarga"

                        # Ajuste da figura
                        fig, ax = plt.subplots(figsize=(8, 10))
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
                        logo_path = "logo.png"
                        if os.path.exists(logo_path):
                            logo_img = Image.open(logo_path).resize((800, 600))
                            logo_arr = np.array(logo_img)
                            fig.figimage(logo_arr, xo=370, yo=600, alpha=0.25, zorder=1)
                        st.pyplot(fig)

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
                                    <strong>Nível freático: </strong> {st.session_state.es:.2f} m <br>
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

                            # else:
                            #     image = Image.open("rig_offshore_bop.png")
                            #     st.image(image, width=200)
                            #     st.markdown(
                            #         f"""
                            #         <div style='position: absolute; top: -240px; left: 200px;
                            #                     padding: 10px; border-radius: 5px;'>
                            #             <strong>Datum: </strong> {st.session_state.datum} <br>
                            #         </div>
                            #         <div style='position: absolute; top: -170px; left: 200px;
                            #                     padding: 10px; border-radius: 5px;'>
                            #             <strong>Air gap: </strong> {st.session_state.rtkb:.2f} m <br>
                            #         </div>
                            #         <div style='position: absolute; top: -90px; left: 200px;
                            #                     padding: 10px; border-radius: 5px;'>
                            #             <strong>Lâmina D'água: </strong> {st.session_state.lda:.2f} m <br>
                            #         </div>
                            #         <div style='position: absolute; top: -43px; left: 200px;
                            #                     padding: 10px; border-radius: 5px;'>
                            #             <strong>Leito Marinho </strong>
                            #         </div>
                            #         """,
                            #         unsafe_allow_html=True
                            #     )

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
        tb = st.tabs(['Gradiente de Pressão de Poros', 'Kick Tolerance', 'Tabela de Dados Calculados'])
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
                            st.segmented_control("***Mecanismo Gerador de Pressão de Poros***", ['Subcompactação','Transferência Lateral'],
                                                 selection_mode="single",default='Subcompactação', key='mgpp', width="stretch")
                            if st.session_state.onshore:
                                profundidade = st.session_state.ext_df['Profundidade em relação a mesa rotativa (m)']
                                densidade = st.session_state.ext_df['Densidade (g/cm³)']
                                sonico = st.session_state.ext_df['Sônico (µs/pé)']
                                raio_gama = st.session_state.ext_df['Perfil Raio Gama']
                                raio_gama_s = st.session_state.ext_df['Raio Gama Suavizado']
                            else:
                                profundidade = df['Profundidade']
                                densidade = df['Perfil de densidade']
                                sonico = df['Perfil sônico']
                                raio_gama = df['Perfil Raio Gama']
                                raio_gama_s = df['Raio Gama Suavizado']

                            # Criação do DataFrame principal
                            df_pp = pd.DataFrame({
                                'Profundidade (m)': profundidade,
                                'Perfil de densidade (g/cm³)': densidade,
                                'Perfil sônico (µs/pé)': sonico,
                                'Perfil Raio Gama': raio_gama,
                                'Raio Gama Suavizado': raio_gama_s
                            })

                            try:
                                if st.session_state.onshore:
                                    # normal(st.session_state.anormal, st.session_state.gn)
                                    normal(df)

                                m = (np.log10(st.session_state.s2 / st.session_state.s1)) / (
                                        st.session_state.pp2 - st.session_state.pp1)
                                rn = []
                                if not st.session_state.suav_s:
                                    s = df_pp['Perfil sônico (µs/pé)']
                                else:
                                    s = df_pp['Perfil sônico suavizado (µs/pé)']
                                for i in range(len(df_pp)):
                                    if pd.isnull(s.iloc[i]) and not pd.isnull(
                                            df_pp['Perfil de densidade (g/cm³)'].iloc[i]):
                                        # rn.append(None)
                                        rn.append(st.session_state.s1 * 10 ** (m * (
                                                df_pp['Profundidade (m)'].iloc[i] - st.session_state.pp1)))
                                    elif not pd.isnull(s.iloc[i]) and s.iloc[i] != 0:
                                        rn.append(st.session_state.s1 * 10 ** (m * (
                                                df_pp['Profundidade (m)'].iloc[i] - st.session_state.pp1)))
                                    elif pd.isnull(s.iloc[i]) and pd.isnull(
                                            df_pp['Perfil de densidade (g/cm³)'].iloc[i]):
                                        rn.append(None)
                                df_pp.insert(4, 'Perfil sônico (µs/pé) Reta Normal', pd.Series(rn))
                            except Exception as e:
                                pass

                            # Aplica a suavização condicionalmente
                            if st.session_state.suav_s:
                                perfil_sonico_suav = suavizar(profundidade, sonico)
                                df_pp.insert(3, 'Perfil sônico suavizado (µs/pé)', perfil_sonico_suav)

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

                                    st.segmented_control("***Pressão***",
                                                         ['Base do arenito = Topo do Folhelho',
                                                          'Topo do arenito = Base do Folhelho'],
                                                         selection_mode="multi",
                                                         default='Base do arenito = Topo do Folhelho',
                                                         key='o_boyance',
                                                         width="stretch")

                                    for i in range(st.session_state.n_boyance):
                                        with st.expander(f"### Boyance - Intervalo {i + 1}", expanded=True):
                                            st.markdown(f"### Boyance - Intervalo {i + 1}")

                                            # ===== INTERVALO DE PROFUNDIDADE (SÓ SE > 1 BLOCO) =====
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
                                                            value=df_pp['Profundidade (m)'].max()+100,
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

                                            # Inicializa o FPR apenas uma vez
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
                                                'prof_inicial': st.session_state.get(f'prof_ini_{i}', None),
                                                'prof_final': st.session_state.get(f'prof_fim_{i}', None)
                                            })

                            if 'n_trending' not in st.session_state:
                                st.session_state.n_trending = 1

                            col_add, col_rem = st.columns(2)

                            with col_add:
                                if st.button(
                                        "Adicionar Trending/LBF",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_add_trending"
                                ):
                                    st.session_state.n_trending += 1

                            with col_rem:
                                if st.button(
                                        "Remover Trending/LBF",
                                        type="primary",
                                        use_container_width=True,
                                        key="b_rem_trending"
                                ):
                                    if st.session_state.n_trending > 1:
                                        idx = st.session_state.n_trending - 1

                                        keys_to_remove = [
                                            f'pp1_{idx}', f'pp2_{idx}',
                                            f's1_{idx}', f's2_{idx}',
                                            f'lbf_{idx}', f'inclbf_{idx}',
                                            f'prof_ini_{idx}', f'prof_fim_{idx}'
                                        ]

                                        for k in keys_to_remove:
                                            if k in st.session_state:
                                                del st.session_state[k]

                                        st.session_state.n_trending -= 1
                            with st.form("p_poros", border=False):
                                if st.session_state.mgpp == 'Subcompactação':
                                    with st.expander("Informações Gerais", expanded=True):
                                        st.number_input('Expoente de Eaton', step=1.0, format='%f', key='expoente')
                                        st.number_input('Profundidade de início da zona anormal', step=100.0,format='%f', key='anormal')
                                        st.number_input('Gradiente Normal', step=1.0, format='%f', key='gn')

                                    for i in range(st.session_state.n_trending):
                                        with st.expander(f"### Trending / LBF {i + 1}", expanded=True):
                                            # ===== INTERVALO DE PROFUNDIDADE (SÓ SE > 1 BLOCO) =====
                                            if st.session_state.n_trending > 1:
                                                colun1, colun2 = st.columns(2)

                                                with colun1:
                                                    st.number_input(
                                                        "Profundidade inicial",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'prof_ini_{i}'
                                                    )

                                                with colun2:
                                                    st.number_input(
                                                        "Profundidade final",
                                                        step=1.0,
                                                        format="%f",
                                                        min_value=0.0,
                                                        key=f'prof_fim_{i}'
                                                    )

                                            # -------- TRENDING --------
                                            with st.expander("Trending", expanded=True):
                                                col1, col2 = st.columns((1, 1))

                                                with col1:
                                                    st.number_input(
                                                        'Profundidade 1',
                                                        step=1.0,
                                                        format='%f',
                                                        min_value=0.0,
                                                        key=f'pp1_{i}'
                                                    )
                                                    st.number_input(
                                                        'Profundidade 2',
                                                        step=1.0,
                                                        format='%f',
                                                        min_value=0.0,
                                                        key=f'pp2_{i}'
                                                    )

                                                with col2:
                                                    st.number_input(
                                                        'Leitura 1 do Sônico',
                                                        step=1.0,
                                                        format='%f',
                                                        min_value=0.0,
                                                        key=f's1_{i}'
                                                    )
                                                    st.number_input(
                                                        'Leitura 2 do Sônico',
                                                        step=1.0,
                                                        format='%f',
                                                        min_value=0.0,
                                                        key=f's2_{i}'
                                                    )

                                            # -------- LINHA BASE DE FOLHELHOS --------
                                            with st.expander("Linha Base de Folhelhos", expanded=True):
                                                st.number_input(
                                                    'Ponto inicial da LBF',
                                                    step=10.0,
                                                    format='%f',
                                                    min_value=1.0,
                                                    value=180.0,
                                                    key=f'lbf_{i}',
                                                    help=(
                                                        "**Linha Base de Folhelhos (LBF)** 📉\n\n"
                                                        "- Representa o comportamento esperado dos **folhelhos normalmente compactados**.\n"
                                                        "- Traçada no registro **raio gama (GAPI) × profundidade (m)**."
                                                    )
                                                )

                                                st.number_input(
                                                    'Inclinação da LBF',
                                                    step=0.1,
                                                    format='%f',
                                                    value=0.0,
                                                    key=f'inclbf_{i}'
                                                )

                                            trendings = []

                                            for i in range(st.session_state.n_trending):
                                                if f'pp1_{i}' in st.session_state:
                                                    trendings.append({
                                                        'pp1': st.session_state.get(f'pp1_{i}'),
                                                        'pp2': st.session_state.get(f'pp2_{i}'),
                                                        's1': st.session_state.get(f's1_{i}'),
                                                        's2': st.session_state.get(f's2_{i}'),
                                                        'lbf': st.session_state.get(f'lbf_{i}'),
                                                        'inclbf': st.session_state.get(f'inclbf_{i}'),
                                                        'prof_ini': st.session_state.get(f'prof_ini_{i}', None),
                                                        'prof_fim': st.session_state.get(f'prof_fim_{i}', None)
                                                    })

                                    # Garante que as colunas existam, mesmo sem trending válido
                                    if 'Perfil sônico (µs/pé) Reta Normal' not in df_pp.columns:
                                        df_pp['Perfil sônico (µs/pé) Reta Normal'] = np.nan

                                    if 'LBF_calc' not in df_pp.columns:
                                        df_pp['LBF_calc'] = np.nan

                                    for tr in trendings:
                                        try:
                                            prof = df_pp['Profundidade (m)']

                                            # -------- VALIDAÇÃO DOS PARÂMETROS --------
                                            if (
                                                    tr['s1'] in (None, 0) or
                                                    tr['s2'] in (None, 0) or
                                                    tr['pp1'] is None or
                                                    tr['pp2'] is None or
                                                    tr['s2'] == tr['s1'] or
                                                    tr['pp2'] == tr['pp1']
                                            ):
                                                continue

                                            # ---------- TRENDING ----------
                                            if st.session_state.onshore:
                                                # Caso ONshore (modelo logarítmico)
                                                m = (np.log10(tr['s2'] / tr['s1'])) / (tr['pp2'] - tr['pp1'])
                                                s_normal = tr['s1'] * 10 ** (m * (prof - tr['pp1']))
                                            else:
                                                # Caso OFFshore (modelo linear invertido)
                                                m = (tr['pp2'] - tr['pp1']) / (tr['s2'] - tr['s1'])
                                                b = -(m * tr['s2']) + tr['pp2']
                                                s_normal = (prof - b) / m

                                            # ---------- INTERVALO DO TRENDING ----------
                                            if tr['prof_ini'] is not None and tr['prof_fim'] is not None:
                                                mask = (prof >= tr['prof_ini']) & (prof <= tr['prof_fim'])
                                            else:
                                                mask = np.ones(len(df_pp), dtype=bool)

                                            # ---------- NOVA VERIFICAÇÃO (OFFSHORE) ----------
                                            if not st.session_state.onshore:
                                                mask = mask & (prof > st.session_state.lda)

                                            df_pp.loc[mask, 'Perfil sônico (µs/pé) Reta Normal'] = s_normal[mask]

                                            # ---------- LBF ----------
                                            prof_ref = prof.min()
                                            lbf_line = tr['inclbf'] * (prof - prof_ref) + tr['lbf']
                                            df_pp.loc[mask, 'LBF_calc'] = lbf_line[mask]

                                        except Exception:
                                            pass

                                    if st.session_state.onshore:
                                        df_pp['Gradiente de Sobrecarga (lb/gal)'] = st.session_state.ext_df[
                                            'Gradiente de Sobrecarga (lb/gal)']
                                    else:
                                        df_pp['Gradiente de Sobrecarga (lb/gal)'] = df[
                                            'Gradiente de Sobrecarga (lb/gal)']

                                    gp = []
                                    prof_min = df["Profundidade"].min()
                                    base_grad = st.session_state.gn
                                    if not st.session_state.suav_s:
                                        s = df_pp['Perfil sônico (µs/pé)']
                                    else:
                                        s = df_pp['Perfil sônico suavizado (µs/pé)']
                                    for i in range(len(df_pp)):
                                        perfil_sonico = s.iloc[i]
                                        if pd.isna(perfil_sonico):
                                            perfil_sonico = df_pp['Perfil sônico (µs/pé) Reta Normal'].iloc[i]
                                        perfil = perfil_sonico
                                        if st.session_state.onshore:
                                            x = (
                                                    df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[i]
                                                    - (
                                                            (df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[
                                                                 i] - base_grad)
                                                            * ((perfil /
                                                                df_pp['Perfil sônico (µs/pé) Reta Normal'].iloc[
                                                                    i]) ** (-st.session_state.expoente))
                                                    )
                                            )
                                            profundidade_atual = df_pp['Profundidade (m)'].iloc[i]
                                            if profundidade_atual < prof_min:
                                                if profundidade_atual < st.session_state.anormal:
                                                    idx_mais_proximo = (
                                                        (st.session_state.df_gfs[
                                                             'Profundidade (m)'] - profundidade_atual)
                                                        .abs()
                                                        .idxmin()
                                                    )
                                                    valor_gradiente = st.session_state.df_gfs.loc[
                                                        idx_mais_proximo, 'Gradiente de Pressão de Poros (lb/gal)'
                                                    ]
                                                    gp.append(valor_gradiente)
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
                                                        valor_gradiente = st.session_state.gn
                                                        gp.append(valor_gradiente)

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
                                                            (df_pp['Gradiente de Sobrecarga (lb/gal)'].iloc[
                                                                 i] - st.session_state.gn)
                                                            * (
                                                                    (perfil / df_pp[
                                                                        'Perfil sônico (µs/pé) Reta Normal'].iloc[
                                                                        i])
                                                                    ** (-st.session_state.expoente)
                                                            )
                                                    )
                                            )

                                            if df_pp['Profundidade (m)'].iloc[i] <= st.session_state.lda:
                                                gp.append(None)
                                            elif df_pp['Profundidade (m)'].iloc[i] < st.session_state.anormal or x < st.session_state.gn:
                                                gp.append(st.session_state.gn)
                                            else:
                                                gp.append(x)

                                    # Resultado final
                                    df_pp['Gradiente de Pressão de Poros (lb/gal)'] = gp

                                    df_pp['Gradiente de Pressão de Poros Médio (lb/gal)'] = (
                                        df_pp['Gradiente de Pressão de Poros (lb/gal)']
                                        .rolling(window=20, min_periods=1)
                                        .mean()
                                    )

                                    # Ajusta valores se ultrapassarem variação máxima fpp
                                    for i in range(1, len(df_pp)):
                                        if df_pp.loc[i, 'Profundidade (m)'] >= st.session_state.anormal:
                                            anterior = df_pp.loc[
                                                i - 1, 'Gradiente de Pressão de Poros Médio (lb/gal)']
                                            atual = df_pp.loc[i, 'Gradiente de Pressão de Poros Médio (lb/gal)']
                                            if atual > anterior + st.session_state.fpp:
                                                df_pp.loc[
                                                    i, 'Gradiente de Pressão de Poros Médio (lb/gal)'] = anterior + st.session_state.fpp

                                    try:
                                        if st.session_state.spp:
                                            df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)'] = suavizar_2(df_pp
                                                                       [
                                                                           'Profundidade (m)'],
                                                                       df_pp[
                                                                           'Gradiente de Pressão de Poros Médio (lb/gal)'],
                                                                       df_pp[
                                                                           'Gradiente de Pressão de Poros Médio (lb/gal)'])
                                    except Exception as e:
                                        pass

                                    df_pp.insert(
                                        loc=9,
                                        column='Pressão de Poros (psi)',
                                        value=0.1704 * df_pp['Gradiente de Pressão de Poros Médio (lb/gal)'] *
                                              df_pp['Profundidade (m)']
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

                                                # Validações básicas
                                                if fpr is None:
                                                    continue
                                                if prof_ini is None or prof_fim is None:
                                                    continue

                                                # Máscara de profundidade
                                                mask = (
                                                        (df_pp["Profundidade (m)"] >= prof_ini) &
                                                        (df_pp["Profundidade (m)"] <= prof_fim)
                                                )

                                                df_pp.loc[mask, "FPR_efetivo"] = fpr

                                        # Preenche eventuais lacunas
                                        df_pp["FPR_efetivo"] = (
                                            df_pp["FPR_efetivo"]
                                            .ffill()
                                            .fillna(st.session_state.get("fpr_0"))
                                        )

                                        incremento = (
                                                0.1704
                                                * df_pp["FPR_efetivo"]
                                                * (df_pp["Profundidade (m)"] - df_pp["Profundidade (m)"].shift(1))
                                        )
                                        if not st.session_state.s_gr:
                                            x = df_pp["Perfil Raio Gama"]
                                        else:
                                            x = df_pp["Raio Gama Suavizado"]
                                        df_pp.insert(loc=12,
                                                     column='Formação',
                                                     value=np.where(x < df_pp["LBF_calc"],
                                                                    "Formação Permeável",
                                                                    "Formação Impermeável")
                                                     )

                                        topo_permeavel = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(1) != "Formação Permeável")
                                        )

                                        # Insere a coluna na posição correta
                                        df_pp.insert(loc=13, column='Pressão Boyance (TA = BF)', value=np.nan)
                                        # Identifica o topo das camadas permeáveis
                                        topo_permeavel = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(1) != "Formação Permeável")
                                        )

                                        if not st.session_state.spp:
                                            y = df_pp['Gradiente de Pressão de Poros Médio (lb/gal)']
                                        else:
                                            y = df_pp['Gradiente de Pressão de Poros Suavizado (lb/gal)']

                                        # Valor inicial no topo da camada
                                        df_pp.loc[topo_permeavel, 'Pressão Boyance (TA = BF)'] = (
                                                y.shift(1)
                                                * 0.1704
                                                * df_pp["Profundidade (m)"]
                                        )

                                        # Cria ID de camada permeável
                                        id_camada = topo_permeavel.cumsum()

                                        # Soma acumulada linha a linha dentro de cada camada permeável
                                        mask_perm = df_pp["Formação"] == "Formação Permeável"

                                        df_pp.loc[mask_perm, 'Pressão Boyance (TA = BF)'] = (
                                            df_pp.loc[mask_perm]
                                            .groupby(id_camada)
                                            .apply(
                                                lambda g: g['Pressão Boyance (TA = BF)'].iloc[0] + incremento.loc[
                                                    g.index].cumsum()
                                            )
                                            .values
                                        )

                                        # Calcula a boyance normalmente
                                        boyance_calc = np.where(
                                            df_pp["Formação"] == "Formação Impermeável",
                                            y,
                                            df_pp["Pressão Boyance (TA = BF)"] / (0.1704 * df_pp["Profundidade (m)"])
                                        )

                                        # Converte para Series para facilitar o tratamento
                                        boyance_calc = pd.Series(boyance_calc, index=df_pp.index)

                                        # Onde for NaN ou None, substitui por y
                                        boyance_calc = boyance_calc.fillna(y)

                                        # Insere no DataFrame
                                        df_pp.insert(
                                            loc=14,
                                            column='Boyance (lb/gal) (TA = BF)',
                                            value=boyance_calc
                                        )

                                        df_pp.insert(loc=15, column='Pressão Boyance (BA = TF)', value=np.nan)

                                        # Identifica a BASE das camadas permeáveis
                                        base_permeavel = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(-1) != "Formação Permeável")
                                        )

                                        # Valor inicial na base (igual ao valor da formação impermeável abaixo)
                                        idx = df_pp.index[base_permeavel]

                                        df_pp.loc[idx, 'Pressão Boyance (BA = TF)'] = np.where(
                                            df_pp.loc[idx, "Formação"].shift(-1) == "Formação Impermeável",
                                            df_pp.loc[idx, 'Pressão de Poros (psi)'].shift(-1),
                                            df_pp.loc[idx, 'Pressão de Poros (psi)']
                                        )

                                        # Cria ID de camada permeável (de cima para baixo)
                                        id_camada = (
                                                (df_pp["Formação"] == "Formação Permeável") &
                                                (df_pp["Formação"].shift(1) != "Formação Permeável")
                                        ).cumsum()

                                        # Calcula a pressão de baixo para cima dentro de cada camada permeável
                                        mask_perm = df_pp["Formação"] == "Formação Permeável"

                                        df_pp.loc[mask_perm, 'Pressão Boyance (BA = TF)'] = (
                                            df_pp.loc[mask_perm]
                                            .groupby(id_camada)
                                            .apply(
                                                lambda g: (
                                                        g['Pressão Boyance (BA = TF)']
                                                        .iloc[-1]
                                                        - incremento.loc[g.index][::-1].cumsum()[::-1]
                                                )
                                            )
                                            .values
                                        )

                                        # Garante ordenação por profundidade
                                        df_pp = df_pp.sort_values("Profundidade (m)").reset_index(drop=True)

                                        # Flag da formação impermeável
                                        impermeavel = df_pp["Formação"] == "Formação Impermeável"

                                        # Verifica se existe impermeável acima (excluindo a linha atual)
                                        impermeavel_acima = impermeavel.shift(fill_value=False).cumsum() > 0

                                        df_pp.insert(
                                            loc=16,
                                            column='Boyance (lb/gal) (BA = TF)',
                                            value=np.where(
                                                (~impermeavel) & (impermeavel_acima),
                                                df_pp["Pressão Boyance (BA = TF)"] / (
                                                            0.1704 * df_pp["Profundidade (m)"]),
                                                y
                                            )
                                        )


                                else:
                                    st.warning('Funcionalidade ainda não disponível', icon="⚠️")

                                st.form_submit_button("Calcular Gradiente de Pessão de Poros", use_container_width=True,type='primary')

                    # GRÁFICO DO GRADIENTE DE PRESSÃO DE POROS
                    with coluna3:
                        with st.container(border=True):
                            if "idg" not in st.session_state:
                                st.session_state.idg = 'Não'

                            fig = plt.figure(figsize=(8, 10))

                            if st.session_state.idg == 'Sim':
                                # === COM coluna de idade ===
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

                                idade_formacao(ax_idade, df_idade, df_pp['Profundidade (m)'].max()+100)

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

                                ax1 = fig.add_subplot(gs[0])
                                ax_gap = fig.add_subplot(gs[1])
                                ax_gap.axis('off')

                                ax = fig.add_subplot(gs[2], sharey=ax1)

                                plt.setp(ax.get_yticklabels(), visible=False)

                            if st.button("Inserir Informações de Fluido e Testes de Formação",
                                         type="primary",
                                         use_container_width=True):
                                rft(ax)
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
                                colu1, colu2 = st.columns(2)
                                with colu1:
                                    st.checkbox('Suavizar Pressão de Poros', key="spp", value=False)
                                    st.checkbox('Suavizar Sônico', key="suav_s", value=False)
                                with colu2:
                                    st.checkbox('Sobrecarga', key="grafpp", value=False)
                                    st.checkbox('Suavizar Raio Gama', key="s_gr", value=False)
                                    st.session_state.ss = True

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

                            if "dados_rft" in st.session_state and not st.session_state["dados_rft"].empty:
                                df_rft = st.session_state["dados_rft"]

                                # Plota Testes RFT se houver valores preenchidos
                                if "Teste RFT (lb/gal)" in df_rft.columns and df_rft[
                                    "Teste RFT (lb/gal)"].notna().any():
                                    ax.scatter(
                                        df_rft["Teste RFT (lb/gal)"],
                                        df_rft["Profundidade (m)"],
                                        color='green',
                                        marker='o',
                                        s=80,
                                        label="Teste de Formação (RFT)",
                                        edgecolors='black',
                                        zorder=5
                                    )

                                # Plota Pesos de Fluido se houver valores preenchidos
                                if "Peso do Fluido (lb/gal)" in df_rft.columns and df_rft[
                                    "Peso do Fluido (lb/gal)"].notna().any():
                                    if st.session_state.ogp == "Gradiente (lb/gal)":
                                        ax.plot(
                                            df_rft["Peso do Fluido (lb/gal)"],
                                            df_rft["Profundidade (m)"],
                                            color='mediumvioletred',
                                            linestyle='-',
                                            linewidth=2,
                                            label="Peso do Fluido",
                                            zorder=5
                                        )
                                    else:
                                        ax.plot(
                                            df_rft["Peso do Fluido (lb/gal)"] * 0.1704 * df_rft[
                                                "Profundidade (m)"],
                                            df_rft["Profundidade (m)"],
                                            color='mediumvioletred',
                                            linestyle='-',
                                            linewidth=2,
                                            label="Peso do Fluido",
                                            zorder=5
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
                                ax.set_ylabel('Profundidade (m)', fontsize=12)
                            else:
                                ax.set_title('Pressão de Poros (psi)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Pressão (psi)', fontsize=12)
                                ax.set_ylabel('Profundidade (m)', fontsize=12)
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
                            logo_path = "logo.png"
                            if os.path.exists(logo_path):
                                logo_img = Image.open(logo_path).resize((800, 600))
                                logo_arr = np.array(logo_img)
                                fig.figimage(logo_arr, xo=440, yo=500, alpha=0.25, zorder=1)

                            # plt.subplots_adjust(wspace=0.45)
                            # Exibe o gráfico no Streamlit
                            st.pyplot(fig)

                    # TRENDING E LBF
                    with coluna2:
                        with st.container(border=True):
                            st.markdown("### Trending e Linha Base de Folhelhos")
                            st.segmented_control("Gráficos", ['LBF', 'Trending'],selection_mode="single",default='LBF',
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

                                    idade_formacao(ax_idade, df_idade, st.session_state.y_max_pp)

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
                                            mask_base = prof.notna()  # todas as profundidades válidas
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
                                ax.set_ylabel('Profundidade (m)', fontsize=12)
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
                                logo_path = "logo.png"
                                if os.path.exists(logo_path):
                                    logo_img = Image.open(logo_path).resize((800, 600))
                                    logo_arr = np.array(logo_img)
                                    st.session_state.fig1.figimage(logo_arr, xo=440, yo=500, alpha=0.25, zorder=1)

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

                                    idade_formacao(ax_idade, df_idade, st.session_state.y_max_pp)

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

                                for idx, tr in enumerate(trendings):

                                    try:
                                        color = TRENDING_COLORS[idx % len(TRENDING_COLORS)]

                                        prof = df_pp['Profundidade (m)']

                                        prof_ref = (
                                            tr['prof_ini']
                                            if tr['prof_ini'] is not None
                                            else prof.min()
                                        )

                                        # 🔹 LBF ANCORADA NO PONTO INICIAL
                                        lbf_line = tr['inclbf'] * (prof - prof_ref) + tr['lbf']

                                        if st.session_state.onshore:
                                            mask_base = prof.notna()
                                        else:
                                            mask_base = prof > st.session_state.lda

                                        if tr['prof_ini'] is not None and tr['prof_fim'] is not None:
                                            mask_tr = (prof >= tr['prof_ini']) & (prof <= tr['prof_fim'])
                                            mask_final = mask_base & mask_tr
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
                                        ax.plot(df_pp['Raio Gama Suavizado'][x:], df_pp['Profundidade (m)'][x:], color='blue',
                                                linestyle='-', linewidth=2, label="Perfil Raio Gama")
                                ax.set_title('GR x Profundidade (m)', fontsize=14, fontweight='bold')
                                ax.set_xlabel('Perfil Raio Gama (GAPI)', fontsize=12)
                                ax.set_ylabel('Profundidade (m)', fontsize=12)


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
                                logo_path = "logo.png"
                                if os.path.exists(logo_path):
                                    logo_img = Image.open(logo_path).resize((800, 600))
                                    logo_arr = np.array(logo_img)
                                    st.session_state.fig2.figimage(logo_arr, xo=440, yo=500, alpha=0.25, zorder=1)
                                plt.subplots_adjust(wspace=0.3)

                                st.pyplot(st.session_state.fig2)

                else:
                    st.error('Preencha corretamente a aba "Gradiente de Sobrecarga"', icon="🚨")
            else:
                st.error('Por favor, insira um documento!', icon="🚨")

        # Ver Dataframes
        with tb[2]:
            if uploaded_file:
                try:
                    st.dataframe(df_pp, use_container_width=True, hide_index=True)
                except Exception as e:
                    pass

    # Estabilidade de Poço
    with (tabs[4]):
        x = 0
        if x == 0:
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

                                        # Cálculo com tratamento de exceção
                                        try:
                                            b, log_a = np.polyfit(gf['K'], np.log(gf['Profundidade (m)']), 1)
                                            a = np.exp(log_a)
                                        except Exception as e:
                                            b, a = 1, 1
                                        st.session_state['a'] = a
                                        st.session_state['b'] = b

                                    with st.expander('Zonas de perda', expanded=True):
                                        with st.form('loss_form', border=False):
                                            st.markdown("### Inserir Zonas de Perda de Circulação")
                                            z = pd.DataFrame({
                                                'Profundidade da zona de perda (m)': [0.0],
                                                'Peso do fluido (lb/gal)': [0.0]
                                            })
                                            if 'zonas' not in st.session_state:
                                                st.session_state.zonas = []
                                            cols_to_check = ["Profundidade da zona de perda (m)", "Peso do fluido (lb/gal)"]
                                            st.session_state.edited_z = st.data_editor(z, hide_index=True,
                                                                                       num_rows='dynamic',
                                                                                       key='edited')
                                            if st.form_submit_button('Inserir Zonas de Perda', use_container_width=True,
                                                                     type='primary'):
                                                st.session_state.zonas = []
                                                if (st.session_state.edited_z[cols_to_check] != 0).all(axis=1).any():
                                                    for i, value in enumerate(
                                                            st.session_state.edited_z["Profundidade da zona de perda (m)"]):
                                                        st.session_state.zonas.append([value, st.session_state.edited_z[
                                                            "Peso do fluido (lb/gal)"][i]])

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

                            with colu3:
                                with st.container(border=True):
                                    fig1 = plt.figure(figsize=(8, 9.95))

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

                                        idade_formacao(ax_idade, df_idade, st.session_state.y_max_pp)

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
                                        st.selectbox('Profundidade', ['MD', 'TVD'], key="t_prof_f")
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

                                            if "dados_rft" in st.session_state and not st.session_state["dados_rft"].empty:
                                                df_rft = st.session_state["dados_rft"]

                                                # Plota Testes RFT se houver valores preenchidos
                                                if "Teste RFT (lb/gal)" in df_rft.columns and df_rft[
                                                    "Teste RFT (lb/gal)"].notna().any():
                                                    ax.scatter(
                                                        df_rft["Teste RFT (lb/gal)"],
                                                        df_rft["Profundidade (m)"],
                                                        color='green',
                                                        marker='o',
                                                        s=80,
                                                        label="Teste de Formação (RFT)",
                                                        edgecolors='black',
                                                        zorder=5
                                                    )

                                                # Plota Pesos de Fluido se houver valores preenchidos
                                                if "Peso do Fluido (lb/gal)" in df_rft.columns and df_rft[
                                                    "Peso do Fluido (lb/gal)"].notna().any():
                                                    if st.session_state.ogf == "Gradiente (lb/gal)":
                                                        ax.plot(
                                                            df_rft["Peso do Fluido (lb/gal)"],
                                                            df_rft["Profundidade (m)"],
                                                            color='mediumvioletred',
                                                            linestyle='-',
                                                            linewidth=2,
                                                            label="Peso do Fluido",
                                                            zorder=5
                                                        )
                                                    else:
                                                        ax.plot(
                                                            df_rft["Peso do Fluido (lb/gal)"] * 0.1704 * df_rft[
                                                                "Profundidade (m)"],
                                                            df_rft["Profundidade (m)"],
                                                            color='mediumvioletred',
                                                            linestyle='-',
                                                            linewidth=2,
                                                            label="Peso do Fluido",
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

                                        if 'edited_z' in st.session_state and not st.session_state.edited_z.empty:
                                            # pega os valores das colunas
                                            x_vals = st.session_state.edited_z["Peso do fluido (lb/gal)"]
                                            y_vals = st.session_state.edited_z["Profundidade da zona de perda (m)"]

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
                                    ax.set_ylabel('Profundidade (m)', fontsize=12)
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
                                    logo_path = "logo.png"
                                    if os.path.exists(logo_path):
                                        logo_img = Image.open(logo_path).resize((800, 600))
                                        logo_arr = np.array(logo_img)
                                        fig1.figimage(logo_arr, xo=530, yo=500, alpha=0.25, zorder=1)
                                    plt.subplots_adjust(wspace=0.3)

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

                                        idade_formacao(ax_idade, df_idade, st.session_state.y_max_pp)

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
                                    depth_trend = a * np.exp(b * k_values)

                                    ax.plot(k_values, depth_trend, color='red', linestyle='--', linewidth=2,
                                            label='Linha de Tendência Exponencial de K')

                                    ax.set_title('K x Profundidade', fontsize=14, fontweight='bold')
                                    ax.set_xlabel('K', fontsize=12)
                                    ax.set_ylabel('Profundidade (m)', fontsize=12)
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
                                    logo_path = "logo.png"
                                    if os.path.exists(logo_path):
                                        logo_img = Image.open(logo_path).resize((800, 600))
                                        logo_arr = np.array(logo_img)
                                        fig2.figimage(logo_arr, xo=530, yo=500, alpha=0.25, zorder=1)
                                    plt.subplots_adjust(wspace=0.3)

                                    st.pyplot(fig2)

                        # except Exception as e:
                        else:
                            st.error('Preencha corretamente a aba "Gradiente de Pressão de Poros"', icon="🚨")

                    else:
                        st.error('Por favor, insira um documento!', icon="🚨")

                # Ver Dataframes
                with tb[1]:
                    if uploaded_file:
                        adriel = True
                        if adriel == True:
                            if all(value != 0 for value in [st.session_state.rtkb]):
                                if all(value != 0 for value in
                                       [st.session_state.gn, st.session_state.anormal, st.session_state.expoente]):
                                    st.dataframe(df_f, use_container_width=True, hide_index=True)

            # Tensões em Volta do Poço
            with tabss[0]:
                if uploaded_file:
                    if st.session_state.rtkb != 0:
                        if all(value != 0 for value in [st.session_state.rtkb]) and all(
                                value != 0 for value in [st.session_state.gn,
                                                         st.session_state.anormal, st.session_state.expoente]):
                        # try:
                            tb = st.tabs(
                                ['Critério de Falha - Mohr Coulomb', 'Visualização 3D das Tensões', 'Configurações',
                                 'Dados Calculados'])
                            if st.session_state.onshore:
                                profundidade = df_pp['Profundidade (m)']
                                md = df['MD']
                                densidade = df_pp['Perfil de densidade (g/cm³)']
                                sonico = df_pp['Perfil sônico (µs/pé)']
                                grad_sobrecarga = df_pp['Gradiente de Sobrecarga (lb/gal)']
                            else:
                                profundidade = df['Profundidade']
                                md = df['MD']
                                densidade = df['Perfil de densidade']
                                sonico = df['Perfil sônico']
                                grad_sobrecarga = df['Gradiente de Sobrecarga (lb/gal)']

                            if "suavi_s" not in st.session_state:
                                st.session_state.suavi_s = False
                            if st.session_state.suavi_s:
                                sonico = suavizar(profundidade, sonico)

                            df_tvp = pd.DataFrame({
                                'Profundidade (m)': profundidade,
                                'MD': md,
                                'Perfil de densidade (g/cm³)': densidade,
                                'Perfil sônico (µs/pé)': sonico,
                                'Gradiente de Sobrecarga (lb/gal)': grad_sobrecarga
                            })

                            # ABA DE CONFIGURAÇÕES
                            with tb[2]:
                                # if uploaded_file:
                                c1, c2 = st.columns(2)
                                with c1:
                                    with st.container(border=True):
                                        st.markdown('### Configurações dos Cálculos')
                                        st.button("Inserir direções das tensões in situ", key="tis",
                                                  use_container_width=True, type='primary', on_click=tensoes)
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
                                                direction="backward"  # pega o valor anterior ou igual
                                            )
                                            dir_H = df_pp['Direção SH']
                                            dir_h = df_pp['Direção SH'] + 90

                                        else:
                                            dir_H = 0
                                            dir_h = 90

                                        st.checkbox("Assumir relação das tensões horizontais iguais ao longo de todo poço",
                                                    key="t_igual", value=True)
                                        if st.session_state.t_igual:
                                            st.number_input('SH% Sobrecarga', key='SH', value=0.7, step=0.1)
                                            st.write("")
                                            st.number_input('Sh% Sobrecarga', key='Sh', value=0.7, step=0.1)

                                        st.write("")
                                        st.number_input("Raio do poço", value=1, step=1, key='rw')
                                        st.write("")
                                        st.number_input("Raio de investigação", value=1, step=1, key='r')

                                with c2:
                                    with st.container(border=True):
                                        st.markdown('### Curvas Plotadas no Gráfico')
                                        if st.button("Restaurar Padrões Originais", key="plot_all_o",
                                                     use_container_width=True, type='primary'):
                                            st.session_state.jo = True
                                            st.session_state.ijo = True
                                            st.session_state.sjo = True
                                            st.session_state.li = False
                                            st.session_state.ls = False
                                            st.session_state.show_pp = False
                                            st.session_state.gs = False
                                            st.session_state.ti = False
                                            st.session_state.cia = False
                                            st.session_state.cib = False
                                            st.session_state.tsa = False
                                            st.session_state.tsb = False
                                            st.session_state.csa = False
                                            st.session_state.csb = False
                                            st.session_state.suav_cia = False
                                            st.session_state.suav_cib = False
                                            st.session_state.suav_tsa = False
                                            st.session_state.suav_tsb = False
                                            st.session_state.suav_csa = False
                                            st.session_state.suav_csb = False

                                        col1, col2 = st.columns(2)
                                        with col1:
                                            # Botão para plotar todas
                                            if st.button("Plotar todas as curvas", key="plot_all", use_container_width=True,
                                                         type='primary'):
                                                st.session_state.jo = True
                                                st.session_state.li = True
                                                st.session_state.ls = True
                                                st.session_state.show_pp = True
                                                st.session_state.gs = True
                                                st.session_state.ti = True
                                                st.session_state.cia = True
                                                st.session_state.cib = True
                                                st.session_state.tsa = True
                                                st.session_state.tsb = True
                                                st.session_state.csa = True
                                                st.session_state.csb = True
                                                st.session_state.ijo = True
                                                st.session_state.sjo = True

                                            with st.container(border=True):
                                                st.write('##### Janela Operacional')
                                                st.checkbox('Janela Operacional', key='jo', value=True)
                                                st.checkbox('Limite Inferior da Janela Operacional', key='li', value=False)
                                                st.checkbox('Limite Superior da Janela Operacional', key='ls', value=False)
                                                st.checkbox('FS Inferior da Janela Operacional', key='ijo', value=True)
                                                st.checkbox('FS Superior da Janela Operacional', key='sjo', value=True)

                                            with st.container(border=True):
                                                st.write('##### Limites Inferiores')
                                                st.checkbox('Pressão de Poros', key='show_pp', value=False)
                                                st.checkbox('Gradiente de Sobrecarga', key='gs', value=False)
                                                st.checkbox('Tração Inferior', key='ti', value=False)
                                                st.checkbox('Comp Inferior σθA', key='cia', value=False)
                                                st.checkbox('Comp Inferior σθB', key='cib', value=False)

                                            with st.container(border=True):
                                                st.write('##### Limites Superiores')
                                                st.checkbox('Tração Superior (σθA)',
                                                            value=st.session_state.get("tsa", False), key='tsa')
                                                st.checkbox('Tração Superior (σθB)',
                                                            value=st.session_state.get("tsb", False), key='tsb')
                                                st.checkbox('Comp Superior σθA', value=st.session_state.get("csa", False),
                                                            key='csa')
                                                st.checkbox('Comp Superior σθB', value=st.session_state.get("csb", False),
                                                            key='csb')

                                        with col2:
                                            # Gatilho do botão: ao clicar, todos os checkboxes desta coluna iniciam marcados
                                            if st.button("Suavizar todas as curvas", key="smooth_all", use_container_width=True, type='primary'):
                                                st.session_state.suav_max_inf = True
                                                st.session_state.suav_min_sup = True
                                                st.session_state.suav_cia = True
                                                st.session_state.suav_cib = True
                                                st.session_state.suav_tsa = True
                                                st.session_state.suav_tsb = True
                                                st.session_state.suav_csa = True
                                                st.session_state.suav_csb = True

                                            with st.container(border=True):
                                                st.write('##### Janela Operacional Suavizada')
                                                st.checkbox("Suavizar Limite Inferior da Janela Operacional",
                                                            value=True,
                                                            key='suav_max_inf')
                                                st.checkbox("Suavizar Limite Superior da Janela Operacional",
                                                            value=True,
                                                            key='suav_min_sup')

                                            with st.container(border=True):
                                                st.write('##### Limites Inferiores Suavizados')
                                                st.checkbox("Suavizar Comp Inferior σθA",
                                                            value=False,
                                                            key='suav_cia')
                                                st.checkbox("Suavizar Comp Inferior σθB",
                                                            value=False,
                                                            key='suav_cib')

                                            with st.container(border=True):
                                                st.write('##### Limites Superiores Suavizados')
                                                st.checkbox("Suavizar Tração Superior σθA",
                                                            value=False,
                                                            key='suav_tsa')
                                                st.checkbox("Suavizar Tração Superior σθB",
                                                            value=False,
                                                            key='suav_tsb')
                                                st.checkbox("Suavizar Comp Superior σθA",
                                                            value=False,
                                                            key='suav_csa')
                                                st.checkbox("Suavizar Comp Superior σθB",
                                                            value=False,
                                                            key='suav_csb')

                                            with st.container(border=True):
                                                st.write('##### Testes de Absorção (FIT/LOT)')
                                                st.checkbox("Testes de Absorção", value=True, key='tab')

                                            with st.container(border=True):
                                                st.write('##### Suavizar Perfil Sônico')
                                                st.checkbox("Suavizar Sônico", value=False, key='suavi_s')

                            @st.dialog("Adicionar Dados Direcionais")
                            def direcional():
                                with st.container(border=True):
                                    st.markdown("## Planilha de Dados Direcionais")
                                    col3, col4 = st.columns(2)

                                    with col3:
                                        step2 = st.number_input("Intervalo entre linhas (Segunda Planilha)", min_value=1,
                                                                value=1,
                                                                step=1, key="step2")

                                    st.session_state.uploaded_file2 = st.file_uploader("Envie a Segunda Planilha",
                                                                                       type=["xlsx", "xls"], key="file2")

                                    if "uploaded_file2" in st.session_state:
                                        try:
                                            excel_data2 = pd.ExcelFile(st.session_state.uploaded_file2)
                                            sheet_name2 = st.selectbox("Selecione a aba (2º Arquivo)",
                                                                       excel_data2.sheet_names,
                                                                       key="sheet2")
                                            df_full2 = pd.read_excel(st.session_state.uploaded_file2,
                                                                     sheet_name=sheet_name2)
                                            df2 = df_full2.iloc[::step2].reset_index(drop=True)

                                            if not df_full2.iloc[-1].equals(df2.iloc[-1]):
                                                df2 = pd.concat([df2, df_full2.iloc[[-1]]], ignore_index=True)

                                            st.session_state.df2 = df2

                                            with col4:
                                                st.write('')
                                                st.write('')
                                                st.markdown(f"**Total de linhas carregadas:** {len(df2)}")

                                            st.dataframe(df2, use_container_width=True, hide_index=True)

                                        except Exception as e:
                                            pass

                                        # Botão para confirmar dados
                                        if st.button("Inserir Dados Direcionais", use_container_width=True, type="primary"):
                                            # Interpolação dos dados de Inc e Azi para profundidades de df1
                                            if 'df1' in st.session_state and 'df2' in st.session_state:
                                                df1 = st.session_state.df1
                                                df2 = st.session_state.df2

                                                try:
                                                    if st.session_state.ex == 'Ativada':
                                                        expand_from_zero = True
                                                    else:
                                                        expand_from_zero = False

                                                    # Identificação da coluna MD em cada dataframe
                                                    col_md1 = [col for col in df1.columns if 'md' in col.lower()]
                                                    col_md2 = [col for col in df2.columns if 'md' in col.lower()]

                                                    if not col_md1 or not col_md2:
                                                        st.error(
                                                            "Colunas de profundidade MD não encontradas em uma ou ambas as planilhas.")
                                                    elif 'Inc' not in df2.columns or 'Azi' not in df2.columns:
                                                        st.error("A segunda planilha deve conter as colunas 'Inc' e 'Azi'.")
                                                    else:
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
                                                        azi_interp = np.interp(md1, md2_sorted, azi2_sorted)

                                                        df_interp = pd.DataFrame({
                                                            "Profundidade": md1,
                                                            "Inc (°)": inc_interp,
                                                            "Azi (°)": azi_interp
                                                        })

                                                        st.session_state.df_interp = df_interp

                                                except Exception as e:
                                                    st.error(f"Erro na interpolação: {e}")

                                            st.rerun()

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
                                    ["Arenito", "Folhelho", "Calcário", "Siltito", "Conglomerado", "Halita"]
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
                                            if st.button('Adicionar Dados Direcionais', use_container_width=True,
                                                         type='primary'):
                                                direcional()
                                            if "ts" not in st.session_state:
                                                st.session_state.ts = False

                                            if st.button("Cosiderar Litologia das Formações", use_container_width=True,
                                                         type="primary", key="lito_button"):
                                                coe_lito()

                                            # st.checkbox('Alterar variáveis manualmente', key='avm')
                                            # if st.session_state.avm:
                                            #     with st.expander("Definir Parâmetros", expanded=True):
                                            #         st.checkbox('Alterar Coesão da Rocha (So)', key='at_So')
                                            #         st.checkbox('Alterar Pressão de Poros', key='at_pp')

                                            with st.form("jop", border=False):
                                                col1, col2 = st.columns((0.8, 1))
                                                with col1:
                                                    st.number_input('Ângulo de fricção (Φ)', key='phi', value=30)
                                                    st.number_input('Limite de falha por tração', key='lft', value=0)
                                                    st.number_input('Profundidade (m)', key='m', value=0.00, format="%.2f")
                                                    st.number_input('Peso do fluido (lb/gal)', key='ppg', value=9.,
                                                                    format="%.2f", step=0.5)
                                                st.selectbox('Método de cálculo do UCS', ['Lacy', 'Mechpro'], key='ucs')
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

                                        # PROFUNDIDADE DAS SAPATAS
                                        with st.expander('Profundidades das Sapatas', expanded=False):
                                            with st.form('sapatas_form', clear_on_submit=False, border=False):
                                                st.markdown("### Profundidade das Sapatas (TVD)")

                                                # DataFrame inicial
                                                z = pd.DataFrame({
                                                    'Fase': [0.000],
                                                    'Profundidade da sapata (m)': [0.0]
                                                })

                                                # Editor de dados dinâmico
                                                edited_sapatas = st.data_editor(
                                                    z,
                                                    hide_index=True,
                                                    num_rows='dynamic',
                                                    key='edited_sapatas'
                                                )

                                                # Botão de envio
                                                submitted = st.form_submit_button('Inserir Sapatas',
                                                                                  use_container_width=True,
                                                                                  type='primary')

                                                if submitted:
                                                    # Garante que as colunas existam
                                                    if 'Fase' not in edited_sapatas.columns:
                                                        edited_sapatas['Fase'] = 1.000

                                                    # Filtra profundidades válidas
                                                    sapatas_df = edited_sapatas[
                                                        edited_sapatas['Profundidade da sapata (m)'] > 0].copy()

                                                    # Converte tipos
                                                    sapatas_df['Fase'] = sapatas_df['Fase'].astype(float).round(3)
                                                    sapatas_df['Profundidade da sapata (m)'] = sapatas_df[
                                                        'Profundidade da sapata (m)'].astype(float)

                                                    # Salva no session_state
                                                    st.session_state.sapatas_df = sapatas_df

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
                                                value=((1 / (((0.8042 * (
                                                        ((1000000 / df_tvp['Perfil sônico (µs/pé)']) / 3.281) / 1000)) -
                                                              0.8559) * 1000)) * 1000000) / 3.281
                                            )

                                            df_tvp.insert(
                                                loc=8,
                                                column='Poisson',
                                                value=(0.5 * (df_tvp['DTS'] / df_tvp['Perfil sônico (µs/pé)']) ** 2 - 1) / (
                                                        (df_tvp['DTS'] / df_tvp['Perfil sônico (µs/pé)']) ** 2 - 1)
                                            )
                                            if st.session_state.ucs == 'Lacy':
                                                df_tvp.insert(
                                                    loc=9,
                                                    column='G dinam (MMpsi)',
                                                    value=(1.34 * 10 ** 10 * df_tvp['Perfil de densidade (g/cm³)'] / (
                                                            df_tvp['DTS'] ** 2)) / 10 ** 6
                                                )
                                                df_tvp.insert(
                                                    loc=10,
                                                    column='E dinâmico (MMpsi)',
                                                    value=2 * df_tvp['G dinam (MMpsi)'] * (1 + df_tvp['Poisson'])
                                                )
                                                df_tvp.insert(
                                                    loc=11,
                                                    column='E estático (MMpsi)',
                                                    value=0.018 * (df_tvp['E dinâmico (MMpsi)'] ** 2) + 0.422 * df_tvp[
                                                        'E dinâmico (MMpsi)']
                                                )
                                                df_tvp.insert(
                                                    loc=12,
                                                    column='UCS (psi)',
                                                    value=(0.2787 * df_tvp['E estático (MMpsi)'] ** 2 + 2.458 * df_tvp[
                                                        'E estático (MMpsi)']) * 1000
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
                                                    value=145.0377 * 1.9e-20 * (
                                                            1000 * df_tvp['Perfil de densidade (g/cm³)']) ** 2 * (
                                                                  304800 / df_tvp['Perfil sônico (µs/pé)']) ** 4 *
                                                          ((1 + df_tvp['Poisson']) / (1 - df_tvp['Poisson'])) ** 2 * (
                                                                  1 - 2 * df_tvp['Poisson']) * (
                                                                  1 + 0.79 * df_tvp['Vsh'])
                                                )
                                            # Calcula So original
                                            df_tvp["So (psi)"] = (df_tvp['UCS (psi)'] *
                                                                  (1 - np.sin(np.radians(st.session_state.phi)))) / \
                                                                 (2 * np.cos(np.radians(st.session_state.phi)))

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

                                            if st.session_state.t_igual:
                                                r1 = st.session_state.SH * df_tvp['Gradiente de Sobrecarga (lb/gal)']
                                                r2 = st.session_state.Sh * df_tvp['Gradiente de Sobrecarga (lb/gal)']

                                            else:
                                                v1 = ((np.log(df_tvp['Profundidade (m)']) - np.log(
                                                    st.session_state.a)) / st.session_state.b)
                                                r1 = r2 = v1 * df_tvp['Gradiente de Sobrecarga (lb/gal)']

                                            # Inserindo a coluna no DataFrame
                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('So (psi)') + 1,
                                                column='SH (lb/gal)',
                                                value=r1
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('SH (lb/gal)') + 1,
                                                column='Direção SH',
                                                value=dir_H
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('Direção SH') + 1,
                                                column='Sh (lb/gal)',
                                                value=r2
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('Sh (lb/gal)') + 1,
                                                column='Direção Sh',
                                                value=dir_h
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('Direção Sh') + 1,
                                                column='τxy',
                                                value=round(((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc'])) *
                                                        -np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH']))) * df_tvp['SH (lb/gal)'] +
                                                       (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc'])) *
                                                        np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH']))) * df_tvp['Sh (lb/gal)']),0)
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('τxy') + 1,
                                                column='τyz',
                                                value=round(((-np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Azi'])) *
                                                        np.sin(np.radians(df_tvp['Inc'])) * df_tvp['SH (lb/gal)']) +
                                                       (np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Azi'])) *
                                                        np.sin(np.radians(df_tvp['Inc'])) * df_tvp['Sh (lb/gal)'])),2)
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('τyz') + 1,
                                                column='τzx',
                                                value=round(((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc'])) *
                                                        np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc'])) *
                                                        df_tvp['SH (lb/gal)']) + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                        np.sin(np.radians(df_tvp['Inc'] )) * np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                        np.cos(np.radians(df_tvp['Inc'])) * df_tvp['Sh (lb/gal)']) +
                                                        (np.cos(np.radians(df_tvp['Inc'])) * -np.sin(np.radians(df_tvp['Inc'])) *
                                                         df_tvp['Gradiente de Sobrecarga (lb/gal)'])),2)
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
                                                    'τzx'] * np.sin(np.radians(df_tvp['θA (°)']))),0)
                                            )

                                            # ==== Inicialmente Pw = 8.8 ====
                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('τθa') + 1,
                                                column='Pw',
                                                value=st.session_state.ppg
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
                                                value=((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.cos(np.radians(df_tvp['Inc'])))**2 *
                                                       df_tvp['SH (lb/gal)'] + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                       np.cos(np.radians(df_tvp['Inc'])))**2 * df_tvp['Sh (lb/gal)'] +
                                                       (np.sin(np.radians(df_tvp['Inc'])))**2 * df_tvp['Gradiente de Sobrecarga (lb/gal)'])
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σx') + 1,
                                                column='σy',
                                                value=((-np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])))**2 * df_tvp['SH (lb/gal)'] +
                                                       (np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])))**2 * df_tvp['Sh (lb/gal)'])
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σy') + 1,
                                                column='σr',
                                                value=(0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 - ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)))) +
                                                      (0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 - (4 * (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) +
                                                              (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.cos(
                                                          np.radians((2 * df_tvp['θA (°)'])))) +
                                                      (df_tvp['τxy'] * (
                                                              1 - (4 * (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) + (
                                                              3 * (df_tvp['rw'] ** 4) /
                                                              (df_tvp['r'] ** 4)) * np.sin(
                                                          np.radians(2 * df_tvp['θA (°)']))) + (
                                                               (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw'])
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σr') + 1,
                                                column='σθA',
                                                value=(0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 + (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2))) +
                                                      (-0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 + 3 * ((df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) *
                                                       np.cos(np.radians(2 * df_tvp['θA (°)']))) -
                                                      (df_tvp['τxy'] * (
                                                              1 + (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.sin(
                                                          np.radians(2 * df_tvp['θA (°)']))) -
                                                      ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw']
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σθA') + 1,
                                                column='σθB',
                                                value=(0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 + (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2))) +
                                                      (-0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 + 3 * ((df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) *
                                                       np.cos(np.radians(2 * df_tvp['θB (°)']))) -
                                                      (df_tvp['τxy'] * (
                                                              1 + (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.sin(
                                                          np.radians(2 * df_tvp['θB (°)']))) -
                                                      ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw']
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σθB') + 1,
                                                column='σa',
                                                value=((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc'])))**2 *
                                                       df_tvp['SH (lb/gal)'] + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                       np.sin(np.radians(df_tvp['Inc'])))**2 * df_tvp['Sh (lb/gal)'] +
                                                       (np.cos(np.radians(df_tvp['Inc'])))**2 * df_tvp['Gradiente de Sobrecarga (lb/gal)'])
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σa') + 1,
                                                column='σr efetivo (psi)',
                                                value=(df_tvp['σr'] - df_tvp[
                                                    'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                      df_tvp['Profundidade (m)']
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σr efetivo (psi)') + 1,
                                                column='σθA efetivo (psi)',
                                                value=(df_tvp['σθA'] - df_tvp[
                                                    'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                      df_tvp['Profundidade (m)']
                                            )

                                            df_tvp.insert(
                                                loc=df_tvp.columns.get_loc('σθA efetivo (psi)') + 1,
                                                column='σθB efetivo (psi)',
                                                value=(df_tvp['σθB'] - df_tvp[
                                                    'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 *
                                                      df_tvp['Profundidade (m)']
                                            )

                                            # ==== Pw que zera cada tensão efetiva ====
                                            coef_r = (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)
                                            coef_t = -(df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)

                                            sigma_r_sem_pw = df_tvp['σr'] - coef_r * df_tvp['Pw']
                                            sigma_ta_sem_pw = df_tvp['σθA'] - coef_t * df_tvp['Pw']
                                            sigma_tb_sem_pw = df_tvp['σθB'] - coef_t * df_tvp['Pw']

                                            df_tvp['Tração Inferior'] = (df_tvp[
                                                                             'Gradiente de Pressão de Poros (lb/gal)'] - sigma_r_sem_pw) / coef_r
                                            df_tvp['Tração Superior (σθA)'] = (df_tvp[
                                                                                   'Gradiente de Pressão de Poros (lb/gal)'] - sigma_ta_sem_pw) / coef_t
                                            df_tvp['Tração Superior (σθB)'] = (df_tvp[
                                                                                   'Gradiente de Pressão de Poros (lb/gal)'] - sigma_tb_sem_pw) / coef_t

                                            # ================== Pw na falha por compressão ==================
                                            phi_rad = np.radians(st.session_state.phi)
                                            t = np.tan(phi_rad)

                                            coef_base = (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)  # (rw^2/r^2)
                                            Kdepth = 0.1704 * df_tvp['Profundidade (m)']  # psi por (lb/gal)
                                            coef_psi = Kdepth * coef_base  # coeficiente do termo linear de Pw já em psi

                                            def sigma_r_sem_pw(theta_deg):
                                                th = np.radians(2 * theta_deg)
                                                return (0.5 * (df_tvp['σx'] + df_tvp['σy']) * (1 - coef_base)
                                                        + 0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                                1 - 4 * coef_base + 3 * (coef_base ** 2)) * np.cos(th)
                                                        + df_tvp['τxy'] * (
                                                                1 - 4 * coef_base + 3 * (coef_base ** 2)) * np.sin(th))

                                            def sigma_t_sem_pw(theta_deg):
                                                th = np.radians(2 * theta_deg)
                                                return (0.5 * (df_tvp['σx'] + df_tvp['σy']) * (1 + coef_base)
                                                        - 0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                                1 + 3 * (coef_base ** 2)) * np.cos(
                                                            th)
                                                        + df_tvp['τxy'] * (1 + 3 * (coef_base ** 2)) * np.sin(th))

                                            Ar_A = sigma_r_sem_pw(df_tvp['θA (°)'])
                                            At_A = sigma_t_sem_pw(df_tvp['θA (°)'])
                                            Ar_B = sigma_r_sem_pw(df_tvp['θB (°)'])
                                            At_B = sigma_t_sem_pw(df_tvp['θB (°)'])
                                            Pp = df_tvp['Gradiente de Pressão de Poros (lb/gal)']

                                            C_A_psi = Kdepth * (0.5 * (At_A + Ar_A) - Pp)
                                            R0_A_psi = Kdepth * (0.5 * (At_A - Ar_A))

                                            C_B_psi = Kdepth * (0.5 * (At_B + Ar_B) - Pp)
                                            R0_B_psi = Kdepth * (0.5 * (At_B - Ar_B))

                                            S0 = df_tvp['So (psi)']

                                            K_A = (t * C_A_psi + S0) ** 2 / (1 + t ** 2)
                                            K_B = (t * C_B_psi + S0) ** 2 / (1 + t ** 2)

                                            sqrtK_A = np.sqrt(np.maximum(K_A, 0))
                                            sqrtK_B = np.sqrt(np.maximum(K_B, 0))

                                            den_ok = np.where(coef_psi != 0, coef_psi, np.nan)

                                            Pw_A_1 = (R0_A_psi - sqrtK_A) / den_ok
                                            Pw_A_2 = (R0_A_psi + sqrtK_A) / den_ok
                                            Pw_B_1 = (R0_B_psi - sqrtK_B) / den_ok
                                            Pw_B_2 = (R0_B_psi + sqrtK_B) / den_ok

                                            Pw_A_inf = np.minimum(Pw_A_1, Pw_A_2)
                                            Pw_A_sup = np.maximum(Pw_A_1, Pw_A_2)
                                            Pw_B_inf = np.minimum(Pw_B_1, Pw_B_2)
                                            Pw_B_sup = np.maximum(Pw_B_1, Pw_B_2)

                                            # Adiciona as colunas ao DataFrame
                                            df_tvp.insert(loc=df_tvp.columns.get_loc('Tração Superior (σθB)') + 1,
                                                          column='Comp Inferior σθA', value=Pw_A_inf)
                                            df_tvp.insert(loc=df_tvp.columns.get_loc('Comp Inferior σθA') + 1,
                                                          column='Comp Superior σθA', value=Pw_A_sup)
                                            df_tvp.insert(loc=df_tvp.columns.get_loc('Comp Superior σθA') + 1,
                                                          column='Comp Inferior σθB', value=Pw_B_inf)
                                            df_tvp.insert(loc=df_tvp.columns.get_loc('Comp Inferior σθB') + 1,
                                                          column='Comp Superior σθB', value=Pw_B_sup)
                                            # ==================================================================
                                            with col2:
                                                opcao_tracao = st.radio(
                                                    "Selecione a tensão para o peso do fluido:",
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
                                                    df_tvp['Pw'] = peso_fluido

                                                    # ==== Recalcular todas as tensões com o novo Pw ====
                                                    # σr
                                                    df_tvp['σr'] = ((0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 - ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)))) +
                                                      (0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 - (4 * (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) +
                                                              (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.cos(
                                                          np.radians((2 * df_tvp['θA (°)'])))) +
                                                      (df_tvp['τxy'] * (
                                                              1 - (4 * (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) + (
                                                              3 * (df_tvp['rw'] ** 4) /
                                                              (df_tvp['r'] ** 4)) * np.sin(
                                                          np.radians(2 * df_tvp['θA (°)']))) + (
                                                               (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw']))

                                                    # σθA
                                                    df_tvp['σθA'] = ((0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 + (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2))) +
                                                      (-0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 + 3 * ((df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) *
                                                       np.cos(np.radians(2 * df_tvp['θA (°)']))) -
                                                      (df_tvp['τxy'] * (
                                                              1 + (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.sin(
                                                          np.radians(2 * df_tvp['θA (°)']))) -
                                                      ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw'])

                                                    # σθB
                                                    df_tvp['σθB'] = ((0.5 * (df_tvp['σx'] + df_tvp['σy']) * (
                                                        1 + (df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2))) +
                                                      (-0.5 * (df_tvp['σx'] - df_tvp['σy']) * (
                                                              1 + 3 * ((df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) *
                                                       np.cos(np.radians(2 * df_tvp['θB (°)']))) -
                                                      (df_tvp['τxy'] * (
                                                              1 + (3 * (df_tvp['rw'] ** 4) / (df_tvp['r'] ** 4))) * np.sin(
                                                          np.radians(2 * df_tvp['θB (°)']))) -
                                                      ((df_tvp['rw'] ** 2) / (df_tvp['r'] ** 2)) * df_tvp['Pw'])

                                                    # σa
                                                    df_tvp['σa'] = ((np.cos(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) * np.sin(np.radians(df_tvp['Inc'])))**2 *
                                                       df_tvp['SH (lb/gal)'] + (np.sin(np.radians(df_tvp['Azi'] - df_tvp['Direção SH'])) *
                                                       np.sin(np.radians(df_tvp['Inc'])))**2 * df_tvp['Sh (lb/gal)'] +
                                                       (np.cos(np.radians(df_tvp['Inc'])))**2 * df_tvp['Gradiente de Sobrecarga (lb/gal)'])

                                                    # Recalcular tensões efetivas
                                                    df_tvp['σr efetivo (psi)'] = (df_tvp['σr'] - df_tvp[
                                                        'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 * df_tvp[
                                                                                     'Profundidade (m)']
                                                    df_tvp['σθA efetivo (psi)'] = (df_tvp['σθA'] - df_tvp[
                                                        'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 * df_tvp[
                                                                                      'Profundidade (m)']
                                                    df_tvp['σθB efetivo (psi)'] = (df_tvp['σθB'] - df_tvp[
                                                        'Gradiente de Pressão de Poros (lb/gal)']) * 0.1704 * df_tvp[
                                                                                      'Profundidade (m)']

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

                                                df_tvp['Max Inferior'] = df_tvp[
                                                    ['Gradiente de Pressão de Poros (lb/gal)', 'Tração Inferior',
                                                     'Comp Inferior σθA', 'Comp Inferior σθB']].max(axis=1)

                                                # Coluna com o menor valor entre Tração Superior σθA, Tração Superior σθB, Comp Superior σθA e Comp Superior σθB
                                                df_tvp['Min Superior'] = df_tvp[
                                                    ['Tração Superior (σθA)', 'Tração Superior (σθB)', 'Comp Superior σθA',
                                                     'Comp Superior σθB']].min(axis=1)

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
                                            st.markdown('### Critério de Falha - Mohr Coulomb')
                                            if not criterio_disponivel(df_tvp):
                                                st.warning(
                                                    "⚠️ Insira os dados direcionais e calcule as tensões antes de avaliar o critério de falha.")

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
                                                df_suav['Comp Inferior σθA'] = suavizar(df_tvp['Profundidade (m)'],
                                                                                        df_tvp['Comp Inferior σθA'])
                                                df_suav['Comp Inferior σθB'] = suavizar(df_tvp['Profundidade (m)'],
                                                                                        df_tvp['Comp Inferior σθB'])
                                                df_suav['Max Inferior'] = df_suav[
                                                    ['Gradiente de Pressão de Poros (lb/gal)', 'Tração Inferior',
                                                     'Comp Inferior σθA', 'Comp Inferior σθB']].max(axis=1)
                                                df_suav['Tração Superior (σθA)'] = suavizar(
                                                    df_tvp['Profundidade (m)'],
                                                    df_tvp['Tração Superior (σθA)'])
                                                df_suav['Tração Superior (σθB)'] = suavizar(
                                                    df_tvp['Profundidade (m)'],
                                                    df_tvp['Tração Superior (σθB)'])
                                                df_suav['Comp Superior σθA'] = suavizar(df_tvp['Profundidade (m)'],
                                                                                        df_tvp['Comp Superior σθA'])
                                                df_suav['Comp Superior σθB'] = suavizar(df_tvp['Profundidade (m)'],
                                                                                        df_tvp['Comp Superior σθB'])
                                                df_suav['Min Superior'] = df_suav[
                                                    ['Tração Superior (σθA)', 'Tração Superior (σθB)',
                                                     'Comp Superior σθA',
                                                     'Comp Superior σθB']].min(axis=1)

                                                colu1, colu2, colu3 = st.columns(3)
                                                with colu1:
                                                    if opcao_tracao == "Peso de Fluido Escolhido":
                                                        linha2 = \
                                                            linha = df_tvp.loc[st.session_state.y == profundidade_proxima].iloc[0]
                                                        max_inferior = max(linha2['Tração Inferior'],
                                                                           linha2['Comp Inferior σθA'],
                                                                           linha2['Comp Inferior σθB'])
                                                        min_superior = min(linha2['Tração Superior (σθA)'],
                                                                           linha2['Tração Superior (σθB)'],
                                                                           linha2['Comp Superior σθA'],
                                                                           linha2['Comp Superior σθB'])

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
                                                    else:
                                                        coluna_ref = 'Profundidade (m)' if st.session_state.t_prof == "TVD" else 'MD'

                                                        linha2 = df_tvp.loc[df_tvp[coluna_ref] == profundidade_proxima].iloc[0]

                                                        max_inferior = max(linha2['Tração Inferior'],
                                                                           linha2['Comp Inferior σθA'],
                                                                           linha2['Comp Inferior σθB'])

                                                        min_superior = min(linha2['Tração Superior (σθA)'],
                                                                           linha2['Tração Superior (σθB)'],
                                                                           linha2['Comp Superior σθA'],
                                                                           linha2['Comp Superior σθB'])

                                                        if peso_fluido <= max_inferior:
                                                            tipo_falha = "Colapso"
                                                            falha = max_inferior
                                                        elif peso_fluido >= min_superior:
                                                            tipo_falha = "Fratura"
                                                            falha = min_superior

                                                        else:
                                                            tipo_falha = None
                                                            falha = None

                                                        if falha is not None:
                                                            st.markdown(
                                                                f"""
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
                                                                        padding: 12px 20px;
                                                                    ">
                                                                        {tipo_falha} em: {falha:.2f} ppg
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
                                                                        color: green;
                                                                        font-weight: bold;
                                                                        border: 2px solid black;
                                                                        border-radius: 10px;
                                                                        padding: 12px 20px;
                                                                    ">
                                                                        Poço Estável
                                                                    </div>
                                                                </div>
                                                                """,
                                                                unsafe_allow_html=True
                                                            )

                                                with colu2:
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
                                                                padding: 0px 0px;
                                                                text-align: center;
                                                            ">
                                                                Peso do Fluido<br>
                                                                <span style="color: red;">{st.session_state.ppg:.2f}</span> lb/gal
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

                                                def intersecao_circulo_reta(centro, raio, m, x0, y0):
                                                    a = 1 + m ** 2
                                                    b = -2 * centro + 2 * m * (y0 - m * x0)
                                                    c = centro ** 2 + (y0 - m * x0) ** 2 - raio ** 2
                                                    delta = b ** 2 - 4 * a * c
                                                    if delta < 0:
                                                        return None
                                                    raiz_delta = np.sqrt(delta)
                                                    x1 = (-b + raiz_delta) / (2 * a)
                                                    x2 = (-b - raiz_delta) / (2 * a)
                                                    return [(x1, m * (x1 - x0) + y0), (x2, m * (x2 - x0) + y0)]

                                                # Parâmetros da reta
                                                m = np.tan(np.radians(st.session_state.phi))
                                                x0, y0 = x_compressao_inicio, y_compressao_inicio

                                                # Interseções com A e B (pega o ponto de maior x se existir)
                                                for nome, centro, raio in [('A', centro_A, raio_A),
                                                                           ('B', centro_B, raio_B)]:
                                                    pontos = intersecao_circulo_reta(centro, raio, m, x0, y0)
                                                    if pontos:
                                                        x, y = max(pontos, key=lambda p: p[0])
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

                                                st.plotly_chart(fig, use_container_width=True)

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

                                                    def minimum_curvature(df, x0=0.0, y0=0.0, tvd0=0.0):
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
                                                            dN = 0.5 * dMD * (np.sin(Inc[i - 1]) * np.cos(
                                                                Azi[i - 1]) + np.sin(
                                                                Inc[i]) * np.cos(Azi[i])) * RF
                                                            dE = 0.5 * dMD * (np.sin(Inc[i - 1]) * np.sin(
                                                                Azi[i - 1]) + np.sin(
                                                                Inc[i]) * np.sin(Azi[i])) * RF
                                                            dTVD = 0.5 * dMD * (
                                                                    np.cos(Inc[i - 1]) + np.cos(Inc[i])) * RF
                                                            Easting.append(Easting[-1] + dE)
                                                            Northing.append(Northing[-1] + dN)
                                                            TVD.append(TVD[-1] + dTVD)

                                                        return pd.DataFrame({
                                                            "MD": MD,
                                                            "Inclinação (°)": np.degrees(Inc),
                                                            "Azimute (°)": np.degrees(Azi),
                                                            "Easting": Easting,
                                                            "Northing": Northing,
                                                            "TVD": TVD,
                                                            "Dogleg Severity (°/30m)": [0.0] + DLS_list
                                                        })

                                                    df_to_use = None

                                                    if "df_interp" in st.session_state and isinstance(
                                                            st.session_state["df_interp"], pd.DataFrame):
                                                        df_to_use = st.session_state["df_interp"].copy()
                                                    elif "df2" in st.session_state and isinstance(
                                                            st.session_state["df2"],
                                                            pd.DataFrame):
                                                        df_to_use = st.session_state["df2"].copy()
                                                    elif "uploaded_file" in locals() and uploaded_file:
                                                        df_to_use = pd.read_excel(uploaded_file)

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
                                                    if "df2" in st.session_state and isinstance(
                                                            st.session_state["df2"],
                                                            pd.DataFrame):
                                                        df_ref = st.session_state["df2"].copy()

                                                        # Identificar colunas de profundidade, inclinação e azimute
                                                        col_md = [c for c in df_ref.columns if
                                                                  "md" in c.lower() or "profund" in c.lower()]
                                                        col_inc = [c for c in df_ref.columns if "inc" in c.lower()]
                                                        col_azi = [c for c in df_ref.columns if
                                                                   "azi" in c.lower() or "azim" in c.lower()]

                                                        if col_md and col_inc and col_azi:
                                                            md_ref = df_ref[col_md[0]].astype(float).values
                                                            inc_ref = df_ref[col_inc[0]].astype(float).values
                                                            azi_ref = df_ref[col_azi[0]].astype(float).values

                                                            # Ordenar por profundidade
                                                            sort_idx = np.argsort(md_ref)
                                                            md_ref = md_ref[sort_idx]
                                                            inc_ref = inc_ref[sort_idx]
                                                            azi_ref = azi_ref[sort_idx]

                                                            first_md = df_proc["MD"].iloc[0]
                                                            if first_md > md_ref.min():
                                                                passo = 1.0
                                                                md_extra = np.arange(md_ref.min(), first_md, passo)

                                                                # Interpolar Inclinação e Azimute de df2 ao longo do intervalo
                                                                inc_interp = np.interp(md_extra, md_ref, inc_ref)
                                                                azi_interp = np.interp(md_extra, md_ref, azi_ref)

                                                                df_extra = pd.DataFrame({
                                                                    "MD": md_extra,
                                                                    "Inc": inc_interp,
                                                                    "Azi": azi_interp
                                                                })

                                                                # Combinar com os dados processados
                                                                df_proc = pd.concat([df_extra, df_proc],
                                                                                    ignore_index=True).drop_duplicates(
                                                                    subset=["MD"]).sort_values("MD")

                                                    df_out = minimum_curvature(df_proc, x0=0.0, y0=0.0, tvd0=0.0)

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
                                                        height=800, width=600,
                                                        scene=dict(
                                                            xaxis=dict(title="Easting"),
                                                            yaxis=dict(title="Northing"),
                                                            zaxis=dict(title="TVD (m)", autorange="reversed"),
                                                        ),
                                                        legend=dict(
                                                            # title="Elementos do Modelo",  # Título da legenda
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
                                                "⚠️ Insira os dados direcionais e calcule as tensões antes de avaliar o critério de falha.")
                                        if criterio_disponivel(df_tvp):
                                            with colu3:
                                                df_tvp['Max Inferior'] = df_tvp[
                                                    ['Tração Inferior', 'Comp Inferior σθA',
                                                     'Comp Inferior σθB']].max(
                                                    axis=1)
                                                df_tvp['Min Superior'] = df_tvp[
                                                    ['Tração Superior (σθA)', 'Tração Superior (σθB)',
                                                     'Comp Superior σθA', 'Comp Superior σθB']].min(axis=1)

                                                linha = \
                                                df_tvp.loc[st.session_state.y == profundidade_proxima].iloc[0]
                                                max_inferior = linha['Max Inferior']
                                                min_superior = linha['Min Superior']

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
                                                                                                        padding: 0px 0px;
                                                                                                        text-align: center;
                                                                                                    ">
                                                                                                        Janela Op.<br>
                                                                                                        <span style="color: red;">{max_inferior:.2f}</span> &lt; ρ &lt; <span style="color: red;">{min_superior:.2f}</span>
                                                                                                    </div>
                                                                                                </div>
                                                                                                """,
                                                    unsafe_allow_html=True
                                                )
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

                                                idade_formacao(ax_idade, df_idade, st.session_state.y_max_pp)

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

                                                ax1 = fig.add_subplot(gs[0])
                                                ax_gap = fig.add_subplot(gs[1])
                                                ax_gap.axis('off')

                                                ax = fig.add_subplot(gs[2], sharey=ax1)

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

                                            if st.session_state.ppg is not None and st.session_state.m is not None:
                                                ax.scatter(
                                                    peso_fluido,
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

                                            if 'fs' not in st.session_state:
                                                st.session_state.fs = 0.5

                                            if st.session_state.ijo:
                                                ax.plot(x_max_inf + st.session_state.fs, st.session_state.y,
                                                        color='gold',
                                                        linestyle='--',
                                                        linewidth=2, label="FS Inferior da Janela Operacional")

                                            if st.session_state.sjo:
                                                ax.plot(x_min_sup - st.session_state.fs, st.session_state.y,
                                                        color='tomato',
                                                        linestyle='--',
                                                        linewidth=2, label="FS Superior da Janela Operacional")

                                            if st.session_state.ijo and st.session_state.sjo:
                                                ax.fill_betweenx(st.session_state.y,
                                                                 x_max_inf + st.session_state.fs,
                                                                 x_min_sup - st.session_state.fs,
                                                                 where=(x_min_sup > x_max_inf),
                                                                 color='lightgreen',
                                                                 alpha=0.2,
                                                                 label='Janela Operacional', interpolate=True)
                                            if not st.session_state.ijo and not st.session_state.sjo:
                                                if st.session_state.jo:
                                                    ax.fill_betweenx(st.session_state.y, x_max_inf, x_min_sup,
                                                                     where=(x_min_sup > x_max_inf),
                                                                     color='lightgreen',
                                                                     alpha=0.2,
                                                                     label='Janela Operacional',
                                                                     interpolate=True)

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
                                                            color='yellow',
                                                            linestyle='-',
                                                            linewidth=2,
                                                            label="Comp Inferior σθA")
                                                else:
                                                    ax.plot(df_tvp['Comp Inferior σθA'], st.session_state.y,
                                                            color='yellow',
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
                                                profundidade_proxima - 10,
                                                f"Profundidade Analisada ({profundidade_proxima:.1f} m)",
                                                color='black',
                                                fontsize=10,
                                                verticalalignment='bottom',
                                                horizontalalignment='right',
                                                zorder=8
                                            )

                                            if 'sapatas_df' in st.session_state and not st.session_state.sapatas_df.empty:
                                                plotted_label = False
                                                # Proteções básicas
                                                df_exist = 'df_tvp' in locals() or 'df_tvp' in globals() or 'df_tvp' in st.session_state
                                                # Preferimos usar a variável local df_tvp, se existir; senão, tentar session_state
                                                df_tvp_local = None
                                                if 'df_tvp' in locals():
                                                    df_tvp_local = df_tvp
                                                elif 'df_tvp' in globals():
                                                    df_tvp_local = globals().get('df_tvp')
                                                elif 'df_tvp' in st.session_state:
                                                    df_tvp_local = st.session_state.df_tvp

                                                for _, row in st.session_state.sapatas_df.iterrows():
                                                    fase = float(row['Fase'])
                                                    tvd_informada = float(row['Profundidade da sapata (m)'])

                                                    # Decide profundidade a plotar (y_plot)
                                                    y_plot = tvd_informada  # fallback padrão é a TVD informada
                                                    tvd_display = tvd_informada
                                                    md_display = None

                                                    try:
                                                        if st.session_state.t_prof == "TVD":
                                                            # usar exatamente o valor informado (TVD)
                                                            y_plot = tvd_informada
                                                        else:
                                                            # visualizar por MD → converter TVD informado para MD buscando o registro mais próximo em df_tvp
                                                            if df_tvp_local is not None and 'Profundidade (m)' in df_tvp_local.columns and 'MD' in df_tvp_local.columns:
                                                                idx_closest = (df_tvp_local[
                                                                                   'Profundidade (m)'] - tvd_informada).abs().idxmin()
                                                                # pega o MD correspondente (pode ser float ou int)
                                                                md_val = float(
                                                                    df_tvp_local.loc[idx_closest, 'MD'])
                                                                y_plot = md_val
                                                                md_display = md_val
                                                            else:
                                                                # fallback: se df_tvp não disponível ou sem coluna MD, usar TVD informado
                                                                y_plot = tvd_informada
                                                    except Exception:
                                                        # proteção contra quaisquer erros inesperados
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

                                                    # Texto à direita: mostra fase e a profundidade original (TVD); se convertido, mostra também o MD usado
                                                    if md_display is None:
                                                        text_str = f"Fase {fase:.3f}, {tvd_display:.2f} m"
                                                    else:
                                                        text_str = f"Fase {fase:.3f}, TVD {tvd_display:.2f} m (MD {md_display:.2f} m)"

                                                    ax.text(
                                                        st.session_state.x_max - (
                                                                st.session_state.x_max - st.session_state.x_min) * 0.01,
                                                        # 1% de margem
                                                        y_plot - 10,  # levemente acima da linha/ marcador
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

                                            if 'edited_z2' in st.session_state and not st.session_state.edited_z.empty:
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
                                            if "dados_rft" in st.session_state and not st.session_state[
                                                "dados_rft"].empty:
                                                df_rft = st.session_state["dados_rft"]

                                                # Plota Testes RFT se houver valores preenchidos
                                                if "Teste RFT (lb/gal)" in df_rft.columns and df_rft[
                                                    "Teste RFT (lb/gal)"].notna().any():
                                                    ax.scatter(
                                                        df_rft["Teste RFT (lb/gal)"],
                                                        df_rft["Profundidade (m)"],
                                                        color='green',
                                                        marker='o',
                                                        s=80,
                                                        label="Teste de Formação (RFT)",
                                                        edgecolors='black',
                                                        zorder=5
                                                    )

                                                # Plota Pesos de Fluido se houver valores preenchidos
                                                if "Peso do Fluido (lb/gal)" in df_rft.columns and df_rft[
                                                    "Peso do Fluido (lb/gal)"].notna().any():
                                                    ax.plot(
                                                        df_rft["Peso do Fluido (lb/gal)"],
                                                        df_rft["Profundidade (m)"],
                                                        color='mediumvioletred',
                                                        linestyle='-',
                                                        linewidth=2,
                                                        label="Peso do Fluido",
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
                                                with st.expander("Configurações da Legenda", expanded=False):
                                                    st.checkbox('Exibir Legendas', key='leg', value=True)
                                                    if st.session_state.leg:
                                                        legendas_pt = {
                                                            "Melhor posição": "best",
                                                            "Superior direito": "upper right",
                                                            "Superior esquerdo": "upper left",
                                                            "Inferior direito": "lower right",
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
                                                            value=8
                                                        )

                                                with st.expander("Configurações dos Eixos", expanded=False):
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

                                            # Configurações do gráfico
                                            ax.set_title('Janela Operacional (lb/gal)', fontsize=14,
                                                         fontweight='bold')
                                            ax.set_xlabel('Gradiente (ppg)', fontsize=12)
                                            ax.set_ylabel('Profundidade (m)', fontsize=12)
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

                                            if st.session_state.leg:
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

                                            logo_path = "logo.png"
                                            if os.path.exists(logo_path):
                                                logo_img = Image.open(logo_path).resize((800, 600))
                                                logo_arr = np.array(logo_img)
                                                fig.figimage(logo_arr, xo=440, yo=500, alpha=0.25, zorder=1)
                                            plt.subplots_adjust(wspace=0.3)
                                            st.pyplot(fig)

                            # VIZUALIZAÇÃO 3D DAS TENSÕES
                            with tb[1]:
                                if not criterio_disponivel(df_tvp):
                                    st.warning(
                                        "⚠️ Insira os dados direcionais e calcule as tensões antes de avaliar o critério de falha.")
                                if criterio_disponivel(df_tvp):
                                    if "fs" not in st.session_state:
                                        st.session_state.fs = 0.5
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
                                    sig_h = linha['Sh (lb/gal)'] * 0.1704 * tvd
                                    sig_H = linha['SH (lb/gal)'] * 0.1704 * tvd
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
                                if not criterio_disponivel(df_tvp):
                                    st.warning(
                                        "⚠️ Insira os dados direcionais e calcule as tensões antes de avaliar o critério de falha.")
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

                        # except Exception as e:
                        #     st.exception(e)
                        else:
                            st.error('Preencha corretamente a aba "Gradiente de Pressão de Poros"', icon="🚨")


                    else:
                        st.error('Preencha corretamente a aba "Gradiente de Sobrecarga"', icon="🚨")
                else:
                    st.error('Por favor, insira um documento!', icon="🚨")

    # Informações Gerais
    with tabs[5]:
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
