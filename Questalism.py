import streamlit as st
import pandas as pd

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

st.title("💰 Questalism")
st.write("Симулятор финансовых целей для подростков")

# --- 1. ЦЕЛЬ ---
st.header("1. Твоя цель")
col1, col2 = st.columns(2)
with col1:
    goal = st.text_input("На что копишь?", "iPhone")
with col2:
    currency = st.selectbox("Валюта", ["Рубли (₽)", "Доллары ($)"])

if currency == "Доллары ($)":
    symbol = "$"
else:
    symbol = "₽"

target = st.number_input(f"Сколько стоит? ({symbol})", min_value=0, value=80000, step=1000)

# --- 2. ДАННЫЕ ---
st.header("2. Твои данные")
col1, col2 = st.columns(2)
with col1:
    age = st.slider("Сколько тебе лет?", 13, 17, 15)
with col2:
    current = st.number_input(f"Сколько есть сейчас? ({symbol})", min_value=0, value=5000, step=1000)

st.write("Сколько можешь откладывать в месяц?")
col1, col2, col3, col4 = st.columns(4)
with col1:
    b1 = st.button("500")
with col2:
    b2 = st.button("1000")
with col3:
    b3 = st.button("2000")
with col4:
    b4 = st.button("Своё")

if "monthly" not in st.session_state:
    st.session_state.monthly = 1000

if b1: st.session_state.monthly = 500
if b2: st.session_state.monthly = 1000
if b3: st.session_state.monthly = 2000
if b4: st.session_state.monthly = st.number_input("Введи сумму:", min_value=1, value=1500, step=100)

monthly = st.session_state.monthly

# --- 3. ПОДРАБОТКИ ---
st.header("3. Подработки")
st.write("Что ты можешь делать?")

jobs = []
if age >= 13:
    jobs.append(("Промоутер", 3000))
if age >= 14:
    jobs.append(("Курьер", 8000))
if age >= 15:
    jobs.append(("Репетитор", 10000))
if age >= 16:
    jobs.append(("Официант", 12000))
    jobs.append(("Фриланс", 15000))

job_choice = st.selectbox("Выбери подработку", ["Нет"] + [j[0] for j in jobs])
extra = 0
for j in jobs:
    if j[0] == job_choice:
        extra = j[1]

# --- 4. РАСЧЁТ ---
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

    # График
    data = []
    balance = current
    for m in range(int(months) + 1):
        data.append({"Месяц": m, "Баланс": balance})
        balance += total_monthly

    df = pd.DataFrame(data)
    st.line_chart(df.set_index("Месяц")["Баланс"])

    # Прогресс
    progress = min(current / target, 1.0)
    st.progress(progress)
    st.write(f"Ты на {progress*100:.1f}% к цели")

    # --- 5. АЛЬТЕРНАТИВЫ ---
    st.header("5. Альтернативы")
    st.write(f"• Найти подработку → срок: {(target - current) / (monthly + 5000):.0f} мес.")
    st.write(f"• Положить на вклад (+10% годовых) → срок: {months * 0.9:.0f} мес.")

    # --- 6. АЧИВКИ ---
    st.header("6. Ачивки")
    if progress > 0.01: st.write("🏆 Первый шаг")
    if monthly >= 1000: st.write("🏆 Сберегатель")
    if progress > 0.5: st.write("🏆 Цель близко")
    if years > 1: st.write("🏆 Марафонец")
    if months < 3: st.write("🏆 Спринтер")
    if extra > 0: st.write("🏆 Работяга")
else:
    st.warning("Введи сумму больше 0.")
