"""
Utilidades para trabalhar com MongoDB na aplicação OddsHunter
"""
import time
import pymongo
from pymongo import MongoClient
import streamlit as st
import urllib.parse
import re
from mongodb_credentials import mask_mongodb_uri

def construir_uri_mongodb(host, porta, usuario=None, senha=None, auth_db=None):
    """
    Constrói uma URI de conexão MongoDB válida
    
    Args:
        host: Host do MongoDB (ex: 'localhost')
        porta: Porta do MongoDB (ex: 27017)
        usuario: Nome de usuário para autenticação (opcional)
        senha: Senha para autenticação (opcional)
        auth_db: Banco de dados para autenticação (opcional, padrão: 'admin')
        
    Returns:
        string: URI formatada do MongoDB
    """
    if not host:
        return "mongodb://localhost:27017/"
    
    # Formatar o host e porta
    if not porta:
        porta = 27017
    
    # Se não tiver autenticação, retorna URI simples
    if not usuario or not senha:
        return f"mongodb://{host}:{porta}/"
    
    # Se tiver autenticação, formata a URI com credenciais
    usuario_encoded = urllib.parse.quote_plus(usuario)
    senha_encoded = urllib.parse.quote_plus(senha)
    auth_db = auth_db or "admin"
    
    return f"mongodb://{usuario_encoded}:{senha_encoded}@{host}:{porta}/{auth_db}"

def validar_uri_mongodb(uri):
    """
    Valida se uma URI de MongoDB tem o formato correto
    
    Args:
        uri: String de conexão MongoDB a ser validada
        
    Returns:
        bool: True se a URI é válida, False caso contrário
    """
    # Regex para validar URIs MongoDB (padrão e SRV)
    # Referência: https://docs.mongodb.com/manual/reference/connection-string/
    padrao_uri_padrao = r'^mongodb:\/\/(.+:.*@)?[a-zA-Z0-9]([-.a-zA-Z0-9]+)?([.][a-zA-Z0-9-]+)?(:[0-9]+)?(\/.+)?$'
    padrao_uri_srv = r'^mongodb\+srv:\/\/(.+:.*@)?[a-zA-Z0-9]([-.a-zA-Z0-9]+)?([.][a-zA-Z0-9-]+)?(:[0-9]+)?(\/.+)?(\?.+)?$'
    
    # Verificar ambos os padrões
    return bool(re.match(padrao_uri_padrao, uri)) or bool(re.match(padrao_uri_srv, uri))

def testar_conexao_mongodb(uri, connect_timeout=5000, server_selection_timeout=5000):
    """
    Testa a conexão com o MongoDB e retorna detalhes do status
    
    Args:
        uri: String de conexão MongoDB
        connect_timeout: Timeout de conexão em ms
        server_selection_timeout: Timeout de seleção de servidor em ms
        
    Returns:
        dict: Dicionário com status da conexão e detalhes
    """
    resultado = {
        "status": False,
        "mensagem": "",
        "detalhes": {},
        "tempo_conexao": 0
    }
    
    # Validar URI antes de tentar conectar
    if not validar_uri_mongodb(uri):
        resultado["mensagem"] = "URI de MongoDB inválida. Verifique o formato."
        resultado["detalhes"] = {
            "error_type": "InvalidURI",
            "uri_masked": mask_mongodb_uri(uri)
        }
        return resultado
    
    try:
        inicio = time.time()
        # Configurar cliente com timeouts explícitos
        # Detecção se é uma URI do MongoDB Atlas
        is_atlas = "mongodb+srv://" in uri
        
        client_options = {
            "connectTimeoutMS": connect_timeout,
            "serverSelectionTimeoutMS": server_selection_timeout
        }
        
        # Opções adicionais para MongoDB Atlas
        if is_atlas:
            client_options.update({
                "retryWrites": True,
                "w": "majority",
                "retryReads": True,
                "appName": "OddsHunter"  # Identificador da aplicação para monitoramento
            })
            
        cliente = MongoClient(uri, **client_options)
        
        # Tentar obter informações do servidor
        info = cliente.server_info()
        
        # Calcular tempo de conexão
        tempo_conexao = (time.time() - inicio) * 1000  # em milissegundos
        
        resultado["status"] = True
        resultado["mensagem"] = "Conexão bem sucedida!" + (" (MongoDB Atlas)" if is_atlas else "")
        resultado["detalhes"] = {
            "version": info.get("version", "N/A"),
            "uptime": info.get("uptime", 0),
            "connections": info.get("connections", {}).get("current", 0) if "connections" in info else 0,
            "host": cliente.address[0] if hasattr(cliente, "address") else "N/A",
            "port": cliente.address[1] if hasattr(cliente, "address") else "N/A",
            "is_atlas": is_atlas,
            "uri_masked": mask_mongodb_uri(uri)  # URI mascarada para logs e debugging
        }
        resultado["tempo_conexao"] = tempo_conexao
        
        # Fechar conexão
        cliente.close()
        
    except pymongo.errors.ServerSelectionTimeoutError as e:
        resultado["mensagem"] = f"Timeout ao conectar ao servidor: {str(e)}"
        resultado["detalhes"] = {
            "error_type": "ServerSelectionTimeoutError",
            "uri_masked": mask_mongodb_uri(uri)  # Segurança adicional nos logs de erro
        }
        
    except pymongo.errors.ConnectionFailure as e:
        resultado["mensagem"] = f"Falha de conexão: {str(e)}"
        resultado["detalhes"] = {
            "error_type": "ConnectionFailure",
            "uri_masked": mask_mongodb_uri(uri)
        }
        
    except pymongo.errors.ConfigurationError as e:
        resultado["mensagem"] = f"Erro de configuração: {str(e)}"
        resultado["detalhes"] = {
            "error_type": "ConfigurationError",
            "uri_masked": mask_mongodb_uri(uri)
        }
        
    except pymongo.errors.OperationFailure as e:
        # Este erro geralmente ocorre com falhas de autenticação
        auth_error_msg = "Falha de autenticação. Verifique usuário e senha." if "auth" in str(e).lower() else str(e)
        resultado["mensagem"] = f"Falha de operação: {auth_error_msg}"
        resultado["detalhes"] = {
            "error_type": "OperationFailure", 
            "auth_error": "auth" in str(e).lower(),
            "uri_masked": mask_mongodb_uri(uri)
        }
        
    except Exception as e:
        resultado["mensagem"] = f"Erro desconhecido: {str(e)}"
        resultado["detalhes"] = {
            "error_type": "Unknown",
            "uri_masked": mask_mongodb_uri(uri)
        }
        
    return resultado

def verificar_banco_colecao(uri, database, collection, connect_timeout=5000, server_selection_timeout=5000):
    """
    Verifica se o banco de dados e a coleção existem
    
    Args:
        uri: String de conexão MongoDB
        database: Nome do banco de dados
        collection: Nome da coleção
        connect_timeout: Timeout de conexão em ms
        server_selection_timeout: Timeout de seleção de servidor em ms
        
    Returns:
        dict: Dicionário com status da verificação e detalhes
    """
    resultado = {
        "banco_existe": False,
        "colecao_existe": False,
        "contagem_documentos": 0,
        "mensagem": "",
        "status": False
    }
    
    try:
        # Detectar se é uma URI do MongoDB Atlas
        is_atlas = "mongodb+srv://" in uri
        
        # Configurar opções do cliente
        client_options = {
            "connectTimeoutMS": connect_timeout,
            "serverSelectionTimeoutMS": server_selection_timeout
        }
        
        # Opções adicionais para MongoDB Atlas
        if is_atlas:
            client_options.update({
                "retryWrites": True,
                "w": "majority",
                "retryReads": True,
                "appName": "OddsHunterVerify"  # Identificador da aplicação para monitoramento
            })
        
        # Tentar conectar ao MongoDB
        cliente = MongoClient(uri, **client_options)
        
        # No MongoDB Atlas, a abordagem é um pouco diferente
        if is_atlas:
            try:
                # Tentar acessar o banco e a coleção diretamente
                db = cliente[database]
                colecao = db[collection]
                
                # Fazer uma consulta simples para verificar se funciona
                # (isso criará automaticamente o banco e a coleção se não existirem)
                count = colecao.count_documents({}, limit=1)
                
                resultado["banco_existe"] = True
                resultado["colecao_existe"] = True
                resultado["contagem_documentos"] = count
                resultado["status"] = True
                resultado["mensagem"] = "Banco de dados e coleção acessíveis no MongoDB Atlas."
            except Exception as e:
                resultado["mensagem"] = f"Erro ao acessar banco/coleção no MongoDB Atlas: {str(e)}"
        else:
            # Para MongoDB local, usamos o método tradicional
            # Verificar se o banco existe na lista de bancos
            bancos = cliente.list_database_names()
            resultado["banco_existe"] = database in bancos
            
            if resultado["banco_existe"]:
                # Verificar se a coleção existe
                db = cliente[database]
                colecoes = db.list_collection_names()
                resultado["colecao_existe"] = collection in colecoes
                
                if resultado["colecao_existe"]:
                    # Contar documentos na coleção
                    colecao = db[collection]
                    resultado["contagem_documentos"] = colecao.count_documents({})
                    resultado["status"] = True
                    resultado["mensagem"] = "Banco de dados e coleção encontrados com sucesso."
                else:
                    resultado["mensagem"] = f"A coleção '{collection}' não existe no banco de dados '{database}'."
            else:
                resultado["mensagem"] = f"O banco de dados '{database}' não existe."
        
        # Fechar conexão
        cliente.close()
        
    except Exception as e:
        resultado["mensagem"] = f"Erro ao verificar banco e coleção: {str(e)}"
        # Adicionar URI mascarada para logs de segurança
        resultado["uri_masked"] = mask_mongodb_uri(uri)
        
    return resultado

def exibir_status_conexao(resultado_teste):
    """
    Exibe o status da conexão em componentes Streamlit
    
    Args:
        resultado_teste: Resultado do teste de conexão
    """
    if resultado_teste["status"]:
        st.success(f"✅ {resultado_teste['mensagem']}")
        
        # Exibir detalhes da conexão em colunas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tempo de Conexão", f"{resultado_teste['tempo_conexao']:.1f} ms")
            st.text(f"MongoDB Versão: {resultado_teste['detalhes'].get('version', 'N/A')}")
        with col2:
            st.metric("Conexões Ativas", resultado_teste['detalhes'].get('connections', 0))
            st.text(f"Servidor: {resultado_teste['detalhes'].get('host', 'N/A')}:{resultado_teste['detalhes'].get('port', 'N/A')}")
    else:
        st.error(f"❌ {resultado_teste['mensagem']}")
        if "error_type" in resultado_teste.get("detalhes", {}):
            tipo_erro = resultado_teste["detalhes"]["error_type"]
            if tipo_erro == "ServerSelectionTimeoutError":
                st.info("Sugestão: Verifique se o servidor MongoDB está em execução e acessível")
            elif tipo_erro == "ConnectionFailure":
                st.info("Sugestão: Verifique se a URI está correta e se não há bloqueios de firewall")
            elif tipo_erro == "ConfigurationError":
                st.info("Sugestão: Verifique a sintaxe da URI de conexão")
            elif tipo_erro == "OperationFailure" and resultado_teste["detalhes"].get("auth_error"):
                st.info("Sugestão: Verifique se as credenciais (usuário/senha) estão corretas")
            elif tipo_erro == "InvalidURI":
                st.info("Sugestão: O formato da URI de conexão está incorreto. Exemplo correto: mongodb://[usuário:senha@]host[:porta][/banco]")

def exibir_status_banco_colecao(resultado_verificacao):
    """
    Exibe o status do banco e coleção em componentes Streamlit
    
    Args:
        resultado_verificacao: Resultado da verificação de banco e coleção
    """
    if resultado_verificacao["status"]:
        st.success(f"✅ {resultado_verificacao['mensagem']}")
        
        # Exibir detalhes
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Banco de Dados", "Encontrado" if resultado_verificacao["banco_existe"] else "Não Encontrado")
        with col2:
            st.metric("Coleção", "Encontrada" if resultado_verificacao["colecao_existe"] else "Não Encontrada")
        
        # Exibir contador de documentos
        st.metric("Documentos na Coleção", resultado_verificacao["contagem_documentos"])
    else:
        st.error(f"❌ {resultado_verificacao['mensagem']}")
