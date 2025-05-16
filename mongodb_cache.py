"""
Cache e gestão de dados para aplicações MongoDB
"""
import time
import json
import os
import pandas as pd
import streamlit as st

class MongoDBCache:
    """
    Implementa um sistema de cache para dados do MongoDB
    para melhorar a performance e lidar com falhas de conexão
    """
    
    def __init__(self, cache_file="mongodb_cache.json", max_age_seconds=3600):
        """
        Inicializa o cache
        
        Args:
            cache_file: Nome do arquivo para armazenar o cache
            max_age_seconds: Idade máxima em segundos para considerar o cache válido
        """
        self.cache_file = cache_file
        self.max_age_seconds = max_age_seconds
        self.cache = self._carregar_cache()
        
    def _carregar_cache(self):
        """Carrega o cache do arquivo"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"timestamp": 0, "data": []}
        except Exception:
            return {"timestamp": 0, "data": []}
    
    def _salvar_cache(self):
        """Salva o cache para o arquivo"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f)
            return True
        except Exception:
            return False
    
    def set_cache(self, data):
        """
        Atualiza o cache com novos dados
        
        Args:
            data: Dados a serem armazenados no cache
        
        Returns:
            bool: True se o cache foi atualizado com sucesso
        """
        self.cache = {
            "timestamp": time.time(),
            "data": data
        }
        return self._salvar_cache()
    
    def get_cache(self):
        """
        Obtém dados do cache se forem válidos
        
        Returns:
            list: Dados do cache ou None se o cache for inválido
        """
        if time.time() - self.cache["timestamp"] > self.max_age_seconds:
            return None  # Cache expirado
        return self.cache["data"]
    
    def is_valid(self):
        """
        Verifica se o cache é válido
        
        Returns:
            bool: True se o cache for válido
        """
        return (time.time() - self.cache["timestamp"] <= self.max_age_seconds and
                len(self.cache["data"]) > 0)
    
    def invalidate(self):
        """Invalida o cache atual"""
        self.cache = {"timestamp": 0, "data": []}
        self._salvar_cache()
    
    def get_age_seconds(self):
        """
        Obtém a idade do cache em segundos
        
        Returns:
            float: Idade do cache em segundos
        """
        return time.time() - self.cache["timestamp"]

def salvar_dados_csv_backup(dados, filename="mongodb_backup.csv"):
    """
    Salva dados em um CSV de backup
    
    Args:
        dados: Lista de dicionários com dados
        filename: Nome do arquivo CSV
    
    Returns:
        bool: True se o backup foi bem-sucedido
    """
    try:
        df = pd.DataFrame(dados)
        df.to_csv(filename, index=False)
        return True
    except Exception:
        return False

def carregar_dados_csv_backup(filename="mongodb_backup.csv"):
    """
    Carrega dados de um CSV de backup
    
    Args:
        filename: Nome do arquivo CSV
    
    Returns:
        list: Lista de dicionários com dados ou lista vazia se falhar
    """
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            return df.to_dict('records')
        return []
    except Exception:
        return []

def obter_dados_com_cache(obter_func, cache_instance=None, force_refresh=False):
    """
    Obtém dados usando cache quando possível
    
    Args:
        obter_func: Função para obter dados do MongoDB
        cache_instance: Instância de MongoDBCache
        force_refresh: Forçar atualização ignorando o cache
    
    Returns:
        tuple: (dados, origem_dados, status)
            dados: Dados obtidos
            origem_dados: "mongodb", "cache" ou "backup"
            status: True se sucesso, False se falha
    """
    # Se não tiver instância de cache, criar uma temporária
    if cache_instance is None:
        cache_instance = MongoDBCache()
    
    # Se for forçada atualização ou cache inválido, buscar do MongoDB
    if force_refresh or not cache_instance.is_valid():
        try:
            # Tentar obter dados do MongoDB
            dados_mongodb = obter_func()
            
            if dados_mongodb and len(dados_mongodb) > 0:
                # Atualizar cache com os novos dados
                cache_instance.set_cache(dados_mongodb)
                # Criar backup em CSV
                salvar_dados_csv_backup(dados_mongodb)
                return dados_mongodb, "mongodb", True
            else:
                # Se não tiver dados no MongoDB, tentar usar cache ou backup
                dados_cache = cache_instance.get_cache()
                if dados_cache and len(dados_cache) > 0:
                    return dados_cache, "cache", True
                else:
                    # Último recurso: usar backup CSV
                    dados_backup = carregar_dados_csv_backup()
                    return dados_backup, "backup", len(dados_backup) > 0
        except Exception as e:
            # Em caso de erro, tentar usar cache
            dados_cache = cache_instance.get_cache()
            if dados_cache and len(dados_cache) > 0:
                return dados_cache, "cache", True
            else:
                # Último recurso: usar backup CSV
                dados_backup = carregar_dados_csv_backup()
                return dados_backup, "backup", len(dados_backup) > 0
    else:
        # Usar cache se for válido
        dados_cache = cache_instance.get_cache()
        return dados_cache, "cache", True
