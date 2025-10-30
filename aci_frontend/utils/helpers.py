# -*- coding: utf-8 -*-
"""
ACI Frontend - Funções Auxiliares
Funções utilitárias para a aplicação
"""

import re
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtCore import QStandardPaths

def validar_protocolo(protocolo: str) -> bool:
    """
    Valida se um protocolo está no formato correto.
    
    Args:
        protocolo: String do protocolo a ser validado
        
    Returns:
        True se o protocolo é válido
    """
    # Exemplo: 1-123456 ou similar
    pattern = r'^\d+-\d+$'
    return bool(re.match(pattern, protocolo.strip()))

def validar_circuito(circuito: str) -> bool:
    """
    Valida se um circuito está no formato correto.
    
    Args:
        circuito: String do circuito a ser validado
        
    Returns:
        True se o circuito é válido
    """
    # Exemplo: CIR123456 ou similar
    pattern = r'^CIR\d+$'
    return bool(re.match(pattern, circuito.strip().upper()))

def validar_cto(cto: str) -> bool:
    """
    Valida se uma CTO está no formato correto.
    
    Args:
        cto: String da CTO a ser validada
        
    Returns:
        True se a CTO é válida
    """
    # Exemplo: CTO-01-A01 ou similar
    pattern = r'^CTO-\d+-[A-Z]\d+$'
    return bool(re.match(pattern, cto.strip().upper()))

def processar_valores_entrada(texto: str) -> List[str]:
    """
    Processa o texto de entrada e retorna uma lista de valores limpos.
    
    Args:
        texto: Texto com valores separados por linha
        
    Returns:
        Lista de valores limpos e únicos
    """
    if not texto:
        return []
    
    # Dividir por linhas e limpar espaços
    valores = [linha.strip() for linha in texto.split('\n') if linha.strip()]
    
    # Remover duplicatas mantendo ordem
    valores_unicos = []
    for valor in valores:
        if valor not in valores_unicos:
            valores_unicos.append(valor)
    
    return valores_unicos

def formatar_data_hora(timestamp: Optional[datetime] = None) -> str:
    """
    Formata uma data/hora para exibição.
    
    Args:
        timestamp: Objeto datetime (usa atual se None)
        
    Returns:
        String formatada da data/hora
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime("%d/%m/%Y %H:%M:%S")

def exportar_para_csv(dados: List[Dict[str, Any]], arquivo: str) -> bool:
    """
    Exporta dados para arquivo CSV.
    
    Args:
        dados: Lista de dicionários com os dados
        arquivo: Caminho do arquivo de destino
        
    Returns:
        True se a exportação foi bem-sucedida
    """
    try:
        if not dados:
            return False
        
        with open(arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            if isinstance(dados[0], dict):
                fieldnames = dados[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dados)
            else:
                writer = csv.writer(csvfile)
                writer.writerows(dados)
        
        return True
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")
        return False

def exportar_para_json(dados: Any, arquivo: str) -> bool:
    """
    Exporta dados para arquivo JSON.
    
    Args:
        dados: Dados a serem exportados
        arquivo: Caminho do arquivo de destino
        
    Returns:
        True se a exportação foi bem-sucedida
    """
    try:
        with open(arquivo, 'w', encoding='utf-8') as jsonfile:
            json.dump(dados, jsonfile, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao exportar JSON: {e}")
        return False

def mostrar_mensagem(titulo: str, mensagem: str, tipo: str = "info") -> None:
    """
    Exibe uma caixa de mensagem para o usuário.
    
    Args:
        titulo: Título da caixa de diálogo
        mensagem: Mensagem a ser exibida
        tipo: Tipo da mensagem ('info', 'warning', 'error', 'question')
    """
    msg_box = QMessageBox()
    msg_box.setWindowTitle(titulo)
    msg_box.setText(mensagem)
    
    if tipo == "info":
        msg_box.setIcon(QMessageBox.Icon.Information)
    elif tipo == "warning":
        msg_box.setIcon(QMessageBox.Icon.Warning)
    elif tipo == "error":
        msg_box.setIcon(QMessageBox.Icon.Critical)
    elif tipo == "question":
        msg_box.setIcon(QMessageBox.Icon.Question)
    
    msg_box.exec()

def selecionar_arquivo_salvar(filtro: str = "Todos os arquivos (*.*)") -> Optional[str]:
    """
    Abre diálogo para o usuário selecionar onde salvar um arquivo.
    
    Args:
        filtro: Filtro de tipos de arquivo
        
    Returns:
        Caminho do arquivo selecionado ou None se cancelado
    """
    try:
        arquivo, _ = QFileDialog.getSaveFileName(
            None, 
            "Salvar arquivo", 
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            filtro
        )
        return arquivo if arquivo else None
    except Exception as e:
        print(f"Erro ao selecionar arquivo: {e}")
        return None

def sanitizar_nome_arquivo(nome: str) -> str:
    """
    Sanitiza um nome de arquivo removendo caracteres inválidos.
    
    Args:
        nome: Nome do arquivo original
        
    Returns:
        Nome sanitizado
    """
    # Remover caracteres inválidos para nomes de arquivo
    caracteres_invalidos = r'[<>:"/\\|?*]'
    nome_limpo = re.sub(caracteres_invalidos, '_', nome)
    
    # Limitar tamanho do nome
    if len(nome_limpo) > 200:
        nome_limpo = nome_limpo[:200]
    
    return nome_limpo.strip()

def gerar_nome_arquivo_exportacao(prefixo: str, extensao: str) -> str:
    """
    Gera um nome de arquivo único para exportação.
    
    Args:
        prefixo: Prefixo do nome do arquivo
        extensao: Extensão do arquivo (sem ponto)
        
    Returns:
        Nome do arquivo gerado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome = f"{prefixo}_{timestamp}.{extensao}"
    return sanitizar_nome_arquivo(nome)

def calcular_estatisticas_basicas(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula estatísticas básicas dos dados.
    
    Args:
        dados: Lista de dicionários com dados
        
    Returns:
        Dicionário com estatísticas
    """
    if not dados:
        return {"total": 0}
    
    stats = {
        "total": len(dados),
        "campos": list(dados[0].keys()) if dados else [],
        "primeira_entrada": dados[0] if dados else None,
        "ultima_entrada": dados[-1] if dados else None
    }
    
    return stats
