import flet as ft
import base64
from datetime import datetime, timedelta
from fpdf import FPDF
from num2words import num2words

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def formata_brl(valor):
    """Transforma 8000.0 em 8.000,00"""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# SISTEMA PRINCIPAL (WEB)
# ==========================================
def main(page: ft.Page):
    page.window_width = 380
    page.window_height = 760
    page.title = "Gerador de Empréstimos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    # Variável invisível para guardar o PDF gerado na memória do navegador
    pdf_base64_atual = ft.Text(visible=False)

    # ==========================================
    # TELA 1: CONFIGURAÇÃO INICIAL (DADOS DA LOJA)
    # ==========================================
    config_titulo = ft.Text("Configuração da Loja", size=24, weight=ft.FontWeight.BOLD)
    config_aviso = ft.Text("Estes dados sairão impressos em todas as Notas Promissórias como o Credor.")
    
    loja_nome_input = ft.TextField(label="Nome do Credor ou Loja", value="Cadastrar seu nome completo")
    loja_cidade_input = ft.TextField(label="Praça de Pagamento (Cidade - Estado)", value="Cidade e Estado")
    
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

    # --- FUNÇÃO WEB: ABRIR O PDF NO NAVEGADOR ---
    def abrir_pdf_web(e):
        if pdf_base64_atual.value:
            # O '_self' força a abertura no mesmo separador, contornando o bloqueio de popups dos telemóveis
            page.launch_url(f"data:application/pdf;base64,{pdf_base64_atual.value}", web_window_name="_self")

    btn_abrir_pdf = ft.ElevatedButton(
        text="Abrir PDF (Imprimir / Baixar)", 
        on_click=abrir_pdf_web, 
        icon=ft.icons.PICTURE_AS_PDF, 
        visible=False, 
        expand=True, 
        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
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

            resumo = (
                f"Cliente: {nome}\n"
                f"Total a Receber: R$ {formata_brl(valor_total)}\n"
                f"{'-'*30}\n"
                f"CRONOGRAMA DE PAGAMENTO:\n"
            )

            nome_credor = page.client_storage.get("nome_credor")
            cidade_credor = page.client_storage.get("cidade_credor")

            # --- GERAÇÃO DO PDF NA MEMÓRIA ---
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False) 
            
            meses = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            hoje = datetime.now()
            texto_emissao = f"{cidade_credor}, {hoje.day:02d} de {meses[hoje.month]} de {hoje.year}."

            for i in range(qtd_parcelas):
                vencimento = data_base + timedelta(days=30 * i)
                data_formatada = vencimento.strftime('%d/%m/%Y')
                valor_extenso = num2words(valor_parcela, lang='pt_BR', to='currency')
                
                resumo += f"Parcela {i+1}/{qtd_parcelas} - R$ {formata_brl(valor_parcela)} - Venc: {data_formatada}\n"

                pdf.add_page()
                pdf.set_draw_color(180, 180, 180)
                pdf.set_xy(10, 148)
                pdf.set_font("Arial", 'I', 8)
                pdf.cell(0, 5, "- - - - - - - - - - - - - - - - - - - - - - - - - CORTAR AQUI - - - - - - - - - - - - - - - - - - - - - - - - -", ln=True, align="C")

                vias = [
                    {"y": 20, "titulo": "VIA DO CREDOR (Manter assinada em posse da loja)"},
                    {"y": 160, "titulo": "VIA DO CLIENTE (Entregar como comprovante)"}
                ]

                for via in vias:
                    y_start = via["y"]
                    pdf.set_draw_color(0, 0, 0)
                    pdf.rect(15, y_start, 180, 120)

                    pdf.set_y(y_start + 4)
                    pdf.set_font("Arial", 'B', 16)
