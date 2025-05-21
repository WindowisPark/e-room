import os
from typing import Optional
import logging
from datetime import datetime
from fpdf import FPDF
import tempfile

logger = logging.getLogger(__name__)

class PDFConverter:
    """텍스트 문서를 PDF로 변환하는 서비스"""
    
    @staticmethod
    def text_to_pdf(text: str, title: str, user_id: int) -> Optional[str]:
        logger.info(f"PDF 변환 시작: 사용자={user_id}, 제목={title}, 텍스트 길이={len(text)}")

        try:
            pdf = FPDF()
            pdf.add_page()

            # ✅ 폰트 경로 자동 탐색
            font_paths = [
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                '/usr/share/fonts/nanum/NanumGothic.ttf',
                '/usr/local/share/fonts/NanumGothic.ttf',
                './fonts/NanumGothic.ttf'
            ]
            font_path = next((p for p in font_paths if os.path.exists(p)), None)

            # ✅ 폰트 설정 및 로깅
            if font_path:
                logger.info(f"사용할 폰트 경로: {font_path}")
                pdf.add_font('NanumGothic', '', font_path, uni=True)
                pdf.set_font('NanumGothic', '', 12)
                font_name = 'NanumGothic'
            else:
                logger.warning("나눔 고딕 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
                pdf.set_font('Arial', '', 12)
                font_name = 'Arial'

            # 제목 출력
            pdf.set_font(font_name, '', 16)
            pdf.cell(200, 10, txt=title, ln=True, align='C')
            pdf.ln(10)

            # 본문 출력
            pdf.set_font(font_name, '', 12)
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                if not para.strip():
                    continue
                lines = para.split("\n")
                for line in lines:
                    pdf.multi_cell(0, 10, txt=line)
                pdf.ln(5)

            # 저장 경로 설정
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"summary_{timestamp}.pdf"
            user_dir = f"storage/users/{user_id}/summary"
            os.makedirs(user_dir, exist_ok=True)
            filepath = os.path.join(user_dir, filename)

            # ✅ 파일 저장 및 로깅
            try:
                pdf.output(filepath)
                logger.info(f"PDF 파일 생성 완료: {filepath}, 크기: {os.path.getsize(filepath)} 바이트")
                return filepath
            except Exception as e:
                logger.error(f"PDF 파일 생성 실패: {filepath}, 오류: {str(e)}", exc_info=True)
                return None

        except Exception as e:
            logger.error(f"PDF 생성 중 예외 발생: {str(e)}", exc_info=True)
            return None