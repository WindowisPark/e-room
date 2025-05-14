def get_job_status(self, job_id: str) -> Dict[str, Any]:
    """
    작업 상태 조회
    
    Args:
        job_id: 작업 ID
        
    Returns:
        작업 상태 정보
    """
    try:
        # Redis 연결이 없는 경우 (개발/테스트 환경)
        if self.redis_conn is None:
            logger.warning(f"Redis 연결 없음: 작업 {job_id}의 상태 조회 불가")
            return {
                "status": "unknown",
                "progress": 0,
                "message": "Redis 연결 없음 (개발 모드)"
            }
        
        # 모든 큐에서 작업 찾기
        job = None
        for queue_name, queue in self.queues.items():
            job = queue.fetch_job(job_id)
            if job:
                break
        
        # 스케줄러에서 작업 찾기
        if not job and self.scheduler:
            for scheduled_job in self.scheduler.get_jobs():
                if scheduled_job.id == job_id:
                    job = scheduled_job
                    break
        
        if not job:
            return {"status": "not_found"}
            
        # 메타데이터 안전하게 추출
        meta = {}
        try:
            if hasattr(job, 'meta') and job.meta:
                for key, value in job.meta.items():
                    # 문자열로 안전하게 변환
                    if isinstance(value, (str, int, float, bool, type(None))):
                        meta[key] = value
                    else:
                        # 복잡한 객체는 문자열로 변환
                        try:
                            meta[key] = str(value)
                        except:
                            meta[key] = "복잡한 객체 (표시 불가)"
        except Exception as e:
            logger.error(f"메타데이터 처리 오류: {str(e)}")
            meta = {}
        
        # 결과 처리 (pickle 직렬화된 바이너리 데이터 처리)
        result = None
        if job.is_finished:
            try:
                import pickle
                # job.result가 바이너리인 경우 pickle.loads로 디코딩 시도
                if isinstance(job.result, bytes):
                    try:
                        result = pickle.loads(job.result)
                    except Exception as e:
                        logger.warning(f"피클 디코딩 실패: {e}")
                        result = "바이너리 데이터 (디코딩 실패)"
                else:
                    result = job.result
            except Exception as e:
                logger.error(f"결과 처리 중 오류: {str(e)}")
                result = f"결과 처리 오류: {str(e)}"
        
        # 결과 구성
        return {
            "status": job.get_status(),
            "progress": meta.get("progress", 0),
            "result": result,
            "error": job.exc_info if job.is_failed else None,
            "created_at": meta.get("created_at"),
            "updated_at": datetime.utcnow().isoformat(),
            "message": meta.get("message", "작업 진행 중"),
            "scheduled_at": meta.get("scheduled_at")
        }
        
    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {str(e)}")
        return {"status": "error", "message": str(e)}
