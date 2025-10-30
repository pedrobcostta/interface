# -*- coding: utf-8 -*-
"""
ACI Frontend - Widget de Resultados
Widget reutilizável que encapsula a tabela de resultados e sua toolbar
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTableView, QHeaderView, QAbstractItemView, QMenu,
    QInputDialog, QMessageBox, QApplication, QDialog, QFileDialog
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QCursor
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal

from typing import List, Dict, Any, Union
from datetime import datetime


class ResultadosWindow(QDialog):
    """Uma nova janela para exibir os resultados da tabela de forma expandida."""

    def __init__(self, source_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualização Expandida de Resultados")
        self.setGeometry(150, 150, 1024, 600)
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        layout = QVBoxLayout(self)

        self.toolbar = self._criar_toolbar()
        layout.addLayout(self.toolbar)

        self.tabela_resultados = QTableView()
        layout.addWidget(self.tabela_resultados)

        self.proxy_model = QSortFilterProxyModel()
        self._copiar_modelo(source_model)
        self._configurar_tabela()

        # Aplicar estilos (será feito pela janela principal)
        self.filtro_tabela.textChanged.connect(self.proxy_model.setFilterFixedString)

    def _criar_toolbar(self):
        """Cria a barra de ferramentas para a janela de resultados."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 10)  # Espaçamento inferior

        label_busca = QLabel("Pesquisar:")
        self.filtro_tabela = QLineEdit()
        self.filtro_tabela.setPlaceholderText("Pesquisar nos resultados...")

        self.btn_exportar = QPushButton("Exportar")
        self.btn_exportar.setObjectName("ExportButton")
        menu_exportar = self._criar_menu_exportacao()
        self.btn_exportar.setMenu(menu_exportar)

        toolbar_layout.addWidget(label_busca)
        toolbar_layout.addWidget(self.filtro_tabela, 1)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.btn_exportar)
        return toolbar_layout

    def _criar_menu_exportacao(self):
        """Cria e retorna o menu de exportação."""
        menu_exportar = QMenu(self)
        menu_exportar.addAction("PDF (.pdf)", self._exportar_para_pdf)
        menu_exportar.addAction("JSON (.json)", self._exportar_para_json)
        menu_exportar.addSeparator()
        grupo_excel = menu_exportar.addMenu("Excel")
        grupo_excel.addAction("CSV (.csv)", self._exportar_para_csv)
        grupo_excel.addAction("XLS (.xls)", self._exportar_para_xls)
        grupo_excel.addAction("XLSX (.xlsx", self._exportar_para_xlsx)
        menu_exportar.addSeparator()
        menu_exportar.addAction("Texto (.txt)", self._exportar_para_txt)
        return menu_exportar

    def _configurar_tabela(self):
        """Aplica as configurações visuais e de comportamento da tabela."""
        self.tabela_resultados.setModel(self.proxy_model)
        self.tabela_resultados.setSortingEnabled(False)  # A ordenação será via menu
        self.tabela_resultados.setAlternatingRowColors(True)
        self.tabela_resultados.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_resultados.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.tabela_resultados.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.sectionClicked.connect(self._show_header_left_click_menu)

    def _copiar_modelo(self, source_model):
        """Cria uma cópia do modelo de dados."""
        if source_model.rowCount() == 0: 
            return

        # CORREÇÃO CRÍTICA: Criar atributo modelo_original que estava faltando
        self.modelo_original = QStandardItemModel()
        headers = [source_model.horizontalHeaderItem(i).text() for i in range(source_model.columnCount())]
        self.modelo_original.setHorizontalHeaderLabels(headers)

        for row in range(source_model.rowCount()):
            row_items = [QStandardItem(source_model.item(row, col).text() if source_model.item(row, col) else "") for
                         col in range(source_model.columnCount())]
            self.modelo_original.appendRow(row_items)

        self.proxy_model.setSourceModel(self.modelo_original)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

    def _show_header_left_click_menu(self, column_index):
        """Exibe o menu de ações ao clicar com o botão esquerdo no cabeçalho."""
        menu = QMenu(self)
        menu.addAction("Ordenar Crescente", lambda: self.proxy_model.sort(column_index, Qt.SortOrder.AscendingOrder))
        menu.addAction("Ordenar Decrescente", lambda: self.proxy_model.sort(column_index, Qt.SortOrder.DescendingOrder))
        menu.addSeparator()
        menu.addAction("Filtrar nesta Coluna...", lambda: self._filter_by_column(column_index))
        menu.exec(QCursor.pos())

    def _filter_by_column(self, column):
        """Abre um diálogo para filtrar por uma coluna específica."""
        header_text = self.proxy_model.headerData(column, Qt.Orientation.Horizontal)
        text, ok = QInputDialog.getText(self, "Filtrar Coluna", f"Mostrar apenas linhas onde '{header_text}' contém:")
        if ok:
            self.proxy_model.setFilterKeyColumn(column)
            self.filtro_tabela.clear()
            self.proxy_model.setFilterFixedString(text)

    # NOVA IMPLEMENTAÇÃO: Funções de exportação funcional
    def _exportar_para_pdf(self):
        """Implementa exportação para PDF."""
        self._executar_exportacao("PDF")

    def _exportar_para_json(self):
        """Implementa exportação para JSON."""
        self._executar_exportacao("JSON")

    def _exportar_para_csv(self):
        """Implementa exportação para CSV."""
        self._executar_exportacao("CSV")

    def _exportar_para_xls(self):
        """Implementa exportação para XLS."""
        self._executar_exportacao("XLS")

    def _exportar_para_xlsx(self):
        """Implementa exportação para XLSX."""
        self._executar_exportacao("Excel")

    def _exportar_para_txt(self):
        """Implementa exportação para TXT."""
        self._executar_exportacao("TXT")
    
    def _executar_exportacao(self, formato: str):
        """
        NOVA FUNÇÃO: Executa o processo completo de exportação.
        
        Args:
            formato (str): Formato de exportação escolhido
        """
        try:
            # 1. Verificar se há dados na tabela
            if self.modelo_original.rowCount() == 0:
                QMessageBox.warning(
                    self,
                    "Exportação",
                    "Não há dados na tabela para exportar.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # 2. Coletar dados da tabela
            dados_tabela = self._coletar_dados_da_tabela()
            
            if not dados_tabela:
                QMessageBox.warning(
                    self,
                    "Exportação", 
                    "Erro ao coletar dados da tabela.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # 3. Importar módulo de exportação
            from ...utils.exportacao import data_exporter
            
            # 4. Converter dados para o formato
            self.status_message_requested.emit(f"Convertendo dados para {formato}...")
            conteudo_arquivo = data_exporter.converter_dados_para_formato(dados_tabela, formato)
            
            # 5. Solicitar local de salvamento
            extensao = data_exporter.get_file_extension(formato)
            nome_sugerido = f"exportacao_aci_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extensao}"
            
            from PySide6.QtWidgets import QFileDialog
            arquivo_destino, _ = QFileDialog.getSaveFileName(
                self,
                f"Salvar como {formato}",
                nome_sugerido,
                f"Arquivos {formato} (*{extensao});;Todos os arquivos (*.*)"
            )
            
            if not arquivo_destino:
                self.status_message_requested.emit("Exportação cancelada pelo usuário.")
                return
            
            # 6. Salvar arquivo
            self._salvar_arquivo_exportacao(arquivo_destino, conteudo_arquivo, formato)
            
            # 7. Confirmar sucesso
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Dados exportados com sucesso para:\n{arquivo_destino}",
                QMessageBox.StandardButton.Ok
            )
            
            self.status_message_requested.emit(f"Exportação para {formato} concluída com sucesso.")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Exportação",
                f"Erro ao exportar para {formato}:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            self.status_message_requested.emit(f"Erro na exportação: {str(e)}")
    
    def _coletar_dados_da_tabela(self) -> List[Dict[str, Any]]:
        """
        Coleta todos os dados da tabela e converte para lista de dicionários.
        
        Returns:
            List[Dict[str, Any]]: Dados da tabela
        """
        dados = []
        
        try:
            # Obter headers
            headers = []
            for col in range(self.modelo_original.columnCount()):
                header_item = self.modelo_original.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Coluna_{col}")
            
            # Obter dados das linhas
            for row in range(self.modelo_original.rowCount()):
                linha_dict = {}
                for col in range(self.modelo_original.columnCount()):
                    item = self.modelo_original.item(row, col)
                    valor = item.text() if item else ""
                    linha_dict[headers[col]] = valor
                dados.append(linha_dict)
            
            return dados
            
        except Exception as e:
            print(f"Erro ao coletar dados da tabela: {str(e)}")
            return []
    
    def _salvar_arquivo_exportacao(self, caminho_arquivo: str, conteudo: Union[str, bytes], formato: str):
        """
        Salva o conteúdo no arquivo especificado.
        
        Args:
            caminho_arquivo (str): Caminho completo do arquivo
            conteudo (Union[str, bytes]): Conteúdo a ser salvo
            formato (str): Formato do arquivo para determinar modo de escrita
        """
        try:
            # Determinar modo de escrita baseado no formato
            if formato.lower() in ['excel', 'pdf', 'xls', 'xlsx']:
                # Formatos binários
                with open(caminho_arquivo, 'wb') as arquivo:
                    arquivo.write(conteudo)
            else:
                # Formatos de texto
                with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                    arquivo.write(conteudo)
                    
        except Exception as e:
            raise Exception(f"Erro ao salvar arquivo: {str(e)}")


class ResultadosWidget(QWidget):
    """Um widget reutilizável que encapsula a tabela de resultados e sua toolbar."""
    status_message_requested = Signal(str)

    def __init__(self, title="Resultados da Consulta", parent=None):
        super().__init__(parent)
        self.original_headers = []
        self.expanded_view_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        resultados_group = QGroupBox(title)
        resultados_layout = QVBoxLayout(resultados_group)

        toolbar_tabela_layout = self._criar_toolbar_tabela()
        self.tabela_resultados = self._criar_tabela_resultados()

        resultados_layout.addLayout(toolbar_tabela_layout)
        resultados_layout.addWidget(self.tabela_resultados)
        layout.addWidget(resultados_group)

        self._conectar_sinais()

    def get_model(self):
        return self.modelo_original

    def clear_results(self):
        """Limpa o modelo da tabela, mantendo os cabeçalhos."""
        self.modelo_original.clear()
        if self.original_headers:
            self.modelo_original.setHorizontalHeaderLabels(self.original_headers)
        self.status_message_requested.emit("Resultados limpos.")

    def _criar_toolbar_tabela(self):
        """Cria o layout da barra de ferramentas com busca e botões de ação."""
        toolbar_layout = QHBoxLayout()

        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        label_busca = QLabel("Pesquisar na tabela:")
        self.filtro_tabela = QLineEdit()
        self.filtro_tabela.setPlaceholderText("Digite para pesquisar...")
        search_layout.addWidget(label_busca)
        search_layout.addWidget(self.filtro_tabela)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.setObjectName("ToolbarButton")
        self.btn_copiar = QPushButton("Copiar Seleção")
        self.btn_copiar.setObjectName("ToolbarButton")
        self.btn_expandir = QPushButton("Expandir Visão")
        self.btn_expandir.setObjectName("ToolbarButton")

        self.btn_exportar = QPushButton("Exportar")
        self.btn_exportar.setObjectName("ExportButton")
        menu_exportar = self._criar_menu_exportacao()
        self.btn_exportar.setMenu(menu_exportar)

        toolbar_layout.addWidget(search_container, 1)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.btn_limpar)
        toolbar_layout.addWidget(self.btn_copiar)
        toolbar_layout.addWidget(self.btn_expandir)
        toolbar_layout.addWidget(self.btn_exportar)

        return toolbar_layout

    def _criar_menu_exportacao(self):
        """Cria e retorna o menu de exportação para a toolbar."""
        menu_exportar = QMenu(self)
        menu_exportar.addAction("PDF (.pdf)...", self._exportar_para_pdf)
        menu_exportar.addAction("JSON (.json)...", self._exportar_para_json)
        menu_exportar.addSeparator()
        grupo_excel = menu_exportar.addMenu("Excel")
        grupo_excel.addAction("CSV (.csv)...", self._exportar_para_csv)
        grupo_excel.addAction("XLS (.xls)...", self._exportar_para_xls)
        grupo_excel.addAction("XLSX (.xlsx)...", self._exportar_para_xlsx)
        menu_exportar.addSeparator()
        menu_exportar.addAction("Texto (.txt)...", self._exportar_para_txt)
        return menu_exportar

    def _criar_tabela_resultados(self):
        """Cria, configura e retorna a QTableView para os resultados."""
        tabela = QTableView()
        tabela.setSortingEnabled(False)
        tabela.setAlternatingRowColors(True)
        tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        tabela.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        v_header = tabela.verticalHeader()
        v_header.setVisible(True)
        v_header.setFixedWidth(40)

        header = tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.modelo_original = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.modelo_original)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

        tabela.setModel(self.proxy_model)
        return tabela

    def _conectar_sinais(self):
        """Conecta os sinais dos widgets internos."""
        self.filtro_tabela.textChanged.connect(self.proxy_model.setFilterFixedString)
        self.btn_copiar.clicked.connect(self._copiar_dados_selecionados)
        self.btn_limpar.clicked.connect(self.clear_results)
        self.btn_expandir.clicked.connect(self._abrir_visualizacao_expandida)

        self.tabela_resultados.customContextMenuRequested.connect(self._show_table_context_menu)
        self.tabela_resultados.verticalHeader().sectionClicked.connect(self._selecionar_linha_pelo_header)
        self.tabela_resultados.horizontalHeader().sectionClicked.connect(self._show_header_left_click_menu)

    def _abrir_visualizacao_expandida(self):
        """Abre uma nova janela com os dados da tabela atual."""
        if self.modelo_original.rowCount() == 0:
            self.status_message_requested.emit("Não há dados para exibir em uma nova janela.")
            return
        self.expanded_view_window = ResultadosWindow(self.modelo_original, self)
        self.expanded_view_window.show()

    def _copiar_dados_selecionados(self):
        """Copia as células selecionadas na tabela para a área de transferência."""
        selection_model = self.tabela_resultados.selectionModel()
        if not selection_model.hasSelection():
            self.status_message_requested.emit("Nenhuma célula selecionada para copiar.")
            return

        indexes = selection_model.selectedIndexes()
        if not indexes: 
            return

        rows_data = {}
        for index in indexes:
            row, col = index.row(), index.column()
            if row not in rows_data: 
                rows_data[row] = {}
            rows_data[row][col] = index.data(Qt.ItemDataRole.DisplayRole)

        clipboard_text = ["\t".join(map(str, (rows_data[row][col] for col in sorted(rows_data[row].keys())))) for row in
                          sorted(rows_data.keys())]
        QApplication.clipboard().setText("\n".join(clipboard_text))
        self.status_message_requested.emit("Seleção copiada para a área de transferência.")

    def _show_table_context_menu(self, pos):
        """Exibe o menu de contexto para o corpo da tabela."""
        menu = QMenu(self)
        copy_action = menu.addAction("Copiar Seleção")
        action = menu.exec(self.tabela_resultados.viewport().mapToGlobal(pos))
        if action == copy_action:
            self._copiar_dados_selecionados()

    def _show_header_left_click_menu(self, column_index):
        """Exibe o menu de ações ao clicar com o botão esquerdo no cabeçalho."""
        menu = QMenu(self)
        menu.addAction("Ordenar Crescente", lambda: self.proxy_model.sort(column_index, Qt.SortOrder.AscendingOrder))
        menu.addAction("Ordenar Decrescente", lambda: self.proxy_model.sort(column_index, Qt.SortOrder.DescendingOrder))
        menu.addSeparator()
        menu.addAction("Filtrar nesta Coluna...", lambda: self._filter_by_column(column_index))
        menu.exec(QCursor.pos())

    def _selecionar_linha_pelo_header(self, logicalIndex):
        """Seleciona a linha inteira quando o cabeçalho vertical é clicado."""
        self.tabela_resultados.clearSelection()
        self.tabela_resultados.selectRow(logicalIndex)

    def _filter_by_column(self, column):
        """Abre um diálogo para filtrar por uma coluna específica."""
        header_text = self.proxy_model.headerData(column, Qt.Orientation.Horizontal)
        text, ok = QInputDialog.getText(self, f"Filtrar Coluna", f"Mostrar apenas linhas onde '{header_text}' contém:")
        if ok:
            self.proxy_model.setFilterKeyColumn(column)
            self.filtro_tabela.clear()
            self.proxy_model.setFilterFixedString(text)

    # NOVA IMPLEMENTAÇÃO: Funções de exportação funcional
    def _exportar_para_pdf(self):
        """Implementa exportação para PDF."""
        self._executar_exportacao("PDF")

    def _exportar_para_json(self):
        """Implementa exportação para JSON."""
        self._executar_exportacao("JSON")

    def _exportar_para_csv(self):
        """Implementa exportação para CSV."""
        self._executar_exportacao("CSV")

    def _exportar_para_xls(self):
        """Implementa exportação para XLS."""
        self._executar_exportacao("XLS")

    def _exportar_para_xlsx(self):
        """Implementa exportação para XLSX."""
        self._executar_exportacao("Excel")

    def _exportar_para_txt(self):
        """Implementa exportação para TXT."""
        self._executar_exportacao("TXT")
    
    def _executar_exportacao(self, formato: str):
        """
        NOVA FUNÇÃO: Executa o processo completo de exportação.
        
        Args:
            formato (str): Formato de exportação escolhido
        """
        try:
            # 1. Verificar se há dados na tabela
            if self.modelo_original.rowCount() == 0:
                QMessageBox.warning(
                    self,
                    "Exportação",
                    "Não há dados na tabela para exportar.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # 2. Coletar dados da tabela
            dados_tabela = self._coletar_dados_da_tabela()
            
            if not dados_tabela:
                QMessageBox.warning(
                    self,
                    "Exportação", 
                    "Erro ao coletar dados da tabela.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # 3. Importar módulo de exportação
            from ...utils.exportacao import data_exporter
            
            # 4. Converter dados para o formato
            self.status_message_requested.emit(f"Convertendo dados para {formato}...")
            conteudo_arquivo = data_exporter.converter_dados_para_formato(dados_tabela, formato)
            
            # 5. Solicitar local de salvamento
            extensao = data_exporter.get_file_extension(formato)
            nome_sugerido = f"exportacao_aci_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extensao}"
            
            arquivo_destino, _ = QFileDialog.getSaveFileName(
                self,
                f"Salvar como {formato}",
                nome_sugerido,
                f"Arquivos {formato} (*{extensao});;Todos os arquivos (*.*)"
            )
            
            if not arquivo_destino:
                self.status_message_requested.emit("Exportação cancelada pelo usuário.")
                return
            
            # 6. Salvar arquivo
            self._salvar_arquivo_exportacao(arquivo_destino, conteudo_arquivo, formato)
            
            # 7. Confirmar sucesso
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Dados exportados com sucesso para:\n{arquivo_destino}",
                QMessageBox.StandardButton.Ok
            )
            
            self.status_message_requested.emit(f"Exportação para {formato} concluída com sucesso.")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Exportação",
                f"Erro ao exportar para {formato}:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            self.status_message_requested.emit(f"Erro na exportação: {str(e)}")
    
    def _coletar_dados_da_tabela(self) -> List[Dict[str, Any]]:
        """
        Coleta todos os dados da tabela e converte para lista de dicionários.
        
        Returns:
            List[Dict[str, Any]]: Dados da tabela
        """
        dados = []
        
        try:
            # Obter headers
            headers = []
            for col in range(self.modelo_original.columnCount()):
                header_item = self.modelo_original.horizontalHeaderItem(col)
                headers.append(header_item.text() if header_item else f"Coluna_{col}")
            
            # Obter dados das linhas
            for row in range(self.modelo_original.rowCount()):
                linha_dict = {}
                for col in range(self.modelo_original.columnCount()):
                    item = self.modelo_original.item(row, col)
                    valor = item.text() if item else ""
                    linha_dict[headers[col]] = valor
                dados.append(linha_dict)
            
            return dados
            
        except Exception as e:
            print(f"Erro ao coletar dados da tabela: {str(e)}")
            return []
    
    def _salvar_arquivo_exportacao(self, caminho_arquivo: str, conteudo: Union[str, bytes], formato: str):
        """
        Salva o conteúdo no arquivo especificado.
        
        Args:
            caminho_arquivo (str): Caminho completo do arquivo
            conteudo (Union[str, bytes]): Conteúdo a ser salvo
            formato (str): Formato do arquivo para determinar modo de escrita
        """
        try:
            # Determinar modo de escrita baseado no formato
            if formato.lower() in ['excel', 'pdf', 'xls', 'xlsx']:
                # Formatos binários
                with open(caminho_arquivo, 'wb') as arquivo:
                    arquivo.write(conteudo)
            else:
                # Formatos de texto
                with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                    arquivo.write(conteudo)
                    
        except Exception as e:
            raise Exception(f"Erro ao salvar arquivo: {str(e)}")
