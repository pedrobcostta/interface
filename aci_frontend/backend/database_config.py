# -*- coding: utf-8 -*-
"""
ACI Frontend - Configuração de Banco de Dados
Gerencia conexões Oracle com os bancos SOMPRD e CMPRD
"""

import os
import oracledb
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """
    Classe responsável pela configuração e gerenciamento de conexões Oracle.
    Utiliza melhores práticas de segurança e performance.
    """
    
    # DSNs para os bancos de dados Oracle - CONSTANTES DE FÁCIL ACESSO
    CMPRD_DSN = "exa02-scan-prd.network.ctbc:1521/CMPRD"
    SOMPRD_DSN = "exa07-scan-prd.network.ctbc:1521/SOMPRD"
    
    # Configurações de pool de conexão
    CONNECTION_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', '30'))
    POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', '5'))
    
    def __init__(self):
        """Inicializa a configuração do banco de dados."""
        self._validate_environment()
        self.pools = {}
        
    def _validate_environment(self):
        """Valida se todas as variáveis de ambiente necessárias estão definidas."""
        required_vars = [
            'CMPRD_USER', 'CMPRD_PASSWORD',
            'SOMPRD_USER', 'SOMPRD_PASSWORD'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}. "
                "Verifique o arquivo .env na raiz do projeto."
            )
    
    def get_connection(self, database: str) -> oracledb.Connection:
        """
        Obtém uma conexão direta para o banco especificado.
        SIMPLIFICADO: Usa conexão direta para evitar problemas de DNS com pools.
        
        Args:
            database (str): Nome do banco ('SOMPRD' ou 'CMPRD')
            
        Returns:
            oracledb.Connection: Conexão ativa com o banco
        """
        if database not in ['SOMPRD', 'CMPRD']:
            raise ValueError(f"Banco de dados inválido: {database}. Use 'SOMPRD' ou 'CMPRD'.")
        
        try:
            # Obter credenciais do ambiente
            user = os.getenv(f'{database}_USER')
            password = os.getenv(f'{database}_PASSWORD')
            dsn = getattr(self, f'{database}_DSN')
            
            logger.info(f"Criando conexão direta para {database}...")
            
            # CORREÇÃO: Conexão direta como no exemplo funcional
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            
            logger.info(f"Conexão com {database} estabelecida com sucesso.")
            return connection
            
        except Exception as e:
            logger.error(f"Erro ao conectar com {database}: {str(e)}")
            raise Exception(f"Falha na conexão com {database}: {str(e)}")
    
    def release_connection(self, connection: oracledb.Connection, database: str):
        """
        Fecha a conexão direta (sem pools).
        
        Args:
            connection (oracledb.Connection): Conexão a ser fechada
            database (str): Nome do banco de origem da conexão
        """
        try:
            if connection:
                connection.close()
                logger.debug(f"Conexão fechada para {database}")
                
        except Exception as e:
            logger.warning(f"Erro ao fechar conexão para {database}: {str(e)}")
    
    def close_all_pools(self):
        """Fecha todos os pools de conexão."""
        for database, pool in self.pools.items():
            try:
                pool.close()
                logger.info(f"Pool de conexões para {database} fechado.")
            except Exception as e:
                logger.warning(f"Erro ao fechar pool {database}: {str(e)}")
        
        self.pools.clear()
    
    def test_connection(self, database: str) -> Dict[str, Any]:
        """
        Testa a conectividade com o banco especificado.
        
        Args:
            database (str): Nome do banco para testar
            
        Returns:
            Dict[str, Any]: Resultado do teste com status e informações
        """
        try:
            connection = self.get_connection(database)
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT SYSDATE FROM DUAL")
                result = cursor.fetchone()
                
            self.release_connection(connection, database)
            
            return {
                "success": True,
                "database": database,
                "server_time": result[0] if result else None,
                "message": f"Conexão com {database} estabelecida com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "database": database,
                "error": str(e),
                "message": f"Falha na conexão com {database}"
            }

# Instância global da configuração do banco
db_config = DatabaseConfig()
