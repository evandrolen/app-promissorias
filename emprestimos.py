import flet as ft

import os

import time

import mimetypes

from datetime import datetime, timedelta

from fpdf import FPDF

from num2words import num2words



# ==========================================

# O "PULO DO GATO" PARA O IPHONE:

# Obriga o servidor a tratar o ficheiro estritamente como PDF oficial

# ==========================================

mimetypes.add_type('application/pdf', '.pdf')



# ==========================================

# FUNÇÕES DE APOIO

# ==========================================

def formata_brl(valor):

    """Transforma 8000.0 em 8.000,00"""

    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")



# Cria a pasta de ficheiros públicos para a web (necessário para o iPhone abrir)

pasta_assets = os.path.join(os.getcwd(), "assets")

os.makedirs(pasta_assets, exist_ok=True)



# ==========================================

# SISTEMA PRINCIPAL (WEB)

# ==========================================

def main(page: ft.Page):

    page.window_width = 380

    page.window_height = 760

    page.title = "Gerador de Empréstimos"

    page.theme_mode = ft.ThemeMode.LIGHT

    page.scroll = ft.ScrollMode.AUTO



    # ==========================================

    # TELA 1: CONFIGURAÇÃO INICIAL

    # ==========================================

    config_titulo = ft.Text("Configuração da Loja", size=24, weight=ft.FontWeight.BOLD)

    config_aviso = ft.Text("Estes dados sairão impressos em todas as Notas Promissórias como o Credor.")

    

    loja_nome_input = ft.TextField(label="Nome do Credor ou Loja", value="Dr. Evandro Lencione")

    loja_cidade_input = ft.TextField(label="Praça de Pagamento (Cidade - Estado)", value="Santa Rita do Passa Quatro - SP")

    

    def salvar_configuracao(e):

        if loja_nome_input.value and loja_cidade_input.value:

            page.client_storage.set("nome_credor", loja_nome_input.value)

            page.client_storage.set("cidade_credor", loja_cidade_input.value)

            abrir_tela_principal()

        else:

            config_aviso.value = "Preencha todos os campos para continuar."

            config_aviso.color = ft.colors.RED

            page.update()



    btn_salvar_config = ft.ElevatedButton(

        text="Salvar e Continuar", 

        on_click=salvar_configuracao,

        expand=True,

        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)

    )



    tela_configuracao = ft.Column([

        config_titulo, config_aviso, loja_nome_input, loja_cidade_input, ft.Row([btn_salvar_config])

    ], visible=False)



    # ==========================================

    # TELA 2: GERADOR DE EMPRÉSTIMOS PRINCIPAL

    # ==========================================

    def abrir_tela_configuracao(e=None):

        tela_principal.visible = False

        tela_configuracao.visible = True

        page.update()



    titulo_linha = ft.Row(

        [

            ft.Text("Novo Empréstimo", size=24, weight=ft.FontWeight.BOLD),

            ft.IconButton(icon=ft.icons.SETTINGS, on_click=abrir_tela_configuracao, tooltip="Configurar Loja")

        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN

    )



    nome_input = ft.TextField(label="Nome do Cliente", autofocus=True)

    cpf_input = ft.TextField(label="CPF", keyboard_type=ft.KeyboardType.NUMBER)

    

    rua_input = ft.TextField(label="Rua/Av", expand=True)

    numero_input = ft.TextField(label="Nº", width=80)

    linha_end1 = ft.Row([rua_input, numero_input])

    

    bairro_input = ft.TextField(label="Bairro", expand=True)

    cep_input = ft.TextField(label="CEP", width=120 
