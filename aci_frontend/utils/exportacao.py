# -*- coding: utf-8 -*-
"""
ACI Frontend - Módulo de Exportação
Funções para converter dados para diferentes formatos de arquivo
"""

import csv
import json
import io
from typing import List, Dict, Any, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataExporter:
    """
    Classe responsável pela conversão e exportação de dados em diferentes formatos.
    """
    
    @staticmethod
    def converter_dados_para_formato(dados: List[Dict[str, Any]], formato: str) -> Union[str, bytes]:
        """
        NOVA FUNÇÃO: Converte dados para o formato especificado.
        
        Args:
            dados (List[Dict[str, Any]]): Lista de registros para exportar
            formato (str): Formato de exportação ('CSV', 'Excel', 'JSON', 'TXT', etc.)
            
        Returns:
            Union[str, bytes]: Conteúdo do arquivo pronto para salvar
            
        Raises:
            ValueError: Se o formato não for suportado
            Exception: Se houver erro na conversão
        """
        if not dados:
            logger.warning("Lista de dados vazia para exportação")
            return DataExporter._get_empty_content_for_format(formato)
        
        formato_lower = formato.lower()
        
        try:
            if formato_lower in ['csv', '.csv']:
                return DataExporter._convert_to_csv(dados)
            elif formato_lower in ['json', '.json']:
                return DataExporter._convert_to_json(dados)
            elif formato_lower in ['txt', '.txt', 'texto']:
                return DataExporter._convert_to_txt(dados)
            elif formato_lower in ['excel', 'xls', '.xls', 'xlsx', '.xlsx']:
                return DataExporter._convert_to_excel(dados, formato_lower)
            elif formato_lower in ['pdf', '.pdf']:
                return DataExporter._convert_to_pdf(dados)
            else:
                raise ValueError(f"Formato '{formato}' não suportado")
                
        except Exception as e:
            logger.error(f"Erro na conversão para {formato}: {str(e)}")
            raise Exception(f"Falha na conversão para {formato}: {str(e)}")
    
    @staticmethod
    def _convert_to_csv(dados: List[Dict[str, Any]]) -> str:
        """Converte dados para formato CSV."""
        if not dados:
            return ""
        
        output = io.StringIO()
        
        # Obter cabeçalhos (remover campos internos)
        headers = [key for key in dados[0].keys() if not key.startswith('_')]
        
        writer = csv.DictWriter(output, fieldnames=headers, lineterminator='\n', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for row in dados:
            # Filtrar campos internos e converter valores None para string vazia
            filtered_row = {
                key: str(value) if value is not None else "" 
                for key, value in row.items() 
                if not key.startswith('_')
            }
            writer.writerow(filtered_row)
        
        content = output.getvalue()
        output.close()
        
        logger.info(f"CSV gerado: {len(dados)} linhas, {len(headers)} colunas")
        return content
    
    @staticmethod
    def _convert_to_json(dados: List[Dict[str, Any]]) -> str:
        """Converte dados para formato JSON."""
        # Filtrar campos internos
        filtered_data = []
        for row in dados:
            filtered_row = {
                key: value for key, value in row.items() 
                if not key.startswith('_')
            }
            filtered_data.append(filtered_row)
        
        # Configurar exportação JSON
        export_data = {
            "exportado_em": datetime.now().isoformat(),
            "total_registros": len(filtered_data),
            "dados": filtered_data
        }
        
        content = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
        logger.info(f"JSON gerado: {len(dados)} registros")
        return content
    
    @staticmethod
    def _convert_to_txt(dados: List[Dict[str, Any]]) -> str:
        """Converte dados para formato TXT (texto delimitado por tabulação)."""
        if not dados:
            return "Nenhum dado para exportar\n"
        
        # Obter cabeçalhos (remover campos internos)
        headers = [key for key in dados[0].keys() if not key.startswith('_')]
        
        lines = []
        
        # Cabeçalho
        lines.append("\t".join(headers))
        
        # Dados
        for row in dados:
            values = []
            for header in headers:
                value = row.get(header, "")
                # Converter None e tratar quebras de linha
                if value is None:
                    value = ""
                else:
                    value = str(value).replace('\n', ' ').replace('\r', ' ')
                values.append(value)
            lines.append("\t".join(values))
        
        content = "\n".join(lines)
        logger.info(f"TXT gerado: {len(dados)} linhas")
        return content
    
    @staticmethod
    def _convert_to_excel(dados: List[Dict[str, Any]], formato: str) -> bytes:
        """Converte dados para formato Excel (.xls ou .xlsx)."""
        try:
            import pandas as pd
            
            # Filtrar campos internos
            filtered_data = []
            for row in dados:
                filtered_row = {
                    key: value for key, value in row.items() 
                    if not key.startswith('_')
                }
                filtered_data.append(filtered_row)
            
            # Criar DataFrame
            df = pd.DataFrame(filtered_data)
            
            # Converter para Excel em memória
            output = io.BytesIO()
            
            # CORREÇÃO: Tratamento específico para cada formato
            if 'xlsx' in formato.lower() or 'excel' in formato.lower():
                try:
                    # Tentar usar openpyxl para .xlsx
                    df.to_excel(output, index=False, engine='openpyxl')
                except ImportError:
                    raise Exception("Exportação para XLSX requer openpyxl. Execute: pip install openpyxl")
            else:
                try:
                    # Tentar usar xlwt para .xls
                    df.to_excel(output, index=False, engine='xlwt')
                except ImportError:
                    raise Exception("Exportação para XLS requer xlwt. Execute: pip install xlwt")
            
            content = output.getvalue()
            output.close()
            
            logger.info(f"Excel gerado: {len(dados)} linhas, formato {formato}")
            return content
            
        except ImportError as ie:
            error_msg = str(ie)
            if "pandas" in error_msg:
                raise Exception("Exportação para Excel requer pandas. Execute: pip install pandas")
            else:
                raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Erro na geração do Excel: {str(e)}")
            raise Exception(f"Erro na exportação para Excel: {str(e)}")
    
    @staticmethod
    def _convert_to_pdf(dados: List[Dict[str, Any]]) -> bytes:
        """Converte dados para formato PDF com layout otimizado."""
        try:
            from reportlab.lib.pagesizes import letter, A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            output = io.BytesIO()
            
            # CORREÇÃO: Usar orientação paisagem para melhor aproveitamento
            page_size = landscape(A4)
            doc = SimpleDocTemplate(output, pagesize=page_size, 
                                  leftMargin=0.5*inch, rightMargin=0.5*inch,
                                  topMargin=0.5*inch, bottomMargin=0.5*inch)
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            normal_style = styles['Normal']
            
            # Elementos do documento
            elements = []
            
            # Título
            title = Paragraph("Relatório de Dados ACI", title_style)
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Informações do relatório
            info_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>Total de registros: {len(dados)}"
            info = Paragraph(info_text, normal_style)
            elements.append(info)
            elements.append(Spacer(1, 12))
            
            if dados:
                # Preparar dados da tabela
                headers = [key for key in dados[0].keys() if not key.startswith('_')]
                
                # CORREÇÃO: Calcular largura disponível e ajustar colunas
                available_width = page_size[0] - 1*inch  # Descontando margens
                num_columns = len(headers)
                max_col_width = available_width / num_columns if num_columns > 0 else 1*inch
                
                # Dados da tabela com truncamento inteligente
                table_data = [headers]  # Primeira linha são os cabeçalhos
                
                for row in dados:
                    row_data = []
                    for header in headers:
                        value = row.get(header, "")
                        if value is None:
                            value = ""
                        
                        # CORREÇÃO: Truncamento baseado no número de colunas
                        value_str = str(value)
                        max_chars = max(15, int(80 / num_columns))  # Mínimo 15 chars
                        if len(value_str) > max_chars:
                            value_str = value_str[:max_chars-3] + "..."
                        row_data.append(value_str)
                    table_data.append(row_data)
                
                # CORREÇÃO: Criar tabela com larguras específicas
                col_widths = [max_col_width] * num_columns
                table = Table(table_data, colWidths=col_widths)
                
                # CORREÇÃO: Estilo da tabela otimizado
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinhamento à esquerda
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),  # Fonte menor no cabeçalho
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),  # Fonte ainda menor nos dados
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinhamento vertical no topo
                    ('WORDWRAP', (0, 0), (-1, -1), True)  # Quebra de linha automática
                ]))
                
                elements.append(table)
            else:
                no_data = Paragraph("Nenhum dado encontrado para exibir.", normal_style)
                elements.append(no_data)
            
            # Gerar PDF
            doc.build(elements)
            content = output.getvalue()
            output.close()
            
            logger.info(f"PDF gerado: {len(dados)} registros em orientação paisagem")
            return content
            
        except ImportError:
            logger.error("ReportLab não instalado - não é possível exportar para PDF")
            raise Exception("Exportação para PDF requer a biblioteca reportlab. Execute: pip install reportlab")
        except Exception as e:
            logger.error(f"Erro na geração do PDF: {str(e)}")
            raise Exception(f"Erro na exportação para PDF: {str(e)}")
    
    @staticmethod
    def _get_empty_content_for_format(formato: str) -> Union[str, bytes]:
        """Retorna conteúdo vazio apropriado para o formato."""
        formato_lower = formato.lower()
        
        if formato_lower in ['csv', '.csv']:
            return "Nenhum dado para exportar\n"
        elif formato_lower in ['json', '.json']:
            return json.dumps({
                "exportado_em": datetime.now().isoformat(),
                "total_registros": 0,
                "dados": [],
                "mensagem": "Nenhum dado encontrado"
            }, ensure_ascii=False, indent=2)
        elif formato_lower in ['txt', '.txt']:
            return "Nenhum dado para exportar\n"
        else:
            return "Nenhum dado para exportar\n"
    
    @staticmethod
    def get_supported_formats() -> List[Dict[str, str]]:
        """
        Retorna lista de formatos suportados para exportação.
        
        Returns:
            List[Dict[str, str]]: Lista com informações dos formatos suportados
        """
        return [
            {"formato": "CSV", "extensao": ".csv", "descricao": "Valores Separados por Vírgula"},
            {"formato": "JSON", "extensao": ".json", "descricao": "JavaScript Object Notation"},
            {"formato": "TXT", "extensao": ".txt", "descricao": "Texto Delimitado por Tabulação"},
            {"formato": "Excel", "extensao": ".xlsx", "descricao": "Planilha Microsoft Excel"},
            {"formato": "PDF", "extensao": ".pdf", "descricao": "Portable Document Format"}
        ]
    
    @staticmethod
    def get_file_extension(formato: str) -> str:
        """
        Retorna a extensão apropriada para o formato.
        
        Args:
            formato (str): Nome do formato
            
        Returns:
            str: Extensão do arquivo (com ponto)
        """
        format_extensions = {
            'csv': '.csv',
            'json': '.json', 
            'txt': '.txt',
            'texto': '.txt',
            'excel': '.xlsx',
            'xlsx': '.xlsx',
            'xls': '.xls',
            'pdf': '.pdf'
        }
        
        return format_extensions.get(formato.lower(), '.txt')

# Instância global do exportador
data_exporter = DataExporter()
