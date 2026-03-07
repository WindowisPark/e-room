<template>
  <div class="resume-page">
    <!-- 왼쪽: 이력서 목록 -->
    <aside class="profile-panel">
      <div class="panel-header">
        <h2>이력서</h2>
        <button class="btn-primary btn-sm" @click="openCreateProfile">+ 새 이력서</button>
      </div>

      <div class="type-tabs">
        <button :class="{ active: profileType === 'job' }" @click="profileType = 'job'">취업용</button>
        <button :class="{ active: profileType === 'academic' }" @click="profileType = 'academic'">학업용</button>
      </div>

      <ul class="profile-list">
        <li
          v-for="p in filteredProfiles"
          :key="p.id"
          class="profile-item"
          :class="{ active: selectedProfile?.id === p.id }"
          @click="selectProfile(p)"
        >
          <div class="profile-title">{{ p.title }}</div>
          <div class="profile-date">{{ formatDate(p.updated_at) }}</div>
        </li>
        <li v-if="filteredProfiles.length === 0" class="empty-hint">이력서가 없습니다.</li>
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
            {{ selectedProfile.title }} <span class="edit-hint"><i class="fa-regular fa-pen-to-square"></i></span>
          </h1>
        </div>
        <div class="export-buttons">
          <button class="btn-outline" @click="exportJson">JSON 내보내기</button>
          <button class="btn-outline" @click="exportPdf">PDF 다운로드</button>
          <button class="btn-danger btn-sm" @click="confirmDeleteProfile">삭제</button>
        </div>
      </div>

      <!-- 기본정보 섹션 -->
      <div class="contact-section">
        <h3 class="section-title"><i class="fa-solid fa-clipboard-list"></i> 기본정보</h3>
        <div class="contact-grid">
          <div class="contact-field">
            <label>이름</label>
            <input v-model="contactInfo.name" @blur="saveContactInfo" placeholder="홍길동" class="contact-input" />
          </div>
          <div class="contact-field">
            <label>연락처</label>
            <input v-model="contactInfo.phone" @blur="saveContactInfo" placeholder="010-0000-0000" class="contact-input" />
          </div>
          <div class="contact-field">
            <label>이메일</label>
            <input v-model="contactInfo.email" @blur="saveContactInfo" placeholder="user@email.com" class="contact-input" />
          </div>
          <div class="contact-field">
            <label>지역</label>
            <input v-model="contactInfo.location" @blur="saveContactInfo" placeholder="서울" class="contact-input" />
          </div>
          <div class="contact-field full-width">
            <label>한 줄 소개</label>
            <input v-model="summaryValue" @blur="saveSummary" placeholder="간단한 자기소개를 입력하세요" class="contact-input" />
          </div>
          <div class="contact-field full-width">
            <label>링크</label>
            <div class="links-wrap">
              <div v-for="(link, li) in contactInfo.links" :key="li" class="link-row">
                <select v-model="link.label" @change="saveContactInfo" class="link-label-select">
                  <option>GitHub</option>
                  <option>블로그</option>
                  <option>포트폴리오</option>
                  <option>LinkedIn</option>
                  <option>기타</option>
                </select>
                <input v-model="link.url" @blur="saveContactInfo" placeholder="https://..." class="link-url-input" />
                <button @click="removeLink(li)" class="btn-icon-sm">✕</button>
              </div>
              <button class="btn-add-link" @click="addLink">+ 링크 추가</button>
            </div>
          </div>
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
        <draggable
          v-model="sortableItems"
          item-key="id"
          handle=".drag-handle"
          ghost-class="sortable-ghost"
          @end="onResumeDragEnd"
        >
          <template #item="{ element: item }">
            <div class="resume-item-card">
              <div class="item-header">
                <div class="item-header-info">
                  <strong class="item-title">{{ item.title }}</strong>
                  <span v-if="item.organization && activeCat !== 'skill'" class="item-org"> | {{ item.organization }}</span>
                  <span v-if="item.start_date && activeCat !== 'skill'" class="item-period">
                    {{ item.start_date }}{{ activeCat !== 'cert' ? ` ~ ${item.end_date || '현재'}` : '' }}
                  </span>
                  <span v-if="activeCat === 'education' && getGraduation(item)" class="grad-badge">
                    {{ getGraduation(item) }}
                  </span>
                </div>
                <div class="item-header-actions">
                  <i class="fa-solid fa-grip-vertical drag-handle"></i>
                  <button class="btn-text" @click="openEditItem(item)">편집</button>
                  <button class="btn-text danger" @click="deleteItem(item.id)">삭제</button>
                </div>
              </div>
              <div v-if="item.description && activeCat !== 'skill'" class="item-desc">{{ item.description }}</div>
              <div v-if="item.tags?.length" class="item-tags">
                <span v-for="tag in displayTags(item)" :key="tag" class="tag-chip">{{ tag }}</span>
              </div>
            </div>
          </template>
        </draggable>
        <div v-if="sortableItems.length === 0" class="empty-items">항목이 없습니다.</div>
        <button class="btn-add" @click="openAddItem">+ {{ currentCatLabel }} 추가</button>
      </div>
    </main>

    <div v-else class="empty-editor">
      <i class="fa-regular fa-file-lines empty-editor-icon"></i>
      <p class="empty-editor-title">아직 이력서가 없어요</p>
      <p class="empty-editor-desc">AI가 함께 다듬어주는 이력서,<br>지금 시작해보세요.</p>
      <button class="btn-primary" @click="openCreateProfile">+ 첫 이력서 만들기</button>
    </div>

    <!-- 이력서 생성 모달 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="dialog-box">
        <h3>새 이력서 만들기</h3>
        <input v-model="newProfileTitle" placeholder="이력서 제목" class="modal-input" />
        <div class="type-radio-group">
          <label><input type="radio" v-model="newProfileType" value="job" /> 취업용</label>
          <label><input type="radio" v-model="newProfileType" value="academic" /> 학업용</label>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="showCreateModal = false">취소</button>
          <button class="btn-primary" @click="createProfile">만들기</button>
        </div>
      </div>
    </div>

    <!-- 항목 추가/편집 모달 -->
    <div v-if="showItemModal" class="modal-overlay" @click.self="showItemModal = false">
      <div class="dialog-box dialog-large">
        <h3>{{ editingItem ? currentCatLabel + ' 편집' : currentCatLabel + ' 추가' }}</h3>

        <!-- skill 전용: 태그 입력 -->
        <template v-if="activeCat === 'skill'">
          <div class="form-group">
            <label>그룹 이름 (선택, 예: 언어, 프레임워크)</label>
            <input v-model="itemForm.title" placeholder="언어" class="modal-input" />
          </div>
          <div class="form-group">
            <label>기술 태그</label>
            <div class="skill-tag-area">
              <span v-for="(tag, ti) in skillTagsList" :key="ti" class="skill-chip">
                {{ tag }}
                <button @click.prevent="removeSkillTag(ti)" class="skill-chip-remove">×</button>
              </span>
              <input
                v-model="skillTagInput"
                @keydown.enter.prevent="addSkillTag"
                @keydown.188.prevent="addSkillTag"
                placeholder="기술명 입력 후 Enter 또는 ,"
                class="skill-tag-input"
              />
            </div>
          </div>
        </template>

        <!-- 일반 카테고리 -->
        <template v-else>
          <div class="form-grid">
            <div class="form-group">
              <label>{{ catFieldLabels.title }} *</label>
              <input v-model="itemForm.title" :placeholder="catFieldLabels.title" class="modal-input" />
            </div>
            <div class="form-group">
              <label>{{ catFieldLabels.org }}</label>
              <input v-model="itemForm.organization" :placeholder="catFieldLabels.org" class="modal-input" />
            </div>

            <!-- cert: 취득일만 -->
            <template v-if="activeCat === 'cert'">
              <div class="form-group">
                <label>취득일</label>
                <input v-model="itemForm.start_date" placeholder="2023-06" class="modal-input" />
              </div>
            </template>

            <!-- 그 외: 시작일 ~ 종료일 -->
            <template v-else>
              <div class="form-group">
                <label>시작일</label>
                <input v-model="itemForm.start_date" placeholder="2023-03" class="modal-input" />
              </div>
              <div class="form-group">
                <label>종료일</label>
                <input v-model="itemForm.end_date" placeholder="2024-06 또는 현재" class="modal-input" />
              </div>
            </template>

            <!-- education: 졸업구분 -->
            <div class="form-group" v-if="activeCat === 'education'">
              <label>졸업구분</label>
              <select v-model="itemForm.graduation" class="modal-input">
                <option value="">선택</option>
                <option v-for="opt in GRAD_OPTIONS" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>

            <!-- 설명 (experience, project, activity) -->
            <div class="form-group full-width" v-if="['experience', 'project', 'activity'].includes(activeCat)">
              <label>{{ catFieldLabels.desc }}</label>
              <textarea v-model="itemForm.description" :placeholder="catFieldLabels.desc" class="modal-input" rows="4"></textarea>
            </div>

            <!-- project: 링크 -->
            <div class="form-group full-width" v-if="activeCat === 'project'">
              <label>링크 (GitHub, 배포 URL 등)</label>
              <input v-model="itemForm.link" placeholder="https://github.com/..." class="modal-input" />
            </div>

            <!-- experience, project: 기술스택 -->
            <div class="form-group full-width" v-if="['experience', 'project'].includes(activeCat)">
              <label>기술스택 (쉼표로 구분)</label>
              <input v-model="itemForm.tagsStr" placeholder="Python, Vue.js, FastAPI" class="modal-input" />
            </div>
          </div>
        </template>

        <div class="modal-actions">
          <button class="btn-outline" @click="showItemModal = false">취소</button>
          <button class="btn-primary" @click="saveItem">저장</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import axios from '@/api/index.js';
import draggable from 'vuedraggable';

const API = '/resume';

const GRAD_OPTIONS = ['졸업', '재학중', '졸업예정', '수료', '중퇴'];

// ─── 상태 ────────────────────────────────────────────────────────

const profiles = ref([]);
const selectedProfile = ref(null);
const items = ref([]);
const activeCat = ref('experience');
const showCreateModal = ref(false);
const showItemModal = ref(false);
const newProfileTitle = ref('');
const newProfileType = ref('job');
const profileType = ref('job');
const editingTitle = ref(false);
const editTitleValue = ref('');
const summaryValue = ref('');
const editingItem = ref(null);
const titleInput = ref(null);
const skillTagInput = ref('');

const contactInfo = ref({ name: '', phone: '', email: '', location: '', links: [] });

const itemForm = ref(defaultItemForm());

const categories = [
  { value: 'experience', label: '경력' },
  { value: 'education', label: '학력' },
  { value: 'project', label: '프로젝트' },
  { value: 'cert', label: '자격증' },
  { value: 'activity', label: '활동' },
  { value: 'skill', label: '기술' },
];

// 카테고리별 라벨
const CAT_LABELS = {
  experience: { title: '직무명', org: '회사명', desc: '담당업무 및 성과' },
  education:  { title: '전공',   org: '학교명', desc: '' },
  project:    { title: '프로젝트명', org: '팀/기관', desc: '설명 및 성과' },
  cert:       { title: '자격증명', org: '발행기관', desc: '' },
  activity:   { title: '활동명', org: '기관·단체', desc: '활동 설명' },
  skill:      { title: '', org: '', desc: '' },
};

function defaultItemForm() {
  return {
    title: '', organization: '', start_date: '', end_date: '',
    description: '', tagsStr: '', graduation: '', link: '',
  };
}

// ─── Computed ─────────────────────────────────────────────────

const filteredProfiles = computed(() =>
  profiles.value.filter(p => (p.profile_type || 'job') === profileType.value)
);

const filteredItems = computed(() =>
  items.value
    .filter(i => i.category === activeCat.value)
    .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0))
);

const sortableItems = ref([]);
watch(filteredItems, (v) => { sortableItems.value = [...v]; }, { immediate: true });

const currentCatLabel = computed(() =>
  categories.find(c => c.value === activeCat.value)?.label || ''
);

const catFieldLabels = computed(() => CAT_LABELS[activeCat.value] || CAT_LABELS.experience);

const skillTagsList = computed(() =>
  itemForm.value.tagsStr
    ? itemForm.value.tagsStr.split(',').map(t => t.trim()).filter(Boolean)
    : []
);

// ─── 유틸 ─────────────────────────────────────────────────────

function formatDate(dt) {
  if (!dt) return '';
  return new Date(dt).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getGraduation(item) {
  const first = item.tags?.[0];
  return first && GRAD_OPTIONS.includes(first) ? first : '';
}

function displayTags(item) {
  if (!item.tags) return [];
  return item.tags.filter(t => !t.startsWith('url:') && !GRAD_OPTIONS.includes(t));
}

function itemToForm(item) {
  const form = {
    title: item.title || '',
    organization: item.organization || '',
    start_date: item.start_date || '',
    end_date: item.end_date || '',
    description: item.description || '',
    tagsStr: '',
    graduation: '',
    link: '',
  };
  const tags = item.tags || [];
  if (item.category === 'education') {
    form.graduation = (tags[0] && GRAD_OPTIONS.includes(tags[0])) ? tags[0] : '';
    form.tagsStr = tags.slice(form.graduation ? 1 : 0).join(', ');
  } else if (item.category === 'project') {
    const urlTag = tags.find(t => t.startsWith('url:'));
    form.link = urlTag ? urlTag.replace('url:', '') : '';
    form.tagsStr = tags.filter(t => !t.startsWith('url:')).join(', ');
  } else {
    form.tagsStr = tags.join(', ');
  }
  return form;
}

function buildPayload() {
  const cat = activeCat.value;
  const f = itemForm.value;
  let tags = [];
  if (cat === 'skill') {
    tags = skillTagsList.value;
  } else if (cat === 'education') {
    const others = f.tagsStr ? f.tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
    tags = f.graduation ? [f.graduation, ...others] : others;
  } else if (cat === 'project') {
    const base = f.tagsStr ? f.tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
    tags = f.link ? [...base, `url:${f.link}`] : base;
  } else {
    tags = f.tagsStr ? f.tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
  }

  return {
    category: cat,
    title: (cat === 'skill' && !f.title.trim()) ? '기술' : f.title.trim(),
    organization: f.organization || null,
    start_date: f.start_date || null,
    end_date: cat !== 'cert' ? (f.end_date || null) : null,
    description: f.description || null,
    tags: tags.length ? tags : null,
  };
}

// ─── Skill 태그 ───────────────────────────────────────────────

function addSkillTag() {
  const val = skillTagInput.value.trim().replace(/,/g, '');
  if (!val) return;
  const current = skillTagsList.value;
  itemForm.value.tagsStr = [...current, val].join(', ');
  skillTagInput.value = '';
}

function removeSkillTag(idx) {
  const tags = [...skillTagsList.value];
  tags.splice(idx, 1);
  itemForm.value.tagsStr = tags.join(', ');
}

// ─── 프로필 CRUD ─────────────────────────────────────────────

async function loadProfiles() {
  try {
    const res = await axios.get(`${API}/profiles`);
    profiles.value = res.data;
  } catch (e) {
    console.warn('이력서 로딩 실패:', e.response?.status);
  }
}

async function selectProfile(p) {
  selectedProfile.value = p;
  summaryValue.value = p.summary || '';
  const ci = p.contact_info || {};
  contactInfo.value = {
    name: ci.name || '',
    phone: ci.phone || '',
    email: ci.email || '',
    location: ci.location || '',
    links: Array.isArray(ci.links) ? ci.links : [],
  };
  editingTitle.value = false;
  const res = await axios.get(`${API}/profiles/${p.id}/items`);
  items.value = res.data;
}

function openCreateProfile() {
  newProfileTitle.value = '';
  newProfileType.value = profileType.value;
  showCreateModal.value = true;
}

async function createProfile() {
  if (!newProfileTitle.value.trim()) return;
  const res = await axios.post(`${API}/profiles`, {
    title: newProfileTitle.value.trim(),
    profile_type: newProfileType.value,
  });
  profiles.value.unshift(res.data);
  profileType.value = newProfileType.value;
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

async function saveContactInfo() {
  await axios.put(`${API}/profiles/${selectedProfile.value.id}`, { contact_info: { ...contactInfo.value } });
}

function addLink() {
  contactInfo.value.links.push({ label: 'GitHub', url: '' });
}

async function removeLink(idx) {
  contactInfo.value.links.splice(idx, 1);
  await saveContactInfo();
}

async function confirmDeleteProfile() {
  if (!confirm(`"${selectedProfile.value.title}" 이력서를 삭제하시겠습니까?`)) return;
  await axios.delete(`${API}/profiles/${selectedProfile.value.id}`);
  profiles.value = profiles.value.filter(p => p.id !== selectedProfile.value.id);
  selectedProfile.value = null;
  items.value = [];
}

// ─── 항목 CRUD ────────────────────────────────────────────────

function openAddItem() {
  editingItem.value = null;
  itemForm.value = defaultItemForm();
  skillTagInput.value = '';
  showItemModal.value = true;
}

function openEditItem(item) {
  editingItem.value = item;
  itemForm.value = itemToForm(item);
  skillTagInput.value = '';
  showItemModal.value = true;
}

async function saveItem() {
  if (!itemForm.value.title.trim() && activeCat.value !== 'skill') return;
  // skill에서 Enter 누른 게 남아 있을 수 있으니 먼저 처리
  if (activeCat.value === 'skill' && skillTagInput.value.trim()) addSkillTag();

  const payload = buildPayload();

  if (editingItem.value) {
    const res = await axios.put(`${API}/items/${editingItem.value.id}`, payload);
    const idx = items.value.findIndex(i => i.id === editingItem.value.id);
    if (idx !== -1) items.value[idx] = res.data;
  } else {
    payload.order_index = filteredItems.value.length;
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

// ─── 순서 변경 ────────────────────────────────────────────────

async function moveItem(item, direction) {
  const sorted = filteredItems.value;
  const idx = sorted.findIndex(i => i.id === item.id);
  const targetIdx = idx + direction;
  if (targetIdx < 0 || targetIdx >= sorted.length) return;

  const other = sorted[targetIdx];
  const tmp = item.order_index ?? idx;
  item.order_index = other.order_index ?? targetIdx;
  other.order_index = tmp;

  if (item.order_index === other.order_index) {
    item.order_index = idx * 10;
    other.order_index = targetIdx * 10;
  }

  await Promise.all([
    axios.put(`${API}/items/${item.id}`, { order_index: item.order_index }),
    axios.put(`${API}/items/${other.id}`, { order_index: other.order_index }),
  ]);
}

async function onResumeDragEnd() {
  sortableItems.value.forEach((item, idx) => { item.order_index = idx; });
  await Promise.all(
    sortableItems.value.map(item =>
      axios.put(`${API}/items/${item.id}`, { order_index: item.order_index })
    )
  );
}

// ─── Export ──────────────────────────────────────────────────

async function exportJson() {
  try {
    const res = await axios.get(`${API}/profiles/${selectedProfile.value.id}/export/json`, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url; a.download = `resume_${selectedProfile.value.id}.json`; a.click();
    URL.revokeObjectURL(url);
  } catch { alert('JSON 내보내기에 실패했습니다.'); }
}

async function exportPdf() {
  try {
    const res = await axios.get(`${API}/profiles/${selectedProfile.value.id}/export/pdf`, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url; a.download = `resume_${selectedProfile.value.id}.pdf`; a.click();
    URL.revokeObjectURL(url);
  } catch { alert('PDF 다운로드에 실패했습니다.'); }
}

onMounted(loadProfiles);
</script>

<style scoped>
.resume-page {
  display: flex;
  height: 100%;
  background: var(--bg-page);
}

/* 왼쪽 패널 */
.profile-panel {
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

.type-tabs { display: flex; border-bottom: 1px solid #eee; }
.type-tabs button {
  flex: 1; padding: 9px 0; background: none; border: none;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  cursor: pointer; font-size: 13px; color: #888; font-weight: 500; transition: all 0.15s;
}
.type-tabs button.active { color: #F76707; border-bottom-color: #F76707; }

.type-radio-group { display: flex; gap: 20px; margin: 12px 0; }
.type-radio-group label { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; color: #444; }

.profile-list { list-style: none; margin: 0; padding: 8px 0; overflow-y: auto; flex: 1; }
.profile-item { padding: 10px 16px; cursor: pointer; border-left: 3px solid transparent; transition: all 0.15s; }
.profile-item:hover { background: #f5f5f5; }
.profile-item.active { border-left-color: #F76707; background: #fff5ee; }
.profile-title { font-size: 14px; font-weight: 500; color: #333; }
.profile-date { font-size: 11px; color: #999; margin-top: 2px; }
.empty-hint { padding: 20px 16px; font-size: 13px; color: #999; }

/* 오른쪽 에디터 */
.editor-panel { flex: 1; overflow-y: auto; padding: 24px 32px; }

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 16px;
}
.profile-name { font-size: 22px; font-weight: 700; color: #222; cursor: pointer; margin: 0 0 4px; }
.edit-hint { font-size: 14px; opacity: 0.4; }
.title-input {
  font-size: 22px; font-weight: 700; border: none;
  border-bottom: 2px solid #F76707; outline: none; padding: 2px 0; width: 300px; margin-bottom: 4px;
}
.export-buttons { display: flex; gap: 8px; flex-shrink: 0; }

/* 기본정보 섹션 */
.contact-section {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}
.section-title { font-size: 14px; font-weight: 600; color: #444; margin: 0 0 16px; }

.contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.contact-field { display: flex; flex-direction: column; gap: 4px; }
.contact-field.full-width { grid-column: 1 / -1; }
.contact-field label { font-size: 11px; color: #888; font-weight: 500; }
.contact-input {
  border: 1px solid #e0e0e0; border-radius: 6px; padding: 7px 10px;
  font-size: 13px; font-family: inherit; background: #fafafa; transition: border-color 0.15s;
}
.contact-input:focus { outline: none; border-color: #F76707; background: #fff; }

.links-wrap { display: flex; flex-direction: column; gap: 8px; }
.link-row { display: flex; gap: 8px; align-items: center; }
.link-label-select {
  border: 1px solid #e0e0e0; border-radius: 6px; padding: 7px 8px;
  font-size: 13px; font-family: inherit; background: #fafafa; min-width: 90px;
}
.link-label-select:focus { outline: none; border-color: #F76707; }
.link-url-input {
  flex: 1; border: 1px solid #e0e0e0; border-radius: 6px; padding: 7px 10px;
  font-size: 13px; font-family: inherit; background: #fafafa;
}
.link-url-input:focus { outline: none; border-color: #F76707; }
.btn-icon-sm {
  background: none; border: none; color: #bbb; cursor: pointer;
  font-size: 13px; padding: 4px 6px; border-radius: 4px;
}
.btn-icon-sm:hover { color: #e53e3e; background: #fef2f2; }
.btn-add-link {
  background: none; border: 1px dashed #ddd; border-radius: 6px; color: #999;
  font-size: 12px; cursor: pointer; padding: 6px 12px; transition: all 0.15s; align-self: flex-start;
}
.btn-add-link:hover { border-color: #F76707; color: #F76707; }

/* 카테고리 탭 */
.category-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid #eee; }
.cat-tab {
  padding: 8px 16px; background: none; border: none;
  border-bottom: 2px solid transparent; margin-bottom: -2px;
  cursor: pointer; font-size: 14px; color: #666; transition: all 0.15s;
}
.cat-tab.active { color: #F76707; border-bottom-color: #F76707; font-weight: 600; }

/* 항목 카드 */
.items-section { padding-bottom: 24px; }
.resume-item-card {
  background: #fff; border: 1px solid #e8e8e8;
  border-radius: 8px; padding: 16px; margin-bottom: 10px;
}
.item-header { display: flex; justify-content: space-between; align-items: center; }
.item-header-info { display: flex; align-items: baseline; gap: 6px; flex: 1; min-width: 0; overflow: hidden; }
.item-title { font-size: 14px; color: #222; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.item-org { font-size: 13px; color: #666; white-space: nowrap; }
.item-period { font-size: 12px; color: #999; white-space: nowrap; }
.grad-badge {
  font-size: 11px; background: #e8f4ff; color: #3182ce;
  border-radius: 10px; padding: 2px 8px; white-space: nowrap;
}
.item-header-actions { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.drag-handle { cursor: grab; color: #ccc; padding: 0 6px; font-size: 14px; }
.drag-handle:hover { color: #F76707; }
.drag-handle:active { cursor: grabbing; }
.sortable-ghost { opacity: 0.4; background: #fff5ee; }
.btn-icon {
  background: none; border: none; color: #ccc; cursor: pointer;
  font-size: 12px; padding: 2px 5px; border-radius: 4px;
}
.order-btn:hover { color: #F76707; background: #fff5ee; }
.order-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.item-desc { font-size: 13px; color: #555; line-height: 1.6; margin: 8px 0 4px; white-space: pre-wrap; }
.item-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.tag-chip {
  background: #fff5ee; color: #F76707; border: 1px solid #ffd8b8;
  border-radius: 12px; padding: 2px 10px; font-size: 11px;
}

.empty-items { padding: 24px; text-align: center; color: #999; font-size: 14px; }

.btn-add {
  display: block; width: 100%; padding: 12px;
  background: #fff; border: 2px dashed #ddd; border-radius: 8px;
  color: #888; font-size: 14px; cursor: pointer; text-align: center; transition: all 0.15s;
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
  background: #F76707; color: #fff; border: none; border-radius: 6px;
  padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-primary:hover { background: #e05500; }
.btn-sm { padding: 5px 10px; font-size: 12px; }

.btn-outline {
  background: #fff; color: #F76707; border: 1px solid #F76707;
  border-radius: 6px; padding: 7px 14px; cursor: pointer; font-size: 13px;
}
.btn-outline:hover { background: #fff5ee; }

.btn-danger {
  background: #fff; color: #e53e3e; border: 1px solid #e53e3e;
  border-radius: 6px; padding: 5px 10px; cursor: pointer; font-size: 12px;
}

.btn-text { background: none; border: none; cursor: pointer; font-size: 12px; color: #888; padding: 2px 6px; }
.btn-text:hover { color: #F76707; }
.btn-text.danger:hover { color: #e53e3e; }

/* 모달 */
.modal-overlay {
  position: fixed !important; inset: 0; background: rgba(0,0,0,0.4);
  display: flex !important; align-items: center; justify-content: center;
  z-index: 9999 !important;
}
.dialog-box {
  background: var(--bg-surface); border-radius: var(--radius-lg); padding: 28px;
  min-width: 320px; max-width: 480px; width: 100%; box-shadow: var(--shadow-float);
}
.dialog-large { max-width: 600px; }
.dialog-box h3 { margin: 0 0 20px; font-size: 17px; color: #222; }
.modal-input {
  width: 100%; border: 1px solid #ddd; border-radius: 6px;
  padding: 9px 12px; font-size: 14px; box-sizing: border-box;
  font-family: inherit; resize: vertical;
}
.modal-input:focus { outline: none; border-color: #F76707; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 4px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 500; }
.full-width { grid-column: 1 / -1; }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }

/* Skill 태그 입력 */
.skill-tag-area {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 8px;
  border: 1px solid #e0e0e0; border-radius: 8px; background: #fff;
  min-height: 44px; align-items: center;
}
.skill-chip {
  display: inline-flex; align-items: center; gap: 4px;
  background: #fff5ee; color: #F76707; border: 1px solid #ffd8b8;
  border-radius: 12px; padding: 3px 8px 3px 10px; font-size: 12px;
}
.skill-chip-remove {
  background: none; border: none; color: #F76707; cursor: pointer;
  font-size: 14px; padding: 0; line-height: 1; opacity: 0.7;
}
.skill-chip-remove:hover { opacity: 1; }
.skill-tag-input { border: none; outline: none; font-size: 13px; min-width: 120px; flex: 1; }
</style>
