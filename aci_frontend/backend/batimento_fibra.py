# -*- coding: utf-8 -*-
"""
ACI Frontend - Módulo de Batimento de Fibra
Adaptação do script de batimento para integração com a aplicação
"""

import pandas as pd
import os
import re
import telnetlib
from time import sleep
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

from .database_config import db_config

logger = logging.getLogger(__name__)

class BatimentoFibra:
    """
    Classe responsável pelo batimento de sinal de fibra óptica em OLTs.
    Versão adaptada e integrada ao sistema ACI Frontend.
    """
    
    def __init__(self):
        """Inicializa o módulo de batimento de fibra."""
        self.database = "CMPRD"  # Base de dados para consulta de circuitos
        
        # Configurações de credenciais (carregadas do .env)
        self.credentials = self._load_credentials_from_env()
    
    def _load_credentials_from_env(self) -> Dict[str, Dict[str, str]]:
        """
        CRÍTICO: Carrega credenciais do arquivo .env ao invés de hardcoded.
        
        Returns:
            Dict[str, Dict[str, str]]: Credenciais organizadas por tecnologia
        """
        try:
            # Configurações FiberHome
            fiberhome_config = {
                'ip': os.getenv('FIBERHOME_IP', ''),
                'porta': os.getenv('FIBERHOME_PORTA', ''),
                'usuario': os.getenv('FIBERHOME_USUARIO', ''),
                'senha': os.getenv('FIBERHOME_SENHA', '')
            }
            
            # Configurações Huawei
            huawei_config = {
                'ip': os.getenv('HUAWEI_IP', ''),
                'porta': os.getenv('HUAWEI_PORTA', ''),
                'usuario': os.getenv('HUAWEI_USUARIO', ''),
                'senha': os.getenv('HUAWEI_SENHA', '')
            }
            
            # Configurações Nokia
            nokia_config = {
                'usuario': os.getenv('NOKIA_USUARIO', ''),
                'senha': os.getenv('NOKIA_SENHA', '')
            }
            
            # Configurações ZTE
            zte_config = {
                'usuario': os.getenv('ZTE_USUARIO', ''),
                'senha': os.getenv('ZTE_SENHA', '')
            }
            
            # Configurações Zhone
            zhone_config = {
                'usuario': os.getenv('ZHONE_USUARIO', 'admin'),
                'senha': os.getenv('ZHONE_SENHA', 'zhone')
            }
            
            return {
                'fiberhome': fiberhome_config,
                'huawei': huawei_config,
                'nokia': nokia_config,
                'zte': zte_config,
                'zhone': zhone_config
            }
            
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais do .env: {str(e)}")
            return {}
    
    def obter_info_circuitos(self, circuitos: List[str]) -> pd.DataFrame:
        """
        MODIFICADO: Consulta informações dos circuitos usando conexão existente do sistema.
        
        Args:
            circuitos (List[str]): Lista de circuitos para consulta
            
        Returns:
            pd.DataFrame: Informações dos circuitos
        """
        if not circuitos:
            return pd.DataFrame()
        
        connection = None
        
        try:
            # Usar conexão existente do sistema
            connection = db_config.get_connection(self.database)
            
            # Construir query com placeholders
            placeholders = ','.join([f':param{i+1}' for i in range(len(circuitos))])
            query = f"""
                SELECT
                    CIRCUITO,
                    CTO,
                    SHELF_SLOT_PORTA,
                    FABRICANTE,
                    IP_DADOS_OLT,
                    SERIAL
                FROM API.MVW_FACILITY_FULL
                WHERE OUTER_VLAN IS NOT NULL
                AND CIRCUITO IN ({placeholders})
            """
            
            # Preparar parâmetros
            params = {f'param{i+1}': circuito for i, circuito in enumerate(circuitos)}
            
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                df = pd.DataFrame(rows, columns=columns)
                
                # Renomear colunas para padrão do script
                df.rename(columns={
                    'CIRCUITO': 'Circuito',
                    'CTO': 'CTO',
                    'SHELF_SLOT_PORTA': 'shelf_slot_porta',
                    'FABRICANTE': 'Tecnologia',
                    'IP_DADOS_OLT': 'ip_olt',
                    'SERIAL': 'serial'
                }, inplace=True)
                
                logger.info(f"Consulta circuitos: {len(circuitos)} solicitados, {len(df)} encontrados")
                return df
                
        except Exception as e:
            logger.error(f"Erro ao consultar circuitos no banco: {str(e)}")
            return pd.DataFrame()
            
        finally:
            if connection:
                db_config.release_connection(connection, self.database)
    
    def executar_batimento_fibra(self, circuitos: List[str]) -> pd.DataFrame:
        """
        FUNÇÃO PRINCIPAL: Executa o batimento de fibra para lista de circuitos.
        
        Args:
            circuitos (List[str]): Lista de circuitos para batimento
            
        Returns:
            pd.DataFrame: Resultados do batimento
        """
        if not circuitos:
            logger.warning("Batimento de Fibra: Nenhum circuito foi fornecido.")
            return pd.DataFrame()
        
        try:
            logger.info(f"Batimento de Fibra: Iniciando para {len(circuitos)} circuitos...")
            
            # 1. Consultar informações dos circuitos no banco
            df_circuitos_db = self.obter_info_circuitos(circuitos)
            
            if df_circuitos_db.empty:
                logger.warning("Batimento de Fibra: Nenhuma informação encontrada para os circuitos no banco.")
                return self._criar_resultados_vazios(circuitos)
            
            # 2. Identificar circuitos encontrados e não encontrados
            circuitos_encontrados_db = df_circuitos_db['Circuito'].tolist()
            circuitos_nao_encontrados = [c for c in circuitos if c not in circuitos_encontrados_db]
            
            # 3. Pré-processar dados e separar por tecnologia
            df_circuitos_db['Tecnologia'] = df_circuitos_db['Tecnologia'].fillna('Desconhecida')
            
            # Separar por tecnologia para otimizar processamento
            is_nokia = df_circuitos_db['Tecnologia'].str.contains("NOKIA", na=False)
            is_zte = df_circuitos_db['Tecnologia'].str.contains("ZTE", na=False)
            
            df_nokia = df_circuitos_db[is_nokia]
            df_zte = df_circuitos_db[is_zte]
            df_outros = df_circuitos_db[~is_nokia & ~is_zte]
            
            resultados_finais = []
            
            # 4. Processar por grupos baseado na tecnologia
            if not df_outros.empty:
                logger.info(f"Batimento: Processando {len(df_outros)} circuitos (outras tecnologias) em paralelo...")
                resultados_finais.extend(
                    self._processar_em_lote_thread(df_outros.to_dict('records'), max_threads=15)
                )
            
            if not df_zte.empty:
                logger.info(f"Batimento: Processando {len(df_zte)} circuitos (ZTE) em paralelo (máx 2 threads)...")
                resultados_finais.extend(
                    self._processar_em_lote_thread(df_zte.to_dict('records'), max_threads=2)
                )
            
            if not df_nokia.empty:
                logger.info(f"Batimento: Processando {len(df_nokia)} circuitos (Nokia) sequencial...")
                for _, row in df_nokia.iterrows():
                    logger.debug(f"  -> Processando Nokia: {row['Circuito']}")
                    resultados_finais.append(self._processar_circuito(row.to_dict()))
            
            # 5. Adicionar circuitos não encontrados no banco
            data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            for circuito in circuitos_nao_encontrados:
                resultados_finais.append({
                    'Momento_Consulta_Sinal': data_hora_atual,
                    'CTO': 'N/A',
                    'Circuito': circuito,
                    'Tecnologia': 'Não encontrado no DB',
                    'Sinal_Fibra': 'N/A',
                    'Parecer_Sinal_Fibra': 'NAO_APLICAVEL',
                    'Status_Modem': 'N/A',
                    'Momento_Conexao': 'N/A',
                    'Momento_Desconexao': 'N/A',
                    'Causa_Desconexao': 'N/A'
                })
            
            # 6. Converter para DataFrame e ordenar
            if not resultados_finais:
                return pd.DataFrame()
            
            df_resultados = pd.DataFrame(resultados_finais)
            
            # Manter ordem original dos circuitos de entrada
            df_resultados['Circuito'] = pd.Categorical(
                df_resultados['Circuito'], 
                categories=circuitos, 
                ordered=True
            )
            df_resultados = df_resultados.sort_values('Circuito').reset_index(drop=True)
            
            # Renomear coluna para padrão da aplicação
            df_resultados.rename(columns={'Circuito': 'CIRCUITO'}, inplace=True)
            
            logger.info(f"Batimento concluído: {len(resultados_finais)} resultados processados")
            return df_resultados
            
        except Exception as e:
            logger.error(f"Erro no batimento de fibra: {str(e)}")
            return self._criar_resultados_erro(circuitos, str(e))
    
    def _criar_resultados_vazios(self, circuitos: List[str]) -> pd.DataFrame:
        """Cria DataFrame com resultados vazios para circuitos não encontrados."""
        data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        resultados = []
        
        for circuito in circuitos:
            resultados.append({
                'Momento_Consulta_Sinal': data_hora_atual,
                'CTO': 'N/A',
                'CIRCUITO': circuito,
                'Tecnologia': 'Não encontrado no DB',
                'Sinal_Fibra': 'N/A',
                'Parecer_Sinal_Fibra': 'NAO_APLICAVEL',
                'Status_Modem': 'N/A',
                'Momento_Conexao': 'N/A',
                'Momento_Desconexao': 'N/A',
                'Causa_Desconexao': 'N/A'
            })
        
        return pd.DataFrame(resultados)
    
    def _criar_resultados_erro(self, circuitos: List[str], erro: str) -> pd.DataFrame:
        """Cria DataFrame com resultados de erro."""
        data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        resultados = []
        
        for circuito in circuitos:
            resultados.append({
                'Momento_Consulta_Sinal': data_hora_atual,
                'CTO': 'ERRO',
                'CIRCUITO': circuito,
                'Tecnologia': 'Erro no processamento',
                'Sinal_Fibra': f'Erro: {erro}',
                'Parecer_Sinal_Fibra': 'ERRO',
                'Status_Modem': 'ERRO',
                'Momento_Conexao': 'N/A',
                'Momento_Desconexao': 'N/A',
                'Causa_Desconexao': 'N/A'
            })
        
        return pd.DataFrame(resultados)
    
    def _processar_em_lote_thread(self, circuitos_info: List[Dict], max_threads: int = 15) -> List[Dict]:
        """
        Processa circuitos em paralelo usando ThreadPoolExecutor.
        
        Args:
            circuitos_info (List[Dict]): Lista de informações dos circuitos
            max_threads (int): Número máximo de threads
            
        Returns:
            List[Dict]: Resultados processados
        """
        resultados = []
        
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_circuito = {
                executor.submit(self._processar_circuito, info): info 
                for info in circuitos_info
            }
            
            for future in as_completed(future_to_circuito):
                try:
                    resultado = future.result()
                    if resultado:
                        resultados.append(resultado)
                except Exception as e:
                    circuito_info = future_to_circuito[future]
                    circuito = circuito_info.get('Circuito', 'N/A')
                    logger.error(f"Erro no processamento da thread para circuito {circuito}: {str(e)}")
        
        return resultados
    
    def _processar_circuito(self, circuito_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um único circuito com tentativas de retry.
        
        Args:
            circuito_info (Dict[str, Any]): Informações do circuito
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        circuito = circuito_info.get('Circuito', 'N/A')
        
        # Estrutura base do resultado
        resultado_final = {
            'Momento_Consulta_Sinal': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'CTO': circuito_info.get('CTO', 'N/A'),
            'Circuito': circuito,
            'Tecnologia': circuito_info.get('Tecnologia', 'Desconhecida'),
            'Sinal_Fibra': "Não consultado",
            'Parecer_Sinal_Fibra': 'N/A',
            'Status_Modem': "N/A",
            'Momento_Conexao': "N/A",
            'Momento_Desconexao': "N/A",
            'Causa_Desconexao': "N/A"
        }
        
        # Implementar retry logic
        max_tentativas = 4
        for tentativa in range(1, max_tentativas + 1):
            try:
                resultado_sinal = self._consultar_sinal(circuito_info)
                sinal_info, status_info = resultado_sinal[0], resultado_sinal[1]
                sinal_valor = sinal_info.get('sinal_fibra', 'Erro de parse')
                
                # Verificar se precisa retry
                if "leitura de sinal falhou" in str(sinal_valor).lower() and tentativa < max_tentativas:
                    logger.warning(f"Tentativa {tentativa}/{max_tentativas-1} falhou para {circuito}. Tentando novamente em 5s...")
                    sleep(5)
                    continue
                
                # Processar resultado
                resultado_final['Sinal_Fibra'] = sinal_valor
                
                # Determinar parecer do sinal
                try:
                    sinal_float = float(sinal_valor)
                    resultado_final['Parecer_Sinal_Fibra'] = (
                        'SINAL_ESTAVEL' if -27.99 <= sinal_float <= -8.01 
                        else 'SINAL_ATENUADO'
                    )
                except (ValueError, TypeError):
                    sinal_str = str(sinal_valor).lower()
                    if 'sem sinal' in sinal_str or 'los' in sinal_str:
                        resultado_final['Parecer_Sinal_Fibra'] = 'SEM_SINAL'
                    elif 'não encontrado' in sinal_str or 'no matching' in sinal_str:
                        resultado_final['Parecer_Sinal_Fibra'] = 'NAO_ENCONTRADO_OLT'
                    else:
                        resultado_final['Parecer_Sinal_Fibra'] = 'NAO_APLICAVEL'
                
                # Processar informações de status
                if status_info.get('retorno'):
                    resultado_final.update({
                        'Status_Modem': status_info.get('status_modem', 'N/A'),
                        'Momento_Conexao': status_info.get('momento_conexao', 'N/A'),
                        'Momento_Desconexao': status_info.get('momento_desconexao', 'N/A'),
                        'Causa_Desconexao': status_info.get('causa_desconexao', 'N/A')
                    })
                else:
                    if resultado_final['Parecer_Sinal_Fibra'] == 'SEM_SINAL':
                        resultado_final['Status_Modem'] = 'Sem Sinal (LOS)'
                    else:
                        resultado_final['Status_Modem'] = 'Consulta de status falhou'
                
                break  # Sucesso, sair do loop
                
            except Exception as e:
                logger.error(f"Erro crítico ao processar circuito {circuito}: {str(e)}")
                resultado_final['Sinal_Fibra'] = "Erro no processamento"
                resultado_final['Parecer_Sinal_Fibra'] = "NAO_APLICAVEL"
                break
        
        return resultado_final
    
    def _consultar_sinal(self, circuito_info: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Direciona consulta de sinal baseado na tecnologia.
        
        Args:
            circuito_info (Dict[str, Any]): Informações do circuito
            
        Returns:
            Tuple[Dict[str, str], Dict[str, Any]]: (info_sinal, info_status)
        """
        tecnologia = circuito_info.get('Tecnologia', '')
        default_fail_response = [
            {'sinal_fibra': 'Não foi possível consultar'}, 
            {'retorno': False}
        ]
        
        try:
            if "HUAWEI" in tecnologia:
                return self._consultar_sinal_huawei(circuito_info['Circuito'])
            elif "FIBERHOME" in tecnologia:
                return self._consultar_sinal_fiberhome(circuito_info)
            elif "NOKIA" in tecnologia:
                return self._consultar_sinal_nokia(circuito_info['ip_olt'], circuito_info['Circuito'])
            elif "ZTE" in tecnologia:
                return self._consultar_sinal_zte(circuito_info)
            elif "ZHONE" in tecnologia:
                return self._consultar_sinal_zhone(circuito_info)
            else:
                msg = f"Tecnologia '{tecnologia}' não implementada"
                logger.warning(f"{msg} para circuito {circuito_info['Circuito']}")
                default_fail_response[0]['sinal_fibra'] = msg
                return default_fail_response
                
        except Exception as e:
            logger.error(f"Erro na consulta de sinal para {circuito_info.get('Circuito', 'N/A')}: {str(e)}")
            default_fail_response[0]['sinal_fibra'] = f"Erro: {str(e)}"
            return default_fail_response
    
    # PLACEHOLDER: Métodos de consulta por tecnologia serão implementados
    def _consultar_sinal_huawei(self, circuito: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Placeholder para consulta Huawei."""
        return [
            {'sinal_fibra': 'Tecnologia Huawei - implementação pendente'}, 
            {'retorno': False, 'status_modem': 'Pendente'}
        ]
    
    def _consultar_sinal_fiberhome(self, circuito_info: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Placeholder para consulta FiberHome."""
        return [
            {'sinal_fibra': 'Tecnologia FiberHome - implementação pendente'}, 
            {'retorno': False, 'status_modem': 'Pendente'}
        ]
    
    def _consultar_sinal_nokia(self, ip_olt: str, circuito: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Placeholder para consulta Nokia."""
        return [
            {'sinal_fibra': 'Tecnologia Nokia - implementação pendente'}, 
            {'retorno': False, 'status_modem': 'Pendente'}
        ]
    
    def _consultar_sinal_zte(self, circuito_info: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Placeholder para consulta ZTE."""
        return [
            {'sinal_fibra': 'Tecnologia ZTE - implementação pendente'}, 
            {'retorno': False, 'status_modem': 'Pendente'}
        ]
    
    def _consultar_sinal_zhone(self, circuito_info: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Placeholder para consulta Zhone."""
        return [
            {'sinal_fibra': 'Tecnologia Zhone - implementação pendente'}, 
            {'retorno': False, 'status_modem': 'Pendente'}
        ]

# Instância global do módulo de batimento
batimento_fibra = BatimentoFibra()
