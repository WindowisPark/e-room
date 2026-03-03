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
            <span v-if="linkedCompany" class="meta-chip">🏢 {{ linkedCompany }}</span>
            <span v-if="linkedResume" class="meta-chip">📄 {{ linkedResume }}</span>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn-primary" @click="generateDrafts" :disabled="generating">
            <span v-if="generating">생성 중... ⏳</span>
            <span v-else>✨ AI 초안 생성</span>
          </button>
          <button class="btn-danger btn-sm" @click="confirmDelete">삭제</button>
        </div>
      </div>

      <!-- 문항 목록 -->
      <div class="questions-section">
        <div
          v-for="(item, idx) in clItems"
          :key="item.id"
          class="question-card"
          :class="{ expanded: expandedItem === item.id }"
        >
          <div class="question-header" @click="toggleExpand(item.id)">
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
              @blur="saveItem(item)"
              :rows="8"
            ></textarea>
            <div class="char-counter" :class="{ over: item.char_limit && (item.answer || '').length > item.char_limit }">
              {{ (item.answer || '').length }}자
              <span v-if="item.char_limit"> / {{ item.char_limit }}자</span>
            </div>
          </div>
        </div>

        <div v-if="clItems.length === 0" class="empty-questions">
          문항이 없습니다. 아래 버튼으로 추가해주세요.
        </div>

        <button class="btn-add" @click="openAddItem">+ 문항 추가</button>
      </div>
    </main>

    <div v-else class="empty-editor">
      <p>왼쪽에서 자소서를 선택하거나 새로 만들어보세요.</p>
    </div>

    <!-- 자소서 생성 모달 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
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

    <!-- 문항 추가 모달 -->
    <div v-if="showAddItemModal" class="modal-overlay" @click.self="showAddItemModal = false">
      <div class="modal">
        <h3>문항 추가</h3>
        <div class="form-group">
          <label>질문 *</label>
          <textarea v-model="newItem.question" placeholder="자소서 질문을 입력하세요" class="modal-input" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label>글자수 제한 (0 또는 빈칸 = 제한 없음)</label>
          <input v-model.number="newItem.char_limit" type="number" placeholder="1000" class="modal-input" />
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showAddItemModal = false">취소</button>
          <button class="btn-primary" @click="addItem">추가</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const CL_API = '/api/v1/coverletter';
const JOBS_API = '/api/v1/jobs';
const RESUME_API = '/api/v1/resume';

const coverLetters = ref([]);
const selectedCl = ref(null);
const clItems = ref([]);
const companies = ref([]);
const resumeProfiles = ref([]);
const expandedItem = ref(null);
const generating = ref(false);
const showCreateModal = ref(false);
const showAddItemModal = ref(false);

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

async function loadAll() {
  const [clRes, jobRes, resumeRes] = await Promise.all([
    axios.get(CL_API),
    axios.get(JOBS_API).catch(() => ({ data: [] })),
    axios.get(`${RESUME_API}/profiles`).catch(() => ({ data: [] })),
  ]);
  coverLetters.value = clRes.data;
  companies.value = jobRes.data;
  resumeProfiles.value = resumeRes.data;
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
  showAddItemModal.value = true;
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
  background: #f8f9fa;
}

/* 왼쪽 패널 */
.cl-panel {
  width: 240px;
  min-width: 200px;
  background: #fff;
  border-right: 1px solid #e0e0e0;
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

.header-actions { display: flex; gap: 8px; align-items: center; }

/* 문항 카드 */
.question-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: box-shadow 0.15s;
}
.question-card.expanded { box-shadow: 0 2px 12px rgba(0,0,0,0.08); }

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
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
  padding: 2px 4px;
}
.btn-icon:hover { color: #e53e3e; }

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

.char-counter {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.char-counter.over { color: #e53e3e; font-weight: 600; }

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
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 15px;
}

/* 버튼 */
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

/* 모달 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  min-width: 360px;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.modal h3 { margin: 0 0 20px; font-size: 17px; color: #222; }

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
</style>
