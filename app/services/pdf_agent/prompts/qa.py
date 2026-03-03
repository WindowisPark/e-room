# QA system node prompts

CHECK_REFERENCE_PROMPT = """다음 질문이 자료 참조가 필요한지(전문적인 고난이도 질문), 기본적인 내재 지식으로 답변 가능(간단하거나 낮은 난이도의 질문)한지 판단하여 숫자만 답변해주세요.
자료 참조 필요(1), 내재 지식으로 답변 가능(0)

질문 : {user_input}"""

QA_WITH_MATERIAL_PROMPT = """다음 질문에 자료를 참고하여 답변해주세요.
만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.

자료 : {material}
질문 : {user_input}"""

QA_WITHOUT_MATERIAL_PROMPT = """다음 질문에 성의껏 답변해주세요.

질문 : {user_input}"""
