# -*- coding: utf-8 -*-
"""
ACI Frontend - Ponto de Entrada Modularizado
Versão modularizada da aplicação ACI Frontend
Autor: Progpy
Data: 29/09/2025
Versão: 2.7.1

Este é o novo ponto de entrada da aplicação modularizada.
Execute este arquivo para iniciar a aplicação com a nova estrutura.
"""

import sys
from PySide6.QtWidgets import QApplication

from aci_frontend.core.main_window import AciMainWindow

def main():
    """Função principal da aplicação."""
    try:
        # Criar a aplicação Qt
        app = QApplication(sys.argv)
        
        # Configurar propriedades da aplicação
        app.setApplicationName("ACI Frontend")
        app.setApplicationVersion("2.7.1")
        app.setOrganizationName("Progpy")
        
        # Criar e exibir a janela principal
        window = AciMainWindow()
        window.show()
        
        # Executar o loop de eventos da aplicação
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Erro ao inicializar a aplicação: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
