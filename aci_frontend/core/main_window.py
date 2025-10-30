# -*- coding: utf-8 -*-
"""
ACI Frontend - Janela Principal
Janela principal modularizada da aplicação ACI
"""

import sys
from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PySide6.QtCore import QTimer

from ..ui.styles.styler import Styler
from ..ui.tabs.aba_consulta import AbaConsulta
from ..ui.tabs.aba_acoes import AbaAcoes
from ..ui.tabs.aba_batimento import AbaBatimento

class AciMainWindow(QMainWindow):
    """Janela principal modularizada do aplicativo ACI."""

    def __init__(self):
        super().__init__()
        self._configurar_janela()
        self._criar_interface()
        self._aplicar_estilos()
        self._conectar_sinais_globais()

    def _configurar_janela(self):
        """Configura as propriedades básicas da janela."""
        self.setWindowTitle("ACI Frontend - Versão Modularizada")
        self.setGeometry(100, 100, 1280, 800)
        
        # Configurar barra de status
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Aplicação inicializada com sucesso.", 3000)

    def _criar_interface(self):
        """Cria a interface principal com as abas."""
        # Widget central com abas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Criar instâncias das abas
        self.tab_consultar = AbaConsulta()
        self.tab_batimento = AbaBatimento()
        self.tab_acoes = AbaAcoes()

        # Adicionar abas ao widget de abas
        self.tabs.addTab(self.tab_consultar, "Consultar Informações")
        self.tabs.addTab(self.tab_batimento, "Batimento")
        self.tabs.addTab(self.tab_acoes, "Ações")

    def _aplicar_estilos(self):
        """Aplica o tema visual da aplicação."""
        self.setStyleSheet(Styler.get_stylesheet())

    def _conectar_sinais_globais(self):
        """Conecta sinais das abas à janela principal (ex: para a status bar)."""
        # Conectar sinais de status das abas
        self.tab_consultar.status_message_requested.connect(self.show_status_message)
        self.tab_batimento.status_message_requested.connect(self.show_status_message)
        self.tab_acoes.status_message_requested.connect(self.show_status_message)
        
        # Conectar mudança de aba para atualizar status
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def show_status_message(self, message: str, timeout: int = 4000):
        """
        Exibe uma mensagem na barra de status.
        
        Args:
            message: Mensagem a ser exibida
            timeout: Tempo em milissegundos para a mensagem desaparecer
        """
        self.statusBar().showMessage(message, timeout)

    def _on_tab_changed(self, index: int):
        """
        Chamado quando o usuário muda de aba.
        
        Args:
            index: Índice da nova aba ativa
        """
        tab_names = ["Consultar Informações", "Batimento", "Ações"]
        if 0 <= index < len(tab_names):
            self.show_status_message(f"Aba '{tab_names[index]}' ativa.", 2000)

    def get_current_tab(self):
        """Retorna a aba atualmente ativa."""
        current_widget = self.tabs.currentWidget()
        if current_widget == self.tab_consultar:
            return "consultar"
        elif current_widget == self.tab_batimento:
            return "batimento"
        elif current_widget == self.tab_acoes:
            return "acoes"
        return None

    def switch_to_tab(self, tab_name: str):
        """
        Muda para uma aba específica.
        
        Args:
            tab_name: Nome da aba ('consultar', 'batimento', 'acoes')
        """
        tab_mapping = {
            "consultar": 0,
            "batimento": 1,
            "acoes": 2
        }
        
        if tab_name in tab_mapping:
            self.tabs.setCurrentIndex(tab_mapping[tab_name])
            self.show_status_message(f"Mudado para aba: {tab_name.title()}")

    def closeEvent(self, event):
        """Evento chamado quando a janela está sendo fechada."""
        self.show_status_message("Fechando aplicação...")
        
        # Aqui você pode adicionar lógica de limpeza se necessário
        # Por exemplo: salvar configurações, fechar conexões, etc.
        
        event.accept()  # Aceita o fechamento da janela
