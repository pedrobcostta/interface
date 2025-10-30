# -*- coding: utf-8 -*-
"""
ACI Frontend - Aba de Ações
Representa a aba 'Ações' com formulários dinâmicos
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QRadioButton, QTextEdit, QStackedWidget,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from ..widgets.resultados_widget import ResultadosWidget

class AbaAcoes(QWidget):
    """Representa a aba 'Ações' com formulários dinâmicos."""
    status_message_requested = Signal(str)

    # Lista de usuários disponíveis - EDITE AQUI para adicionar/remover usuários
    USUARIOS_DISPONIVEIS = [
        "costa.joao",
        "marco.costa", 
        "anna.vale",
        "massivafield"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inicializar_ui()
        self._conectar_sinais()

    def _inicializar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)

        # --- SOLUÇÃO CRÍTICA: LISTA LATERAL + STACKED WIDGET ---
        # Splitter horizontal para dividir abas e conteúdo
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # CORREÇÃO OBRIGATÓRIA: Lista lateral com texto HORIZONTAL
        self.lista_acoes = QListWidget()
        self.lista_acoes.setObjectName("lista_acoes")
        self.lista_acoes.setMaximumWidth(180)
        self.lista_acoes.setMinimumWidth(180)
        
        # Adicionar itens à lista com texto HORIZONTAL garantido
        acoes = ["Cancelar OS", "Mover OS", "Adicionar Obs", "Resgatar OS", "Massiva (Link)", "Massiva (Input)"]
        for acao in acoes:
            item = QListWidgetItem(acao)
            self.lista_acoes.addItem(item)
        
        # Selecionar primeiro item por padrão
        self.lista_acoes.setCurrentRow(0)
        
        # Container direito com formulários e resultados
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de formulários (StackedWidget para trocar conteúdo)
        form_frame = QFrame()
        form_frame.setObjectName("form_frame")
        form_frame.setStyleSheet("""
            QFrame#form_frame {
                border: 1px solid #DEE2E6;
                border-left: none;
                background-color: #FFFFFF;
                border-radius: 0px 8px 8px 0px;
                padding: 25px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        
        # CRÍTICO: StackedWidget para mostrar formulários
        self.stacked_forms = QStackedWidget()
        self.stacked_forms.addWidget(self._criar_form_cancelar_os())
        self.stacked_forms.addWidget(self._criar_form_mover_os()) 
        self.stacked_forms.addWidget(self._criar_form_adicionar_obs())
        self.stacked_forms.addWidget(self._criar_form_resgatar_os())
        self.stacked_forms.addWidget(self._criar_form_massiva_link())
        self.stacked_forms.addWidget(self._criar_form_massiva_input())
        
        form_layout.addWidget(self.stacked_forms)
        
        # Botão de Ação Principal
        self.btn_executar_acao = QPushButton("Executar: Cancelar OS")
        self.btn_executar_acao.setObjectName("PrimaryButton")
        self.btn_executar_acao.setFixedWidth(200)
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_executar_acao)
        
        # Widget de resultados
        self.resultados_widget = ResultadosWidget("Resultados da Ação")
        
        # Adicionar ao container direito
        right_layout.addWidget(form_frame)
        right_layout.addWidget(button_container)
        right_layout.addWidget(self.resultados_widget, 1)
        
        # Adicionar ao splitter principal
        main_splitter.addWidget(self.lista_acoes)
        main_splitter.addWidget(right_container)
        
        # Definir proporções
        main_splitter.setSizes([180, 1000])
        main_splitter.setCollapsible(0, False)
        
        layout_principal.addWidget(main_splitter)

    # --- Métodos para criar os formulários dinâmicos ---

    def _criar_campo_multilinha(self, label_texto, altura=80, com_botao_colar=True):
        """Helper para criar um par (Label, QTextEdit) com botão de colar opcional."""
        label = QLabel(label_texto)
        
        if com_botao_colar:
            # Container para o campo + botão
            container = QWidget()
            container_layout = QGridLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            text_edit = QTextEdit()
            text_edit.setFixedHeight(altura)
            text_edit.setStyleSheet("padding-top: 5px; padding-right: 30px;")
            
            btn_colar = QPushButton("📋")
            btn_colar.setObjectName("PasteButton")
            btn_colar.setCursor(Qt.PointingHandCursor)
            btn_colar.setFixedSize(24, 24)
            btn_colar.setToolTip("Colar da área de transferência (Ctrl+V)")
            btn_colar.clicked.connect(text_edit.paste)
            
            container_layout.addWidget(text_edit, 0, 0)
            container_layout.addWidget(btn_colar, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            
            return label, container, text_edit
        else:
            text_edit = QTextEdit()
            text_edit.setFixedHeight(altura)
            return label, text_edit

    def _criar_campo_unilinha(self, label_texto, com_botao_colar=False):
        """Helper para criar um par (Label, QLineEdit) com botão de colar opcional."""
        label = QLabel(label_texto)
        
        if com_botao_colar:
            # Container para o campo + botão
            container = QWidget()
            container_layout = QGridLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            line_edit = QLineEdit()
            line_edit.setStyleSheet("padding-right: 30px;")
            
            btn_colar = QPushButton("📋")
            btn_colar.setObjectName("PasteButton")
            btn_colar.setCursor(Qt.PointingHandCursor)
            btn_colar.setFixedSize(24, 24)
            btn_colar.setToolTip("Colar da área de transferência (Ctrl+V)")
            btn_colar.clicked.connect(line_edit.paste)
            
            container_layout.addWidget(line_edit, 0, 0)
            container_layout.addWidget(btn_colar, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignCenter)
            
            return label, container, line_edit
        else:
            line_edit = QLineEdit()
            return label, line_edit

    def _criar_campo_usuario(self, label_texto="Usuário:"):
        """Helper para criar um dropdown de usuário."""
        label = QLabel(label_texto)
        combo_user = QComboBox()
        combo_user.addItems(self.USUARIOS_DISPONIVEIS)
        combo_user.setCurrentIndex(0)  # Seleciona o primeiro usuário por padrão
        return label, combo_user

    def _criar_form_cancelar_os(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        group_tipo = QGroupBox("Tipo")
        layout_tipo = QHBoxLayout(group_tipo)
        layout_tipo.addWidget(QRadioButton("Corretiva"))
        layout_tipo.addWidget(QRadioButton("PAF"))
        layout_tipo.addStretch(1)

        label_proto, proto_container, self.in_cancel_proto = self._criar_campo_multilinha("Protocolo:")
        label_obs, obs_container, self.in_cancel_obs = self._criar_campo_multilinha("Observação:")
        label_user, self.combo_cancel_user = self._criar_campo_usuario()

        layout.addWidget(group_tipo, 0, 0, 1, 2)
        layout.addWidget(label_proto, 1, 0)
        layout.addWidget(proto_container, 1, 1)
        layout.addWidget(label_obs, 2, 0)
        layout.addWidget(obs_container, 2, 1)
        layout.addWidget(label_user, 3, 0)
        layout.addWidget(self.combo_cancel_user, 3, 1)
        layout.setColumnStretch(1, 1)

        return widget

    def _criar_form_mover_os(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        label_mover, combo_mover = QLabel("Mover para:"), QComboBox()
        combo_mover.addItems(["Massiva", "Despacho"])

        label_proto, proto_container, self.in_move_proto = self._criar_campo_multilinha("Protocolo:")
        label_obs, obs_container, self.in_move_obs = self._criar_campo_multilinha("Observação:")
        label_user, self.combo_move_user = self._criar_campo_usuario()

        layout.addWidget(label_mover, 0, 0)
        layout.addWidget(combo_mover, 0, 1)
        layout.addWidget(label_proto, 1, 0)
        layout.addWidget(proto_container, 1, 1)
        layout.addWidget(label_obs, 2, 0)
        layout.addWidget(obs_container, 2, 1)
        layout.addWidget(label_user, 3, 0)
        layout.addWidget(self.combo_move_user, 3, 1)
        layout.setColumnStretch(1, 1)

        return widget

    def _criar_form_adicionar_obs(self):
        widget = QWidget()
        layout = QGridLayout(widget)

        label_proto, proto_container, self.in_obs_proto = self._criar_campo_multilinha("Protocolo:")
        label_obs, obs_container, self.in_obs_obs = self._criar_campo_multilinha("Observação:", 120)
        label_user, self.combo_obs_user = self._criar_campo_usuario()

        layout.addWidget(label_proto, 0, 0)
        layout.addWidget(proto_container, 0, 1)
        layout.addWidget(label_obs, 1, 0)
        layout.addWidget(obs_container, 1, 1)
        layout.addWidget(label_user, 2, 0)
        layout.addWidget(self.combo_obs_user, 2, 1)
        layout.setColumnStretch(1, 1)

        return widget

    def _criar_form_resgatar_os(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # NOVOS CAMPOS SOLICITADOS
        label_proto, proto_container, self.in_resg_proto = self._criar_campo_multilinha("Protocolo:")
        label_os_massiva, os_container, self.in_resg_os_massiva = self._criar_campo_unilinha("OS de Massiva:", com_botao_colar=True)
        label_nota, nota_container, self.in_resg_nota = self._criar_campo_multilinha("Nota:", altura=100)
        label_user, self.combo_resg_user = self._criar_campo_usuario()
        
        layout.addWidget(label_proto, 0, 0)
        layout.addWidget(proto_container, 0, 1)
        layout.addWidget(label_os_massiva, 1, 0)
        layout.addWidget(os_container, 1, 1)
        layout.addWidget(label_nota, 2, 0)
        layout.addWidget(nota_container, 2, 1)
        layout.addWidget(label_user, 3, 0)
        layout.addWidget(self.combo_resg_user, 3, 1)
        layout.setColumnStretch(1, 1)
        return widget

    def _criar_form_massiva_link(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grupo de busca por
        group_buscar = QGroupBox("Buscar por:")
        layout_buscar = QGridLayout(group_buscar)
        
        # Radio buttons para modo de pesquisa (REMOVIDO: Cidade)
        self.radio_massiva_protocolo = QRadioButton("Protocolo")
        self.radio_massiva_circuito = QRadioButton("Circuito")
        self.radio_massiva_cto = QRadioButton("CTO")
        self.radio_massiva_olt = QRadioButton("OLT")
        self.radio_massiva_pon = QRadioButton("PON")
        self.radio_massiva_localidade = QRadioButton("Localidade")
        self.radio_massiva_estacao = QRadioButton("Estação")
        self.radio_massiva_fila = QRadioButton("Fila")
        
        # Configurar primeiro como selecionado
        self.radio_massiva_protocolo.setChecked(True)
        
        # Layout dos radio buttons (reorganizado sem Cidade)
        layout_buscar.addWidget(self.radio_massiva_protocolo, 0, 0)
        layout_buscar.addWidget(self.radio_massiva_circuito, 0, 1)
        layout_buscar.addWidget(self.radio_massiva_cto, 0, 2)
        layout_buscar.addWidget(self.radio_massiva_olt, 1, 0)
        layout_buscar.addWidget(self.radio_massiva_pon, 1, 1)
        layout_buscar.addWidget(self.radio_massiva_localidade, 1, 2)
        layout_buscar.addWidget(self.radio_massiva_estacao, 2, 0)
        layout_buscar.addWidget(self.radio_massiva_fila, 2, 1)

        # NOVO: Container de inputs condicionais
        self.massiva_inputs_container = QStackedWidget()
        
        # Widget 1: Input padrão para maioria dos tipos
        input_padrao_widget = QWidget()
        input_padrao_layout = QVBoxLayout(input_padrao_widget)
        
        # Checkboxes condicionais
        self.checkbox_massiva_protocolo = QCheckBox("Adicionar dois zeros à esquerda")
        self.checkbox_massiva_protocolo.setVisible(False)
        self.checkbox_massiva_circuito = QCheckBox("Adicionar um zero à esquerda")
        self.checkbox_massiva_circuito.setVisible(False)
        
        label_input, input_container, self.in_mass_generico = self._criar_campo_multilinha("Valores:", com_botao_colar=True)
        
        input_padrao_layout.addWidget(self.checkbox_massiva_protocolo)
        input_padrao_layout.addWidget(self.checkbox_massiva_circuito)
        input_padrao_layout.addWidget(label_input)
        input_padrao_layout.addWidget(input_container)
        
        # Widget 2: Campos específicos para OLT
        olt_widget = self._criar_campos_olt_massiva()
        
        # Widget 3: Campos específicos para PON
        pon_widget = self._criar_campos_pon_massiva()
        
        # Widget 4: Dropdown para Localidade
        localidade_widget = QWidget()
        localidade_layout = QVBoxLayout(localidade_widget)
        label_localidade = QLabel("Localidade:")
        self.combo_massiva_localidade = QComboBox()
        self.combo_massiva_localidade.addItem("Selecione a Localidade")
        localidade_layout.addWidget(label_localidade)
        localidade_layout.addWidget(self.combo_massiva_localidade)
        localidade_layout.addStretch(1)
        
        # Widget 5: Dropdown para Fila
        fila_widget = QWidget()
        fila_layout = QVBoxLayout(fila_widget)
        label_fila = QLabel("Fila:")
        self.combo_massiva_fila = QComboBox()
        self.combo_massiva_fila.addItems(["Despacho", "Triagem", "Massiva"])
        fila_layout.addWidget(label_fila)
        fila_layout.addWidget(self.combo_massiva_fila)
        fila_layout.addStretch(1)

        # Adicionar widgets ao stack
        self.massiva_inputs_container.addWidget(input_padrao_widget)  # 0: Padrão
        self.massiva_inputs_container.addWidget(olt_widget)  # 1: OLT
        self.massiva_inputs_container.addWidget(pon_widget)  # 2: PON
        self.massiva_inputs_container.addWidget(localidade_widget)  # 3: Localidade
        self.massiva_inputs_container.addWidget(fila_widget)  # 4: Fila

        layout.addWidget(group_buscar)
        layout.addWidget(self.massiva_inputs_container, 1)
        
        # Conectar sinais para mudança de modo
        self.radio_massiva_protocolo.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_circuito.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_cto.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_olt.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_pon.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_localidade.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_estacao.toggled.connect(self._atualizar_campos_massiva)
        self.radio_massiva_fila.toggled.connect(self._atualizar_campos_massiva)
        
        return widget

    def _criar_form_massiva_input(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Coluna da Esquerda
        col_esq = QVBoxLayout()
        group_elem = QGroupBox("Elemento")
        layout_elem = QVBoxLayout(group_elem)
        opcoes_elem = ["CTO", "OLT", "NOME GERENCIA OLT", "IP OLT", "ESTAÇÃO", "CIDADE"]
        for op in opcoes_elem: 
            layout_elem.addWidget(QRadioButton(op))
        label_lista_elem, elem_container, self.in_mass_in_lista_elem = self._criar_campo_multilinha("Lista de Elementos:")
        col_esq.addWidget(group_elem)
        col_esq.addWidget(label_lista_elem)
        col_esq.addWidget(elem_container)

        # Coluna da Direita
        col_dir = QVBoxLayout()
        group_param = QGroupBox("Parâmetro de Pesquisa")
        layout_param = QVBoxLayout(group_param)
        layout_param.addWidget(QRadioButton("Circuito"))
        layout_param.addWidget(QRadioButton("Protocolo"))
        label_lista_param, param_container, self.in_mass_in_lista_param = self._criar_campo_multilinha("Lista de Parâmetros:")
        col_dir.addWidget(group_param)
        col_dir.addWidget(label_lista_param)
        col_dir.addWidget(param_container)

        layout.addLayout(col_esq, 1)
        layout.addLayout(col_dir, 1)
        return widget

    def _criar_campos_olt_massiva(self):
        """Cria campos específicos para busca por OLT na ação Massiva (Link)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de radio buttons para tipo de OLT
        grupo_tipo_olt = QGroupBox("Tipo de Informação OLT")
        layout_tipo_olt = QVBoxLayout(grupo_tipo_olt)
        
        self.radio_massiva_nome_olt = QRadioButton("Nome OLT")
        self.radio_massiva_nome_olt.setChecked(True)
        self.radio_massiva_nome_gerencia = QRadioButton("Nome Gerência")
        self.radio_massiva_ip_olt = QRadioButton("IP da OLT")
        self.radio_massiva_vlan_outer = QRadioButton("VLAN Outer")
        
        layout_tipo_olt.addWidget(self.radio_massiva_nome_olt)
        layout_tipo_olt.addWidget(self.radio_massiva_nome_gerencia)
        layout_tipo_olt.addWidget(self.radio_massiva_ip_olt)
        layout_tipo_olt.addWidget(self.radio_massiva_vlan_outer)
        
        # Campo de input dinâmico
        self.label_olt_dinamico = QLabel("Nome OLT:")
        self.input_olt_massiva = QLineEdit()
        self.input_olt_massiva.setPlaceholderText("Digite o nome da OLT")
        
        # Conectar mudança de tipo para atualizar label e placeholder
        self.radio_massiva_nome_olt.toggled.connect(lambda checked: self._atualizar_campo_olt_dinamico("Nome OLT:", "Digite o nome da OLT") if checked else None)
        self.radio_massiva_nome_gerencia.toggled.connect(lambda checked: self._atualizar_campo_olt_dinamico("Nome Gerência:", "Digite o nome da gerência") if checked else None)
        self.radio_massiva_ip_olt.toggled.connect(lambda checked: self._atualizar_campo_olt_dinamico("IP da OLT:", "Digite o IP da OLT") if checked else None)
        self.radio_massiva_vlan_outer.toggled.connect(lambda checked: self._atualizar_campo_olt_dinamico("VLAN Outer:", "Digite a VLAN Outer") if checked else None)
        
        layout.addWidget(grupo_tipo_olt)
        layout.addWidget(self.label_olt_dinamico)
        layout.addWidget(self.input_olt_massiva)
        layout.addStretch(1)
        
        return widget

    def _criar_campos_pon_massiva(self):
        """Cria campos específicos para busca por PON na ação Massiva (Link)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de radio buttons para formato de entrada
        grupo_formato = QGroupBox("Formato de Entrada")
        layout_formato = QVBoxLayout(grupo_formato)
        
        self.radio_massiva_pon_separados = QRadioButton("OLT + PON separados")
        self.radio_massiva_pon_separados.setChecked(True)
        self.radio_massiva_pon_juntos = QRadioButton("Juntos (OLT[shelf/slot/porta])")
        
        layout_formato.addWidget(self.radio_massiva_pon_separados)
        layout_formato.addWidget(self.radio_massiva_pon_juntos)
        
        layout.addWidget(grupo_formato)
        layout.addStretch(1)
        
        return widget

    def _atualizar_campo_olt_dinamico(self, label_text, placeholder):
        """Atualiza o label e placeholder do campo OLT dinâmico."""
        self.label_olt_dinamico.setText(label_text)
        self.input_olt_massiva.setPlaceholderText(placeholder)

    def _atualizar_campos_massiva(self):
        """Atualiza os campos exibidos baseado no tipo de busca selecionado na Massiva (Link)."""
        # Ocultar todos os checkboxes primeiro
        self.checkbox_massiva_protocolo.setVisible(False)
        self.checkbox_massiva_circuito.setVisible(False)
        
        # Determinar qual widget mostrar
        if self.radio_massiva_protocolo.isChecked():
            self.massiva_inputs_container.setCurrentIndex(0)  # Input padrão
            self.checkbox_massiva_protocolo.setVisible(True)
        elif self.radio_massiva_circuito.isChecked():
            self.massiva_inputs_container.setCurrentIndex(0)  # Input padrão
            self.checkbox_massiva_circuito.setVisible(True)
        elif self.radio_massiva_olt.isChecked():
            self.massiva_inputs_container.setCurrentIndex(1)  # Campos OLT
        elif self.radio_massiva_pon.isChecked():
            self.massiva_inputs_container.setCurrentIndex(2)  # Campos PON
        elif self.radio_massiva_localidade.isChecked():
            self.massiva_inputs_container.setCurrentIndex(3)  # Dropdown localidade
        elif self.radio_massiva_fila.isChecked():
            self.massiva_inputs_container.setCurrentIndex(4)  # Dropdown fila
        else:
            # CTO, Estação, Cidade - campos padrão
            self.massiva_inputs_container.setCurrentIndex(0)  # Input padrão

    def _conectar_sinais(self):
        # CRÍTICO: Conectar lista lateral ao stacked widget
        self.lista_acoes.currentRowChanged.connect(self._on_acao_changed)
        self.resultados_widget.status_message_requested.connect(self.status_message_requested)
    
    def _on_acao_changed(self, index):
        """CRÍTICO: Atualiza formulário e botão baseado na ação selecionada."""
        if index >= 0:
            # Trocar formulário ativo
            self.stacked_forms.setCurrentIndex(index)
            
            # Atualizar texto do botão
            acoes = ["Cancelar OS", "Mover OS", "Adicionar Obs", "Resgatar OS", "Massiva (Link)", "Massiva (Input)"]
            if index < len(acoes):
                self.btn_executar_acao.setText(f"Executar: {acoes[index]}")
                self.status_message_requested.emit(f"Ação selecionada: {acoes[index]}")
