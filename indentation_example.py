"""
Exemplo correto das configurações do MongoDB Atlas no streamlit_app.py
"""

# Exemplo de código com indentação correta
# Apenas para referência - não será usado diretamente

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
            else:
                # Mostrar erro de validação
                st.error(f"URI inválida: {validation_result['mensagem']}")
                if "erro_detalhes" in validation_result and validation_result["erro_detalhes"]:
                    with st.expander("Detalhes do erro"):
                        st.code(validation_result["erro_detalhes"])
        else:
            st.error("A URI deve começar com 'mongodb+srv://' para o MongoDB Atlas")
            
    # Mostrar ajuda para configuração do MongoDB Atlas
    with st.expander("Ajuda para configurar MongoDB Atlas"):
        provide_atlas_uri_guidance()
        
    # Mostrar link para documentação detalhada
    st.markdown("[📄 Consulte a documentação completa de segurança](mongodb_atlas_setup.md)")
    
    st.caption("A URI do MongoDB Atlas inclui usuário, senha e configurações de conexão")
    
    # Mostrar informações da conexão atual de forma segura
    display_mongodb_status(MONGODB_URI)
    
    # Configurações avançadas colapsadas
    with st.expander("Configurações Avançadas"):
        mongodb_db = st.text_input("Database:", value=MONGODB_DATABASE)
        mongodb_collection = st.text_input("Collection:", value=MONGODB_COLLECTION)
        mongodb_timeout = st.number_input("Timeout (ms):", value=MONGODB_CONNECT_TIMEOUT, min_value=1000, step=1000)
        mongodb_max_retries = st.number_input("Máx. Tentativas:", value=MONGODB_MAX_RETRIES, min_value=1, max_value=10, step=1)
else:
    # Configuração MongoDB Local
    mongodb_host = st.text_input("Host MongoDB:", value="localhost")
    mongodb_porta = st.number_input("Porta MongoDB:", value=27017, min_value=1, max_value=65535)
