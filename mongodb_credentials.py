"""
Módulo para gerenciar credenciais do MongoDB Atlas de forma segura
"""
import os
import re
import streamlit as st
from urllib.parse import quote_plus

def mask_mongodb_uri(uri):
    """
    Mascara a URI do MongoDB para exibição segura,
    substituindo nome de usuário e senha com asteriscos
    
    Args:
        uri: URI original do MongoDB
        
    Returns:
        str: URI mascarada
    """
    if not uri:
        return ""
        
    # Se for uma URI do MongoDB Atlas (começa com mongodb+srv://)
    if uri.startswith("mongodb+srv://"):
        # Extrair apenas o host e parâmetros
        match = re.search(r'@([^/?]+)(.*)', uri)
        if match:
            host_part = match.group(1)
            params_part = match.group(2) if match.group(2) else ""
            return f"mongodb+srv://******:******@{host_part}{params_part}"
    
    # Se for uma URI padrão do MongoDB (começa com mongodb://)
    elif uri.startswith("mongodb://"):
        # Verificar se tem autenticação
        if '@' in uri:
            # Extrair apenas o host e parâmetros
            match = re.search(r'@([^/?]+)(.*)', uri)
            if match:
                host_part = match.group(1)
                params_part = match.group(2) if match.group(2) else ""
                return f"mongodb://******:******@{host_part}{params_part}"
        else:
            # Sem autenticação, retorna a URI como está
            return uri
    
    # Retorna a URI mascarada ou a original se não conseguir mascarar
    return uri

def get_mongodb_atlas_uri():
    """
    Obtém a URI do MongoDB Atlas de forma segura,
    verificando primeiro as variáveis de ambiente e
    depois o session_state do Streamlit
    
    Returns:
        str: URI do MongoDB Atlas
    """
    # Tentar obter da variável de ambiente (mais seguro para produção)
    env_uri = os.getenv('MONGODB_ATLAS_URI')
    if env_uri:
        return env_uri
    
    # Se não tiver na variável de ambiente, usar do session_state
    return st.session_state.get('MONGODB_ATLAS_URI', "")

def set_mongodb_atlas_uri(uri):
    """
    Define a URI do MongoDB Atlas de forma segura na session_state
    
    Args:
        uri: URI do MongoDB Atlas
    """
    st.session_state['MONGODB_ATLAS_URI'] = uri

def parse_mongodb_atlas_uri(uri):
    """
    Analisa uma URI do MongoDB Atlas e retorna seus componentes
    
    Args:
        uri: URI do MongoDB Atlas
        
    Returns:
        dict: Componentes da URI (username, password, host, etc)
    """
    components = {
        "is_atlas": False,
        "username": "",
        "password": "",
        "host": "",
        "database": "",
        "options": {}
    }
    
    if not uri:
        return components
    
    # Verificar se é uma URI do MongoDB Atlas
    components["is_atlas"] = uri.startswith("mongodb+srv://")
    
    try:
        # Extrair username e password se presentes
        if '@' in uri:
            auth_part = uri.split('@')[0]
            if '//' in auth_part:
                auth_credentials = auth_part.split('//')[1]
                if ':' in auth_credentials:
                    components["username"], components["password"] = auth_credentials.split(':', 1)
        
        # Extrair host
        if '@' in uri:
            host_part = uri.split('@')[1]
            if '/' in host_part:
                components["host"] = host_part.split('/')[0]
            else:
                components["host"] = host_part
        else:
            host_part = uri.split('//')[1]
            if '/' in host_part:
                components["host"] = host_part.split('/')[0]
            else:
                components["host"] = host_part
        
        # Extrair banco de dados se presente
        if '@' in uri and '/' in uri.split('@')[1]:
            path_part = uri.split('@')[1].split('/', 1)[1]
            if path_part and '?' in path_part:
                components["database"] = path_part.split('?')[0]
            elif path_part:
                components["database"] = path_part
        elif '/' in uri.split('//')[1]:
            path_part = uri.split('//')[1].split('/', 1)[1]
            if path_part and '?' in path_part:
                components["database"] = path_part.split('?')[0]
            elif path_part:
                components["database"] = path_part
        
        # Extrair opções de query string
        if '?' in uri:
            query_part = uri.split('?')[1]
            for param in query_part.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    components["options"][key] = value
    
    except Exception:
        # Em caso de erro na análise, retornar componentes padrão
        pass
    
    return components

def build_mongodb_atlas_uri(username, password, host, database="", options=None):
    """
    Constrói uma URI do MongoDB Atlas a partir de seus componentes
    
    Args:
        username: Nome de usuário
        password: Senha
        host: Host (incluindo porta se necessário)
        database: Banco de dados (opcional)
        options: Dicionário com opções de conexão (opcional)
        
    Returns:
        str: URI do MongoDB Atlas
    """
    if not host:
        return ""
    
    # Codificar username e password
    encoded_username = quote_plus(username) if username else ""
    encoded_password = quote_plus(password) if password else ""
    
    # Construir a parte básica da URI
    if username and password:
        base_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{host}"
    else:
        base_uri = f"mongodb+srv://{host}"
    
    # Adicionar banco de dados se fornecido
    if database:
        base_uri = f"{base_uri}/{database}"
    
    # Adicionar opções se fornecidas
    if options and isinstance(options, dict) and options:
        options_str = "&".join([f"{k}={quote_plus(str(v))}" for k, v in options.items()])
        base_uri = f"{base_uri}?{options_str}"
    
    return base_uri

def display_mongodb_status(uri):
    """
    Exibe um indicador visual do status da conexão MongoDB Atlas
    
    Args:
        uri: URI do MongoDB
    """
    is_atlas = "mongodb+srv://" in uri
    components = parse_mongodb_atlas_uri(uri) if is_atlas else {}
    
    # Exibir o tipo de conexão
    st.caption("Tipo: " + ("MongoDB Atlas" if is_atlas else "MongoDB Local"))
    
    # Para o MongoDB Atlas, mostrar informações adicionais
    if is_atlas and components["host"]:
        st.caption(f"Servidor: {components['host']}")
        if components["database"]:
            st.caption(f"Database: {components['database']}")
        
        # Listar opções importantes
        if components["options"]:
            important_options = ["retryWrites", "w", "appName"]
            options_info = [f"{k}={v}" for k, v in components["options"].items() 
                           if k in important_options]
            if options_info:
                st.caption("Opções: " + ", ".join(options_info))
