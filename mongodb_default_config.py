# mongodb_default_config.py
"""
Configuração padrão para conexão MongoDB Atlas
Este arquivo contém a URI padrão para conectar ao MongoDB Atlas
"""

# URI padrão para o MongoDB Atlas
DEFAULT_MONGODB_ATLAS_URI = "mongodb+srv://marcelodick:Indra123@cluster0.3cizyna.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Configurações padrão do banco
DEFAULT_MONGODB_DATABASE = "oddshunter"
DEFAULT_MONGODB_COLLECTION = "dados_recentes"
DEFAULT_MONGODB_CONNECT_TIMEOUT = 10000
DEFAULT_MONGODB_SERVER_SELECTION_TIMEOUT = 10000
DEFAULT_MONGODB_MAX_RETRIES = 3
