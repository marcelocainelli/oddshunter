"""
Função para exibir o status da conexão MongoDB na interface
"""
import streamlit as st
from mongodb_credentials import parse_mongodb_atlas_uri, mask_mongodb_uri
# Verificar se existe uma função display_mongodb_status em mongodb_credentials
# para evitar conflito de importação
try:
    from mongodb_credentials import display_mongodb_status as _legacy_display_mongodb_status
    HAS_LEGACY_DISPLAY = True
except ImportError:
    HAS_LEGACY_DISPLAY = False

def display_mongodb_status(uri):
    """
    Exibe um indicador visual do status da conexão MongoDB com informações de segurança
    
    Args:
        uri: URI do MongoDB
    """
    is_atlas = "mongodb+srv://" in uri
    components = parse_mongodb_atlas_uri(uri) if is_atlas else {}
    
    # Criar um container com borda para destacar as informações
    with st.container():
        st.markdown("---")
        st.markdown("### Status da Conexão")
        
        # Exibir o tipo de conexão com formato colorido
        if is_atlas:
            st.markdown(f"<h4 style='color:#3366ff;'>MongoDB Atlas</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='color:#33cc33;'>MongoDB Local</h4>", unsafe_allow_html=True)
        
        # Para MongoDB Atlas, mostrar informações adicionais de forma segura
        if is_atlas and components["host"]:
            # Exibir informações do host
            st.markdown(f"**Servidor:** {components['host']}")
            
            # Exibir nome de usuário mascarado se existir
            if components["username"]:
                masked_username = "*" * len(components["username"])
                st.markdown(f"**Usuário:** {masked_username}")
            
            # Exibir banco de dados se configurado
            if components["database"]:
                st.markdown(f"**Database:** {components['database']}")
            
            # Mostrar opções importantes de forma organizada
            if components["options"]:
                important_options = {
                    "retryWrites": "Retry de escritas",
                    "w": "Nível de consistência",
                    "maxPoolSize": "Tamanho do pool",
                    "readPreference": "Preferência de leitura"
                }
                
                options_found = []
                for key, label in important_options.items():
                    if key in components["options"]:
                        options_found.append(f"**{label}:** {components['options'][key]}")
                
                if options_found:
                    st.markdown("**Configurações:**")
                    for option in options_found:
                        st.markdown(f"- {option}")
              # Exibir a URI mascarada para referência
            masked_uri = mask_mongodb_uri(uri)
            st.markdown("**URI Mascarada:**")
            st.code(masked_uri, language="text")
            
        # Para MongoDB local, mostrar informações básicas
        elif not is_atlas:
            # Extrair host e porta da URI local
            try:
                # Remover o prefixo mongodb://
                clean_uri = uri.replace("mongodb://", "")
                
                # Lidar com autenticação se presente
                if "@" in clean_uri:
                    # Tem autenticação
                    auth_part, server_part = clean_uri.split("@")
                    # Mascarar as credenciais
                    masked_auth = "******:******"
                    # Extrair host/porta
                    if "/" in server_part:
                        host_port, _ = server_part.split("/", 1)
                    else:
                        host_port = server_part
                    
                    # Exibir detalhes mascarados
                    st.markdown(f"**Servidor:** {host_port}")
                    st.markdown("**Autenticação:** Configurada")
                      # Exibir URI mascarada
                    masked_uri = f"mongodb://{masked_auth}@{server_part}"
                    st.markdown("**URI Mascarada:**")
                    st.code(masked_uri, language="text")
                else:
                    # Sem autenticação
                    if "/" in clean_uri:
                        host_port, _ = clean_uri.split("/", 1)
                    else:
                        host_port = clean_uri
                    st.markdown(f"**Servidor:** {host_port}")
                    st.markdown("**Autenticação:** Não configurada")
                    
                    # Exibir URI completa (sem credenciais para mascarar)
                    st.markdown("**URI Completa:**")
                    st.code(uri, language="text")
            except:
                # Em caso de erro ao analisar a URI local
                st.markdown(f"**URI:** Formato não reconhecido")
        
        st.markdown("---")
