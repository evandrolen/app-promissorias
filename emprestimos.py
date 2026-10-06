import flet as ft
from datetime import datetime, timedelta
from fpdf import FPDF
from num2words import num2words
import os
import asyncio
if not os.path.exists("assets"):
    os.makedirs("assets")

def converter_valor_brl(texto):
    """Converte textos como 5000, 5.000,00 ou R$ 5.000,00 para float."""
    if texto is None:
        raise ValueError("Informe o valor emprestado.")
    texto = str(texto).strip().replace("R$", "").replace(" ", "")
    if not texto:
        raise ValueError("Informe o valor emprestado.")
    texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def formatar_valor_brl(valor):
    """Formata número no padrão brasileiro: 1234.5 -> 1.234,50."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def main(page: ft.Page):
    page.title = "Juan Imports"
    page.window.width = 380
    page.window.height = 740
    page.title = "Gerador de Empréstimos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    # Mantemos os dados do credor em memória durante a sessão.
    # Isso evita travamentos do client_storage em navegadores móveis.
    config_atual = {
        "nome_credor": "",
        "cidade_credor": "",
    }

    # FilePicker mantido vivo durante toda a sessão.
    file_picker = ft.FilePicker()

    # ==========================================
    # TELA 1: CONFIGURAÇÃO INICIAL (DADOS DA LOJA)
    # ==========================================
    config_titulo = ft.Text("Configuração da Loja", size=24, weight=ft.FontWeight.BOLD)
    config_aviso = ft.Text("Estes dados sairão impressos em todas as Notas Promissórias como o Credor.")
    
    loja_nome_input = ft.TextField(label="Nome do Credor ou Loja", value=config_atual["nome_credor"])
    loja_cidade_input = ft.TextField(label="Praça de Pagamento (Cidade - Estado)", value=config_atual["cidade_credor"])
    
    def salvar_configuracao(e):
        if loja_nome_input.value and loja_cidade_input.value:
            config_atual["nome_credor"] = loja_nome_input.value.strip()
            config_atual["cidade_credor"] = loja_cidade_input.value.strip()
            abrir_tela_principal()
        else:
            config_aviso.value = "Preencha todos os campos para continuar."
            config_aviso.color = ft.Colors.RED
            page.update()

    btn_salvar_config = ft.Button(
        content="Salvar e Continuar", 
        on_click=salvar_configuracao,
        expand=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
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
            ft.IconButton(icon=ft.Icons.SETTINGS, on_click=abrir_tela_configuracao, tooltip="Configurar Loja")
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
    
    cidade_cliente_input = ft.TextField(label="Cidade - Estado", value="")

    def formatar_campo_valor(e):
        try:
            if valor_input.value and valor_input.value.strip():
                valor = converter_valor_brl(valor_input.value)
                valor_input.value = formatar_valor_brl(valor)
                page.update()
        except ValueError:
            # A validação completa continua sendo feita ao gerar o PDF.
            pass

    valor_input = ft.TextField(
        label="Valor Emprestado (R$)",
        keyboard_type=ft.KeyboardType.NUMBER,
        on_blur=formatar_campo_valor,
    )
    juros_input = ft.TextField(label="Juros Total do Período (%)", keyboard_type=ft.KeyboardType.NUMBER)
    parcelas_input = ft.TextField(label="Quantidade de Parcelas", keyboard_type=ft.KeyboardType.NUMBER)
    data_input = ft.TextField(label="Vencimento 1ª Parcela (DD/MM/AAAA)", keyboard_type=ft.KeyboardType.NUMBER)
    
    resultado_texto = ft.Text(size=15, weight=ft.FontWeight.W_500)

    # Mensagem de status fica antes dos botões para ser visível no iPhone.
    status_geracao = ft.Text(
        value="",
        size=14,
        weight=ft.FontWeight.W_500,
        visible=False,
    )

    async def simular_emprestimo(e):
        try:
            # Dá retorno visual imediato. No celular o resultado ficava abaixo da tela
            # e parecia que o botão não fazia nada.
            btn_gerar.disabled = True
            btn_gerar.content = "Gerando PDF..."
            status_geracao.value = "Gerando as promissórias, aguarde..."
            status_geracao.color = ft.Colors.BLUE_700
            status_geracao.visible = True
            page.update()
            await asyncio.sleep(0.05)

            nome = nome_input.value.strip()
            cpf = cpf_input.value.strip()

            if not nome:
                raise ValueError("Informe o nome do cliente.")
            if not cpf:
                raise ValueError("Informe o CPF do cliente.")

            endereco_completo = f"{rua_input.value}, {numero_input.value}, {bairro_input.value}, {cidade_cliente_input.value}, {cep_input.value}"
            
            valor = converter_valor_brl(valor_input.value)
            valor_input.value = formatar_valor_brl(valor)
            
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
                f"Total a Receber: R$ {formatar_valor_brl(valor_total)}\n"
                f"{'-'*30}\n"
                f"CRONOGRAMA DE PAGAMENTO:\n"
            )

            nome_credor = config_atual["nome_credor"]
            cidade_credor = config_atual["cidade_credor"]

            # --- GERAÇÃO DO  ---
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False) 
            
            meses = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            hoje = datetime.now()
            texto_emissao = f"{cidade_credor}, {hoje.day:02d} de {meses[hoje.month]} de {hoje.year}."

            for i in range(qtd_parcelas):
                vencimento = data_base + timedelta(days=30 * i)
                data_formatada = vencimento.strftime('%d/%m/%Y')
                valor_extenso = num2words(valor_parcela, lang='pt_BR', to='currency')
                
                resumo += f"Parcela {i+1}/{qtd_parcelas} - R$ {formatar_valor_brl(valor_parcela)} - Venc: {data_formatada}\n"

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
                    pdf.cell(0, 8, "NOTA PROMISSÓRIA", ln=True, align="C")
                    
                    pdf.set_y(y_start + 11)
                    pdf.set_font("Arial", 'I', 9)
                    pdf.cell(0, 5, via["titulo"], ln=True, align="C")
                    
                    pdf.set_y(y_start + 16)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 5, "="*60, ln=True, align="C")

                    pdf.set_y(y_start + 23)
                    pdf.set_x(20)
                    pdf.cell(90, 6, f"Nº da Parcela: {i+1:02d}/{qtd_parcelas:02d}")
                    pdf.cell(70, 6, f"Valor: R$ {formatar_valor_brl(valor_parcela)}", align="R", ln=True)
                    
                    pdf.set_x(20)
                    pdf.cell(0, 6, f"Data de Vencimento: {data_formatada}", ln=True)
                    
                    pdf.set_y(y_start + 38)
                    pdf.set_x(20)
                    pdf.set_font("Arial", '', 12)
                    
                    texto_promissoria = (
                        f"Aos {vencimento.strftime('%d')} dias do mês de {meses[vencimento.month]} de {vencimento.strftime('%Y')}, "
                        f"pagarei por esta única via de NOTA PROMISSÓRIA a {nome_credor}, ou à "
                        f"sua ordem, a quantia de R$ {formatar_valor_brl(valor_parcela)} ({valor_extenso}), em moeda corrente deste país."
                    )
                    pdf.multi_cell(170, 6, texto_promissoria, align="J")
                    
                    pdf.set_y(y_start + 63)
                    pdf.set_x(20)
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 6, f"Praça de Pagamento: {cidade_credor}", ln=True)
                    
                    pdf.set_y(y_start + 76)
                    pdf.set_x(20)
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(0, 5, "DADOS DO EMITENTE (Devedor)", ln=True)
                    
                    pdf.set_font("Arial", '', 10)
                    pdf.set_x(20)
                    pdf.cell(0, 5, f"Nome: {nome}        CPF: {cpf}", ln=True)
                    pdf.set_x(20)
                    pdf.multi_cell(170, 5, f"Endereço: {endereco_completo}")
                    
                    pdf.ln(2)
                    pdf.set_x(20)
                    pdf.cell(170, 5, texto_emissao, ln=True, align="R")
                    
                    pdf.set_y(y_start + 105)
                    pdf.set_x(20)
                    pdf.cell(170, 6, "_______________________________________________________________", ln=True, align="C")
                    pdf.set_x(20)
                    pdf.cell(170, 6, "Assinatura do Emitente", ln=True, align="C")

            # --- GERA O ARQUIVO E ENTREGA DIRETAMENTE AO IPHONE / NAVEGADOR ---
            if not os.path.exists("assets"):
                os.makedirs("assets")

            nome_seguro = "_".join(nome.split()) or "cliente"
            nome_arquivo = f"Promissorias_{nome_seguro}.pdf"
            caminho_arquivo = os.path.join("assets", nome_arquivo)
            pdf.output(caminho_arquivo)

            with open(caminho_arquivo, "rb") as arquivo_pdf:
                pdf_bytes = arquivo_pdf.read()

            status_geracao.value = "PDF pronto. Abrindo o download..."
            status_geracao.color = ft.Colors.GREEN_700
            page.update()
            await asyncio.sleep(0.05)

            # Em Web/iPhone, src_bytes envia o arquivo para o navegador,
            # sem depender de URL em assets ou de nova aba.
            await file_picker.save_file(
                file_name=nome_arquivo,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
                src_bytes=pdf_bytes,
            )

            status_geracao.value = "PDF gerado. Se o Safari solicitar confirmação, escolha Baixar."
            status_geracao.color = ft.Colors.GREEN_700
            resultado_texto.value = resumo
            resultado_texto.color = ft.Colors.BLUE_GREY_900

        except Exception as erro:
            status_geracao.value = f"Não foi possível gerar o PDF: {erro}"
            status_geracao.color = ft.Colors.RED
            status_geracao.visible = True
            resultado_texto.value = ""

        finally:
            btn_gerar.disabled = False
            btn_gerar.content = "Gerar Carnê e PDF"
            page.update()

    def limpar_campos(e):
        nome_input.value = ""
        cpf_input.value = ""
        rua_input.value = ""
        numero_input.value = ""
        bairro_input.value = ""
        cep_input.value = ""
        valor_input.value = ""
        juros_input.value = ""
        parcelas_input.value = ""
        data_input.value = ""
        resultado_texto.value = ""
        status_geracao.value = ""
        status_geracao.visible = False
        page.update()

    btn_gerar = ft.Button(
        content="Gerar Carnê e PDF", on_click=simular_emprestimo, expand=True,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
    )
    btn_limpar = ft.Button(
        content="Limpar", on_click=limpar_campos, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK)
    )

    tela_principal = ft.Column([
        titulo_linha,
        nome_input, cpf_input,
        linha_end1, linha_end2, cidade_cliente_input,
        ft.Divider(),
        valor_input, juros_input, parcelas_input, data_input,
        status_geracao,
        ft.Row([btn_gerar, btn_limpar]),
        ft.Divider(),
        resultado_texto
    ], visible=False)

    def abrir_tela_principal():
        tela_configuracao.visible = False
        tela_principal.visible = True
        page.update()

    page.add(tela_configuracao, tela_principal)

    # Abre direto a tela principal usando os valores padrão.
    # O ícone de engrenagem continua permitindo editar os dados do credor.
    abrir_tela_principal()

# Executa o aplicativo diretamente no navegador
ft.run(main, view=ft.AppView.WEB_BROWSER, assets_dir="assets")
