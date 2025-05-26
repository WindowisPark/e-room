// src/api/authApi.js

import api from '@/api';

const BASE_URL = '/auth';
const headers = { 'Content-Type': 'multipart/form-data' };

export default {

  // 🔐 로그인 요청
  async login(credentials) {
    const { data } = await api.post(`${BASE_URL}/login`, credentials);
    console.log('AUTH LOGIN: ', data);
    return data;
  },

  // ✅ 회원 ID 중복 체크
  async checkId(id) {
    const { data } = await api.get(`${BASE_URL}/checkid/${id}`);
    console.log('AUTH GET CHECK ID', data);
    return data;
  },

  // ✅ 회원 정보 조회 (username == id)
  async get(id) {
    const { data } = await api.get(`${BASE_URL}/${id}`);
    console.log('AUTH GET', data);
    return data;
  },

  // ✅ 회원 가입
  async create(member) {
    const payload = {
      email: member.email,
      username: member.username,
      password: member.password,
      full_name: member.full_name,
      phone_number: member.phone_number
    };

    // ✅ 디버깅용 로그
    const endpoint = `${BASE_URL}/register`;
    console.log('[회원가입 요청] endpoint:', endpoint);
    console.log('[회원가입 요청] payload:', payload);

    const { data } = await api.post(endpoint, payload);
    console.log('AUTH REGISTER:', data);
    return data;
  },

  // ✅ 회원 정보 수정
  async update(member) {
    const formData = new FormData();
    formData.append('id', member.id);
    formData.append('name', member.name);
    formData.append('password', member.password);
    formData.append('email', member.email);
    if (member.avatar) {
      formData.append('avatar', member.avatar);
    }

    const { data } = await api.put(`${BASE_URL}/${member.id}`, formData, headers);
    console.log('AUTH PUT: ', data);
    return data;
  },

  // ✅ 회원 탈퇴
  async delete(id) {
    const { data } = await api.delete(`${BASE_URL}/${id}`);
    console.log('AUTH DELETE: ', data);
    return data;
  },

  // ✅ 비밀번호 수정
  async changePassword(formData) {
    console.log('formData : ', formData);
    const { data } = await api.put(`${BASE_URL}/${formData.id}/changepassword`, formData);
    console.log('AUTH PUT: ', data);
    return data;
  },

};
