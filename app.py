import streamlit as st
import pandas as pd
import random
import sqlite3
from datetime import date, timedelta


# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()

    # Таблица твоего профиля
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats
                 (id INTEGER PRIMARY KEY, name TEXT, streak INTEGER, last_login TEXT, xp INTEGER, crystals INTEGER)''')

    # Таблица для Лиги (все игроки)
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                 (name TEXT PRIMARY KEY, xp INTEGER)''')

    c.execute("SELECT * FROM user_stats WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO user_stats (id, name, streak, last_login, xp, crystals) VALUES (1, '', 0, '', 0, 0)")

        # Добавляем фейковых игроков в лигу при первом запуске
        bots = [("Alex", 120), ("Max", 85), ("Sophie", 150), ("Ivan", 40), ("Kate", 200)]
        for bot_name, bot_xp in bots:
            c.execute("INSERT OR IGNORE INTO leaderboard (name, xp) VALUES (?, ?)", (bot_name, bot_xp))

    conn.commit()
    conn.close()


def get_user_stats():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT name, streak, last_login, xp, crystals FROM user_stats WHERE id = 1")
    data = c.fetchone()
    conn.close()
    return data


def set_username(name):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("UPDATE user_stats SET name = ? WHERE id = 1", (name,))
    c.execute("INSERT OR REPLACE INTO leaderboard (name, xp) VALUES (?, 0)", (name,))
    conn.commit()
    conn.close()


def sync_xp_to_leaderboard(name, xp):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("UPDATE leaderboard SET xp = ? WHERE name = ?", (xp, name))
    conn.commit()
    conn.close()


def update_streak_and_xp():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT streak, last_login, xp FROM user_stats WHERE id = 1")
    streak, last_login, xp = c.fetchone()

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_login == today:
        pass
    elif last_login == yesterday:
        streak += 1
    else:
        streak = 1

    if last_login != today:
        xp += 10

    c.execute("UPDATE user_stats SET streak = ?, last_login = ?, xp = ? WHERE id = 1", (streak, today, xp))
    conn.commit()
    conn.close()


def add_rewards(xp_amount, crystal_amount):
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("UPDATE user_stats SET xp = xp + ?, crystals = crystals + ? WHERE id = 1", (xp_amount, crystal_amount))
    conn.commit()
    conn.close()


def get_leaderboard():
    conn = sqlite3.connect('questalism.db')
    c = conn.cursor()
    c.execute("SELECT name, xp FROM leaderboard ORDER BY xp DESC")
    data = c.fetchall()
    conn.close()
    return data


init_db()
user_name, streak, last_login, xp, crystals = get_user_stats()

# --- ОНБОРДИНГ ---
if not user_name:
    st.set_page_config(page_title="Questalism", page_icon="💰", layout="centered")
    st.title("💰 Добро пожаловать в Questalism!")
    st.write("Твоя мечта. Твой путь. Твои деньги.")
    st.write("---")
    st.subheader("Давай познакомимся. Как тебя зовут?")

    new_name = st.text_input("Введи своё имя:")

    if st.button("Начать путь 🚀", use_container_width=True):
        if new_name.strip():
            set_username(new_name.strip())
            st.rerun()
        else:
            st.error("Пожалуйста, введи имя.")
    st.stop()

update_streak_and_xp()
user_name, streak, last_login, xp, crystals = get_user_stats()
sync_xp_to_leaderboard(user_name, xp)  # Обновляем лигу

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

# --- ДИЗАЙН (тот же) ---
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] {display: none;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background: radial-gradient(circle at 10% 20%, #2b1055 0%, #000000 90%); background-attachment: fixed; color: white; }
    .stApp::before { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px); background-size: 30px 30px; z-index: -1; pointer-events: none; }
    h1, h2, h3, p, label, .stMarkdown { color: #ffffff !important; }
    .stButton>button { color: white !important; background-color: #6c5ce7 !important; border: 1px solid #a29bfe !important; }
    .stButton>button:hover { background-color: #a29bfe !important; color: #000000 !important; }
    .result-card { background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(255, 65, 108, 0.3); }
    .achievement { background-color: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #00ffcc !important; font-weight: bold; }
    .quest-level { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #ffcc00; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
    .hustle-box { background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border: 1px dashed #00ffcc; text-align: center; margin-top: 10px; }
    .profile-card { background: rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #6c5ce7; margin-bottom: 20px; }

    /* Стили для лиги */
    .league-row { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .league-me { background-color: rgba(108, 92, 231, 0.3); border-radius: 5px; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- СЛОВАРИ ---
# (Оставляем твои словари texts и terms, я их не трогаю для экономии места)
texts = {
    "Русский": {
        "title": "💰 Questalism", "subtitle": "Твоя мечта. Твой путь. Твои деньги.", "nav_home": "🏠 Главная",
        "nav_game": "🎮 Твой квест", "nav_knowledge": "📚 База знаний", "nav_league": "🏆 Лига", "who": "Кто ты?",
        "teen": "Подросток", "adult": "Взрослый", "age": "Сколько тебе лет?", "goal_header": "1. Твоя цель",
        "goal_input": "На что копишь?", "currency": "Валюта", "rub": "Рубли (₽)", "usd": "Доллары ($)",
        "target": "Сколько стоит?", "data_header": "2. Твои данные", "current": "Сколько есть сейчас?",
        "monthly": "**Сколько можешь откладывать в месяц?**", "custom": "Своё", "custom_input": "Введи сумму:",
        "jobs_header": "3. Твоя подработка", "choose": "Выбери", "no": "Нет", "own_job": "Своя подработка",
        "salary": "Сколько ты зарабатываешь?", "result": "🏆 Твой результат", "target_label": "Цель",
        "term_label": "Срок", "inflation_label": "С инфляцией",
        "inflation_info": "Инфляция — это подорожание денег в будущем.", "months": "мес.", "chart_month": "Месяц",
        "chart_balance": "Баланс", "you_at": "Ты на", "to_goal": "% к цели", "achievements": "🎖️ Твои ачивки",
        "quest_levels": "🛡️ Твои вехи (Этапы)", "speed_up": "🚀 Как ускорить цель", "if_more": "Если откладывать на",
        "more": "больше → срок:", "need_daily": "Нужно откладывать в день:", "wish": "Удачи! Ты справишься. 💪",
        "warning": "Введи сумму больше 0.", "goal_reached": "Ты уже накопил на эту цель! 🎉",
        "status_green": "🟢 **Реально!** Ты достигнешь цели быстро.",
        "status_yellow": "🟡 **Средне.** Придется постараться.",
        "status_red": "🔴 **Долго.** Подумай, как увеличить доход.", "next_step": "👉 **Следующий шаг:**",
        "next_step_1": "Попробуй добавить подработку, чтобы сократить срок.",
        "share_text": "Я накоплю на {goal} за {months} месяцев с Questalism! А ты сможешь? Проверь свои финансы: questalism.onrender.com",
        "hustle_btn": "Сгенерировать идею",
        "hustle_result": "Тебе подойдет: {idea}. Примерный доход: {income} {symbol}.",
        "hustles": [("Выгул собак", 5000), ("Помощь с уроками", 6000), ("Курьер", 8000), ("Стриминг", 3000),
                    ("Продажа вещей", 4000), ("Репетиторство", 10000), ("Компьютеры", 7000), ("Документы", 6000)],
        "ach1": "🎯 **Первый шаг**", "ach2": "💎 **Сберегатель**", "ach3": "🥇 **Четверть пути**",
        "ach4": "🔥 **Половина**", "ach5": "⭐ **Почти у цели**", "ach6": "🏆 **Марафонец**", "ach7": "🚀 **Спринтер**",
        "ach8": "💪 **Работяга**", "ach9": "👑 **Высокий доход**", "ach10": "🎓 **Школьник**",
        "milestone_10": "10% — Первый шаг", "milestone_25": "25% — Четверть пути", "milestone_50": "50% — Экватор",
        "milestone_75": "75% — Финиш близко", "milestone_100": "100% — Покупка!", "milestone_done": "✅ Пройдено",
        "milestone_wait": "🔒 Впереди", "why_save": "Почему важно копить", "why1": "• Свобода.", "why2": "• Мечты.",
        "why3": "• Уверенность.", "why4": "• Будущее.", "spend_less": "Как меньше тратить",
        "spend1": "• Правило 24 часов.", "spend2": "• Список покупок.", "spend3": "• Кофе дома.",
        "spend4": "• Подписки.", "spend5": "• Импульс.", "psychology": "Психология", "psy1": "• Автоматизация.",
        "psy2": "• Визуализация.", "psy3": "• Маленькие шаги.", "psy4": "• Поддержка.", "psy5": "• Прощение.",
        "dictionary": "Словарь", "feature": "💡 Совет дня", "feature_btn": "Получить совет",
        "tips": ["Начни с 100 рублей.", "Запиши цель.", "Сравни с собой.", "Отложи 10%.", "Начни сегодня."],
        "dash_hello": "Привет, {name}!", "dash_level": "Уровень", "dash_xp": "Опыт", "dash_start": "🚀 Продолжить путь",
        "dash_daily": "📅 Задания дня", "dash_daily_1": "Зайди (✅)", "dash_daily_2": "Рассчитай цель (+50 XP)",
        "dash_daily_3": "Прочитай совет", "btn_save": "💾 Сохранить (+50 XP, +10💎)"
    },
    "English": {
        "title": "💰 Questalism", "subtitle": "Your dream. Your path. Your money.", "nav_home": "🏠 Home",
        "nav_game": "🎮 Quest", "nav_knowledge": "📚 Knowledge", "nav_league": "🏆 League", "who": "Who are you?",
        "teen": "Teenager", "adult": "Adult", "age": "Age?", "goal_header": "1. Goal", "goal_input": "Saving for?",
        "currency": "Currency", "rub": "Rubles (₽)", "usd": "Dollars ($)", "target": "Cost?", "data_header": "2. Data",
        "current": "Current savings?", "monthly": "**Monthly savings?**", "custom": "Custom", "custom_input": "Amount:",
        "jobs_header": "3. Job", "choose": "Choose", "no": "None", "own_job": "Own", "salary": "Earn?",
        "result": "🏆 Result", "target_label": "Goal", "term_label": "Term", "inflation_label": "Inflation",
        "inflation_info": "Inflation is price rise.", "months": "mo.", "chart_month": "Month",
        "chart_balance": "Balance", "you_at": "You at", "to_goal": "%", "achievements": "🎖️ Achievements",
        "quest_levels": "🛡️ Milestones", "speed_up": "🚀 Speed up", "if_more": "Save", "more": "more → term:",
        "need_daily": "Daily:", "wish": "Good luck!", "warning": "Enter > 0.", "goal_reached": "Goal reached! 🎉",
        "status_green": "🟢 **Realistic!**", "status_yellow": "🟡 **Medium.**", "status_red": "🔴 **Long.**",
        "next_step": "👉 **Next:**", "next_step_1": "Add a job.",
        "share_text": "I'll save for {goal} in {months} months with Questalism! Check: questalism.onrender.com",
        "hustle_btn": "Generate idea", "hustle_result": "Try: {idea}. Income: {income} {symbol}.",
        "hustles": [("Dog walking", 5000), ("Homework", 6000), ("Courier", 8000), ("Streaming", 3000),
                    ("Selling", 4000), ("Tutor", 10000), ("PC help", 7000), ("Docs", 6000)], "ach1": "🎯 First step",
        "ach2": "💎 Saver", "ach3": "🥇 Quarter", "ach4": "🔥 Halfway", "ach5": "⭐ Almost", "ach6": "🏆 Marathoner",
        "ach7": "🚀 Sprinter", "ach8": "💪 Worker", "ach9": "👑 High income", "ach10": "🎓 Student", "milestone_10": "10%",
        "milestone_25": "25%", "milestone_50": "50%", "milestone_75": "75%", "milestone_100": "100%",
        "milestone_done": "✅ Done", "milestone_wait": "🔒 Ahead", "why_save": "Why save", "why1": "• Freedom.",
        "why2": "• Dreams.", "why3": "• Confidence.", "why4": "• Future.", "spend_less": "Spend less",
        "spend1": "• 24h rule.", "spend2": "• List.", "spend3": "• Coffee.", "spend4": "• Subscriptions.",
        "spend5": "• Impulse.", "psychology": "Psychology", "psy1": "• Automation.", "psy2": "• Visualization.",
        "psy3": "• Small steps.", "psy4": "• Support.", "psy5": "• Forgiveness.", "dictionary": "Dictionary",
        "feature": "💡 Tip", "feature_btn": "Get tip",
        "tips": ["Start with $1.", "Write goal.", "Compare to self.", "Save 10%.", "Start today."],
        "dash_hello": "Hello, {name}!", "dash_level": "Level", "dash_xp": "XP", "dash_start": "🚀 Continue",
        "dash_daily": "📅 Daily Quests", "dash_daily_1": "Log in (✅)", "dash_daily_2": "Calculate (+50 XP)",
        "dash_daily_3": "Read tip", "btn_save": "💾 Save (+50 XP, +10💎)"
    }
}

terms = {
    "Русский": {"Инфляция": "Подорожание денег.", "Вклад": "Банк платит процент.", "Акции": "Доля в компании.",
                "Облигации": "Даёшь в долг."},
    "English": {"Inflation": "Price rise.", "Deposit": "Interest.", "Stocks": "Share.", "Bonds": "Loan."}
}

# --- НАВИГАЦИЯ ---
col_lang, col_space, col_streak, col_xp = st.columns([2, 2, 1, 1])
with col_lang:
    lang = st.radio("Язык / Language", ["Русский", "English"], horizontal=True, label_visibility="collapsed")
t = texts[lang]
current_terms = terms[lang]
level = (xp // 100) + 1

with col_streak:
    st.write(f"🔥 **{streak}**")
with col_xp:
    st.write(f"⭐ **{xp} XP**")

# 4 вкладки теперь
nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    if st.button(t["nav_home"], use_container_width=True): st.session_state.page = "home"
with nav2:
    if st.button(t["nav_game"], use_container_width=True): st.session_state.page = "game"
with nav3:
    if st.button(t["nav_knowledge"], use_container_width=True): st.session_state.page = "knowledge"
with nav4:
    if st.button(t["nav_league"], use_container_width=True): st.session_state.page = "league"

if "page" not in st.session_state:
    st.session_state.page = "home"

# ==========================================
# СТРАНИЦА 0: ГЛАВНАЯ
# ==========================================
if st.session_state.page == "home":
    st.title(t["dash_hello"].format(name=user_name))
    col_prof, col_daily = st.columns([1, 1])
    with col_prof:
        st.markdown(f"""
        <div class="profile-card">
            <h2>👤 {t['dash_level']} {level}</h2>
            <p>{t['dash_xp']}: {xp}</p>
            <p>🔥 Стрик: {streak} дней</p>
            <p>💎 Кристаллы: {crystals}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button(t["dash_start"], use_container_width=True):
            st.session_state.page = "game"
            st.rerun()
    with col_daily:
        st.subheader(t["dash_daily"])
        st.write(t["dash_daily_1"])
        if st.button(t["dash_daily_2"]):
            st.session_state.page = "game"
            st.rerun()
        st.write(t["dash_daily_3"])

# ==========================================
# СТРАНИЦА ЛИГА
# ==========================================
elif st.session_state.page == "league":
    st.title("🏆 Лига")
    st.write("Соревнуйся с другими подростками! Зарабатывай XP и поднимайся в топ.")

    leaderboard_data = get_leaderboard()

    for rank, (name, p_xp) in enumerate(leaderboard_data, start=1):
        row_class = "league-me" if name == user_name else ""
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."

        st.markdown(f"""
        <div class="league-row {row_class}">
            <span>{medal} {name}</span>
            <span>⭐ {p_xp} XP</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# СТРАНИЦА 1: ИГРА (КАЛЬКУЛЯТОР)
# ==========================================
elif st.session_state.page == "game":
    # (Тут код калькулятора, я его оставил точно таким же, как в прошлый раз)
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
        goal = st.text_input(t["goal_input"], "iPhone")
    with col2:
        currency = st.selectbox(t["currency"], [t["rub"], t["usd"]])
    is_usd = (currency == t["usd"])
    symbol = "$" if is_usd else "₽"
    rate = 90 if is_usd else 1
    target = st.number_input(f"{t['target']} ({symbol})", min_value=0, value=80000 if not is_usd else 1000, step=1000)
    st.header(t["data_header"])
    current = st.number_input(f"{t['current']} ({symbol})", min_value=0, value=5000 if not is_usd else 50, step=1000)
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

    if "monthly" not in st.session_state: st.session_state.monthly = 500
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
    monthly = st.session_state.monthly

    st.header(t["jobs_header"])
    if st.button(t["hustle_btn"]):
        idea, income = random.choice(t["hustles"])
        st.markdown(
            f'<div class="hustle-box">💡 {t["hustle_result"].format(idea=idea, income=income, symbol=symbol)}</div>',
            unsafe_allow_html=True)

    job_choice = st.selectbox(t["choose"], [j[0] for j in jobs])
    base_salary = next((j[1] for j in jobs if j[0] == job_choice), 0)
    if is_usd: base_salary = base_salary / rate
    extra = 0
    if job_choice in [t["own_job"]]:
        extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=0, step=1000)
    elif job_choice != t["no"]:
        extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=int(base_salary), step=1000)

    total_monthly = monthly + extra
    st.header(t["result"])
    if target <= current:
        st.success(t["goal_reached"])
    elif total_monthly > 0:
        months = (target - current) / total_monthly
        years = months / 12
        inflation = 0.06
        real_target = target * ((1 + inflation) ** years)

        st.markdown(f"""
        <div class="result-card">
            <h2 style="margin:0;">🎯 {goal}: {target:,.0f} {symbol}</h2>
            <h3 style="margin:10px 0 0 0;">⏱️ {months:.0f} {t['months']}</h3>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t["target_label"], f"{target:,.0f} {symbol}")
        with col2:
            st.metric(t["inflation_label"], f"{real_target:,.0f} {symbol}")
        if months <= 6:
            st.success(t["status_green"])
        elif months <= 18:
            st.warning(t["status_yellow"])
        else:
            st.error(t["status_red"])

        data = []
        balance = current
        for m in range(int(months) + 1):
            data.append({t["chart_month"]: m, t["chart_balance"]: balance})
            balance += total_monthly
        df = pd.DataFrame(data)
        st.line_chart(df.set_index(t["chart_month"])[t["chart_balance"]])
        progress = min(current / target, 1.0)
        st.progress(progress)
        st.write(f"{t['you_at']} {progress * 100:.1f}{t['to_goal']}")

        st.header(t["quest_levels"])


        def milestone_status(percentage):
            return t["milestone_done"] if progress >= percentage else t["milestone_wait"]


        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_10"]}</b> ({target * 0.1:,.0f} {symbol}) — {milestone_status(0.1)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_25"]}</b> ({target * 0.25:,.0f} {symbol}) — {milestone_status(0.25)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_50"]}</b> ({target * 0.5:,.0f} {symbol}) — {milestone_status(0.5)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_75"]}</b> ({target * 0.75:,.0f} {symbol}) — {milestone_status(0.75)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_100"]}</b> ({target:,.0f} {symbol}) — {milestone_status(1.0)}</div>',
            unsafe_allow_html=True)

        st.header(t["achievements"])
        earned = []
        if progress > 0.01: earned.append(t["ach1"])
        if monthly >= 1000: earned.append(t["ach2"])
        if progress > 0.25: earned.append(t["ach3"])
        if progress > 0.5: earned.append(t["ach4"])
        if progress > 0.75: earned.append(t["ach5"])
        if years > 1: earned.append(t["ach6"])
        if months < 6: earned.append(t["ach7"])
        if extra > 0: earned.append(t["ach8"])
        if user_type == t["teen"]: earned.append(t["ach10"])
        for ach in earned: st.markdown(f'<div class="achievement">{ach}</div>', unsafe_allow_html=True)
        st.info(f"{t['next_step']} {t['next_step_1']}")

        st.write("---")
        if st.button(t["btn_save"], use_container_width=True):
            add_rewards(50, 10)
            st.balloons()
            st.success("Сохранено! +50 XP, +10 💎")
            st.rerun()

        share_msg = t["share_text"].format(goal=goal, months=f"{months:.0f}")
        st.code(share_msg, language="text")
        st.success(t["wish"])
    else:
        st.warning(t["warning"])

# ==========================================
# СТРАНИЦА 2: БАЗА ЗНАНИЙ
# ==========================================
elif st.session_state.page == "knowledge":
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
    if st.button(t["feature_btn"]):
        st.success(random.choice(t["tips"]))
