import random
import string
import json
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
import os
from pytz import timezone
from pyrogram.enums import ChatType
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus




API_ID = 0
API_HASH = ""
BOT_TOKEN = ""

app = Client(
    "TOPVEGA_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)



BANK_NAME = "Vega Bank"
CURRENCY = "SAR"
BANK_OWNER = 7654641648

SALARY_COOLDOWN = 20 * 60
TIP_COOLDOWN = 10 * 60
STEAL_COOLDOWN = 10 * 60
INVEST_COOLDOWN = 30 * 60
LUCK_COOLDOWN = 15 * 60
TREASURE_COOLDOWN = 6 * 60 * 60
WHEEL_COOLDOWN = 4 * 60 * 60
PROTECTION_COOLDOWN = 60 * 60
CODE_COOLDOWN = 24 * 60 * 60
MAX_ACTIVE_CODES = 100

def generate_random_code(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def load_codes_data():
    try:
        with open('codes_data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'active_codes': {},
            'used_codes': {}
        }

def save_codes_data(data):
    with open('codes_data.json', 'w') as f:
        json.dump(data, f, indent=4)

def generate_new_codes(count=10):
    codes_data = load_codes_data()
    current_time = int(time.time())
    for code in list(codes_data['active_codes'].keys()):
        if codes_data['active_codes'][code]['expires_at'] < current_time:
            del codes_data['active_codes'][code]
    new_codes = []
    for _ in range(count):
        code = generate_random_code()
        reward = random.choice([
            random.randint(500, 1000),
            random.randint(1000, 2000),
            random.randint(2000, 5000),
            random.randint(5000, 10000)
        ])
        codes_data['active_codes'][code] = {
            'reward': reward,
            'created_at': current_time,
            'expires_at': current_time + (24 * 60 * 60),
            'used': False
        }
        new_codes.append((code, reward))
    save_codes_data(codes_data)
    return new_codes

def load_data():
    try:
        with open('bank_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'accounts': {},
            'transactions': [],
            'thieves': {},
            'cooldowns': {},
            'protected': {},
            'treasure': 1000000
        }

def save_data(data):
    with open('bank_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def format_money(amount):
    return f"{amount:,} {CURRENCY}"

def get_account(user_id):
    data = load_data()
    return data['accounts'].get(str(user_id))

def update_account(user_id, account):
    data = load_data()
    data['accounts'][str(user_id)] = account
    save_data(data)

def check_cooldown(user_id, action):
    data = load_data()
    cooldowns = data.get('cooldowns', {})
    last_time = cooldowns.get(f"{user_id}_{action}", 0)
    remaining = max(0, (last_time + globals()[f"{action.upper()}_COOLDOWN"]) - int(time.time()))
    return remaining

def update_cooldown(user_id, action):
    data = load_data()
    data['cooldowns'][f"{user_id}_{action}"] = int(time.time())
    save_data(data)

last_added = {}

@app.on_message(filters.command("addmoney", "") & filters.user(BANK_OWNER), group=588)
async def add_money(client, message):
    try:
        user_id = BANK_OWNER
        current_time = datetime.now()
        last_time = last_added.get(user_id)
        if last_time and (current_time - last_time) < timedelta(hours=12):
            remaining_time = timedelta(hours=12) - (current_time - last_time)
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            await message.reply(f"You can use this feature once every 12 hours!\nRemaining time: {hours} hours and {minutes} minutes")
            return
        amount = 1000000
        data = load_data()
        if str(user_id) not in data['accounts']:
            await message.reply("You don't have a bank account! Please create one first")
            return
        old_balance = data['accounts'][str(user_id)]['balance']
        bank_type = data['accounts'][str(user_id)]['bank']
        data['accounts'][str(user_id)]['balance'] += amount
        new_balance = data['accounts'][str(user_id)]['balance']
        save_data(data)
        last_added[user_id] = current_time
        try:
            user = await client.get_users(user_id)
            user_name = user.first_name
            user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
        except:
            user_name = "Owner"
            user_mention = "Owner"
        bank_info = BANKS.get(bank_type, {})
        bank_name = bank_info.get('name', 'Unknown Bank')
        response = (
            f"<b>Automatic balance addition for owner</b>\n\n"
            f"User: {user_mention}\n"
            f"Bank type: {bank_name}\n"
            f"Amount added: <b>({format_money(amount)})</b>\n\n"
            f"Previous balance: <b>({format_money(old_balance)})</b>\n"
            f"New balance: <b>({format_money(new_balance)})</b>\n\n"
            f"Automatic addition completed successfully\n"
        )
        await message.reply(response, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        print(f"Error in add_money: {e}")
        await message.reply("An error occurred while adding balance!")

@app.on_message(filters.command("deleteaccount", "") & filters.user(BANK_OWNER), group=5688)
async def delete_account(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to the person to delete their account")
        return
    user_id = message.reply_to_message.from_user.id
    data = load_data()
    if str(user_id) not in data['accounts']:
        await message.reply("They don't have an account!")
        return
    del data['accounts'][str(user_id)]
    save_data(data)
    await message.reply("Account deleted")

@app.on_message(filters.command("resetbank", "") & filters.user(BANK_OWNER), group=5577)
async def reset_bank(client, message):
    data = {
        'accounts': {},
        'transactions': [],
        'thieves': {},
        'cooldowns': {},
        'protected': {},
        'treasure': 1000000
    }
    save_data(data)
    await message.reply("The entire bank has been reset")

BANKS = {
    "ahli": {
        "name": "Ahli Bank",
        "min_balance": 1000,
        "visa_fee": 50
    },
    "bluesky": {
        "name": "Blue Sky Bank",
        "min_balance": 2000,
        "visa_fee": 100
    },
    "credit": {
        "name": "Credit Bank",
        "min_balance": 5000,
        "visa_fee": 200
    }
}

@app.on_message(filters.regex("^create bank account$"), group=67899)
async def create_account(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    data = load_data()
    if str(user_id) in data['accounts']:
        await message.reply("You already have a bank account!")
        return
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{BANKS['ahli']['name']}", callback_data="bank_ahli"),
            InlineKeyboardButton(f"{BANKS['bluesky']['name']}", callback_data="bank_bluesky")
        ],
        [
            InlineKeyboardButton(f"{BANKS['credit']['name']}", callback_data="bank_credit")
        ]
    ])
    await message.reply(
        f"Welcome {user_name}\nChoose the bank you want:\n\n"
        "Ahli Bank\n"
        "Blue Sky Bank\n"
        "Credit Bank\n\n"
        "Click on the bank name you want:\n"
        "Use command `bank` to see the commands",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^bank_(.*)$"), group=59980088)
async def handle_bank_selection(client, callback_query):
    bank_key = callback_query.matches[0].group(1)
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name
    if bank_key not in BANKS:
        await callback_query.answer("This bank is not available")
        return
    bank = BANKS[bank_key]
    account_number = str(random.randint(1000000000, 9999999999))
    visa_number = f"4{random.randint(100000000000000, 999999999999999)}"
    data = load_data()
    data['accounts'][str(user_id)] = {
        'bank': bank_key,
        'account_number': account_number,
        'balance': bank['min_balance'],
        'visa': {
            'number': visa_number,
            'expiry': f"{random.randint(1, 12):02d}/{random.randint(23, 30)}",
            'cvv': f"{random.randint(100, 999)}"
        },
        'created_at': int(time.time()),
        'user_name': user_name
    }
    save_data(data)
    await callback_query.message.edit_text(
        f"Account created at {bank['name']} {user_name}!\n\n"
        f"Your name: {user_name}\n"
        f"Account number: `{account_number}`\n"
        f"Initial balance: {bank['min_balance']} SAR\n\n"
        f"Visa:\n"
        f"Number: `{visa_number}`\n"
        f"Expiry: {data['accounts'][str(user_id)]['visa']['expiry']}\n"
        f"CVV: {data['accounts'][str(user_id)]['visa']['cvv']}\n\n"
        f"Use `myaccount` to see your account information"
    )

@app.on_message(filters.command("myaccount", ""), group=59009)
async def my_account(client, message):
    user_id = message.from_user.id
    data = load_data()
    if str(user_id) not in data['accounts']:
        await message.reply("You don't have a bank account! Use `bank` to create one")
        return
    account = data['accounts'][str(user_id)]
    bank = BANKS[account['bank']]
    await message.reply(
        f"Your account information at {bank['name']}\n\n"
        f"Account number: `{account['account_number']}`\n"
        f"Balance: **({account['balance']})** SAR\n\n"
        f"Visa:\n"
        f"Number: `{account['visa']['number']}`\n"
        f"Expiry: {account['visa']['expiry']}\n"
        f"CVV: {account['visa']['cvv']}\n\n"
        f"Created: {time.strftime('%Y-%m-%d', time.localtime(account['created_at']))}"
    )

@app.on_message(filters.command("deletemyaccount", ""), group=54433)
async def delete_my_account(client, message):
    user_id = message.from_user.id
    data = load_data()
    if str(user_id) not in data['accounts']:
        await message.reply("You don't have an account!")
        return
    del data['accounts'][str(user_id)]
    save_data(data)
    await message.reply("Your account has been deleted")

@app.on_message(filters.command(["mybalance", "mycash"], ""), group=5433)
async def my_balance(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    await message.reply(f"Your current balance: **({format_money(account['balance'])})**")

@app.on_message(filters.command(["hisbalance", "hiscash"], ""), group=53223)
async def user_balance(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to the person to see their balance")
        return
    user_id = message.reply_to_message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("They don't have an account!")
        return
    await message.reply(f"Their balance: **({format_money(account['balance'])})**")

@app.on_message(filters.command("transfer", ""), group=5578)
async def transfer(client, message):
    user_id = message.from_user.id
    sender_account = get_account(user_id)
    if not sender_account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    try:
        _, account_number, amount = message.text.split()
        amount = int(amount)
    except:
        await message.reply("Use it like this:\ntransfer account_number amount")
        return
    if amount <= 0:
        await message.reply("Amount must be greater than zero")
        return
    if sender_account['balance'] < amount:
        await message.reply(f"Your money is not enough! You have: {format_money(sender_account['balance'])}")
        return
    data = load_data()
    receiver_id = None
    for uid, acc in data['accounts'].items():
        if str(acc['account_number']) == account_number:
            receiver_id = uid
            break
    if not receiver_id:
        await message.reply("Account number is wrong!")
        return
    if int(receiver_id) == user_id:
        await message.reply("You can't transfer to yourself!")
        return
    data['accounts'][str(user_id)]['balance'] -= amount
    data['accounts'][receiver_id]['balance'] += amount
    data['transactions'].append({
        'from': user_id,
        'to': int(receiver_id),
        'amount': amount,
        'time': int(time.time())
    })
    save_data(data)
    await message.reply(
        f"Transfer completed!\n"
        f"Amount: **({format_money(amount)})**\n"
        f"To account: {account_number}\n\n"
        f"Your new balance: {format_money(data['accounts'][str(user_id)]['balance'])}"
    )

JOBS = {
    "blacksmith": {"salary": (1000, 2000)},
    "doctor": {"salary": (2000, 3000)},
    "engineer": {"salary": (1500, 2500)},
    "programmer": {"salary": (1700, 2700)},
    "cook": {"salary": (800, 1500)},
    "driver": {"salary": (700, 1200)},
    "carpenter": {"salary": (900, 1800)},
    "police": {"salary": (1200, 2200)},
    "teacher": {"salary": (1100, 2100)},
    "farmer": {"salary": (600, 1300)}
}

@app.on_message(filters.command("salary", ""), group=50988)
async def salary(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `create` to create an account")
        return
    remaining = check_cooldown(user_id, 'salary')
    if remaining > 0:
        mins, secs = divmod(remaining, 60)
        await message.reply(f"You can't take salary now!\nCome back after {mins} minutes and {secs} seconds")
        return
    job_name, job_info = random.choice(list(JOBS.items()))
    salary_amount = random.randint(job_info["salary"][0], job_info["salary"][1])
    data = load_data()
    old_balance = data['accounts'][str(user_id)]['balance']
    data['accounts'][str(user_id)]['balance'] += salary_amount
    new_balance = old_balance + salary_amount
    save_data(data)
    update_cooldown(user_id, 'salary')
    user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    await message.reply(
        f"Deposit notification | {user_mention}\n\n"
        f"Amount: <b>({format_money(salary_amount)})</b> SAR\n"
        f"Your job: {job_name}\n"
        f"Transaction type: salary addition\n"
        f"Your balance now: <b>({format_money(new_balance)})</b> SAR",
        parse_mode=enums.ParseMode.HTML
    )

@app.on_message(filters.command("tip", ""), group=554330)
async def tip(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'tip')
    if remaining > 0:
        mins = remaining // 60
        await message.reply(f"You can't get a tip now!\nCome back after {mins} minutes")
        return
    tip_amount = random.randint(100, 500)
    data = load_data()
    data['accounts'][str(user_id)]['balance'] += tip_amount
    save_data(data)
    update_cooldown(user_id, 'tip')
    await message.reply(
        f"You got a tip!\n"
        f"Amount: **({format_money(tip_amount)})**\n"
        f"Your balance now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
    )

@app.on_message(filters.command(["steal", "rob"], ""), group=53456)
async def steal(client, message):
    user_id = message.from_user.id
    thief_account = get_account(user_id)
    if not thief_account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'steal')
    if remaining > 0:
        mins = remaining // 60
        await message.reply(f"You can't steal now!\nCome back after {mins} minutes")
        return
    if not message.reply_to_message:
        await message.reply("Reply to the person you want to steal from!")
        return
    victim_id = message.reply_to_message.from_user.id
    if victim_id == user_id:
        await message.reply("You can't steal from yourself!")
        return
    victim_account = get_account(victim_id)
    if not victim_account:
        await message.reply("They don't have an account!")
        return
    if victim_account.get('protected', False):
        await message.reply("They have protection that stops stealing!")
        return
    if victim_account['balance'] < 100:
        await message.reply("Their money is not worth it!")
        return
    steal_amount = random.randint(50, min(500, victim_account['balance']))
    if random.random() > 0.5:
        data = load_data()
        data['accounts'][str(user_id)]['balance'] += steal_amount
        data['accounts'][str(victim_id)]['balance'] -= steal_amount
        if str(user_id) not in data['thieves']:
            data['thieves'][str(user_id)] = 0
        data['thieves'][str(user_id)] += steal_amount
        save_data(data)
        update_cooldown(user_id, 'steal')
        await message.reply(
            f"You stole from them!\n"
            f"Amount: **({format_money(steal_amount)})**\n"
            f"Your balance now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
        )
    else:
        update_cooldown(user_id, 'steal')
        await message.reply("You got caught stealing! You got nothing")

@app.on_message(filters.command("invest", ""), group=5333)
async def invest(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'invest')
    if remaining > 0:
        mins = remaining // 60
        await message.reply(f"You can't invest now!\nCome back after {mins} minutes")
        return
    try:
        _, amount = message.text.split()
        amount = int(amount)
    except:
        await message.reply("Use it like this:\ninvest amount")
        return
    if amount <= 0:
        await message.reply("Amount must be greater than zero")
        return
    if account['balance'] < amount:
        await message.reply(f"Your money is not enough! You have: {format_money(account['balance'])}")
        return
    profit_percent = random.randint(-10, 20)
    profit_amount = int(amount * profit_percent / 100)
    data = load_data()
    data['accounts'][str(user_id)]['balance'] += profit_amount
    save_data(data)
    update_cooldown(user_id, 'invest')
    if profit_amount >= 0:
        await message.reply(
            f"Successful investment!\n"
            f"Profit percentage: {profit_percent}%\n"
            f"Profit amount: ({format_money(profit_amount)})\n"
            f"Your money now: ({format_money(data['accounts'][str(user_id)]['balance'])})"
        )
    else:
        await message.reply(
            f"Losing investment!\n"
            f"Loss percentage: **({abs(profit_percent)}%)**\n"
            f"Loss amount: ({format_money(abs(profit_amount))})\n"
            f"Your money now: ({format_money(data['accounts'][str(user_id)]['balance'])})"
        )

STOCK_TYPES = {
    "oil": {"volatility": 15, "description": "Oil and gas companies"},
    "jewelry": {"volatility": 10, "description": "Jewelry and precious stones"},
    "diamond": {"volatility": 12, "description": "Global diamond trade"},
    "watches": {"volatility": 8, "description": "Luxury watch companies"},
    "devices": {"volatility": 20, "description": "Electronics companies"},
    "buildings": {"volatility": 5, "description": "Construction and real estate companies"},
    "planes": {"volatility": 18, "description": "Aviation and aerospace companies"},
    "ships": {"volatility": 12, "description": "Shipping and maritime transport companies"},
    "nvidia": {"volatility": 25, "description": "Nvidia technology company"},
    "microsoft": {"volatility": 15, "description": "Microsoft company"},
    "apple": {"volatility": 18, "description": "Apple company"},
    "gold": {"volatility": 7, "description": "Global gold trade"},
    "silver": {"volatility": 5, "description": "Global silver trade"}
}

@app.on_message(filters.command("buystock", ""), group=5336)
async def buy_stock(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `create` to create an account")
        return
    if len(message.text.split()) <= 2:
        stocks_list = "\n".join(
            f"{name} - {info['description']} (volatility: {info['volatility']}%)"
            for name, info in STOCK_TYPES.items()
        )
        await message.reply(
            f"<b>Available stocks to buy:\n\n{stocks_list}\n\n"
            "Use the command like this:\n`buystock` type amount\n"
            "Example: `buystock oil 1000`</b>"
        )
        return
    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("Use the command like this:\n`buystock` type amount")
            return
        stock_type = parts[2]
        amount = int(parts[3])
        if stock_type not in STOCK_TYPES:
            await message.reply("Stock type is incorrect! Use `buystock` to see options")
            return
        if amount < 100:
            await message.reply("Minimum stock purchase is 100 SAR")
            return
        if account['balance'] < amount:
            await message.reply(f"Your money is not enough! You have: {format_money(account['balance'])}")
            return
        volatility = STOCK_TYPES[stock_type]["volatility"]
        profit_percent = random.randint(-volatility, volatility)
        profit_amount = int(amount * profit_percent / 100)
        data = load_data()
        if 'investments' not in data:
            data['investments'] = {}
        if str(user_id) not in data['investments']:
            data['investments'][str(user_id)] = {}
        stock_id = str(int(time.time()))
        data['investments'][str(user_id)][stock_id] = {
            'type': stock_type,
            'amount': amount,
            'profit': profit_amount,
            'time': int(time.time()),
            'sold': False
        }
        data['accounts'][str(user_id)]['balance'] -= amount
        data['accounts'][str(user_id)]['balance'] += (amount + profit_amount)
        save_data(data)
        if profit_amount >= 0:
            await message.reply(
                f"Successful purchase!\n"
                f"Stock type: {stock_type}\n"
                f"Invested amount: {format_money(amount)}\n"
                f"Profit percentage: **({profit_percent}%)**\n"
                f"Profit amount: **({format_money(profit_amount)})**\n"
                f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
            )
        else:
            await message.reply(
                f"Losing purchase!\n"
                f"Stock type: {stock_type}\n"
                f"Invested amount: **({format_money(amount)})**\n"
                f"Loss percentage: **({abs(profit_percent)}%)**\n"
                f"Loss amount: **({format_money(abs(profit_amount))})**\n"
                f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
            )
    except ValueError:
        await message.reply("Amount must be a valid number!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("An error occurred! Make sure to use the command correctly:\n`buystock type amount`")

@app.on_message(filters.command("sellstock", ""), group=5337)
async def sell_stock(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `create` to create an account")
        return
    if len(message.text.split()) < 3:
        await message.reply("Use the command like this:\n`sellstock` stock_id\nExample: `sellstock 1754355053`")
        return
    try:
        stock_id = message.text.split()[2]
        data = load_data()
        if 'investments' not in data or str(user_id) not in data['investments'] or not data['investments'][str(user_id)]:
            await message.reply("You don't have any stocks!")
            return
        user_stocks = data['investments'][str(user_id)]
        if stock_id not in user_stocks:
            await message.reply("Stock ID is incorrect or doesn't belong to you!")
            return
        stock = user_stocks[stock_id]
        total_value = stock['amount'] + stock['profit']
        data['accounts'][str(user_id)]['balance'] += total_value
        del data['investments'][str(user_id)][stock_id]
        if not data['investments'][str(user_id)]:
            del data['investments'][str(user_id)]
        save_data(data)
        stock_type = stock['type']
        if stock['profit'] >= 0:
            await message.reply(
                f"Successful sale!\n"
                f"Stock type: {stock_type}\n"
                f"Invested amount: **({format_money(stock['amount'])})**\n"
                f"Profit achieved: **({format_money(stock['profit'])})**\n"
                f"Total value: **({format_money(total_value)})**\n"
                f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
            )
        else:
            await message.reply(
                f"Losing sale!\n"
                f"Stock type: {stock_type}\n"
                f"Invested amount: **({format_money(stock['amount'])})**\n"
                f"Loss achieved: **({format_money(abs(stock['profit']))})**\n"
                f"Total value: **({format_money(total_value)})**\n"
                f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
            )
    except Exception as e:
        print(f"Error in sell_stock: {e}")
        await message.reply("An error occurred! Make sure to use the command correctly:\n`sellstock stock_id`")

@app.on_message(filters.command("mystocks", ""), group=5338)
async def my_stocks(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `create`")
        return
    data = load_data()
    if 'investments' not in data or str(user_id) not in data['investments'] or not data['investments'][str(user_id)]:
        await message.reply("You don't have any stocks!")
        return
    stocks = data['investments'][str(user_id)]
    response = "Your investment portfolio:\n\n"
    for stock_id, stock in stocks.items():
        current_value = stock['amount'] + stock['profit']
        profit_percent = int((stock['profit'] / stock['amount']) * 100) if stock['amount'] > 0 else 0
        response += (
            f"**{stock['type']}**\n"
            f"Stock ID: `{stock_id}`\n"
            f"Current value: {format_money(current_value)}\n"
            f"Profit/Loss: {profit_percent}% ({format_money(stock['profit'])})\n"
            f"Purchase date: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stock['time']))}\n\n"
        )
    response += "Use:\n"
    response += "`sellstock` stock_id to sell a specific stock\n"
    response += "`sellallstocks` to sell all your stocks at once"
    await message.reply(response)

@app.on_message(filters.command("sellallstocks", ""), group=5339)
async def sell_all_stocks(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `create`")
        return
    data = load_data()
    if 'investments' not in data or str(user_id) not in data['investments'] or not data['investments'][str(user_id)]:
        await message.reply("You don't have any stocks!")
        return
    total_amount = 0
    stocks_count = 0
    for stock_id, stock in list(data['investments'][str(user_id)].items()):
        stock_value = int((stock['amount'] + stock['profit']) * 0.8)
        total_amount += stock_value
        stocks_count += 1
        del data['investments'][str(user_id)][stock_id]
    data['accounts'][str(user_id)]['balance'] += total_amount
    if not data['investments'][str(user_id)]:
        del data['investments'][str(user_id)]
    save_data(data)
    await message.reply(
        f"All stocks sold!\n\n"
        f"Number of stocks sold: {stocks_count}\n"
        f"Total amount: **({format_money(total_amount)})**\n"
        f"Your current balance: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
    )

@app.on_message(filters.command(["gamble", "double"], ""), group=56788)
async def gamble(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    try:
        _, amount = message.text.split()
        amount = int(amount)
    except:
        await message.reply("Use it like this:\ngamble amount")
        return
    if amount <= 0:
        await message.reply("Amount must be greater than zero")
        return
    if account['balance'] < amount:
        await message.reply(f"Your money is not enough! You have: {format_money(account['balance'])}")
        return
    result_percent = random.randint(-90, 90)
    result_amount = int(amount * result_percent / 100)
    data = load_data()
    data['accounts'][str(user_id)]['balance'] += result_amount
    save_data(data)
    if result_amount >= 0:
        await message.reply(
            f"You won the gamble!\n"
            f"Amount: **({format_money(amount)})**\n"
            f"Percentage: (+{result_percent}%)\n"
            f"Profit: ({format_money(result_amount)})\n"
            f"Your money now:**({format_money(data['accounts'][str(user_id)]['balance'])})**"
        )
    else:
        await message.reply(
            f"You lost the gamble!\n"
            f"Amount: **({format_money(amount)})**\n"
            f"Percentage: {result_percent}%\n"
            f"Loss: {format_money(abs(result_amount))}\n"
            f"Your money now: {format_money(data['accounts'][str(user_id)]['balance'])}"
        )

@app.on_message(filters.command("luck", ""), group=56788)
async def luck(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'luck')
    if remaining > 0:
        mins = remaining // 60
        await message.reply(f"Wait {mins} minutes to play your luck again")
        return
    try:
        _, amount = message.text.split()
        amount = int(amount)
    except:
        await message.reply("Use it like this:\nluck amount")
        return
    if amount <= 0:
        await message.reply("Amount must be greater than zero")
        return
    if account['balance'] < amount:
        await message.reply(f"Your money is not enough! You have: {format_money(account['balance'])}")
        return
    if random.random() > 0.5:
        win_multiplier = random.uniform(1.0, 3.0)
        win_amount = int(amount * win_multiplier)
        data = load_data()
        data['accounts'][str(user_id)]['balance'] += win_amount
        save_data(data)
        update_cooldown(user_id, 'luck')
        await message.reply(
            f"You won the luck game!\n"
            f"Amount: **({format_money(amount)})**\n"
            f"Multiplier: {win_multiplier:.1f}x\n"
            f"Profit: **({format_money(win_amount)})**\n"
            f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
        )
    else:
        data = load_data()
        data['accounts'][str(user_id)]['balance'] -= amount
        save_data(data)
        update_cooldown(user_id, 'luck')
        await message.reply(
            f"You lost the luck game!\n"
            f"Amount: **({format_money(amount)})**\n"
            f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
        )

@app.on_message(filters.command("wheel", ""), group=59988)
async def wheel_of_fortune(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'wheel')
    if remaining > 0:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await message.reply(f"Wait {hours} hours and {mins} minutes to spin the wheel again")
        return
    prizes = [
        ("Small prize", random.randint(100, 500)),
        ("Medium prize", random.randint(500, 1000)),
        ("Big prize", random.randint(1000, 2000)),
        ("Gold prize", random.randint(2000, 5000)),
        ("Nothing", 0),
        ("Try again", 0)
    ]
    prize_name, prize_amount = random.choice(prizes)
    data = load_data()
    data['accounts'][str(user_id)]['balance'] += prize_amount
    save_data(data)
    update_cooldown(user_id, 'wheel')
    if prize_amount > 0:
        await message.reply(
            f"Wheel result:\n"
            f"{prize_name}\n"
            f"Winnings: **({format_money(prize_amount)})**\n"
            f"Your money now:** ({format_money(data['accounts'][str(user_id)]['balance'])})**"
        )
    else:
        await message.reply(
            f"Wheel result:\n"
            f"{prize_name}\n"
            f"You got nothing this time!"
        )

@app.on_message(filters.command(["protect", "protectmoney"], ""), group=5999)
async def protect_money(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'protection')
    if remaining > 0:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await message.reply(f"Wait {hours} hours and {mins} minutes to protect your money again")
        return
    protection_cost = 500
    if account['balance'] < protection_cost:
        await message.reply(f"Your money is not enough! You need {format_money(protection_cost)} to buy protection")
        return
    data = load_data()
    data['accounts'][str(user_id)]['balance'] -= protection_cost
    data['accounts'][str(user_id)]['protected'] = True
    save_data(data)
    update_cooldown(user_id, 'protection')
    await message.reply(
        f"Your money protection is now active!\n"
        f"Cost: **({format_money(protection_cost)})**\n"
        f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**\n\n"
        f"Protection will end after 24 hours or after one steal"
    )

@app.on_message(filters.command(["police", "report"], ""), group=56789)
async def police(client, message):
    if not message.reply_to_message:
        await message.reply("Reply to the person to report them")
        return
    user_id = message.from_user.id
    reporter_account = get_account(user_id)
    if not reporter_account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    thief_id = message.reply_to_message.from_user.id
    if thief_id == user_id:
        await message.reply("You can't report yourself!")
        return
    thief_account = get_account(thief_id)
    if not thief_account:
        await message.reply("They don't have an account!")
        return
    if random.random() < 0.3:
        stolen_amount = random.randint(100, min(1000, thief_account['balance']))
        data = load_data()
        if data['accounts'][str(thief_id)]['balance'] >= stolen_amount:
            data['accounts'][str(thief_id)]['balance'] -= stolen_amount
            data['accounts'][str(user_id)]['balance'] += stolen_amount
            if str(thief_id) in data['protected']:
                del data['protected'][str(thief_id)]
            save_data(data)
            await message.reply(
                f"The police caught the thief!\n"
                f"They recovered for you: **({format_money(stolen_amount)})**\n"
                f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**"
            )
        else:
            await message.reply("Their money is not worth it!")
    else:
        await message.reply("The police couldn't catch them this time!")

@app.on_message(filters.command("treasure", ""), group=5899)
async def treasure(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    remaining = check_cooldown(user_id, 'treasure')
    if remaining > 0:
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        await message.reply(f"Wait {hours} hours and {mins} minutes to search for treasure again")
        return
    data = load_data()
    if data['treasure'] <= 0:
        await message.reply("The treasure is empty now, try tomorrow!")
        return
    if random.random() < 0.2:
        treasure_amount = random.randint(1000, min(5000, data['treasure']))
        data['accounts'][str(user_id)]['balance'] += treasure_amount
        data['treasure'] -= treasure_amount
        save_data(data)
        update_cooldown(user_id, 'treasure')
        await message.reply(
            f"You found a treasure!\n"
            f"Amount: **({format_money(treasure_amount)})**\n"
            f"Your money now: **({format_money(data['accounts'][str(user_id)]['balance'])})**\n"
            f"Remaining treasure: {format_money(data['treasure'])}"
        )
    else:
        update_cooldown(user_id, 'treasure')
        await message.reply("You found nothing this time, try tomorrow!")

@app.on_message(filters.command(["topmoney", "topbalances"], ""), group=5008)
async def top_balances(client, message):
    data = load_data()
    accounts = data['accounts']
    if not accounts:
        await message.reply("No bank accounts yet!")
        return
    filtered_accounts = {k: v for k, v in accounts.items() if v['balance'] >= 50000}
    if not filtered_accounts:
        await message.reply("No one has reached 50,000 SAR yet!")
        return
    sorted_accounts = sorted(filtered_accounts.items(), key=lambda x: x[1]['balance'], reverse=True)
    response = "These are the richest 20 players in the game\n\n"
    for idx, (user_id, account) in enumerate(sorted_accounts, 1):
        try:
            user = await client.get_users(int(user_id))
            name = user.first_name
        except:
            name = "Unknown"
        response += f"{idx}. {name}: {format_money(account['balance'])}\n"
    await message.reply(response)

@app.on_message(filters.command("medals", ""), group=5009)
async def my_medals(client, message):
    user_id = message.from_user.id
    data = load_data()
    accounts = data['accounts']
    if str(user_id) not in accounts:
        await message.reply("You don't have a bank account! Use create to create an account")
        return
    user_balance = accounts[str(user_id)]['balance']
    if user_balance < 50000:
        await message.reply("You don't have any medals yet! Your current balance: " + format_money(user_balance))
        return
    filtered_accounts = {k: v for k, v in accounts.items() if v['balance'] >= 50000}
    sorted_accounts = sorted(filtered_accounts.items(), key=lambda x: x[1]['balance'], reverse=True)[:3]
    user_in_top = any(str(user_id) == account[0] for account in sorted_accounts)
    if not user_in_top:
        await message.reply(f"Your balance is {format_money(user_balance)} but you are not in the top three!")
        return
    response = "Top 3 players in the bank\n\n"
    for idx, (account_id, account) in enumerate(sorted_accounts, 1):
        try:
            user = await client.get_users(int(account_id))
            name = user.first_name
        except:
            name = "Unknown"
        medal = ""
        if idx == 1:
            medal = "Bank champion "
        elif idx == 2:
            medal = "Runner-up "
        elif idx == 3:
            medal = "Excellent position "
        is_me = " (You) " if str(user_id) == account_id else ""
        response += f"{medal}{is_me}\nName: {name}\nBalance: {format_money(account['balance'])}\n\n"
    if str(user_id) in [x[0] for x in sorted_accounts]:
        user_position = [i+1 for i, x in enumerate(sorted_accounts) if x[0] == str(user_id)][0]
        response += f"You are in position {user_position}! Your money: {format_money(user_balance)}"
    await message.reply(response)

@app.on_message(filters.command(["topthieves", "topsteal"], ""), group=5877755)
async def top_thieves(client, message):
    data = load_data()
    thieves = data.get('thieves', {})
    if not thieves:
        await message.reply("No thieves registered yet!")
        return
    sorted_thieves = sorted(thieves.items(), key=lambda x: x[1], reverse=True)[:10]
    response = "Top 10 thieves:\n\n"
    for idx, (user_id, amount) in enumerate(sorted_thieves, 1):
        try:
            user = await client.get_users(int(user_id))
            name = user.first_name
        except:
            name = "Unknown"
        response += f"{idx}. {name}: **({format_money(amount)})** stolen\n"
    await message.reply(response)

@app.on_message(filters.command("bribe", ""), group=5334)
async def bribe(client, message):
    user_id = message.from_user.id
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    if not message.reply_to_message:
        await message.reply("Reply to the person to bribe them")
        return
    target_id = message.reply_to_message.from_user.id
    if target_id == user_id:
        await message.reply("You can't bribe yourself!")
        return
    bribe_amount = random.randint(300, 1000)
    if account['balance'] < bribe_amount:
        await message.reply(f"Your money is not enough! You need {format_money(bribe_amount)} to bribe them")
        return
    if random.random() < 0.7:
        data = load_data()
        data['accounts'][str(user_id)]['balance'] -= bribe_amount
        if str(target_id) in data['accounts']:
            data['accounts'][str(target_id)]['balance'] += bribe_amount // 2
        save_data(data)
        await message.reply(
            f"The bribe succeeded!\n"
            f"Amount: {format_money(bribe_amount)}\n"
            f"Your money now: {format_money(data['accounts'][str(user_id)]['balance'])}"
        )
    else:
        await message.reply("The bribe failed and you were reported!")

user_last_show_codes = {}
user_last_use_any_code = {}

@app.on_message(filters.command("scratch", ""), group=54333)
async def scratch_codes(client, message):
    user_id = message.from_user.id
    if user_id in user_last_show_codes:
        last_time = user_last_show_codes[user_id]
        current_time = time.time()
        elapsed_time = current_time - last_time
        remaining_time = 12 * 3600 - elapsed_time
        if elapsed_time < 12 * 3600:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            seconds = int(remaining_time % 60)
            if hours > 0:
                wait_msg = f"Wait {hours} hours and {minutes} minutes to see new codes"
            elif minutes > 0:
                wait_msg = f"Wait {minutes} minutes and {seconds} seconds to see new codes"
            else:
                wait_msg = f"Wait {seconds} seconds to see new codes"
            await message.reply(wait_msg)
            return
    account = get_account(user_id)
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    new_codes = generate_new_codes(10)
    codes_message = "**Here are 10 scratch codes for you **\n\n"
    codes_message += "You can only scratch one code from this list every 12 hours\n\n"
    for idx, (code, reward) in enumerate(new_codes, 1):
        codes_message += f"{idx}. `{code}`\n"
    codes_message += "\nUse: `scratchcode` to scratch (one code every 12 hours)"
    user_last_show_codes[user_id] = time.time()
    await message.reply(codes_message)

@app.on_message(filters.command("scratchcode", ""), group=578)
async def use_code(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    account = get_account(user_id)
    if user_id in user_last_use_any_code:
        last_time = user_last_use_any_code[user_id]
        current_time = time.time()
        elapsed_time = current_time - last_time
        remaining_time = 12 * 3600 - elapsed_time
        if elapsed_time < 12 * 3600:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            seconds = int(remaining_time % 60)
            if hours > 0:
                wait_msg = f"You can't scratch another code until after {hours} hours and {minutes} minutes"
            elif minutes > 0:
                wait_msg = f"You can't scratch another code until after {minutes} minutes and {seconds} seconds"
            else:
                wait_msg = f"You can't scratch another code until after {seconds} seconds"
            await message.reply(wait_msg)
            return
    if not account:
        await message.reply("You don't have a bank account! Use `bank`")
        return
    try:
        _, code = message.text.split()
    except:
        await message.reply("Use it like this:\nscratchcode code")
        return
    codes_data = load_codes_data()
    if code not in codes_data['active_codes']:
        await message.reply("Code is wrong or expired!")
        return
    if codes_data['active_codes'][code]['used']:
        await message.reply("This code has already been used!")
        return
    if codes_data['active_codes'][code]['expires_at'] < int(time.time()):
        await message.reply("Code has expired!")
        return
    reward = codes_data['active_codes'][code]['reward']
    data = load_data()
    data['accounts'][str(user_id)]['balance'] += reward
    codes_data['active_codes'][code]['used'] = True
    codes_data['used_codes'][code] = {
        'user_id': user_id,
        'reward': reward,
        'used_at': int(time.time())
    }
    save_data(data)
    save_codes_data(codes_data)
    user_last_use_any_code[user_id] = time.time()
    user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    await message.reply(
        f"Congratulations! {user_mention} won!\n\n"
        f"Amount: <b>({format_money(reward)})</b>\n"
        f"Your money now: <b>({format_money(data['accounts'][str(user_id)]['balance'])})</b>\n\n"
        f"You can scratch another code after 12 hours",
        parse_mode=enums.ParseMode.HTML
    )

@app.on_message(filters.command("bank", ""), group=59999)
async def bank_help(client, message):
    help_text = """
**Bank game commands**
- `create bank account` : Create a new bank account
- `myaccount` : See your account information
- `mybalance` or `mycash` : See your balance
- `hisbalance` or `hiscash` by reply : See someone else's balance

**Transfers and stocks**:
- `transfer` account_number amount : Transfer money
- `buystock` : Show the stock list
- buystock type amount to buy the stock you want
- `mystocks` : See your portfolio
- `sellstock` stock_id : Sell a specific stock
- `sellallstocks` : Sell all your stocks

**Earning money**:
- `salary` : Take your salary (every 20 minutes)
- `tip` : Free gift (every 10 minutes)
- `invest amount` : Safe investment (every 30 minutes)
- `gamble amount` : High-risk gambling
- `luck amount` : Luck game (50% chance to win)
- `wheel` : Prize every 4 hours
- `treasure` : Treasure every 6 hours

**Protection and stealing**:
- `steal` or `rob` by reply : Steal (every 10 minutes)
- `protect` : Protect your account (every hour)
- `police` or `report` by reply : Report a thief
- `bribe` by reply : Try to bribe someone

**Codes**:
- `scratch` : See available codes (every 12 hours)
- `scratchcode` : Scratch a code and win (every 12 hours)

**Tops**:
- `topmoney` : Top 20 players
- `topthieves` : Top thieves
- `medals` : Top players
"""
    await message.reply(help_text)



if __name__ == "__main__":
    app.run()    