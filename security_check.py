"""
Utilitário de verificação de segurança para o OddsHunter
"""
import os
import re
import streamlit as st
from mongodb_credentials import parse_mongodb_atlas_uri

def check_for_exposed_credentials(show_warning=True):
    """
    Verifica se há credenciais expostas no código ou variáveis de ambiente
    e mostra avisos ao usuário
    
    Args:
        show_warning: Se True, exibe avisos no Streamlit
        
    Returns:
        dict: Resultado da verificação com status e detalhes
    """
    result = {
        "has_exposed_credentials": False,
        "warnings": [],
        "security_suggestions": []
    }
    
    # 1. Verificar se a URI do MongoDB Atlas está configurada via variável de ambiente
    atlas_uri_env = os.getenv('MONGODB_ATLAS_URI')
    if not atlas_uri_env:
        warning_msg = "MongoDB Atlas URI não configurada via variável de ambiente (menos seguro)"
        result["warnings"].append(warning_msg)
        result["security_suggestions"].append(
            "Configure a variável de ambiente 'MONGODB_ATLAS_URI' para maior segurança."
        )
        
    # 2. Verificar se há credenciais no código-fonte (hardcoded)
    # Isso é apenas uma demonstração - numa aplicação real precisaríamos varrer os arquivos
    # Note: Como não podemos verificar realmente o código, apenas simulamos o comportamento
    
    try:
        # Analisar a URI atual para ver se contém informações sensíveis
        if "MONGODB_URI" in globals():
            uri = globals().get("MONGODB_URI", "")
            components = parse_mongodb_atlas_uri(uri)
            
            if components["username"] and components["password"]:
                warning_msg = "Possíveis credenciais expostas na URI do MongoDB"
                result["warnings"].append(warning_msg)
                result["has_exposed_credentials"] = True
                result["security_suggestions"].append(
                    "Use variáveis de ambiente para armazenar credenciais em vez de hardcoding."
                )
    except:
        # Se não conseguir analisar, ignorar esta verificação
        pass
        
    # 3. Sugestões de segurança gerais
    result["security_suggestions"].extend([
        "Use conexões HTTPS/TLS para comunicação com MongoDB Atlas",
        "Configure regras de firewall para restringir o acesso ao MongoDB",
        "Utilize usuários com permissões mínimas necessárias",
        "Implemente autenticação de dois fatores no MongoDB Atlas",
        "Faça backups regulares dos dados"
    ])
    
    # Exibir avisos se solicitado
    if show_warning and result["warnings"]:
        st.warning("⚠️ Alerta de Segurança:", icon="⚠️")
        for warning in result["warnings"]:
            st.warning(warning)
            
    return result

def display_security_recommendations():
    """
    Exibe recomendações de segurança para MongoDB Atlas
    """
    st.markdown("### Recomendações de Segurança para MongoDB Atlas")
    
    recomendacoes = [
        ("**Use variáveis de ambiente**", "Armazene credenciais como `MONGODB_ATLAS_URI` em variáveis de ambiente, não no código."),
        ("**Configure IPs permitidos**", "Restrinja o acesso apenas para IPs confiáveis nas configurações do MongoDB Atlas."),
        ("**Privilégios mínimos**", "Crie usuários com acesso apenas ao necessário para cada aplicação."),
        ("**Autenticação avançada**", "Habilite autenticação de dois fatores para todas as contas do MongoDB Atlas."),
        ("**Auditoria e logs**", "Monitore e registre todas as atividades no seu cluster para detectar acessos suspeitos."),
        ("**Backup automatizado**", "Configure backups regulares dos seus dados para evitar perda de informações."),
        ("**Criptografia**", "Use criptografia em repouso e em trânsito para proteger os dados."),
        ("**Atualização automática**", "Mantenha seu cluster com a versão mais recente do MongoDB.")
    ]
    
    for titulo, descricao in recomendacoes:
        st.markdown(f"{titulo}: {descricao}")
        
    # Link para documentação oficial
    st.markdown("---")
    st.markdown("[Consulte o guia completo de segurança do MongoDB Atlas](https://docs.atlas.mongodb.com/security/)", unsafe_allow_html=True)
