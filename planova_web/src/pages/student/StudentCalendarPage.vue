  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.2);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .task-context-modal {
    background: white;
    border-radius: 12px;
    padding: 20px 0;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
    width: 240px;
  }
  
  .task-context-modal .context-menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    font-size: 15px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .task-context-modal .context-menu-item:hover {
    background-color: #f5f5f5;
  }
  
  .task-context-modal .context-menu-item svg {
    color: #666;
  }
  
  .task-context-modal .context-menu-item.delete {
    color: #e53935;
  }
  
  .task-context-modal .context-menu-item.delete svg {
    color: #e53935;
  }
<template>
  <div class="student-calendar-page two-column-layout">
    <!-- 왼쪽: 캘린더 -->
    <div class="left-column">
      <div class="calendar-container">
        <div class="calendar-header">
          <h2>{{ currentYear }}년 {{ currentMonth }}월</h2>
          <div class="navigation-buttons">
            <button @click="previousMonth" class="nav-btn"><span>&lt;</span></button>
            <button @click="nextMonth" class="nav-btn"><span>&gt;</span></button>
          </div>
        </div>

        <div class="calendar-grid">
          <div class="weekdays">
            <div v-for="day in weekdays" :key="day" class="weekday" :class="{ 'weekend': day === '일' || day === '토' }">{{ day }}</div>
          </div>

          <div class="days">
            <div 
              v-for="day in calendarDays" 
              :key="day.date" 
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
          <h3>오늘 일정</h3>
          <div class="date">{{ formatSelectedDate }}</div>
        </div>
        <div class="divider"></div>

        <div v-if="selectedDayTasks.length === 0" class="empty-tasks">
          <p>등록된 일정이 없습니다.</p>
        </div>

        <div class="schedule-list scrollable-tasks">
        <div style="position: relative;">
          <div v-for="(task, index) in selectedDayTasks" :key="index" class="task-item" @contextmenu.prevent="openTaskContextMenu($event, task.id)">
            <div class="task-dot" :class="{ 'completed': task.completed }"></div>
            <div class="task-content">{{ task.title }}</div>
            <div class="task-status">
              <div 
                :class="['status-circle', { 'completed': task.completed }]"
                @click.stop="toggleTaskStatus(task)"
              >
                <svg v-if="task.completed" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="white"/>
                </svg>
              </div>
            </div>
</div>
  <div v-if="showTaskContextMenu" class="modal-overlay" @click.self="showTaskContextMenu = false">
    <div class="task-context-modal">
      <div class="context-menu-item" @click="editTask(contextTaskId)">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20h9"></path>
          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
        </svg>
        <span>이름 변경</span>
      </div>
      <div class="context-menu-item delete" @click="deleteTask(contextTaskId)">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          <line x1="10" y1="11" x2="10" y2="17"></line>
          <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>
        <span>삭제</span>
      </div>
    </div>
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
          <div v-for="(goal, index) in weeklyGoals" :key="index" class="goal-item" @contextmenu.prevent="deleteGoal(goal.id)">
            <div class="goal-dot" :class="{ 'completed': goal.completed }"></div>
            <div class="goal-content">{{ goal.title }}</div>
            <div class="goal-status">
              <div 
                :class="['status-circle', { 'completed': goal.completed }]"
                @click="toggleGoalStatus(goal)"
              >
                <svg v-if="goal.completed" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="white"/>
                </svg>
              </div>
              <button class="delete-goal-btn" @click="deleteGoal(goal.id)">삭제</button>
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

<script>
  export default {
    name: 'StudentCalendarPage',
    data() {
      return {
        currentDate: new Date(),
        selectedDate: new Date(),
        weekdays: ['일', '월', '화', '수', '목', '금', '토'],
        tasks: [
          { 
            id: 1,
            date: new Date(2025, 1, 9), 
            title: '넵어온 일정 (최상단)', 
            completed: true 
          },
          { 
            id: 2,
            date: new Date(2025, 1, 9), 
            title: '1과목 pdf 공부하기', 
            completed: true 
          },
          { 
            id: 3,
            date: new Date(2025, 1, 9), 
            title: '2과목 pdf 공부하기', 
            completed: true 
          },
          { 
            id: 4,
            date: new Date(2025, 1, 9), 
            title: '3과목 pdf 공부하기', 
            completed: true 
          }
        ],
        weeklyGoals: [
         
        ],
        showTaskForm: false,
        newTaskText: '',
        showGoalForm: false,
        newGoalText: '',
        nextTaskId: 5,
        nextGoalId: 3,
        showTaskContextMenu: false,
        contextTaskId: null,
        contextMenuX: 0,
        contextMenuY: 0
      };
    },
    computed: {
      currentYear() {
        return this.currentDate.getFullYear();
      },
      currentMonth() {
        return this.currentDate.getMonth() + 1; // JavaScript는 0부터 시작하므로 +1
      },
      currentWeek() {
        const year = this.selectedDate.getFullYear();
        const month = this.selectedDate.getMonth(); // 0-based
        const date = this.selectedDate.getDate();

        const firstDayOfMonth = new Date(year, month, 1);
        const firstDayWeekday = firstDayOfMonth.getDay(); // 요일 (0: 일, ..., 6: 토)

        return Math.ceil((date + firstDayWeekday) / 7);
      },
      calendarDays() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        // 현재 월의 첫날과 마지막 날
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        // 이전 달의 마지막 날
        const prevMonthLastDay = new Date(year, month, 0);
        
        const daysArray = [];
        
        // 이전 달의 날짜 추가
        const firstDayOfWeek = firstDay.getDay();
        for (let i = firstDayOfWeek - 1; i >= 0; i--) {
          const day = new Date(year, month - 1, prevMonthLastDay.getDate() - i);
          daysArray.push({
            date: day,
            dayNumber: day.getDate(),
            isCurrentMonth: false,
            isToday: this.isToday(day),
            isSelected: this.isSameDay(day, this.selectedDate),
            hasEvents: this.hasEvents(day)
          });
        }
        
        // 현재 달의 날짜 추가
        for (let i = 1; i <= lastDay.getDate(); i++) {
          const day = new Date(year, month, i);
          daysArray.push({
            date: day,
            dayNumber: i,
            isCurrentMonth: true,
            isToday: this.isToday(day),
            isSelected: this.isSameDay(day, this.selectedDate),
            hasEvents: this.hasEvents(day)
          });
        }
        
        // 다음 달의 날짜 추가
        const remainingDays = 42 - daysArray.length; // 6주 캘린더를 채우기 위해
        for (let i = 1; i <= remainingDays; i++) {
          const day = new Date(year, month + 1, i);
          daysArray.push({
            date: day,
            dayNumber: i,
            isCurrentMonth: false,
            isToday: this.isToday(day),
            isSelected: this.isSameDay(day, this.selectedDate),
            hasEvents: this.hasEvents(day)
          });
        }
        
        return daysArray;
      },
      selectedDayTasks() {
        return this.tasks.filter(task => this.isSameDay(task.date, this.selectedDate));
      },
      formatSelectedDate() {
        const date = this.selectedDate;
        const dayOfWeek = ['일', '월', '화', '수', '목', '금', '토'][date.getDay()];
        return `${date.getMonth() + 1}/${date.getDate()}(${dayOfWeek})`;
      },
      selectedDay() {
        return this.calendarDays.find(day => this.isSameDay(day.date, this.selectedDate));
      }
    },
    methods: {
      previousMonth() {
        this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() - 1, 1);
      },
      nextMonth() {
        this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 1);
      },
      selectDay(day) {
        this.selectedDate = new Date(day.date);
        this.showTaskForm = false;
      },
      isToday(date) {
        const today = new Date();
        return this.isSameDay(date, today);
      },
      isSameDay(date1, date2) {
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
      },
      hasEvents(date) {
        return this.tasks.some(task => this.isSameDay(task.date, date));
      },
      // 일정 관련 메서드
      showAddTaskForm() {
        this.showTaskForm = true;
        this.$nextTick(() => {
          this.$refs.taskInput.focus();
        });
      },
      cancelAddTask() {
        this.showTaskForm = false;
        this.newTaskText = '';
      },
      addTask() {
        if (!this.newTaskText.trim()) return;
        
        const newTask = {
          id: this.nextTaskId++,
          date: new Date(this.selectedDate),
          title: this.newTaskText.trim(),
          completed: false
        };
        
        this.tasks.push(newTask);
        this.newTaskText = '';
        this.showTaskForm = false;
      },
      toggleTaskStatus(task) {
        task.completed = !task.completed;
      },
      
      // 목표 관련 메서드
      showAddGoalForm() {
        this.showGoalForm = true;
        this.$nextTick(() => {
          this.$refs.goalInput.focus();
        });
      },
      cancelAddGoal() {
        this.showGoalForm = false;
        this.newGoalText = '';
      },
      addGoal() {
        if (!this.newGoalText.trim()) return;
        
        const newGoal = {
          id: this.nextGoalId++,
          week: this.currentWeek,
          month: this.currentMonth,
          year: this.currentYear,
          title: this.newGoalText.trim(),
          completed: false
        };
        
        this.weeklyGoals.push(newGoal);
        this.newGoalText = '';
        this.showGoalForm = false;
      },
      toggleGoalStatus(goal) {
        goal.completed = !goal.completed;
      },
      deleteGoal(goalId) {
        this.weeklyGoals = this.weeklyGoals.filter(goal => goal.id !== goalId);
      },
      deleteTask(taskId) {
        this.tasks = this.tasks.filter(task => task.id !== taskId);
      },
      openTaskContextMenu(event, taskId) {
        this.contextTaskId = taskId;
        this.contextMenuX = event.clientX + 12;
        this.contextMenuY = event.clientY + 12;
        this.showTaskContextMenu = true;
      },
      editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
          this.newTaskText = task.title;
          this.deleteTask(taskId);
          this.showTaskForm = true;
          this.$nextTick(() => {
            this.$refs.taskInput.focus();
          });
        }
        this.showTaskContextMenu = false;
      }
    }
  };
  </script>
  
  <style scoped>
  .student-calendar-page {
    padding: 40px 40px;
    background-color: #fafafa;
  }
  
  .calendar-container {
    background-color: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    padding: 24px;
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
    background-color:#0000;
    color: black;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
  }
  
  .day.weekend:not(.other-month) .day-number {
    color: #ff6b6b;
  }

  .day.selected.weekend .day-number {
    color: white;
  }
  
  .day.selected {
    background-color: rgba(245, 135, 54, 0.1);
    border: 1px solid #f58736;
  }
  
  .day.selected .day-number {
    background-color: #f58736;
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
    background-color: #f58736;
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
    max-height: 400px;
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
  
  .date, .week-indicator {
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
  
  .task-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #f58736;
    margin-right: 16px;
    flex-shrink: 0;
  }
  
  .task-dot.completed {
    background-color: #ccc;
  }
  
  .task-content, .goal-content {
    flex: 1;
    font-size: 15px;
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
  }
  
  .add-task-form input:focus, .add-goal-form input:focus {
    outline: none;
    border-color: #f58736;
    box-shadow: 0 0 0 2px rgba(245, 135, 54, 0.2);
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
    background-color: #f58736;
    border: none;
    color: white;
  }
  
  .add-btn:hover {
    background-color: #e57826;
  }
  
  .add-btn:disabled {
    background-color: #ffc497;
    cursor: not-allowed;
  }
  
  @media (max-width: 768px) {
    .student-calendar-page {
      padding: 10px;
    }

    .two-column-layout {
      flex-direction: column;
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

  .goal-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #f58736;
    margin-right: 16px;
    flex-shrink: 0;
  }

  .goal-dot.completed {
    background-color: #ccc;
  }

  .goal-status {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .delete-goal-btn {
    background: transparent;
    border: none;
    color: #888;
    font-size: 12px;
    cursor: pointer;
    padding: 4px;
  }

  .delete-goal-btn:hover {
    color: #e53935;
  }

  .goals-list {
    max-height: 240px;
    overflow-y: auto;
  }

  .scrollable-tasks {
    max-height: 120px;
    overflow-y: auto;
    margin-bottom: 12px;
  }

  </style>
    mounted() {
      window.addEventListener('click', () => {
        this.showTaskContextMenu = false;
      });
    },
  /* .task-context-menu {
    position: fixed;
    background: white;
    border: 1px solid #ddd;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    z-index: 999;
    width: 160px;
    padding: 8px 0;
    pointer-events: auto;
  } */
  
  .context-menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    font-size: 14px;
    cursor: pointer;
    color: #333;
    transition: background-color 0.2s;
  }

  .context-menu-item:hover {
    background-color: #f5f5f5;
  }

  .context-menu-item svg {
    flex-shrink: 0;
    color: #666;
  }

  .context-menu-item.delete {
    color: #e53935;
  }

  .context-menu-item.delete svg {
    color: #e53935;
  }