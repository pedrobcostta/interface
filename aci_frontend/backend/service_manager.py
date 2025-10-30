# -*- coding: utf-8 -*-
"""
ACI Frontend - Gerenciador de Serviços Backend
Orquestra a integração entre frontend e backend
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .input_processor import InputProcessor
from .somprd_queries import somprd_queries
from .cmprd_queries import cmprd_queries
from .database_config import db_config

logger = logging.getLogger(__name__)

class ServiceManager:
    """
    Classe principal que orquestra todos os serviços backend.
    Responsável pela integração entre frontend e módulos de dados.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de serviços."""
        self.input_processor = InputProcessor()
        
    def process_search_request(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma solicitação de busca completa do frontend.
        
        FLUXO COMPLETO:
        1. Validar dados de entrada
        2. Pré-processar inputs (adicionar zeros, limpar valores)
        3. Executar consulta no banco apropriado
        4. Formatar resultados para o frontend
        
        NOVA FUNCIONALIDADE: Consulta Encadeada (SOMPRD → CMPRD)
        
        Args:
            frontend_data (Dict[str, Any]): Dados da requisição do frontend
                Estrutura esperada:
                {
                    "search_type": "Protocolo Algar SOM",
                    "values": "123\n456\n789",
                    "add_zeros_protocolo": True,
                    "add_zero_circuito": False,
                    "selected_systems": ["SOMPRD", "CMPRD"],
                    "selected_fields": ["protocolo", "circuito", "localidade"],
                    "fila_value": "Despacho",  # apenas para busca por fila
                    "data_inicio": "01/01/2024",  # opcional
                    "data_inicio_fila": "01/01/2024",  # opcional
                    "consulta_encadeada": True  # NOVA OPÇÃO
                }
                
        Returns:
            Dict[str, Any]: Resultado processado para o frontend
        """
        try:
            start_time = datetime.now()
            
            # ETAPA 1: Validar entrada
            validation_result = self._validate_search_request(frontend_data)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"],
                    "data": [],
                    "error": validation_result.get("error", "Dados inválidos")
                }
            
            # ETAPA 2: Pré-processar inputs
            logger.info(f"Processando busca: {frontend_data.get('search_type', 'N/A')}")
            processed_params = self.input_processor.process_search_params(frontend_data)
            
            if processed_params.get("error"):
                return {
                    "success": False,
                    "message": "Erro no pré-processamento dos dados",
                    "data": [],
                    "error": processed_params["error"]
                }
            
            # Adicionar parâmetros extras do frontend
            processed_params.update({
                "selected_systems": frontend_data.get("selected_systems", ["SOMPRD"]),
                "selected_fields": frontend_data.get("selected_fields", []),
                "fila_value": frontend_data.get("fila_value", ""),
                "data_inicio": frontend_data.get("data_inicio"),
                "data_inicio_fila": frontend_data.get("data_inicio_fila"),
                "apenas_corretiva": frontend_data.get("apenas_corretiva", False)  # NOVA INTEGRAÇÃO
            })
            
            # NOVA FUNCIONALIDADE: Verificar se é consulta encadeada
            consulta_encadeada = frontend_data.get("consulta_encadeada", False)
            
            if consulta_encadeada:
                # ETAPA 3A: Executar consulta encadeada SOMPRD → CMPRD
                final_result = self._execute_chained_search(processed_params)
            else:
                # ETAPA 3B: Executar consultas nos bancos selecionados (fluxo normal)
                results = self._execute_multi_database_search(processed_params)
                
                # ETAPA 4: Consolidar e formatar resultados
                final_result = self._consolidate_search_results(results, processed_params)
            
            # Adicionar metadados de execução
            execution_time = (datetime.now() - start_time).total_seconds()
            final_result.update({
                "total_execution_time": execution_time,
                "processed_at": datetime.now().isoformat(),
                "input_summary": {
                    "search_type": processed_params.get("search_type"),
                    "value_count": processed_params.get("count", 0),
                    "transformations": processed_params.get("transformations_applied", {})
                }
            })
            
            logger.info(f"Busca concluída: {final_result.get('total_records', 0)} registros em {execution_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Erro no processamento da busca: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno no processamento da busca",
                "data": [],
                "error": str(e),
                "total_records": 0
            }
    
    def _validate_search_request(self, frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida os dados da requisição de busca.
        
        Args:
            frontend_data (Dict[str, Any]): Dados do frontend
            
        Returns:
            Dict[str, Any]: Resultado da validação
        """
        required_fields = ["search_type"]
        missing_fields = [field for field in required_fields if not frontend_data.get(field)]
        
        if missing_fields:
            return {
                "is_valid": False,
                "message": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}",
                "error": "MISSING_REQUIRED_FIELDS"
            }
        
        # Validar tipo de busca
        search_type_validation = self.input_processor.validate_search_type(
            frontend_data["search_type"]
        )
        
        if not search_type_validation["is_valid"]:
            return {
                "is_valid": False,
                "message": search_type_validation["message"],
                "error": "INVALID_SEARCH_TYPE"
            }
        
        # Validar se há valores para busca (exceto para busca por fila)
        if (frontend_data["search_type"] != "Fila" and 
            not frontend_data.get("values", "").strip()):
            return {
                "is_valid": False,
                "message": "Valores de busca são obrigatórios para este tipo de consulta",
                "error": "MISSING_SEARCH_VALUES"
            }
        
        return {
            "is_valid": True,
            "message": "Dados válidos"
        }
    
    def _execute_multi_database_search(self, processed_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa busca em múltiplos bancos conforme seleção do usuário.
        
        Args:
            processed_params (Dict[str, Any]): Parâmetros processados
            
        Returns:
            Dict[str, Any]: Resultados de todos os bancos
        """
        results = {}
        selected_systems = processed_params.get("selected_systems", ["SOMPRD"])
        
        # Executar busca no SOMPRD se selecionado
        if "SOMPRD" in selected_systems or "Algar SOM" in selected_systems:
            logger.debug("Executando busca no SOMPRD...")
            results["SOMPRD"] = somprd_queries.execute_search_query(processed_params)
        
        # Executar busca no CMPRD se selecionado
        if "CMPRD" in selected_systems or "Connect Master" in selected_systems:
            logger.debug("Executando busca no CMPRD...")
            results["CMPRD"] = cmprd_queries.execute_search_query(processed_params)
        
        return results
    
    def _consolidate_search_results(self, results: Dict[str, Any], processed_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolida resultados de múltiplos bancos em formato unificado.
        
        Args:
            results (Dict[str, Any]): Resultados por banco
            processed_params (Dict[str, Any]): Parâmetros da busca
            
        Returns:
            Dict[str, Any]: Resultado consolidado
        """
        consolidated_data = []
        total_records = 0
        success_count = 0
        error_messages = []
        
        for database, result in results.items():
            if result.get("success", False):
                success_count += 1
                database_data = result.get("data", [])
                
                # DEBUG: Log dos dados antes de consolidar
                logger.debug(f"Dados do {database}: {len(database_data)} registros")
                if database_data:
                    logger.debug(f"Primeiro registro {database}: {database_data[0]}")
                
                # CORREÇÃO: Adicionar identificador do banco SEM SOBRESCREVER os dados
                for record in database_data:
                    if record:  # Verificar se o registro não está vazio
                        record["_source_database"] = database
                    else:
                        logger.warning(f"Registro vazio encontrado em {database}")
                
                consolidated_data.extend(database_data)
                total_records += len(database_data)
                
                # DEBUG: Log após consolidação
                logger.debug(f"Total consolidado após {database}: {len(consolidated_data)} registros")
                
            else:
                error_messages.append(f"{database}: {result.get('message', 'Erro desconhecido')}")
        
        # Determinar sucesso geral
        overall_success = success_count > 0
        
        # Montar mensagem final
        if overall_success:
            if error_messages:
                message = f"Busca parcialmente bem-sucedida. {total_records} registros encontrados. Erros: {'; '.join(error_messages)}"
            else:
                message = f"Busca concluída com sucesso. {total_records} registros encontrados."
        else:
            message = f"Busca falhou em todos os sistemas. Erros: {'; '.join(error_messages)}"
        
        # Aplicar filtros de campos selecionados (se especificado)
        filtered_data = self._apply_field_filters(consolidated_data, processed_params.get("selected_fields", []))
        
        return {
            "success": overall_success,
            "data": filtered_data,
            "total_records": total_records,
            "databases_queried": list(results.keys()),
            "successful_databases": success_count,
            "message": message,
            "errors": error_messages if error_messages else None,
            "search_summary": {
                "search_type": processed_params.get("search_type"),
                "value_count": processed_params.get("count", 0),
                "databases": list(results.keys())
            }
        }
    
    def _apply_field_filters(self, data: List[Dict[str, Any]], selected_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Aplica filtros de campos selecionados aos dados.
        CORREÇÃO: Não aplica filtro se selected_fields estiver vazio para manter compatibilidade.
        
        Args:
            data (List[Dict[str, Any]]): Dados completos
            selected_fields (List[str]): Campos selecionados pelo usuário
            
        Returns:
            List[Dict[str, Any]]: Dados filtrados ou completos
        """
        if not data:
            return data
        
        # CORREÇÃO CRÍTICA: Se nenhum campo específico foi selecionado, 
        # retornar todos os dados SEM filtrar para evitar perda de dados
        if not selected_fields:
            logger.debug("Nenhum campo específico selecionado - retornando todos os dados")
            return data
        
        # Se campos foram selecionados, aplicar mapeamento correto
        # Mapeamento frontend (minúscula) -> banco (MAIÚSCULA)
        frontend_to_db_mapping = {
            'id_os': 'SERVICE_ORDER_ID',
            'protocolo': 'PROTOCOLO',
            'circuito': 'CIRCUITO',
            'subscrição': 'SUBSCRICAO',  # Já vem como alias da query
            'localidade': 'LOCALIDADE',
            'fila_atual': 'FILA_ATUAL',  # Alias da query
            'tipo_de_os': 'TIPO',  # Alias da query
            'data_de_criação': 'DATA_CRIACAO',
            'data_de_entrada_na_fila': 'DATA_ENTRADA_FILA'  # Alias da query
        }
        
        # Converter campos selecionados para nomes do banco
        db_fields_to_keep = []
        for field in selected_fields:
            if field in frontend_to_db_mapping:
                db_fields_to_keep.append(frontend_to_db_mapping[field])
            else:
                # Caso o campo já esteja no formato do banco
                db_fields_to_keep.append(field.upper())
        
        # Sempre manter campo essencial
        essential_fields = ["_source_database"]
        all_fields_to_keep = essential_fields + db_fields_to_keep
        
        filtered_data = []
        for record in data:
            filtered_record = {
                field: record.get(field) 
                for field in all_fields_to_keep 
                if field in record
            }
            # Se após filtro não sobrou nenhum campo além do essencial, manter tudo
            if len(filtered_record) <= len(essential_fields):
                logger.warning("Filtro removeu todos os campos de dados - mantendo registro original")
                filtered_data.append(record)
            else:
                filtered_data.append(filtered_record)
        
        logger.debug(f"Filtro aplicado: {len(selected_fields)} campos selecionados -> {len(db_fields_to_keep)} campos do banco")
        return filtered_data
    
    def test_backend_connectivity(self) -> Dict[str, Any]:
        """
        Testa conectividade com todos os sistemas backend.
        
        Returns:
            Dict[str, Any]: Status de conectividade
        """
        results = {}
        
        # Testar SOMPRD
        try:
            results["SOMPRD"] = db_config.test_connection("SOMPRD")
        except Exception as e:
            results["SOMPRD"] = {
                "success": False,
                "error": str(e),
                "message": f"Falha no teste SOMPRD: {str(e)}"
            }
        
        # Testar CMPRD
        try:
            results["CMPRD"] = db_config.test_connection("CMPRD")
        except Exception as e:
            results["CMPRD"] = {
                "success": False,
                "error": str(e),
                "message": f"Falha no teste CMPRD: {str(e)}"
            }
        
        # Resumo geral
        successful_connections = sum(1 for result in results.values() if result.get("success", False))
        total_connections = len(results)
        
        return {
            "overall_success": successful_connections > 0,
            "successful_connections": successful_connections,
            "total_connections": total_connections,
            "details": results,
            "message": f"{successful_connections}/{total_connections} conexões bem-sucedidas"
        }
    
    def _execute_chained_search(self, processed_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        NOVA FUNCIONALIDADE: Executa consulta encadeada SOMPRD → CMPRD.
        
        FLUXO:
        1. Executa consulta inicial no SOMPRD com parâmetros do usuário
        2. Extrai circuitos únicos dos resultados
        3. Executa segunda consulta no CMPRD usando os circuitos extraídos
        4. Retorna resultados da segunda consulta (CMPRD)
        
        Args:
            processed_params (Dict[str, Any]): Parâmetros processados da busca
            
        Returns:
            Dict[str, Any]: Resultado da consulta encadeada
        """
        try:
            logger.info("Iniciando consulta encadeada SOMPRD → CMPRD")
            
            # ETAPA 1: Executar consulta inicial no SOMPRD
            logger.debug("Etapa 1: Executando consulta inicial no SOMPRD...")
            somprd_result = somprd_queries.execute_search_query(processed_params)
            
            if not somprd_result.get("success", False):
                return {
                    "success": False,
                    "data": [],
                    "total_records": 0,
                    "message": f"Falha na consulta inicial SOMPRD: {somprd_result.get('message', 'Erro desconhecido')}",
                    "error": somprd_result.get('error', 'Consulta SOMPRD falhou'),
                    "chained_search": True,
                    "step_failed": "SOMPRD_INITIAL"
                }
            
            somprd_data = somprd_result.get("data", [])
            if not somprd_data:
                return {
                    "success": True,
                    "data": [],
                    "total_records": 0,
                    "message": "Consulta inicial no SOMPRD não retornou resultados. Consulta encadeada interrompida.",
                    "chained_search": True,
                    "step_completed": "SOMPRD_EMPTY"
                }
            
            logger.info(f"SOMPRD retornou {len(somprd_data)} registros")
            
            # ETAPA 2: Extrair circuitos únicos da coluna CIRCUITO
            logger.debug("Etapa 2: Extraindo circuitos únicos...")
            circuitos_unicos = set()
            
            for record in somprd_data:
                circuito = record.get("CIRCUITO", "").strip()
                if circuito:  # Só adicionar circuitos não vazios
                    circuitos_unicos.add(circuito)
            
            circuitos_list = list(circuitos_unicos)
            
            if not circuitos_list:
                return {
                    "success": True,
                    "data": [],
                    "total_records": 0,
                    "message": "Nenhum circuito válido encontrado nos resultados do SOMPRD. Consulta encadeada interrompida.",
                    "chained_search": True,
                    "step_completed": "SOMPRD_NO_CIRCUITS",
                    "somprd_records": len(somprd_data)
                }
            
            logger.info(f"Extraídos {len(circuitos_list)} circuitos únicos")
            
            # ETAPA 3: Preparar parâmetros para consulta no CMPRD
            logger.debug("Etapa 3: Preparando consulta no CMPRD...")
            cmprd_params = processed_params.copy()
            
            # Modificar parâmetros para busca por circuito no CMPRD
            cmprd_params.update({
                "search_type": "Circuito",
                "processed_values": circuitos_list,
                "count": len(circuitos_list),
                "original_search_type": processed_params.get("search_type"),  # Preservar tipo original
                "chained_from_somprd": True
            })
            
            # ETAPA 4: Executar consulta no CMPRD
            logger.debug(f"Etapa 4: Executando consulta no CMPRD com {len(circuitos_list)} circuitos...")
            cmprd_result = cmprd_queries.execute_search_query(cmprd_params)
            
            if not cmprd_result.get("success", False):
                return {
                    "success": False,
                    "data": [],
                    "total_records": 0,
                    "message": f"Falha na consulta CMPRD: {cmprd_result.get('message', 'Erro desconhecido')}",
                    "error": cmprd_result.get('error', 'Consulta CMPRD falhou'),
                    "chained_search": True,
                    "step_failed": "CMPRD_FINAL",
                    "somprd_records": len(somprd_data),
                    "circuitos_extraidos": len(circuitos_list)
                }
            
            # ETAPA 5: Preparar resultado final
            cmprd_data = cmprd_result.get("data", [])
            
            # Adicionar metadados da consulta encadeada
            for record in cmprd_data:
                record["_chained_search"] = True
                record["_source_database"] = "CMPRD"
                record["_original_search_type"] = processed_params.get("search_type")
            
            logger.info(f"Consulta encadeada concluída: {len(somprd_data)} → {len(circuitos_list)} → {len(cmprd_data)}")
            
            return {
                "success": True,
                "data": cmprd_data,
                "total_records": len(cmprd_data),
                "message": f"Consulta encadeada concluída. {len(somprd_data)} registros SOMPRD → {len(circuitos_list)} circuitos únicos → {len(cmprd_data)} registros CMPRD.",
                "chained_search": True,
                "chain_summary": {
                    "somprd_records": len(somprd_data),
                    "unique_circuits": len(circuitos_list),
                    "cmprd_records": len(cmprd_data),
                    "original_search_type": processed_params.get("search_type"),
                    "final_search_type": "Circuito"
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na consulta encadeada: {str(e)}")
            return {
                "success": False,
                "data": [],
                "total_records": 0,
                "message": f"Erro interno na consulta encadeada: {str(e)}",
                "error": str(e),
                "chained_search": True,
                "step_failed": "INTERNAL_ERROR"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o sistema backend.
        
        Returns:
            Dict[str, Any]: Informações do sistema
        """
        return {
            "backend_version": "1.0.0",
            "supported_databases": ["SOMPRD", "CMPRD"],
            "supported_search_types": [
                "Protocolo Algar SOM", "Circuito", "ID OS", "CTO", 
                "OLT", "PON", "Fila", "Localidade"
            ],
            "features": {
                "zero_padding": True,
                "oracle_large_in_clause": True,
                "multi_database_search": True,
                "field_filtering": True,
                "chained_search": True  # NOVA FUNCIONALIDADE
            },
            "limitations": {
                "oracle_in_clause_limit": 1000,
                "max_concurrent_connections": db_config.POOL_SIZE
            }
        }

# Instância global do gerenciador de serviços
service_manager = ServiceManager()
