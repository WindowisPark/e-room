// src/api/authApi.js

import api from '@/api';

const BASE_URL = '/auth';
const headers = { 'Content-Type': 'multipart/form-data' };

export default {

  async login(credentials) {
    const { data } = await api.post(`${BASE_URL}/login`, credentials);
    return data;
  },

  async checkId(id) {
    const { data } = await api.get(`${BASE_URL}/checkid/${id}`);
    return data;
  },

  async get(id) {
    const { data } = await api.get(`${BASE_URL}/${id}`);
    return data;
  },

  async create(member) {
    const payload = {
      email: member.email,
      username: member.username,
      password: member.password,
      full_name: member.full_name,
      phone_number: member.phone_number
    };
    const { data } = await api.post(`${BASE_URL}/register`, payload);
    return data;
  },

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
    return data;
  },

  async delete(id) {
    const { data } = await api.delete(`${BASE_URL}/${id}`);
    return data;
  },

  async kakaoLogin(kakaoAccessToken) {
    const { data } = await api.post(`${BASE_URL}/kakao/token`, { kakao_access_token: kakaoAccessToken });
    return data;
  },

  async changePassword(formData) {
    const { data } = await api.put(`${BASE_URL}/${formData.id}/changepassword`, formData);
    return data;
  },

};
