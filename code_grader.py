import streamlit as st
import nbformat
import difflib
import pandas as pd
import re
import contextlib
import io

st.set_page_config(page_title="파이썬 실기 자동 채점기", layout="wide")
st.title("💻2025년 1학기 중간고사  자동 채점기")
st.markdown(".ipynb 파일을 업로드하면 `#문제1`부터 `#문제10`까지 자동 채점합니다. 공백 차이는 무시합니다.")

reference_codes = {
    2: '''count = 0
while count < 5:
    print("나는 행복합니다")
    count += 1''',
    3: '''for i in range(5):
    print("나는 행복합니다")''',
    5: '''total_seconds = int(input("초를 입력하세요: "))
hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60
print(f"{hours}시간 {minutes}분 {seconds}초")''',
    6: '''age = int(input("나이를 입력하세요: "))
if age >= 65:
    print("group is 노인")
elif age >= 19:
    print("group is 성인")
elif age >= 13:
    print("group is 청소년")
else:
    print("group is 어린이")''',
    7: '''my_list = [100, 200, 400, 800, 1000, 1300]
for i in range(len(my_list) - 2):
    avg = (my_list[i] + my_list[i+1] + my_list[i+2]) / 3
    print(f"{avg:.1f}")''',
    8: '''for num in range(100, 1000):
    num_str = str(num)
    if int(num_str[0]) % 2 == 0 and int(num_str[-1]) % 2 == 1:
        if num % 4 != 0:
            print(num)''',
    9: '''for num in range(2, 101):
    is_prime = True
    for i in range(2, num):
        if num % i == 0:
            is_prime = False
            break
    if is_prime:
        print(num)''',
    10: '''count = 0
max_val = None
while True:
    n = int(input("입력: "))
    if n == 0:
        break
    count += 1
    if max_val is None or n > max_val:
        max_val = n
print("입력된 수의 개수:", count)
print("최댓값:", max_val)'''
}

scores = {i: 5 for i in range(1, 5)}
scores.update({5: 10, 6: 10, 7: 15, 8: 15, 9: 15, 10: 15})

def normalize_code(code):
    return re.sub(r"\s+", "", code.strip())

def extract_student_codes(nb_content):
    notebook = nbformat.reads(nb_content, as_version=4)
    student_codes = {}
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            lines = cell.source.strip().split('\n')
            if lines and lines[0].startswith('#문제'):
                try:
                    num = int(re.findall(r'\d+', lines[0])[0])
                    student_codes[num] = '\n'.join(lines[1:]).strip()
                except:
                    continue
    return student_codes

def execute_and_capture_output(code):
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {})
        return f.getvalue().strip()
    except Exception as e:
        return str(e)

def score_problem(qnum, student_code):
    if not student_code:
        return 0, "미제출"

    if qnum == 1:
        output = execute_and_capture_output(student_code)
        if "53.56" in output:
            return scores[qnum], "출력값 53.56 포함"
        else:
            return 0, "출력값 누락"

    if qnum == 4:
        output = execute_and_capture_output(student_code)
        if "for" in student_code and output.strip() == "d\nc\np":
            return scores[qnum], "for문 포함, 출력 일치"
        else:
            return 0, "for문 누락 또는 출력 불일치"

    student_clean = normalize_code(student_code)
    reference_clean = normalize_code(reference_codes.get(qnum, ""))
    if student_clean == reference_clean:
        return scores[qnum], "정확히 일치"
    ratio = difflib.SequenceMatcher(None, student_clean, reference_clean).ratio()
    if ratio > 0.95:
        return scores[qnum], "매우 유사"
    elif ratio > 0.85:
        return int(scores[qnum]*0.8), "유사"
    elif ratio > 0.7:
        return int(scores[qnum]*0.6), "부분 유사"
    else:
        return 0, "유사도 낮음"

uploaded_file = st.file_uploader("📂 Colab .ipynb 파일 업로드", type=["ipynb"])

if uploaded_file:
    st.success("파일 업로드 완료 ✅")
    content = uploaded_file.read().decode("utf-8")
    student_codes = extract_student_codes(content)

    st.subheader("📊 채점 결과")
    results = []
    total = 0

    for qnum in range(1, 11):
        code = student_codes.get(qnum, "")
        score, reason = score_problem(qnum, code)
        total += score
        results.append({"문제": f"문제{qnum}", "점수": score, "이유": reason})

    results.append({"문제": "총점", "점수": total, "이유": ""})
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 채점 결과 CSV 다운로드", data=csv, file_name="grading_result.csv", mime="text/csv")