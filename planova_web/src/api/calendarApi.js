import api from '@/api';

const BASE = '/calendar';

export default {
  getTasks(date) {
    return api.get(`${BASE}/tasks`, { params: { date } });
  },
  createTask(title, taskDate) {
    return api.post(`${BASE}/tasks`, { title, task_date: taskDate });
  },
  toggleTask(id) {
    return api.patch(`${BASE}/tasks/${id}/toggle`);
  },
  deleteTask(id) {
    return api.delete(`${BASE}/tasks/${id}`);
  },

  getGoals(year, month, week) {
    return api.get(`${BASE}/goals`, { params: { year, month, week } });
  },
  createGoal(title, year, month, week) {
    return api.post(`${BASE}/goals`, { title, year, month, week });
  },
  toggleGoal(id) {
    return api.patch(`${BASE}/goals/${id}/toggle`);
  },
  deleteGoal(id) {
    return api.delete(`${BASE}/goals/${id}`);
  },
};
