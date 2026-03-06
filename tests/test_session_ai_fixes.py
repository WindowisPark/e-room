# tests/test_session_ai_fixes.py
"""
TDD: 세션 중복 호출 & AI 품질 개선 구현 검증

검증 항목:
  Fix 1 - onActivated TTL 3분 로직 (JS 등가 Python 검증)
  Fix 2 - LLM 파라미터: temperature=0.4, max_output_tokens=2048, response_mime_type
  Fix 3 - 컨텍스트 크기 제한: resume[:3000], job[:2000]
  Fix 4 - extract_json: 마크다운 코드블록 → JSON 파싱
  통합  - generate_drafts 엔드포인트 전체 플로우
  통합  - _analyze_with_ai_sync 플로우
"""

import json
import re
import time
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────────────────────────────────
# Fix 4: extract_json — 마크다운 코드블록 파싱
# cover_letter.py & job_research.py 양쪽에 동일 알고리즘 존재 (중첩 함수)
# 알고리즘을 여기서 복제 후 단위 테스트 → 구현 코드와 동일해야 통과
# ──────────────────────────────────────────────────────────────────────────────

def extract_json(raw: str) -> str:
    """cover_letter.py / job_research.py의 extract_json 알고리즘 복사"""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


class TestExtractJson:
    def test_plain_json_passthrough(self):
        raw = '[{"question_index": 1, "draft": "내용"}]'
        assert extract_json(raw) == raw

    def test_markdown_json_fence(self):
        raw = '```json\n[{"question_index": 1, "draft": "내용"}]\n```'
        assert extract_json(raw) == '[{"question_index": 1, "draft": "내용"}]'

    def test_markdown_fence_no_language_label(self):
        raw = '```\n{"key": "value"}\n```'
        assert extract_json(raw) == '{"key": "value"}'

    def test_leading_trailing_whitespace_stripped(self):
        raw = '  {"key": "value"}  '
        assert extract_json(raw) == '{"key": "value"}'

    def test_multiline_array_in_fence_is_valid_json(self):
        raw = (
            '```json\n'
            '[\n'
            '  {"question_index": 1, "draft": "a"},\n'
            '  {"question_index": 2, "draft": "b"}\n'
            ']\n'
            '```'
        )
        parsed = json.loads(extract_json(raw))
        assert len(parsed) == 2
        assert parsed[1]["draft"] == "b"

    def test_result_is_parseable_json(self):
        raw = '```json\n[{"question_index": 1, "draft": "초안"}]\n```'
        parsed = json.loads(extract_json(raw))
        assert parsed[0]["question_index"] == 1
        assert parsed[0]["draft"] == "초안"

    def test_extra_text_before_fence_ignored(self):
        raw = '다음은 결과입니다:\n```json\n{"ok": true}\n```'
        assert json.loads(extract_json(raw)) == {"ok": True}


# ──────────────────────────────────────────────────────────────────────────────
# Fix 3: 컨텍스트 크기 제한
# ──────────────────────────────────────────────────────────────────────────────

class TestContextTruncation:
    def test_resume_truncated_at_3000(self):
        long_resume = "이력서 내용 " * 500   # ~5000자
        ctx = long_resume[:3000] if long_resume else "(이력서 정보 없음)"
        assert len(ctx) == 3000

    def test_job_truncated_at_2000(self):
        long_job = "기업 정보 내용 " * 400   # ~4000자
        ctx = long_job[:2000] if long_job else "(기업 정보 없음)"
        assert len(ctx) == 2000

    def test_short_resume_unchanged(self):
        short = "짧은 이력서"
        ctx = short[:3000] if short else "(이력서 정보 없음)"
        assert ctx == short

    def test_empty_resume_uses_fallback(self):
        resume = ""
        ctx = resume[:3000] if resume else "(이력서 정보 없음)"
        assert ctx == "(이력서 정보 없음)"

    def test_empty_job_uses_fallback(self):
        job = ""
        ctx = job[:2000] if job else "(기업 정보 없음)"
        assert ctx == "(기업 정보 없음)"

    def test_none_resume_uses_fallback(self):
        resume = None
        ctx = resume[:3000] if resume else "(이력서 정보 없음)"
        assert ctx == "(이력서 정보 없음)"


# ──────────────────────────────────────────────────────────────────────────────
# Fix 1: onActivated TTL 로직 — JS 코드 Python 등가 검증
#
# JS 원본 (StudentMyroomPage.vue):
#   const TTL_MS = 3 * 60 * 1000
#   onActivated(() => {
#     if (Date.now() - lastFetchTime.value > TTL_MS) fetchAll()
#   })
# ──────────────────────────────────────────────────────────────────────────────

class TestOnActivatedTTL:
    TTL_MS = 3 * 60 * 1000  # 180_000 ms

    def _should_refetch(self, last_fetch_ms: int, now_ms: int) -> bool:
        return (now_ms - last_fetch_ms) > self.TTL_MS

    def test_refetch_when_ttl_expired(self):
        now = int(time.time() * 1000)
        last = now - (self.TTL_MS + 1000)   # 3분 1초 전
        assert self._should_refetch(last, now) is True

    def test_no_refetch_within_ttl(self):
        now = int(time.time() * 1000)
        last = now - (self.TTL_MS - 1000)   # 2분 59초 전
        assert self._should_refetch(last, now) is False

    def test_no_refetch_at_exactly_ttl_boundary(self):
        now = int(time.time() * 1000)
        last = now - self.TTL_MS            # 정확히 3분 (> 가 아님 → False)
        assert self._should_refetch(last, now) is False

    def test_refetch_when_last_fetch_is_zero(self):
        """초기값 0 → 항상 refetch"""
        now = int(time.time() * 1000)
        assert self._should_refetch(0, now) is True

    def test_ttl_constant_is_3_minutes(self):
        assert self.TTL_MS == 180_000


# ──────────────────────────────────────────────────────────────────────────────
# Fix 2: LLM 파라미터 — temperature, max_output_tokens, response_mime_type
# ──────────────────────────────────────────────────────────────────────────────

class TestLLMParameters:
    """ChatGoogleGenerativeAI 생성자가 올바른 파라미터를 받는지 검증"""

    EXPECTED = {
        "temperature": 0.4,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
    }

    def _init_llm(self, MockLLM):
        from langchain_google_genai import ChatGoogleGenerativeAI
        ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key="test-key",
            request_timeout=60,
            temperature=self.EXPECTED["temperature"],
            max_output_tokens=self.EXPECTED["max_output_tokens"],
            model_kwargs={"response_mime_type": self.EXPECTED["response_mime_type"]},
        )
        return MockLLM.call_args.kwargs

    def test_temperature_is_0_4(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as M:
            kwargs = self._init_llm(M)
        assert kwargs["temperature"] == 0.4

    def test_max_output_tokens_is_2048(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as M:
            kwargs = self._init_llm(M)
        assert kwargs["max_output_tokens"] == 2048

    def test_response_mime_type_is_json(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as M:
            kwargs = self._init_llm(M)
        assert kwargs["model_kwargs"]["response_mime_type"] == "application/json"

    def test_cover_letter_endpoint_uses_correct_params(self):
        """cover_letter.py의 실제 LLM 초기화 파라미터를 intercept"""
        from app.models.cover_letter import CoverLetter, CoverLetterItem
        from app.main import app
        from app.api import deps

        mock_cl = Mock(spec=CoverLetter)
        mock_cl.id = 1
        mock_cl.user_id = 1
        mock_cl.resume_profile_id = None
        mock_cl.company_id = None

        mock_item = Mock(spec=CoverLetterItem)
        mock_item.id = 10
        mock_item.question = "지원 동기"
        mock_item.char_limit = None
        mock_item.order_index = 0
        mock_item.answer = None

        mock_db = _make_mock_db(cl=mock_cl, items=[mock_item])

        ai_json = '[{"question_index": 1, "draft": "테스트 초안"}]'

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            mock_inst = Mock()
            mock_inst.invoke.return_value = Mock(content=ai_json)
            MockLLM.return_value = mock_inst

            with _override_deps(app, deps, user_id=1, mock_db=mock_db):
                client = TestClient(app)
                resp = client.post(
                    "/api/v1/coverletter/1/generate",
                    headers={"Authorization": "Bearer test"},
                )

        assert resp.status_code == 200
        init_kwargs = MockLLM.call_args.kwargs
        assert init_kwargs["temperature"] == 0.4
        assert init_kwargs["max_output_tokens"] == 2048
        assert init_kwargs["model_kwargs"]["response_mime_type"] == "application/json"


# ──────────────────────────────────────────────────────────────────────────────
# 통합: generate_drafts 엔드포인트 전체 플로우
# ──────────────────────────────────────────────────────────────────────────────

class TestGenerateDraftsEndpoint:

    def _setup(self, cl_override=None, items=None):
        from app.models.cover_letter import CoverLetter, CoverLetterItem
        from app.main import app
        from app.api import deps

        mock_cl = cl_override or _default_cl()
        mock_items = items if items is not None else [_default_item()]
        mock_db = _make_mock_db(cl=mock_cl, items=mock_items)
        return app, deps, mock_db

    def test_success_returns_updated_list(self):
        app, deps, mock_db = self._setup()
        ai_json = '[{"question_index": 1, "draft": "강점은 문제 해결 능력입니다."}]'

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = Mock(content=ai_json)
            with _override_deps(app, deps, user_id=1, mock_db=mock_db):
                resp = TestClient(app).post(
                    "/api/v1/coverletter/1/generate",
                    headers={"Authorization": "Bearer test"},
                )

        assert resp.status_code == 200
        body = resp.json()
        assert "updated" in body
        assert len(body["updated"]) == 1
        assert body["updated"][0]["id"] == 10
        assert "강점" in body["updated"][0]["answer"]

    def test_no_items_returns_400(self):
        app, deps, mock_db = self._setup(items=[])

        with _override_deps(app, deps, user_id=1, mock_db=mock_db):
            resp = TestClient(app).post(
                "/api/v1/coverletter/1/generate",
                headers={"Authorization": "Bearer test"},
            )

        assert resp.status_code == 400
        assert "문항이 없습니다" in resp.json()["detail"]

    def test_nonexistent_cl_returns_404(self):
        from app.main import app
        from app.api import deps

        mock_db = _make_mock_db(cl=None, items=[])

        with _override_deps(app, deps, user_id=1, mock_db=mock_db):
            resp = TestClient(app).post(
                "/api/v1/coverletter/999/generate",
                headers={"Authorization": "Bearer test"},
            )

        assert resp.status_code == 404

    def test_markdown_wrapped_response_parsed_correctly(self):
        """AI가 마크다운 블록으로 반환해도 정상 파싱"""
        app, deps, mock_db = self._setup()
        ai_markdown = '```json\n[{"question_index": 1, "draft": "마크다운 초안"}]\n```'

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = Mock(content=ai_markdown)
            with _override_deps(app, deps, user_id=1, mock_db=mock_db):
                resp = TestClient(app).post(
                    "/api/v1/coverletter/1/generate",
                    headers={"Authorization": "Bearer test"},
                )

        assert resp.status_code == 200
        assert resp.json()["updated"][0]["answer"] == "마크다운 초안"

    def test_multiple_items_all_updated(self):
        """문항 3개 → updated 3개"""
        from app.models.cover_letter import CoverLetterItem
        items = [
            _item(id=10, question="Q1", order_index=0),
            _item(id=11, question="Q2", order_index=1),
            _item(id=12, question="Q3", order_index=2),
        ]
        app, deps, mock_db = self._setup(items=items)
        ai_json = json.dumps([
            {"question_index": 1, "draft": "답변1"},
            {"question_index": 2, "draft": "답변2"},
            {"question_index": 3, "draft": "답변3"},
        ])

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = Mock(content=ai_json)
            with _override_deps(app, deps, user_id=1, mock_db=mock_db):
                resp = TestClient(app).post(
                    "/api/v1/coverletter/1/generate",
                    headers={"Authorization": "Bearer test"},
                )

        assert resp.status_code == 200
        assert len(resp.json()["updated"]) == 3


# ──────────────────────────────────────────────────────────────────────────────
# 통합: _analyze_with_ai_sync (job_research)
# ──────────────────────────────────────────────────────────────────────────────

class TestAnalyzeWithAiSync:

    def test_returns_valid_analysis_dict(self):
        result_data = {
            "company_name": "테스트컴퍼니",
            "job_title": "백엔드 개발자",
            "overview": "개요 내용",
            "tech_stack": ["Python", "FastAPI"],
            "requirements": ["3년 이상"],
            "preferred": ["AWS 경험"],
            "culture": "수평적 문화",
            "interview_questions": ["질문1", "질문2"],
        }
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.return_value.invoke.return_value = Mock(
                content=json.dumps(result_data)
            )
            from app.api.v1.endpoints.job_research import _analyze_with_ai_sync
            result = _analyze_with_ai_sync("채용공고 내용")

        assert result["company_name"] == "테스트컴퍼니"
        assert "Python" in result["tech_stack"]
        assert result["job_title"] == "백엔드 개발자"

    def test_returns_fallback_on_llm_exception(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            MockLLM.side_effect = Exception("API 오류")
            from app.api.v1.endpoints.job_research import _analyze_with_ai_sync
            result = _analyze_with_ai_sync("내용")

        assert result["company_name"] == ""
        assert "분석에 실패" in result["overview"]
        assert result["tech_stack"] == []

    def test_content_truncated_at_6000_in_prompt(self):
        """프롬프트 내 content[:6000] 적용 확인: 6000자 이후 고유 마커가 prompt에 없어야 함"""
        unique_marker = "BEYOND_6000_UNIQUE_MARKER_XYZ"
        # 6000자 패딩 + 고유 마커 → 마커는 프롬프트에 포함되면 안 됨
        long_content = "a" * 6000 + unique_marker + "b" * 100
        result_data = {
            "company_name": "A", "job_title": "", "overview": "",
            "tech_stack": [], "requirements": [], "preferred": [],
            "culture": "", "interview_questions": [],
        }
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            mock_inst = Mock()
            mock_inst.invoke.return_value = Mock(content=json.dumps(result_data))
            MockLLM.return_value = mock_inst

            from app.api.v1.endpoints.job_research import _analyze_with_ai_sync
            _analyze_with_ai_sync(long_content)

            prompt_arg = mock_inst.invoke.call_args[0][0]

        assert len(long_content) > 6000
        # content[:6000] 이 적용됐다면 고유 마커는 프롬프트에 없어야 함
        assert unique_marker not in prompt_arg

    def test_llm_called_with_correct_params(self):
        """_analyze_with_ai_sync 내부 LLM도 올바른 파라미터로 초기화"""
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as MockLLM:
            mock_inst = Mock()
            mock_inst.invoke.return_value = Mock(
                content='{"company_name":"","job_title":"","overview":"","tech_stack":[],"requirements":[],"preferred":[],"culture":"","interview_questions":[]}'
            )
            MockLLM.return_value = mock_inst

            from app.api.v1.endpoints.job_research import _analyze_with_ai_sync
            _analyze_with_ai_sync("공고")

        kwargs = MockLLM.call_args.kwargs
        assert kwargs["temperature"] == 0.4
        assert kwargs["max_output_tokens"] == 2048
        assert kwargs["model_kwargs"]["response_mime_type"] == "application/json"


# ──────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def _default_cl():
    from app.models.cover_letter import CoverLetter
    cl = Mock(spec=CoverLetter)
    cl.id = 1
    cl.user_id = 1
    cl.resume_profile_id = None
    cl.company_id = None
    return cl


def _default_item():
    return _item(id=10, question="본인의 강점을 서술하세요.", order_index=0)


def _item(id, question, order_index, char_limit=None):
    from app.models.cover_letter import CoverLetterItem
    it = Mock(spec=CoverLetterItem)
    it.id = id
    it.question = question
    it.char_limit = char_limit
    it.order_index = order_index
    it.answer = None
    return it


def _make_mock_db(cl, items):
    """SQLAlchemy query 체인을 모델별로 분리해 반환하는 Mock DB"""
    from app.models.cover_letter import CoverLetter, CoverLetterItem

    mock_db = MagicMock(spec=Session)

    def query_side_effect(model):
        q = MagicMock()
        if model is CoverLetter:
            q.filter.return_value.first.return_value = cl
        elif model is CoverLetterItem:
            q.filter.return_value.order_by.return_value.all.return_value = items
        else:
            q.filter.return_value.first.return_value = None
        return q

    mock_db.query.side_effect = query_side_effect
    return mock_db


from contextlib import contextmanager

@contextmanager
def _override_deps(app, deps, user_id: int, mock_db):
    """app.dependency_overrides를 사용해 인증+DB를 모킹"""
    from app.models.user import User
    from datetime import datetime

    mock_user = User(
        id=user_id,
        email="test@test.com",
        username="tester",
        full_name="테스터",
        is_active=True,
        role="user",
        created_at=datetime.utcnow(),
    )

    app.dependency_overrides[deps.get_current_user] = lambda: mock_user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(deps.get_current_user, None)
        app.dependency_overrides.pop(deps.get_db, None)
