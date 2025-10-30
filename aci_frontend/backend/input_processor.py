# -*- coding: utf-8 -*-
"""
ACI Frontend - Processador de Inputs
Responsável pelo pré-processamento de dados vindos do frontend
"""

import re
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class InputProcessor:
    """
    Classe responsável pelo pré-processamento de inputs do usuário.
    Aplica transformações necessárias antes da execução das consultas.
    """
    
    @staticmethod
    def add_leading_zeros_protocolo(values: List[str]) -> List[str]:
        """
        Adiciona dois zeros à esquerda dos valores de protocolo.
        
        REGRA: Operação incondicional, sem validar conteúdo ou tamanho.
        
        Args:
            values (List[str]): Lista de protocolos originais
            
        Returns:
            List[str]: Lista com protocolos processados (00 + valor original)
            
        Examples:
            >>> InputProcessor.add_leading_zeros_protocolo(["123", "abc"])
            ["00123", "00abc"]
        """
        if not values:
            return []
        
        processed = [f"00{value}" for value in values]
        logger.debug(f"Protocolos processados: {len(values)} valores com zeros adicionados")
        return processed
    
    @staticmethod
    def add_leading_zero_circuito(values: List[str]) -> List[str]:
        """
        Adiciona um zero à esquerda dos valores de circuito.
        
        REGRA: Operação incondicional, sem validar conteúdo ou tamanho.
        
        Args:
            values (List[str]): Lista de circuitos originais
            
        Returns:
            List[str]: Lista com circuitos processados (0 + valor original)
            
        Examples:
            >>> InputProcessor.add_leading_zero_circuito(["456", "xyz"])
            ["0456", "0xyz"]
        """
        if not values:
            return []
        
        processed = [f"0{value}" for value in values]
        logger.debug(f"Circuitos processados: {len(values)} valores com zero adicionado")
        return processed
    
    @staticmethod
    def clean_and_split_input(raw_input: str) -> List[str]:
        """
        Limpa e divide entrada bruta do usuário em lista de valores únicos.
        
        Args:
            raw_input (str): Texto bruto do campo de entrada (múltiplas linhas)
            
        Returns:
            List[str]: Lista de valores únicos, limpos e não vazios
        """
        if not raw_input or not raw_input.strip():
            return []
        
        # Dividir por quebras de linha e limpar espaços
        lines = raw_input.strip().split('\n')
        
        # Remover espaços em branco, valores vazios e duplicatas
        cleaned_values = []
        seen = set()
        
        for line in lines:
            value = line.strip()
            if value and value not in seen:
                cleaned_values.append(value)
                seen.add(value)
        
        logger.debug(f"Input processado: {len(cleaned_values)} valores únicos extraídos")
        return cleaned_values
    
    @staticmethod
    def process_search_params(search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa parâmetros de busca vindos do frontend.
        Aplica transformações necessárias baseadas no tipo de busca e opções selecionadas.
        
        Args:
            search_data (Dict[str, Any]): Dados da busca do frontend
                - search_type: Tipo de busca (Protocolo, Circuito, etc.)
                - values: String com valores separados por linha
                - add_zeros_protocolo: Boolean se deve adicionar zeros para protocolo
                - add_zero_circuito: Boolean se deve adicionar zero para circuito
                - outros campos específicos...
                
        Returns:
            Dict[str, Any]: Parâmetros processados para consulta SQL
        """
        try:
            search_type = search_data.get('search_type', '').strip()
            raw_values = search_data.get('values', '')
            
            # Limpar e dividir valores de entrada
            values = InputProcessor.clean_and_split_input(raw_values)
            
            if not values:
                return {
                    "processed_values": [],
                    "search_type": search_type,
                    "error": "Nenhum valor válido fornecido"
                }
            
            # Aplicar transformações baseadas no tipo e opções
            processed_values = values.copy()
            
            # REGRA CRÍTICA: Adicionar zeros conforme solicitado
            if search_data.get('add_zeros_protocolo', False) and 'Protocolo' in search_type:
                processed_values = InputProcessor.add_leading_zeros_protocolo(processed_values)
                logger.info(f"Aplicada regra de zeros para protocolo: {len(processed_values)} valores")
            
            elif search_data.get('add_zero_circuito', False) and 'Circuito' in search_type:
                processed_values = InputProcessor.add_leading_zero_circuito(processed_values)
                logger.info(f"Aplicada regra de zero para circuito: {len(processed_values)} valores")
            
            return {
                "processed_values": processed_values,
                "original_values": values,
                "search_type": search_type,
                "count": len(processed_values),
                "transformations_applied": {
                    "protocolo_zeros": search_data.get('add_zeros_protocolo', False) and 'Protocolo' in search_type,
                    "circuito_zero": search_data.get('add_zero_circuito', False) and 'Circuito' in search_type
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento de parâmetros: {str(e)}")
            return {
                "processed_values": [],
                "search_type": search_type,
                "error": f"Erro no processamento: {str(e)}"
            }
    
    @staticmethod
    def validate_search_type(search_type: str) -> Dict[str, Any]:
        """
        Valida se o tipo de busca é suportado.
        
        Args:
            search_type (str): Tipo de busca fornecido
            
        Returns:
            Dict[str, Any]: Resultado da validação
        """
        valid_types = [
            'Protocolo Algar SOM', 'Circuito', 'ID OS', 'CTO', 
            'OLT', 'PON', 'Fila', 'Localidade'
        ]
        
        is_valid = search_type in valid_types
        
        return {
            "is_valid": is_valid,
            "search_type": search_type,
            "valid_types": valid_types,
            "message": "Tipo de busca válido" if is_valid else f"Tipo '{search_type}' não suportado"
        }
    
    @staticmethod
    def split_values_for_oracle_in_clause(values: List[str], chunk_size: int = 1000) -> List[List[str]]:
        """
        CRÍTICO: Divide lista de valores em chunks para contornar limitação Oracle de 1000 elementos por IN.
        
        Args:
            values (List[str]): Lista completa de valores
            chunk_size (int): Tamanho máximo por chunk (padrão: 1000)
            
        Returns:
            List[List[str]]: Lista de chunks, cada um com no máximo chunk_size elementos
            
        Examples:
            >>> values = ["val" + str(i) for i in range(1500)]
            >>> chunks = InputProcessor.split_values_for_oracle_in_clause(values)
            >>> len(chunks)  # Resultado: 2 (1000 + 500)
            2
        """
        if not values:
            return []
        
        chunks = []
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i + chunk_size]
            chunks.append(chunk)
        
        logger.debug(f"Valores divididos em {len(chunks)} chunks para Oracle IN clause")
        return chunks

# Instância global do processador
input_processor = InputProcessor()
