# -*- coding: utf-8 -*-
"""
ACI Frontend - Consultas SOMPRD
Módulo responsável pelas consultas dinâmicas no banco SOMPRD
"""

import oracledb
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from .database_config import db_config
from .input_processor import InputProcessor

logger = logging.getLogger(__name__)

class SOMPRDQueries:
    """
    Classe responsável pelas consultas no banco SOMPRD.
    Implementa queries dinâmicas com tratamento de limitações Oracle.
    """
    
    # Nome da tabela conforme exemplo fornecido
    TABLE_NAME = "ALGARSOM.SOM_VW_SOM_WORKLIST"
    
    def __init__(self):
        """Inicializa o módulo de consultas SOMPRD."""
        self.database = "SOMPRD"
    
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
            'id_os': 'SERVICE_ORDER_ID',
            'protocolo': 'PROTOCOLO',
            'circuito': 'CIRCUITO',
            'subscrição': "'A' || ID_SUBSCRIPTION AS SUBSCRICAO",  # NOVO: com "A" na frente
            'localidade': 'LOCALIDADE',
            'fila_atual': 'ATIVIDADE AS FILA_ATUAL',
            'tipo_de_os': 'SERVICO AS TIPO',
            'data_de_criação': 'DATA_CRIACAO',
            'data_de_entrada_na_fila': 'START_DATE AS DATA_ENTRADA_FILA'
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
                'SERVICE_ORDER_ID',
                'PROTOCOLO', 
                'CIRCUITO',
                'ATIVIDADE AS FILA_ATUAL',
                'LOCALIDADE',
                'SERVICO AS TIPO',
                'DATA_CRIACAO',
                'START_DATE AS DATA_ENTRADA_FILA'
            ]
        
        select_clause = ', '.join(selected_db_fields)
        
        logger.info(f"Query construída com campos: {select_clause}")
        
        return f"""
        SELECT
            {select_clause}
        FROM {self.TABLE_NAME}
        WHERE 1=1
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
        
        # Filtros baseados no tipo de busca
        if search_type == 'Protocolo Algar SOM' and values:
            clause, clause_params = self._build_in_clause_with_chunks('PROTOCOLO', values, 'protocolo')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'Circuito' and values:
            clause, clause_params = self._build_in_clause_with_chunks('CIRCUITO', values, 'circuito')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'ID OS' and values:
            clause, clause_params = self._build_in_clause_with_chunks('SERVICE_ORDER_ID', values, 'service_order')
            where_clauses.append(clause)
            params.update(clause_params)
            
        elif search_type == 'Localidade' and values:
            clause, clause_params = self._build_in_clause_with_chunks('LOCALIDADE', values, 'localidade')
            where_clauses.append(clause)
            params.update(clause_params)
        
        # Filtros específicos por tipo de fila
        elif search_type == 'Fila':
            fila_selecionada = search_params.get('fila_value', '')
            
            if fila_selecionada == 'Massiva':
                where_clauses.append("AND ATIVIDADE = :atividade_massiva")
                params['atividade_massiva'] = 'SUSPEITA DE MASSIVA'
                
            elif fila_selecionada == 'Despacho':
                where_clauses.append("AND ATIVIDADE = :atividade_despacho AND SERVICO = :servico_despacho")
                params['atividade_despacho'] = 'DESPACHAR'
                params['servico_despacho'] = 'CORRETIVA DADOS'
                
            elif fila_selecionada == 'Triagem':
                where_clauses.append("AND ATIVIDADE LIKE :atividade_triagem AND SERVICO = :servico_triagem")
                params['atividade_triagem'] = '%TRIAGEM%'
                params['servico_triagem'] = 'CORRETIVA DADOS'
        
        # Filtros de período (se fornecidos)
        data_inicio = search_params.get('data_inicio')
        if data_inicio:
            where_clauses.append("AND DATA_CRIACAO BETWEEN TO_DATE(:data_inicio, 'DD/MM/YYYY') AND SYSDATE")
            params['data_inicio'] = data_inicio
        
        data_inicio_fila = search_params.get('data_inicio_fila')
        if data_inicio_fila:
            where_clauses.append("AND START_DATE BETWEEN TO_DATE(:data_inicio_fila, 'DD/MM/YYYY') AND SYSDATE")
            params['data_inicio_fila'] = data_inicio_fila
        
        # NOVA IMPLEMENTAÇÃO: Filtro "Apenas Corretiva de Dados"
        apenas_corretiva = search_params.get('apenas_corretiva', False)
        if apenas_corretiva:
            where_clauses.append("AND SERVICO = :servico_corretiva")
            params['servico_corretiva'] = 'CORRETIVA DADOS'
        
        return ' '.join(where_clauses), params
    
    def execute_search_query(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa consulta de busca no SOMPRD com parâmetros dinâmicos.
        
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
            
            logger.info(f"Executando consulta SOMPRD: {search_params.get('search_type', 'N/A')}")
            logger.debug(f"Query: {full_query}")
            logger.debug(f"Parâmetros: {len(params)} valores")
            
            # Executar query
            with connection.cursor() as cursor:
                start_time = datetime.now()
                cursor.execute(full_query, params)
                results = cursor.fetchall()
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Obter nomes das colunas
                column_names = [desc[0] for desc in cursor.description]
                
                # DEBUG: Log dos dados retornados do banco
                logger.debug(f"Query executada: {len(results)} linhas retornadas")
                logger.debug(f"Colunas: {column_names}")
                if results:
                    logger.debug(f"Primeira linha: {results[0]}")
            
            # REGRA DE NEGÓCIO CRUCIAL: Verificar se é busca por ID único sem resultados
            if (search_params.get('search_type') == 'ID OS' and 
                len(results) == 0 and 
                len(search_params.get('processed_values', [])) > 0):
                
                return {
                    "success": True,
                    "data": [],
                    "columns": column_names,
                    "count": 0,
                    "execution_time": execution_time,
                    "message": "A OS não foi encontrada e pode estar cancelada ou fechada.",
                    "search_params": search_params
                }
            
            # CORREÇÃO: Converter resultados para formato estruturado (como no exemplo)
            formatted_results = []
            for row in results:
                if row:  # Verificar se a linha não é None
                    row_dict = dict(zip(column_names, row))
                    # DEBUG: Log da conversão
                    if len(formatted_results) == 0:  # Log apenas da primeira linha
                        logger.debug(f"Primeira linha convertida: {row_dict}")
                    formatted_results.append(row_dict)
                else:
                    logger.warning("Linha vazia encontrada nos resultados")
            
            # NOVA REGRA: Manter ordem dos resultados conforme entrada do usuário
            if formatted_results and search_params.get('processed_values'):
                formatted_results = self._reorder_results_by_input(
                    formatted_results, 
                    search_params.get('processed_values', []),
                    search_params.get('search_type', '')
                )
            
            # NOVA REGRA: Tratar resultados vazios para SOMPRD
            if len(formatted_results) == 0:
                return {
                    "success": True,
                    "data": [],
                    "columns": column_names,
                    "count": 0,
                    "execution_time": execution_time,
                    "message": "OS pode estar fechada/cancelada/NE",
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
            logger.error(f"Erro na consulta SOMPRD: {str(e)}")
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
    
    def get_available_filas(self) -> Dict[str, Any]:
        """
        Obtém lista de filas disponíveis no sistema.
        
        Returns:
            Dict[str, Any]: Lista de filas e metadados
        """
        connection = None
        
        try:
            connection = db_config.get_connection(self.database)
            
            query = f"""
            SELECT DISTINCT ATIVIDADE
            FROM {self.TABLE_NAME}
            WHERE ATIVIDADE IS NOT NULL
            ORDER BY ATIVIDADE
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            filas = [row[0] for row in results if row[0]]
            
            return {
                "success": True,
                "filas": filas,
                "count": len(filas),
                "message": f"{len(filas)} filas encontradas"
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter filas: {str(e)}")
            return {
                "success": False,
                "filas": [],
                "error": str(e),
                "message": f"Erro ao consultar filas: {str(e)}"
            }
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def _reorder_results_by_input(self, results: List[Dict[str, Any]], input_values: List[str], search_type: str) -> List[Dict[str, Any]]:
        """
        NOVA REGRA: Reordena os resultados para manter a ordem da entrada do usuário.
        CRÍTICO: Inclui registros placeholder para valores não encontrados.
        
        Args:
            results (List[Dict[str, Any]]): Resultados da query
            input_values (List[str]): Valores de entrada na ordem original
            search_type (str): Tipo de busca para determinar o campo de ordenação
            
        Returns:
            List[Dict[str, Any]]: Resultados reordenados com placeholders
        """
        if not input_values:
            return results
        
        # Determinar campo de ordenação baseado no tipo de busca
        order_field_mapping = {
            'Protocolo Algar SOM': 'PROTOCOLO',
            'Circuito': 'CIRCUITO', 
            'ID OS': 'SERVICE_ORDER_ID',
            'Localidade': 'LOCALIDADE'
        }
        
        order_field = order_field_mapping.get(search_type)
        if not order_field:
            logger.debug(f"Tipo de busca {search_type} não suporta reordenação com placeholders")
            return results
        
        # NOVA LÓGICA: Criar placeholders para valores não encontrados
        if search_type == 'Protocolo Algar SOM':
            return self._create_protocol_placeholders(results, input_values, order_field)
        else:
            # Para outros tipos, usar lógica padrão sem placeholders
            return self._reorder_without_placeholders(results, input_values, order_field)
    
    def _create_protocol_placeholders(self, results: List[Dict[str, Any]], input_protocols: List[str], order_field: str) -> List[Dict[str, Any]]:
        """
        NOVA FUNÇÃO: Cria placeholders para protocolos não encontrados.
        
        Args:
            results (List[Dict[str, Any]]): Resultados encontrados no banco
            input_protocols (List[str]): Protocolos consultados pelo usuário
            order_field (str): Campo para ordenação
            
        Returns:
            List[Dict[str, Any]]: Lista com resultados + placeholders na ordem original
        """
        # Criar mapa de resultados encontrados
        results_map = {}
        for result in results:
            protocol_value = str(result.get(order_field, '')).strip()
            if protocol_value:
                results_map[protocol_value] = result
        
        # Obter template de campos do primeiro resultado (se existir)
        field_template = {}
        if results:
            for key in results[0].keys():
                field_template[key] = None  # Valores nulos por padrão
        else:
            # Template mínimo se não há resultados
            field_template = {
                'PROTOCOLO': None,
                'SERVICE_ORDER_ID': None,
                'CIRCUITO': None,
                'ATIVIDADE': 'Cancelado/Fechado/NE',
                'LOCALIDADE': None,
                'SERVICO': None,
                'DATA_CRIACAO': None,
                'START_DATE': None,
                '_source_database': 'SOMPRD'
            }
        
        # Construir lista final na ordem de entrada
        final_results = []
        for protocol in input_protocols:
            protocol = str(protocol).strip()
            
            if protocol in results_map:
                # Protocolo encontrado - usar dados reais
                final_results.append(results_map[protocol])
            else:
                # Protocolo não encontrado - criar placeholder
                placeholder = field_template.copy()
                placeholder['PROTOCOLO'] = protocol
                placeholder['ATIVIDADE'] = 'Cancelado/Fechado/NE'
                final_results.append(placeholder)
        
        logger.info(f"Protocolos processados: {len(input_protocols)} entrada(s), {len(results)} encontrado(s), {len(input_protocols) - len(results)} placeholder(s)")
        return final_results
    
    def _reorder_without_placeholders(self, results: List[Dict[str, Any]], input_values: List[str], order_field: str) -> List[Dict[str, Any]]:
        """
        Reordenação padrão sem criação de placeholders.
        
        Args:
            results (List[Dict[str, Any]]): Resultados da query
            input_values (List[str]): Valores de entrada na ordem original
            order_field (str): Campo para ordenação
            
        Returns:
            List[Dict[str, Any]]: Resultados reordenados (apenas encontrados)
        """
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
        
        logger.debug(f"Reordenação sem placeholders concluída: {len(input_values)} entradas -> {len(reordered_results)} resultados encontrados")
        return reordered_results
    
    def obter_localidades_unicas(self) -> List[str]:
        """
        NOVA FUNÇÃO: Obtém lista de localidades únicas do banco SOMPRD.
        
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
            ORDER BY LOCALIDADE ASC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            localidades = [row[0] for row in results if row[0] and row[0].strip()]
            
            logger.info(f"Localidades únicas encontradas: {len(localidades)}")
            return localidades
            
        except Exception as e:
            logger.error(f"Erro ao obter localidades únicas: {str(e)}")
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
            test_query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE ROWNUM <= 1"
            
            with connection.cursor() as cursor:
                cursor.execute(test_query)
                result = cursor.fetchone()
            
            return {
                "success": True,
                "table_accessible": True,
                "table_name": self.TABLE_NAME,
                "message": "Acesso à tabela confirmado"
            }
            
        except Exception as e:
            logger.error(f"Erro no teste de acesso à tabela: {str(e)}")
            return {
                "success": False,
                "table_accessible": False,
                "table_name": self.TABLE_NAME,
                "error": str(e),
                "message": f"Falha no acesso à tabela: {str(e)}"
            }
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)

# Instância global das consultas SOMPRD
somprd_queries = SOMPRDQueries()
