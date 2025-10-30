# -*- coding: utf-8 -*-
"""
ACI Frontend - Configurações
Configurações centralizadas da aplicação
"""

import os
from typing import Dict, Any

class Config:
    """Classe para gerenciar configurações da aplicação."""
    
    # Informações da aplicação
    APP_NAME = "ACI Frontend"
    APP_VERSION = "2.7.1"
    APP_AUTHOR = "Progpy"
    
    # Configurações de interface
    DEFAULT_WINDOW_WIDTH = 1280
    DEFAULT_WINDOW_HEIGHT = 800
    DEFAULT_WINDOW_X = 100
    DEFAULT_WINDOW_Y = 100
    
    # Configurações de API
    API_TIMEOUT = 30  # segundos
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 1  # segundos
    
    # URLs das APIs (configurar conforme necessário)
    ALGAR_SOM_API_URL = "https://api.algar.som.example.com"
    CONNECT_MASTER_API_URL = "https://api.connectmaster.example.com"
    
    # Configurações de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configurações de exportação
    EXPORT_FORMATS = ["PDF", "CSV", "XLS", "XLSX", "JSON", "TXT"]
    DEFAULT_EXPORT_DIR = os.path.expanduser("~/Documents/ACI_Exports")
    
    # Configurações de cache
    CACHE_ENABLED = True
    CACHE_DURATION = 300  # 5 minutos em segundos
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Retorna todas as configurações como dicionário."""
        return {
            key: value for key, value in cls.__dict__.items() 
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def update_setting(cls, key: str, value: Any) -> bool:
        """
        Atualiza uma configuração específica.
        
        Args:
            key: Nome da configuração
            value: Novo valor
            
        Returns:
            True se a configuração foi atualizada com sucesso
        """
        if hasattr(cls, key):
            setattr(cls, key, value)
            return True
        return False
    
    @classmethod
    def ensure_export_dir(cls) -> str:
        """
        Garante que o diretório de exportação existe.
        
        Returns:
            Caminho do diretório de exportação
        """
        if not os.path.exists(cls.DEFAULT_EXPORT_DIR):
            os.makedirs(cls.DEFAULT_EXPORT_DIR, exist_ok=True)
        return cls.DEFAULT_EXPORT_DIR

# Instância global de configuração
config = Config()
