def enqueue_task(
    self, 
    func: Callable, 
    *args, 
    queue_name: str = "default", 
    job_id: Optional[str] = None, 
    job_timeout: int = 3600,
    user_id: Optional[int] = None,
    db: Optional[Session] = None,
    task_type: Optional[str] = None,
    document_id: Optional[int] = None,
    **kwargs
) -> str:
    """
    작업 큐에 태스크 등록
    
    Args:
        func: 실행할 함수
        args: 함수 인자
        queue_name: 큐 이름 (default, pdf, ai)
        job_id: 작업 ID (None인 경우 자동 생성)
        job_timeout: 작업 타임아웃 (초)
        user_id: 작업 소유자 ID (선택)
        db: DB 세션 (선택 - 작업 기록용)
        task_type: 작업 유형 (선택 - 작업 기록용)
        document_id: 문서 ID (선택 - 작업 기록용)
        kwargs: 함수 키워드 인자
        
    Returns:
        작업 ID
    """
    job_id = job_id or f"task_{uuid.uuid4()}"
    
    try:
        queue = self.queues.get(queue_name, self.queues["default"])
        
        # Redis 연결이 없는 경우 (개발/테스트 환경)
        if self.redis_conn is None:
            logger.warning(f"Redis 연결 없음: 작업 {job_id}가 큐에 추가되었다고 가정")
            
            # DB에 작업 기록 (선택)
            if db and user_id and task_type:
                create_task_record(
                    db=db,
                    user_id=user_id,
                    task_type=task_type,
                    document_id=document_id or 0,
                    job_id=job_id
                )
                
            return job_id
        
        # 작업 메타데이터 설정
        meta = {
            "created_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "status": "queued",
            "user_id": user_id
        }
        
        # 작업 설명 생성
        description = f"{func.__name__} 작업"
        if document_id:
            description += f" (문서 ID: {document_id})"
        
        # 작업 등록
        # timeout은 RQ 큐 옵션으로만 사용하고, 함수에는 전달하지 않음
        job = queue.enqueue(
            func,
            *args,
            **kwargs,  # 함수에 전달할 인자
            job_id=job_id,
            timeout=job_timeout,  # RQ 옵션
            result_ttl=86400,     # RQ 옵션
            meta=meta,            # RQ 옵션
            description=description  # RQ 옵션
        )
        
        # DB에 작업 기록 (선택)
        if db and user_id and task_type:
            create_task_record(
                db=db,
                user_id=user_id,
                task_type=task_type,
                document_id=document_id or 0,
                job_id=job_id
            )
        
        logger.info(f"작업 등록 성공: {job_id} (큐: {queue_name})")
        return job_id
        
    except Exception as e:
        logger.error(f"작업 등록 실패: {str(e)}")
        return job_id  # 실패해도 ID 반환 (클라이언트 처리 일관성)
