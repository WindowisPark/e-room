<template>
  <div class="dashboard">
    <!-- 프로필 헤더 -->
    <div class="profile-header">
      <div class="profile-greeting">
        <span class="greeting-text">안녕하세요, <strong>{{ userName }}</strong>님!</span>
        <span class="journey-text">플래노바 <span class="accent">{{ daysSinceSignup }}</span>일째 여정</span>
      </div>
    </div>

    <!-- 토스트 -->
    <div class="toast-container" v-if="showToastFlag">
      <div class="toast-message">{{ toastMessage }}</div>
    </div>

    <!-- 상단 그리드: 출석 + 오늘 할 일 -->
    <div class="top-grid">
      <!-- 출석 카드 -->
      <div class="card attendance-card">
        <h3 class="card-title">출석 스트릭</h3>
        <div class="attendance-row">
          <div class="day-circle">
            <div class="day-number">{{ currentDay }}</div>
            <div class="day-texts">
              <div class="day-greeting">연속 출석</div>
              <div class="day-status">{{ consecutiveDays }}일째</div>
            </div>
          </div>
          <div class="progress-container">
            <div class="progress-dots">
              <template v-for="day in 7" :key="day">
                <div :class="['dot', attendanceStatus.completedDays.includes(day) ? 'completed' : '']">
                  <span v-if="attendanceStatus.completedDays.includes(day)" class="check-icon">✓</span>
                  <span v-else>{{ day }}</span>
                </div>
              </template>
            </div>
            <div class="progress-bar">
              <div class="progress-filled" :style="{ width: progressFillWidth }"></div>
            </div>
          </div>
          <button :class="attendanceBtnClass" @click="checkAttendance" :disabled="isLoading || !attendanceStatus.canCheckToday">
            {{ buttonText }}
          </button>
        </div>
      </div>

      <!-- 오늘의 할 일 -->
      <div class="card today-tasks-card">
        <h3 class="card-title">오늘의 할 일 <span class="task-date">{{ formattedToday }}</span></h3>
        <div v-if="tasksLoading" class="empty-state">불러오는 중...</div>
        <div v-else-if="todayTasks.length === 0" class="empty-state">
          오늘 등록된 할 일이 없습니다.<br>
          <span class="link-text" @click="router.push('/student/calendar')">캘린더에서 추가하기 →</span>
        </div>
        <ul v-else class="task-list">
          <li
            v-for="task in todayTasks"
            :key="task.id"
            :class="['task-item', task.is_completed ? 'done' : '']"
            @click="handleToggleTask(task)"
          >
            <span class="task-check">{{ task.is_completed ? '✓' : '○' }}</span>
            <span class="task-title">{{ task.title }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- 빠른 바로가기 -->
    <div class="card shortcuts-card">
      <h3 class="card-title">빠른 바로가기</h3>
      <div class="shortcuts-grid">
        <div class="shortcut-item" @click="router.push('/student/resume')">
          <div class="shortcut-icon">📄</div>
          <div class="shortcut-label">이력서</div>
          <div class="shortcut-count">{{ resumeCount }}개</div>
        </div>
        <div class="shortcut-item" @click="router.push('/student/coverletter')">
          <div class="shortcut-icon">✉️</div>
          <div class="shortcut-label">자소서</div>
          <div class="shortcut-count">{{ clCount }}개</div>
        </div>
        <div class="shortcut-item" @click="router.push('/student/jobs')">
          <div class="shortcut-icon">🏢</div>
          <div class="shortcut-label">기업조사</div>
          <div class="shortcut-count">{{ jobsCount }}개</div>
        </div>
        <div class="shortcut-item" @click="router.push('/student/calendar')">
          <div class="shortcut-icon">📅</div>
          <div class="shortcut-label">캘린더</div>
          <div class="shortcut-count">{{ todayTasks.length }}건</div>
        </div>
        <div class="shortcut-item" @click="router.push('/student/pdf')">
          <div class="shortcut-icon">📚</div>
          <div class="shortcut-label">PDF</div>
          <div class="shortcut-count">{{ pdfCount }}개</div>
        </div>
      </div>
    </div>

    <!-- 하단 그리드: 최근 활동 + 달성 배지 -->
    <div class="bottom-grid">
      <!-- 최근 활동 -->
      <div class="card activity-card">
        <h3 class="card-title">최근 활동</h3>
        <div v-if="recentActivity.length === 0" class="empty-state">아직 활동 내역이 없습니다.</div>
        <ul v-else class="activity-list">
          <li v-for="item in recentActivity" :key="item.id + item.type" class="activity-item">
            <span class="activity-icon">{{ item.icon }}</span>
            <div class="activity-info">
              <span class="activity-name">{{ item.name }}</span>
              <span class="activity-type">{{ item.typeLabel }}</span>
            </div>
            <span class="activity-date">{{ item.relativeDate }}</span>
          </li>
        </ul>
      </div>

      <!-- 달성 배지 & 플래니 진화 -->
      <div class="card evolution-card">
        <h3 class="card-title">달성 배지 &amp; 플래니</h3>
        <div class="evolution-inner">
          <!-- 왼쪽: 플래니 -->
          <div class="planny-side">
            <PlannySvg :size="110" :stage="evolutionStage" />
            <div class="evo-name">{{ evolutionInfo.name }}</div>
            <div class="evo-count">{{ earnedCount }}/6 배지 획득</div>
            <div class="evo-next" v-if="evolutionInfo.next">
              다음 진화까지 {{ evolutionInfo.next - earnedCount }}개
            </div>
            <div class="evo-next complete" v-else>🎉 완전 진화!</div>
          </div>
          <!-- 오른쪽: 배지 그리드 -->
          <div class="badges-side">
            <div class="badges-grid">
              <div
                v-for="badge in badges"
                :key="badge.id"
                :class="['badge-item', badge.earned ? 'earned' : 'locked']"
                :title="badge.condition"
              >
                <div class="badge-icon">{{ badge.icon }}</div>
                <div class="badge-name">{{ badge.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 하단 홍보 배너 -->
    <PromoBannerCarousel />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';
import calendarApi from '@/api/calendarApi';
import PlannySvg from '@/components/PlannySvg.vue';
import PromoBannerCarousel from '@/components/PromoBannerCarousel.vue';

const router = useRouter();

// ── 사용자 정보 ──────────────────────────────────
const userName = ref('');
const daysSinceSignup = ref(0);
const pdfCount = ref(0);

// ── 오늘 날짜 ────────────────────────────────────
const todayStr = () => new Date().toISOString().split('T')[0];
const today = new Date();
const formattedToday = today.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' });

// ── 출석 ─────────────────────────────────────────
const currentDay = ref(1);
const consecutiveDays = ref(1);
const progressFillWidth = ref('0%');
const isLoading = ref(false);
const attendanceStatus = reactive({
  lastCheckDate: null,
  completedDays: [1],
  canCheckToday: true,
});

// daysSinceSignup 기준으로 출석 상태 초기화 (백엔드 값과 동기화)
const initAttendanceFromBackend = (totalDays) => {
  consecutiveDays.value = totalDays;
  const dayInCycle = ((totalDays - 1) % 7) + 1; // 1~7 순환
  currentDay.value = dayInCycle;
  attendanceStatus.completedDays = Array.from({ length: dayInCycle }, (_, i) => i + 1);
  progressFillWidth.value = `${(dayInCycle - 1) * 16.66}%`;

  // 오늘 이미 방문 여부 → localStorage로만 체크
  const lastCheck = localStorage.getItem('lastAttendanceDate');
  if (lastCheck) {
    const last = new Date(lastCheck);
    const now = new Date();
    const isNewDay =
      last.getDate() !== now.getDate() ||
      last.getMonth() !== now.getMonth() ||
      last.getFullYear() !== now.getFullYear();
    attendanceStatus.canCheckToday = isNewDay;
  }
};

const loadAttendanceData = () => {
  // 레거시 localStorage 데이터는 무시하고 백엔드 값으로 대체
  // (initAttendanceFromBackend에서 처리)
  const savedData = localStorage.getItem('attendanceData');
  if (savedData) {
    const data = JSON.parse(savedData);
    currentDay.value = data.currentDay;
    consecutiveDays.value = data.consecutiveDays;
    attendanceStatus.completedDays = data.completedDays;
    attendanceStatus.lastCheckDate = data.lastCheckDate;
    const lastCheck = new Date(data.lastCheckDate);
    const now = new Date();
    const isNewDay =
      lastCheck.getDate() !== now.getDate() ||
      lastCheck.getMonth() !== now.getMonth() ||
      lastCheck.getFullYear() !== now.getFullYear();
    attendanceStatus.canCheckToday = isNewDay;
    progressFillWidth.value = `${(currentDay.value - 1) * 16.66}%`;
  }
};


const checkAttendance = async () => {
  if (!attendanceStatus.canCheckToday) {
    showToast('오늘은 이미 출석체크를 완료했습니다!');
    return;
  }
  isLoading.value = true;
  try {
    attendanceStatus.lastCheckDate = new Date().toISOString();
    attendanceStatus.canCheckToday = false;
    localStorage.setItem('lastAttendanceDate', new Date().toISOString());
    showToast('출석체크 완료!');
  } finally {
    isLoading.value = false;
  }
};

const buttonText = computed(() => {
  if (isLoading.value) return '처리 중...';
  if (!attendanceStatus.canCheckToday) return '완료';
  return '출석';
});

const attendanceBtnClass = computed(() =>
  attendanceStatus.canCheckToday ? 'attendance-btn' : 'attendance-btn completed'
);

// ── 토스트 ────────────────────────────────────────
const toastMessage = ref('');
const showToastFlag = ref(false);
const showToast = (message) => {
  toastMessage.value = message;
  showToastFlag.value = true;
  setTimeout(() => { showToastFlag.value = false; }, 3000);
};

// ── 오늘 할 일 ────────────────────────────────────
const todayTasks = ref([]);
const tasksLoading = ref(true);

const handleToggleTask = async (task) => {
  try {
    await calendarApi.toggleTask(task.id);
    task.is_completed = !task.is_completed;
  } catch {
    showToast('상태 변경에 실패했습니다.');
  }
};

// ── 빠른 바로가기 카운트 ──────────────────────────
const resumeCount = ref(0);
const clCount = ref(0);
const jobsCount = ref(0);

// ── 최근 활동 ─────────────────────────────────────
const recentActivity = ref([]);

const relativeDate = (dateStr) => {
  if (!dateStr) return '';
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  if (diff === 0) return '오늘';
  if (diff === 1) return '어제';
  return `${diff}일 전`;
};

const buildActivityFeed = (resumeData, jobsData, clData) => {
  const items = [];
  const take2 = (arr, icon, typeLabel) =>
    (arr || []).slice(0, 2).map((item, i) => ({
      id: item.id ?? i,
      type: typeLabel,
      icon,
      typeLabel,
      name: item.name || item.title || item.company_name || '(제목 없음)',
      date: item.updated_at || item.created_at || null,
      relativeDate: relativeDate(item.updated_at || item.created_at),
    }));

  items.push(...take2(resumeData, '📄', '이력서'));
  items.push(...take2(jobsData, '🏢', '기업조사'));
  items.push(...take2(clData, '✉️', '자소서'));

  items.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
  recentActivity.value = items.slice(0, 5);
};

// ── 배지 & 진화 ───────────────────────────────────
const badges = computed(() => [
  { id: 'first',    icon: '🌱', name: '첫걸음',     condition: '플래노바 시작',       earned: true },
  { id: 'resume',   icon: '📝', name: '이력서 작성자', condition: '이력서 1개 이상',    earned: resumeCount.value > 0 },
  { id: 'jobs',     icon: '🔍', name: '기업탐정',    condition: '기업조사 3개 이상',   earned: jobsCount.value >= 3 },
  { id: 'cl',       icon: '✉️', name: '스토리텔러',  condition: '자소서 1개 이상',     earned: clCount.value >= 1 },
  { id: 'planner',  icon: '📅', name: '플래너',      condition: '오늘 할 일 등록',     earned: todayTasks.value.length > 0 },
  { id: 'streak7',  icon: '🔥', name: '7일 전사',    condition: '7일 연속 출석',       earned: consecutiveDays.value >= 7 },
]);

const earnedCount = computed(() => badges.value.filter(b => b.earned).length);

const evolutionStage = computed(() => {
  if (earnedCount.value >= 6) return 4;
  if (earnedCount.value >= 4) return 3;
  if (earnedCount.value >= 2) return 2;
  return 1;
});

const evolutionInfo = computed(() => {
  const map = {
    1: { name: '잠든 행성',     next: 2, desc: '첫 배지를 획득했어요!' },
    2: { name: '성장 중',       next: 4, desc: '플래니가 눈을 떴어요.' },
    3: { name: '빛나는 탐험가', next: 6, desc: '반짝이기 시작했어요!' },
    4: { name: '완전체 플래니', next: null, desc: '모든 배지를 달성했어요!' },
  };
  return map[evolutionStage.value];
});

// ── onMounted ─────────────────────────────────────
onMounted(async () => {
  const [detailsRes, tasksRes, resumeRes, jobsRes, clRes] = await Promise.allSettled([
    api.get('/users/me/details'),
    calendarApi.getTasks(todayStr()),
    api.get('/resume/profiles'),
    api.get('/jobs'),
    api.get('/coverletter'),
  ]);

  if (detailsRes.status === 'fulfilled') {
    const d = detailsRes.value.data;
    const info = d.user_info ?? d.user ?? {};
    userName.value = info.full_name || info.username || info.email || '사용자';
    const totalDays = (d.signup_info?.days_since_signup ?? 0) + 1;
    daysSinceSignup.value = totalDays;
    pdfCount.value = d.storage?.total_pdfs ?? 0;
    // 출석 스트릭을 백엔드 가입일수와 동기화
    initAttendanceFromBackend(totalDays);
  } else {
    loadAttendanceData(); // 백엔드 실패 시 로컬 폴백
  }

  tasksLoading.value = false;
  if (tasksRes.status === 'fulfilled') {
    todayTasks.value = tasksRes.value.data || [];
  }

  const resumeData = resumeRes.status === 'fulfilled' ? (resumeRes.value.data || []) : [];
  const jobsData   = jobsRes.status === 'fulfilled'   ? (jobsRes.value.data || [])   : [];
  const clData     = clRes.status === 'fulfilled'     ? (clRes.value.data || [])     : [];

  resumeCount.value = resumeData.length;
  jobsCount.value   = jobsData.length;
  clCount.value     = clData.length;

  buildActivityFeed(resumeData, jobsData, clData);
});
</script>

<style scoped>
.dashboard {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: var(--space-page);
  background-color: var(--bg-page);
  color: var(--text-primary);
  position: relative;
}

/* ── 프로필 헤더 ── */
.profile-header {
  width: 95%;
  margin: 0 auto 20px auto;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
}

.profile-greeting {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.greeting-text {
  font-size: 20px;
  font-weight: 600;
  color: #222;
}

.journey-text {
  font-size: 15px;
  color: #777;
}

.accent {
  color: #F76707;
  font-weight: 800;
}

/* ── 토스트 ── */
.toast-container {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.toast-message {
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 12px 24px;
  border-radius: 24px;
  font-size: 14px;
  white-space: nowrap;
}

/* ── 공용 카드 ── */
.card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-card);
  box-shadow: var(--shadow-card);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-date {
  font-size: 13px;
  font-weight: 400;
  color: #999;
}

/* ── 상단 그리드 ── */
.top-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  width: 95%;
  margin: 0 auto 20px auto;
}

/* 출석 카드 */
.attendance-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.day-circle {
  width: 90px;
  height: 90px;
  background-color: #F76707;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  padding: 10px;
  box-shadow: 0 4px 8px rgba(247, 103, 7, 0.3);
  flex-shrink: 0;
}

.day-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: white;
  color: #F76707;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 6px;
}

.day-texts { text-align: center; }

.day-greeting {
  font-size: 11px;
  margin-bottom: 2px;
  opacity: 0.9;
}

.day-status {
  font-size: 13px;
  font-weight: bold;
}

.progress-container {
  flex: 1;
  margin: 0 20px;
}

.progress-dots {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #eee;
  font-size: 12px;
  color: #666;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  margin-top: 5px;
  z-index: 2;
}

.dot.completed {
  background-color: #F76707;
  color: white;
  box-shadow: 0 2px 6px rgba(247, 103, 7, 0.4);
}

.check-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.progress-bar {
  height: 4px;
  background-color: #eee;
  border-radius: 2px;
  margin-top: -14px;
  z-index: 1;
  position: relative;
  top: -8px;
}

.progress-filled {
  height: 100%;
  background-color: #F76707;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.attendance-btn {
  background-color: #F76707;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 22px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(247, 103, 7, 0.3);
  transition: all 0.2s ease;
  min-width: 80px;
  flex-shrink: 0;
}

.attendance-btn:hover:not(:disabled) {
  background-color: #e05e00;
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(247, 103, 7, 0.4);
}

.attendance-btn:disabled { cursor: not-allowed; opacity: 0.8; }

.attendance-btn.completed {
  background-color: #777;
  box-shadow: 0 4px 8px rgba(119, 119, 119, 0.3);
}

/* 오늘 할 일 */
.today-tasks-card { display: flex; flex-direction: column; }

.empty-state {
  color: #aaa;
  font-size: 14px;
  text-align: center;
  padding: 20px 0;
  line-height: 1.8;
}

.link-text {
  color: #F76707;
  cursor: pointer;
  font-size: 13px;
}

.link-text:hover { text-decoration: underline; }

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 14px;
}

.task-item:hover { background: #f5f5f5; }

.task-item.done .task-title {
  text-decoration: line-through;
  color: #aaa;
}

.task-check {
  color: #F76707;
  font-size: 16px;
  width: 18px;
  flex-shrink: 0;
}

.task-item.done .task-check { color: #ccc; }

/* ── 바로가기 ── */
.shortcuts-card {
  width: 95%;
  margin: 0 auto 20px auto;
}

.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.shortcut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border-radius: 12px;
  background: #faf9f7;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #f0ede8;
}

.shortcut-item:hover {
  background: #fff3eb;
  border-color: #F76707;
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(247, 103, 7, 0.15);
}

.shortcut-icon { font-size: 28px; margin-bottom: 6px; }

.shortcut-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.shortcut-count {
  font-size: 12px;
  color: #F76707;
  font-weight: 500;
}

/* ── 하단 그리드 ── */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  width: 95%;
  margin: 0 auto;
}

/* 최근 활동 */
.activity-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
}

.activity-item:last-child { border-bottom: none; }

.activity-icon { font-size: 20px; flex-shrink: 0; }

.activity-info {
  flex: 1;
  overflow: hidden;
}

.activity-name {
  display: block;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-type {
  font-size: 12px;
  color: #aaa;
}

.activity-date {
  font-size: 12px;
  color: #bbb;
  flex-shrink: 0;
}

/* 배지 */
.badges-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  border-radius: 12px;
  background: #fafafa;
  transition: transform 0.2s;
}

.badge-item.earned { background: #fff8f3; }

.badge-item.locked {
  filter: grayscale(1);
  opacity: 0.35;
}

.badge-item.earned:hover { transform: translateY(-2px); }

.badge-icon { font-size: 28px; margin-bottom: 6px; }

.badge-name {
  font-size: 12px;
  font-weight: 500;
  color: #555;
  text-align: center;
}

/* ── 플래니 진화 카드 ── */
.evolution-inner {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.planny-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
}

.planny-side :deep(svg) {
  filter: drop-shadow(0 6px 16px rgba(247, 103, 7, 0.25));
}

.evo-name {
  font-size: 14px;
  font-weight: 700;
  color: #F76707;
  margin-top: 8px;
}

.evo-count {
  font-size: 12px;
  color: #aaa;
  margin-top: 2px;
}

.evo-next {
  font-size: 11px;
  color: #bbb;
  margin-top: 4px;
  text-align: center;
}

.evo-next.complete {
  color: #F76707;
  font-weight: 600;
}

.badges-side { flex: 1; }

/* ── 반응형 ── */
@media (max-width: 900px) {
  .shortcuts-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .top-grid,
  .bottom-grid { grid-template-columns: 1fr; }

  .shortcuts-grid { grid-template-columns: repeat(3, 1fr); }

  .attendance-row {
    flex-direction: column;
    gap: 16px;
  }

  .progress-container { margin: 0; width: 100%; }

  .attendance-btn { width: 100%; }

  .evolution-inner {
    flex-direction: column;
    align-items: center;
  }

  .badges-side { width: 100%; }
}

@media (max-width: 480px) {
  .shortcuts-grid { grid-template-columns: repeat(2, 1fr); }
  .badges-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
