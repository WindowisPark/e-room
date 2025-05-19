"""
PDF 업로드 기능 테스트 모듈
이 모듈은 파일 업로드 엔드포인트의 정상 동작과 예외 처리를 검증합니다.
"""

import os
from pathlib import Path

def test_upload_single_pdf(client):
    user_id = 1
    folder_name = "test_folder"
    file_path = Path("tests/assets/sample.pdf")

    with open(file_path, "rb") as f:
        response = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": ("sample.pdf", f, "application/pdf")}
        )

    assert response.status_code == 200

    data = response.json()
    print("RESPONSE JSON:", data)

    assert "success" in data
    assert isinstance(data["success"], list)
    assert len(data["success"]) >= 1

def test_upload_invalid_file_type(client):
    """
    테스트 목적: PDF 외 확장자(.txt 등)를 업로드할 경우 400 오류 반환 여부 확인

    전제 조건:
    - .txt 파일이 준비되어 있어야 함

    검증 내용:
    - status_code == 400
    - 응답 메시지에 "PDF" 또는 관련 에러 문구 포함
    """
    user_id = 1
    folder_name = "invalid_upload_test"
    file_path = Path("tests/assets/invalid.txt")

    with open(file_path, "rb") as f:
        response = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": ("invalid.txt", f, "text/plain")}
        )

    assert response.status_code == 400
    assert "실패" in response.json()["detail"]

def test_upload_duplicate_filename(client):
    """
    테스트 목적: 동일한 이름의 PDF를 업로드하면 중복 처리되어 저장되는지 검증

    전제 조건:
    - sample.pdf 파일이 준비되어 있어야 함

    검증 내용:
    - 첫 업로드는 정상 저장
    - 두 번째 업로드는 이름이 달라져야 함
    """
    user_id = 1
    folder_name = "duplicate_upload_test"
    file_path = Path("tests/assets/sample.pdf")

    # 첫 번째 업로드
    with open(file_path, "rb") as f1:
        response1 = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": ("sample.pdf", f1, "application/pdf")}
        )

    assert response1.status_code == 200
    first_result = response1.json()["success"][0]
    first_saved_name = first_result["saved_name"]

    # 두 번째 업로드 (같은 파일명)
    with open(file_path, "rb") as f2:
        response2 = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": ("sample.pdf", f2, "application/pdf")}
        )

    assert response2.status_code == 200
    second_result = response2.json()["success"][0]
    second_saved_name = second_result["saved_name"]

    # ✅ 파일명이 달라야 함 (중복 방지 처리 확인)
    assert first_saved_name != second_saved_name

def test_rename_file(client):
    """
    테스트 목적: 업로드된 PDF 파일의 이름을 정상적으로 변경할 수 있는지 검증

    전제 조건:
    - sample.pdf 파일이 업로드되어 있어야 함

    검증 내용:
    - 변경 요청 시 status_code == 200
    - 응답에 변경된 파일 이름이 포함되어야 함
    - 새로운 이름으로 실제 파일이 존재해야 함
    """
    # Arrange
    user_id = 1
    folder_name = "rename_test"
    original_name = "sample.pdf"
    new_name = "renamed_sample"

    file_path = Path("tests/assets/sample.pdf")

    # 1. 파일 업로드
    with open(file_path, "rb") as f:
        upload_res = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": (original_name, f, "application/pdf")}
        )
    assert upload_res.status_code == 200

    # ✅ 실제 저장된 이름 추출 (uuid_xxx_sample.pdf 형태)
    saved_name = upload_res.json()["success"][0]["saved_name"]

    # 2. 이름 변경 요청
    rename_res = client.put(
        f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files/{saved_name}/rename",
        params={"new_name": new_name}
    )
    print("RENAME RESPONSE:", rename_res.json())
    assert rename_res.status_code == 200

    # 3. 결과 검증
    data = rename_res.json()
    assert data["new_name"].startswith(new_name)
    assert Path(f"./storage/{user_id}/{folder_name}/{data['new_name']}").exists()

def test_move_file(client):
    """
    테스트 목적: 업로드된 파일을 다른 폴더로 이동할 수 있는지 검증

    전제 조건:
    - sample.pdf 파일이 원본 폴더에 업로드되어 있어야 함

    검증 내용:
    - 이동 요청 시 status_code == 200
    - 응답에 새로운 경로가 포함되어야 함
    - 이동된 폴더에 파일이 존재해야 함
    """
    user_id = 1
    old_folder = "move_test_src"
    new_folder = "move_test_dest"
    file_name = "sample.pdf"

    file_path = Path("tests/assets/sample.pdf")

    # 1. 원본 폴더에 업로드
    with open(file_path, "rb") as f:
        upload_res = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{old_folder}/files",
            files={"files": (file_name, f, "application/pdf")}
        )
    assert upload_res.status_code == 200
    saved_name = upload_res.json()["success"][0]["saved_name"]

    # 2. 파일 이동 요청
    move_res = client.put(
        f"/api/v1/pdf/users/{user_id}/folders/{old_folder}/files/{saved_name}/move",
        params={"new_folder": new_folder, "create_if_not_exists": True}
    )
    print("MOVE RESPONSE:", move_res.json())
    assert move_res.status_code == 200

    # 3. 파일이 새로운 위치에 실제로 존재하는지 확인
    new_path = Path(f"./storage/{user_id}/{new_folder}/{saved_name}")
    assert new_path.exists()

def test_delete_file(client):
    """
    테스트 목적: 업로드된 PDF 파일을 정상적으로 삭제할 수 있는지 검증

    전제 조건:
    - sample.pdf 파일이 삭제 대상 폴더에 업로드되어 있어야 함

    검증 내용:
    - 삭제 요청 시 status_code == 200
    - 응답에 삭제 대상 파일명이 포함되어야 함
    - 파일이 실제로 삭제되었는지 확인
    """
    user_id = 1
    folder_name = "delete_test"
    file_name = "sample.pdf"

    file_path = Path("tests/assets/sample.pdf")

    # 1. 파일 업로드
    with open(file_path, "rb") as f:
        upload_res = client.post(
            f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files",
            files={"files": (file_name, f, "application/pdf")}
        )
    assert upload_res.status_code == 200
    saved_name = upload_res.json()["success"][0]["saved_name"]

    # 2. 삭제 요청
    delete_res = client.delete(
        f"/api/v1/pdf/users/{user_id}/folders/{folder_name}/files/{saved_name}"
    )
    print("DELETE RESPONSE:", delete_res.json())
    assert delete_res.status_code == 200
    assert delete_res.json()["target"] == saved_name

    # 3. 실제 파일 삭제 확인
    deleted_path = Path(f"./storage/{user_id}/{folder_name}/{saved_name}")
    assert not deleted_path.exists()
