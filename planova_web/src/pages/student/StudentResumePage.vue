<template>
  <div class="resume-page">
    <!-- 왼쪽: 이력서 목록 -->
    <aside class="profile-panel">
      <div class="panel-header">
        <h2>이력서</h2>
        <button class="btn-primary btn-sm" @click="openCreateProfile">+ 새 이력서</button>
      </div>
      <ul class="profile-list">
        <li
          v-for="p in profiles"
          :key="p.id"
          class="profile-item"
          :class="{ active: selectedProfile?.id === p.id }"
          @click="selectProfile(p)"
        >
          <div class="profile-title">{{ p.title }}</div>
          <div class="profile-date">{{ formatDate(p.updated_at) }}</div>
        </li>
        <li v-if="profiles.length === 0" class="empty-hint">이력서가 없습니다.</li>
      </ul>
    </aside>

    <!-- 오른쪽: 이력서 편집 -->
    <main class="editor-panel" v-if="selectedProfile">
      <div class="editor-header">
        <div>
          <input
            v-if="editingTitle"
            v-model="editTitleValue"
            class="title-input"
            @blur="saveTitle"
            @keyup.enter="saveTitle"
            ref="titleInput"
          />
          <h1 v-else class="profile-name" @click="startEditTitle">
            {{ selectedProfile.title }} <span class="edit-hint">✏️</span>
          </h1>
          <textarea
            class="summary-input"
            placeholder="한 줄 소개 (선택)"
            v-model="summaryValue"
            @blur="saveSummary"
          ></textarea>
        </div>
        <div class="export-buttons">
          <button class="btn-outline" @click="exportJson">JSON 내보내기</button>
          <button class="btn-outline" @click="exportPdf">PDF 다운로드</button>
          <button class="btn-danger btn-sm" @click="confirmDeleteProfile">삭제</button>
        </div>
      </div>

      <!-- 카테고리 탭 -->
      <div class="category-tabs">
        <button
          v-for="cat in categories"
          :key="cat.value"
          class="cat-tab"
          :class="{ active: activeCat === cat.value }"
          @click="activeCat = cat.value"
        >{{ cat.label }}</button>
      </div>

      <!-- 항목 목록 -->
      <div class="items-section">
        <div
          v-for="item in filteredItems"
          :key="item.id"
          class="resume-item-card"
        >
          <div class="item-header">
            <strong>{{ item.title }}</strong>
            <span v-if="item.organization" class="item-org"> | {{ item.organization }}</span>
            <span v-if="item.start_date" class="item-period"> {{ item.start_date }} ~ {{ item.end_date || '현재' }}</span>
          </div>
          <p v-if="item.description" class="item-desc">{{ item.description }}</p>
          <div v-if="item.tags?.length" class="item-tags">
            <span v-for="tag in item.tags" :key="tag" class="tag-chip">{{ tag }}</span>
          </div>
          <div class="item-actions">
            <button class="btn-text" @click="openEditItem(item)">편집</button>
            <button class="btn-text danger" @click="deleteItem(item.id)">삭제</button>
          </div>
        </div>
        <div v-if="filteredItems.length === 0" class="empty-items">항목이 없습니다.</div>
        <button class="btn-add" @click="openAddItem">+ {{ currentCatLabel }} 추가</button>
      </div>
    </main>

    <div v-else class="empty-editor">
      <p>왼쪽에서 이력서를 선택하거나 새로 만들어보세요.</p>
    </div>

    <!-- 이력서 생성 모달 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h3>새 이력서 만들기</h3>
        <input v-model="newProfileTitle" placeholder="이력서 제목" class="modal-input" />
        <div class="modal-actions">
          <button class="btn-outline" @click="showCreateModal = false">취소</button>
          <button class="btn-primary" @click="createProfile">만들기</button>
        </div>
      </div>
    </div>

    <!-- 항목 추가/편집 모달 -->
    <div v-if="showItemModal" class="modal-overlay" @click.self="showItemModal = false">
      <div class="modal modal-large">
        <h3>{{ editingItem ? '항목 편집' : '항목 추가' }}</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>카테고리</label>
            <select v-model="itemForm.category" class="modal-input">
              <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>제목 *</label>
            <input v-model="itemForm.title" placeholder="직무명, 프로젝트명 등" class="modal-input" />
          </div>
          <div class="form-group">
            <label>기관/회사</label>
            <input v-model="itemForm.organization" placeholder="회사명, 학교명 등" class="modal-input" />
          </div>
          <div class="form-group">
            <label>시작일</label>
            <input v-model="itemForm.start_date" placeholder="2023-03" class="modal-input" />
          </div>
          <div class="form-group">
            <label>종료일</label>
            <input v-model="itemForm.end_date" placeholder="2024-06 또는 현재" class="modal-input" />
          </div>
          <div class="form-group full-width">
            <label>설명</label>
            <textarea v-model="itemForm.description" placeholder="주요 업무 및 성과" class="modal-input" rows="4"></textarea>
          </div>
          <div class="form-group full-width">
            <label>태그 (쉼표로 구분)</label>
            <input v-model="itemForm.tagsStr" placeholder="Python, FastAPI, Vue.js" class="modal-input" />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showItemModal = false">취소</button>
          <button class="btn-primary" @click="saveItem">저장</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import axios from 'axios';

const API = '/api/v1/resume';

const profiles = ref([]);
const selectedProfile = ref(null);
const items = ref([]);
const activeCat = ref('experience');
const showCreateModal = ref(false);
const showItemModal = ref(false);
const newProfileTitle = ref('');
const editingTitle = ref(false);
const editTitleValue = ref('');
const summaryValue = ref('');
const editingItem = ref(null);
const titleInput = ref(null);

const categories = [
  { value: 'experience', label: '경력' },
  { value: 'education', label: '학력' },
  { value: 'project', label: '프로젝트' },
  { value: 'cert', label: '자격증' },
  { value: 'activity', label: '활동' },
  { value: 'skill', label: '기술' },
];

const defaultItemForm = () => ({
  category: activeCat.value,
  title: '',
  organization: '',
  start_date: '',
  end_date: '',
  description: '',
  tagsStr: '',
});

const itemForm = ref(defaultItemForm());

const filteredItems = computed(() =>
  items.value.filter(i => i.category === activeCat.value)
);

const currentCatLabel = computed(() =>
  categories.find(c => c.value === activeCat.value)?.label || ''
);

function formatDate(dt) {
  if (!dt) return '';
  return new Date(dt).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

async function loadProfiles() {
  const res = await axios.get(`${API}/profiles`);
  profiles.value = res.data;
}

async function selectProfile(p) {
  selectedProfile.value = p;
  summaryValue.value = p.summary || '';
  editingTitle.value = false;
  const res = await axios.get(`${API}/profiles/${p.id}/items`);
  items.value = res.data;
}

function openCreateProfile() {
  newProfileTitle.value = '';
  showCreateModal.value = true;
}

async function createProfile() {
  if (!newProfileTitle.value.trim()) return;
  const res = await axios.post(`${API}/profiles`, { title: newProfileTitle.value.trim() });
  profiles.value.unshift(res.data);
  await selectProfile(res.data);
  showCreateModal.value = false;
}

function startEditTitle() {
  editTitleValue.value = selectedProfile.value.title;
  editingTitle.value = true;
  nextTick(() => titleInput.value?.focus());
}

async function saveTitle() {
  if (!editTitleValue.value.trim()) { editingTitle.value = false; return; }
  await axios.put(`${API}/profiles/${selectedProfile.value.id}`, { title: editTitleValue.value.trim() });
  selectedProfile.value.title = editTitleValue.value.trim();
  const p = profiles.value.find(p => p.id === selectedProfile.value.id);
  if (p) p.title = editTitleValue.value.trim();
  editingTitle.value = false;
}

async function saveSummary() {
  await axios.put(`${API}/profiles/${selectedProfile.value.id}`, { summary: summaryValue.value });
}

async function confirmDeleteProfile() {
  if (!confirm(`"${selectedProfile.value.title}" 이력서를 삭제하시겠습니까?`)) return;
  await axios.delete(`${API}/profiles/${selectedProfile.value.id}`);
  profiles.value = profiles.value.filter(p => p.id !== selectedProfile.value.id);
  selectedProfile.value = null;
  items.value = [];
}

function openAddItem() {
  editingItem.value = null;
  itemForm.value = defaultItemForm();
  itemForm.value.category = activeCat.value;
  showItemModal.value = true;
}

function openEditItem(item) {
  editingItem.value = item;
  itemForm.value = {
    category: item.category,
    title: item.title,
    organization: item.organization || '',
    start_date: item.start_date || '',
    end_date: item.end_date || '',
    description: item.description || '',
    tagsStr: (item.tags || []).join(', '),
  };
  showItemModal.value = true;
}

async function saveItem() {
  if (!itemForm.value.title.trim()) return;
  const payload = {
    category: itemForm.value.category,
    title: itemForm.value.title.trim(),
    organization: itemForm.value.organization || null,
    start_date: itemForm.value.start_date || null,
    end_date: itemForm.value.end_date || null,
    description: itemForm.value.description || null,
    tags: itemForm.value.tagsStr ? itemForm.value.tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [],
  };

  if (editingItem.value) {
    const res = await axios.put(`${API}/items/${editingItem.value.id}`, payload);
    const idx = items.value.findIndex(i => i.id === editingItem.value.id);
    if (idx !== -1) items.value[idx] = res.data;
  } else {
    const res = await axios.post(`${API}/profiles/${selectedProfile.value.id}/items`, payload);
    items.value.push(res.data);
  }
  showItemModal.value = false;
}

async function deleteItem(itemId) {
  if (!confirm('항목을 삭제하시겠습니까?')) return;
  await axios.delete(`${API}/items/${itemId}`);
  items.value = items.value.filter(i => i.id !== itemId);
}

async function exportJson() {
  try {
    const res = await axios.get(`${API}/profiles/${selectedProfile.value.id}/export/json`, {
      responseType: 'blob',
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_${selectedProfile.value.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('JSON 내보내기에 실패했습니다.');
  }
}

async function exportPdf() {
  try {
    const res = await axios.get(`${API}/profiles/${selectedProfile.value.id}/export/pdf`, {
      responseType: 'blob',
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_${selectedProfile.value.id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('PDF 다운로드에 실패했습니다.');
  }
}

onMounted(loadProfiles);
</script>

<style scoped>
.resume-page {
  display: flex;
  height: 100%;
  background: #f8f9fa;
}

/* 왼쪽 패널 */
.profile-panel {
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

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.profile-list {
  list-style: none;
  margin: 0;
  padding: 8px 0;
  overflow-y: auto;
  flex: 1;
}

.profile-item {
  padding: 10px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}

.profile-item:hover { background: #f5f5f5; }
.profile-item.active { border-left-color: #F76707; background: #fff5ee; }

.profile-title { font-size: 14px; font-weight: 500; color: #333; }
.profile-date { font-size: 11px; color: #999; margin-top: 2px; }

.empty-hint { padding: 20px 16px; font-size: 13px; color: #999; }

/* 오른쪽 에디터 */
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
  gap: 16px;
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  color: #222;
  cursor: pointer;
  margin: 0 0 8px;
}

.edit-hint { font-size: 14px; opacity: 0.4; }

.title-input {
  font-size: 22px;
  font-weight: 700;
  border: none;
  border-bottom: 2px solid #F76707;
  outline: none;
  padding: 2px 0;
  width: 300px;
  margin-bottom: 8px;
}

.summary-input {
  width: 400px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 8px;
  font-size: 13px;
  resize: vertical;
  color: #555;
  font-family: inherit;
}

.export-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 카테고리 탭 */
.category-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
  padding-bottom: 0;
}

.cat-tab {
  padding: 8px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.15s;
}

.cat-tab.active {
  color: #F76707;
  border-bottom-color: #F76707;
  font-weight: 600;
}

/* 항목 카드 */
.resume-item-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.item-header { font-size: 14px; color: #333; margin-bottom: 6px; }
.item-org { color: #666; }
.item-period { color: #888; font-size: 12px; margin-left: 8px; }

.item-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 6px 0;
  white-space: pre-wrap;
}

.item-tags { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0; }
.tag-chip {
  background: #fff5ee;
  color: #F76707;
  border: 1px solid #ffd8b8;
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 11px;
}

.item-actions { display: flex; gap: 8px; margin-top: 8px; justify-content: flex-end; }

.empty-items {
  padding: 24px;
  text-align: center;
  color: #999;
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

/* 버튼 공통 */
.btn-primary {
  background: #F76707;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}
.btn-primary:hover { background: #e05500; }

.btn-sm { padding: 5px 10px; font-size: 12px; }

.btn-outline {
  background: #fff;
  color: #F76707;
  border: 1px solid #F76707;
  border-radius: 6px;
  padding: 7px 14px;
  cursor: pointer;
  font-size: 13px;
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

.btn-text { background: none; border: none; cursor: pointer; font-size: 12px; color: #888; padding: 2px 6px; }
.btn-text:hover { color: #F76707; }
.btn-text.danger:hover { color: #e53e3e; }

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
  min-width: 320px;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.modal-large { max-width: 640px; }

.modal h3 { margin: 0 0 20px; font-size: 17px; color: #222; }

.modal-input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 9px 12px;
  font-size: 14px;
  box-sizing: border-box;
  font-family: inherit;
}

.modal-input:focus { outline: none; border-color: #F76707; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  font-weight: 500;
}

.full-width { grid-column: 1 / -1; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
