# -*- coding: utf-8 -*-
"""
ACI Frontend - Sistema de Estilos
Centraliza cores, ícones e geração de folhas de estilo (QSS)
"""

class Styler:
    """
    Classe dedicada para gerenciar a aparência da aplicação.
    Centraliza cores, ícones e a geração da folha de estilos (QSS).
    """
    # Paleta de cores para fácil manutenção do tema.
    PALETTE = {
        "fundo": "#FFFFFF",
        "fundo_alternativo": "#F8F9FA",
        "fundo_hover_leve": "#E9ECEF",
        "texto_paragrafo": "#343A40",
        "texto_titulo": "#212529",
        "borda_divisor": "#DEE2E6",
        "borda_input": "#CED4DA",
        "primario": "#007BFF",
        "primario_hover": "#0069D9",
        "primario_pressionado": "#0056B3",
        "selecao_fundo": "#D4EDDA",
        "selecao_texto": "#155724",
        "selecao_borda": "#28A745",
    }

    # Símbolos Unicode para ícones (mais compatíveis que SVG Base64)
    ICONS = {
        "check_solid": "✓",  # Símbolo de check
        "chevron_down": "▼",  # Seta para baixo
        "paste": "📋"  # Ícone de clipboard/colar
    }

    @staticmethod
    def get_stylesheet() -> str:
        """Gera e retorna a folha de estilos completa para a aplicação."""
        p = Styler.PALETTE
        i = Styler.ICONS
        return f"""
            /* --- ESTILOS GERAIS --- */
            QWidget {{
                background-color: {p['fundo']};
                color: {p['texto_paragrafo']};
                font-family: Segoe UI;
                font-size: 10pt;
            }}

            QGroupBox {{
                border: 1px solid {p['borda_divisor']};
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
                color: {p['texto_titulo']};
                font-weight: bold;
                font-size: 11pt;
            }}

            QLabel#Title {{
                color: {p['texto_titulo']};
                font-size: 14pt;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
            }}

            /* --- INPUTS E CONTROLES --- */
            QLineEdit, QComboBox, QTextEdit {{
                border: 1px solid {p['borda_divisor']};
                padding: 8px;
                border-radius: 4px;
                background-color: {p['fundo']};
                selection-background-color: {p['primario']};
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 1px solid {p['primario']};
            }}
            QScrollArea#ScrollArea {{
                border: 1px solid {p['borda_divisor']};
                border-radius: 4px;
            }}

            /* --- BOTÕES --- */
            QPushButton#PrimaryButton {{
                background-color: {p['primario']};
                color: {p['fundo']};
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton#PrimaryButton:hover {{ background-color: {p['primario_hover']}; }}
            QPushButton#PrimaryButton:pressed {{ background-color: {p['primario_pressionado']}; }}

            QPushButton#ToolbarButton {{
                background-color: {p['fundo']};
                color: {p['primario']};
                border: 1px solid {p['primario']};
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton#ExportButton {{ /* Estilo específico para o botão de exportar com seta */
                padding: 5px 25px 5px 15px; /* Mais espaço à direita para a seta */
            }}
            QPushButton#ToolbarButton:hover, QPushButton#ExportButton:hover {{
                background-color: #E7F1FF;
                border-color: {p['primario_pressionado']};
            }}
            QPushButton[objectName*="Button"]::menu-indicator {{
                width: 12px;
                height: 12px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
                right: 5px;
            }}

            /* Botões secundários dentro de painéis */
            QGroupBox QPushButton {{
                background-color: {p['fundo_alternativo']};
                color: {p['texto_paragrafo']};
                border: 1px solid {p['borda_divisor']};
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: normal;
            }}
            QGroupBox QPushButton:hover {{
                background-color: {p['fundo_hover_leve']};
                border-color: #ADB5BD;
            }}
            QGroupBox QPushButton:pressed {{ background-color: {p['borda_divisor']}; }}

            QPushButton#PasteButton {{
                background-color: transparent;
                border: none;
                padding: 4px;
                border-radius: 12px;
                font-size: 12pt;
            }}
            QPushButton#PasteButton:hover {{
                background-color: {p['fundo_hover_leve']};
            }}

            /* --- CORREÇÃO CRÍTICA: DESTAQUE INEQUÍVOCO DA ABA SUPERIOR ATIVA --- */
            QTabWidget::pane {{
                border: 2px solid {p['primario']};
                border-radius: 0px 12px 12px 12px;
                padding: 20px;
                background-color: {p['fundo']};
                margin-top: 0px;
            }}
            
            /* Abas principais horizontais - BASE */
            QTabBar[tabPosition="0"]::tab {{
                background: {p['fundo_alternativo']};
                border: 2px solid {p['borda_divisor']};
                border-bottom: none;
                padding: 16px 32px;
                margin-right: 2px;
                border-radius: 12px 12px 0px 0px;
                font-weight: 500;
                color: {p['texto_paragrafo']};
                min-width: 140px;
                font-size: 11pt;
                position: relative;
            }}
            
            /* ABA ATIVA SUPERIOR - DESTAQUE MÁXIMO OBRIGATÓRIO */
            QTabBar[tabPosition="0"]::tab:selected {{
                background: {p['fundo']};
                color: {p['primario']};
                border: 2px solid {p['primario']};
                border-bottom: 2px solid {p['fundo']};
                font-weight: 800;
                font-size: 12pt;
                z-index: 10;
                margin-bottom: -2px;
                padding: 18px 36px;
            }}
            
            /* Hover nas abas inativas */
            QTabBar[tabPosition="0"]::tab:!selected:hover {{ 
                background: {p['fundo_hover_leve']};
                border-color: {p['primario_hover']};
                color: {p['primario_hover']};
                font-weight: 600;
            }}
            
            /* Barra de abas principais */
            QTabWidget > QTabBar {{
                background: transparent;
                border: none;
                outline: none;
            }}
            
            /* --- NAVEGAÇÃO VERTICAL COM LISTA LATERAL (SOLUÇÃO CRÍTICA) --- */
            /* GARANTIA ABSOLUTA: Texto sempre HORIZONTAL */
            QListWidget[objectName="lista_acoes"] {{
                background-color: {p['fundo_alternativo']};
                border: 1px solid {p['borda_divisor']};
                border-right: none;
                border-radius: 8px 0px 0px 8px;
                padding: 15px 5px;
                outline: none;
            }}
            
            /* Itens da lista lateral com texto HORIZONTAL garantido */
            QListWidget[objectName="lista_acoes"]::item {{
                background: {p['fundo_alternativo']};
                border: 1px solid {p['borda_divisor']};
                border-right: none;
                padding: 14px 16px;
                margin: 3px 4px 3px 8px;
                border-radius: 8px 0px 0px 8px;
                font-weight: 500;
                color: {p['texto_paragrafo']};
                text-align: left;
                min-height: 20px;
                font-family: 'Segoe UI';
                font-size: 10pt;
            }}
            
            /* Item ativo - conexão suave com painel OBRIGATÓRIA */
            QListWidget[objectName="lista_acoes"]::item:selected {{
                background: {p['fundo']};
                color: {p['primario']};
                font-weight: 700;
                border: 1px solid {p['borda_divisor']};
                border-right: none;
                border-left: 3px solid {p['primario']};
                margin-right: 0px;
                border-radius: 8px 0px 0px 8px;
            }}
            
            /* Hover nos itens inativos */
            QListWidget[objectName="lista_acoes"]::item:hover:!selected {{
                background: {p['fundo_hover_leve']};
                border: 1px solid {p['borda_input']};
                border-right: none;
                color: {p['primario_hover']};
            }}

            /* --- TABELA --- */
            QTableView {{
                border: 1px solid {p['borda_divisor']};
                gridline-color: {p['borda_divisor']};
                background-color: {p['fundo']};
                alternate-background-color: {p['fundo_alternativo']};
            }}
            QTableView::item:selected {{
                background-color: {p['selecao_fundo']};
                color: {p['selecao_texto']};
                border: 1px solid {p['selecao_borda']};
            }}
            QTableView::item:hover {{
                background-color: {p['selecao_fundo']};
                color: {p['selecao_texto']};
            }}
            QHeaderView::section {{
                background-color: {p['fundo_hover_leve']};
                padding: 8px;
                border: 1px solid {p['borda_divisor']};
                font-weight: bold;
                color: {p['texto_titulo']};
            }}
            QHeaderView::section:hover {{
                background-color: #DFE6EC;
            }}

            /* --- CHECKBOX & RADIO BUTTON --- */
            QRadioButton, QCheckBox {{ spacing: 8px; }}

            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {p['borda_input']};
                border-radius: 3px;
                background-color: {p['fundo']};
            }}
            QCheckBox::indicator:hover {{ border: 1px solid {p['primario']}; }}
            QCheckBox::indicator:checked {{
                background-color: {p['primario']};
                border: 1px solid {p['primario_pressionado']};
            }}

            QRadioButton::indicator {{
                width: 16px; height: 16px;
                border-radius: 9px;
                border: 2px solid {p['borda_input']};
                background-color: transparent;
            }}
            QRadioButton::indicator:hover {{ border-color: {p['primario_hover']}; }}
            QRadioButton::indicator:checked {{
                background-color: {p['primario']};
                border: 2px solid {p['primario']};
            }}

            /* --- OUTROS --- */
            QMenu {{
                background-color: {p['fundo']};
                border: 1px solid {p['borda_divisor']};
                border-radius: 6px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                background-color: transparent;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {p['fundo_hover_leve']};
                color: {p['texto_titulo']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {p['borda_divisor']};
                margin: 5px 10px;
            }}

            QStatusBar {{ font-size: 9pt; }}
        """
