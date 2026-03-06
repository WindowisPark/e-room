<template>
  <div class="student-calendar-page two-column-layout">
    <!-- 왼쪽: 캘린더 -->
    <div class="left-column">
      <div class="calendar-container">
        <div class="calendar-header">
          <h2>{{ currentYear }}년 {{ currentMonth }}월</h2>
          <div class="header-controls">
            <button class="today-btn" @click="goToToday">오늘</button>
            <div class="navigation-buttons">
              <button @click="previousMonth" class="nav-btn"><span>&lt;</span></button>
              <button @click="nextMonth" class="nav-btn"><span>&gt;</span></button>
            </div>
          </div>
        </div>

        <div class="calendar-grid">
          <div class="weekdays">
            <div v-for="day in weekdays" :key="day" class="weekday" :class="{ 'weekend': day === '일' || day === '토' }">{{ day }}</div>
          </div>

          <div class="days">
            <div
              v-for="day in calendarDays"
              :key="day.dateStr"
              :class="[
                'day',
                {
                  'today': day.isToday,
                  'selected': day.isSelected,
                  'other-month': !day.isCurrentMonth,
                  'has-events': day.hasEvents,
                  'weekend': day.date.getDay() === 0 || day.date.getDay() === 6
                }
              ]"
              @click="selectDay(day)"
            >
              <span class="day-number">{{ day.dayNumber }}</span>
              <div v-if="day.hasEvents" class="event-indicator"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 오른쪽: 일정 + 목표 -->
    <div class="right-column">
      <div class="schedule-section" v-if="selectedDay">
        <div class="schedule-header">
          <h3>{{ formatSelectedDate }} 일정</h3>
        </div>
        <div class="divider"></div>

        <div v-if="selectedDayTasks.length === 0" class="empty-tasks">
          <p>등록된 일정이 없습니다.</p>
        </div>

        <div class="schedule-list scrollable-tasks">
          <div v-for="task in selectedDayTasks" :key="task.id" class="task-item">
            <div class="task-content" v-if="editingTaskId !== task.id">{{ task.title }}</div>
            <input
              v-else
              class="task-edit-input"
              v-model="editingTaskTitle"
              @keyup.enter="saveTaskEdit(task)"
              @keyup.esc="editingTaskId = null"
              @blur="saveTaskEdit(task)"
              ref="taskEditInput"
            />
            <div class="task-actions">
              <button class="action-btn" @click.stop="startEditTask(task)" title="편집">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20h9"></path>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
              </button>
              <button class="action-btn delete" @click.stop="deleteTask(task.id)" title="삭제">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
            <div
              :class="['status-circle', { 'completed': task.is_completed }]"
              @click.stop="toggleTask(task)"
            >
              <svg v-if="task.is_completed" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="white"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="add-task-form" v-if="showTaskForm">
          <input
            type="text"
            v-model="newTaskText"
            placeholder="새 일정을 입력하세요"
            @keyup.enter="addTask"
            ref="taskInput"
          />
          <div class="form-buttons">
            <button class="cancel-btn" @click="cancelAddTask">취소</button>
            <button class="add-btn" @click="addTask" :disabled="!newTaskText.trim()">추가</button>
          </div>
        </div>

        <button v-else class="add-task-btn" @click="showAddTaskForm">
          <span class="plus-icon">+</span> 일정 추가하기
        </button>
      </div>

      <div class="monthly-summary">
        <div class="summary-header">
          <h3>이번 주 목표</h3>
          <div class="week-indicator">{{ currentMonth }}월 {{ currentWeek }}주차</div>
        </div>
        <div class="divider"></div>

        <div v-if="weeklyGoals.length === 0" class="empty-goals">
          <p>이번 주 목표가 없습니다.</p>
        </div>

        <div class="goals-list">
          <div v-for="goal in weeklyGoals" :key="goal.id" class="goal-item">
            <div class="goal-content" v-if="editingGoalId !== goal.id">{{ goal.title }}</div>
            <input
              v-else
              class="task-edit-input"
              v-model="editingGoalTitle"
              @keyup.enter="saveGoalEdit(goal)"
              @keyup.esc="editingGoalId = null"
              @blur="saveGoalEdit(goal)"
              ref="goalEditInput"
            />
            <div class="task-actions">
              <button class="action-btn" @click.stop="startEditGoal(goal)" title="편집">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20h9"></path>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
              </button>
              <button class="action-btn delete" @click.stop="deleteGoal(goal.id)" title="삭제">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
            <div
              :class="['status-circle', { 'completed': goal.is_completed }]"
              @click="toggleGoal(goal)"
            >
              <svg v-if="goal.is_completed" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="white"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="add-goal-form" v-if="showGoalForm">
          <input
            type="text"
            v-model="newGoalText"
            placeholder="새 목표를 입력하세요"
            @keyup.enter="addGoal"
            ref="goalInput"
          />
          <div class="form-buttons">
            <button class="cancel-btn" @click="cancelAddGoal">취소</button>
            <button class="add-btn" @click="addGoal" :disabled="!newGoalText.trim()">추가</button>
          </div>
        </div>

        <button v-else class="add-task-btn" @click="showAddGoalForm">
          <span class="plus-icon">+</span> 목표 추가하기
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'StudentCalendarPage' })
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import calendarApi from '@/api/calendarApi';

const weekdays = ['일', '월', '화', '수', '목', '금', '토'];

const currentDate = ref(new Date());
const selectedDate = ref(new Date());

function toDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth() + 1);

const currentWeek = computed(() => {
  const d = selectedDate.value;
  const firstDayWeekday = new Date(d.getFullYear(), d.getMonth(), 1).getDay();
  return Math.ceil((d.getDate() + firstDayWeekday) / 7);
});

// Tasks
const allTaskDates = ref(new Set());
const selectedDayTasks = ref([]);
const showTaskForm = ref(false);
const newTaskText = ref('');
const taskInput = ref(null);
const taskEditInput = ref(null);
const editingTaskId = ref(null);
const editingTaskTitle = ref('');

// Goals
const weeklyGoals = ref([]);
const showGoalForm = ref(false);
const newGoalText = ref('');
const goalInput = ref(null);
const goalEditInput = ref(null);
const editingGoalId = ref(null);
const editingGoalTitle = ref('');

// ── 캘린더 계산 ──────────────────────────────────────

function isSameDay(d1, d2) {
  return d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate();
}

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const prevMonthLastDay = new Date(year, month, 0);
  const days = [];

  const firstDayOfWeek = firstDay.getDay();
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const d = new Date(year, month - 1, prevMonthLastDay.getDate() - i);
    days.push(makeDay(d, false));
  }
  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(makeDay(new Date(year, month, i), true));
  }
  const remaining = 42 - days.length;
  for (let i = 1; i <= remaining; i++) {
    days.push(makeDay(new Date(year, month + 1, i), false));
  }
  return days;
});

function makeDay(d, isCurrentMonth) {
  const today = new Date();
  return {
    date: d,
    dateStr: toDateStr(d),
    dayNumber: d.getDate(),
    isCurrentMonth,
    isToday: isSameDay(d, today),
    isSelected: isSameDay(d, selectedDate.value),
    hasEvents: allTaskDates.value.has(toDateStr(d)),
  };
}

const selectedDay = computed(() =>
  calendarDays.value.find(d => d.isSelected)
);

const formatSelectedDate = computed(() => {
  const d = selectedDate.value;
  const dow = ['일', '월', '화', '수', '목', '금', '토'][d.getDay()];
  return `${d.getMonth() + 1}/${d.getDate()}(${dow})`;
});

// ── 월 이동 ──────────────────────────────────────────

function previousMonth() {
  const d = currentDate.value;
  currentDate.value = new Date(d.getFullYear(), d.getMonth() - 1, 1);
}
function nextMonth() {
  const d = currentDate.value;
  currentDate.value = new Date(d.getFullYear(), d.getMonth() + 1, 1);
}

function goToToday() {
  const today = new Date();
  currentDate.value = new Date(today.getFullYear(), today.getMonth(), 1);
  selectedDate.value = today;
  loadTasks();
  loadGoals();
}

// ── 날짜 선택 & Task 로드 ─────────────────────────────

async function selectDay(day) {
  selectedDate.value = new Date(day.date);
  showTaskForm.value = false;
  editingTaskId.value = null;
  await loadTasks();
}

async function loadTasks() {
  try {
    const { data } = await calendarApi.getTasks(toDateStr(selectedDate.value));
    selectedDayTasks.value = data;
  } catch {
    selectedDayTasks.value = [];
  }
}

async function loadTaskDates() {
  try {
    const { data } = await calendarApi.getTaskDates(currentYear.value, currentMonth.value);
    allTaskDates.value = new Set(data);
  } catch {
    allTaskDates.value = new Set();
  }
}

// ── Goals 로드 ────────────────────────────────────────

async function loadGoals() {
  try {
    const { data } = await calendarApi.getGoals(
      selectedDate.value.getFullYear(),
      selectedDate.value.getMonth() + 1,
      currentWeek.value,
    );
    weeklyGoals.value = data;
  } catch {
    weeklyGoals.value = [];
  }
}

// ── Task CRUD ─────────────────────────────────────────

function showAddTaskForm() {
  showTaskForm.value = true;
  nextTick(() => taskInput.value?.focus());
}
function cancelAddTask() {
  showTaskForm.value = false;
  newTaskText.value = '';
}

async function addTask() {
  if (!newTaskText.value.trim()) return;
  try {
    await calendarApi.createTask(newTaskText.value.trim(), toDateStr(selectedDate.value));
    newTaskText.value = '';
    await loadTasks();
    // Set 반응성을 위해 새 Set으로 교체
    allTaskDates.value = new Set([...allTaskDates.value, toDateStr(selectedDate.value)]);
    nextTick(() => taskInput.value?.focus());
  } catch { /* 무시 */ }
}

async function toggleTask(task) {
  try {
    const { data } = await calendarApi.toggleTask(task.id);
    const idx = selectedDayTasks.value.findIndex(t => t.id === task.id);
    if (idx !== -1) selectedDayTasks.value[idx] = data;
  } catch { /* 무시 */ }
}

async function deleteTask(taskId) {
  try {
    await calendarApi.deleteTask(taskId);
    selectedDayTasks.value = selectedDayTasks.value.filter(t => t.id !== taskId);
    if (selectedDayTasks.value.length === 0) {
      const newSet = new Set(allTaskDates.value);
      newSet.delete(toDateStr(selectedDate.value));
      allTaskDates.value = newSet;
    }
  } catch { /* 무시 */ }
}

function startEditTask(task) {
  editingTaskId.value = task.id;
  editingTaskTitle.value = task.title;
  nextTick(() => {
    const el = Array.isArray(taskEditInput.value) ? taskEditInput.value[0] : taskEditInput.value;
    el?.focus();
  });
}

async function saveTaskEdit(task) {
  if (!editingTaskTitle.value.trim() || editingTaskTitle.value.trim() === task.title) {
    editingTaskId.value = null;
    return;
  }
  try {
    const { data } = await calendarApi.updateTask(task.id, editingTaskTitle.value.trim());
    const idx = selectedDayTasks.value.findIndex(t => t.id === task.id);
    if (idx !== -1) selectedDayTasks.value[idx] = data;
  } catch { /* 무시 */ }
  editingTaskId.value = null;
}

// ── Goal CRUD ─────────────────────────────────────────

function showAddGoalForm() {
  showGoalForm.value = true;
  nextTick(() => goalInput.value?.focus());
}
function cancelAddGoal() {
  showGoalForm.value = false;
  newGoalText.value = '';
}

async function addGoal() {
  if (!newGoalText.value.trim()) return;
  try {
    await calendarApi.createGoal(
      newGoalText.value.trim(),
      selectedDate.value.getFullYear(),
      selectedDate.value.getMonth() + 1,
      currentWeek.value,
    );
    newGoalText.value = '';
    showGoalForm.value = false;
    await loadGoals();
  } catch { /* 무시 */ }
}

async function toggleGoal(goal) {
  try {
    const { data } = await calendarApi.toggleGoal(goal.id);
    const idx = weeklyGoals.value.findIndex(g => g.id === goal.id);
    if (idx !== -1) weeklyGoals.value[idx] = data;
  } catch { /* 무시 */ }
}

async function deleteGoal(goalId) {
  try {
    await calendarApi.deleteGoal(goalId);
    weeklyGoals.value = weeklyGoals.value.filter(g => g.id !== goalId);
  } catch { /* 무시 */ }
}

function startEditGoal(goal) {
  editingGoalId.value = goal.id;
  editingGoalTitle.value = goal.title;
  nextTick(() => {
    const el = Array.isArray(goalEditInput.value) ? goalEditInput.value[0] : goalEditInput.value;
    el?.focus();
  });
}

async function saveGoalEdit(goal) {
  if (!editingGoalTitle.value.trim() || editingGoalTitle.value.trim() === goal.title) {
    editingGoalId.value = null;
    return;
  }
  try {
    const { data } = await calendarApi.updateGoal(goal.id, editingGoalTitle.value.trim());
    const idx = weeklyGoals.value.findIndex(g => g.id === goal.id);
    if (idx !== -1) weeklyGoals.value[idx] = data;
  } catch { /* 무시 */ }
  editingGoalId.value = null;
}

// ── 초기 로드 ──────────────────────────────────────────

onMounted(async () => {
  await Promise.all([loadTasks(), loadGoals(), loadTaskDates()]);
});

onBeforeUnmount(() => {
  // 전역 이벤트 리스너 없음 — 클린업 불필요
});

// 월 변경 시 이벤트 점 재로드
watch([currentYear, currentMonth], loadTaskDates);

// selectedDate 변경 시 goals 재로드 (주차 변경 감지)
watch(currentWeek, loadGoals);
</script>

<style scoped>
.student-calendar-page {
  padding: var(--space-page);
  background-color: var(--bg-page);
}

.calendar-container {
  background-color: var(--bg-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: var(--space-card);
  margin-bottom: 24px;
  height: 550px;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.calendar-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.today-btn {
  padding: 6px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
}

.today-btn:hover {
  border-color: #F76707;
  color: #F76707;
}

.navigation-buttons {
  display: flex;
  gap: 12px;
}

.nav-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f5f5f7;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background: #e8e8ed;
}

.nav-btn span {
  font-size: 18px;
  color: #555;
}

.two-column-layout {
  display: flex;
  gap: 24px;
}

.left-column {
  flex: 1.2;
  min-width: 360px;
  display: flex;
  flex-direction: column;
  justify-content: stretch;
}

.right-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.calendar-grid {
  border-radius: 12px;
  overflow: hidden;
  background-color: #fff;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  background-color: #f8f8fa;
  padding: 12px 0;
  border-radius: 12px 12px 0 0;
}

.weekday {
  font-weight: 600;
  font-size: 14px;
  color: #666;
}

.weekday.weekend {
  color: #ff6b6b;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: #fff;
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.day {
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  border: 1px solid #f5f5f7;
  transition: all 0.2s ease;
}

.day:hover {
  background-color: #f8f8fa;
}

.day-number {
  font-size: 15px;
  margin-bottom: 4px;
}

.day.other-month {
  color: #bbb;
  background-color: #fcfcfc;
}

.day.today .day-number {
  border: 2px solid #333;
  background-color: transparent;
  color: #333;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.day.today.selected .day-number {
  background-color: #F76707;
  border-color: #F76707;
  color: white;
}

.day.weekend:not(.other-month) .day-number {
  color: #ff6b6b;
}

.day.selected.weekend .day-number {
  color: white;
}

.day.selected {
  background-color: rgba(247, 103, 7, 0.1);
  border: 1px solid #F76707;
}

.day.selected .day-number {
  background-color: #F76707;
  color: white;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.event-indicator {
  width: 5px;
  height: 5px;
  background-color: #F76707;
  border-radius: 50%;
  margin-top: 2px;
}

.schedule-section, .monthly-summary {
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 24px;
  margin-bottom: 12px;
}

.schedule-section {
  display: flex;
  flex-direction: column;
}

.schedule-header, .summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.schedule-header h3, .summary-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.week-indicator {
  color: #666;
  font-size: 14px;
  background-color: #f5f5f7;
  padding: 6px 12px;
  border-radius: 20px;
}

.divider {
  height: 1px;
  background-color: #eaeaea;
  margin: 16px 0;
}

.task-item, .goal-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 10px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.task-item:hover, .goal-item:hover {
  background-color: #f8f8fa;
}

.task-content, .goal-content {
  flex: 1;
  font-size: 15px;
}

.task-edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #F76707;
  border-radius: 4px;
  font-size: 15px;
  outline: none;
  box-shadow: 0 0 0 2px rgba(247, 103, 7, 0.2);
}

.task-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
  margin-right: 8px;
}

.task-item:hover .task-actions,
.goal-item:hover .task-actions {
  opacity: 1;
}

.action-btn {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  transition: all 0.15s;
}

.action-btn:hover {
  background: #f0f0f0;
  color: #555;
}

.action-btn.delete:hover {
  background: #ffeaea;
  color: #e53935;
}

.status-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  cursor: pointer;
}

.status-circle:hover {
  border-color: #aaa;
}

.status-circle.completed {
  background-color: #4dabf7;
  border-color: #4dabf7;
}

.empty-tasks, .empty-goals {
  text-align: center;
  padding: 20px 0;
  color: #999;
  font-style: italic;
}

.add-task-btn {
  width: 100%;
  padding: 10px;
  margin-top: 16px;
  background-color: transparent;
  border: 2px dashed #ddd;
  border-radius: 8px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.add-task-btn:hover {
  border-color: #bbb;
  color: #666;
}

.plus-icon {
  font-size: 18px;
  margin-right: 8px;
}

.add-task-form, .add-goal-form {
  margin-top: 16px;
}

.add-task-form input, .add-goal-form input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 12px;
  box-sizing: border-box;
}

.add-task-form input:focus, .add-goal-form input:focus {
  outline: none;
  border-color: #F76707;
  box-shadow: 0 0 0 2px rgba(247, 103, 7, 0.2);
}

.form-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.cancel-btn, .add-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background-color: transparent;
  border: 1px solid #ddd;
  color: #666;
}

.cancel-btn:hover {
  background-color: #f5f5f7;
}

.add-btn {
  background-color: #F76707;
  border: none;
  color: white;
}

.add-btn:hover {
  background-color: #e05a00;
}

.add-btn:disabled {
  background-color: #ffc497;
  cursor: not-allowed;
}

.scrollable-tasks {
  overflow-y: auto;
  margin-bottom: 12px;
}

.goals-list {
  overflow-y: auto;
}

@media (max-width: 768px) {
  .student-calendar-page {
    padding: 10px;
  }

  .two-column-layout {
    flex-direction: column;
  }

  .right-column {
    height: auto;
    overflow-y: visible;
  }

  .calendar-container, .schedule-section, .monthly-summary {
    padding: 16px;
  }

  .day {
    height: 50px;
  }

  .day-number {
    font-size: 14px;
  }

  .form-buttons {
    flex-direction: column;
    gap: 8px;
  }

  .cancel-btn, .add-btn {
    width: 100%;
  }
}
</style>
