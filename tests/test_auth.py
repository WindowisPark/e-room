"""인증 보안 테스트 - TDD 방식으로 작성"""

import pytest
import logging
from unittest.mock import patch, MagicMock, Mock
from redis.exceptions import RedisError
from starlette.middleware.cors import CORSMiddleware

from app.core.rate_limiter import login_limiter, register_limiter, forgot_password_limiter


# ============================================================
# Commit 1: Rate Limiting + Redis 장애 처리
# ============================================================


class TestRateLimiting:
    """인증 엔드포인트 Rate Limiting 테스트"""

    def setup_method(self):
        login_limiter.reset()
        register_limiter.reset()
        forgot_password_limiter.reset()

    @patch("app.api.v1.auth.crud")
    def test_login_rate_limit_blocks_after_threshold(self, mock_crud, client, mock_redis):
        """로그인 5회 초과 시 429 반환"""
        mock_redis.exists.return_value = False
        mock_crud.user.authenticate.return_value = None

        for _ in range(5):
            client.post("/api/v1/auth/login", json={
                "email": "test@example.com", "password": "wrong12345"
            })

        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com", "password": "wrong12345"
        })
        assert resp.status_code == 429

    @patch("app.api.v1.auth.crud")
    def test_login_rate_limit_allows_under_threshold(self, mock_crud, client, mock_redis):
        """로그인 5회 이하 시 429 아님"""
        mock_redis.exists.return_value = False
        mock_crud.user.authenticate.return_value = None

        for _ in range(4):
            resp = client.post("/api/v1/auth/login", json={
                "email": "test@example.com", "password": "wrong12345"
            })
            assert resp.status_code != 429

    @patch("app.api.v1.auth.crud")
    @patch("app.api.v1.auth.deps.get_db")
    def test_register_rate_limit_blocks(self, mock_get_db, mock_crud, client, mock_redis):
        """회원가입 3회 초과 시 429 반환"""
        mock_redis.exists.return_value = False
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.user.get_by_email.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_mock = MagicMock()
        user_mock.id = 99
        user_mock.email = "new@example.com"
        user_mock.username = "newuser"
        mock_crud.user.create.return_value = user_mock

        payload = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "password1234",
        }

        for i in range(3):
            client.post("/api/v1/auth/register", json={
                **payload, "email": f"new{i}@example.com", "username": f"user{i}"
            })

        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 429

    @patch("app.api.v1.auth.password_reset_service")
    @patch("app.api.v1.auth.crud")
    def test_forgot_password_rate_limit(self, mock_crud, mock_prs, client, mock_redis):
        """비밀번호 찾기 3회 초과 시 429 반환"""
        mock_redis.exists.return_value = False
        mock_prs.request_password_reset.return_value = {
            "success": True,
            "message": "이메일을 발송했습니다",
            "email": "test@example.com",
            "token_expires_in_minutes": 30,
        }

        for _ in range(3):
            client.post("/api/v1/auth/forgot-password", json={
                "email": "test@example.com"
            })

        resp = client.post("/api/v1/auth/forgot-password", json={
            "email": "test@example.com"
        })
        assert resp.status_code == 429


class TestRedisResilience:
    """Redis 장애 시 토큰 블랙리스트 복원력 테스트"""

    def test_token_blacklist_redis_failure_no_crash(self, client, test_token, mock_redis):
        """Redis 장애 시 500 아닌 정상 처리 (fail-open)"""
        mock_redis.exists.side_effect = RedisError("Connection refused")

        with patch("app.api.deps.redis_client", mock_redis):
            with patch("app.api.deps.crud") as mock_crud:
                user_mock = MagicMock()
                user_mock.id = 1
                user_mock.email = "test@example.com"
                user_mock.username = "testuser"
                user_mock.full_name = "Test"
                user_mock.is_active = True
                user_mock.role = "user"
                mock_crud.user.get.return_value = user_mock

                resp = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {test_token}"},
                )
                assert resp.status_code != 500

    def test_token_blacklist_redis_failure_logs_warning(self, client, test_token, test_user, mock_redis, caplog):
        """Redis 장애 시 경고 로그 기록"""
        mock_redis.exists.side_effect = RedisError("Connection refused")

        with patch("app.api.deps.redis_client", mock_redis):
            with patch("app.api.deps.crud") as mock_crud:
                mock_crud.user.get.return_value = test_user

                with caplog.at_level(logging.WARNING, logger="app.api.deps"):
                    client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {test_token}"},
                    )

                assert any("fail-open" in r.message for r in caplog.records)

    def test_revoked_token_rejected(self, client, test_token, mock_redis):
        """블랙리스트에 있는 토큰은 401"""
        mock_redis.exists.return_value = True

        with patch("app.api.deps.redis_client", mock_redis):
            resp = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert resp.status_code == 401


# ============================================================
# Commit 2: 로그아웃 + 토큰 갱신
# ============================================================


class TestLogout:
    """로그아웃 테스트"""

    def test_logout_returns_success(self, client, test_token, test_user, mock_redis):
        """로그아웃 시 200 반환"""
        mock_redis.exists.return_value = False

        with patch("app.api.deps.redis_client", mock_redis):
            with patch("app.api.deps.crud") as mock_crud:
                mock_crud.user.get.return_value = test_user
                with patch("app.api.v1.auth.security") as mock_security:
                    mock_security.delete_refresh_token.return_value = None

                    resp = client.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {test_token}"},
                    )
                    assert resp.status_code == 200
                    assert "로그아웃" in resp.json()["msg"]

    def test_logout_deletes_refresh_token(self, client, test_token, test_user, mock_redis):
        """로그아웃 시 refresh token 삭제 호출"""
        mock_redis.exists.return_value = False

        with patch("app.api.deps.redis_client", mock_redis):
            with patch("app.api.deps.crud") as mock_crud:
                mock_crud.user.get.return_value = test_user
                with patch("app.api.v1.auth.security") as mock_security:
                    mock_security.delete_refresh_token.return_value = None

                    client.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {test_token}"},
                    )
                    mock_security.delete_refresh_token.assert_called_once_with(test_user.id)


class TestRefreshToken:
    """토큰 갱신 테스트"""

    def test_refresh_returns_new_access_token(self, client, mock_redis):
        """유효한 refresh token -> 새 access token 반환"""
        mock_redis.exists.return_value = False

        with patch("app.api.v1.auth.security") as mock_security:
            mock_security.verify_refresh_token.return_value = 1
            mock_security.create_access_token.return_value = "new_access_token"
            with patch("app.api.v1.auth.redis_client", mock_redis):
                mock_redis.get.return_value = "valid_refresh_token"

                resp = client.post(
                    "/api/v1/auth/refresh-token",
                    json="valid_refresh_token",
                )
                assert resp.status_code == 200
                assert resp.json()["access_token"] == "new_access_token"

    def test_refresh_rejects_invalid_token(self, client, mock_redis):
        """잘못된 refresh token -> 401"""
        with patch("app.api.v1.auth.security") as mock_security:
            mock_security.verify_refresh_token.return_value = None

            resp = client.post(
                "/api/v1/auth/refresh-token",
                json="invalid_token",
            )
            assert resp.status_code == 401

    def test_refresh_rejects_not_in_redis(self, client, mock_redis):
        """Redis에 없는 refresh token -> 401"""
        with patch("app.api.v1.auth.security") as mock_security:
            mock_security.verify_refresh_token.return_value = 1
            with patch("app.api.v1.auth.redis_client", mock_redis):
                mock_redis.get.return_value = None

                resp = client.post(
                    "/api/v1/auth/refresh-token",
                    json="orphan_token",
                )
                assert resp.status_code == 401


# ============================================================
# Commit 3: 입력 검증 + 열거 방지 + CORS
# ============================================================


class TestRegistrationSecurity:
    """회원가입 보안 테스트"""

    def setup_method(self):
        register_limiter.reset()

    @patch("app.api.v1.auth.crud")
    @patch("app.api.v1.auth.deps.get_db")
    def test_existing_email_generic_error(self, mock_get_db, mock_crud, client, mock_redis):
        """이메일 중복 시 구체적 메시지 없이 통합 에러"""
        mock_redis.exists.return_value = False
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.user.get_by_email.return_value = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.post("/api/v1/auth/register", json={
            "email": "exists@example.com",
            "username": "newuser",
            "password": "password1234",
        })
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert "이메일 또는 사용자명" in detail
        assert "이미 등록된 이메일" not in detail

    @patch("app.api.v1.auth.crud")
    def test_existing_username_generic_error(self, mock_crud, client, mock_redis):
        """사용자명 중복 시 동일한 통합 에러"""
        mock_redis.exists.return_value = False
        mock_crud.user.get_by_email.return_value = None

        from app.main import app
        from app.api.deps import get_db

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post("/api/v1/auth/register", json={
                "email": "new@example.com",
                "username": "existsuser",
                "password": "password1234",
            })
            assert resp.status_code == 409
            detail = resp.json()["detail"]
            assert "이메일 또는 사용자명" in detail
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_password_7_chars_rejected(self, client, mock_redis):
        """7자 비밀번호 -> 422 거부"""
        mock_redis.exists.return_value = False
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "1234567",
        })
        assert resp.status_code == 422

    @patch("app.api.v1.auth.crud")
    @patch("app.api.v1.auth.deps.get_db")
    def test_password_8_chars_accepted(self, mock_get_db, mock_crud, client, mock_redis):
        """8자 비밀번호 -> 통과"""
        mock_redis.exists.return_value = False
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_crud.user.get_by_email.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_mock = MagicMock()
        user_mock.id = 1
        user_mock.email = "test@example.com"
        user_mock.username = "testuser"
        mock_crud.user.create.return_value = user_mock

        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "12345678",
        })
        assert resp.status_code != 422


class TestCORS:
    """CORS 설정 테스트"""

    def test_cors_does_not_use_wildcard_methods(self):
        """CORS allow_methods에 와일드카드가 아닌 구체적 메서드만 허용"""
        from app.main import app

        for middleware in app.user_middleware:
            if middleware.cls is CORSMiddleware:
                kwargs = middleware.kwargs
                methods = kwargs.get("allow_methods", [])
                assert "*" not in methods, "allow_methods에 '*' 와일드카드 사용 금지"
                assert "GET" in methods
                assert "POST" in methods
                break

    def test_cors_does_not_use_wildcard_headers(self):
        """CORS allow_headers에 와일드카드가 아닌 구체적 헤더만 허용"""
        from app.main import app

        for middleware in app.user_middleware:
            if middleware.cls is CORSMiddleware:
                kwargs = middleware.kwargs
                headers = kwargs.get("allow_headers", [])
                assert "*" not in headers, "allow_headers에 '*' 와일드카드 사용 금지"
                assert "Authorization" in headers
                assert "Content-Type" in headers
                break

    def test_cors_allows_whitelisted(self, client):
        """허용된 origin -> 정상 응답"""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://planova.kr",
                "Access-Control-Request-Method": "POST",
            },
        )
        acao = resp.headers.get("access-control-allow-origin")
        assert acao == "https://planova.kr"
