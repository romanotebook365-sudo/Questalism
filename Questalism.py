import streamlit as st
import pandas as pd

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

# --- ФОН ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2070&auto=format&fit=crop&sat=-100");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        z-index: -1;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💰 Questalism")
st.write("Твоя мечта. Твой путь. Твои деньги.")

# --- 1. КТО ТЫ ---
user_type = st.radio("Кто ты?", ["Подросток", "Взрослый"])

if user_type == "Подросток":
    age = st.slider("Сколько тебе лет?", 13, 17, 15)
    jobs = [
        ("Нет", 0), ("Промоутер", 3000), ("Курьер", 8000),
        ("Репетитор", 10000), ("Официант", 12000), ("Фриланс", 15000),
        ("Мойка машин", 7000), ("Выгул собак", 5000),
        ("Помощь с уроками", 6000), ("Продажа вещей", 4000),
        ("Стриминг", 3000), ("Своя подработка", 0),
    ]
    alternatives = [
        ("Найди подработку", "Дополнительный доход ускорит цель."),
        ("Трать меньше", "Меньше трат — больше накоплений."),
        ("Положи на вклад", "Банк платит процент. Деньги работают."),
        ("Продай ненужное", "Старые вещи — это деньги."),
    ]
    terms = {
        "Инфляция": "Подорожание денег в будущем. Через год та же цель будет стоить дороже.",
        "Вклад": "Ты кладёшь деньги в банк. Банк платит процент. Деньги работают.",
    }
else:
    age = st.slider("Сколько тебе лет?", 18, 60, 30)
    jobs = [
        ("Нет", 0), ("Врач", 80000), ("Учитель", 50000),
        ("Инженер", 70000), ("Программист", 100000), ("Менеджер", 60000),
        ("Дизайнер", 65000), ("Маркетолог", 55000), ("Бухгалтер", 50000),
        ("Юрист", 90000), ("Своя работа", 0),
    ]
    alternatives = [
        ("Откладывай больше", "Увеличь сумму — срок сократится."),
        ("Трать меньше", "Меньше трат — больше накоплений."),
        ("Вклад", "Банк платит процент. Безопасно."),
        ("Инвестиции", "Акции, облигации. Долгосрочно."),
        ("Автоматизация", "Откладывай сразу при доходе."),
    ]
    terms = {
        "Инфляция": "Подорожание денег. Через год та же цель будет стоить дороже.",
        "Вклад": "Ты кладёшь деньги в банк. Банк платит процент.",
        "Акции": "Доля в компании. Растёт компания — растут деньги.",
        "Облигации": "Ты даёшь в долг. Тебе платят процент.",
    }

# --- 2. ЦЕЛЬ ---
st.header("1. Твоя цель")
col1, col2 = st.columns(2)
with col1:
    goal = st.text_input("На что копишь?", "iPhone")
with col2:
    currency = st.selectbox("Валюта", ["Рубли (₽)", "Доллары ($)"])

symbol = "₽" if currency == "Рубли (₽)" else "$"
target = st.number_input(f"Сколько стоит? ({symbol})", min_value=0, value=80000, step=1000)

# --- 3. ДАННЫЕ ---
st.header("2. Твои данные")
current = st.number_input(f"Сколько есть сейчас? ({symbol})", min_value=0, value=5000, step=1000)

st.write("Сколько можешь откладывать в месяц?")

col1, col2, col3, col4 = st.columns(4)
with col1: b0 = st.button("100")
with col2: b1 = st.button("500")
with col3: b2 = st.button("1000")
with col4: b3 = st.button("2000")

col5, col6, col7 = st.columns(3)
with col5: b4 = st.button("3000")
with col6: b5 = st.button("5000")
with col7: b6 = st.button("Своё")

if "monthly" not in st.session_state:
    st.session_state.monthly = 500
if "custom_mode" not in st.session_state:
    st.session_state.custom_mode = False

if b0:
    st.session_state.monthly = 100
    st.session_state.custom_mode = False
if b1:
    st.session_state.monthly = 500
    st.session_state.custom_mode = False
if b2:
    st.session_state.monthly = 1000
    st.session_state.custom_mode = False
if b3:
    st.session_state.monthly = 2000
    st.session_state.custom_mode = False
if b4:
    st.session_state.monthly = 3000
    st.session_state.custom_mode = False
if b5:
    st.session_state.monthly = 5000
    st.session_state.custom_mode = False
if b6:
    st.session_state.custom_mode = True

if st.session_state.custom_mode:
    custom = st.number_input(
        "Введи сумму:",
        min_value=1,
        value=st.session_state.monthly,
        step=100,
        key="custom_input"
    )
    st.session_state.monthly = custom

monthly = st.session_state.monthly

# --- 4. РАБОТА ---
if user_type == "Подросток":
    st.header("3. Подработки")
else:
    st.header("3. Работа")

job_choice = st.selectbox("Выбери", [j[0] for j in jobs])
extra = 0
if job_choice == "Своя подработка" or job_choice == "Своя работа":
    extra = st.number_input(f"Сколько ты зарабатываешь? ({symbol})", min_value=0, value=0, step=1000, key="job_input")
elif job_choice != "Нет":
    extra = st.number_input(f"Сколько ты зарабатываешь? ({symbol})", min_value=0, value=0, step=1000, key="job_input")

# --- 5. РАСЧЁТ ---
total_monthly = monthly + extra
if total_monthly > 0:
    months = (target - current) / total_monthly
    years = months / 12
    inflation = 0.06
    real_target = target * ((1 + inflation) ** years)

    st.header("4. Результат")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Цель", f"{target:,} {symbol}")
    with col2:
        st.metric("Срок", f"{months:.0f} мес.")
    with col3:
        st.metric("С инфляцией", f"{real_target:,.0f} {symbol}")
    st.info("Инфляция — это подорожание денег в будущем.")

    data = []
    balance = current
    for m in range(int(months) + 1):
        data.append({"Месяц": m, "Баланс": balance})
        balance += total_monthly
    df = pd.DataFrame(data)
    st.line_chart(df.set_index("Месяц")["Баланс"])

    progress = min(current / target, 1.0)
    st.progress(progress)
    st.write(f"Ты на {progress*100:.1f}% к цели")

    # --- 5. АЧИВКИ ---
    st.header("5. Ачивки")
    if progress > 0.01:
        st.write("🎯 Первый шаг — ты начал копить.")
    if monthly >= 1000:
        st.write("💎 Сберегатель — откладываешь больше 1000 в месяц.")
    if progress > 0.25:
        st.write("🥇 Четверть пути — ты прошёл 25% к цели.")
    if progress > 0.5:
        st.write("🔥 Половина — ты на середине пути.")
    if progress > 0.75:
        st.write("⭐ Почти у цели — осталось 25%.")
    if years > 1:
        st.write("🏆 Марафонец — твоя цель на год и больше.")
    if months < 6:
        st.write("🚀 Спринтер — ты достигнешь цели за полгода.")
    if extra > 0:
        st.write("💪 Работяга — у тебя есть дополнительный доход.")
    if extra > 10000:
        st.write("👑 Высокий доход — ты зарабатываешь больше 10K.")
    if user_type == "Подросток":
        st.write("🎓 Школьник — ты учишься и копишь одновременно.")

    # --- 6. НАПОМИНАНИЕ ---
    st.header("6. Напоминание")
    st.write("📅 Откладывай 1-го числа каждого месяца.")
    st.write("📅 Проверяй прогресс каждое воскресенье.")
    st.write("📅 Пересматривай цель раз в месяц.")

    # --- 7. КАК УСКОРИТЬ ---
    st.header("7. Как ускорить цель")
    st.write(f"• Если откладывать на 500 {symbol} больше → срок: {(target - current) / (total_monthly + 500):.0f} мес.")
    st.write(f"• Если откладывать на 1000 {symbol} больше → срок: {(target - current) / (total_monthly + 1000):.0f} мес.")
    daily = (target - current) / (months * 30)
    st.write(f"• Нужно откладывать в день: {daily:.0f} {symbol}")
    for alt_name, alt_desc in alternatives:
        st.write(f"{alt_name} — {alt_desc}")
    # --- 8. ПОЧЕМУ ВАЖНО ---
    st.header("8. Почему важно копить")
    st.write("• Финансовая свобода — ты не зависишь от других.")
    st.write("• Мечты сбываются — ты достигаешь целей.")
    st.write("• Уверенность — ты знаешь, что справишься.")
    st.write("• Будущее — ты строишь базу для жизни.")

    # --- 9. КАК МЕНЬШЕ ТРАТИТЬ ---
    st.header("9. Как меньше тратить")
    st.write("• Правило 24 часов — подожди день перед покупкой.")
    st.write("• Список покупок — не ходи в магазин без него.")
    st.write("• Кофе дома — экономия каждый день.")
    st.write("• Подписки — проверь, что не используешь.")
    st.write("• Импульс — не покупай на эмоциях.")

    # --- 10. ПСИХОЛОГИЯ ---
    st.header("10. Психология накоплений")
    st.write("• Автоматизация — откладывай сразу при доходе.")
    st.write("• Визуализация — смотри на цель каждый день.")
    st.write("• Маленькие шаги — лучше 100, чем 0.")
    st.write("• Поддержка — расскажи другу о цели.")
    st.write("• Прощение — если сорвался, продолжай.")

    # --- 11. СЛОВАРЬ ---
    st.header("11. Словарь")
    for term, definition in terms.items():
        st.write(f"{term} — {definition}")

    # --- 12. ПОЖЕЛАНИЕ ---
    st.success("Удачи! Ты справишься. 💪")

else:
    st.warning("Введи сумму больше 0.")
