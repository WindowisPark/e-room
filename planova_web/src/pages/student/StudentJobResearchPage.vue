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

    <!-- 오른쪽: 분석 결과 / 빈 상태 -->
    <main class="detail-panel">
      <!-- 분석 폼 -->
      <div v-if="showAnalyzeForm" class="analyze-form">
        <h2>채용 공고 분석</h2>
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
      </div>

      <!-- 분석 결과 미리보기 (저장 전) -->
      <div v-else-if="analysisResult" class="analysis-result">
        <div class="result-header">
          <div>
            <h2>{{ analysisResult.analysis.company_name || '회사명 미확인' }}</h2>
            <p class="job-title-text">{{ analysisResult.analysis.job_title || '' }}</p>
          </div>
          <button class="btn-primary" @click="saveAnalysis">저장하기</button>
        </div>
        <AnalysisCards :analysis="analysisResult.analysis" />
      </div>

      <!-- 저장된 기업 상세 -->
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
        <AnalysisCards v-if="selectedCompany.analysis" :analysis="selectedCompany.analysis" />
      </div>

      <!-- 초기 빈 상태 -->
      <div v-else class="empty-state">
        <div class="empty-icon">🏢</div>
        <p>채용 공고를 분석하고 기업 정보를 저장해보세요.</p>
        <button class="btn-primary" @click="openAnalyzeForm">공고 분석 시작</button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, defineComponent, h } from 'vue';
import axios from 'axios';

const API = '/api/v1/jobs';

const companies = ref([]);
const selectedCompany = ref(null);
const showAnalyzeForm = ref(false);
const analyzing = ref(false);
const analyzeUrl = ref('');
const analyzeText = ref('');
const analysisResult = ref(null);

// ─── 인라인 AnalysisCards 컴포넌트 ──────────────────────────────────────────
const AnalysisCards = defineComponent({
  props: { analysis: Object },
  setup(props) {
    return () => {
      const a = props.analysis;
      if (!a) return null;

      const card = (title, content) => h('div', { class: 'analysis-card' }, [
        h('h3', { class: 'card-title' }, title),
        h('div', { class: 'card-content' }, content)
      ]);

      const tagList = (items) => (items || []).map(t => h('span', { class: 'tag-chip' }, t));
      const bulletList = (items) => h('ul', { class: 'bullet-list' },
        (items || []).map(i => h('li', i))
      );

      return h('div', { class: 'analysis-grid' }, [
        a.overview && card('📋 회사 개요', h('p', a.overview)),
        a.tech_stack?.length && card('⚙️ 기술 스택', h('div', { class: 'tag-group' }, tagList(a.tech_stack))),
        a.requirements?.length && card('✅ 자격 요건', bulletList(a.requirements)),
        a.preferred?.length && card('⭐ 우대 사항', bulletList(a.preferred)),
        a.culture && card('🌱 조직 문화', h('p', a.culture)),
        a.interview_questions?.length && card('💬 예상 면접 질문', bulletList(a.interview_questions)),
      ].filter(Boolean));
    };
  }
});

async function loadCompanies() {
  const res = await axios.get(API);
  companies.value = res.data;
}

function openAnalyzeForm() {
  selectedCompany.value = null;
  analysisResult.value = null;
  analyzeUrl.value = '';
  analyzeText.value = '';
  showAnalyzeForm.value = true;
}

function selectCompany(c) {
  selectedCompany.value = c;
  showAnalyzeForm.value = false;
  analysisResult.value = null;
}

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
  selectedCompany.value = res.data;
  analysisResult.value = null;
}

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
  background: #f8f9fa;
}

/* 왼쪽 패널 */
.company-panel {
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
.analyze-form { max-width: 680px; }
.analyze-form h2 { font-size: 20px; font-weight: 700; color: #222; margin-bottom: 24px; }

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

/* 분석 결과 / 상세 */
.result-header, .detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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

/* 분석 카드 그리드 */
:deep(.analysis-grid) {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

:deep(.analysis-card) {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 16px;
}

:deep(.card-title) {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  margin: 0 0 10px;
}

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

:deep(.bullet-list) {
  margin: 0;
  padding-left: 18px;
}
:deep(.bullet-list li) {
  font-size: 13px;
  color: #555;
  line-height: 1.7;
  margin-bottom: 4px;
}

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
</style>
