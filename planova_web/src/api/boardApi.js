import api from '@/api';

const BASE_URL = '/board';
const headers = { 'Content-Type': 'multipart/form-data' };

export default {
  async getList(params) {
    const { data } = await api.get(BASE_URL, { params });
    return data;
  },

  async get(no) {
    const { data } = await api.get(`${BASE_URL}/${no}`);
    return data;
  },

  async getTypes() {
    const { data } = await api.get(`${BASE_URL}/types`);
    return data;
  },

  async create(article) {
    const formData = new FormData();
    formData.append('title', article.title);
    formData.append('type', article.type);
    formData.append('writer', article.writer);
    formData.append('content', article.content);
    if (article.files) {
      for (let i = 0; i < article.files.length; i++) {
        formData.append('files', article.files[i]);
      }
    }
    const { data } = await api.post(BASE_URL, formData, { headers });
    return data;
  },

  async update(article) {
    const formData = new FormData();
    formData.append('bno', article.bno);
    formData.append('type', article.type);
    formData.append('title', article.title);
    formData.append('content', article.content);
    if (article.files) {
      for (let i = 0; i < article.files.length; i++) {
        formData.append('files', article.files[i]);
      }
    }
    const { data } = await api.put(`${BASE_URL}/${article.bno}`, formData, { headers });
    return data;
  },

  async delete(no) {
    const { data } = await api.delete(`${BASE_URL}/${no}`);
    return data;
  },

  async deleteAttachment(no) {
    const { data } = await api.delete(`${BASE_URL}/attachment/${no}`);
    return data;
  },

  async sendReply(reply) {
    const { data } = await api.post(`${BASE_URL}/reply/${reply.bno}`, reply);
    return data;
  },

  async deleteReply(rno) {
    const { data } = await api.delete(`${BASE_URL}/reply/${rno}`);
    return data;
  },
};
