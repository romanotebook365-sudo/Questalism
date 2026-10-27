import streamlit as st
import pandas as pd
import random
import sqlite3
from datetime import date, timedelta
from streamlit_local_storage import LocalStorage
import pyperclip


# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (name TEXT PRIMARY KEY, streak INTEGER, last_login TEXT, xp INTEGER, crystals INTEGER, 
                  last_xp_date TEXT, theme TEXT, quest_calc INTEGER, quest_read INTEGER, level INTEGER, shared INTEGER,
                  max_streak INTEGER, max_level INTEGER, avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                 (name TEXT PRIMARY KEY, xp INTEGER)''')

    c.execute("SELECT COUNT(*) FROM leaderboard")
    if c.fetchone()[0] == 0:
        bots = [("Alex", 120, "🐱"), ("Max", 85, "🐶"), ("Sophie", 150, "🦊"), ("Ivan", 40, "🐻"), ("Kate", 200, "🐼")]
        for bot_name, bot_xp, bot_avatar in bots:
            c.execute("INSERT OR IGNORE INTO users (name, avatar) VALUES (?, ?)", (bot_name, bot_avatar))
            c.execute("INSERT OR IGNORE INTO leaderboard (name, xp) VALUES (?, ?)", (bot_name, bot_xp))
    conn.commit()
    conn.close()


def get_user_stats(name):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute(
        "SELECT streak, last_login, xp, crystals, last_xp_date, theme, quest_calc, quest_read, level, shared, max_streak, max_level, avatar FROM users WHERE name = ?",
        (name,))
    data = c.fetchone()
    conn.close()
    return data


def create_user(name):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (name, streak, last_login, xp, crystals, last_xp_date, theme, quest_calc, quest_read, level, shared, max_streak, max_level, avatar) VALUES (?, 0, '', 0, 0, '', 'default', 0, 0, 1, 0, 0, 1, '🦉')",
        (name,))
    c.execute("INSERT OR IGNORE INTO leaderboard (name, xp) VALUES (?, 0)", (name,))
    conn.commit()
    conn.close()


def buy_avatar(name, avatar_emoji, cost):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT crystals FROM users WHERE name = ?", (name,))
    crystals = c.fetchone()[0]
    if crystals >= cost:
        c.execute("UPDATE users SET crystals = crystals - ?, avatar = ? WHERE name = ?", (cost, avatar_emoji, name))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def update_streak_and_xp(name):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT streak, last_login, xp, level, max_streak, max_level FROM users WHERE name = ?", (name,))
    streak, last_login, xp, current_level, max_streak, max_level = c.fetchone()
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_login == today:
        pass
    elif last_login == yesterday:
        streak += 1
    else:
        streak = 1

    if last_login != today: xp += 10

    new_level = (xp // 100) + 1
    if new_level > current_level:
        crystals_bonus = 50
        c.execute("UPDATE users SET crystals = crystals + ? WHERE name = ?", (crystals_bonus, name))
        st.toast(f"🎉 Новый уровень {new_level}! Получено 50 💎", icon="🎊")

    if streak > max_streak: max_streak = streak
    if new_level > max_level: max_level = new_level

    c.execute(
        "UPDATE users SET streak = ?, last_login = ?, xp = ?, level = ?, max_streak = ?, max_level = ? WHERE name = ?",
        (streak, today, xp, new_level, max_streak, max_level, name))
    c.execute("UPDATE leaderboard SET xp = ? WHERE name = ?", (xp, name))
    conn.commit()
    conn.close()


def complete_quest(name, quest_name, reward_xp, reward_crystals):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    if quest_name == "calc":
        c.execute("UPDATE users SET quest_calc = 1, xp = xp + ?, crystals = crystals + ? WHERE name = ?",
                  (reward_xp, reward_crystals, name))
    elif quest_name == "read":
        c.execute("UPDATE users SET quest_read = 1, xp = xp + ?, crystals = crystals + ? WHERE name = ?",
                  (reward_xp, reward_crystals, name))
    elif quest_name == "share":
        c.execute("UPDATE users SET shared = 1, crystals = crystals + ? WHERE name = ?", (reward_crystals, name))

    c.execute("SELECT xp FROM users WHERE name = ?", (name,))
    new_xp = c.fetchone()[0]
    c.execute("UPDATE leaderboard SET xp = ? WHERE name = ?", (new_xp, name))
    conn.commit()
    conn.close()


def buy_theme(name, theme_id, cost):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT crystals FROM users WHERE name = ?", (name,))
    crystals = c.fetchone()[0]
    if crystals >= cost:
        c.execute("UPDATE users SET crystals = crystals - ?, theme = ? WHERE name = ?", (cost, theme_id, name))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_leaderboard():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute('''SELECT leaderboard.name, leaderboard.xp, users.avatar 
                 FROM leaderboard 
                 LEFT JOIN users ON leaderboard.name = users.name 
                 ORDER BY leaderboard.xp DESC''')
    data = c.fetchall()
    conn.close()
    return [(row[0], row[1], row[2] if row[2] else "🦉") for row in data]


init_db()

# --- СЛОВАРИ ---
texts = {
    "Русский": {
        "title": "💰 Questalism", "subtitle": "Твоя мечта. Твой путь. Твои деньги.",
        "nav_home": "🏠 Главная", "nav_game": "🎮 Твой квест", "nav_league": "🏆 Лига", "nav_shop": "🛒 Магазин",
        "nav_knowledge": "📚 База знаний",
        "who": "Кто ты?", "teen": "Подросток", "adult": "Взрослый", "age": "Сколько тебе лет?",
        "goal_header": "1. Твоя цель", "goal_input": "На что копишь?", "currency": "Валюта",
        "rub": "Рубли (₽)", "usd": "Доллары ($)", "target": "Сколько стоит?",
        "data_header": "2. Твои данные", "current": "Сколько есть сейчас?",
        "monthly": "**Сколько можешь откладывать в месяц?**", "custom": "Своё", "custom_input": "Введи сумму:",
        "jobs_header": "3. Твоя подработка", "choose": "Выбери", "no": "Нет", "own_job": "Своя подработка",
        "salary": "Сколько ты зарабатываешь?", "result": "🏆 Твой результат",
        "target_label": "Цель", "term_label": "Срок", "inflation_label": "С инфляцией",
        "inflation_info": "Инфляция — это подорожание денег в будущем.", "months": "мес.",
        "chart_month": "Месяц", "chart_balance": "Баланс", "you_at": "Ты на", "to_goal": "% к цели",
        "achievements": "🎖️ Твои ачивки", "quest_levels": "🛡️ Твои вехи (Этапы)",
        "speed_up": "🚀 Как ускорить цель", "if_more": "Если откладывать на", "more": "больше → срок:",
        "need_daily": "Нужно откладывать в день:", "wish": "Удачи! Ты справишься. 💪",
        "warning": "Введи сумму больше 0.", "goal_reached": "Ты уже накопил на эту цель! 🎉",
        "status_green": "🟢 **Реально!** Ты достигнешь цели быстро.",
        "status_yellow": "🟡 **Средне.** Придется постараться.",
        "status_red": "🔴 **Долго.** Подумай, как увеличить доход.", "next_step": "👉 **Следующий шаг:**",
        "next_step_1": "Попробуй добавить подработку, чтобы сократить срок.",
        "next_step_2": "Отлично! Теперь просто придерживайся плана.",
        "share_text": "Я накоплю на {goal} за {months} месяцев с Questalism! А ты сможешь? Проверь свои финансы: questalism-llhu.onrender.com",
        "hustle_btn": "Сгенерировать идею",
        "hustle_result": "Тебе подойдет: {idea}. Примерный доход: {income} {symbol}.",
        "hustles": [("Выгул собак", 5000), ("Помощь с уроками", 6000), ("Курьер", 8000), ("Стриминг", 3000),
                    ("Продажа вещей", 4000), ("Репетиторство", 10000), ("Компьютеры", 7000), ("Документы", 6000)],
        "ach1": "🎯 **Первый шаг** — ты начал копить.", "ach2": "💎 **Сберегатель** — откладываешь больше 1000 в месяц.",
        "ach3": "🥇 **Четверть пути** — ты прошёл 25% к цели.", "ach4": "🔥 **Половина** — ты на середине пути.",
        "ach5": "⭐ **Почти у цели** — осталось 25%.", "ach6": "🏆 **Марафонец** — твоя цель на год и больше.",
        "ach7": "🚀 **Спринтер** — ты добьешься цели меньше чем за 6 месяцев.",
        "ach8": "💪 **Работяга** — у тебя есть дополнительный доход.",
        "ach9": "👑 **Высокий доход** — ты зарабатываешь больше 10K.",
        "ach10": "🎓 **Школьник** — ты учишься и копишь одновременно.",
        "milestone_10": "10% — Первый шаг", "milestone_25": "25% — Четверть пути", "milestone_50": "50% — Экватор",
        "milestone_75": "75% — Финиш близко", "milestone_100": "100% — Покупка!", "milestone_done": "✅ Пройдено",
        "milestone_wait": "🔒 Впереди",
        "why_save": "Почему важно копить",
        "why1": "• Финансовая свобода: ты не зависишь от родителей в мелочах.",
        "why2": "• Мечты сбываются: покупка того, что давно хотел.",
        "why3": "• Уверенность: ты знаешь, что у тебя есть запас.",
        "why4": "• Будущее: привычка копить останется с тобой навсегда.",
        "spend_less": "Как меньше тратить",
        "spend1": "• Правило 24 часов: если хочешь импульсивную покупку — подожди день. Если желание не пропало — бери.",
        "spend2": "• Список покупок: иди в магазин только с готовым списком, чтобы не набрать лишнего.",
        "spend3": "• Кофе дома: делай напитки сам, это экономит тысячи рублей в месяц.",
        "spend4": "• Подписки: проверь, какими сервисами ты реально пользуешься. Остальные — отмени.",
        "spend5": "• Импульс: не покупай, когда злишься или грустишь.",
        "psychology": "Психология накоплений",
        "psy1": "• Автоматизация: откладывай деньги сразу в день, когда они пришли.",
        "psy2": "• Визуализация: повесь картинку цели на видное место.",
        "psy3": "• Маленькие шаги: лучше отложить 100 рублей, чем 0.",
        "psy4": "• Поддержка: расскажи другу о цели, он будет тебя подбадривать.",
        "psy5": "• Прощение: если потратил лишнее — не ругай себя, просто продолжай.",
        "dictionary": "Словарь", "feature": "💡 Совет дня", "feature_btn": "Получить совет",
        "tips": ["Начни с 100 рублей. Главное — начать.", "Запиши цель на бумаге.", "Сравни себя с собой вчерашним.",
                 "Отложи 10%.", "Не жди понедельника."],
        "dash_hello": "Привет, {name}!", "dash_level": "Уровень", "dash_xp": "⭐ Опыт",
        "dash_daily": "📅 Задания дня", "dash_daily_1": "Зайди (✅)", "dash_daily_2": "Рассчитай цель (+50 XP)",
        "dash_daily_3": "Прочитай совет (+20 XP)",
        "streak_label": "Стрик", "days": "дней", "crystals_label": "Кристаллы",
        "league_title": "🏆 Лига", "league_desc": "Соревнуйся с другими пользователями!",
        "shop_title": "🛒 Магазин", "shop_desc": "Трать кристаллы на улучшение профиля.",
        "theme_default": "Стандартная", "theme_neon": "Неон", "theme_light": "Светлая", "theme_space": "Космос",
        "cost_label": "Стоимость: {cost} 💎",
        "buy_btn": "Купить за {cost} 💎", "owned_btn": "Уже куплено ✅", "not_enough": "Не хватает кристаллов!",
        "btn_next_game": "Идём к цели ➡️", "btn_next_knowledge": "Идём в Базу знаний ➡️",
        "btn_next_league": "Идём в Лигу ➡️", "btn_next_shop": "Идём в Магазин ➡️",
        "btn_next_home": "Идём на Главную ➡️",
        "quest_calc_done": "Квест 'Рассчитать цель' выполнен! +50 XP, +10 💎",
        "quest_read_done": "Квест 'Прочитать совет' выполнен! +20 XP, +5 💎",
        "btn_claim_calc": "🎯 Завершить квест", "btn_claim_read": "💡 Получить совет",
        "btn_share_reward": "📲 Скопировать и получить 20 💎", "share_reward_done": "✅ Награда за рекламу получена!",
        "records_title": "🏅 Личные рекорды", "rec_streak": "Максимальный стрик", "rec_level": "Максимальный уровень",
        "ad_text": "Скопируй текст ниже и отправь другу:",
        "chest_title": "🎁 Сундук за 7 дней", "chest_desc": "Заходи 7 дней подряд, чтобы получить 100 💎",
        "level_progress": "Прогресс до следующего уровня", "copy_btn": "📋 Скопировать текст",
        "copied": "✅ Скопировано!",
        "view_profile": "Посмотреть профиль соперника",
        "avatar_shop": "🦉 Аватарки", "avatar_desc": "Смени своего совенка!",
        "theme_shop": "🎨 Темы оформления", "theme_desc": "Смени цвета сайта!",
        "quest_map": "🗺️ Твой путь", "q_step1": "Поставить цель", "q_step2": "Рассчитать срок",
        "q_step3": "Прочитать совет", "q_step4": "Поделиться"
    },
    "English": {
        "title": "💰 Questalism", "subtitle": "Your dream. Your path. Your money.",
        "nav_home": "🏠 Home", "nav_game": "🎮 Quest", "nav_league": "🏆 League", "nav_shop": "🛒 Shop",
        "nav_knowledge": "📚 Knowledge",
        "who": "Who are you?", "teen": "Teenager", "adult": "Adult", "age": "Age?",
        "goal_header": "1. Goal", "goal_input": "Saving for?", "currency": "Currency",
        "rub": "Rubles (₽)", "usd": "Dollars ($)", "target": "Cost?",
        "data_header": "2. Data", "current": "Current savings?",
        "monthly": "**Monthly savings?**", "custom": "Custom", "custom_input": "Amount:",
        "jobs_header": "3. Job", "choose": "Choose", "no": "None", "own_job": "Own",
        "salary": "Earn?", "result": "🏆 Result",
        "target_label": "Goal", "term_label": "Term", "inflation_label": "Inflation",
        "inflation_info": "Inflation is price rise.", "months": "mo.",
        "chart_month": "Month", "chart_balance": "Balance", "you_at": "You at", "to_goal": "%",
        "achievements": "🎖️ Achievements", "quest_levels": "🛡️ Milestones",
        "speed_up": "🚀 Speed up", "if_more": "Save", "more": "more → term:",
        "need_daily": "Daily:", "wish": "Good luck!",
        "warning": "Enter > 0.", "goal_reached": "Goal reached! 🎉",
        "status_green": "🟢 **Realistic!**", "status_yellow": "🟡 **Medium.**", "status_red": "🔴 **Long.**",
        "next_step": "👉 **Next:**", "next_step_1": "Add a job to speed up.",
        "next_step_2": "Great! Just stick to the plan.",
        "share_text": "I'll save for {goal} in {months} months with Questalism! Check: questalism-llhu.onrender.com",
        "hustle_btn": "Generate idea", "hustle_result": "Try: {idea}. Income: {income} {symbol}.",
        "hustles": [("Dog walking", 5000), ("Homework", 6000), ("Courier", 8000), ("Streaming", 3000),
                    ("Selling", 4000), ("Tutor", 10000), ("PC help", 7000), ("Docs", 6000)],
        "ach1": "🎯 **First step** — started saving.", "ach2": "💎 **Saver** — save > 1000/mo.",
        "ach3": "🥇 **Quarter** — 25% done.",
        "ach4": "🔥 **Halfway** — 50% done.", "ach5": "⭐ **Almost** — 75% done.", "ach6": "🏆 **Marathoner** — > 1 year.",
        "ach7": "🚀 **Sprinter** — you will reach your goal in less than 6 months.",
        "ach8": "💪 **Worker** — extra income.", "ach9": "👑 **High income** — > 10K.",
        "ach10": "🎓 **Student** — study & save.",
        "milestone_10": "10%", "milestone_25": "25%", "milestone_50": "50%",
        "milestone_75": "75%", "milestone_100": "100%", "milestone_done": "✅ Done", "milestone_wait": "🔒 Ahead",
        "why_save": "Why save",
        "why1": "• Financial freedom: you don't depend on parents.",
        "why2": "• Dreams come true: buying what you wanted.",
        "why3": "• Confidence: you know you have a backup.",
        "why4": "• Future: the habit of saving will stay with you forever.",
        "spend_less": "Spend less",
        "spend1": "• 24-hour rule: wait a day before an impulse buy.",
        "spend2": "• Shopping list: don't go shopping without it.",
        "spend3": "• Coffee at home: make drinks yourself.",
        "spend4": "• Subscriptions: check what you really use.",
        "spend5": "• Impulse: don't buy when you are angry or sad.",
        "psychology": "Psychology of saving",
        "psy1": "• Automation: save money immediately when it arrives.",
        "psy2": "• Visualization: put a picture of your goal in a visible place.",
        "psy3": "• Small steps: better to save 100 rubles than 0.",
        "psy4": "• Support: tell a friend about your goal.",
        "psy5": "• Forgiveness: if you overspent, don't scold yourself.",
        "dictionary": "Dictionary", "feature": "💡 Tip", "feature_btn": "Get tip",
        "tips": ["Start with $1.", "Write goal.", "Compare to self.", "Save 10%.", "Start today."],
        "dash_hello": "Hello, {name}!", "dash_level": "Level", "dash_xp": "⭐ XP",
        "dash_daily": "📅 Daily Quests", "dash_daily_1": "Log in (✅)", "dash_daily_2": "Calculate (+50 XP)",
        "dash_daily_3": "Read tip (+20 XP)",
        "streak_label": "Streak", "days": "days", "crystals_label": "Crystals",
        "league_title": "🏆 League", "league_desc": "Compete with other users!",
        "shop_title": "🛒 Shop", "shop_desc": "Spend crystals to upgrade your profile.",
        "theme_default": "Default", "theme_neon": "Neon", "theme_light": "Light", "theme_space": "Space",
        "cost_label": "Cost: {cost} 💎",
        "buy_btn": "Buy for {cost} 💎", "owned_btn": "Owned ✅", "not_enough": "Not enough crystals!",
        "btn_next_game": "Go to Quest ➡️", "btn_next_knowledge": "Go to Knowledge ➡️",
        "btn_next_league": "Go to League ➡️", "btn_next_shop": "Go to Shop ➡️", "btn_next_home": "Go to Home ➡️",
        "quest_calc_done": "Quest 'Calculate' completed! +50 XP, +10 💎",
        "quest_read_done": "Quest 'Read tip' completed! +20 XP, +5 💎",
        "btn_claim_calc": "🎯 Complete quest", "btn_claim_read": "💡 Get tip",
        "btn_share_reward": "📲 Copy and get 20 💎", "share_reward_done": "✅ Ad reward received!",
        "records_title": "🏅 Personal Records", "rec_streak": "Max Streak", "rec_level": "Max Level",
        "ad_text": "Copy the text below and send it to a friend:",
        "chest_title": "🎁 7-Day Chest", "chest_desc": "Log in 7 days in a row to get 100 💎",
        "level_progress": "Progress to next level", "copy_btn": "📋 Copy text", "copied": "✅ Copied!",
        "view_profile": "View rival's profile",
        "avatar_shop": "🦉 Avatars", "avatar_desc": "Change your owl!",
        "theme_shop": "🎨 Themes", "theme_desc": "Change site colors!",
        "quest_map": "🗺️ Your Path", "q_step1": "Set a goal", "q_step2": "Calculate term", "q_step3": "Read a tip",
        "q_step4": "Share result"
    }
}

terms = {
    "Русский": {"Инфляция": "Это когда деньги обесцениваются, а товары дорожают.",
                "Вклад": "Ты даешь банку деньги, а он платит тебе процент."},
    "English": {"Inflation": "Money loses value, prices rise.",
                "Deposit": "You give money to the bank, they pay interest."}
}

# --- ПАМЯТЬ БРАУЗЕРА ---
localS = LocalStorage()
saved_name = localS.getItem("questalism_user")
saved_lang = localS.getItem("questalism_lang")

if saved_name is None:
    user_name = ""
else:
    user_name = saved_name

if saved_lang == "English":
    lang_index = 1
else:
    lang_index = 0

# --- ОНБОРДИНГ ---
if not user_name:
    st.set_page_config(page_title="Questalism", page_icon="💰", layout="centered")
    st.title("💰 Questalism")
    st.write("---")
    ob_lang = st.radio("Язык / Language", ["Русский", "English"], horizontal=True)

    st.subheader(
        "Давай познакомимся. Как тебя зовут?" if ob_lang == "Русский" else "Let's get acquainted. What's your name?")
    new_name = st.text_input("Введи своё имя:" if ob_lang == "Русский" else "Enter your name:")

    if st.button("Начать путь 🚀" if ob_lang == "Русский" else "Start 🚀", use_container_width=True):
        if new_name.strip():
            create_user(new_name.strip())
            localS.setItem("questalism_user", new_name.strip(), key="save_user_1")
            localS.setItem("questalism_lang", ob_lang, key="save_lang_1")
            st.rerun()
        else:
            st.error("Введи имя!" if ob_lang == "Русский" else "Enter name!")
    st.stop()

# Данные
stats = get_user_stats(user_name)
if stats is None:
    create_user(user_name)
    stats = get_user_stats(user_name)

streak, last_login, xp, crystals, last_xp_date, current_theme, quest_calc, quest_read, level, shared, max_streak, max_level, current_avatar = stats
update_streak_and_xp(user_name)
streak, last_login, xp, crystals, last_xp_date, current_theme, quest_calc, quest_read, level, shared, max_streak, max_level, current_avatar = get_user_stats(
    user_name)

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

# --- ДИЗАЙН ---
if current_theme == "neon":
    bg_css = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
    btn_color = "#ff007f"
elif current_theme == "light":
    bg_css = "linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)"
    btn_color = "#4a90e2"
elif current_theme == "space":
    bg_css = "radial-gradient(circle, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%)"
    btn_color = "#2a2a72"
else:
    bg_css = "radial-gradient(circle at 10% 20%, #2b1055 0%, #000000 90%)"
    btn_color = "#6c5ce7"

text_color = "#000000" if current_theme == "light" else "#ffffff"

st.markdown(
    f"""
    <style>
    [data-testid="collapsedControl"] {{display: none;}}
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{ background: {bg_css}; background-attachment: fixed; color: {text_color}; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: {text_color} !important; }}
    .stButton>button {{ color: white !important; background-color: {btn_color} !important; border: 1px solid {btn_color} !important; }}
    .stButton>button:hover {{ opacity: 0.8; }}
    .result-card {{ background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); color: white; }}
    .achievement {{ background-color: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #00ffcc !important; font-weight: bold; }}
    .quest-level {{ background: rgba(128, 128, 128, 0.2); border-left: 5px solid #ffcc00; padding: 10px; margin-bottom: 10px; border-radius: 5px; color: {text_color}; }}
    .hustle-box {{ background: rgba(128, 128, 128, 0.2); padding: 15px; border-radius: 10px; border: 1px dashed #00ffcc; text-align: center; margin-top: 10px; }}
    .profile-card {{ background: rgba(128, 128, 128, 0.2); border-radius: 15px; padding: 20px; text-align: center; border: 1px solid {btn_color}; margin-bottom: 20px; }}
    .league-row {{ display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.3); color: {text_color}; }}
    .league-me {{ background-color: rgba(108, 92, 231, 0.3); border-radius: 5px; font-weight: bold; }}
    .shop-item {{ background: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid {btn_color}; margin-bottom: 10px; }}
    .chest-box {{ background: rgba(255, 215, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ffd700; margin-top: 10px; color: {text_color}; }}
    .quest-step {{ background: rgba(128, 128, 128, 0.2); border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px; font-weight: bold; border: 2px solid {btn_color}; font-size: 18px; position: relative; }}
    .quest-step-done {{ background: rgba(0, 255, 204, 0.2); border: 2px solid #00ffcc; color: #00ffcc; }}
    .quest-line {{ text-align: center; font-size: 24px; margin-bottom: 15px; color: {btn_color}; }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- НАВИГАЦИЯ ---
col_lang, col_space, col_streak, col_xp, col_cryst = st.columns([2, 1, 1, 1, 1])
with col_lang:
    lang = st.radio("Язык / Language", ["Русский", "English"], index=lang_index, horizontal=True,
                    label_visibility="collapsed")
t = texts[lang]
current_terms = terms[lang]

with col_streak: st.write(f"🔥 **{streak}**")
with col_xp: st.write(f"⭐ **{xp} XP**")
with col_cryst: st.write(f"💎 **{crystals}**")

nav1, nav2, nav3, nav4, nav5 = st.columns(5)
with nav1:
    if st.button(t["nav_home"], use_container_width=True): st.session_state.page = "home"
with nav2:
    if st.button(t["nav_game"], use_container_width=True): st.session_state.page = "game"
with nav3:
    if st.button(t["nav_league"], use_container_width=True): st.session_state.page = "league"
with nav4:
    if st.button(t["nav_shop"], use_container_width=True): st.session_state.page = "shop"
with nav5:
    if st.button(t["nav_knowledge"], use_container_width=True): st.session_state.page = "knowledge"

if "page" not in st.session_state: st.session_state.page = "home"

# ==========================================
# СТРАНИЦА 0: ГЛАВНАЯ
# ==========================================
if st.session_state.page == "home":
    st.title(t["dash_hello"].format(name=user_name))
    col_prof, col_daily = st.columns([1, 1])
    with col_prof:
        st.markdown(f"""
        <div class="profile-card">
            <div style="font-size: 50px; margin-bottom: 10px;">{current_avatar}</div>
            <h2>👤 {t['dash_level']} {level}</h2>
            <p>{t['dash_xp']}: {xp}</p>
            <p>🔥 {t['streak_label']}: {streak} {t['days']}</p>
            <p>💎 {t['crystals_label']}: {crystals}</p>
        </div>
        """, unsafe_allow_html=True)

        xp_for_next = (level * 100) - xp
        st.write(f"{t['level_progress']}: {xp % 100} / 100")
        st.progress((xp % 100) / 100)

        st.markdown(f"""
        <div class="chest-box">
            <b>{t['chest_title']}</b><br>
            {t['chest_desc']}<br>
            <small>Стрик: {streak} / 7</small>
        </div>
        """, unsafe_allow_html=True)

    with col_daily:
        st.subheader(t["quest_map"])

        if quest_calc == 0:
            st.markdown(f'<div class="quest-step">1️⃣ {t["q_step1"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quest-line">⬇️</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quest-step">2️⃣ {t["q_step2"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="quest-step quest-step-done">✅ {t["q_step1"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quest-line">⬇️</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quest-step quest-step-done">✅ {t["q_step2"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="quest-line">⬇️</div>', unsafe_allow_html=True)

        if quest_read == 0:
            st.markdown(f'<div class="quest-step">3️⃣ {t["q_step3"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="quest-step quest-step-done">✅ {t["q_step3"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="quest-line">⬇️</div>', unsafe_allow_html=True)

        if shared == 0:
            st.markdown(f'<div class="quest-step">4️⃣ {t["q_step4"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="quest-step quest-step-done">✅ {t["q_step4"]}</div>', unsafe_allow_html=True)

    st.write("---")
    if st.button(t["btn_next_game"], use_container_width=True):
        st.session_state.page = "game"
        st.rerun()

# ==========================================
# СТРАНИЦА ЛИГА
# ==========================================
elif st.session_state.page == "league":
    st.title(t["league_title"])
    st.write(t["league_desc"])

    all_players = get_leaderboard()
    player_names = [p[0] for p in all_players if p[0] != user_name]

    st.write(f"**{t['view_profile']}**")
    selected_player = st.selectbox("", player_names, label_visibility="collapsed")

    if selected_player:
        if selected_player in ["Alex", "Max", "Sophie", "Ivan", "Kate"]:
            bot_stats = {"Alex": (5, 120, 50, 12, 3, "🐱"), "Max": (2, 85, 20, 5, 2, "🐶"),
                         "Sophie": (7, 150, 120, 20, 4, "🦊"), "Ivan": (1, 40, 10, 2, 1, "🐻"),
                         "Kate": (10, 200, 300, 25, 5, "🐼")}
            p_streak, p_xp, p_crystals, p_max_streak, p_max_level, p_avatar = bot_stats[selected_player]
            st.info(
                f"**{selected_player}** {p_avatar} | 🔥 {p_streak} {t['days']} | 💎 {p_crystals} | ⭐ {p_xp} XP | 🏆 Рекорд: {p_max_streak} дней")
        else:
            p_stats = get_user_stats(selected_player)
            if p_stats:
                p_streak, _, p_xp, p_crystals, _, _, _, _, _, _, p_max_streak, p_max_level, p_avatar = p_stats
                st.info(
                    f"**{selected_player}** {p_avatar} | 🔥 {p_streak} {t['days']} | 💎 {p_crystals} | ⭐ {p_xp} XP | 🏆 Рекорд: {p_max_streak} дней")

    st.write("---")

    for rank, (name, p_xp, p_avatar) in enumerate(all_players, start=1):
        row_class = "league-me" if name == user_name else ""
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."

        st.markdown(f"""
        <div class="league-row {row_class}">
            <span>{medal} {p_avatar} {name}</span>
            <span>⭐ {p_xp} XP</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    if st.button(t["btn_next_shop"], use_container_width=True):
        st.session_state.page = "shop"
        st.rerun()

# ==========================================
# СТРАНИЦА МАГАЗИН
# ==========================================
elif st.session_state.page == "shop":
    st.title(t["shop_title"])
    st.write(t["shop_desc"])

    st.subheader(t["avatar_shop"])
    st.write(t["avatar_desc"])

    avatars = [("🦉", 0), ("🐱", 30), ("🐶", 30), ("🦊", 50), ("🐼", 50), ("🐸", 100)]
    cols = st.columns(3)
    for i, (av_emoji, cost) in enumerate(avatars):
        with cols[i % 3]:
            if current_avatar == av_emoji:
                st.button(f"{av_emoji} {t['owned_btn']}", key=f"av_{av_emoji}", disabled=True, use_container_width=True)
            else:
                if st.button(f"{av_emoji} {t['buy_btn'].format(cost=cost)}", key=f"av_{av_emoji}",
                             use_container_width=True):
                    if buy_avatar(user_name, av_emoji, cost):
                        st.success("Куплено!" if lang == "Русский" else "Purchased!")
                        st.rerun()
                    else:
                        st.error(t["not_enough"])

    st.write("---")
    st.subheader(t["theme_shop"])
    st.write(t["theme_desc"])

    col1, col2, col3 = st.columns(3)
    themes = [("light", t["theme_light"], 35), ("neon", t["theme_neon"], 50), ("space", t["theme_space"], 100)]

    for i, (theme_id, theme_name, cost) in enumerate(themes):
        col = [col1, col2, col3][i]
        with col:
            st.markdown(f"""
            <div class="shop-item">
                <h3>{theme_name}</h3>
                <p>{t['cost_label'].format(cost=cost)}</p>
            </div>
            """, unsafe_allow_html=True)
            if current_theme == theme_id:
                st.button(t["owned_btn"], key=f"btn_{theme_id}", disabled=True, use_container_width=True)
            else:
                if st.button(t["buy_btn"].format(cost=cost), key=f"btn_{theme_id}", use_container_width=True):
                    if buy_theme(user_name, theme_id, cost):
                        st.success("Куплено!" if lang == "Русский" else "Purchased!")
                        st.rerun()
                    else:
                        st.error(t["not_enough"])

    st.write("---")
    if st.button(t["btn_next_knowledge"], use_container_width=True):
        st.session_state.page = "knowledge"
        st.rerun()

# ==========================================
# СТРАНИЦА 1: ИГРА
# ==========================================
elif st.session_state.page == "game":
    if "goal" not in st.session_state: st.session_state.goal = "iPhone"
    if "target" not in st.session_state: st.session_state.target = 80000
    if "current" not in st.session_state: st.session_state.current = 5000
    if "monthly" not in st.session_state: st.session_state.monthly = 500
    if "extra" not in st.session_state: st.session_state.extra = 0

    user_type = st.radio(t["who"], [t["teen"], t["adult"]], horizontal=True)
    if lang == "Русский":
        if user_type == t["teen"]:
            jobs = [("Нет", 0), ("Промоутер", 3000), ("Курьер", 8000), ("Репетитор", 10000), ("Официант", 12000),
                    ("Фриланс", 15000), ("Мойка машин", 7000), ("Выгул собак", 5000), ("Помощь с уроками", 6000),
                    ("Продажа вещей", 4000), ("Стриминг", 3000), ("Своя подработка", 0)]
        else:
            jobs = [("Нет", 0), ("Врач", 80000), ("Учитель", 50000), ("Инженер", 70000), ("Программист", 100000),
                    ("Менеджер", 60000), ("Дизайнер", 65000), ("Маркетолог", 55000), ("Бухгалтер", 50000),
                    ("Юрист", 90000), ("Своя работа", 0)]
    else:
        if user_type == t["teen"]:
            jobs = [("None", 0), ("Promoter", 3000), ("Courier", 8000), ("Tutor", 10000), ("Waiter", 12000),
                    ("Freelance", 15000), ("Car wash", 7000), ("Dog walking", 5000), ("Homework help", 6000),
                    ("Selling stuff", 4000), ("Streaming", 3000), ("Own part-time job", 0)]
        else:
            jobs = [("None", 0), ("Doctor", 80000), ("Teacher", 50000), ("Engineer", 70000), ("Programmer", 100000),
                    ("Manager", 60000), ("Designer", 65000), ("Marketer", 55000), ("Accountant", 50000),
                    ("Lawyer", 90000), ("Own work", 0)]

    st.header(t["goal_header"])
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.goal = st.text_input(t["goal_input"], st.session_state.goal)
    with col2:
        currency = st.selectbox(t["currency"], [t["rub"], t["usd"]])
    is_usd = (currency == t["usd"])
    symbol = "$" if is_usd else "₽"
    rate = 90 if is_usd else 1

    st.session_state.target = st.number_input(f"{t['target']} ({symbol})", min_value=0, value=st.session_state.target,
                                              step=1000)

    st.header(t["data_header"])
    st.session_state.current = st.number_input(f"{t['current']} ({symbol})", min_value=0,
                                               value=st.session_state.current, step=1000)
    st.write(t["monthly"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        b0 = st.button("100")
    with col2:
        b1 = st.button("500")
    with col3:
        b2 = st.button("1000")
    with col4:
        b3 = st.button("2000")
    col5, col6, col7 = st.columns(3)
    with col5:
        b4 = st.button("3000")
    with col6:
        b5 = st.button("5000")
    with col7:
        b6 = st.button(t["custom"])

    if "custom_mode" not in st.session_state: st.session_state.custom_mode = False

    if b0: st.session_state.monthly, st.session_state.custom_mode = 100, False
    if b1: st.session_state.monthly, st.session_state.custom_mode = 500, False
    if b2: st.session_state.monthly, st.session_state.custom_mode = 1000, False
    if b3: st.session_state.monthly, st.session_state.custom_mode = 2000, False
    if b4: st.session_state.monthly, st.session_state.custom_mode = 3000, False
    if b5: st.session_state.monthly, st.session_state.custom_mode = 5000, False
    if b6: st.session_state.custom_mode = True

    if st.session_state.custom_mode:
        custom = st.number_input(t["custom_input"], min_value=1, value=st.session_state.monthly, step=100)
        st.session_state.monthly = custom

    st.header(t["jobs_header"])
    if st.button(t["hustle_btn"]):
        idea, income = random.choice(t["hustles"])
        st.markdown(
            f'<div class="hustle-box">💡 {t["hustle_result"].format(idea=idea, income=income, symbol=symbol)}</div>',
            unsafe_allow_html=True)

    job_choice = st.selectbox(t["choose"], [j[0] for j in jobs])
    base_salary = next((j[1] for j in jobs if j[0] == job_choice), 0)
    if is_usd: base_salary = base_salary / rate

    if job_choice in [t["own_job"]]:
        st.session_state.extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=st.session_state.extra,
                                                 step=1000)
    elif job_choice != t["no"]:
        st.session_state.extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=int(base_salary),
                                                 step=1000)
    else:
        st.session_state.extra = 0

    total_monthly = st.session_state.monthly + st.session_state.extra
    st.header(t["result"])

    if st.session_state.target <= st.session_state.current:
        st.success(t["goal_reached"])
    elif total_monthly > 0:
        months = (st.session_state.target - st.session_state.current) / total_monthly
        years = months / 12
        inflation = 0.06
        real_target = st.session_state.target * ((1 + inflation) ** years)

        st.markdown(f"""
        <div class="result-card">
            <h2 style="margin:0;">🎯 {st.session_state.goal}: {st.session_state.target:,.0f} {symbol}</h2>
            <h3 style="margin:10px 0 0 0;">⏱️ {months:.0f} {t['months']}</h3>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t["target_label"], f"{st.session_state.target:,.0f} {symbol}")
        with col2:
            st.metric(t["inflation_label"], f"{real_target:,.0f} {symbol}")
        if months <= 6:
            st.success(t["status_green"])
        elif months <= 18:
            st.warning(t["status_yellow"])
        else:
            st.error(t["status_red"])

        data = []
        balance = st.session_state.current
        for m in range(int(months) + 1):
            data.append({t["chart_month"]: m, t["chart_balance"]: balance})
            balance += total_monthly
        df = pd.DataFrame(data)
        st.line_chart(df.set_index(t["chart_month"])[t["chart_balance"]])
        progress = min(st.session_state.current / st.session_state.target, 1.0)
        st.progress(progress)
        st.write(f"{t['you_at']} {progress * 100:.1f}{t['to_goal']}")

        st.header(t["quest_levels"])


        def milestone_status(percentage):
            return t["milestone_done"] if progress >= percentage else t["milestone_wait"]


        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_10"]}</b> ({st.session_state.target * 0.1:,.0f} {symbol}) — {milestone_status(0.1)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_25"]}</b> ({st.session_state.target * 0.25:,.0f} {symbol}) — {milestone_status(0.25)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_50"]}</b> ({st.session_state.target * 0.5:,.0f} {symbol}) — {milestone_status(0.5)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_75"]}</b> ({st.session_state.target * 0.75:,.0f} {symbol}) — {milestone_status(0.75)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_100"]}</b> ({st.session_state.target:,.0f} {symbol}) — {milestone_status(1.0)}</div>',
            unsafe_allow_html=True)

        st.header(t["achievements"])
        earned = []
        if progress > 0.01: earned.append(t["ach1"])
        if st.session_state.monthly >= 1000: earned.append(t["ach2"])
        if progress > 0.25: earned.append(t["ach3"])
        if progress > 0.5: earned.append(t["ach4"])
        if progress > 0.75: earned.append(t["ach5"])
        if years > 1: earned.append(t["ach6"])
        if months < 6: earned.append(t["ach7"])
        if st.session_state.extra > 0: earned.append(t["ach8"])
        if user_type == t["teen"]: earned.append(t["ach10"])
        for ach in earned: st.markdown(f'<div class="achievement">{ach}</div>', unsafe_allow_html=True)

        if st.session_state.extra == 0:
            st.info(f"{t['next_step']} {t['next_step_1']}")
        else:
            st.success(f"{t['next_step']} {t['next_step_2']}")

        st.write("---")

        if quest_calc == 1:
            st.success(t["quest_calc_done"])
        else:
            if st.button(t["btn_claim_calc"], use_container_width=True):
                complete_quest(user_name, "calc", 50, 10)
                st.balloons()
                st.rerun()

        st.write("---")

        st.write(t["ad_text"])
        share_msg = t["share_text"].format(goal=st.session_state.goal, months=f"{months:.0f}")
        st.text_area("Текст для копирования", value=share_msg, height=100, label_visibility="collapsed")

        if st.button(t["copy_btn"], use_container_width=True):
            try:
                pyperclip.copy(share_msg)
                st.success(t["copied"])
            except:
                st.error("Не удалось скопировать.")

        if shared == 1:
            st.success(t["share_reward_done"])
        else:
            if st.button(t["btn_share_reward"], use_container_width=True):
                complete_quest(user_name, "share", 0, 20)
                st.success("+20 💎")
                st.rerun()

        st.success(t["wish"])
    else:
        st.warning(t["warning"])

    st.write("---")
    if st.button(t["btn_next_league"], use_container_width=True):
        st.session_state.page = "league"
        st.rerun()

# ==========================================
# СТРАНИЦА 2: БАЗА ЗНАНИЙ
# ==========================================
elif st.session_state.page == "knowledge":
    if "current_tip" not in st.session_state:
        st.session_state.current_tip = None

    st.header(t["speed_up"])
    st.info(
        "Введи данные в разделе 'Твой квест', чтобы увидеть персональные расчеты." if lang == "Русский" else "Enter data in 'Your Quest' to see personalized calculations.")
    st.divider()
    st.header(t["why_save"])
    st.write(t["why1"]);
    st.write(t["why2"]);
    st.write(t["why3"]);
    st.write(t["why4"])
    st.header(t["spend_less"])
    st.write(t["spend1"]);
    st.write(t["spend2"]);
    st.write(t["spend3"]);
    st.write(t["spend4"]);
    st.write(t["spend5"])
    st.header(t["psychology"])
    st.write(t["psy1"]);
    st.write(t["psy2"]);
    st.write(t["psy3"]);
    st.write(t["psy4"]);
    st.write(t["psy5"])
    st.header(t["dictionary"])
    for term, definition in current_terms.items():
        st.write(f"**{term}** — {definition}")
    st.divider()
    st.header(t["feature"])

    if quest_read == 1:
        st.success(t["quest_read_done"])
        if st.session_state.current_tip:
            st.success(f"💡 {st.session_state.current_tip}")
    else:
        if st.button(t["btn_claim_read"]):
            st.session_state.current_tip = random.choice(t["tips"])
            complete_quest(user_name, "read", 20, 5)
            st.balloons()
            st.rerun()

        if st.session_state.current_tip:
            st.success(f"💡 {st.session_state.current_tip}")

    st.write("---")
    if st.button(t["btn_next_home"], use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
