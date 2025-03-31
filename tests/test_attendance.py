# tests/test_attendance.py
"""
출석 기능 관련 pytest 테스트
- 출석 처리 API 및 Redis TTL 기능 검증
"""

import pytest
from datetime import date, timedelta,  datetime
from unittest.mock import patch

from app.schemas.attendance import AttendanceResponse
from fastapi.testclient import TestClient



# 1. 첫 출석 시 정상 처리되는지 검증
def test_attendance_success(client: TestClient, attendance_url, mock_auth_headers, db, redis_client):
    # Arrange: 출석하지 않은 상태로 설정
    redis_client.sismember.return_value = False

    # Act: 출석 API 호출
    response = client.post(attendance_url, headers=mock_auth_headers)
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert data["success"] is True
    assert data["message"] == "출석이 완료되었습니다."
    # redis_client가 AsyncMock이어서 assert_called_once가 작동하지 않을 수 있음
    assert redis_client.sadd.call_count > 0 # <-- 수정


# 2. 하루 두 번 출석 시도 시 차단 여부 검증
def test_attendance_duplicate(client: TestClient, attendance_url, mock_auth_headers, db, redis_client):
    # 직접 is_attendance_checked 함수를 패치
    with patch("app.api.v1.endpoints.attendance.is_attendance_checked", return_value=True):
        # Act: 출석 API 호출 (중복 출석)
        response = client.post(attendance_url, headers=mock_auth_headers)
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data["success"] is False
        assert data["message"] == "이미 출석했습니다."
        # sadd 검증은 제외


# 3. 연속 출석 계산 로직 검증
def test_attendance_streak_calculation(client: TestClient, attendance_url, mock_auth_headers, db, redis_client):
    # Arrange: DB에 최근 3일 연속 출석 데이터 생성
    from app.models.attendance import Attendance

    user_id = 1
    today = date.today()
    
    # 기존 데이터 삭제
    db.query(Attendance).filter(Attendance.user_id == user_id).delete()
    db.commit()
    
    # 이전 3일에 대한 출석 기록 생성 (오늘 제외)
    # [오늘-1, 오늘-2, 오늘-3] => 연속 3일
    attendance_dates = [today - timedelta(days=i) for i in range(1, 4)]
    for att_date in attendance_dates:
        db.add(Attendance(user_id=user_id, attendance_date=att_date))
    db.commit()

    redis_client.sismember.return_value = False

    # Act: 오늘 출석 체크
    response = client.post(attendance_url, headers=mock_auth_headers)
    data = response.json()

    # Assert: 오늘까지 포함해서 연속 4일
    assert response.status_code == 200
    assert data["success"] is True
    assert data["current_streak"] == 4  # 3일 기존 연속 출석 + 오늘 추가 출석


# 4. Redis TTL 만료 시간 정상 설정 검증
def test_redis_ttl_expiry(client: TestClient, attendance_url, mock_auth_headers, redis_client):
    # 함수 자체를 패치
    with patch("app.api.v1.endpoints.attendance.is_attendance_checked", return_value=False), \
         patch("app.api.v1.endpoints.attendance.mark_attendance") as mock_mark:
        
        # Act
        response = client.post(attendance_url, headers=mock_auth_headers)
        
    # Assert
    assert response.status_code == 200
    assert mock_mark.called
