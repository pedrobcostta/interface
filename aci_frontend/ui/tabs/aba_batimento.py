# -*- coding: utf-8 -*-
"""
ACI Frontend - Aba de Batimento
Representa a aba 'Batimento' com atualizações para suporte a Localidade e filtro Corretiva
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QGroupBox, QRadioButton, QTextEdit, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem

from ..widgets.resultados_widget import ResultadosWidget

class AbaBatimento(QWidget):
    """Representa a aba 'Batimento' com suporte a Localidade e filtro Corretiva."""
    status_message_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inicializar_ui()
        self._conectar_sinais()

    def _inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)

        # --- CABEÇALHO DE CONTROLES ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Lado Esquerdo: Controles de Batimento
        left_controls_widget = QWidget()
        left_controls_layout = QVBoxLayout(left_controls_widget)

        # Painel de seleção de fonte
        self.painel_selecao_fonte = self._criar_painel_selecao_fonte()
        left_controls_layout.addWidget(self.painel_selecao_fonte)

        group_tipo = QGroupBox("Qual batimento?")
        layout_tipo = QHBoxLayout(group_tipo)
        self.radio_fibra = QRadioButton("Fibra")
        self.radio_autenticacao = QRadioButton("Autenticação")
        self.radio_ambas = QRadioButton("Ambas")
        self.radio_fibra.setChecked(True)  # Padrão
        layout_tipo.addWidget(self.radio_fibra)
        layout_tipo.addWidget(self.radio_autenticacao)
        layout_tipo.addWidget(self.radio_ambas)
        layout_tipo.addStretch(1)

        group_buscar_por = QGroupBox("Buscar por:")
        layout_buscar = QGridLayout(group_buscar_por)
        
        # ATUALIZADO: Radio buttons para buscar por (removida "Cidade", adicionada "Localidade")
        self.radio_batimento_circuito = QRadioButton("Circuito")
        self.radio_batimento_protocolo = QRadioButton("Protocolo")
        self.radio_batimento_cto = QRadioButton("CTO")
        self.radio_batimento_olt = QRadioButton("OLT")
        self.radio_batimento_pon = QRadioButton("PON")
        self.radio_batimento_localidade = QRadioButton("Localidade")  # NOVO
        self.radio_batimento_estacao = QRadioButton("Estação")
        
        # Layout dos radio buttons
        layout_buscar.addWidget(self.radio_batimento_circuito, 0, 0)
        layout_buscar.addWidget(self.radio_batimento_protocolo, 0, 1)
        layout_buscar.addWidget(self.radio_batimento_cto, 0, 2)
        layout_buscar.addWidget(self.radio_batimento_olt, 1, 0)
        layout_buscar.addWidget(self.radio_batimento_pon, 1, 1)
        layout_buscar.addWidget(self.radio_batimento_localidade, 1, 2)  # NOVO
        layout_buscar.addWidget(self.radio_batimento_estacao, 2, 0)
        
        # Configurar primeiro como selecionado
        self.radio_batimento_circuito.setChecked(True)

        # Checkboxes condicionais para Protocolo e Circuito
        self.checkbox_batimento_protocolo = QCheckBox("Adicionar dois zeros à esquerda")
        self.checkbox_batimento_protocolo.setVisible(False)
        
        self.checkbox_batimento_circuito = QCheckBox("Adicionar um zero à esquerda")
        self.checkbox_batimento_circuito.setVisible(True)  # Circuito já está selecionado

        # NOVA IMPLEMENTAÇÃO: Checkbox "Apenas Corretiva de Dados"
        self.checkbox_apenas_corretiva = QCheckBox("Retornar apenas corretiva de dados")
        self.checkbox_apenas_corretiva.setVisible(False)  # Inicialmente oculto

        # NOVO: Dropdown para Localidade (inicialmente oculto)
        self.combo_localidade = QComboBox()
        self.combo_localidade.addItem("Selecione a Localidade")
        self.combo_localidade.setVisible(False)

        left_controls_layout.addWidget(group_tipo)
        left_controls_layout.addWidget(group_buscar_por)
        left_controls_layout.addWidget(self.checkbox_batimento_protocolo)
        left_controls_layout.addWidget(self.checkbox_batimento_circuito)
        left_controls_layout.addWidget(self.combo_localidade)  # Dropdown localidade
        left_controls_layout.addWidget(self.checkbox_apenas_corretiva)  # Nova checkbox
        left_controls_layout.addStretch(1)

        # Lado Direito: Input de Valores
        group_valores = QGroupBox("Valores (um por linha)")
        layout_valores = QVBoxLayout(group_valores)
        
        # Container para o campo + botão de colar
        input_container = QWidget()
        input_layout = QGridLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        self.input_valores_batimento = QTextEdit()
        self.input_valores_batimento.setPlaceholderText("Cole ou digite os valores para o batimento...")
        self.input_valores_batimento.setStyleSheet("padding-top: 5px; padding-right: 30px;")
        
        self.btn_colar_batimento = QPushButton("📋")
        self.btn_colar_batimento.setObjectName("PasteButton")
        self.btn_colar_batimento.setCursor(Qt.PointingHandCursor)
        self.btn_colar_batimento.setFixedSize(24, 24)
        self.btn_colar_batimento.setToolTip("Colar da área de transferência (Ctrl+V)")
        
        input_layout.addWidget(self.input_valores_batimento, 0, 0)
        input_layout.addWidget(self.btn_colar_batimento, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        layout_valores.addWidget(input_container)

        header_layout.addWidget(left_controls_widget, 1)
        header_layout.addWidget(group_valores, 1)
        layout_principal.addWidget(header_widget)

        # Botão de Ação Principal
        self.btn_bater_dados = QPushButton("Bater Dados")
        self.btn_bater_dados.setObjectName("PrimaryButton")
        self.btn_bater_dados.setFixedWidth(150)
        layout_principal.addWidget(self.btn_bater_dados, 0, Qt.AlignmentFlag.AlignRight)

        # --- CORPO DE RESULTADOS ---
        self.resultados_widget = ResultadosWidget("Resultados do Batimento")
        layout_principal.addWidget(self.resultados_widget, 1)

        # Conectar sinal da status bar
        self.resultados_widget.status_message_requested.connect(self.status_message_requested)

    def _criar_painel_selecao_fonte(self):
        """NOVA IMPLEMENTAÇÃO: Cria painel para seleção de fonte de dados."""
        group_box = QGroupBox("Fonte da Consulta")
        layout = QHBoxLayout(group_box)
        
        self.radio_fonte_algar = QRadioButton("Algar SOM")
        self.radio_fonte_connect = QRadioButton("Connect Master")
        self.radio_fonte_algar.setChecked(True)  # Padrão
        
        layout.addWidget(self.radio_fonte_algar)
        layout.addWidget(self.radio_fonte_connect)
        layout.addStretch(1)
        
        return group_box

    def _conectar_sinais(self):
        """Conecta todos os sinais dos widgets."""
        # Conectar sinais para atualizar checkboxes baseado no tipo de busca
        self.radio_batimento_protocolo.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_circuito.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_cto.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_olt.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_pon.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_localidade.toggled.connect(self._atualizar_interface_batimento)
        self.radio_batimento_estacao.toggled.connect(self._atualizar_interface_batimento)
        
        # Conectar mudanças de fonte
        self.radio_fonte_algar.toggled.connect(self._atualizar_interface_batimento)
        self.radio_fonte_connect.toggled.connect(self._atualizar_interface_batimento)
        
        # Conectar botão de colar
        self.btn_colar_batimento.clicked.connect(self.input_valores_batimento.paste)
        
        # NOVA CONEXÃO: Conectar botão de execução do batimento
        self.btn_bater_dados.clicked.connect(self._executar_batimento_fibra)

    def _atualizar_interface_batimento(self):
        """
        NOVA IMPLEMENTAÇÃO: Atualiza interface baseada nas seleções.
        Inclui lógica para Localidade e checkbox "Apenas Corretiva".
        """
        # Ocultar todos os elementos condicionais primeiro
        self.checkbox_batimento_protocolo.setVisible(False)
        self.checkbox_batimento_circuito.setVisible(False)
        self.combo_localidade.setVisible(False)
        self.checkbox_apenas_corretiva.setVisible(False)
        
        # Mostrar elementos específicos baseado na seleção
        if self.radio_batimento_protocolo.isChecked():
            self.checkbox_batimento_protocolo.setVisible(True)
        elif self.radio_batimento_circuito.isChecked():
            self.checkbox_batimento_circuito.setVisible(True)
        elif self.radio_batimento_localidade.isChecked():
            self.combo_localidade.setVisible(True)
            # Carregar localidades se Algar SOM estiver selecionado
            if self.radio_fonte_algar.isChecked():
                self._carregar_localidades_unicas()
            
        # NOVA REGRA: Mostrar checkbox "Apenas Corretiva" para busca por Localidade
        if self.radio_batimento_localidade.isChecked():
            self.checkbox_apenas_corretiva.setVisible(True)
        
        # Emitir status de mudança
        tipo_selecionado = self._obter_tipo_busca_selecionado()
        fonte_selecionada = "Algar SOM" if self.radio_fonte_algar.isChecked() else "Connect Master"
        
        if tipo_selecionado:
            self.status_message_requested.emit(f"Batimento por {tipo_selecionado} ({fonte_selecionada}) selecionado")

    def _obter_tipo_busca_selecionado(self) -> str:
        """Retorna o tipo de busca atualmente selecionado."""
        if self.radio_batimento_protocolo.isChecked():
            return "Protocolo"
        elif self.radio_batimento_circuito.isChecked():
            return "Circuito"
        elif self.radio_batimento_cto.isChecked():
            return "CTO"
        elif self.radio_batimento_olt.isChecked():
            return "OLT"
        elif self.radio_batimento_pon.isChecked():
            return "PON"
        elif self.radio_batimento_localidade.isChecked():
            return "Localidade"
        elif self.radio_batimento_estacao.isChecked():
            return "Estação"
        return ""

    def _carregar_localidades_unicas(self):
        """
        NOVA IMPLEMENTAÇÃO: Carrega localidades únicas do banco selecionado.
        """
        try:
            self.status_message_requested.emit("Carregando localidades disponíveis...")
            self.combo_localidade.setEnabled(False)
            
            # Determinar qual banco usar baseado na fonte selecionada
            if self.radio_fonte_algar.isChecked():
                from ...backend.somprd_queries import somprd_queries
                localidades = somprd_queries.obter_localidades_unicas()
            else:
                from ...backend.cmprd_queries import cmprd_queries
                localidades = cmprd_queries.obter_localidades_unicas()
            
            # Limpar e popular dropdown
            self.combo_localidade.clear()
            
            if localidades:
                self.combo_localidade.addItem("Selecione a Localidade")
                for localidade in localidades:
                    self.combo_localidade.addItem(localidade)
                self.combo_localidade.setEnabled(True)
                fonte = "Algar SOM" if self.radio_fonte_algar.isChecked() else "Connect Master"
                self.status_message_requested.emit(f"{len(localidades)} localidades carregadas do {fonte}.")
            else:
                self.combo_localidade.addItem("Nenhuma localidade encontrada")
                self.combo_localidade.setEnabled(False)
                self.status_message_requested.emit("Nenhuma localidade encontrada no banco.")
                
        except Exception as e:
            self.combo_localidade.clear()
            self.combo_localidade.addItem("Erro ao carregar localidades")
            self.combo_localidade.setEnabled(False)
            self.status_message_requested.emit(f"Erro ao carregar localidades: {str(e)}")

    def _coletar_dados_batimento(self) -> dict:
        """
        NOVA IMPLEMENTAÇÃO: Coleta dados do formulário para o backend.
        
        Returns:
            dict: Dados estruturados para processamento
        """
        try:
            # Tipo de busca
            search_type = self._obter_tipo_busca_selecionado()
            
            # Valores de entrada
            if search_type == "Localidade":
                values = self.combo_localidade.currentText()
            else:
                values = self.input_valores_batimento.toPlainText()
            
            # Sistema selecionado
            selected_system = "SOMPRD" if self.radio_fonte_algar.isChecked() else "CMPRD"
            
            # Tipo de batimento
            tipo_batimento = ""
            if self.radio_fibra.isChecked():
                tipo_batimento = "Fibra"
            elif self.radio_autenticacao.isChecked():
                tipo_batimento = "Autenticação"
            else:
                tipo_batimento = "Ambas"
            
            # Montar estrutura de dados
            batimento_data = {
                "search_type": search_type,
                "values": values,
                "selected_system": selected_system,
                "tipo_batimento": tipo_batimento,
                "add_zeros_protocolo": self.checkbox_batimento_protocolo.isChecked(),
                "add_zero_circuito": self.checkbox_batimento_circuito.isChecked(),
                "apenas_corretiva": self.checkbox_apenas_corretiva.isChecked(),
            }
            
            return batimento_data
            
        except Exception as e:
            self.status_message_requested.emit(f"Erro ao coletar dados: {str(e)}")
            return None

    def _executar_batimento_fibra(self):
        """
        NOVA IMPLEMENTAÇÃO: Executa o batimento de fibra integrado.
        """
        try:
            # Coletar dados do formulário
            dados = self._coletar_dados_batimento()
            
            if not dados:
                self.status_message_requested.emit("Erro ao coletar dados do formulário")
                return
            
            # Validar se é batimento de fibra
            if dados.get("tipo_batimento") not in ["Fibra", "Ambas"]:
                self.status_message_requested.emit("Batimento de Autenticação ainda não implementado. Use 'Fibra' ou 'Ambas'.")
                return
            
            # Validar se há valores para processar
            values = dados.get("values", "").strip()
            if not values:
                self.status_message_requested.emit("Digite circuitos para o batimento de fibra.")
                return
            
            # Para busca por Localidade, usar comportamento especial
            if dados.get("search_type") == "Localidade":
                if values == "Selecione a Localidade":
                    self.status_message_requested.emit("Selecione uma localidade válida.")
                    return
                self.status_message_requested.emit("Batimento por localidade ainda não implementado. Use busca por Circuito.")
                return
            
            # Processar lista de circuitos
            if dados.get("search_type") == "Circuito":
                # Extrair circuitos da entrada de texto
                circuitos_list = [
                    linha.strip() 
                    for linha in values.split('\n') 
                    if linha.strip()
                ]
                
                if not circuitos_list:
                    self.status_message_requested.emit("Nenhum circuito válido encontrado na entrada.")
                    return
                
                # Aplicar transformações se necessário
                if dados.get("add_zero_circuito"):
                    circuitos_list = [f"0{circuito}" if not circuito.startswith("0") else circuito for circuito in circuitos_list]
                
                self.status_message_requested.emit(f"Iniciando batimento de fibra para {len(circuitos_list)} circuitos...")
                
                # Importar e executar módulo de batimento
                from ...backend.batimento_fibra import batimento_fibra
                
                # Executar batimento
                df_resultados = batimento_fibra.executar_batimento_fibra(circuitos_list)
                
                if df_resultados.empty:
                    self.status_message_requested.emit("Batimento concluído, mas nenhum resultado foi gerado.")
                    self.resultados_widget.clear_results()
                    return
                
                # Converter DataFrame para formato da tabela
                self._popular_tabela_resultados(df_resultados)
                
                self.status_message_requested.emit(f"Batimento concluído: {len(df_resultados)} resultados processados.")
                
            else:
                self.status_message_requested.emit(f"Batimento por {dados.get('search_type')} ainda não implementado. Use busca por Circuito.")
                return
            
        except Exception as e:
            self.status_message_requested.emit(f"Erro na execução do batimento: {str(e)}")
            import traceback
            print(f"Erro detalhado no batimento: {traceback.format_exc()}")
    
    def _popular_tabela_resultados(self, df_resultados):
        """
        Popula a tabela de resultados com os dados do DataFrame.
        
        Args:
            df_resultados: DataFrame com resultados do batimento
        """
        try:
            # Limpar resultados existentes
            self.resultados_widget.clear_results()
            
            if df_resultados.empty:
                return
            
            # Obter modelo da tabela
            modelo = self.resultados_widget.get_model()
            
            # Configurar cabeçalhos
            headers = df_resultados.columns.tolist()
            modelo.setHorizontalHeaderLabels(headers)
            self.resultados_widget.original_headers = headers
            
            # Adicionar dados linha por linha
            for index, row in df_resultados.iterrows():
                row_items = []
                for col_name in headers:
                    valor = str(row[col_name]) if row[col_name] is not None else ""
                    item = QStandardItem(valor)
                    row_items.append(item)
                modelo.appendRow(row_items)
            
        except Exception as e:
            self.status_message_requested.emit(f"Erro ao popular tabela: {str(e)}")
            import traceback
            print(f"Erro detalhado ao popular tabela: {traceback.format_exc()}")
