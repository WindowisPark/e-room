<template>
  <div class="membership-page">
    <!-- 인사 헤더 -->
    <div class="greeting-header">
      <div>
        <div class="greeting-name">안녕하세요, <span>{{ username }}</span>님 👋</div>
        <div class="greeting-date">{{ todayStr }}</div>
      </div>
    </div>

    <div class="page-container">
      <!-- 좌측: 퀵메뉴 -->
      <div class="left-section">
        <div class="menu-group">
          <div class="menu-group-label">학습</div>
          <div class="career-cards">
            <router-link to="/student/pdf" class="career-card">
              <span class="career-icon">📚</span>
              <div class="career-info">
                <div class="career-title">PDF 학습</div>
                <div class="career-desc">AI가 요약·분석해주는 학습 도우미</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
            <router-link to="/student/ai-tutor" class="career-card">
              <span class="career-icon">🤖</span>
              <div class="career-info">
                <div class="career-title">AI 튜터</div>
                <div class="career-desc">질문하면 바로 답해주는 AI 선생님</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
            <router-link to="/student/calendar" class="career-card">
              <span class="career-icon">🗓️</span>
              <div class="career-info">
                <div class="career-title">캘린더</div>
                <div class="career-desc">나의 학습·취업 일정 관리</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
          </div>
        </div>

        <div class="menu-group" style="margin-top: 24px;">
          <div class="menu-group-label">취업</div>
          <div class="career-cards">
            <router-link to="/student/resume" class="career-card">
              <span class="career-icon">📄</span>
              <div class="career-info">
                <div class="career-title">이력서 · 포트폴리오</div>
                <div class="career-desc">AI가 다듬어주는 나만의 이력서</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
            <router-link to="/student/coverletter" class="career-card">
              <span class="career-icon">✍️</span>
              <div class="career-info">
                <div class="career-title">자기소개서</div>
                <div class="career-desc">AI 초안으로 시작하는 자소서</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
            <router-link to="/student/jobs" class="career-card">
              <span class="career-icon">🔍</span>
              <div class="career-info">
                <div class="career-title">기업 조사</div>
                <div class="career-desc">공고 분석 · 기업 정보 한눈에</div>
              </div>
              <span class="career-arrow">→</span>
            </router-link>
          </div>
        </div>
      </div>

      <!-- 우측: 오늘 일정 + 캘린더 -->
      <div class="right-section">
        <div class="user-info-card">
          <div class="today-task-header">
            <span>오늘의 일정</span>
            <span class="task-count">{{ todayTasks.length }}개</span>
          </div>

          <div class="task-input-row">
            <input
              v-model="newTaskTitle"
              placeholder="새 일정 입력..."
              @keyup.enter="addTask"
            />
            <button @click="addTask">추가</button>
          </div>

          <ul class="task-list" v-if="todayTasks.length">
            <li v-for="task in todayTasks" :key="task.id" :class="{ done: task.is_completed }">
              <span class="task-check" @click="toggle(task)">
                <i :class="task.is_completed ? 'fa-solid fa-circle-check' : 'fa-regular fa-circle'"></i>
              </span>
              <span class="task-title">{{ task.title }}</span>
              <button class="task-del" @click="remove(task)">×</button>
            </li>
          </ul>

          <div class="no-task-msg" v-else>
            <i class="fa-regular fa-calendar-xmark"></i>
            오늘 등록된 일정이 없습니다.
          </div>

          <div class="calendar-container">
            <v-calendar
              :attributes="calendarAttributes"
              :is-expanded="true"
              :columns="1"
              :rows="1"
              title-position="left"
              class="custom-calendar"
              color="indigo"
              :masks="masks"
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import 'v-calendar/dist/style.css';
import { useAuthStore } from '@/stores/auth';
import calendarApi from '@/api/calendarApi';

const authStore = useAuthStore();
const username = computed(() => authStore.username);

const today = new Date();
const todayStr = computed(() =>
  `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일`
);

const masks = { title: 'YYYY년 M월' };

// 캘린더 — 오늘 하이라이트만
const calendarAttributes = computed(() => [
  {
    key: 'today',
    highlight: { color: 'indigo', fillMode: 'solid' },
    dates: new Date()
  }
]);

// 오늘 일정
const todayTasks = ref([]);
const newTaskTitle = ref('');

async function loadTodayTasks() {
  try {
    const iso = today.toISOString().slice(0, 10);
    const res = await calendarApi.getTasks(iso);
    todayTasks.value = res.data ?? [];
  } catch {
    todayTasks.value = [];
  }
}

async function addTask() {
  if (!newTaskTitle.value.trim()) return;
  const iso = today.toISOString().slice(0, 10);
  await calendarApi.createTask(newTaskTitle.value.trim(), iso);
  newTaskTitle.value = '';
  await loadTodayTasks();
}

async function toggle(task) {
  await calendarApi.toggleTask(task.id);
  await loadTodayTasks();
}

async function remove(task) {
  await calendarApi.deleteTask(task.id);
  await loadTodayTasks();
}

onMounted(() => {
  loadTodayTasks();
});

</script>

<style scoped>
.membership-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-page);
  color: var(--text-primary);
  background-color: var(--bg-page);
  min-height: calc(100vh - 60px);
}

/* 인사 헤더 */
.greeting-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.greeting-name {
  font-size: 1.4rem;
  font-weight: 800;
  color: #1a1a1a;
}

.greeting-name span {
  color: #F76707;
}

.greeting-date {
  font-size: 0.88rem;
  color: #888;
  margin-top: 4px;
}

/* 페이지 레이아웃 */
.page-container {
  display: flex;
  gap: 30px;
  position: relative;
  margin-bottom: 30px;
}

.left-section {
  flex: 3;
  background: linear-gradient(135deg, #FFFAF4, #FFF6E8);
  border-radius: 20px;
  padding: 35px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.07);
}

.right-section {
  flex: 2;
}

/* 메뉴 그룹 */
.menu-group-label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #aaa;
  text-transform: uppercase;
  margin-bottom: 10px;
}

/* 퀵메뉴 카드 */
.career-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.career-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border-left: 4px solid transparent;
  text-decoration: none;
  color: inherit;
  transition: border-left-color 0.2s, box-shadow 0.2s;
}

.career-card:hover {
  border-left-color: #F76707;
  box-shadow: 0 6px 16px rgba(247, 103, 7, 0.12);
}

.career-icon {
  font-size: 1.6rem;
  flex-shrink: 0;
}

.career-info {
  flex: 1;
}

.career-title {
  font-size: 1rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 4px;
}

.career-desc {
  font-size: 0.85rem;
  color: #888;
}

.career-arrow {
  font-size: 1.2rem;
  color: #F76707;
  flex-shrink: 0;
}

/* 우측 카드 */
.user-info-card {
  background-color: #fff9ef;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.07);
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 오늘 일정 헤더 */
.today-task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 14px;
}

.task-count {
  background: #FFF3E8;
  color: #F76707;
  border-radius: 50px;
  padding: 2px 10px;
  font-size: 0.82rem;
  font-weight: 700;
}

/* 입력 */
.task-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.task-input-row input {
  flex: 1;
  border: 1.5px solid #eee;
  border-radius: 8px;
  padding: 9px 14px;
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.2s;
  background: white;
}

.task-input-row input:focus {
  border-color: #F76707;
}

.task-input-row button {
  background: #F76707;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  font-size: 0.88rem;
}

/* 일정 목록 */
.task-list {
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fafafa;
  border-radius: 10px;
  transition: background 0.15s;
}

.task-list li.done .task-title {
  text-decoration: line-through;
  color: #bbb;
}

.task-check {
  cursor: pointer;
  color: #F76707;
  font-size: 1.1rem;
}

.task-title {
  flex: 1;
  font-size: 0.9rem;
  color: #333;
}

.task-del {
  background: none;
  border: none;
  color: #ccc;
  font-size: 1rem;
  cursor: pointer;
  padding: 0 4px;
}

.task-del:hover {
  color: #e74c3c;
}

/* 일정 없음 */
.no-task-msg {
  text-align: center;
  padding: 20px;
  color: #bbb;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.no-task-msg i {
  font-size: 1.8rem;
}

/* 캘린더 */
.calendar-container {
  margin-top: 10px;
  width: 100%;
}

:deep(.custom-calendar) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  background-color: white;
  width: 100%;
}

:deep(.vc-title) {
  font-weight: bold;
  font-size: 20px;
  background-color: white;
}

:deep(.vc-weekday) {
  color: #888;
  font-size: 14px;
  font-weight: normal;
}

:deep(.vc-day) {
  font-size: 14px;
  color: #333;
  height: 50px;
}

:deep(.vc-day-content) {
  height: 45px;
  width: 45px;
  align-items: center;
  justify-content: center;
}

:deep(.vc-container) {
  border: none;
}

:deep(.vc-highlight) {
  background-color: #ff7300;
}

:deep(.vc-day.is-today) {
  font-weight: bold;
}

:deep(.vc-day.is-not-in-month) {
  opacity: 0.4;
}


/* 반응형 */
@media (max-width: 768px) {
  .page-container {
    flex-direction: column;
  }

  .right-section {
    margin-top: 0;
  }

  .left-section {
    padding: 25px;
  }
}
</style>
