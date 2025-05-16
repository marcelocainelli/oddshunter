"""
Funções para teste de segurança e validação de URIs do MongoDB Atlas
"""
import re
import pymongo
import streamlit as st
from pymongo import MongoClient
from mongodb_credentials import mask_mongodb_uri

def validate_mongodb_atlas_uri(uri, test_connection=False, timeout=3000):
    """
    Valida uma URI do MongoDB Atlas e opcionalmente testa a conexão
    
    Args:
        uri: URI do MongoDB Atlas para validar
        test_connection: Se True, tenta estabelecer uma conexão com o servidor
        timeout: Timeout em milissegundos para a conexão
        
    Returns:
        dict: Resultado da validação/teste com status e mensagens
    """
    resultado = {
        "valido": False,
        "mensagem": "",
        "erro_detalhes": None,
        "is_atlas": False
    }
    
    # Verificar se é uma URI do MongoDB Atlas
    if not uri.startswith("mongodb+srv://"):
        resultado["mensagem"] = "A URI deve começar com 'mongodb+srv://' para MongoDB Atlas"
        return resultado
    
    # Marcar como Atlas
    resultado["is_atlas"] = True
    
    # Validar formato com regex
    formato_valido = re.match(r'^mongodb\+srv://(.+:.*@)?[a-zA-Z0-9]([-.a-zA-Z0-9]+)?([.][a-zA-Z0-9-]+)?(:[0-9]+)?(\/.+)?(\?.+)?$', uri)
    
    if not formato_valido:
        resultado["mensagem"] = "Formato inválido para URI do MongoDB Atlas"
        return resultado
    
    # Verificar se contém usuário e senha
    if '@' not in uri:
        resultado["mensagem"] = "A URI deve conter usuário e senha (formato: mongodb+srv://usuario:senha@host...)"
        return resultado
    
    # A URI parece válida em termos de formato
    resultado["valido"] = True
    
    # Se solicitado, testar a conexão
    if test_connection:
        try:
            # Configurar cliente com timeout explícito
            client = MongoClient(
                uri, 
                connectTimeoutMS=timeout, 
                serverSelectionTimeoutMS=timeout,
                retryWrites=True,
                retryReads=True,
                w="majority"
            )
            
            # Tentar obter informações do servidor (isso vai falhar se a conexão não for possível)
            info = client.server_info()
            client.close()
            
            # Se chegou aqui, a conexão funcionou
            resultado["mensagem"] = "URI validada e conexão estabelecida com sucesso"
            resultado["valido"] = True
            
        except pymongo.errors.ServerSelectionTimeoutError as e:
            resultado["mensagem"] = "Timeout ao conectar ao servidor MongoDB Atlas"
            resultado["erro_detalhes"] = str(e)
            resultado["valido"] = False  # A URI pode estar correta, mas a conexão falhou
            
        except pymongo.errors.OperationFailure as e:
            # Erro de autenticação
            if "auth" in str(e).lower():
                resultado["mensagem"] = "Falha de autenticação. Verifique usuário e senha."
            else:
                resultado["mensagem"] = f"Falha de operação: {str(e)}"
            resultado["erro_detalhes"] = str(e)
            resultado["valido"] = False
            
        except Exception as e:
            resultado["mensagem"] = f"Erro ao testar conexão: {str(e)}"
            resultado["erro_detalhes"] = str(e)
            resultado["valido"] = False
    else:
        resultado["mensagem"] = "URI validada (formato correto)"
        
    return resultado

def provide_atlas_uri_guidance():
    """
    Fornece orientações sobre como obter e formatar uma URI do MongoDB Atlas
    """
    st.markdown("### Como obter sua URI do MongoDB Atlas")
    
    st.markdown("""
    1. Faça login no [MongoDB Atlas](https://cloud.mongodb.com/)
    2. Navegue até o seu cluster
    3. Clique em "Connect"
    4. Escolha "Connect your application"
    5. Selecione "Python" como driver
    6. Copie a URI de conexão (substitua `<password>` pela sua senha real)
    """)
    
    st.markdown("### Formato da URI")
    st.code("mongodb+srv://usuário:senha@cluster.exemplo.mongodb.net/?retryWrites=true&w=majority", language="text")
    
    st.markdown("### Dicas de segurança")
    st.markdown("""
    - Considere usar variáveis de ambiente para armazenar a URI de forma segura
    - Certifique-se de que seu IP está na lista de permitidos no MongoDB Atlas
    - Use uma senha forte e um usuário com privilégios mínimos necessários
    """)
    
    # Atalho para configurar variável de ambiente
    st.markdown("### Configurar via variável de ambiente (recomendado)")
    st.code("setx MONGODB_ATLAS_URI \"mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?opções\"", language="bash")
    
    # Link para mais informações
    st.markdown("[Consulte a documentação do MongoDB Atlas para mais informações](https://docs.mongodb.com/guides/atlas/connection-string/)")

def display_atlas_uri_validation_result(result):
    """
    Exibe o resultado da validação da URI do MongoDB Atlas
    
    Args:
        result: Resultado da validação retornado por validate_mongodb_atlas_uri
    """
    if result["valido"]:
        st.success(f"✓ {result['mensagem']}")
    else:
        st.error(f"✗ {result['mensagem']}")
        
        # Se houver detalhes de erro, mostrar em um expander
        if result["erro_detalhes"]:
            with st.expander("Detalhes do erro"):
                st.code(result["erro_detalhes"], language="text")
        
        # Fornecer sugestões com base no erro
        if "auth" in result.get("erro_detalhes", "").lower():
            st.info("Verifique se o usuário e senha estão corretos")
        elif "timeout" in result.get("erro_detalhes", "").lower():
            st.info("Verifique se seu IP está na lista de IPs permitidos no MongoDB Atlas")
        elif "formato" in result.get("mensagem", "").lower():
            st.info("A URI deve começar com 'mongodb+srv://' e incluir usuário, senha e hostname")
            
    # Se for uma URI Atlas válida, mostrar versão mascarada
    if result["is_atlas"]:
        st.caption("A URI parece ser do MongoDB Atlas")
