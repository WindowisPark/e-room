# app/core/pdf_processor.py
import re
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime

class PDFProcessor:
    """
    PDF 주석, 태그, 멘션 처리 클래스
    """
    
    @staticmethod
    def parse_mentions_and_tags(content: str) -> Tuple[List[str], List[str]]:
        """
        텍스트 내용에서 멘션(@사용자)과 태그(#태그) 추출
        
        Args:
            content: 파싱할 텍스트 내용
            
        Returns:
            (멘션 목록, 태그 목록) 튜플
        """
        # @username 패턴 찾기
        mentions = re.findall(r"@(\w+)", content)
        
        # #tag 패턴 찾기
        tags = re.findall(r"#(\w+)", content)
        
        return mentions, tags
    
    @staticmethod
    def create_annotation(
        pdf_id: int,
        user_id: int,
        page: int,
        content: str,
        position: Dict[str, float],
        annotation_type: str = "highlight"
    ) -> Dict[str, Any]:
        """
        주석 객체 생성
        
        Args:
            pdf_id: PDF 문서 ID
            user_id: 주석 작성자 ID
            page: 페이지 번호 (1부터 시작)
            content: 주석 내용
            position: 좌표 정보 딕셔너리 (x1, y1, x2, y2) - 페이지 크기 대비 백분율
            annotation_type: 주석 타입 (highlight, note, underline 등)
            
        Returns:
            주석 정보를 담은 딕셔너리
        """
        mentions, tags = PDFProcessor.parse_mentions_and_tags(content)
        
        annotation = {
            "pdf_id": pdf_id,
            "user_id": user_id,
            "page": page,
            "content": content,
            "position": position,
            "type": annotation_type,
            "created_at": datetime.now().isoformat(),
            "mentions": mentions,
            "tags": tags
        }
        
        return annotation
    
    @staticmethod
    def serialize_annotations(annotations: List[Dict[str, Any]]) -> str:
        """
        주석 목록을 JSON 문자열로 직렬화
        
        Args:
            annotations: 주석 딕셔너리 목록
            
        Returns:
            JSON 문자열
        """
        return json.dumps(annotations, ensure_ascii=False)
    
    @staticmethod
    def deserialize_annotations(json_data: str) -> List[Dict[str, Any]]:
        """
        JSON 문자열에서 주석 목록 복원
        
        Args:
            json_data: 주석 JSON 문자열
            
        Returns:
            주석 딕셔너리 목록
        """
        return json.loads(json_data)
    
    @staticmethod
    def merge_annotations(
        existing_annotations: List[Dict[str, Any]],
        new_annotation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        새 주석을 기존 주석 목록에 병합 (중복 방지)
        
        Args:
            existing_annotations: 기존 주석 목록
            new_annotation: 추가할 새 주석
            
        Returns:
            업데이트된 주석 목록
        """
        # 새 주석에 ID가 없으면 고유 ID 생성
        if "id" not in new_annotation:
            # 타임스탬프와 사용자 ID로 간단한 고유 ID 생성
            new_annotation["id"] = f"{new_annotation['user_id']}_{datetime.now().timestamp()}"
            
        # 동일 ID를 가진 주석이 있는지 확인
        for i, annotation in enumerate(existing_annotations):
            if annotation.get("id") == new_annotation["id"]:
                # 기존 주석 업데이트
                existing_annotations[i] = new_annotation
                return existing_annotations
        
        # 새 주석 추가
        existing_annotations.append(new_annotation)
        return existing_annotations