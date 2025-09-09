import asyncio
import logging
import os
import random
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN não encontrado!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DONO_ID = 8206910765  # Seu ID para admin

# Dados reais (configs, users, estoque, afiliados, etc.)
configs = {
    "suporte_link": "https://t.me/suporte_default",
    "grupo_clientes": "https://t.me/grupo_default",
    "separador": "===",
    "log_destino": "@log_channel",
    "bonus_registro": 0.0,
    "deposito_min": 1.0,
    "deposito_max": 1000.0,
    "expiracao_pix": 15,
    "bonus_deposito": 0.0,
    "min_bonus": 0.0,
    "afiliados_on": True,
    "pontos_por_recarga": 10,
    "pontos_min_convert": 400,
    "multiplicador_convert": 0.01,
    "pesquisa_on": True,
    "pix_manual": False,
    "pix_auto": True,
    "mp_token": "default_token",
    "software_version": "1.0",
    "vencimento": "2025-12-31",
    "vip": "Ativo",
    "manutencao": False,
    "texts": {  # Textos editáveis
        "welcome": "🥇Descubra como nosso bot pode transformar sua experiência de compras! ...",
        # Adicione todos textos aqui para edição
    }
}
users = {}  # {user_id: {"saldo": 0.0, "compras": [], "recargas": [], "gifts": 0.0, "afiliados": 0, "pontos": 0, "indications": []}}
admins = [DONO_ID]  # Lista de admins
estoque = {}  # {"NETFLIX": {"preco": 10.0, "estoque": 5, "desc": "Descrição...", "logins": ["email:senha"]}}
pesquisa_imagens = []  # Links de imagens para pesquisa
alertas = {}  # {produto: [user_ids que querem alerta]}

class AdminStates(StatesGroup):
    alterar_suporte = State()
    alterar_separador = State()
    alterar_log = State()
    adicionar_admin = State()
    remover_admin = State()
    pontos_por_recarga = State()
    pontos_min_convert = State()
    multiplicador_convert = State()
    transmitir = State()
    pesquisar_user = State()
    bonus_registro = State()
    mudar_token = State()
    deposito_min = State()
    deposito_max = State()
    expiracao_pix = State()
    bonus_deposito = State()
    min_bonus = State()
    adicionar_login = State()
    remover_login = State()
    remover_plataforma = State()
    mudar_valor_serv = State()
    mudar_valor_todos = State()
    adicionar_imagem = State()
    remover_imagem = State()
    # Adicione mais states para outros fluxos

# Menu Inicial (Loja + Admin para dono)
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"saldo": configs["bonus_registro"], "compras": [], "recargas": [], "gifts": 0.0, "afiliados": 0, "pontos": 0, "indications": []}
    texto = configs["texts"]["welcome"].format(suporte_link=configs["suporte_link"], grupo_clientes=configs["grupo_clientes"], id=user_id, saldo=users[user_id]["saldo"], user=message.from_user.username)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💎 Logins | Contas Premium", callback_data="logins_premium")],
        [InlineKeyboardButton("🪪 PERFIL", callback_data="perfil"), InlineKeyboardButton("💰 RECARGA", callback_data="recarga")],
        [InlineKeyboardButton("🎖️ Ranking", callback_data="ranking")],
        [InlineKeyboardButton("👩‍💻 Suporte", url=configs["suporte_link"]), InlineKeyboardButton("ℹ️ Informações", callback_data="info")],
        [InlineKeyboardButton("🔎 Pesquisar Serviços", callback_data="pesquisar_servicos")]
    ])
    await message.answer_photo(photo="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSltpwF6kTey6ImHK0Z76OBq2AmdNgMsS7irFzm7Xv4Ji9whMxq-eD6PO2Y&s=10", caption=texto, reply_markup=markup)

    if user_id == DONO_ID:
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("⚔️ Menu Inicial /start", callback_data="start")],
            [InlineKeyboardButton("🗡️ Menu Administrativo /admin", callback_data="admin")]
        ])
        await message.answer("Menu Dono:", reply_markup=admin_markup)

# Menu Admin
@dp.callback_query(F.data == "admin")
async def admin_menu(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != DONO_ID and callback_query.from_user.id not in admins:
        await callback_query.answer("Acesso negado!")
        return
    texto = "⚙️ DASHBOARD @\n📅 Vencimento: {vencimento}\n👑 Vip: {vip}\n🤖 Software version: {version}\n\n📔 Métrica do business\n📊 User: {users}\n📈 Receita total: R$ {receita_total}\n🗓️ Receita mensal: R$ {receita_mensal}\n💠 Receita de hoje: R$ {receita_hoje}\n🥇 Vendas total: {vendas_total}\n🏆 Vendas hoje: {vendas_hoje}".format(
        vencimento=configs["vencimento"], vip=configs["vip"], version=configs["software_version"], users=len(users),
        receita_total=sum(sum(r['valor'] for r in u['recargas']) for u in users.values()),  # Calcula real
        receita_mensal=0, receita_hoje=0, vendas_total=sum(len(u['compras']) for u in users.values()), vendas_hoje=0  # Adicione lógica data
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔧 CONFIGURAÇÕES", callback_data="configs")],
        [InlineKeyboardButton("🔖 AÇÕES", callback_data="acoes")],
        [InlineKeyboardButton("🔄 TRANSAÇÕES", callback_data="transacoes")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="voltar")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Configurações Gerais
@dp.callback_query(F.data == "configs")
async def configs_menu(callback_query: CallbackQuery, state: FSMContext):
    texto = "🔧 MENU DE CONFIGURAÇÕES DO BOT\n👮 Admin: {admins}\n💼 Dono: {dono}".format(admins=admins, dono=DONO_ID)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚙️ CONFIGURAÇÕES GERAIS ⚙️", callback_data="configs_gerais")],
        [InlineKeyboardButton("🕵️‍♀️ CONFIGURAR ADMINS", callback_data="configs_admins")],
        [InlineKeyboardButton("👥 CONFIGURAR AFILIADOS", callback_data="configs_afiliados")],
        [InlineKeyboardButton("👤 CONFIGURAR USUARIOS", callback_data="configs_users")],
        [InlineKeyboardButton("💠 CONFIGURAR PIX", callback_data="configs_pix")],
        [InlineKeyboardButton("🖥️ CONFIGURAR LOGINS", callback_data="configs_logins")],
        [InlineKeyboardButton("🔎 CONFIGURAR PESQUISA DE LOGIN", callback_data="configs_pesquisa")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="admin")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Configs Gerais (exemplo, adicione mais)
@dp.callback_query(F.data == "configs_gerais")
async def configs_gerais(callback_query: CallbackQuery, state: FSMContext):
    texto = "📭 DESTINO DAS LOG'S: {log}\n👤 LINK DO SUPORTE ATUAL: {suporte}\n✂️ SEPARADOR: {sep}".format(log=configs["log_destino"], suporte=configs["suporte_link"], sep=configs["separador"])
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("♻️ RENOVAR PLANO", callback_data="renovar_plano")],
        [InlineKeyboardButton("🤖 REINICIAR BOT", callback_data="reiniciar_bot")],
        [InlineKeyboardButton(f"🔴 MANUTENÇÃO ({'on' if configs['manutencao'] else 'off'})", callback_data="toggle_manutencao")],
        [InlineKeyboardButton("🎧 MUDAR SUPORTE", callback_data="mudar_suporte")],
        [InlineKeyboardButton("✂️ MUDAR SEPARADOR", callback_data="mudar_separador")],
        [InlineKeyboardButton("📭 MUDAR DESTINO LOG", callback_data="mudar_log")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Fluxo Mudar Suporte (exemplo de state)
@dp.callback_query(F.data == "mudar_suporte")
async def mudar_suporte_prompt(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.alterar_suporte)
    await callback_query.message.answer("Envie o novo link de suporte:")
    await callback_query.answer()

@dp.message(AdminStates.alterar_suporte)
async def process_mudar_suporte(message: Message, state: FSMContext):
    configs["suporte_link"] = message.text
    await message.answer("Suporte atualizado para: " + message.text)
    await state.clear()

# Adicione similar para outros (separador, log, etc.)

# Configs Admins
@dp.callback_query(F.data == "configs_admins")
async def configs_admins(callback_query: CallbackQuery, state: FSMContext):
    texto = "🅰️ PAINEL CONFIGURAR ADMIN\n👮 Administradores: " + str(admins)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ ADICIONAR ADM", callback_data="add_admin")],
        [InlineKeyboardButton("🚮 REMOVER ADM", callback_data="rem_admin")],
        [InlineKeyboardButton("🗞️ LISTA DE ADM", callback_data="lista_admin")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

@dp.callback_query(F.data == "add_admin")
async def add_admin_prompt(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.adicionar_admin)
    await callback_query.message.answer("Envie o ID do novo admin:")
    await callback_query.answer()

@dp.message(AdminStates.adicionar_admin)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        admin_id = int(message.text)
        if admin_id not in admins:
            admins.append(admin_id)
            await message.answer("Admin adicionado: " + str(admin_id))
        else:
            await message.answer("Já é admin!")
    except ValueError:
        await message.answer("ID inválido!")
    await state.clear()

# Adicione rem_admin, lista_admin similar.

# Configs Afiliados
@dp.callback_query(F.data == "configs_afiliados")
async def configs_afiliados(callback_query: CallbackQuery, state: FSMContext):
    texto = "🔻 PONTOS MÍNIMO PARA SALDO: {min} ✖️ MULTIPLICADOR: {mult}".format(min=configs["pontos_min_convert"], mult=configs["multiplicador_convert"])
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🟢 SISTEMA DE INDICAÇÃO ({'on' if configs['afiliados_on'] else 'off'})", callback_data="toggle_afiliados")],
        [InlineKeyboardButton("🗞️ PONTOS POR RECARGA", callback_data="pontos_recarga")],
        [InlineKeyboardButton("🔻 PONTOS MINIMO PARA CONVERTER", callback_data="pontos_min_convert")],
        [InlineKeyboardButton("✖️ MULTIPLICADOR PARA CONVERTER", callback_data="multi_convert")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

@dp.callback_query(F.data == "toggle_afiliados")
async def toggle_afiliados(callback_query: CallbackQuery, state: FSMContext):
    configs["afiliados_on"] = not configs["afiliados_on"]
    await configs_afiliados(callback_query, state)  # Refresh menu

# Adicione states para mudar pontos, etc.

# Configs Users
@dp.callback_query(F.data == "configs_users")
async def configs_users(callback_query: CallbackQuery, state: FSMContext):
    texto = "Configs Users"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📭 TRANSMITIR A TODOS", callback_data="transmitir")],
        [InlineKeyboardButton("🔎 PESQUISAR USUARIO", callback_data="pesquisar_user")],
        [InlineKeyboardButton("🎁 BONUS DE REGISTRO", callback_data="bonus_reg")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Adicione fluxos similares.

# Configs Pix
@dp.callback_query(F.data == "configs_pix")
async def configs_pix(callback_query: CallbackQuery, state: FSMContext):
    texto = "Configs Pix"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🔴 PIX MANUAL ({'on' if configs['pix_manual'] else 'off'})", callback_data="toggle_pix_manual")],
        [InlineKeyboardButton(f"🟢 PIX AUTOMATICO ({'on' if configs['pix_auto'] else 'off'})", callback_data="toggle_pix_auto")],
        [InlineKeyboardButton("🔑 MUDAR TOKEN", callback_data="mudar_token")],
        [InlineKeyboardButton("🔻 MUDAR DEPOSITO MIN", callback_data="deposito_min")],
        [InlineKeyboardButton("❗️ MUDAR DEPOSITO MAX", callback_data="deposito_max")],
        [InlineKeyboardButton("⏰ MUDAR TEMPO DE EXPIRAÇÃO", callback_data="expiracao")],
        [InlineKeyboardButton("🔶 MUDAR BONUS", callback_data="bonus_deposito")],
        [InlineKeyboardButton("🔷 MUDAR MIN PARA BONUS", callback_data="min_bonus")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Adicione toggles e states.

# Configs Logins
@dp.callback_query(F.data == "configs_logins")
async def configs_logins(callback_query: CallbackQuery, state: FSMContext):
    texto = "📦 LOGINS NO ESTOQUE: {total}".format(total=sum(len(p['logins']) for p in estoque.values()))
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📮 ADICIONAR LOGIN", callback_data="add_login")],
        [InlineKeyboardButton("🥾 REMOVER LOGIN", callback_data="rem_login")],
        [InlineKeyboardButton("❌ REMOVER POR PLATAFORMA", callback_data="rem_plataforma")],
        [InlineKeyboardButton("📦 ESTOQUE DETALHADO", callback_data="estoque_detalhado")],
        [InlineKeyboardButton("🗑️ ZERAR ESTOQUE", callback_data="zerar_estoque")],
        [InlineKeyboardButton("💸 MUDAR VALOR DO SERVIÇO", callback_data="mudar_valor_serv")],
        [InlineKeyboardButton("🪪 MUDAR VALOR DE TODOS", callback_data="mudar_valor_todos")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

@dp.callback_query(F.data == "add_login")
async def add_login_prompt(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.adicionar_login)
    await callback_query.message.answer("Envie logins no formato: NOME{sep}VALOR{sep}DESC{sep}EMA/L{sep}SENHA{sep}DURACAO".format(sep=configs["separador"]))
    await callback_query.answer()

@dp.message(AdminStates.adicionar_login)
async def process_add_login(message: Message, state: FSMContext):
    lines = message.text.split('\n')
    for line in lines:
        if line.strip():
            parts = line.split(configs["separador"])
            if len(parts) == 6:
                nome, valor, desc, email, senha, duracao = parts
                if nome not in estoque:
                    estoque[nome] = {"preco": float(valor), "desc": desc, "logins": [], "estoque": 0}
                estoque[nome]["logins"].append(f"{email}:{senha}:{duracao}")
                estoque[nome]["estoque"] += 1
    await message.answer("Logins adicionados!")
    await state.clear()

# Adicione rem, zerar, etc. similar.

# Configs Pesquisa
@dp.callback_query(F.data == "configs_pesquisa")
async def configs_pesquisa(callback_query: CallbackQuery, state: FSMContext):
    texto = "🔎 PAINEL DE CONFIGURAÇÃO DA PESQUISA DE SERVIÇOS\n📸 IMAGENS SALVAS: {imgs}".format(imgs=len(pesquisa_imagens))
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🟢 SISTEMA PESQUISA ({'on' if configs['pesquisa_on'] else 'off'})", callback_data="toggle_pesquisa")],
        [InlineKeyboardButton("➕ ADICIONAR IMAGEM", callback_data="add_imagem")],
        [InlineKeyboardButton("🚮 REMOVER IMAGEM", callback_data="rem_imagem")],
        [InlineKeyboardButton("↩️ VOLTAR", callback_data="configs")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Adicione fluxos.

# Loja - Logins Premium
@dp.callback_query(F.data == "logins_premium")
async def logins_premium(callback_query: CallbackQuery, state: FSMContext):
    texto = "🎟️ Logins Premium | Acesso Exclusivo\n🏦 Carteira\n💸 Saldo Atual: R${saldo}".format(saldo=users[callback_query.from_user.id]["saldo"])
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for nome in estoque:
        markup.inline_keyboard.append([InlineKeyboardButton(nome, callback_data=f"prod_{nome}")])
    markup.inline_keyboard.append([InlineKeyboardButton("↩️ Voltar", callback_data="voltar")])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Detalhe Produto
@dp.callback_query(F.data.startswith("prod_"))
async def prod_detalhe(callback_query: CallbackQuery, state: FSMContext):
    nome = callback_query.data[5:]
    p = estoque[nome]
    user_id = callback_query.from_user.id
    texto = f"⚜️ACESSO: {nome}\n💵 Preço: R${p['preco']}\n💼 Saldo Atual: {users[user_id]['saldo']}\n📥 Estoque Disponível: {p['estoque']}\n🗒️ Descrição: {p['desc']}\n♻️ Garantia: 30"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛒 Comprar", callback_data=f"comprar_{nome}")],
        [InlineKeyboardButton("↩️ Voltar", callback_data="logins_premium")]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Comprar
@dp.callback_query(F.data.startswith("comprar_"))
async def comprar(callback_query: CallbackQuery, state: FSMContext):
    nome = callback_query.data[9:]
    p = estoque[nome]
    user_id = callback_query.from_user.id
    if users[user_id]["saldo"] >= p["preco"] and p["estoque"] > 0:
        users[user_id]["saldo"] -= p["preco"]
        users[user_id]["compras"].append({"prod": nome, "data": time.time()})
        login = p["logins"].pop(0)
        p["estoque"] -= 1
        await callback_query.message.edit_text("Compra realizada! Login: " + login)
    else:
        await callback_query.answer("Saldo insuficiente! Faltam R${diff}. Faça uma recarga.".format(diff=p["preco"] - users[user_id]["saldo"]))

# Adicione mais fluxos para perfil, recarga, ranking, etc. (similar, com cálculos reais).

# Ranking (exemplo serviços vendidos)
@dp.callback_query(F.data == "ranking")
async def ranking_menu(callback_query: CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛍️ Serviços", callback_data="rank_servicos")],
        [InlineKeyboardButton("💰 Recargas", callback_data="rank_recargas")],
        [InlineKeyboardButton("🛒 Compras", callback_data="rank_compras")],
        [InlineKeyboardButton("🎁 Gift Card", callback_data="rank_gifts")],
        [InlineKeyboardButton("💸 Saldo", callback_data="rank_saldo")],
        [InlineKeyboardButton("↩️ Voltar", callback_data="voltar")]
    ])
    await callback_query.message.edit_text("Ranking:", reply_markup=markup)
    await callback_query.answer()

@dp.callback_query(F.data == "rank_servicos")
async def rank_servicos(callback_query: CallbackQuery, state: FSMContext):
    # Calcula real: Conta compras por prod
    prod_counts = {}
    for u in users.values():
        for c in u["compras"]:
            prod_counts[c["prod"]] = prod_counts.get(c["prod"], 0) + 1
    sorted_prods = sorted(prod_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    texto = "🏆 Ranking dos serviços mais vendidos (deste mês)\n"
    for i, (prod, count) in enumerate(sorted_prods, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else ""
        texto += f"{i}°) {prod} {medal}Com {count} pedidos\n"
    await callback_query.message.edit_text(texto)
    await callback_query.answer()

# Adicione rank_recargas, compras, gifts, saldo similar (calcula de users).

# /pix Comando
@dp.message(F.text.startswith("/pix "))
async def pix_comando(message: Message):
    try:
        valor = float(message.text.split()[1])
        if configs["deposito_min"] <= valor <= configs["deposito_max"]:
            await generate_pix(message, valor)
        else:
            await message.reply("Valor fora do limite!")
    except:
        await message.reply("Formato incorreto. Ex: /pix 10")

# Generate Pix (similar ao anterior, com bonus se min_bonus)
async def generate_pix(message: Message, valor: float):
    # ... (lógica similar ao código anterior, adicione bonus se valor >= min_bonus)
    if valor >= configs["min_bonus"]:
        valor += configs["bonus_deposito"]
    users[message.from_user.id]["saldo"] += valor  # Adiciona após "pagamento"
    users[message.from_user.id]["recargas"].append({"valor": valor, "data": time.time()})
    # Para afiliados: Se user tem indicador, adicione pontos

# /historico
@dp.message(F.text == "/historico")
async def historico(message: Message):
    user_id = message.from_user.id
    texto = "HISTORICO DETALHADO\n@{bot.username}\n_______________________\nCOMPRAS:\n" + "\n".join(c["prod"] for c in users[user_id]["compras"]) + "\n_______________________\nPAGAMENTOS:\n" + "\n".join(str(r["valor"]) for r in users[user_id]["recargas"])
    await message.answer(texto)  # Simula TXT

# /afiliados
@dp.message(F.text == "/afiliados")
async def afiliados(message: Message):
    if not configs["afiliados_on"]:
        await message.answer("Sistema off!")
        return
    user_id = message.from_user.id
    link = f"https://t.me/{bot.username}?start=aff_{user_id}"
    texto = "ℹ️ Status: on\n📊 Comissão por Indicação: {comiss}\n👥 Total de Afiliados: {total}\n🔗 Link para Indicar: {link}".format(comiss=configs["multiplicador_convert"], total=users[user_id]["afiliados"], link=link)
    await message.answer(texto)

@dp.message(F.text.startswith("?start=aff_"))
async def afiliado_start(message: Message):
    aff_id = int(message.text.split("_")[1])
    if aff_id in users and message.from_user.id not in users[aff_id]["indications"]:
        users[aff_id]["indications"].append(message.from_user.id)
        users[aff_id]["afiliados"] += 1
        users[aff_id]["pontos"] += configs["pontos_por_recarga"]  # Adicione ao recarregar

# /id
@dp.message(F.text == "/id")
async def id_comando(message: Message):
    await message.answer("🆔 Seu id é: " + str(message.from_user.id))

# /ranking (redireciona para callback)
@dp.message(F.text == "/ranking")
async def ranking_comando(message: Message):
    await ranking_menu(Message(text="/ranking", from_user=message.from_user), None)  # Simula callback

# /alertas
@dp.message(F.text == "/alertas")
async def alertas_menu(message: Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for prod in estoque:
        on = message.from_user.id in alertas.get(prod, [])
        markup.inline_keyboard.append([InlineKeyboardButton(f"{prod} ({'on' if on else 'off'})", callback_data=f"toggle_alerta_{prod}")])
    await message.answer("Alertas:", reply_markup=markup)

@dp.callback_query(F.data.startswith("toggle_alerta_"))
async def toggle_alerta(callback_query: CallbackQuery):
    prod = callback_query.data[14:]
    user_id = callback_query.from_user.id
    if prod not in alertas:
        alertas[prod] = []
    if user_id in alertas[prod]:
        alertas[prod].remove(user_id)
    else:
        alertas[prod].append(user_id)
    await alertas_menu(callback_query.message)  # Refresh

# Quando adicionar login, notificar alertas
# Em process_add_login, após add: for user in alertas.get(nome, []): await bot.send_message(user, f"🤖 {nome} ABASTECIDO NO BOT")

# Voltar Geral
@dp.callback_query(F.data == "voltar")
async def voltar(callback_query: CallbackQuery, state: FSMContext):
    await start(callback_query.message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
