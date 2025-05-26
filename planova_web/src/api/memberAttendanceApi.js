// src/services/api/memberAttendanceApi.js
import instance from '@/api/index.js';

const BASE_URL = '/attendance';  // ✅ 상대 경로로 수정

export const memberAttendanceApi = {
  /**
   * 출석체크 요청
   * @returns {Promise} 출석체크 결과
   */
  checkAttendance() {
    return instance.post(`${BASE_URL}/`);
  },

  /**
   * 현재 출석 상태 조회
   * @returns {Promise} 출석 상태 정보
   */
  getAttendanceStatus() {
    return instance.get(`${BASE_URL}/`);
  },

  /**
   * 출석 기록 조회
   * @param {Object} params - 조회 파라미터
   * @returns {Promise} 출석 기록 목록
   */
  getAttendanceHistory(params = {}) {
    return instance.get(`${BASE_URL}/history/`, { params });
  }
};

export default memberAttendanceApi;