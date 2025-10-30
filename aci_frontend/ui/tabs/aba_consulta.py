# -*- coding: utf-8 -*-
"""
ACI Frontend - Aba de Consulta
Representa a aba 'Consultar Informações'
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QCheckBox, QScrollArea,
    QTextEdit, QMenu, QRadioButton, QStackedWidget, QMessageBox
)
from PySide6.QtGui import QStandardItem
from PySide6.QtCore import Qt, Signal, QThread

from ..widgets.resultados_widget import ResultadosWidget
from ...backend.service_manager import service_manager

class AbaConsulta(QWidget):
    """Representa a aba 'Consultar Informações'."""
    status_message_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inicializar_ui()
        self._conectar_sinais()
        self._atualizar_fluxo_consulta(self.combo_tipo_busca.currentText())
        # Dados fictícios removidos - tabela iniciará vazia

    def _inicializar_ui(self):
        """Configura a interface da aba de consulta com layout de cabeçalho e corpo."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)

        # --- CABEÇALHO DE CONTROLES ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.painel_principal = self._criar_painel_principal()
        header_layout.addWidget(self.painel_principal, 1)

        right_controls_widget = QWidget()
        right_controls_layout = QVBoxLayout(right_controls_widget)
        right_controls_layout.setContentsMargins(0, 0, 0, 0)

        self.painel_selecao_sistemas = self._criar_painel_selecao_sistemas()

        campos_retornar_container = QGroupBox("Campos a Retornar")
        campos_retornar_layout = QHBoxLayout(campos_retornar_container)

        campos_algar = ["ID OS", "Protocolo", "Circuito", "Subscrição", "Localidade", "Fila Atual", "Tipo de OS",
                        "Data de criação", "Data de entrada na fila"]
        self.painel_algar, self.checkboxes_algar = self._criar_painel_selecao_campos("Sistema Algar SOM", campos_algar)

        campos_connect = ["CTO", "Porta da CTO", "Status (Ocupado, vago, etc)", "OLT", "Nome da gerencia da OLT",
                          "IP da OLT", "Shelf/Slot/Porta", "Tecnologia", "Serial", "VLAN's"]
        self.painel_connect, self.checkboxes_connect = self._criar_painel_selecao_campos("Sistema Connect Master",
                                                                                         campos_connect)

        campos_retornar_layout.addWidget(self.painel_algar)
        campos_retornar_layout.addWidget(self.painel_connect)

        right_controls_layout.addWidget(self.painel_selecao_sistemas)
        right_controls_layout.addWidget(campos_retornar_container)
        right_controls_layout.addStretch(1)

        header_layout.addWidget(right_controls_widget, 2)
        layout_principal.addWidget(header_widget)

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setObjectName("PrimaryButton")
        self.btn_consultar.setFixedWidth(150)
        layout_principal.addWidget(self.btn_consultar, 0, Qt.AlignmentFlag.AlignRight)

        # --- CORPO DE RESULTADOS ---
        self.resultados_widget = ResultadosWidget()
        layout_principal.addWidget(self.resultados_widget, 1)

    def _criar_painel_selecao_sistemas(self):
        group_box = QGroupBox("Fonte da Consulta")
        layout = QHBoxLayout(group_box)
        self.radio_apenas_algar = QRadioButton("Algar SOM")
        self.radio_apenas_connect = QRadioButton("Connect Master")
        self.radio_ambos = QRadioButton("Ambos os Sistemas")
        self.radio_ambos.setChecked(True)
        layout.addWidget(self.radio_apenas_algar)
        layout.addWidget(self.radio_apenas_connect)
        layout.addWidget(self.radio_ambos)
        layout.addStretch(1)
        return group_box

    def _criar_painel_principal(self):
        group_box = QGroupBox("Parâmetros de Busca")
        layout = QGridLayout(group_box)
        layout.setSpacing(10)

        label_tipo = QLabel("Buscar por:")
        self.combo_tipo_busca = QComboBox()
        self.combo_tipo_busca.addItems(["Protocolo Algar SOM", "Circuito", "ID OS", "CTO", "OLT", "PON", "Fila", "Localidade"])

        # NOVO: Checkboxes condicionais para Protocolo e Circuito
        self.checkbox_protocolo_zeros = QCheckBox("Adicionar dois zeros à esquerda")
        self.checkbox_protocolo_zeros.setVisible(False)
        
        self.checkbox_circuito_zero = QCheckBox("Adicionar um zero à esquerda")
        self.checkbox_circuito_zero.setVisible(False)

        self.label_valor = QLabel("Valores (um por linha):")

        # Container principal para inputs condicionais
        self.inputs_container = QStackedWidget()
        
        # Widget 1: Input de texto padrão
        self.input_container = QWidget()
        input_layout = QGridLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        self.input_valor_busca = QTextEdit()
        self.input_valor_busca.setPlaceholderText("Cole ou digite os valores aqui...")
        self.input_valor_busca.setStyleSheet("padding-top: 5px; padding-right: 30px;")
        self.input_valor_busca.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.btn_colar_busca = QPushButton()
        self.btn_colar_busca.setObjectName("PasteButton")
        self.btn_colar_busca.setCursor(Qt.PointingHandCursor)
        self.btn_colar_busca.setFixedSize(24, 24)
        self.btn_colar_busca.setToolTip("Colar da área de transferência (Ctrl+V)")

        input_layout.addWidget(self.input_valor_busca, 0, 0)
        input_layout.addWidget(self.btn_colar_busca, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Widget 2: Dropdown para Fila
        self.combo_fila_busca = QComboBox()
        self.combo_fila_busca.addItems(["Despacho", "Triagem", "Massiva"])

        # Widget 3: NOVO - Campos para PON
        self.pon_container = self._criar_campos_pon()
        
        # Widget 4: NOVO - Dropdown para Localidade
        self.combo_localidade = QComboBox()
        self.combo_localidade.addItem("Selecione a Localidade")
        self.combo_localidade.setPlaceholderText("Selecione a Localidade")

        # Adicionar widgets ao stack
        self.inputs_container.addWidget(self.input_container)  # 0: Padrão
        self.inputs_container.addWidget(self.combo_fila_busca)  # 1: Fila
        self.inputs_container.addWidget(self.pon_container)  # 2: PON
        self.inputs_container.addWidget(self.combo_localidade)  # 3: Localidade

        # NOVA IMPLEMENTAÇÃO: Checkbox "Apenas Corretiva de Dados"
        self.checkbox_apenas_corretiva = QCheckBox("Retornar apenas corretiva de dados")
        self.checkbox_apenas_corretiva.setVisible(False)  # Inicialmente oculto

        # CORREÇÃO CRÍTICA: Layout compacto e organizado
        layout.addWidget(label_tipo, 0, 0, 1, 2)
        layout.addWidget(self.combo_tipo_busca, 1, 0, 1, 2)
        layout.addWidget(self.checkbox_protocolo_zeros, 2, 0, 1, 2)
        layout.addWidget(self.checkbox_circuito_zero, 2, 0, 1, 2)
        layout.addWidget(self.label_valor, 3, 0, 1, 2)
        layout.addWidget(self.inputs_container, 4, 0, 1, 2)
        layout.addWidget(self.checkbox_apenas_corretiva, 5, 0, 1, 2)  # Nova checkbox
        
        # CRÍTICO: Controle de altura para evitar expansão excessiva
        layout.setRowStretch(0, 0)  # Tipo: sem stretch
        layout.setRowStretch(1, 0)  # Combo: sem stretch 
        layout.setRowStretch(2, 0)  # Checkboxes: sem stretch
        layout.setRowStretch(3, 0)  # Label: sem stretch
        layout.setRowStretch(4, 1)  # Inputs: expandir apenas se necessário
        
        # Definir altura máxima para containers específicos
        self.combo_fila_busca.setMaximumHeight(40)
        self.combo_localidade.setMaximumHeight(40)

        return group_box

    def _criar_painel_selecao_campos(self, nome_sistema, campos):
        widget = QWidget()
        layout_principal_grupo = QVBoxLayout(widget)
        layout_principal_grupo.setContentsMargins(0, 0, 0, 0)

        label_titulo = QLabel(nome_sistema)
        label_titulo.setStyleSheet("font-weight: bold; margin-bottom: 5px;")

        layout_botoes_selecao = QHBoxLayout()
        btn_selecionar_todos = QPushButton("Todos")
        btn_limpar_selecao = QPushButton("Nenhum")
        layout_botoes_selecao.addWidget(btn_selecionar_todos)
        layout_botoes_selecao.addWidget(btn_limpar_selecao)
        layout_botoes_selecao.addStretch(1)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("ScrollArea")
        widget_scroll = QWidget()
        layout_checkboxes = QVBoxLayout(widget_scroll)

        checkboxes_list = [QCheckBox(campo) for campo in campos]
        for chk in checkboxes_list:
            chk.setChecked(True)
            layout_checkboxes.addWidget(chk)

        layout_checkboxes.addStretch(1)
        scroll_area.setWidget(widget_scroll)

        layout_principal_grupo.addWidget(label_titulo)
        layout_principal_grupo.addLayout(layout_botoes_selecao)
        layout_principal_grupo.addWidget(scroll_area)

        btn_selecionar_todos.clicked.connect(lambda: self._selecionar_todos(checkboxes_list))
        btn_limpar_selecao.clicked.connect(lambda: self._limpar_todos(checkboxes_list))

        return widget, checkboxes_list

    def _criar_campos_pon(self):
        """Cria os campos específicos para busca por PON."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de radio buttons para formato de entrada
        grupo_formato = QGroupBox("Formato de Entrada")
        layout_formato = QVBoxLayout(grupo_formato)
        
        self.radio_pon_separados = QRadioButton("OLT + PON separados")
        self.radio_pon_separados.setChecked(True)
        self.radio_pon_juntos = QRadioButton("Juntos (OLT[shelf/slot/porta])")
        
        layout_formato.addWidget(self.radio_pon_separados)
        layout_formato.addWidget(self.radio_pon_juntos)
        
        # Campos de entrada
        campos_container = QWidget()
        campos_layout = QGridLayout(campos_container)
        
        # Campo OLT
        label_olt = QLabel("OLT:")
        self.input_olt = QLineEdit()
        self.input_olt.setPlaceholderText("Nome da OLT, IP, etc.")
        
        # Campo Shelf/Slot/Porta
        label_shelf = QLabel("Shelf/Slot/Porta:")
        self.input_shelf = QLineEdit()
        self.input_shelf.setPlaceholderText("Ex: 1/1/1")
        
        campos_layout.addWidget(label_olt, 0, 0)
        campos_layout.addWidget(self.input_olt, 0, 1)
        campos_layout.addWidget(label_shelf, 1, 0)
        campos_layout.addWidget(self.input_shelf, 1, 1)
        
        # Grupo de radio buttons para tipo de OLT
        grupo_tipo_olt = QGroupBox("Tipo de Informação OLT")
        layout_tipo_olt = QVBoxLayout(grupo_tipo_olt)
        
        self.radio_nome_olt = QRadioButton("Nome OLT")
        self.radio_nome_olt.setChecked(True)
        self.radio_nome_gerencia = QRadioButton("Nome Gerência")
        self.radio_ip_olt = QRadioButton("IP da OLT")
        self.radio_vlan_outer = QRadioButton("VLAN Outer")
        
        layout_tipo_olt.addWidget(self.radio_nome_olt)
        layout_tipo_olt.addWidget(self.radio_nome_gerencia)
        layout_tipo_olt.addWidget(self.radio_ip_olt)
        layout_tipo_olt.addWidget(self.radio_vlan_outer)
        
        layout.addWidget(grupo_formato)
        layout.addWidget(campos_container)
        layout.addWidget(grupo_tipo_olt)
        layout.addStretch(1)
        
        return widget

    def _conectar_sinais(self):
        """Conecta todos os sinais (eventos) dos widgets aos seus slots (funções)."""
        self.combo_tipo_busca.currentTextChanged.connect(self._atualizar_fluxo_consulta)
        self.btn_colar_busca.clicked.connect(self.input_valor_busca.paste)
        self.input_valor_busca.customContextMenuRequested.connect(self._show_input_context_menu)

        self.radio_apenas_algar.toggled.connect(self._atualizar_visibilidade_paineis_campos)
        self.radio_apenas_connect.toggled.connect(self._atualizar_visibilidade_paineis_campos)
        self.radio_ambos.toggled.connect(self._atualizar_visibilidade_paineis_campos)

        # NOVA REGRA: Conectar carregamento de localidades
        self.radio_apenas_algar.toggled.connect(self._verificar_carregamento_localidades)
        self.combo_tipo_busca.currentTextChanged.connect(self._verificar_carregamento_localidades)

        self.btn_consultar.clicked.connect(self._processar_consulta_com_validacao)
        self.resultados_widget.status_message_requested.connect(self.status_message_requested)

    def _limpar_tela(self):
        """Reseta todos os campos de input para o estado inicial."""
        self.input_valor_busca.clear()
        self.combo_tipo_busca.setCurrentIndex(0)
        self.radio_ambos.setChecked(True)
        self._selecionar_todos(self.checkboxes_algar)
        self._selecionar_todos(self.checkboxes_connect)
        self.resultados_widget.clear_results()  # Limpa também a tabela
        self.status_message_requested.emit("Tela limpa. Pronto para nova consulta.")

    def _show_input_context_menu(self, pos):
        """Exibe um menu de contexto customizado e em português para o campo de texto."""
        menu = QMenu(self)
        menu.addAction("Recortar", self.input_valor_busca.cut).setEnabled(
            self.input_valor_busca.textCursor().hasSelection())
        menu.addAction("Copiar", self.input_valor_busca.copy).setEnabled(
            self.input_valor_busca.textCursor().hasSelection())
        menu.addAction("Colar", self.input_valor_busca.paste)
        menu.addSeparator()
        menu.addAction("Desfazer", self.input_valor_busca.undo).setEnabled(
            self.input_valor_busca.document().isUndoAvailable())
        menu.addAction("Refazer", self.input_valor_busca.redo).setEnabled(
            self.input_valor_busca.document().isRedoAvailable())
        menu.addSeparator()
        menu.addAction("Selecionar Tudo", self.input_valor_busca.selectAll)
        menu.exec(self.input_valor_busca.mapToGlobal(pos))

    def _atualizar_fluxo_consulta(self, tipo_busca):
        """Controla a visibilidade dos campos com base no parâmetro de busca."""
        # Ocultar todos os checkboxes condicionais primeiro
        self.checkbox_protocolo_zeros.setVisible(False)
        self.checkbox_circuito_zero.setVisible(False)
        
        # Mostrar checkboxes específicos baseados no tipo de busca
        if "Protocolo" in tipo_busca:
            self.checkbox_protocolo_zeros.setVisible(True)
        elif "Circuito" in tipo_busca:
            self.checkbox_circuito_zero.setVisible(True)
        
        # Determinar qual widget mostrar no stack
        if tipo_busca == "Fila":
            self.inputs_container.setCurrentIndex(1)  # Dropdown de fila
            self.label_valor.setText("Selecione a Fila:")
        elif tipo_busca == "PON":
            self.inputs_container.setCurrentIndex(2)  # Campos PON
            self.label_valor.setText("Configuração PON:")
        elif tipo_busca == "Localidade":
            self.inputs_container.setCurrentIndex(3)  # Dropdown localidade
            self.label_valor.setText("Selecione a Localidade:")
        else:
            self.inputs_container.setCurrentIndex(0)  # Input padrão
            self.label_valor.setText("Valores (um por linha):")
        
        # Lógica para sistemas
        opcoes_connect_master = ["CTO", "OLT", "PON"]
        is_connect_only = tipo_busca in opcoes_connect_master
        
        self.painel_selecao_sistemas.setVisible(not is_connect_only)
        if is_connect_only:
            self.radio_apenas_connect.setChecked(True)

        # NOVA IMPLEMENTAÇÃO: Controlar visibilidade da checkbox "Apenas Corretiva"
        self._atualizar_visibilidade_checkbox_corretiva()
        
        self._atualizar_visibilidade_paineis_campos()
        
        # Emitir status de mudança
        self.status_message_requested.emit(f"Modo de busca alterado para: {tipo_busca}")

    def _atualizar_visibilidade_paineis_campos(self):
        """Mostra ou oculta os painéis de seleção de campos com base no Radio Button."""
        show_algar = self.radio_apenas_algar.isChecked() or self.radio_ambos.isChecked()
        show_connect = self.radio_apenas_connect.isChecked() or self.radio_ambos.isChecked()
        self.painel_algar.setVisible(show_algar)
        self.painel_connect.setVisible(show_connect)
        
        # NOVA IMPLEMENTAÇÃO: Atualizar visibilidade da checkbox após mudança de sistema
        self._atualizar_visibilidade_checkbox_corretiva()
    
    def _atualizar_visibilidade_checkbox_corretiva(self):
        """
        NOVA FUNÇÃO: Controla visibilidade da checkbox "Apenas Corretiva de Dados".
        Exibe apenas quando busca por 'Localidade' ou 'Fila' estiver ativa.
        """
        search_type = self.combo_tipo_busca.currentText()
        
        # Mostrar checkbox para buscas por Localidade ou Fila
        show_checkbox = search_type in ["Localidade", "Fila"]
        
        self.checkbox_apenas_corretiva.setVisible(show_checkbox)
        
        # Reset checkbox se oculta
        if not show_checkbox:
            self.checkbox_apenas_corretiva.setChecked(False)

    def _selecionar_todos(self, checkboxes):
        for checkbox in checkboxes: 
            checkbox.setChecked(True)

    def _limpar_todos(self, checkboxes):
        for checkbox in checkboxes: 
            checkbox.setChecked(False)

    def _criar_modelo_exemplo(self):
        """Cria e define o modelo de dados de exemplo na tabela de resultados."""
        modelo = self.resultados_widget.get_model()
        modelo.clear()

        headers = ["Protocolo", "Circuito", "CTO", "PON", "OLT", "FILA", "Status"]
        modelo.setHorizontalHeaderLabels(headers)
        self.resultados_widget.original_headers = headers

        dados = [
            ["1-123456", "CIR456789", "CTO-01-A01", "1", "OLT-UB-01", "DESPACHO", "Aberto"],
            ["1-234567", "CIR567890", "CTO-02-B03", "3", "OLT-UB-02", "TRIAGEM", "Pendente"],
            ["1-345678", "CIR678901", "CTO-03-C05", "5", "OLT-UB-03", "MASSIVA", "Em Análise"],
            ["1-456789", "CIR789012", "CTO-04-D07", "7", "OLT-UB-04", "DESPACHO", "Resolvido"],
            ["1-567890", "CIR890123", "CTO-05-E09", "9", "OLT-UB-05", "TRIAGEM", "Aguardando"],
        ]
        for i, linha in enumerate(dados):
            for j, valor in enumerate(linha):
                modelo.setItem(i, j, QStandardItem(valor))
        self.status_message_requested.emit(f"{len(dados)} resultados carregados.")

    def _executar_consulta_backend(self):
        """
        NOVA INTEGRAÇÃO: Executa consulta real usando o backend Oracle.
        Substitui o método de exemplo anterior.
        """
        try:
            # Desabilitar botão durante execução
            self.btn_consultar.setEnabled(False)
            self.btn_consultar.setText("Consultando...")
            self.status_message_requested.emit("Iniciando consulta no backend...")
            
            # Coletar dados do frontend
            frontend_data = self._coletar_dados_frontend()
            
            # Validar dados básicos
            if not frontend_data:
                self._mostrar_erro("Erro ao coletar dados do formulário")
                return
            
            # Executar consulta via service manager
            resultado = service_manager.process_search_request(frontend_data)
            
            # Processar resultado
            self._processar_resultado_backend(resultado)
            
        except Exception as e:
            self._mostrar_erro(f"Erro na consulta: {str(e)}")
            
        finally:
            # Reabilitar botão
            self.btn_consultar.setEnabled(True)
            self.btn_consultar.setText("Consultar")
    
    def _coletar_dados_frontend(self) -> dict:
        """
        Coleta todos os dados do formulário para enviar ao backend.
        
        Returns:
            dict: Dados estruturados para o backend
        """
        try:
            # Tipo de busca
            search_type = self.combo_tipo_busca.currentText()
            
            # Valores de entrada
            values = ""
            if search_type == "Fila":
                values = self.combo_fila_busca.currentText()
            elif search_type == "Localidade":
                values = self.combo_localidade.currentText()
            else:
                values = self.input_valor_busca.toPlainText()
            
            # Sistemas selecionados
            selected_systems = []
            if self.radio_apenas_algar.isChecked():
                selected_systems = ["SOMPRD"]
            elif self.radio_apenas_connect.isChecked():
                selected_systems = ["CMPRD"]
            else:  # Ambos
                selected_systems = ["SOMPRD", "CMPRD"]
            
            # Campos selecionados
            selected_fields = []
            if self.painel_algar.isVisible():
                for checkbox in self.checkboxes_algar:
                    if checkbox.isChecked():
                        selected_fields.append(checkbox.text().lower().replace(" ", "_"))
            
            if self.painel_connect.isVisible():
                for checkbox in self.checkboxes_connect:
                    if checkbox.isChecked():
                        selected_fields.append(checkbox.text().lower().replace(" ", "_"))
            
            # Montar estrutura de dados
            frontend_data = {
                "search_type": search_type,
                "values": values,
                "add_zeros_protocolo": self.checkbox_protocolo_zeros.isChecked(),
                "add_zero_circuito": self.checkbox_circuito_zero.isChecked(),
                "selected_systems": selected_systems,
                "selected_fields": selected_fields,
                "fila_value": self.combo_fila_busca.currentText() if search_type == "Fila" else "",
                "apenas_corretiva": self.checkbox_apenas_corretiva.isChecked(),  # NOVA INTEGRAÇÃO
            }
            
            return frontend_data
            
        except Exception as e:
            self.status_message_requested.emit(f"Erro ao coletar dados: {str(e)}")
            return None
    
    def _processar_resultado_backend(self, resultado: dict):
        """
        Processa o resultado do backend e atualiza a tabela.
        
        Args:
            resultado (dict): Resultado retornado pelo service manager
        """
        try:
            # DEBUG: Log completo do resultado
            print(f"DEBUG: Resultado completo recebido: {resultado}")
            
            if not resultado.get("success", False):
                error_msg = resultado.get("message", "Erro desconhecido na consulta")
                self._mostrar_erro(error_msg)
                return
            
            # Obter dados
            data = resultado.get("data", [])
            total_records = resultado.get("total_records", 0)
            
            print(f"DEBUG: total_records = {total_records}")
            print(f"DEBUG: len(data) = {len(data)}")
            print(f"DEBUG: data = {data}")
            
            if total_records == 0:
                self.resultados_widget.clear_results()
                message = resultado.get("message", "Nenhum resultado encontrado")
                self.status_message_requested.emit(message)
                
                # Mostrar mensagem especial para OS não encontrada
                if "não foi encontrada" in message:
                    QMessageBox.information(
                        self, 
                        "Resultado da Consulta", 
                        message,
                        QMessageBox.StandardButton.Ok
                    )
                return
            
            # Preparar modelo da tabela
            modelo = self.resultados_widget.get_model()
            modelo.clear()
            
            # Extrair cabeçalhos dos dados (se houver dados)
            if data:
                headers = list(data[0].keys())
                print(f"DEBUG: headers originais = {headers}")
                
                # Remover campo interno do sistema
                if "_source_database" in headers:
                    headers.remove("_source_database")
                
                print(f"DEBUG: headers finais = {headers}")
                
                modelo.setHorizontalHeaderLabels(headers)
                self.resultados_widget.original_headers = headers
                
                # Adicionar dados à tabela
                for row_idx, record in enumerate(data):
                    print(f"DEBUG: Processando linha {row_idx}: {record}")
                    for col_idx, header in enumerate(headers):
                        value = str(record.get(header, ""))
                        print(f"DEBUG: Célula [{row_idx}][{col_idx}] {header} = {value}")
                        item = QStandardItem(value)
                        modelo.setItem(row_idx, col_idx, item)
                
                print(f"DEBUG: Modelo populado com {modelo.rowCount()} linhas e {modelo.columnCount()} colunas")
            
            # Atualizar status
            execution_time = resultado.get("total_execution_time", 0)
            message = f"Consulta concluída: {total_records} registro(s) em {execution_time:.2f}s"
            self.status_message_requested.emit(message)
            
            # Log adicional para debugging
            print(f"DEBUG: Resultado processado com sucesso - {total_records} registros")
            
        except Exception as e:
            print(f"DEBUG: Erro no processamento: {str(e)}")
            import traceback
            traceback.print_exc()
            self._mostrar_erro(f"Erro ao processar resultado: {str(e)}")
    
    def _verificar_carregamento_localidades(self):
        """
        NOVA REGRA: Carrega localidades únicas quando Algar SOM + Localidade é selecionado.
        """
        # Verificar condições para carregamento
        is_algar_selected = self.radio_apenas_algar.isChecked()
        is_localidade_search = self.combo_tipo_busca.currentText() == "Localidade"
        
        if is_algar_selected and is_localidade_search:
            self._carregar_localidades_unicas()
        else:
            # Reset dropdown se condições não atendidas
            self.combo_localidade.clear()
            self.combo_localidade.addItem("Selecione a Localidade")
            self.combo_localidade.setEnabled(False)
    
    def _carregar_localidades_unicas(self):
        """
        Carrega localidades únicas do banco SOMPRD.
        """
        try:
            self.status_message_requested.emit("Carregando localidades disponíveis...")
            self.combo_localidade.setEnabled(False)
            
            # Importar e usar função do backend
            from ...backend.somprd_queries import somprd_queries
            localidades = somprd_queries.obter_localidades_unicas()
            
            # Limpar e popular dropdown
            self.combo_localidade.clear()
            
            if localidades:
                self.combo_localidade.addItem("Selecione a Localidade")
                for localidade in localidades:
                    self.combo_localidade.addItem(localidade)
                self.combo_localidade.setEnabled(True)
                self.status_message_requested.emit(f"{len(localidades)} localidades carregadas.")
            else:
                self.combo_localidade.addItem("Nenhuma localidade encontrada")
                self.combo_localidade.setEnabled(False)
                self.status_message_requested.emit("Nenhuma localidade encontrada no banco.")
                
        except Exception as e:
            self.combo_localidade.clear()
            self.combo_localidade.addItem("Erro ao carregar localidades")
            self.combo_localidade.setEnabled(False)
            self.status_message_requested.emit(f"Erro ao carregar localidades: {str(e)}")
    
    def _processar_consulta_com_validacao(self):
        """
        NOVA FUNÇÃO: Processa consulta com validação de campos obrigatórios.
        """
        try:
            # NOVA REGRA: Validar se pelo menos um campo foi selecionado
            campos_selecionados = []
            
            # Verificar campos Algar SOM
            if self.painel_algar.isVisible():
                for checkbox in self.checkboxes_algar:
                    if checkbox.isChecked():
                        campos_selecionados.append(checkbox.text())
            
            # Verificar campos Connect Master  
            if self.painel_connect.isVisible():
                for checkbox in self.checkboxes_connect:
                    if checkbox.isChecked():
                        campos_selecionados.append(checkbox.text())
            
            # Validação de campos obrigatórios
            if not campos_selecionados:
                QMessageBox.warning(
                    self,
                    "Validação",
                    "Selecione pelo menos um campo para exibir no resultado.",
                    QMessageBox.StandardButton.Ok
                )
                self.status_message_requested.emit("Erro: Nenhum campo selecionado para exibição.")
                return
            
            # Validar valores de entrada para tipos que requerem
            search_type = self.combo_tipo_busca.currentText()
            
            if search_type not in ["Fila"]:  # Fila não precisa de valores de entrada
                values = ""
                if search_type == "Localidade":
                    if self.combo_localidade.currentText() in ["Selecione a Localidade", "Nenhuma localidade encontrada", "Erro ao carregar localidades"]:
                        QMessageBox.warning(
                            self,
                            "Validação",
                            "Selecione uma localidade válida para a consulta.",
                            QMessageBox.StandardButton.Ok
                        )
                        return
                else:
                    values = self.input_valor_busca.toPlainText().strip()
                    if not values:
                        QMessageBox.warning(
                            self,
                            "Validação", 
                            "Digite pelo menos um valor para realizar a consulta.",
                            QMessageBox.StandardButton.Ok
                        )
                        return
            
            # Se passou na validação, executar consulta
            self.status_message_requested.emit(f"Validação concluída. {len(campos_selecionados)} campos selecionados.")
            self._executar_consulta_backend()
            
        except Exception as e:
            self._mostrar_erro(f"Erro na validação: {str(e)}")
    
    def _mostrar_erro(self, mensagem: str):
        """
        Exibe erro ao usuário e atualiza status.
        
        Args:
            mensagem (str): Mensagem de erro
        """
        self.status_message_requested.emit(f"ERRO: {mensagem}")
        QMessageBox.critical(
            self,
            "Erro na Consulta",
            mensagem,
            QMessageBox.StandardButton.Ok
        )
