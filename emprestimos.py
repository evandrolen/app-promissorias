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
    cep_input = ft.TextField(label="CEP", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    linha_end2 = ft.Row([bairro_input, cep_input])
    
    cidade_cliente_input = ft.TextField(label="Cidade - Estado", value="Santa Rita do Passa Quatro - SP")

    valor_input = ft.TextField(label="Valor Emprestado (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    juros_input = ft.TextField(label="Juros Total do Período (%)", keyboard_type=ft.KeyboardType.NUMBER)
    parcelas_input = ft.TextField(label="Quantidade de Parcelas", keyboard_type=ft.KeyboardType.NUMBER)
    data_input = ft.TextField(label="Vencimento 1ª Parcela (DD/MM/AAAA)", keyboard_type=ft.KeyboardType.NUMBER)
    
    resultado_texto = ft.Text(size=15, weight=ft.FontWeight.W_500)

    # --- BOTÃO PASSO 2: O LINK OFICIAL DO PDF ---
    btn_passo2_abrir = ft.ElevatedButton(
        text="2º PASSO: Abrir Documento PDF", 
        icon=ft.icons.PICTURE_AS_PDF, 
        visible=False, 
        expand=True, 
        url_target="_blank",
        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
    )

    # Dica invisível que só aparece com o Botão 2
    dica_iphone = ft.Text(
        "DICA IPHONE: O PDF abre no ecrã. Para Enviar (WhatsApp) ou Imprimir, toque no ecrã e use o botão 'Partilhar' (Quadrado com Seta) na barra inferior do Safari.", 
        size=12, color=ft.colors.GREY_600, italic=True, visible=False
    )

    def simular_emprestimo(e):
        try:
            nome = nome_input.value
            cpf = cpf_input.value
            endereco_completo = f"{rua_input.value}, {numero_input.value}, {bairro_input.value}, {cidade_cliente_input.value}, {cep_input.value}"
            
            valor_limpo = valor_input.value.replace('.', '').replace(',', '.')
            valor = float(valor_limpo)
            
            juros_limpo = juros_input.value.replace('.', '').replace(',', '.')
            juros = float(juros_limpo)
            
            qtd_parcelas = int(parcelas_input.value)
            
            data_str = data_input.value.replace('/', '').replace('-', '')
            if len(data_str) == 8:
                data_str = f"{data_str[:2]}/{data_str[2:4]}/{data_str[4:]}"
                data_input.value = data_str 
            
            data_base = datetime.strptime(data_str, "%d/%m/%Y")
            
            valor_juros = valor * (juros / 100)
            valor_total = valor + valor_juros
            valor_parcela = valor_total / qtd_parcelas
