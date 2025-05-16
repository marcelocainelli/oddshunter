"""
Utilitário para gerenciamento de variáveis de ambiente
"""
import os
import streamlit as st
import platform
import subprocess

def get_environment_variable_status():
    """
    Verifica o status das variáveis de ambiente necessárias para o OddsHunter
    
    Returns:
        dict: Dicionário com status de cada variável de ambiente
    """
    env_vars = {
        "MONGODB_ATLAS_URI": {
            "description": "URI de conexão do MongoDB Atlas (credenciais)",
            "set": False,
            "masked_value": None,
            "importance": "Crítica"
        }
    }
    
    # Verificar cada variável de ambiente
    for var_name in env_vars:
        value = os.getenv(var_name)
        if value:
            env_vars[var_name]["set"] = True
            # Mascarar a variável para exibição segura
            if "URI" in var_name and len(value) > 20:
                masked = value[:10] + "..." + value[-10:]
                env_vars[var_name]["masked_value"] = masked
            else:
                env_vars[var_name]["masked_value"] = "*" * len(value)
                
    return env_vars

def display_environment_variables():
    """
    Exibe o status das variáveis de ambiente na interface do Streamlit
    """
    st.markdown("### Variáveis de Ambiente")
    
    env_vars = get_environment_variable_status()
    
    # Exibir status de cada variável
    for var_name, info in env_vars.items():
        if info["set"]:
            st.success(f"✅ {var_name}: Configurada")
            st.caption(f"Valor: {info['masked_value']} (mascarado)")
        else:
            st.error(f"❌ {var_name}: Não configurada")
            st.caption(f"Importância: {info['importance']}")
            st.caption(f"Descrição: {info['description']}")
            
    # Instruções para configurar variáveis de ambiente
    st.markdown("### Como configurar variáveis de ambiente")
    
    sistema = platform.system()
    if sistema == "Windows":
        st.code("""
# No Prompt de Comando (como Administrador):
setx MONGODB_ATLAS_URI "mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?opcoes"

# OU no PowerShell:
[Environment]::SetEnvironmentVariable("MONGODB_ATLAS_URI", "mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?opcoes", "User")
        """, language="bash")
    elif sistema == "Linux" or sistema == "Darwin":  # Darwin = macOS
        st.code("""
# No terminal:
echo 'export MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?opcoes"' >> ~/.bashrc
source ~/.bashrc

# Ou se usar zsh:
echo 'export MONGODB_ATLAS_URI="mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?opcoes"' >> ~/.zshrc
source ~/.zshrc
        """, language="bash")
    else:
        st.info("Consulte a documentação do seu sistema operacional para configurar variáveis de ambiente.")
        
    st.caption("Nota: Após configurar as variáveis de ambiente, pode ser necessário reiniciar o terminal ou o computador para que as alterações tenham efeito.")
    
def set_temp_environment_variable(var_name, value):
    """
    Define uma variável de ambiente temporária para a sessão atual
    do processo Python (não permanece após reiniciar)
    
    Args:
        var_name: Nome da variável de ambiente
        value: Valor da variável
        
    Returns:
        bool: True se definido com sucesso, False caso contrário
    """
    try:
        os.environ[var_name] = value
        return True
    except:
        return False
