class AppException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundException(AppException): pass      # → 404
class ConflictException(AppException): pass      # → 409
class ForbiddenException(AppException): pass     # → 403
class UnauthorizedException(AppException): pass  # → 401
class BadRequestException(AppException): pass    # → 400
class DatabaseException(AppException): pass      # → 500


class ErrorMessage:
    # 인증
    AUTH_REQUIRED           = "인증이 필요합니다"
    TOKEN_REVOKED           = "토큰이 취소되었습니다"
    TOKEN_INVALID           = "유효하지 않은 토큰입니다"
    REFRESH_TOKEN_INVALID   = "유효하지 않은 리프레시 토큰입니다"
    CREDENTIALS_INVALID     = "인증 정보를 확인할 수 없습니다"
    LOGIN_FAILED            = "이메일 또는 비밀번호가 올바르지 않습니다"

    # 사용자
    USER_NOT_FOUND          = "사용자를 찾을 수 없습니다"
    USER_INACTIVE           = "비활성화된 사용자입니다"
    EMAIL_ALREADY_EXISTS    = "이미 등록된 이메일입니다"
    USERNAME_ALREADY_EXISTS = "이미 사용 중인 사용자명입니다"
    ADMIN_REQUIRED          = "관리자 권한이 필요합니다"

    # 리소스
    RESUME_NOT_FOUND        = "이력서를 찾을 수 없습니다"
    ITEM_NOT_FOUND          = "항목을 찾을 수 없습니다"
    COVER_LETTER_NOT_FOUND  = "자소서를 찾을 수 없습니다"
    PAYMENT_NOT_FOUND       = "결제 정보를 찾을 수 없습니다"
    SESSION_NOT_FOUND       = "세션을 찾을 수 없습니다"

    # 비즈니스
    JOB_INPUT_REQUIRED      = "url 또는 text 중 하나를 입력해주세요"
    JOB_FETCH_FAILED        = "공고 내용을 가져올 수 없습니다. 텍스트를 직접 입력해주세요"

    # DB / 서버
    DB_ERROR                = "데이터베이스 오류가 발생했습니다"
    SERVER_ERROR            = "서버 오류가 발생했습니다"
