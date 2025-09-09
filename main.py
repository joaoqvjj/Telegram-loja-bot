import asyncio
import logging
import os
import random
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

# Logs para debug no Render
logging.basicConfig(level=logging.INFO)

# Token (env var no Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("ERRO: BOT_TOKEN não encontrado! Adicione no Render.")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Produtos inventados (preços aleatórios, estoque inicial)
produtos = [
    {"nome": "💜 Deezer Premium (Seu Email)", "preco": 3.00, "estoque": 2},
    {"nome": "🎵 Spotify Premium", "preco": 5.00, "estoque": 10},
    {"nome": "📺 Netflix Tela", "preco": 8.00, "estoque": 5},
    {"nome": "🎬 Prime Video", "preco": 7.00, "estoque": 3},
    {"nome": "🎮 Xbox Game Pass", "preco": 12.00, "estoque": 4},
]

# Saldo e estoque fake (por user_id)
user_data = {}  # {user_id: {"saldo": 0.0, "compras": 0}}

# Menu principal (como na imagem: botões em posições exatas)
def menu_principal():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 COMPRAR CONTA", callback_data="comprar"),
            InlineKeyboardButton(text="👤 PERFIL", callback_data="perfil")
        ],
        [
            InlineKeyboardButton(text="💎 ADICIONAR SALDO", callback_data="addsaldo"),
            InlineKeyboardButton(text="📞 FALE CONOSCO", url="https://t.me/seu_username_aqui")  # Mude para real
        ],
        [
            InlineKeyboardButton(text="📜 TERMOS E REGRAS", callback_data="termos"),
            InlineKeyboardButton(text="🏆 RANKS", callback_data="ranks")
        ],
        [InlineKeyboardButton(text="🔍 PESQUISAR SERVIÇOS", callback_data="pesquisar")]
    ])
    return markup

# Start (menu 𝗦𝗧𝗢𝗥𝗘)
@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"saldo": 0.0, "compras": 0}
    await message.answer("👋 Bem-vindo à 𝗦𝗧𝗢𝗥𝗘 Bot!\nEscolha uma opção abaixo:", reply_markup=menu_principal())

# Comprar Conta
@dp.callback_query(F.data == "comprar")
async def comprar_menu(callback_query: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for i, p in enumerate(produtos):
        markup.inline_keyboard.append([InlineKeyboardButton(text=f"{p['nome']} - R${p['preco']:.2f}", callback_data=f"produto_{i}")])
    markup.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Voltar", callback_data="voltar")])
    await callback_query.message.edit_text("𝗦𝗘𝗟𝗘𝗖𝗜𝗢𝗡𝗘 𝗔 𝗖𝗢𝗡𝗧𝗔 𝗗𝗘𝗦𝗘𝗝𝗔𝗗𝗔", reply_markup=markup)
    await callback_query.answer()

# Detalhe Produto
@dp.callback_query(F.data.startswith("produto_"))
async def produto_info(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[1])
    p = produtos[index]
    saldo = user_data[user_id]["saldo"]
    estoque = p["estoque"]

    texto = f"🛍️ 𝗙𝗜𝗡𝗔𝗟𝗜𝗭𝗔𝗥 𝗖𝗢𝗠𝗣𝗥𝗔 🛍️\n\n" \
            f"🖥️|• 𝐒𝐄𝐑𝐕𝐈𝐂̧𝐎: {p['nome']}\n" \
            f"💰|• 𝐏𝐑𝐄𝐂̧𝐎: R${p['preco']:.2f}\n" \
            f"🪙|• 𝐒𝐀𝐋𝐃𝐎 𝐃𝐈𝐒𝐏𝐎𝐍𝐈́𝐕𝐄𝐋: R${saldo:.2f}\n" \
            f"📦|• 𝐃𝐈𝐒𝐏𝐎𝐍𝐈́𝐕𝐄𝐋: {estoque}\n\n" \
            f"🔎 |•𝑰𝑵𝑭𝑶𝑹𝑴𝑨𝑪̧𝑶𝑬𝑺 𝑫𝑬𝑺𝑺𝑬 𝑷𝑹𝑶𝑫𝑼𝑻𝑶:\n" \
            f"USE APENAS O SEU PERFIL | NÃO COMPARTILHE O ACESSO | NÃO MUDE OS DADOS DA CONTA | USE APENAS EM 1 APARELHO!\n\n" \
            f"🎬 Esse login é uma ótima opção, garanta já! 🚀\n" \
            f"✅ Durabilidade e suporte por 30 dias!\n" \
            f"❗ Clique em comprar e adquira seu login automaticamente!"

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Comprar", callback_data=f"comprar_{index}"),
            InlineKeyboardButton(text="Comprar na Quantidade", callback_data=f"comprar_qtd_{index}")
        ],
        [
            InlineKeyboardButton(text="ADICIONAR SALDO", callback_data="addsaldo"),
            InlineKeyboardButton(text="VOLTAR", callback_data="comprar")
        ]
    ])
    await callback_query.message.edit_text(texto, reply_markup=markup)
    await callback_query.answer()

# Comprar (1 unidade – simula confirmação)
@dp.callback_query(F.data.startswith("comprar_"))
async def comprar_simples(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    index = int(callback_query.data.split("_")[1])
    p = produtos[index]
    if p["estoque"] > 0 and user_data[user_id]["saldo"] >= p["preco"]:
        user_data[user_id]["saldo"] -= p["preco"]
        user_data[user_id]["compras"] += 1
        p["estoque"] -= 1
        await callback_query.answer("Compra realizada! Login: fake@login.com (simulado).")
    else:
        await callback_query.answer("Saldo insuficiente ou estoque vazio!")
    await callback_query.message.edit_text("Compra finalizada. Volte ao menu:", reply_markup=menu_principal())

# Comprar na Quantidade (pergunta qtd, reply automático)
@dp.callback_query(F.data.startswith("comprar_qtd_"))
async def comprar_qtd_prompt(callback_query: CallbackQuery):
    index = int(callback_query.data.split("_")[1])
    p = produtos[index]
    msg = await callback_query.message.answer(f"Quantos logins de {p['nome']} você deseja comprar?")
    # Salva estado para handler de quantidade (use filtros ou state, mas simples: reply to this msg)
    await callback_query.answer()

@dp.message(F.text.isdigit())  # Handler para quantidade (responde reply)
async def process_qtd(message: Message):
    if message.reply_to_message and "Quantos logins" in message.reply_to_message.text:
        user_id = message.from_user.id
        qtd = int(message.text)
        # Extrai produto do reply (simples parse)
        nome_prod = message.reply_to_message.text.split("de ")[1].split(" você")[0]
        index = next(i for i, p in enumerate(produtos) if p['nome'] == nome_prod)
        p = produtos[index]
        total = p["preco"] * qtd
        if p["estoque"] >= qtd and user_data[user_id]["saldo"] >= total:
            user_data[user_id]["saldo"] -= total
            user_data[user_id]["compras"] += qtd
            p["estoque"] -= qtd
            await message.answer(f"Compra de {qtd} logins realizada! Total: R${total:.2f}. Gerando Pix simulado...")
            # Simula Pix para compra
            await generate_pix(message, total, is_compra=True, qtd=qtd, prod_nome=p['nome'])
        else:
            await message.answer(f"Saldo insuficiente após comprar 0 logins. (Necessário: R${total:.2f})")

# Adicionar Saldo
@dp.callback_query(F.data == "addsaldo")
async def addsaldo_menu(callback_query: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pix automatico", callback_data="pix_auto")],
        [InlineKeyboardButton(text="Voltar", callback_data="voltar")]
    ])
    await callback_query.message.edit_text("Escolha:", reply_markup=markup)
    await callback_query.answer()

# Pix Automático (pergunta valor, reply)
@dp.callback_query(F.data == "pix_auto")
async def pix_prompt(callback_query: CallbackQuery):
    msg = await callback_query.message.answer("Digite o valor que deseja recarregar!\nmínimo: R$4.00\nmáximo: R$999.00")
    await callback_query.answer()

@dp.message(F.text.replace('.', '', 1).isdigit())  # Handler para valor (float ok)
async def process_valor(message: Message):
    if message.reply_to_message and "Digite o valor" in message.reply_to_message.text:
        valor = float(message.text)
        if 4 <= valor <= 999:
            await generate_pix(message, valor)
        else:
            await message.answer("Valor fora do limite!")

# Gerar Pix (fake, com botão aguardar)
async def generate_pix(message: Message, valor: float, is_compra=False, qtd=0, prod_nome=""):
    expira_em = int(time.time()) + 900  # 15 min
    id_compra = random.randint(100000000000, 999999999999)
    fake_pix_code = "00020126360014br.gov.bcb.pix0114+5588996478524520400005303986540528.005802BR5918DARA202401101939296009Sao Paulo62250521mpqrinter12547870808863048C41"  # Fake example

    texto = f"💰 {'Comprar Saldo' if not is_compra else 'Pagar Compra'} com pix automático:\n\n" \
            f"⏱ Expira em: 15 min\n" \
            f"💰 Valor: R${valor:.2f}\n" \
            f"✨ ID da compra: {id_compra}\n\n" \
            f"📃 Este código \"copia e cola\" é valido para apenas 1 pagamento!\n" \
            f"Ou seja, se você utilizar ele mais de 1 vez para adicionar saldo, você PERDERAR o saldo e não tem direito a reembolso!\n\n" \
            f"💎 Pix copia e cola:\n\n" \
            f"💡 Clique no código para copia-lo.\n\n" \
            f"{fake_pix_code}\n\n" \
            f"🇧🇷 Após o pagamento ser efetuado, seu saldo será liberado instantaneamente."

    if is_compra:
        texto += f"\nCompra: {qtd} x {prod_nome}"

    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Aguardando o pagamento", callback_data="check_pag")]])
    await message.answer(texto, reply_markup=markup)

# Check Pagamento (simula confirmação fake)
@dp.callback_query(F.data == "check_pag")
async def check_pag(callback_query: CallbackQuery):
    # Simula delay e confirma (fake – em real, poll API)
    await asyncio.sleep(2)  # Fake wait
    user_id = callback_query.from_user.id
    # Adiciona saldo fake (assume pago)
    user_data[user_id]["saldo"] += 28.00  # Exemplo valor
    await callback_query.message.edit_text("Pagamento confirmado! Saldo adicionado.")
    await callback_query.answer("Pago (simulado)!")

# Perfil
@dp.callback_query(F.data == "perfil")
async def perfil(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    saldo = user_data[user_id]["saldo"]
    compras = user_data[user_id]["compras"]
    texto = f"👤 PERFIL DO USUÁRIO\n\n🆔 ID: {user_id}\n💰 Saldo: R${saldo:.2f}\n📦 Compras: {compras}"
    await callback_query.message.edit_text(texto, reply_markup=menu_principal())
    await callback_query.answer()

# Voltar (edita para menu)
@dp.callback_query(F.data == "voltar")
async def voltar(callback_query: CallbackQuery):
    await callback_query.message.edit_text("👋 Menu principal:", reply_markup=menu_principal())
    await callback_query.answer()

# Placeholders (termos, ranks, pesquisar)
@dp.callback_query(F.data.in_(["termos", "ranks", "pesquisar"]))
async def placeholders(callback_query: CallbackQuery):
    await callback_query.answer("Em desenvolvimento!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
