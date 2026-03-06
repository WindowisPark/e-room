<template>
  <div class="jobs-page">
    <!-- 왼쪽: 저장된 기업 목록 -->
    <aside class="company-panel">
      <div class="panel-header">
        <h2>기업 조사</h2>
        <button class="btn-primary btn-sm" @click="openAnalyzeForm">+ 공고 분석</button>
      </div>
      <ul class="company-list">
        <li
          v-for="c in companies"
          :key="c.id"
          class="company-item"
          :class="{ active: selectedCompany?.id === c.id }"
          @click="selectCompany(c)"
        >
          <div class="company-name">{{ c.company_name }}</div>
          <div class="company-job">{{ c.job_title || '직무 미정' }}</div>
        </li>
        <li v-if="companies.length === 0" class="empty-hint">저장된 기업이 없습니다.</li>
      </ul>
    </aside>

    <!-- 오른쪽 -->
    <main class="detail-panel">

      <!-- ① 공고 분석 / 직접입력 폼 -->
      <div v-if="showAnalyzeForm" class="analyze-form">
        <h2>채용 공고 분석</h2>
        <div class="analyze-mode-tabs">
          <button :class="{ active: analyzeMode === 'ai' }" @click="analyzeMode = 'ai'">URL / 텍스트 분석</button>
          <button :class="{ active: analyzeMode === 'manual' }" @click="analyzeMode = 'manual'">직접 입력</button>
        </div>

        <!-- AI 분석 -->
        <template v-if="analyzeMode === 'ai'">
          <div class="form-group">
            <label>공고 URL (선택)</label>
            <input v-model="analyzeUrl" placeholder="https://..." class="form-input" />
          </div>
          <div class="divider-text">또는</div>
          <div class="form-group">
            <label>공고 텍스트 직접 붙여넣기</label>
            <textarea v-model="analyzeText" placeholder="채용 공고 내용을 붙여넣어 주세요..." class="form-input" rows="10"></textarea>
          </div>
          <div class="form-actions">
            <button class="btn-outline" @click="showAnalyzeForm = false">취소</button>
            <button class="btn-primary" @click="runAnalysis" :disabled="analyzing">
              <span v-if="analyzing">분석 중... ⏳</span>
              <span v-else>AI 분석 시작</span>
            </button>
          </div>
        </template>

        <!-- 직접 입력 -->
        <template v-else>
          <div class="manual-grid">
            <div class="form-group">
              <label>회사명 *</label>
              <input v-model="manualForm.company_name" placeholder="네이버" class="form-input" />
            </div>
            <div class="form-group">
              <label>채용 직무</label>
              <input v-model="manualForm.job_title" placeholder="백엔드 개발자" class="form-input" />
            </div>
          </div>
          <div class="form-group">
            <label>회사 소개</label>
            <textarea v-model="manualForm.overview" placeholder="회사 및 직무 개요를 입력하세요..." class="form-input" rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>자격요건 (줄바꿈으로 구분)</label>
            <textarea v-model="manualForm.requirements_text" placeholder="경력 3년 이상&#10;Java 또는 Kotlin 개발 경험" class="form-input" rows="4"></textarea>
          </div>
          <div class="form-group">
            <label>기술스택</label>
            <div class="tag-input-area">
              <span v-for="t in manualTechTags" :key="t" class="tag-chip">
                {{ t }}
                <button @click="removeManualTech(t)" class="chip-remove">×</button>
              </span>
              <input
                v-model="manualTechInput"
                @keydown.enter.prevent="addManualTech"
                @keydown.188.prevent="addManualTech"
                placeholder="기술명 입력 후 Enter"
                class="chip-input"
              />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-outline" @click="showAnalyzeForm = false">취소</button>
            <button class="btn-primary" @click="saveManualEntry">저장하기</button>
          </div>
        </template>
      </div>

      <!-- ② AI 분석 결과 미리보기 (저장 전) -->
      <div v-else-if="analysisResult" class="analysis-result">
        <div class="result-header">
          <div>
            <h2>{{ analysisResult.analysis.company_name || '회사명 미확인' }}</h2>
            <p class="job-title-text">{{ analysisResult.analysis.job_title || '' }}</p>
          </div>
          <button class="btn-primary" @click="saveAnalysis">저장하기</button>
        </div>
        <AnalysisCards :analysis="analysisResult.analysis" :readonly="true" />
      </div>

      <!-- ③ 저장된 기업 상세 (탭 구조) -->
      <div v-else-if="selectedCompany" class="company-detail">
        <div class="detail-header">
          <div>
            <h2>{{ selectedCompany.company_name }}</h2>
            <p class="job-title-text">{{ selectedCompany.job_title || '' }}</p>
            <a v-if="selectedCompany.source_url" :href="selectedCompany.source_url" target="_blank" class="source-link">
              원본 공고 보기 →
            </a>
          </div>
          <button class="btn-danger btn-sm" @click="deleteCompany(selectedCompany.id)">삭제</button>
        </div>

        <!-- 상세 탭 -->
        <div class="detail-tabs">
          <button :class="{ active: detailTab === 'analysis' }" @click="detailTab = 'analysis'">AI 분석</button>
          <button :class="{ active: detailTab === 'interview' }" @click="detailTab = 'interview'">면접 준비</button>
          <button :class="{ active: detailTab === 'notes' }" @click="detailTab = 'notes'">메모</button>
        </div>

        <!-- AI 분석 탭 -->
        <div v-if="detailTab === 'analysis'" class="tab-content">
          <AnalysisCards
            :analysis="selectedCompany.analysis"
            :readonly="false"
            @edit-section="handleEditSection"
          />
        </div>

        <!-- 면접 준비 탭 -->
        <div v-if="detailTab === 'interview'" class="tab-content interview-tab">
          <p v-if="interviewNotes.length === 0" class="empty-tab-hint">
            AI 분석에서 예상 면접 질문이 생성되면 여기에 표시됩니다.
          </p>
          <div v-for="(note, ni) in interviewNotes" :key="ni" class="interview-item" :class="{ done: note.done }">
            <div class="interview-item-header">
              <span class="interview-q-text">{{ note.question }}</span>
              <label class="done-label">
                <input type="checkbox" v-model="note.done" @change="saveInterviewNotes" />
                준비 완료
              </label>
            </div>
            <div v-if="note.expanded" class="interview-answer-wrap">
              <textarea
                v-model="note.my_answer"
                class="interview-textarea"
                rows="4"
                placeholder="이 질문에 대한 내 답변을 작성하세요..."
                @blur="saveInterviewNotes"
              ></textarea>
            </div>
            <button class="btn-toggle-answer" @click="note.expanded = !note.expanded">
              {{ note.expanded ? '▲ 접기' : '▼ 내 답변 작성' }}
            </button>
          </div>
        </div>

        <!-- 메모 탭 -->
        <div v-if="detailTab === 'notes'" class="tab-content notes-tab">
          <textarea
            v-model="personalNotes"
            class="notes-textarea"
            rows="15"
            maxlength="2000"
            placeholder="이 기업에 대해 자유롭게 메모하세요... (지원 일정, 면접 후기, 개인 생각 등)"
            @blur="savePersonalNotes"
          ></textarea>
          <div class="notes-counter">{{ personalNotes.length }} / 2000자</div>
        </div>
      </div>

      <!-- ④ 초기 빈 상태 -->
      <div v-else class="empty-state">
        <div class="empty-icon">🏢</div>
        <p>채용 공고를 분석하고 기업 정보를 저장해보세요.</p>
        <button class="btn-primary" @click="openAnalyzeForm">공고 분석 시작</button>
      </div>
    </main>

    <!-- 섹션 편집 모달 -->
    <div v-if="editModal.visible" class="modal-overlay" @click.self="editModal.visible = false">
      <div class="modal">
        <h3>{{ editModal.title }} 편집</h3>
        <textarea
          v-model="editModal.value"
          class="modal-textarea"
          :rows="editModal.isText ? 8 : 6"
          :placeholder="editModal.placeholder"
        ></textarea>
        <p v-if="!editModal.isText" class="edit-hint-text">줄바꿈으로 항목을 구분해주세요.</p>
        <div class="modal-actions">
          <button class="btn-outline" @click="editModal.visible = false">취소</button>
          <button class="btn-primary" @click="saveEditSection">저장</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue';
import axios from '@/api/index.js';

const API = '/jobs';

// ─── 인라인 AnalysisCards 컴포넌트 (읽기 + 편집 가능) ────────────────────────

const AnalysisCards = defineComponent({
  name: 'AnalysisCards',
  props: {
    analysis: Object,
    readonly: { type: Boolean, default: false },
  },
  emits: ['editSection'],
  setup(props, { emit }) {
    return () => {
      const a = props.analysis;
      if (!a) return null;

      const editBtn = (section, label) =>
        !props.readonly
          ? h('button', {
              class: 'card-edit-btn',
              onClick: () => emit('editSection', section),
              title: `${label} 편집`,
            }, '✏️')
          : null;

      const card = (title, section, content) =>
        h('div', { class: 'analysis-card' }, [
          h('div', { class: 'card-header' }, [
            h('h3', { class: 'card-title' }, title),
            editBtn(section, title),
          ]),
          h('div', { class: 'card-content' }, content),
        ]);

      const tagList = (items) =>
        h('div', { class: 'tag-group' }, (items || []).map(t => h('span', { class: 'tag-chip' }, t)));

      const bulletList = (items) =>
        h('ul', { class: 'bullet-list' }, (items || []).map(i => h('li', i)));

      return h('div', { class: 'analysis-grid' }, [
        a.overview && card('📋 회사 개요', 'overview', h('p', a.overview)),
        a.tech_stack?.length && card('⚙️ 기술 스택', 'tech_stack', tagList(a.tech_stack)),
        a.requirements?.length && card('✅ 자격 요건', 'requirements', bulletList(a.requirements)),
        a.preferred?.length && card('⭐ 우대 사항', 'preferred', bulletList(a.preferred)),
        a.culture && card('🌱 조직 문화', 'culture', h('p', a.culture)),
        a.interview_questions?.length && card('💬 예상 면접 질문', 'interview_questions', bulletList(a.interview_questions)),
      ].filter(Boolean));
    };
  },
});

// ─── 상태 ────────────────────────────────────────────────────────

const companies = ref([]);
const selectedCompany = ref(null);
const showAnalyzeForm = ref(false);
const analyzing = ref(false);
const analyzeUrl = ref('');
const analyzeText = ref('');
const analysisResult = ref(null);
const analyzeMode = ref('ai'); // 'ai' | 'manual'
const detailTab = ref('analysis'); // 'analysis' | 'interview' | 'notes'

const interviewNotes = ref([]);
const personalNotes = ref('');

const manualForm = ref({ company_name: '', job_title: '', overview: '', requirements_text: '' });
const manualTechInput = ref('');
const manualTechTags = ref([]);

const editModal = ref({
  visible: false,
  section: '',
  title: '',
  value: '',
  placeholder: '',
  isText: true,
});

// ─── 기업 목록 ───────────────────────────────────────────────

async function loadCompanies() {
  const res = await axios.get(API);
  companies.value = res.data;
}

function openAnalyzeForm() {
  selectedCompany.value = null;
  analysisResult.value = null;
  analyzeUrl.value = '';
  analyzeText.value = '';
  analyzeMode.value = 'ai';
  manualForm.value = { company_name: '', job_title: '', overview: '', requirements_text: '' };
  manualTechInput.value = '';
  manualTechTags.value = [];
  showAnalyzeForm.value = true;
}

function selectCompany(c) {
  selectedCompany.value = c;
  showAnalyzeForm.value = false;
  analysisResult.value = null;
  detailTab.value = 'analysis';
  loadInterviewNotes(c);
  personalNotes.value = c.analysis?.personal_notes || '';
}

// ─── AI 분석 ─────────────────────────────────────────────────

async function runAnalysis() {
  if (!analyzeUrl.value.trim() && !analyzeText.value.trim()) {
    alert('URL 또는 텍스트를 입력해주세요.');
    return;
  }
  analyzing.value = true;
  try {
    const res = await axios.post(`${API}/analyze`, {
      url: analyzeUrl.value.trim() || null,
      text: analyzeText.value.trim() || null,
    });
    analysisResult.value = res.data;
    showAnalyzeForm.value = false;
  } catch (e) {
    alert(e.response?.data?.detail || '분석에 실패했습니다.');
  } finally {
    analyzing.value = false;
  }
}

async function saveAnalysis() {
  const a = analysisResult.value.analysis;
  const res = await axios.post(`${API}/save`, {
    company_name: a.company_name || '미확인',
    job_title: a.job_title || null,
    source_url: analyzeUrl.value.trim() || null,
    raw_content: analysisResult.value.raw_content,
    analysis: a,
  });
  companies.value.unshift(res.data);
  selectCompany(res.data);
  analysisResult.value = null;
}

// ─── 직접 입력 ───────────────────────────────────────────────

function addManualTech() {
  const val = manualTechInput.value.trim().replace(/,/g, '');
  if (!val) return;
  if (!manualTechTags.value.includes(val)) manualTechTags.value.push(val);
  manualTechInput.value = '';
}

function removeManualTech(tag) {
  manualTechTags.value = manualTechTags.value.filter(t => t !== tag);
}

async function saveManualEntry() {
  if (!manualForm.value.company_name.trim()) {
    alert('회사명을 입력해주세요.');
    return;
  }
  const analysis = {
    company_name: manualForm.value.company_name.trim(),
    job_title: manualForm.value.job_title.trim(),
    overview: manualForm.value.overview.trim(),
    requirements: manualForm.value.requirements_text
      .split('\n').map(s => s.trim()).filter(Boolean),
    tech_stack: [...manualTechTags.value],
    preferred: [],
    culture: '',
    interview_questions: [],
  };
  const res = await axios.post(`${API}/save`, {
    company_name: analysis.company_name,
    job_title: analysis.job_title || null,
    source_url: null,
    raw_content: null,
    analysis,
  });
  companies.value.unshift(res.data);
  selectCompany(res.data);
  showAnalyzeForm.value = false;
}

// ─── 분석 카드 인라인 편집 ───────────────────────────────────

const SECTION_META = {
  overview:            { title: '회사 개요',   isText: true,  placeholder: '회사 개요를 입력하세요...' },
  culture:             { title: '조직 문화',   isText: true,  placeholder: '조직 문화를 입력하세요...' },
  tech_stack:          { title: '기술 스택',   isText: false, placeholder: 'Python\nVue.js\nFastAPI' },
  requirements:        { title: '자격 요건',   isText: false, placeholder: '경력 3년 이상\nJava 경험' },
  preferred:           { title: '우대 사항',   isText: false, placeholder: '오픈소스 기여 경험\nCI/CD 경험' },
  interview_questions: { title: '예상 면접 질문', isText: false, placeholder: '질문 1\n질문 2\n질문 3' },
};

function handleEditSection(section) {
  const meta = SECTION_META[section];
  if (!meta) return;
  const a = selectedCompany.value.analysis || {};
  let currentValue = '';
  if (meta.isText) {
    currentValue = a[section] || '';
  } else {
    currentValue = (a[section] || []).join('\n');
  }
  editModal.value = {
    visible: true,
    section,
    title: meta.title,
    value: currentValue,
    placeholder: meta.placeholder,
    isText: meta.isText,
  };
}

async function saveEditSection() {
  const { section, value, isText } = editModal.value;
  const newAnalysis = { ...(selectedCompany.value.analysis || {}) };
  if (isText) {
    newAnalysis[section] = value;
  } else {
    newAnalysis[section] = value.split('\n').map(s => s.trim()).filter(Boolean);
  }
  const res = await axios.put(`${API}/${selectedCompany.value.id}`, { analysis: newAnalysis });
  selectedCompany.value = res.data;
  // Update in list
  const idx = companies.value.findIndex(c => c.id === res.data.id);
  if (idx !== -1) companies.value[idx] = res.data;
  // Reload interview notes if questions changed
  if (section === 'interview_questions') loadInterviewNotes(res.data);
  editModal.value.visible = false;
}

// ─── 면접 준비 탭 ────────────────────────────────────────────

function loadInterviewNotes(company) {
  const baseQs = company.analysis?.interview_questions || [];
  const savedNotes = company.analysis?.interview_notes || [];
  interviewNotes.value = baseQs.map(q => {
    const saved = savedNotes.find(n => n.question === q);
    return {
      question: q,
      my_answer: saved?.my_answer || '',
      done: saved?.done || false,
      expanded: false,
    };
  });
}

async function saveInterviewNotes() {
  const notes = interviewNotes.value.map(n => ({
    question: n.question,
    my_answer: n.my_answer,
    done: n.done,
  }));
  const newAnalysis = { ...(selectedCompany.value.analysis || {}), interview_notes: notes };
  await axios.put(`${API}/${selectedCompany.value.id}`, { analysis: newAnalysis });
  selectedCompany.value.analysis = newAnalysis;
}

// ─── 메모 탭 ─────────────────────────────────────────────────

async function savePersonalNotes() {
  const newAnalysis = { ...(selectedCompany.value.analysis || {}), personal_notes: personalNotes.value };
  await axios.put(`${API}/${selectedCompany.value.id}`, { analysis: newAnalysis });
  selectedCompany.value.analysis = newAnalysis;
}

// ─── 삭제 ────────────────────────────────────────────────────

async function deleteCompany(id) {
  if (!confirm('삭제하시겠습니까?')) return;
  await axios.delete(`${API}/${id}`);
  companies.value = companies.value.filter(c => c.id !== id);
  selectedCompany.value = null;
}

onMounted(loadCompanies);
</script>

<style scoped>
.jobs-page {
  display: flex;
  height: 100%;
  background: var(--bg-page);
}

/* 왼쪽 패널 */
.company-panel {
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

.company-list { list-style: none; margin: 0; padding: 8px 0; overflow-y: auto; flex: 1; }
.company-item {
  padding: 10px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}
.company-item:hover { background: #f5f5f5; }
.company-item.active { border-left-color: #F76707; background: #fff5ee; }
.company-name { font-size: 14px; font-weight: 500; color: #333; }
.company-job { font-size: 11px; color: #999; margin-top: 2px; }
.empty-hint { padding: 20px 16px; font-size: 13px; color: #999; }

/* 오른쪽 패널 */
.detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

/* 분석 폼 */
.analyze-form { max-width: 720px; }
.analyze-form h2 { font-size: 20px; font-weight: 700; color: #222; margin-bottom: 20px; }

/* 분석 모드 탭 */
.analyze-mode-tabs {
  display: flex;
  border-bottom: 2px solid #eee;
  margin-bottom: 20px;
}
.analyze-mode-tabs button {
  padding: 10px 20px;
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
.analyze-mode-tabs button.active { color: #F76707; border-bottom-color: #F76707; }

.manual-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: #666; margin-bottom: 6px; font-weight: 500; }
.form-input {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  box-sizing: border-box;
  font-family: inherit;
  resize: vertical;
}
.form-input:focus { outline: none; border-color: #F76707; }

.divider-text { text-align: center; color: #bbb; font-size: 13px; margin: 8px 0; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }

/* 태그 입력 영역 */
.tag-input-area {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  min-height: 44px;
  align-items: center;
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fff5ee;
  color: #F76707;
  border: 1px solid #ffd8b8;
  border-radius: 12px;
  padding: 3px 8px 3px 10px;
  font-size: 12px;
}
.chip-remove {
  background: none;
  border: none;
  color: #F76707;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
  opacity: 0.7;
}
.chip-remove:hover { opacity: 1; }
.chip-input {
  border: none;
  outline: none;
  font-size: 13px;
  min-width: 120px;
  flex: 1;
}

/* 분석 결과 헤더 */
.result-header, .detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.result-header h2, .detail-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #222;
  margin: 0 0 4px;
}
.job-title-text { font-size: 14px; color: #666; margin: 0 0 6px; }
.source-link { font-size: 12px; color: #F76707; text-decoration: none; }
.source-link:hover { text-decoration: underline; }

/* 상세 탭 */
.detail-tabs {
  display: flex;
  border-bottom: 2px solid #eee;
  margin-bottom: 20px;
}
.detail-tabs button {
  padding: 10px 20px;
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
.detail-tabs button.active { color: #F76707; border-bottom-color: #F76707; }

.tab-content { animation: fadeIn 0.15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

/* 분석 카드 그리드 */
:deep(.analysis-grid) {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
:deep(.analysis-card) {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px;
  transition: box-shadow 0.15s;
}
:deep(.analysis-card:hover) { box-shadow: var(--shadow-card); }
:deep(.card-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
:deep(.card-title) {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  margin: 0;
}
:deep(.card-edit-btn) {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.5;
  padding: 2px 4px;
  border-radius: 4px;
  transition: opacity 0.15s;
}
:deep(.card-edit-btn:hover) { opacity: 1; background: #f0f0f0; }
:deep(.card-content p) {
  font-size: 13px;
  color: #555;
  line-height: 1.7;
  margin: 0;
}
:deep(.tag-group) { display: flex; flex-wrap: wrap; gap: 6px; }
:deep(.tag-chip) {
  background: #fff5ee;
  color: #F76707;
  border: 1px solid #ffd8b8;
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 12px;
}
:deep(.bullet-list) { margin: 0; padding-left: 18px; }
:deep(.bullet-list li) {
  font-size: 13px;
  color: #555;
  line-height: 1.7;
  margin-bottom: 4px;
}

/* 면접 준비 탭 */
.interview-tab { display: flex; flex-direction: column; gap: 12px; }

.empty-tab-hint {
  text-align: center;
  color: #bbb;
  font-size: 14px;
  padding: 40px;
}

.interview-item {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  transition: border-color 0.15s;
}
.interview-item.done { border-color: #38a169; }
.interview-item.done .interview-q-text { text-decoration: line-through; color: #999; }

.interview-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 16px;
  gap: 12px;
}

.interview-q-text {
  font-size: 14px;
  color: #333;
  flex: 1;
  line-height: 1.6;
}

.done-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.done-label input { cursor: pointer; accent-color: #38a169; }

.interview-answer-wrap { padding: 0 16px 12px; }

.interview-textarea {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.7;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
  background: #fafafa;
}
.interview-textarea:focus { outline: none; border-color: #F76707; background: #fff; }

.btn-toggle-answer {
  background: none;
  border: none;
  border-top: 1px solid #f0f0f0;
  width: 100%;
  padding: 8px;
  font-size: 12px;
  color: #999;
  cursor: pointer;
  text-align: center;
  transition: background 0.15s;
}
.btn-toggle-answer:hover { background: #fafafa; color: #F76707; }

/* 메모 탭 */
.notes-tab { display: flex; flex-direction: column; gap: 8px; }

.notes-textarea {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
  background: #fff;
}
.notes-textarea:focus { outline: none; border-color: #F76707; }

.notes-counter { text-align: right; font-size: 12px; color: #bbb; }

/* 빈 상태 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60%;
  color: #bbb;
  gap: 16px;
}
.empty-icon { font-size: 48px; }
.empty-state p { font-size: 15px; color: #999; margin: 0; }

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

/* 편집 모달 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}
.modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  min-width: 480px;
  max-width: 640px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.modal h3 { margin: 0 0 16px; font-size: 17px; color: #222; }
.modal-textarea {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
  line-height: 1.7;
}
.modal-textarea:focus { outline: none; border-color: #F76707; }
.edit-hint-text { font-size: 12px; color: #999; margin: 6px 0 0; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
</style>
