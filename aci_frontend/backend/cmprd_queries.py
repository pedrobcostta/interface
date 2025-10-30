# -*- coding: utf-8 -*-
"""
ACI Frontend - Consultas CMPRD
Módulo responsável pelas consultas dinâmicas no banco Connect Master
"""

import oracledb
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from .database_config import db_config
from .input_processor import InputProcessor

logger = logging.getLogger(__name__)

class CMPRDQueries:
    """
    Classe responsável pelas consultas no banco CMPRD (Connect Master).
    Implementa queries dinâmicas com tratamento de limitações Oracle.
    """
    
    # Nome da tabela conforme especificação
    TABLE_NAME = "API.MVW_FACILITY_FULL"
    
    def __init__(self):
        """Inicializa o módulo de consultas CMPRD."""
        self.database = "CMPRD"
    
    def _build_dynamic_query(self, selected_fields: List[str]) -> str:
        """
        Constrói query dinâmica baseada nos campos selecionados pelo usuário.
        
        Args:
            selected_fields (List[str]): Campos selecionados no frontend
            
        Returns:
            str: Query SQL com campos dinâmicos
        """
        # DEBUG: Log dos campos recebidos
        logger.debug(f"Campos selecionados recebidos: {selected_fields}")
        
        # Mapeamento frontend -> banco de dados
        field_mapping = {
            'cto': 'CTO',
            'porta_da_cto': 'PORTA AS PORTA_CTO',
            'status_(ocupado,_vago,_etc)': 'STATUS AS STATUS_PORTA_CTO',
            'olt': 'OLT',
            'nome_da_gerencia_da_olt': 'NOME_OLT_GERENCIA',
            'ip_da_olt': 'IP_DADOS_OLT',
            'shelf/slot/porta': 'SHELF_SLOT_PORTA',
            'tecnologia': 'FABRICANTE AS TECNOLOGIA',
            'serial': 'SERIAL',
            "vlan's": 'OUTER_VLAN, INNER_VLAN',
            'localidade': 'LOCALIDADE',
            'estacao': 'ESTACAO'
        }
        
        # CORREÇÃO: Usar sempre campos padrão se lista estiver vazia ou inválida
        selected_db_fields = []
        
        # Se há campos selecionados, tentar mapeá-los
        if selected_fields:
            for field in selected_fields:
                if field in field_mapping:
                    selected_db_fields.append(field_mapping[field])
                    logger.debug(f"Campo mapeado: {field} -> {field_mapping[field]}")
        
        # Se nenhum campo foi mapeado com sucesso, usar campos padrão
        if not selected_db_fields:
            logger.info("Nenhum campo selecionado válido, usando campos padrão")
            selected_db_fields = [
                'CTO',
                'PORTA AS PORTA_CTO', 
                'STATUS AS STATUS_PORTA_CTO',
                'SHELF_SLOT_PORTA',
                'LOCALIDADE',
                'ESTACAO',
                'FABRICANTE AS TECNOLOGIA',
                'OLT',
                'NOME_OLT_GERENCIA',
                'IP_DADOS_OLT',
                'OUTER_VLAN',
                'INNER_VLAN'
            ]
        
        select_clause = ', '.join(selected_db_fields)
        
        logger.info(f"Query construída com campos: {select_clause}")
        
        return f"""
        SELECT
            {select_clause}
        FROM {self.TABLE_NAME}
        WHERE 1=1
        AND STATUS = 'OCUPADO'
        """
    
    def _build_in_clause_with_chunks(self, field_name: str, values: List[str], param_prefix: str) -> Tuple[str, Dict[str, str]]:
        """
        CRÍTICO: Constrói cláusula IN com tratamento de limitação Oracle (1000 elementos).
        
        Args:
            field_name (str): Nome do campo na query
            values (List[str]): Lista de valores para o IN
            param_prefix (str): Prefixo para os parâmetros
            
        Returns:
            Tuple[str, Dict[str, str]]: (cláusula SQL, dicionário de parâmetros)
        """
        if not values:
            return "", {}
        
        # Dividir valores em chunks de 1000
        chunks = InputProcessor.split_values_for_oracle_in_clause(values)
        
        if len(chunks) == 1:
            # Caso simples: apenas um chunk
            params = {}
            param_names = []
            
            for i, value in enumerate(chunks[0]):
                param_name = f"{param_prefix}_{i+1}"
                params[param_name] = value
                param_names.append(f":{param_name}")
            
            clause = f"AND {field_name} IN ({', '.join(param_names)})"
            
        else:
            # Caso complexo: múltiplos chunks unidos por OR
            or_clauses = []
            params = {}
            
            for chunk_idx, chunk in enumerate(chunks):
                param_names = []
                
                for i, value in enumerate(chunk):
                    param_name = f"{param_prefix}_c{chunk_idx+1}_{i+1}"
                    params[param_name] = value
                    param_names.append(f":{param_name}")
                
                or_clauses.append(f"{field_name} IN ({', '.join(param_names)})")
            
            clause = f"AND ({' OR '.join(or_clauses)})"
        
        logger.debug(f"Cláusula IN construída para {field_name}: {len(chunks)} chunks, {len(values)} valores")
        return clause, params
    
    def _build_dynamic_filters(self, search_params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Constrói filtros dinâmicos baseado nos parâmetros de busca.
        
        Args:
            search_params (Dict[str, Any]): Parâmetros processados de busca
            
        Returns:
            Tuple[str, Dict[str, Any]]: (cláusulas WHERE adicionais, parâmetros)
        """
        where_clauses = []
        params = {}
        
        search_type = search_params.get('search_type', '')
        values = search_params.get('processed_values', [])
        
        # NOVA IMPLEMENTAÇÃO: Filtros baseados no tipo de busca para Connect Master
        if search_type == 'Circuito' and values:
            clause, clause_params = self._build_in_clause_with_chunks('CIRCUITO', values, 'circuito')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'CTO' and values:
            clause, clause_params = self._build_in_clause_with_chunks('CTO', values, 'cto')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'Localidade' and values:
            clause, clause_params = self._build_in_clause_with_chunks('LOCALIDADE', values, 'localidade')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'VLAN Outer' and values:
            clause, clause_params = self._build_in_clause_with_chunks('OUTER_VLAN', values, 'vlan_outer')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'IP da OLT' and values:
            clause, clause_params = self._build_in_clause_with_chunks('IP_DADOS_OLT', values, 'ip_olt')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'OLT' and values:
            clause, clause_params = self._build_in_clause_with_chunks('OLT', values, 'olt_nome')
            where_clauses.append(clause)
            params.update(clause_params)
        
        # NOVA IMPLEMENTAÇÃO: Filtros PON (complexos)
        elif search_type == 'PON':
            pon_info = search_params.get('pon_info', {})
            pon_value = pon_info.get('shelf_slot_porta', '')
            olt_type = pon_info.get('olt_type', 'nome')  # 'nome', 'gerencia', 'ip', 'vlan'
            olt_value = pon_info.get('olt_value', '')
            
            if pon_value and olt_value:
                # Filtro PON específico
                where_clauses.append("AND SHELF_SLOT_PORTA = :pon_value")
                params['pon_value'] = pon_value
                
                # Filtro OLT baseado no tipo
                if olt_type == 'nome':
                    where_clauses.append("AND OLT = :olt_value")
                elif olt_type == 'gerencia':
                    where_clauses.append("AND NOME_OLT_GERENCIA = :olt_value")
                elif olt_type == 'ip':
                    where_clauses.append("AND IP_DADOS_OLT = :olt_value")
                elif olt_type == 'vlan':
                    where_clauses.append("AND OUTER_VLAN = :olt_value")
                
                params['olt_value'] = olt_value
        
        # NOVA IMPLEMENTAÇÃO: Filtro "Apenas Corretiva de Dados"
        apenas_corretiva = search_params.get('apenas_corretiva', False)
        if apenas_corretiva:
            where_clauses.append("AND TIPO = :tipo_corretiva")
            params['tipo_corretiva'] = 'CORRETIVA DADOS'
        
        return ' '.join(where_clauses), params
    
    def execute_search_query(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa consulta de busca no CMPRD com parâmetros dinâmicos.
        
        Args:
            search_params (Dict[str, Any]): Parâmetros processados de busca
            
        Returns:
            Dict[str, Any]: Resultado da consulta com dados e metadados
        """
        connection = None
        
        try:
            # Obter conexão
            connection = db_config.get_connection(self.database)
            
            # Construir query dinâmica com campos selecionados
            selected_fields = search_params.get('selected_fields', [])
            base_query = self._build_dynamic_query(selected_fields)
            dynamic_filters, params = self._build_dynamic_filters(search_params)
            
            full_query = base_query + dynamic_filters
            
            logger.info(f"Executando consulta CMPRD: {search_params.get('search_type', 'N/A')}")
            logger.debug(f"Query: {full_query}")
            logger.debug(f"Parâmetros: {len(params)} valores")
            
            # Executar query
            with connection.cursor() as cursor:
                start_time = datetime.now()
                
                # DEBUG CRÍTICO: Log da query completa e parâmetros
                logger.info(f"=== CMPRD DEBUG QUERY ===")
                logger.info(f"Query: {full_query}")
                logger.info(f"Parâmetros: {params}")
                logger.info(f"Total parâmetros: {len(params)}")
                
                cursor.execute(full_query, params)
                results = cursor.fetchall()
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Obter nomes das colunas
                column_names = [desc[0] for desc in cursor.description]
                
                # DEBUG CRÍTICO: Log detalhado dos resultados
                logger.info(f"=== CMPRD RESULTADOS ===")
                logger.info(f"Linhas retornadas: {len(results)}")
                logger.info(f"Colunas: {column_names}")
                
                if results:
                    logger.info(f"Primeira linha: {results[0]}")
                    if len(results) > 1:
                        logger.info(f"Segunda linha: {results[1]}")
                    if len(results) > 5:
                        logger.info(f"Amostra de 5 linhas: {results[:5]}")
                else:
                    logger.warning("NENHUM RESULTADO RETORNADO!")
            
            # CORREÇÃO: Converter resultados para formato estruturado
            formatted_results = []
            for row in results:
                if row:  # Verificar se a linha não é None
                    row_dict = dict(zip(column_names, row))
                    # Adicionar identificador da fonte
                    row_dict['_source_database'] = 'CMPRD'
                    # DEBUG: Log da conversão
                    if len(formatted_results) == 0:  # Log apenas da primeira linha
                        logger.debug(f"Primeira linha convertida: {row_dict}")
                    formatted_results.append(row_dict)
                else:
                    logger.warning("Linha vazia encontrada nos resultados")
            
            # NOVA REGRA: Manter ordem dos resultados conforme entrada do usuário (se aplicável)
            if formatted_results and search_params.get('processed_values'):
                formatted_results = self._reorder_results_by_input(
                    formatted_results, 
                    search_params.get('processed_values', []),
                    search_params.get('search_type', '')
                )
            
            # NOVA REGRA: Tratar resultados vazios para CMPRD
            if len(formatted_results) == 0:
                return {
                    "success": True,
                    "data": [],
                    "columns": column_names,
                    "count": 0,
                    "execution_time": execution_time,
                    "message": "Nenhum registro encontrado no Connect Master.",
                    "search_params": search_params
                }
            
            return {
                "success": True,
                "data": formatted_results,
                "columns": column_names,
                "count": len(results),
                "execution_time": execution_time,
                "message": f"Consulta executada com sucesso. {len(results)} registro(s) encontrado(s).",
                "search_params": search_params
            }
            
        except Exception as e:
            logger.error(f"Erro na consulta CMPRD: {str(e)}")
            return {
                "success": False,
                "data": [],
                "columns": [],
                "count": 0,
                "error": str(e),
                "message": f"Erro na execução da consulta: {str(e)}",
                "search_params": search_params
            }
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def _reorder_results_by_input(self, results: List[Dict[str, Any]], input_values: List[str], search_type: str) -> List[Dict[str, Any]]:
        """
        Reordena os resultados para manter a ordem da entrada do usuário.
        
        Args:
            results (List[Dict[str, Any]]): Resultados da query
            input_values (List[str]): Valores de entrada na ordem original
            search_type (str): Tipo de busca para determinar o campo de ordenação
            
        Returns:
            List[Dict[str, Any]]: Resultados reordenados
        """
        if not results or not input_values:
            return results
        
        # Determinar campo de ordenação baseado no tipo de busca
        order_field_mapping = {
            'Circuito': 'CIRCUITO',
            'CTO': 'CTO', 
            'Localidade': 'LOCALIDADE',
            'VLAN Outer': 'OUTER_VLAN',
            'IP da OLT': 'IP_DADOS_OLT',
            'OLT': 'OLT'
        }
        
        order_field = order_field_mapping.get(search_type)
        if not order_field:
            logger.debug(f"Tipo de busca {search_type} não suporta reordenação no CMPRD")
            return results
        
        # Criar mapa de resultados por valor do campo de ordenação
        results_map = {}
        for result in results:
            field_value = str(result.get(order_field, '')).strip()
            if field_value:
                results_map[field_value] = result
        
        # Reordenar baseado na ordem de entrada
        reordered_results = []
        for input_value in input_values:
            input_value = str(input_value).strip()
            if input_value in results_map:
                reordered_results.append(results_map[input_value])
                # Remover do mapa para evitar duplicatas
                del results_map[input_value]
        
        # Adicionar resultados não mapeados no final
        reordered_results.extend(results_map.values())
        
        logger.debug(f"Reordenação CMPRD concluída: {len(input_values)} entradas -> {len(reordered_results)} resultados ordenados")
        return reordered_results
    
    def obter_localidades_unicas(self) -> List[str]:
        """
        Obtém lista de localidades únicas do banco CMPRD.
        
        Returns:
            List[str]: Lista de localidades únicas ordenadas alfabeticamente
        """
        connection = None
        
        try:
            connection = db_config.get_connection(self.database)
            
            query = f"""
            SELECT DISTINCT LOCALIDADE 
            FROM {self.TABLE_NAME} 
            WHERE LOCALIDADE IS NOT NULL 
            AND STATUS = 'OCUPADO'
            ORDER BY LOCALIDADE ASC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            localidades = [row[0] for row in results if row[0] and row[0].strip()]
            
            logger.info(f"Localidades únicas CMPRD encontradas: {len(localidades)}")
            return localidades
            
        except Exception as e:
            logger.error(f"Erro ao obter localidades únicas CMPRD: {str(e)}")
            return []
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def obter_ctos_unicas(self) -> List[str]:
        """
        Obtém lista de CTOs únicas do banco CMPRD.
        
        Returns:
            List[str]: Lista de CTOs únicas ordenadas alfabeticamente
        """
        connection = None
        
        try:
            connection = db_config.get_connection(self.database)
            
            query = f"""
            SELECT DISTINCT CTO 
            FROM {self.TABLE_NAME} 
            WHERE CTO IS NOT NULL 
            AND STATUS = 'OCUPADO'
            ORDER BY CTO ASC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            ctos = [row[0] for row in results if row[0] and row[0].strip()]
            
            logger.info(f"CTOs únicas encontradas: {len(ctos)}")
            return ctos
            
        except Exception as e:
            logger.error(f"Erro ao obter CTOs únicas: {str(e)}")
            return []
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def obter_olts_unicas(self) -> List[str]:
        """
        Obtém lista de OLTs únicas do banco CMPRD.
        
        Returns:
            List[str]: Lista de OLTs únicas ordenadas alfabeticamente
        """
        connection = None
        
        try:
            connection = db_config.get_connection(self.database)
            
            query = f"""
            SELECT DISTINCT OLT 
            FROM {self.TABLE_NAME} 
            WHERE OLT IS NOT NULL 
            AND STATUS = 'OCUPADO'
            ORDER BY OLT ASC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            olts = [row[0] for row in results if row[0] and row[0].strip()]
            
            logger.info(f"OLTs únicas encontradas: {len(olts)}")
            return olts
            
        except Exception as e:
            logger.error(f"Erro ao obter OLTs únicas: {str(e)}")
            return []
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def test_table_access(self) -> Dict[str, Any]:
        """
        Testa acesso à tabela principal e retorna informações básicas.
        
        Returns:
            Dict[str, Any]: Resultado do teste
        """
        connection = None
        
        try:
            connection = db_config.get_connection(self.database)
            
            # Testar acesso básico
            test_query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE ROWNUM <= 1 AND STATUS = 'OCUPADO'"
            
            with connection.cursor() as cursor:
                cursor.execute(test_query)
                result = cursor.fetchone()
            
            return {
                "success": True,
                "table_accessible": True,
                "table_name": self.TABLE_NAME,
                "message": "Acesso à tabela CMPRD confirmado"
            }
            
        except Exception as e:
            logger.error(f"Erro no teste de acesso à tabela CMPRD: {str(e)}")
            return {
                "success": False,
                "table_accessible": False,
                "table_name": self.TABLE_NAME,
                "error": str(e),
                "message": f"Falha no acesso à tabela CMPRD: {str(e)}"
            }
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)

# Instância global das consultas CMPRD
cmprd_queries = CMPRDQueries()
