<template>
  <div class="cl-page">
    <!-- 왼쪽: 자소서 목록 -->
    <aside class="cl-panel">
      <div class="panel-header">
        <h2>자소서</h2>
        <button class="btn-primary btn-sm" @click="openCreateModal">+ 새 자소서</button>
      </div>
      <ul class="cl-list">
        <li
          v-for="cl in coverLetters"
          :key="cl.id"
          class="cl-item"
          :class="{ active: selectedCl?.id === cl.id }"
          @click="selectCoverLetter(cl.id)"
        >
          <div class="cl-title">{{ cl.title }}</div>
          <div class="cl-date">{{ formatDate(cl.updated_at) }}</div>
        </li>
        <li v-if="coverLetters.length === 0" class="empty-hint">자소서가 없습니다.</li>
      </ul>
    </aside>

    <!-- 오른쪽: 편집 영역 -->
    <main class="editor-panel" v-if="selectedCl">
      <div class="editor-header">
        <div>
          <h1 class="cl-name">{{ selectedCl.title }}</h1>
          <div class="cl-meta">
            <span v-if="linkedCompany" class="meta-chip"><i class="fa-solid fa-building"></i> {{ linkedCompany }}</span>
            <span v-if="linkedResume" class="meta-chip"><i class="fa-solid fa-id-card"></i> {{ linkedResume }}</span>
          </div>
        </div>
        <div class="header-actions">
          <span v-if="saveStatus" class="save-status" :class="saveStatus">
            {{ saveStatus === 'saving' ? '↻ 저장 중...' : '• 저장됨' }}
          </span>
          <button class="btn-primary" @click="generateDrafts" :disabled="generating">
            <span v-if="generating">생성 중... ⏳</span>
            <span v-else>✨ AI 초안 생성</span>
          </button>
          <button class="btn-danger btn-sm" @click="confirmDelete">삭제</button>
        </div>
      </div>

      <!-- 문항 목록 -->
      <div class="questions-section">
        <draggable
          v-model="clItems"
          item-key="id"
          handle=".drag-handle"
          ghost-class="sortable-ghost"
          @end="onClDragEnd"
        >
          <template #item="{ element: item, index: idx }">
        <div
          class="question-card"
          :class="{ expanded: expandedItem === item.id }"
        >
          <div class="question-header" @click="toggleExpand(item.id)">
            <i class="fa-solid fa-grip-vertical drag-handle" @click.stop></i>
            <span class="q-num">Q{{ idx + 1 }}</span>
            <span class="q-text">{{ item.question }}</span>
            <span v-if="item.char_limit" class="char-limit-badge">{{ item.char_limit }}자</span>
            <span class="expand-icon">{{ expandedItem === item.id ? '▲' : '▼' }}</span>
            <button class="btn-icon" @click.stop="deleteItem(item.id)">✕</button>
          </div>

          <div v-if="expandedItem === item.id" class="answer-section">
            <textarea
              v-model="item.answer"
              class="answer-input"
              :placeholder="'답변을 작성해주세요.' + (item.char_limit ? ` (최대 ${item.char_limit}자)` : '')"
              @input="triggerAutoSave(item)"
              :rows="8"
            ></textarea>
            <div v-if="item.char_limit" class="char-progress-bg">
              <div
                class="char-progress-fill"
                :style="{ width: getProgressWidth(item), background: getProgressColor(item) }"
              ></div>
            </div>
            <div class="char-counter" :class="{ over: item.char_limit && (item.answer || '').length > item.char_limit }">
              {{ (item.answer || '').length }}자
              <span v-if="item.char_limit"> / {{ item.char_limit }}자</span>
            </div>
          </div>
        </div>
          </template>
        </draggable>

        <div v-if="clItems.length === 0" class="empty-questions">
          문항이 없습니다. 아래 버튼으로 추가해주세요.
        </div>

        <button class="btn-add" @click="openAddItem">+ 문항 추가</button>
      </div>
    </main>

    <div v-else class="empty-editor">
      <i class="fa-regular fa-pen-to-square empty-editor-icon"></i>
      <p class="empty-editor-title">아직 자소서가 없어요</p>
      <p class="empty-editor-desc">AI가 초안을 작성해주는 자소서,<br>지금 시작해보세요.</p>
      <button class="btn-primary" @click="openCreateModal">+ 첫 자소서 만들기</button>
    </div>

    <!-- 자소서 생성 모달 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="dialog-box">
        <h3>새 자소서 만들기</h3>
        <div class="form-group">
          <label>제목 *</label>
          <input v-model="newCl.title" placeholder="예: 카카오 개발자 자소서" class="modal-input" />
        </div>
        <div class="form-group">
          <label>연결할 기업 (선택)</label>
          <select v-model="newCl.company_id" class="modal-input">
            <option :value="null">선택 안 함</option>
            <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.company_name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>연결할 이력서 (선택)</label>
          <select v-model="newCl.resume_profile_id" class="modal-input">
            <option :value="null">선택 안 함</option>
            <option v-for="r in resumeProfiles" :key="r.id" :value="r.id">{{ r.title }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showCreateModal = false">취소</button>
          <button class="btn-primary" @click="createCoverLetter">만들기</button>
        </div>
      </div>
    </div>

    <!-- 문항 추가 모달 (프리셋 + 직접입력) -->
    <div v-if="showAddItemModal" class="modal-overlay" @click.self="showAddItemModal = false">
      <div class="dialog-box dialog-wide">
        <h3>문항 추가</h3>
        <div class="add-mode-tabs">
          <button :class="{ active: addMode === 'preset' }" @click="addMode = 'preset'"><i class="fa-solid fa-clipboard-list"></i> 기본 문항 선택</button>
          <button :class="{ active: addMode === 'manual' }" @click="addMode = 'manual'"><i class="fa-regular fa-pen-to-square"></i> 직접 입력</button>
        </div>

        <!-- 프리셋 목록 -->
        <div v-if="addMode === 'preset'" class="preset-list">
          <button
            v-for="preset in PRESET_QUESTIONS"
            :key="preset.label"
            class="preset-item"
            @click="selectPreset(preset)"
          >
            <div class="preset-item-top">
              <span class="preset-label">{{ preset.label }}</span>
              <span class="preset-limit-badge">{{ preset.limit }}자</span>
            </div>
            <p class="preset-text">{{ preset.text }}</p>
          </button>
        </div>

        <!-- 직접 입력 -->
        <div v-else class="manual-form">
          <div class="form-group">
            <label>질문 *</label>
            <textarea v-model="newItem.question" placeholder="자소서 질문을 입력하세요" class="modal-input" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>글자수 제한 (빈칸 = 제한 없음)</label>
            <input v-model.number="newItem.char_limit" type="number" placeholder="1000" class="modal-input" />
          </div>
          <div class="modal-actions">
            <button class="btn-outline" @click="showAddItemModal = false">취소</button>
            <button class="btn-primary" @click="addItem">추가</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from '@/api/index.js';
import draggable from 'vuedraggable';

const CL_API = '/coverletter';
const JOBS_API = '/jobs';
const RESUME_API = '/resume';

const PRESET_QUESTIONS = [
  { label: '성장과정',    text: '본인의 성장과정을 기술해 주세요.',                  limit: 800 },
  { label: '지원동기',    text: '당사 및 해당 직무에 지원한 동기를 기술해 주세요.',  limit: 700 },
  { label: '장점/단점',   text: '본인의 장점과 단점을 기술해 주세요.',               limit: 600 },
  { label: '직무역량',    text: '직무 수행에 필요한 역량과 경험을 기술해 주세요.',   limit: 800 },
  { label: '입사 후 포부', text: '입사 후 목표와 포부를 기술해 주세요.',             limit: 600 },
  { label: '팀워크',      text: '팀 프로젝트 경험과 협업 방식을 기술해 주세요.',    limit: 700 },
  { label: '도전/실패',   text: '가장 도전적인 경험과 극복 과정을 기술해 주세요.',  limit: 800 },
  { label: '경험/경력',   text: '관련 경험 또는 경력을 구체적으로 기술해 주세요.',  limit: 800 },
];

const coverLetters = ref([]);
const selectedCl = ref(null);
const clItems = ref([]);
const companies = ref([]);
const resumeProfiles = ref([]);
const expandedItem = ref(null);
const generating = ref(false);
const showCreateModal = ref(false);
const showAddItemModal = ref(false);
const addMode = ref('preset');
const saveStatus = ref(null); // null | 'saving' | 'saved'
const saveTimers = {};

const newCl = ref({ title: '', company_id: null, resume_profile_id: null });
const newItem = ref({ question: '', char_limit: null });

const linkedCompany = computed(() => {
  if (!selectedCl.value?.company_id) return null;
  return companies.value.find(c => c.id === selectedCl.value.company_id)?.company_name || null;
});

const linkedResume = computed(() => {
  if (!selectedCl.value?.resume_profile_id) return null;
  return resumeProfiles.value.find(r => r.id === selectedCl.value.resume_profile_id)?.title || null;
});

function formatDate(dt) {
  if (!dt) return '';
  return new Date(dt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

// ─── 진행 바 ─────────────────────────────────────────────────

function getProgressWidth(item) {
  if (!item.char_limit) return '0%';
  const ratio = Math.min((item.answer || '').length / item.char_limit, 1);
  return `${ratio * 100}%`;
}

function getProgressColor(item) {
  if (!item.char_limit) return '#e8e8e8';
  const ratio = (item.answer || '').length / item.char_limit;
  if (ratio > 1) return '#e03e00';
  if (ratio >= 0.8) return '#F76707';
  return '#e8e8e8';
}

// ─── 자동저장 ─────────────────────────────────────────────────

function triggerAutoSave(item) {
  saveStatus.value = 'saving';
  clearTimeout(saveTimers[item.id]);
  saveTimers[item.id] = setTimeout(async () => {
    await saveItem(item);
    saveStatus.value = 'saved';
    setTimeout(() => { saveStatus.value = null; }, 2000);
  }, 1000);
}

// ─── 데이터 로드 ─────────────────────────────────────────────

async function loadAll() {
  try {
    const [clRes, jobRes, resumeRes] = await Promise.all([
      axios.get(CL_API),
      axios.get(JOBS_API).catch(() => ({ data: [] })),
      axios.get(`${RESUME_API}/profiles`).catch(() => ({ data: [] })),
    ]);
    coverLetters.value = clRes.data;
    companies.value = jobRes.data;
    resumeProfiles.value = resumeRes.data;
  } catch (e) {
    console.warn('자소서 로딩 실패:', e.response?.status);
  }
}

async function selectCoverLetter(id) {
  const res = await axios.get(`${CL_API}/${id}`);
  selectedCl.value = res.data;
  clItems.value = res.data.items || [];
  expandedItem.value = clItems.value[0]?.id || null;
}

function openCreateModal() {
  newCl.value = { title: '', company_id: null, resume_profile_id: null };
  showCreateModal.value = true;
}

async function createCoverLetter() {
  if (!newCl.value.title.trim()) return;
  const res = await axios.post(CL_API, {
    title: newCl.value.title.trim(),
    company_id: newCl.value.company_id || null,
    resume_profile_id: newCl.value.resume_profile_id || null,
  });
  coverLetters.value.unshift(res.data);
  await selectCoverLetter(res.data.id);
  showCreateModal.value = false;
}

async function confirmDelete() {
  if (!confirm(`"${selectedCl.value.title}" 자소서를 삭제하시겠습니까?`)) return;
  await axios.delete(`${CL_API}/${selectedCl.value.id}`);
  coverLetters.value = coverLetters.value.filter(c => c.id !== selectedCl.value.id);
  selectedCl.value = null;
  clItems.value = [];
}

function toggleExpand(id) {
  expandedItem.value = expandedItem.value === id ? null : id;
}

function openAddItem() {
  newItem.value = { question: '', char_limit: null };
  addMode.value = 'preset';
  showAddItemModal.value = true;
}

async function selectPreset(preset) {
  const res = await axios.post(`${CL_API}/${selectedCl.value.id}/items`, {
    question: preset.text,
    char_limit: preset.limit,
    order_index: clItems.value.length,
  });
  clItems.value.push(res.data);
  expandedItem.value = res.data.id;
  showAddItemModal.value = false;
}

async function addItem() {
  if (!newItem.value.question.trim()) return;
  const res = await axios.post(`${CL_API}/${selectedCl.value.id}/items`, {
    question: newItem.value.question.trim(),
    char_limit: newItem.value.char_limit || null,
    order_index: clItems.value.length,
  });
  clItems.value.push(res.data);
  expandedItem.value = res.data.id;
  showAddItemModal.value = false;
}

async function saveItem(item) {
  await axios.put(`${CL_API}/items/${item.id}`, { answer: item.answer });
}

async function deleteItem(itemId) {
  if (!confirm('문항을 삭제하시겠습니까?')) return;
  await axios.delete(`${CL_API}/items/${itemId}`);
  clItems.value = clItems.value.filter(i => i.id !== itemId);
}

async function onClDragEnd() {
  clItems.value.forEach((item, idx) => { item.order_index = idx; });
  await Promise.all(
    clItems.value.map(item =>
      axios.put(`${CL_API}/items/${item.id}`, { order_index: item.order_index }).catch(() => {})
    )
  );
}

async function generateDrafts() {
  if (!confirm('AI가 각 문항의 초안을 생성합니다. 기존 작성 내용이 덮어쓰여질 수 있습니다. 계속하시겠습니까?')) return;
  generating.value = true;
  try {
    const res = await axios.post(`${CL_API}/${selectedCl.value.id}/generate`);
    for (const upd of res.data.updated) {
      const item = clItems.value.find(i => i.id === upd.id);
      if (item) item.answer = upd.answer;
    }
    alert('AI 초안이 생성되었습니다. 내용을 검토하고 수정해주세요.');
  } catch (e) {
    alert(e.response?.data?.detail || 'AI 초안 생성에 실패했습니다.');
  } finally {
    generating.value = false;
  }
}

onMounted(loadAll);
</script>

<style scoped>
.cl-page {
  display: flex;
  height: 100%;
  background: var(--bg-page);
}

/* 왼쪽 패널 */
.cl-panel {
  width: var(--panel-width);
  min-width: 200px;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px 16px;
  border-bottom: 1px solid #eee;
}
.panel-header h2 { font-size: 16px; font-weight: 600; color: #333; margin: 0; }

.cl-list { list-style: none; margin: 0; padding: 8px 0; overflow-y: auto; flex: 1; }

.cl-item {
  padding: 10px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}
.cl-item:hover { background: #f5f5f5; }
.cl-item.active { border-left-color: #F76707; background: #fff5ee; }

.cl-title { font-size: 14px; font-weight: 500; color: #333; }
.cl-date { font-size: 11px; color: #999; margin-top: 2px; }
.empty-hint { padding: 20px 16px; font-size: 13px; color: #999; }

/* 에디터 */
.editor-panel {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  position: sticky;
  top: 0;
  background: var(--bg-page);
  z-index: 10;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  margin-left: -32px;
  margin-right: -32px;
  padding-left: 32px;
  padding-right: 32px;
  padding-top: 4px;
}

.cl-name { font-size: 22px; font-weight: 700; color: #222; margin: 0 0 8px; }

.cl-meta { display: flex; gap: 8px; flex-wrap: wrap; }

.meta-chip {
  background: #f0f0f0;
  color: #555;
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 12px;
}

.header-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }

/* 저장 상태 */
.save-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
}
.save-status.saving { color: #F76707; background: #fff5ee; }
.save-status.saved { color: #38a169; background: #f0fff4; }

/* 문항 카드 */
.questions-section { padding-top: 16px; }

.question-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  overflow: hidden;
  transition: box-shadow 0.15s;
}
.question-card.expanded { box-shadow: var(--shadow-card); border-color: var(--color-primary); }

.question-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
}
.question-header:hover { background: #fafafa; }

.q-num {
  font-size: 12px;
  font-weight: 700;
  color: #F76707;
  min-width: 24px;
}

.q-text {
  flex: 1;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.char-limit-badge {
  font-size: 11px;
  background: #eee;
  color: #777;
  border-radius: 10px;
  padding: 2px 8px;
  white-space: nowrap;
}

.expand-icon { font-size: 10px; color: #bbb; }

.btn-icon {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 5px;
  border-radius: 4px;
}
.btn-icon:hover { color: #e53e3e; background: #fef2f2; }

.drag-handle { cursor: grab; color: #ccc; padding: 0 6px; font-size: 13px; }
.drag-handle:hover { color: #F76707; }
.drag-handle:active { cursor: grabbing; }
.sortable-ghost { opacity: 0.4; background: #fff5ee; }

.answer-section {
  padding: 0 16px 16px;
  border-top: 1px solid #f0f0f0;
}

.answer-input {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
  color: #333;
  margin-top: 12px;
}
.answer-input:focus { outline: none; border-color: #F76707; }

/* 진행 바 */
.char-progress-bg {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.char-progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s, background 0.3s;
}

.char-counter {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.char-counter.over { color: #e03e00; font-weight: 600; }

.empty-questions {
  text-align: center;
  padding: 32px;
  color: #bbb;
  font-size: 14px;
}

.btn-add {
  display: block;
  width: 100%;
  padding: 12px;
  background: #fff;
  border: 2px dashed #ddd;
  border-radius: 8px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  margin-top: 8px;
}
.btn-add:hover { border-color: #F76707; color: #F76707; background: #fff8f5; }

.empty-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 40px;
}
.empty-editor-icon {
  font-size: 52px;
  color: #ddd;
}
.empty-editor-title {
  font-size: 18px;
  font-weight: 600;
  color: #555;
  margin: 0;
}
.empty-editor-desc {
  font-size: 14px;
  color: #999;
  line-height: 1.6;
  margin: 0;
}

/* 버튼 공통 */
.btn-primary {
  background: #F76707;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 9px 18px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn-primary:hover { background: #e05500; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm { padding: 5px 10px; font-size: 12px; }

.btn-outline {
  background: #fff;
  color: #F76707;
  border: 1px solid #F76707;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
}
.btn-outline:hover { background: #fff5ee; }

.btn-danger {
  background: #fff;
  color: #e53e3e;
  border: 1px solid #e53e3e;
  border-radius: 6px;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 12px;
}

/* 모달 공통 */
.modal-overlay {
  position: fixed !important;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex !important;
  align-items: center;
  justify-content: center;
  z-index: 9999 !important;
}

.dialog-box {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: 28px;
  min-width: 360px;
  max-width: 480px;
  width: 100%;
  box-shadow: var(--shadow-float);
}

.dialog-wide {
  max-width: 640px;
}

.dialog-box h3 { margin: 0 0 20px; font-size: 17px; color: #222; }

.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 500; }

.modal-input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 9px 12px;
  font-size: 14px;
  box-sizing: border-box;
  font-family: inherit;
  resize: vertical;
}
.modal-input:focus { outline: none; border-color: #F76707; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

/* 문항 추가 탭 */
.add-mode-tabs {
  display: flex;
  border-bottom: 2px solid #eee;
  margin-bottom: 20px;
}

.add-mode-tabs button {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  font-size: 14px;
  color: #888;
  font-weight: 500;
  transition: all 0.15s;
}

.add-mode-tabs button.active {
  color: #F76707;
  border-bottom-color: #F76707;
}

/* 프리셋 목록 */
.preset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
}

.preset-item {
  text-align: left;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.15s;
  width: 100%;
}

.preset-item:hover {
  border-color: #F76707;
  background: #fff8f5;
}

.preset-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.preset-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.preset-limit-badge {
  font-size: 11px;
  background: #eee;
  color: #666;
  padding: 2px 8px;
  border-radius: 10px;
}

.preset-text {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

.manual-form { padding-top: 4px; }
</style>
