import streamlit as st
import pandas as pd
from openai import OpenAI

# OpenAI 클라이언트 (API 키는 Streamlit secrets에서 불러오기)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="변호사시험 자동 채점기", page_icon="📑", layout="wide")

st.title("📑 변호사시험 자동 채점기")

st.markdown("""
CSV 파일을 업로드하면 각 학생 답안을 자동으로 채점합니다.  
출력은 **점수(score)** 와 **짧은 피드백(feedback)** 으로 구성됩니다.
""")

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("📄 원본 데이터 미리보기", df.head())

    if st.button("채점 시작"):
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, row in df.iterrows():
            student_answer = row["student_answer"]

            prompt = f"""
            당신은 대한민국 변호사시험 채점관입니다.
            루브릭(0~5점): 5=완전정답, 4=거의 완전, 3=부분정답, 2=부분오답, 1=거의 틀림, 0=무관.
            학생 답안을 평가하고 JSON 형식으로만 답하세요.

            질문: {row['question_text']}
            모범답안: {row['reference_answer']}
            학생답안: {student_answer}

            출력 예시:
            {{"score": 3, "feedback": "핵심 논점은 잘 짚었으나 보충 설명이 부족함"}}
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            try:
                result = eval(response.choices[0].message.content)
            except:
                result = {"score": None, "feedback": "⚠️ JSON 파싱 실패"}

            results.append(result)

            progress.progress((i+1)/len(df))
            status.text(f"{i+1}/{len(df)} 답안 채점 완료")

        # 결과 합치기
        df["score"] = [r["score"] for r in results]
        df["feedback"] = [r["feedback"] for r in results]

        st.success("✅ 채점 완료")
        st.write("📊 채점 결과 미리보기", df.head())

        # CSV 다운로드 버튼
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 채점 결과 CSV 다운로드", csv, "graded_results.csv", "text/csv")
