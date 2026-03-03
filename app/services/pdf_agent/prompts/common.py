# Common node prompts

JUDGE_PURPOSE_PROMPT = """사용자의 질문 의도를 분석하고 purpose map을 참고하여 python 문법에 맞게 json형식으로 바로 변환 가능하게 json형식으로 답변해주세요.
출력 예시는 아래와 같습니다.
1) input : 운영체제 1편을 요약해주세요.
   output : {{"question": "운영체제 1편을 요약해달라 함.", "purpose": "summary"}}
2) input : 스파르타 때의 정치는 어떤 것들이 있어요?
   output : {{"question": "스파르타 시기의 정치를 물음.", "purpose": "qa_system"}}

질문 : {question}
purpose map : {purpose_map}"""

EXTRACT_TARGET_PROMPT = """다음 문장에서 어떤 파일 또는 폴더를 기준으로 학습 계획을 세워야 하는지 판단해주세요.
- 파일명이나 폴더명이 명시되어 있다면 그것을 반환
- 없으면 "None"을 반환
- 형식: {{"target": "정보보호_암호학.pdf"}} 또는 {{"target": "None"}}

질문: "{question}" """
