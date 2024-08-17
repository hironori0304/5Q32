import streamlit as st
import pandas as pd
import random

# クイズデータを読み込む関数
def load_quizzes(file):
    df = pd.read_csv(file, encoding='utf-8')
    return df

# アプリケーションのタイトル
st.title('国家試験対策アプリ')

# セッション状態の初期化
def initialize_session_state():
    if 'highlighted_questions' not in st.session_state:
        st.session_state.highlighted_questions = set()
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'score' not in st.session_state:
        st.session_state.score = None
    if 'total_questions' not in st.session_state:
        st.session_state.total_questions = 0
    if 'percentage' not in st.session_state:
        st.session_state.percentage = None
    if 'shuffled_options' not in st.session_state:
        st.session_state.shuffled_options = {}
    if 'selected_years' not in st.session_state:
        st.session_state.selected_years = []
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = []

initialize_session_state()

# ファイルアップロード
uploaded_file = st.file_uploader("問題データのCSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    # アップロードされたファイルを読み込む
    df = load_quizzes(uploaded_file)

    # 年と分類の選択肢を取得し、「すべて」を追加
    years = df['year'].unique().tolist()
    categories = df['category'].unique().tolist()
    
    years = ['すべて'] + years
    categories = ['すべて'] + categories
    
    # ユーザーが「年」と「分類」を選択
    selected_years = st.multiselect('過去問を選択', years)
    selected_categories = st.multiselect('内容を選択', categories)
    
    # 選択された条件をセッション状態に保存
    st.session_state.selected_years = selected_years
    st.session_state.selected_categories = selected_categories

    # 年と分類の選択に応じてデータをフィルタリング
    if 'すべて' in selected_years and 'すべて' in selected_categories:
        filtered_df = df
    elif 'すべて' in selected_years:
        filtered_df = df[df['category'].isin(selected_categories)]
    elif 'すべて' in selected_categories:
        filtered_df = df[df['year'].isin(selected_years)]
    else:
        filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]

    # 年とカテゴリーの選択順に基づいてソート
    if 'year' in filtered_df.columns and 'category' in filtered_df.columns:
        category_order = {category: idx for idx, category in enumerate(st.session_state.selected_categories)}
        year_order = {year: idx for idx, year in enumerate(st.session_state.selected_years)}

        filtered_df['category_order'] = filtered_df['category'].map(category_order).fillna(float('inf'))
        filtered_df['year_order'] = filtered_df['year'].map(year_order).fillna(float('inf'))

        filtered_df = filtered_df.sort_values(by=['category_order', 'year_order'])
        filtered_df = filtered_df.drop(columns=['category_order', 'year_order'])

    total_questions = len(filtered_df)
    st.write(f"選択された問題は{total_questions}問あります")

    quizzes = []
    for _, row in filtered_df.iterrows():
        options = [row[f"option{i}"] for i in range(1, 6) if pd.notna(row[f"option{i}"])]
        answers = [row[f"answer{i}"] for i in range(1, 6) if pd.notna(row[f"answer{i}"])]
        
        if row["question"] not in st.session_state.shuffled_options:
            shuffled_options = options[:]
            random.shuffle(shuffled_options)
            st.session_state.shuffled_options[row["question"]] = shuffled_options

        quiz = {
            "question": row["question"],
            "type": row["type"],
            "options": st.session_state.shuffled_options[row["question"]],
            "answers": answers
        }
        quizzes.append(quiz)

    for idx, quiz in enumerate(quizzes, start=1):
        highlight = 'background-color: #fdd; padding: 10px;' if idx in st.session_state.highlighted_questions else ''
        st.markdown(f'<div style="{highlight}">問題{idx}</div>', unsafe_allow_html=True)
        st.markdown(f'<div>{quiz["question"]}</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            div[role='radiogroup'] {
                margin-top: -20px; 
            }
            div[role='radiogroup'] > label {
                margin-bottom: 10px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        if quiz["type"] == "single":
            user_answer = st.session_state.user_answers.get(quiz["question"], None)
            selected_option = st.radio("", quiz["options"], key=f"{idx}_radio", index=quiz["options"].index(user_answer) if user_answer in quiz["options"] else None)
            st.session_state.user_answers[quiz["question"]] = selected_option
        elif quiz["type"] == "multiple":
            selected_options = st.session_state.user_answers.get(quiz["question"], [])
            for option in quiz["options"]:
                checked = option in selected_options
                if st.checkbox(option, key=f"{idx}_{option}", value=checked):
                    if option not in selected_options:
                        selected_options.append(option)
                else:
                    if option in selected_options:
                        selected_options.remove(option)
            st.session_state.user_answers[quiz["question"]] = selected_options

        st.markdown("<br>", unsafe_allow_html=True)

    # 回答ボタンを作成
    if st.button('回答'):
        # 成績の計算と間違った問題のリストの更新
        correct_count = 0
        total_questions = len(quizzes)
        highlighted_questions = set()

        for idx, quiz in enumerate(quizzes, start=1):
            if quiz["type"] == "single":
                user_answer = st.session_state.user_answers.get(quiz["question"], None)
                is_correct = user_answer == quiz["answers"][0]
                if not is_correct:
                    highlighted_questions.add(idx)
            elif quiz["type"] == "multiple":
                user_answers_options = set(st.session_state.user_answers.get(quiz["question"], []))
                correct_answers = set(quiz["answers"])
                is_correct = user_answers_options == correct_answers
                if not is_correct:
                    highlighted_questions.add(idx)
                else:
                    correct_count += 1

        # 現在の間違った問題リストをクリアし、新しい間違った問題のみを登録
        st.session_state.highlighted_questions = highlighted_questions
        st.session_state.score = total_questions - len(highlighted_questions)
        st.session_state.total_questions = total_questions
        st.session_state.percentage = (st.session_state.score / total_questions) * 100

        # 成績の表示
        st.write(f"成績: {st.session_state.score}/{st.session_state.total_questions} 正解")
        st.write(f"正解率: {st.session_state.percentage:.2f}%")

    # 不正解問題ボタンを作成
    if st.button('不正解問題'):
        # 不正解問題の番号にハイライトをつける
        for idx, quiz in enumerate(quizzes, start=1):
            highlight = 'background-color: #fdd; padding: 10px;' if idx in st.session_state.highlighted_questions else ''
            
            