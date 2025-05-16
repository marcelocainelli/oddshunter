import streamlit as st

# Configuração da página - DEVE ser o primeiro comando do Streamlit
st.set_page_config(
    layout="wide", 
    page_title="OddsHunter - Monitoramento de Odds e Arbitragem",
    initial_sidebar_state="auto",
    menu_items=None  # Remove menu items
)

import pandas as pd
import numpy as np
import math
import time
import json
import os
from datetime import datetime
import odds_api_simulator as api # Mantém o simulador de dados (mantido para compatibilidade)
from PIL import Image # Para carregar o logo
import subprocess
import pymongo
from pymongo import MongoClient
# Importar utilitários de MongoDB
from mongodb_utils import testar_conexao_mongodb, verificar_banco_colecao, exibir_status_conexao, exibir_status_banco_colecao
# Importar cache para MongoDB
from mongodb_cache import MongoDBCache, obter_dados_com_cache
# Importar módulo de credenciais seguras
from mongodb_credentials import mask_mongodb_uri, get_mongodb_atlas_uri, set_mongodb_atlas_uri
from mongodb_display import display_mongodb_status
from mongodb_atlas_validator import validate_mongodb_atlas_uri, provide_atlas_uri_guidance
from security_check import check_for_exposed_credentials, display_security_recommendations
from env_manager import display_environment_variables, get_environment_variable_status, set_temp_environment_variable
from mongodb_default_config import (
    DEFAULT_MONGODB_ATLAS_URI, 
    DEFAULT_MONGODB_DATABASE, 
    DEFAULT_MONGODB_COLLECTION,
    DEFAULT_MONGODB_CONNECT_TIMEOUT,
    DEFAULT_MONGODB_SERVER_SELECTION_TIMEOUT,
    DEFAULT_MONGODB_MAX_RETRIES
)


# Esconder o rodapé padrão do Streamlit e o ícone "Hosted with Streamlit"
hide_streamlit_style = """
<style>
/* Esconder elementos padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden !important;}
footer:after {
    content:'OddsHunter © 2025'; 
    visibility: visible;
    display: block;
    position: relative;
    padding: 5px;
    top: 2px;
    color: #0A2239;
}

/* Esconder TODOS os possíveis elementos de branding do Streamlit */
/* Abordagem geral para ocultar o badge "Hosted with Streamlit" */
.viewerBadge_container__1QSob {display: none !important;}
.viewerBadge_link__1S137 {display: none !important;}
._profilePreview_gzau3_63 {display: none !important;}
div[data-testid="stProfilePreview"] {display: none !important;}
div[class*="ProfilePreview"] {display: none !important;}
div[class*="viewerBadge"] {display: none !important;}
div[class*="stBadge"] {display: none !important;}
a[class*="viewerBadge"] {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
div[class*="streamlit-footer"] {display: none !important;}
div[class*="profilePreview"] {display: none !important;}
div[class*="stHeader"] {display: none !important;}
.streamlit-container {padding-bottom: 0px !important;}
.stDeployButton {display: none !important;}
#stConnectionStatus {bottom: 4px !important;}

/* Ocultar ícones específicos do canto inferior direito */
section[data-testid="stSidebar"] div[data-testid="stImage"] {display: none !important;}
img[alt="Streamlit logo"] {display: none !important;}
div[class*="stSidebarHosted"] {display: none !important;}
.styles_hostHideSmall__1esSw {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Identidade Visual OddsHunter ---
LOGO_PATH = "logo_oddshunter_v1.png"  # Caminho relativo para o Streamlit Cloud
COR_PRIMARIA_AZUL = "#0A2239"
COR_SECUNDARIA_VERDE = "#2A7A7B"
COR_DESTAQUE_DOURADO = "#E6A12E"
COR_TEXTO_BRANCO = "#FFFFFF"
COR_TEXTO_CINZA_CLARO = "#F0F0F0"
COR_TEXTO_CINZA_ESCURO = "#333333"

# --- MongoDB Settings ---
# Verificar se há URI salva na sessão ou usar padrão
if 'MONGODB_ATLAS_URI' not in st.session_state:
    # Inicializar com o valor de ambiente, sessão ou padrão
    # A função get_mongodb_atlas_uri já retorna a URI padrão se não houver configuração
    atlas_uri = get_mongodb_atlas_uri()
    set_mongodb_atlas_uri(atlas_uri)

# Verificar segurança das credenciais
security_check_result = check_for_exposed_credentials(show_warning=False)

MONGODB_URI = get_mongodb_atlas_uri()  # Obtém a URI de forma segura
MONGODB_DATABASE = DEFAULT_MONGODB_DATABASE
MONGODB_COLLECTION = DEFAULT_MONGODB_COLLECTION
MONGODB_CONNECT_TIMEOUT = DEFAULT_MONGODB_CONNECT_TIMEOUT
MONGODB_SERVER_SELECTION_TIMEOUT = DEFAULT_MONGODB_SERVER_SELECTION_TIMEOUT
MONGODB_MAX_RETRIES = DEFAULT_MONGODB_MAX_RETRIES

# Funções do arbitrage_calculator.py integradas aqui para o protótipo
def calcular_probabilidade_implicita(odds):
    if odds <= 0:
        return float('inf')
    return 1 / odds

def verificar_arbitragem_2_vias(odds_r1_casaA, nome_casaA, nome_r1, odds_r2_casaB, nome_casaB, nome_r2, investimento_total=100):
    prob_impl_r1 = calcular_probabilidade_implicita(odds_r1_casaA)
    prob_impl_r2 = calcular_probabilidade_implicita(odds_r2_casaB)
    soma_probabilidades = prob_impl_r1 + prob_impl_r2

    if soma_probabilidades < 1:
        lucro_percentual = (1 - soma_probabilidades) * 100
        retorno_garantido = investimento_total / soma_probabilidades
        stake1 = retorno_garantido / odds_r1_casaA
        stake2 = retorno_garantido / odds_r2_casaB
        investimento_real_total = stake1 + stake2

        return {
            "tipo_mercado": "2-vias",
            "oportunidade": True,
            "soma_probabilidades_implicitas": soma_probabilidades,
            "lucro_percentual_garantido": lucro_percentual,
            "detalhes_apostas": [
                {"casa": nome_casaA, "resultado": nome_r1, "odd": odds_r1_casaA, "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1_casaA},
                {"casa": nome_casaB, "resultado": nome_r2, "odd": odds_r2_casaB, "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2_casaB}
            ],
            "investimento_total_sugerido": investimento_real_total,
            "retorno_garantido": retorno_garantido
        }
    return None

def verificar_arbitragem_3_vias(odds_r1_casaA, nome_casaA, nome_r1, odds_r2_casaB, nome_casaB, nome_r2, odds_r3_casaC, nome_casaC, nome_r3, investimento_total=100):
    prob_impl_r1 = calcular_probabilidade_implicita(odds_r1_casaA)
    prob_impl_r2 = calcular_probabilidade_implicita(odds_r2_casaB)
    prob_impl_r3 = calcular_probabilidade_implicita(odds_r3_casaC)
    soma_probabilidades = prob_impl_r1 + prob_impl_r2 + prob_impl_r3

    if soma_probabilidades < 1:
        lucro_percentual = (1 - soma_probabilidades) * 100
        retorno_garantido = investimento_total / soma_probabilidades
        stake1 = retorno_garantido / odds_r1_casaA
        stake2 = retorno_garantido / odds_r2_casaB
        stake3 = retorno_garantido / odds_r3_casaC
        investimento_real_total = stake1 + stake2 + stake3

        return {
            "tipo_mercado": "3-vias",
            "oportunidade": True,
            "soma_probabilidades_implicitas": soma_probabilidades,
            "lucro_percentual_garantido": lucro_percentual,
            "detalhes_apostas": [
                {"casa": nome_casaA, "resultado": nome_r1, "odd": odds_r1_casaA, "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1_casaA},
                {"casa": nome_casaB, "resultado": nome_r2, "odd": odds_r2_casaB, "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2_casaB},
                {"casa": nome_casaC, "resultado": nome_r3, "odd": odds_r3_casaC, "stake_sugerido": stake3, "retorno_individual": stake3 * odds_r3_casaC}
            ],
            "investimento_total_sugerido": investimento_real_total,
            "retorno_garantido": retorno_garantido
        }
    return None

def encontrar_oportunidades_arbitragem_reais(dados_odds_api, investimento_desejado):
    oportunidades = []
    for evento_data in dados_odds_api:
        id_evento = evento_data["id_evento"]
        descricao_evento = evento_data["descricao_evento"]
        esporte = evento_data["esporte"]
        liga = evento_data["liga"]
        if not evento_data["odds_por_casa"]: continue
        primeiro_conjunto_odds = evento_data["odds_por_casa"][0]["odds"]
        resultados_possiveis = list(primeiro_conjunto_odds.keys())
        tipo_mercado = "3-vias" if len(resultados_possiveis) == 3 else "2-vias"
        melhores_odds = {}
        casas_melhores_odds = {}
        for resultado in resultados_possiveis:
            melhor_odd = 0
            casa_melhor_odd = None
            for casa_odds in evento_data["odds_por_casa"]:
                if resultado in casa_odds["odds"] and casa_odds["odds"][resultado] > melhor_odd:
                    melhor_odd = casa_odds["odds"][resultado]
                    casa_melhor_odd = casa_odds["nome_casa"]
            if melhor_odd > 0:
                melhores_odds[resultado] = melhor_odd
                casas_melhores_odds[resultado] = casa_melhor_odd
        if len(melhores_odds) != len(resultados_possiveis): continue
        if tipo_mercado == "2-vias" and len(resultados_possiveis) == 2:
            r1, r2 = resultados_possiveis
            oportunidade = verificar_arbitragem_2_vias(
                melhores_odds[r1], casas_melhores_odds[r1], r1,
                melhores_odds[r2], casas_melhores_odds[r2], r2,
                investimento_total=investimento_desejado)
            if oportunidade:
                oportunidade.update({"id_evento": id_evento, "descricao_evento": descricao_evento, "esporte": esporte, "liga": liga, "timestamp": time.time()})
                oportunidades.append(oportunidade)
        elif tipo_mercado == "3-vias" and len(resultados_possiveis) == 3:
            r1, r2, r3 = resultados_possiveis
            oportunidade = verificar_arbitragem_3_vias(
                melhores_odds[r1], casas_melhores_odds[r1], r1,
                melhores_odds[r2], casas_melhores_odds[r2], r2,
                melhores_odds[r3], casas_melhores_odds[r3], r3,
                investimento_total=investimento_desejado)
            if oportunidade:
                oportunidade.update({"id_evento": id_evento, "descricao_evento": descricao_evento, "esporte": esporte, "liga": liga, "timestamp": time.time()})
                oportunidades.append(oportunidade)
    return oportunidades

# --- MongoDB Integration ---
def conectar_mongodb():
    """Estabelece conexão com o MongoDB e retorna o cliente de conexão com retry logic"""
    retry_count = 0
    # Obter a URI atual de forma segura
    current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
    
    # Detectar se é uma conexão Atlas
    is_atlas = "mongodb+srv://" in current_uri
    
    while retry_count < MONGODB_MAX_RETRIES:
        try:
            # Configurar opções de cliente
            client_options = {
                "connectTimeoutMS": MONGODB_CONNECT_TIMEOUT,
                "serverSelectionTimeoutMS": MONGODB_SERVER_SELECTION_TIMEOUT
            }
            
            # Adicionar opções específicas para MongoDB Atlas
            if is_atlas:
                client_options.update({
                    "retryWrites": True,
                    "w": "majority",
                    "retryReads": True
                })
            
            # Configurar a conexão com as opções
            client = MongoClient(current_uri, **client_options)
            
            # Verificar a conexão tentando obter informações do servidor
            # Isso falha rapidamente se o servidor não estiver acessível
            client.server_info()
            return client
            
        except pymongo.errors.ServerSelectionTimeoutError as e:
            retry_count += 1
            if retry_count >= MONGODB_MAX_RETRIES:
                st.error(f"Erro ao conectar ao MongoDB após {MONGODB_MAX_RETRIES} tentativas: {e}")
                if is_atlas:
                    st.info("Verifique se suas credenciais do MongoDB Atlas estão corretas e se sua rede permite conexões.")
                else:
                    st.info("Verifique se o servidor MongoDB está rodando e acessível no endereço configurado.")
                return None
            else:
                st.warning(f"Tentativa {retry_count} de conectar ao MongoDB falhou. Tentando novamente...")
                time.sleep(1)  # Esperar 1 segundo antes de tentar novamente
                
        except pymongo.errors.OperationFailure as e:
            st.error(f"Falha de autenticação: {e}")
            st.info("Verifique usuário e senha do MongoDB.")
            return None
                
        except Exception as e:
            st.error(f"Erro desconhecido ao conectar ao MongoDB: {e}")
            st.info("Verifique sua configuração de MongoDB e suas credenciais.")
            return None
    
    return None

def obter_dados_mongodb():
    """Obtém dados da coleção definida nas configurações com melhor tratamento de erros"""
    client = conectar_mongodb()
    if client:
        try:
            db = client[MONGODB_DATABASE]
            collection = db[MONGODB_COLLECTION]
            
            # Obter a URI atual de forma segura
            current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
            
            # Detectar se é MongoDB Atlas
            is_atlas = "mongodb+srv://" in current_uri
            
            # Executar a consulta com opções específicas para Atlas ou local
            if is_atlas:
                # Para Atlas, podemos usar opções mais específicas
                dados = list(collection.find().limit(1000))  # Limitar quantidade para performance
            else:
                # Para MongoDB local
                dados = list(collection.find())
                
            client.close()
            
            # Verificar se encontrou dados
            if not dados:
                if is_atlas:
                    st.warning(f"A coleção '{MONGODB_COLLECTION}' no banco '{MONGODB_DATABASE}' do MongoDB Atlas está vazia.")
                else:
                    st.warning(f"A coleção '{MONGODB_COLLECTION}' no banco '{MONGODB_DATABASE}' está vazia.")
            
            # Se temos dados, fazer um backup em CSV
            if dados:
                try:
                    from mongodb_cache import salvar_dados_csv_backup
                    salvar_dados_csv_backup(dados, "mongodb_backup.csv")
                except:
                    pass  # Não interromper se o backup falhar
            
            return dados
            
        except pymongo.errors.OperationFailure as e:
            st.error(f"Erro de operação no MongoDB: {e}")
            st.info("Verifique se você tem permissões para acessar este banco de dados e coleção.")
            client.close()
        except Exception as e:
            st.error(f"Erro ao obter dados do MongoDB: {e}")
            client.close()
    
    # Fallback: Tentar usar o CSV local
    try:
        st.warning("Tentando usar dados locais de CSV como fallback...")
        # Tentar primeiro o backup gerado pelo MongoDB
        csv_file = "mongodb_backup.csv"
        if not os.path.exists(csv_file):
            csv_file = "surebets_oddspedia.csv"  # Fallback para o CSV original
            
        df = pd.read_csv(csv_file)
        if not df.empty:
            # Converter DataFrame para formato similar ao MongoDB
            dados_fallback = df.to_dict('records')
            st.success(f"Usando {len(dados_fallback)} registros de dados locais de {csv_file}.")
            return dados_fallback
    except Exception as e:
        st.error(f"Também não foi possível carregar dados de fallback: {e}")
    
    return []

def processar_oportunidades_mongodb(dados_mongodb, investimento_desejado=100):
    """Processa os dados do MongoDB e retorna oportunidades formatadas com melhor tratamento de erros"""
    oportunidades = []
    registros_com_erro = 0
    
    for item in dados_mongodb:
        try:
            # Verifica se há odds válidas para pelo menos 2 resultados
            if not item.get('odd_1') or not item.get('odd_2'):
                continue
                
            tipo_mercado = "3-vias" if item.get('odd_3') else "2-vias"
            lucro_percentual = item.get('lucro_percentual', 0)
            
            # Converter odds de string para float com tratamento de erros
            try:
                # Normalizar diferentes formatos (vírgula/ponto como separador decimal)
                odds_r1 = float(str(item.get('odd_1', '0')).replace(',', '.'))
                odds_r2 = float(str(item.get('odd_2', '0')).replace(',', '.'))
                odds_r3 = float(str(item.get('odd_3', '0')).replace(',', '.')) if item.get('odd_3') else 0
            except (ValueError, TypeError):
                registros_com_erro += 1
                continue
                
            # Pular registros com odds inválidas
            if odds_r1 <= 1 or odds_r2 <= 1 or (tipo_mercado == "3-vias" and odds_r3 <= 1):
                continue
                
            # Calcular probabilidades implícitas
            prob_impl_r1 = calcular_probabilidade_implicita(odds_r1)
            prob_impl_r2 = calcular_probabilidade_implicita(odds_r2)
            prob_impl_r3 = calcular_probabilidade_implicita(odds_r3) if tipo_mercado == "3-vias" else 0
            
            soma_probabilidades = prob_impl_r1 + prob_impl_r2
            if tipo_mercado == "3-vias":
                soma_probabilidades += prob_impl_r3
                
            if soma_probabilidades < 1:
                retorno_garantido = investimento_desejado / soma_probabilidades
                stake1 = retorno_garantido / odds_r1
                stake2 = retorno_garantido / odds_r2
                
                if tipo_mercado == "2-vias":
                    investimento_real_total = stake1 + stake2
                    nomes_resultados = item.get('linha', 'Casa/Fora').split('/')
                    if len(nomes_resultados) < 2:
                        nomes_resultados = ['Casa', 'Fora']  # Padrão se não tiver informação
                        
                    oportunidade = {
                        "tipo_mercado": tipo_mercado,
                        "oportunidade": True,
                        "soma_probabilidades_implicitas": soma_probabilidades,
                        "lucro_percentual_garantido": float(lucro_percentual) if isinstance(lucro_percentual, (int, float, str)) else 0,
                        "detalhes_apostas": [
                            {"casa": item.get('casa_1', ''), "resultado": nomes_resultados[0], "odd": odds_r1, 
                             "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1},
                            {"casa": item.get('casa_2', ''), "resultado": nomes_resultados[1], "odd": odds_r2, 
                             "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2}
                        ],
                        "investimento_total_sugerido": investimento_real_total,
                        "retorno_garantido": retorno_garantido,
                        "id_evento": str(item.get('_id', '')),
                        "descricao_evento": item.get('evento', item.get('times', '')),
                        "esporte": item.get('esporte', ''),
                        "liga": item.get('liga', ''),
                        "timestamp": time.time(),
                        "data_hora_evento": item.get('data_hora', ''),
                        "data_extracao": item.get('data_extracao', datetime.now())
                    }
                    oportunidades.append(oportunidade)
                
                elif tipo_mercado == "3-vias":
                    stake3 = retorno_garantido / odds_r3
                    investimento_real_total = stake1 + stake2 + stake3
                    nomes_resultados = item.get('linha', 'Casa/Empate/Fora').split('/')
                    if len(nomes_resultados) < 3:
                        nomes_resultados = ['Casa', 'Empate', 'Fora']  # Padrão se não tiver informação
                    
                    oportunidade = {
                        "tipo_mercado": tipo_mercado,
                        "oportunidade": True,
                        "soma_probabilidades_implicitas": soma_probabilidades,
                        "lucro_percentual_garantido": float(lucro_percentual) if isinstance(lucro_percentual, (int, float, str)) else 0,
                        "detalhes_apostas": [
                            {"casa": item.get('casa_1', ''), "resultado": nomes_resultados[0], "odd": odds_r1, 
                             "stake_sugerido": stake1, "retorno_individual": stake1 * odds_r1},
                            {"casa": item.get('casa_2', ''), "resultado": nomes_resultados[1], "odd": odds_r2, 
                             "stake_sugerido": stake2, "retorno_individual": stake2 * odds_r2},
                            {"casa": item.get('casa_3', ''), "resultado": nomes_resultados[2], "odd": odds_r3, 
                             "stake_sugerido": stake3, "retorno_individual": stake3 * odds_r3}
                        ],
                        "investimento_total_sugerido": investimento_real_total,
                        "retorno_garantido": retorno_garantido,
                        "id_evento": str(item.get('_id', '')),
                        "descricao_evento": item.get('evento', item.get('times', '')),
                        "esporte": item.get('esporte', ''),
                        "liga": item.get('liga', ''),
                        "timestamp": time.time(),
                        "data_hora_evento": item.get('data_hora', ''),
                        "data_extracao": item.get('data_extracao', datetime.now())
                    }
                    oportunidades.append(oportunidade)
        except Exception as e:
            registros_com_erro += 1
            # Não mostramos o erro na UI para não poluir, mas poderia ser registrado em um log
            continue
    
    # Se houve erros, avisar discretamente
    if registros_com_erro > 0:
        st.caption(f"Nota: {registros_com_erro} registros foram ignorados devido a erros de formato.")
                
    return oportunidades

def mostrar_detalhes_oportunidade(oportunidade):
    """Mostra detalhes de uma oportunidade específica"""
    st.markdown(f"<h3 style='color:{COR_SECUNDARIA_VERDE};'>🎯 {oportunidade['descricao_evento']} ({oportunidade['esporte']} - {oportunidade['liga']})</h3>", unsafe_allow_html=True)
    
    # Informações de horário e data
    if 'data_hora_evento' in oportunidade and oportunidade['data_hora_evento']:
        st.markdown(f"**Data e Hora do Evento:** {oportunidade['data_hora_evento']}")
    
    # Informações principais
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Lucro Garantido:** <span class='lucro-destaque'>{oportunidade['lucro_percentual_garantido']:.2f}%</span>", unsafe_allow_html=True)
        st.markdown(f"**Investimento Sugerido:** R$ {oportunidade['investimento_total_sugerido']:.2f}")
    with col2:
        st.markdown(f"**Retorno Garantido:** R$ {oportunidade['retorno_garantido']:.2f}")
        st.markdown(f"**Soma Probabilidades:** {oportunidade['soma_probabilidades_implicitas']:.4f}")
    
    # Detalhes das apostas
    st.markdown("**Detalhes das Apostas Sugeridas:**")
    detalhes_df = pd.DataFrame(oportunidade['detalhes_apostas'])
    detalhes_df_display = detalhes_df[['casa', 'resultado', 'odd', 'stake_sugerido', 'retorno_individual']]
    detalhes_df_display['stake_sugerido'] = detalhes_df_display['stake_sugerido'].map(lambda x: f"R$ {x:.2f}")
    detalhes_df_display['retorno_individual'] = detalhes_df_display['retorno_individual'].map(lambda x: f"R$ {x:.2f}")
    detalhes_df_display.rename(columns={'casa': 'Casa', 'resultado': 'Apostar em', 'odd': 'Odd', 'stake_sugerido': 'Stake', 'retorno_individual': 'Retorno'}, inplace=True)
    st.table(detalhes_df_display.set_index('Casa'))
    
    # Adicionar informações de tempo de extração
    if 'data_extracao' in oportunidade and oportunidade['data_extracao']:
        st.caption(f"Dados extraídos em: {oportunidade['data_extracao']}")
    
    st.divider()

# Tentar conectar ao MongoDB Atlas logo na inicialização
try:
    client = conectar_mongodb()
    if client:
        st.session_state.mongodb_status = True
        # Fechar a conexão após o teste inicial
        client.close()
    else:
        st.session_state.mongodb_status = False
except Exception as e:
    st.session_state.mongodb_status = False
    
# Registrar o timestamp da verificação
st.session_state.last_mongo_check = time.time()

# Aplicar CSS customizado para cores e fontes (básico)
# Idealmente, usaríamos um config.toml para temas mais completos, mas para uma demo rápida:
st.markdown(f"""
<style>
    .stApp {{
        background-color: {COR_PRIMARIA_AZUL};
        color: {COR_TEXTO_CINZA_CLARO};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {COR_TEXTO_BRANCO}; 
    }}
    .stButton>button {{
        background-color: {COR_SECUNDARIA_VERDE};
        color: {COR_TEXTO_BRANCO};
        border-radius: 5px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {COR_DESTAQUE_DOURADO};
        color: {COR_PRIMARIA_AZUL};
    }}
    .stMarkdown {{ color: {COR_TEXTO_CINZA_CLARO}; }}
    .stDataFrame {{ color: {COR_TEXTO_CINZA_ESCURO}; }}
    .stTable {{ color: {COR_TEXTO_CINZA_ESCURO}; }}
    /* Para destacar o lucro com a cor de destaque */
    .lucro-destaque {{
        color: {COR_DESTAQUE_DOURADO};
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# Logo e Título
col_logo1, col_logo2 = st.columns([1, 5])
with col_logo1:
    try:
        logo_image = Image.open(LOGO_PATH)
        st.image(logo_image, width=100)
    except FileNotFoundError:
        st.error("Logo não encontrado.")
with col_logo2:
    st.markdown(f"<h1 style='color:{COR_TEXTO_BRANCO};'>OddsHunter</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COR_SECUNDARIA_VERDE}; font-size: 1.1em;'>Monitoramento Inteligente de Odds e Arbitragem</p>", unsafe_allow_html=True)

st.caption("Versão com Integração MongoDB - Dados de arbitragem em tempo real")

# Sidebar para configurações
st.sidebar.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>⚙️ Configurações</h2>", unsafe_allow_html=True)
investimento_usuario = st.sidebar.number_input("Valor Total para Investir (R$):", min_value=10.0, value=100.0, step=10.0)
auto_refresh = st.sidebar.checkbox("Atualização Automática", value=True)
refresh_interval = st.sidebar.slider("Intervalo de Atualização (s):", min_value=5, max_value=60, value=15, step=5)
limiar_lucro = st.sidebar.slider("Limiar Mínimo de Lucro (%):", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

# Cache e controle de dados
with st.sidebar.expander("Controle de Cache"):
    st.markdown("#### Cache de Dados MongoDB")
    
    # Mostrar status atual do cache
    if 'mongodb_cache' in st.session_state:
        cache = st.session_state.mongodb_cache
        if cache.is_valid():
            st.success("Cache válido")
            st.info(f"Idade do cache: {cache.get_age_seconds() / 60:.1f} minutos")
        else:
            st.warning("Cache expirado ou vazio")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Limpar Cache"):
                cache.invalidate()
                st.success("Cache invalidado!")
                st.session_state.data_source = "sem dados"
                st.experimental_rerun()
        
        with col2:
            # Permitir ajustar o tempo de validade do cache
            tempo_cache = st.number_input(
                "Validade (min)", 
                value=cache.max_age_seconds // 60,
                min_value=1,
                max_value=60,
                step=5
            )
            cache.max_age_seconds = tempo_cache * 60  # Converter para segundos

# Configurações MongoDB (colapsado por padrão)
with st.sidebar.expander("Configurações do MongoDB"):
    # Tipo de conexão
    connection_type = st.radio(
        "Tipo de Conexão:", 
        ["MongoDB Atlas", "MongoDB Local"],
        index=0 if "mongodb+srv://" in MONGODB_URI else 1
    )
    
    if connection_type == "MongoDB Atlas":
        # Configuração MongoDB Atlas - usando sistema seguro de credenciais
        st.markdown("#### Configuração MongoDB Atlas")
        
        # Mostrar URI atual de forma mascarada
        masked_uri = mask_mongodb_uri(get_mongodb_atlas_uri())
        st.info(f"URI atual: {masked_uri}")
        # Campo para nova URI com tipo password
        new_uri = st.text_input(
            "Nova MongoDB Atlas URI:",
            value="",
            type="password",
            placeholder="mongodb+srv://usuário:senha@cluster.exemplo.mongodb.net/?opções"
        )
        if new_uri:
            if new_uri.startswith("mongodb+srv://"):
                # Validar a URI antes de aplicar
                validation_result = validate_mongodb_atlas_uri(new_uri, test_connection=True)
                
                if validation_result["valido"]:
                    # Atualizar a URI apenas se for válida
                    set_mongodb_atlas_uri(new_uri)
                    st.success("URI do MongoDB Atlas atualizada com sucesso!")
                    # Atualizar a variável global também
                    MONGODB_URI = new_uri
                else:                    # Mostrar erro de validação
                    st.error(f"URI inválida: {validation_result['mensagem']}")
                    if "erro_detalhes" in validation_result and validation_result["erro_detalhes"]:
                        st.markdown("#### Detalhes do erro")
                        st.code(validation_result["erro_detalhes"])
            else:
                st.error("A URI deve começar com 'mongodb+srv://' para o MongoDB Atlas")
                # Mostrar ajuda para configuração do MongoDB Atlas
        st.markdown("#### Ajuda para configurar MongoDB Atlas")
        provide_atlas_uri_guidance()
              # Mostrar link para documentação detalhada
        st.markdown("[📄 Consulte a documentação completa de segurança](mongodb_atlas_setup.md)")
        
        st.caption("A URI do MongoDB Atlas inclui usuário, senha e configurações de conexão")
          # Mostrar informações da conexão atual de forma segura
        display_mongodb_status(MONGODB_URI)
          # Configurações avançadas colapsadas
        st.markdown("#### Configurações Avançadas Atlas")
        mongodb_db = st.text_input("Database:", value=MONGODB_DATABASE)
        mongodb_collection = st.text_input("Collection:", value=MONGODB_COLLECTION)
        mongodb_timeout = st.number_input("Timeout (ms):", value=MONGODB_CONNECT_TIMEOUT, min_value=1000, step=1000)
        mongodb_max_retries = st.number_input("Máx. Tentativas:", value=MONGODB_MAX_RETRIES, min_value=1, max_value=10, step=1)
    else:
        # Configuração MongoDB Local
        mongodb_host = st.text_input("Host MongoDB:", value="localhost")
        mongodb_porta = st.number_input("Porta MongoDB:", value=27017, min_value=1, max_value=65535)
          # Autenticação (opcional)
        usar_autenticacao = st.checkbox("Usar Autenticação", value=False)
        if usar_autenticacao:
            col1_auth, col2_auth = st.columns(2)
            with col1_auth:
                mongodb_usuario = st.text_input("Usuário:", placeholder="usuário")
            with col2_auth:
                mongodb_senha = st.text_input("Senha:", type="password", placeholder="senha")
            mongodb_auth_db = st.text_input("Banco de Auth:", value="admin", placeholder="admin")
        # Configurações avançadas
        st.markdown("#### Configurações Avançadas Local")
        mongodb_db = st.text_input("Database:", value=MONGODB_DATABASE)
        mongodb_collection = st.text_input("Collection:", value=MONGODB_COLLECTION)
        mongodb_timeout = st.number_input("Timeout (ms):", value=MONGODB_CONNECT_TIMEOUT, min_value=1000, step=1000)
        mongodb_max_retries = st.number_input("Máx. Tentativas:", value=MONGODB_MAX_RETRIES, min_value=1, max_value=10, step=1)
        
        # Construir URI baseada nas configurações locais
        if usar_autenticacao:
            from mongodb_utils import construir_uri_mongodb
            mongodb_uri = construir_uri_mongodb(
                mongodb_host, 
                mongodb_porta, 
                mongodb_usuario if usar_autenticacao else None,
                mongodb_senha if usar_autenticacao else None,
                mongodb_auth_db if usar_autenticacao else None
            )
        else:
            mongodb_uri = f"mongodb://{mongodb_host}:{mongodb_porta}/"
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Atualizar Configurações"):
            # Atualizar as configurações globais
            if connection_type == "MongoDB Atlas":
                # Usando a URI já atualizada via set_mongodb_atlas_uri
                MONGODB_URI = get_mongodb_atlas_uri()
            else:
                # URI do MongoDB local
                MONGODB_URI = mongodb_uri
            
            MONGODB_DATABASE = mongodb_db
            MONGODB_COLLECTION = mongodb_collection
            MONGODB_CONNECT_TIMEOUT = mongodb_timeout
            MONGODB_SERVER_SELECTION_TIMEOUT = mongodb_timeout
            MONGODB_MAX_RETRIES = mongodb_max_retries
            
            st.success("Configurações atualizadas com sucesso!")
            
            # Mostrar a URI gerada de forma segura
            if connection_type == "MongoDB Atlas":
                st.info(f"URI: {mask_mongodb_uri(MONGODB_URI)}")
            else:
                # Mascarar senha se houver autenticação
                if usar_autenticacao and mongodb_senha:
                    uri_masked = mongodb_uri.replace(mongodb_senha, "*" * len(mongodb_senha))
                    st.info(f"URI: {uri_masked}")                
                else:
                    st.info(f"URI: {mongodb_uri}")
    
    with col2:
        if st.button("Testar Conexão"):
            with st.spinner("Testando conexão..."):
                # Obter a URI correta com base no tipo de conexão
                uri_to_test = get_mongodb_atlas_uri() if connection_type == "MongoDB Atlas" else mongodb_uri
                
                # Para MongoDB Atlas, usar nosso validador avançado
                if connection_type == "MongoDB Atlas":
                    validation_result = validate_mongodb_atlas_uri(uri_to_test, test_connection=True, timeout=mongodb_timeout)
                    
                    if validation_result["valido"]:
                        st.success(f"✅ {validation_result['mensagem']}")
                        
                        # Se a validação básica passar, verificar banco e coleção
                        resultado_verificacao = verificar_banco_colecao(
                            uri_to_test,                            mongodb_db,
                            mongodb_collection,
                            connect_timeout=mongodb_timeout,
                            server_selection_timeout=mongodb_timeout
                        )
                        exibir_status_banco_colecao(resultado_verificacao)
                    else:
                        st.error(f"❌ {validation_result['mensagem']}")
                        if validation_result.get("erro_detalhes"):
                            st.markdown("#### Detalhes do erro")
                            st.code(validation_result["erro_detalhes"])
                # Para MongoDB local, usar o fluxo normal
                else:
                    # Testar conexão básica
                    resultado_teste = testar_conexao_mongodb(
                        uri_to_test, 
                        connect_timeout=mongodb_timeout,
                        server_selection_timeout=mongodb_timeout
                    )
                    exibir_status_conexao(resultado_teste)
                    
                    # Se a conexão básica funcionar, verificar banco e coleção
                    if resultado_teste["status"]:
                        resultado_verificacao = verificar_banco_colecao(
                            uri_to_test,
                            mongodb_db,
                            mongodb_collection,
                            connect_timeout=mongodb_timeout,
                            server_selection_timeout=mongodb_timeout
                        )
                        exibir_status_banco_colecao(resultado_verificacao)

# Botão para atualização manual
col1_main, col2_main, col3_main = st.columns([3, 1, 1])
with col1_main:
    st.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Dados de Odds do MongoDB em Tempo Real</h3>", unsafe_allow_html=True)
with col2_main:
    manual_refresh = st.button("Atualizar Agora")
with col3_main:
    # Verificação rápida do status do MongoDB para o indicador
    if 'mongodb_status' not in st.session_state:
        st.session_state.mongodb_status = False
    
    # Executamos a verificação apenas periodicamente para não sobrecarregar
    if time.time() - st.session_state.get('last_mongo_check', 0) > 60:  # verificar a cada 60 segundos
        try:
            # Obter a URI atual de forma segura
            current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
            
            # Verificação rápida sem mostrar erros na UI
            cliente = MongoClient(
                current_uri,
                connectTimeoutMS=2000,  # timeout mais curto para ser rápido
                serverSelectionTimeoutMS=2000
            )
            cliente.server_info()
            st.session_state.mongodb_status = True
            cliente.close()
        except:
            st.session_state.mongodb_status = False
        st.session_state.last_mongo_check = time.time()
    
    # Mostrar o indicador de status
    is_atlas = "mongodb+srv://" in MONGODB_URI
    connection_type = "MongoDB Atlas" if is_atlas else "MongoDB Local"
    
    if st.session_state.mongodb_status:
        st.markdown(f"<h5 style='color:{COR_SECUNDARIA_VERDE};'>●</h5> {connection_type} Conectado", unsafe_allow_html=True)
    else:
        st.markdown(f"<h5 style='color:red;'>●</h5> {connection_type} Desconectado", unsafe_allow_html=True)

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0
if 'odds_data' not in st.session_state:
    st.session_state.odds_data = None
if 'oportunidades' not in st.session_state:
    st.session_state.oportunidades = []
if 'mongodb_cache' not in st.session_state:
    # Inicializar cache do MongoDB (válido por 30 minutos)
    st.session_state.mongodb_cache = MongoDBCache(max_age_seconds=1800)
if 'mongodb_status' not in st.session_state:
    st.session_state.mongodb_status = False
if 'last_mongo_check' not in st.session_state:
    st.session_state.last_mongo_check = 0
if 'data_source' not in st.session_state:
    st.session_state.data_source = "sem dados"

current_time = time.time()
should_refresh = manual_refresh or (auto_refresh and (current_time - st.session_state.last_refresh) > refresh_interval)

if should_refresh:
    with st.spinner("Carregando dados de surebets do MongoDB..."):
        try:
            # Obter dados do MongoDB com cache
            dados_mongodb, origem_dados, status = obter_dados_com_cache(
                obter_dados_mongodb,  # Função original para obter dados
                cache_instance=st.session_state.mongodb_cache,
                force_refresh=manual_refresh  # Forçar atualização apenas no botão manual
            )
            
            if status and dados_mongodb:
                # Processar os dados em oportunidades
                st.session_state.oportunidades = processar_oportunidades_mongodb(dados_mongodb, investimento_usuario)
                st.session_state.last_refresh = current_time
                st.session_state.data_source = origem_dados
                
                # Mensagem adaptativa baseada na origem dos dados
                if origem_dados == "mongodb":
                    # Obter a URI atual de forma segura
                    current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
                    
                    # Indica se é MongoDB Atlas ou local
                    is_atlas = "mongodb+srv://" in current_uri
                    mongodb_type = "MongoDB Atlas" if is_atlas else "MongoDB Local"
                    st.success(f"Dados atualizados de {mongodb_type}! {len(st.session_state.oportunidades)} oportunidades encontradas.")
                elif origem_dados == "cache":
                    # Mostrar idade do cache
                    cache_age = st.session_state.mongodb_cache.get_age_seconds() / 60  # em minutos
                    st.info(f"Usando dados em cache (de {cache_age:.1f} minutos atrás). {len(st.session_state.oportunidades)} oportunidades.")
                elif origem_dados == "backup":
                    st.warning(f"Usando dados de backup local. {len(st.session_state.oportunidades)} oportunidades.")
            else:
                st.error("Não foi possível obter dados do MongoDB, cache ou backup.")
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")
    
    # Mostrar informação sobre última atualização
    # Obter a URI atual de forma segura
    current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
    is_atlas = "mongodb+srv://" in current_uri
    db_type = "MongoDB Atlas" if is_atlas else "MongoDB"
    st.caption(f"Última atualização: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')} | Fonte: {st.session_state.data_source} ({db_type})")
elif st.session_state.oportunidades:
    # Se não estiver atualizando, mostrar de onde vieram os dados atualmente exibidos
    idade_dados = (current_time - st.session_state.last_refresh) / 60  # em minutos
    # Obter a URI atual de forma segura
    current_uri = get_mongodb_atlas_uri() if "mongodb+srv://" in MONGODB_URI else MONGODB_URI
    is_atlas = "mongodb+srv://" in current_uri
    db_type = "MongoDB Atlas" if is_atlas else "MongoDB"
    st.caption(f"Dados de {idade_dados:.1f} minutos atrás | Fonte: {st.session_state.data_source} ({db_type})")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>🚨 Oportunidades de Arbitragem</h2>", unsafe_allow_html=True)
if st.session_state.oportunidades:
    oportunidades_filtradas = [op for op in st.session_state.oportunidades if op["lucro_percentual_garantido"] >= limiar_lucro]
    if oportunidades_filtradas:
        # Criar seletor de oportunidade
        opcoes_oportunidades = [f"{op['descricao_evento']} - {op['lucro_percentual_garantido']:.2f}% ({op['esporte']})" for op in oportunidades_filtradas]
        indice_selecionado = st.selectbox("Selecione uma oportunidade para ver detalhes:", 
                                      options=range(len(opcoes_oportunidades)),
                                      format_func=lambda i: opcoes_oportunidades[i])
        
        # Mostrar detalhes da oportunidade selecionada
        mostrar_detalhes_oportunidade(oportunidades_filtradas[indice_selecionado])
        
        # Opção para mostrar todas as oportunidades
        if st.checkbox("Mostrar todas as oportunidades"):
            for op in oportunidades_filtradas:
                mostrar_detalhes_oportunidade(op)
    else:
        st.info(f"Nenhuma oportunidade de arbitragem encontrada com lucro acima de {limiar_lucro}%.")
else:
    st.warning("Aguardando dados. Clique em 'Atualizar Agora' ou aguarde a atualização automática.")

st.markdown(f"<h2 style='color:{COR_TEXTO_BRANCO};'>📊 Visualização de Dados de MongoDB</h2>", unsafe_allow_html=True)

# Obter dados brutos do MongoDB para visualização
with st.expander("Dados de Oportunidades no MongoDB"):
    try:
        dados_mongodb_raw = obter_dados_mongodb()
        if dados_mongodb_raw:
            # Converter para DataFrame para visualização
            df_mongo = pd.DataFrame(dados_mongodb_raw)
            
            # Selecionar colunas relevantes para exibição
            colunas_exibir = ['esporte', 'liga', 'evento', 'data_hora', 'linha', 
                            'odd_1', 'casa_1', 'odd_2', 'casa_2', 'odd_3', 'casa_3', 
                            'lucro_garantido', 'lucro_percentual']
            
            colunas_disponiveis = [col for col in colunas_exibir if col in df_mongo.columns]
            if colunas_disponiveis:
                df_display = df_mongo[colunas_disponiveis].copy()
                
                # Filtrar por esporte
                esportes_disponiveis = sorted(df_display['esporte'].unique().tolist())
                if esportes_disponiveis:
                    esporte_filtro = st.selectbox("Filtrar por Esporte:", options=["Todos"] + esportes_disponiveis)
                    
                    if esporte_filtro != "Todos":
                        df_display = df_display[df_display['esporte'] == esporte_filtro]
                    
                    # Exibir dados
                    st.dataframe(df_display.style.highlight_max(subset=['lucro_percentual'], 
                                                            props=f'color:{COR_TEXTO_CINZA_ESCURO}; background-color:{COR_DESTAQUE_DOURADO};'),
                                use_container_width=True)
                    
                    # Mostrar estatísticas
                    st.markdown(f"**Estatísticas de Lucro por Esporte:**")
                    df_stats = df_mongo.groupby('esporte')['lucro_percentual'].agg(['mean', 'max', 'count']).reset_index()
                    df_stats.columns = ['Esporte', 'Lucro Médio (%)', 'Lucro Máximo (%)', 'Quantidade de Oportunidades']
                    df_stats['Lucro Médio (%)'] = df_stats['Lucro Médio (%)'].map(lambda x: f"{x:.2f}%")
                    df_stats['Lucro Máximo (%)'] = df_stats['Lucro Máximo (%)'].map(lambda x: f"{x:.2f}%")
                    st.table(df_stats.set_index('Esporte'))
                    
                    # Gráfico de distribuição de lucro
                    if not df_mongo.empty and 'lucro_percentual' in df_mongo.columns:
                        st.markdown("**Distribuição de Lucro Percentual:**")
                        hist_data = df_mongo['lucro_percentual'].dropna()
                        if not hist_data.empty:
                            st.bar_chart(hist_data.value_counts(bins=10).sort_index())
                else:
                    st.warning("Não há dados de esportes disponíveis.")
            else:
                st.warning("Estrutura de dados no MongoDB não corresponde ao formato esperado.")
        else:
            st.warning("Não há dados disponíveis no MongoDB.")
    except Exception as e:
        st.error(f"Erro ao processar dados do MongoDB para visualização: {e}")

st.markdown("<hr style='border: 1px solid #2A7A7B;'>", unsafe_allow_html=True)
st.caption(f"OddsHunter v2.0 - MongoDB Integration - Desenvolvido por MDC. Dados em tempo real.")

# Adicionar informações sobre o deploy permanente
st.sidebar.markdown("---")
st.sidebar.markdown(f"<h3 style='color:{COR_TEXTO_BRANCO};'>Sobre este Deploy</h3>", unsafe_allow_html=True)
st.sidebar.markdown("Esta é uma versão 2.0 do OddsHunter com integração ao MongoDB.")
st.sidebar.markdown("Dados de oportunidades de arbitragem em tempo real.")

# Adicionar seção de segurança
with st.sidebar.expander("🔒 Segurança"):
    st.markdown("### Verificações de Segurança")
    
    # Verificar segurança novamente (mostrar na UI)
    security_result = check_for_exposed_credentials(show_warning=True)
    
    # Mostrar recomendações de segurança
    if st.checkbox("Mostrar recomendações de segurança"):
        display_security_recommendations()

# Adicionar seção de variáveis de ambiente
with st.sidebar.expander("🔑 Variáveis de Ambiente"):
    display_environment_variables()
