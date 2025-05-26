<template>
  <div class="pdf-viewer-container">
    <div class="pdf-header">
      <button class="back-button" @click="goBack">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>뒤로 가기</span>
      </button>
      <h2 class="pdf-title">{{ pdfName }}</h2>
      
      
      <div class="pdf-controls">
        <button class="control-button" @click="zoomIn">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="11" y1="8" x2="11" y2="14"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </button>
        <button class="control-button" @click="zoomOut">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            <line x1="8" y1="11" x2="14" y2="11"></line>
          </svg>
        </button>
        <div class="page-controls">
          <button class="control-button" @click="prevPage" :disabled="currentPage <= 1">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button class="control-button" @click="nextPage" :disabled="currentPage >= totalPages">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
        <button class="note-button" @click="toggleNotePanel">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
          <span>메모</span>
        </button>
        <button class="control-button" @click="clearHighlights">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          <span class="sr-only">하이라이트 초기화</span>
        </button>
      </div>
    </div>

    <div class="content-container">
      <div class="pdf-container" ref="pdfContainer">
        <div class="loading-indicator" v-if="loading">
          <svg class="spinner" width="40" height="40" viewBox="0 0 50 50">
            <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
          </svg>
          <span>PDF 로딩 중...</span>
        </div>
        <div class="pdf-page-container">
          <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
          <div ref="textLayer" class="textLayer"></div>
          <div class="annotation-layer">
            <div 
              v-for="(note, index) in scaledNotes" 
              :key="index" 
              class="note-marker"
              :style="{left: note.scaledX + 'px', top: note.scaledY + 'px'}"
              @click="openNote(note)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#FFD700" stroke="#333" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15.5 3H5a2 2 0 0 0-2 2v14c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z"></path>
                <path d="M15 3v6h6"></path>
              </svg>
            </div>
          </div>
          <div class="highlight-layer" ref="highlightLayer">
            <div
              v-for="(box, index) in currentPageHighlights"
              :key="index"
              class="highlight-box"
              :style="{
                top: box.top * highlightLayerHeight + 'px',
                left: box.left * highlightLayerWidth + 'px',
                width: box.width * highlightLayerWidth + 'px',
                height: box.height * highlightLayerHeight + 'px'
              }"
            />
          </div>
          <div
            v-if="isHighlighting"
            class="highlight-box-temp"
            :style="highlightBoxStyle"
          ></div>
        </div>
      </div>

      <div class="note-panel" :class="{ 'open': showNotePanel }">
        <div class="note-panel-header">
          <h3>메모 목록</h3>
          <button class="close-button" @click="toggleNotePanel">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div class="note-list">
          <div v-if="currentPageNotes.length === 0" class="no-notes">
            이 페이지에 메모가 없습니다. <hr>PDF 위에서 더블클릭하여 메모를 추가하세요.
          </div>
          <div 
            v-for="(note, index) in currentPageNotes" 
            :key="index" 
            class="note-item"
            @click="openNote(note)"
          >
            <div class="note-content">{{ note.content.length > 50 ? note.content.substring(0, 50) + '...' : note.content }}</div>
            <div class="note-actions">
              <button class="delete-button" @click.stop="deleteNote(note.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"></path>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        <button class="add-note-button" @click="showAddNoteTooltip">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>메모 추가 방법</span>
        </button>
      </div>
    </div>

    <!-- 메모 모달 -->
    <div class="modal" v-if="showNoteModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingNote ? '메모 편집' : '새 메모 추가' }}</h3>
          <button class="close-button" @click="closeNoteModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <textarea 
            v-model="noteContent" 
            placeholder="메모 내용을 입력하세요..." 
            class="note-textarea"
          ></textarea>
        </div>
        <div class="modal-footer">
          <button class="cancel-button" @click="closeNoteModal">취소</button>
          <button class="save-button" @click="saveNote">저장</button>
        </div>
      </div>
    </div>

    <!-- 메모 추가 툴팁 -->
    <div class="tooltip" v-if="showAddNoteHelp">
      <div class="tooltip-content">
        <p>PDF 위에서 더블클릭하여 원하는 위치에 메모를 추가할 수 있습니다.</p>
        <button class="tooltip-close" @click="showAddNoteHelp = false">확인</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed, onBeforeUnmount, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import IndexedDBService from '@/util/IndexedDBService.js';

export default {
  name: 'PdfViewer',

  setup() {
    // Highlight variables
    const highlightLayer = ref(null);
    let startX = 0;
    let startY = 0;
    let currentHighlight = null;
    // --- Highlighting reactive state for temp box ---
    const isHighlighting = ref(false);
    const highlightBoxStyle = ref({
      top: '0px',
      left: '0px',
      width: '0px',
      height: '0px'
    });
    // Persisted highlights (per page)
    const savedHighlights = ref({});
    // Persist savedHighlights to localStorage on update
    watch(savedHighlights, (newVal) => {
      const fileId = route.params.fileId;
      localStorage.setItem(`pdfHighlights_${fileId}`, JSON.stringify(newVal));
    }, { deep: true });

    // Computed for current page highlights
    const currentPageHighlights = computed(() => {
      return savedHighlights.value[currentPage.value] || [];
    });

    // Highlight layer dimensions for relative/absolute conversion (ref-based)
    const highlightLayerWidth = ref(1);
    const highlightLayerHeight = ref(1);

    const updateHighlightLayerSize = () => {
      nextTick(() => {
        if (highlightLayer.value) {
          highlightLayerWidth.value = highlightLayer.value.offsetWidth;
          highlightLayerHeight.value = highlightLayer.value.offsetHeight;
        }
      });
    };
    const router = useRouter();
    const route = useRoute();

    const pdfContainer = ref(null);
    const pdfCanvas = ref(null);
    const textLayer = ref(null);
    const pdfName = ref('');
    const currentPage = ref(1);
    const totalPages = ref(0);
    const loading = ref(true);
    const scale = ref(1.0);
    
    // 메모 관련 상태
    const showNotePanel = ref(false);
    const showNoteModal = ref(false);
    const showAddNoteHelp = ref(false);
    const notes = ref([]);
    const noteContent = ref('');
    const editingNote = ref(null);
    const newNotePosition = ref({ x: 0, y: 0 });

    // 텍스트 색상 관련 상태 추가
    const textColor = ref('#000000');
    const isTransparent = ref(true);

    let pdfDoc = null;
    let pageRendering = false;
    let pageNumPending = null;
    let pdfjsLib = window.pdfjsLib;

    // 현재 페이지의 메모만 필터링
    const currentPageNotes = computed(() => {
      return notes.value.filter(note => note.page === currentPage.value);
    });

    // 스케일에 맞춰 조정된 메모 위치 계산
    const scaledNotes = computed(() => {
      return currentPageNotes.value.map(note => ({
        ...note,
        scaledX: note.x * scale.value,
        scaledY: note.y * scale.value
      }));
    });

    // PDF.js 워커 설정
    const setupPdfJs = () => {
      if (!pdfjsLib) {
        console.error('PDF.js 라이브러리가 로드되지 않았습니다.');
        return false;
      }

      // 워커 URL 설정
      pdfjsLib.GlobalWorkerOptions.workerSrc = 
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
      
      return true;
    };

    const goBack = () => {
      router.push('/student/pdf');
    };

    const renderPage = (pageNum) => {
      pageRendering = true;
      loading.value = true;

      pdfDoc.getPage(pageNum).then(function(page) {
        const viewport = page.getViewport({ scale: scale.value });
        const canvas = pdfCanvas.value;

        const dpr = window.devicePixelRatio || 1;

        // 캔버스 크기를 DPR 기준으로 설정
        canvas.width = viewport.width * dpr;
        canvas.height = viewport.height * dpr;
        canvas.style.width = viewport.width + 'px';
        canvas.style.height = viewport.height + 'px';

        const canvasContext = canvas.getContext('2d');
        canvasContext.setTransform(dpr, 0, 0, dpr, 0, 0);  // DPI 적용

        const renderContext = {
          canvasContext: canvasContext,
          viewport: viewport
        };

        
        const renderTask = page.render(renderContext);
        const textLayerDiv = textLayer.value;
        
        // 텍스트 내용 가져오기
        page.getTextContent().then(function(textContent) {
          // 텍스트 레이어 초기화
          textLayerDiv.innerHTML = '';
          
          // 텍스트 레이어 뷰포트 설정
          textLayerDiv.style.left = canvas.offsetLeft + 'px';
          textLayerDiv.style.top = canvas.offsetTop + 'px';
          textLayerDiv.style.height = canvas.height + 'px';
          textLayerDiv.style.width = canvas.width + 'px';
          
          // 텍스트 레이어 렌더링
          textContent.items.forEach(function(textItem) {
            const tx = pdfjsLib.Util.transform(
              viewport.transform,
              textItem.transform
            );
            
            const fontHeight = Math.sqrt((tx[2] * tx[2]) + (tx[3] * tx[3]));
            const angle = Math.atan2(tx[1], tx[0]);
            
            const textDiv = document.createElement('span');
            textDiv.textContent = textItem.str;
            
            // 스타일 적용
            const style = textDiv.style;
            style.left = tx[4] + 'px';
            style.top = (tx[5] - fontHeight) + 'px';
            style.fontSize = fontHeight + 'px';
            style.fontFamily = textItem.fontName;
            style.transform = 'rotate(' + angle + 'rad)';
            style.position = 'absolute';
            
            // 텍스트 색상 적용
            style.color = isTransparent.value ? 'transparent' : textColor.value;
            style.cursor = 'text';
            style.whiteSpace = 'pre';
            
            textLayerDiv.appendChild(textDiv);
          });
        });
        
        renderTask.promise.then(function() {
          pageRendering = false;
          loading.value = false;
          // --- Ensure highlightLayer is refreshed after rendering ---
          nextTick(() => {
            highlightLayer.value = pdfContainer.value.querySelector('.highlight-layer');
            updateHighlightLayerSize();
            console.log('📏 highlightLayer dimensions (forced refresh):', highlightLayer.value?.clientWidth, highlightLayer.value?.clientHeight);
          });
          if (pageNumPending !== null) {
            renderPage(pageNumPending);
            pageNumPending = null;
          }
        });
      });

      currentPage.value = pageNum;
    };

    const queueRenderPage = (pageNum) => {
      if (pageRendering) {
        pageNumPending = pageNum;
      } else {
        renderPage(pageNum);
      }
    };

    const prevPage = () => {
      if (currentPage.value <= 1) return;
      queueRenderPage(currentPage.value - 1);
    };

    const nextPage = () => {
      if (currentPage.value >= totalPages.value) return;
      queueRenderPage(currentPage.value + 1);
    };

    const zoomIn = () => {
      scale.value += 0.2;
      queueRenderPage(currentPage.value);
    };

    const zoomOut = () => {
      if (scale.value > 0.4) {
        scale.value -= 0.2;
        queueRenderPage(currentPage.value);
      }
    };

    // PDF 로딩 함수
    const loadPDF = async (fileId) => {
      console.log('📄 PDF 로딩 시작:', fileId);
      
      if (!setupPdfJs()) {
        alert('PDF.js 라이브러리를 로드할 수 없습니다.');
        return;
      }

      loading.value = true;

      try {
        // IndexedDB에서 파일 정보 가져오기
        const fileInfo = await IndexedDBService.getFile(fileId);
        console.log('📄 fileInfo:', fileInfo ? '로드 성공' : '로드 실패');

        if (!fileInfo) {
          alert('📁 파일을 찾을 수 없습니다. IndexedDB에서 파일 정보를 가져올 수 없습니다.');
          loading.value = false;
          return;
        }

        pdfName.value = fileInfo.name;
        loadNotes(fileId);

        // Load saved highlights from localStorage
        const savedBoxes = localStorage.getItem(`pdfHighlights_${fileId}`);
        if (savedBoxes) {
          savedHighlights.value = JSON.parse(savedBoxes);
          console.log('📦 하이라이트 불러오기 완료:', savedHighlights.value);
        } else {
          savedHighlights.value = {};
        }

        // Base64 데이터 처리ㅌ
        let uint8Array;
        
        if (fileInfo.content.startsWith('data:')) {
          const base64Data = fileInfo.content.split(',')[1];
          const binary = atob(base64Data);
          const len = binary.length;
          uint8Array = new Uint8Array(len);
          
          for (let i = 0; i < len; i++) {
            uint8Array[i] = binary.charCodeAt(i);
          }
        } else {
          const binary = atob(fileInfo.content);
          const len = binary.length;
          uint8Array = new Uint8Array(len);
          
          for (let i = 0; i < len; i++) {
            uint8Array[i] = binary.charCodeAt(i);
          }
        }

        // PDF.js로 PDF 문서 로드
        const loadingTask = pdfjsLib.getDocument({ data: uint8Array });
        
        loadingTask.promise.then(function (pdfDocument) {
          console.log('✅ PDF 문서 로드 성공');
          pdfDoc = pdfDocument;
          totalPages.value = pdfDocument.numPages;
          renderPage(1);
        }, function (error) {
          console.error('❌ PDF 로딩 에러:', error);
          alert('PDF를 표시할 수 없습니다: ' + error.message);
          loading.value = false;
        });
        
      } catch (err) {
        console.error('❌ PDF 로딩 에러:', err);
        alert('PDF를 표시할 수 없습니다: ' + err.message);
        loading.value = false;
      }
    };

    // 메모 패널 토글
    const toggleNotePanel = () => {
      showNotePanel.value = !showNotePanel.value;
    };

    // 메모 불러오기
    const loadNotes = (fileId) => {
      const savedNotes = localStorage.getItem(`pdfNotes_${fileId}`);
      if (savedNotes) {
        notes.value = JSON.parse(savedNotes);
      } else {
        notes.value = [];
      }
    };

    // 메모 저장하기
    const saveNotes = () => {
      const fileId = route.params.fileId;
      localStorage.setItem(`pdfNotes_${fileId}`, JSON.stringify(notes.value));
    };

    // 새 메모 추가 모달 열기
    const openAddNoteModal = (x, y) => {
      editingNote.value = null;
      noteContent.value = '';
      newNotePosition.value = { x, y };
      showNoteModal.value = true;
    };

    // 메모 편집 모달 열기
    const openNote = (note) => {
      editingNote.value = note;
      noteContent.value = note.content;
      showNoteModal.value = true;
    };

    // 메모 모달 닫기
    const closeNoteModal = () => {
      showNoteModal.value = false;
      editingNote.value = null;
      noteContent.value = '';
    };

    // 메모 저장
    const saveNote = () => {
      if (noteContent.value.trim() === '') {
        alert('메모 내용을 입력해주세요.');
        return;
      }

      if (editingNote.value) {
        // 기존 메모 편집
        const index = notes.value.findIndex(n => n.id === editingNote.value.id);
        if (index !== -1) {
          notes.value[index].content = noteContent.value;
        }
      } else {
        // 새 메모 추가 - 상대적 좌표로 저장
        const newNote = {
          id: Date.now().toString(),
          page: currentPage.value,
          x: newNotePosition.value.x, // 이미 상대 좌표
          y: newNotePosition.value.y, // 이미 상대 좌표
          content: noteContent.value,
          createdAt: new Date().toISOString()
        };
        notes.value.push(newNote);
      }

      saveNotes();
      closeNoteModal();
    };

    // 메모 삭제
    const deleteNote = (noteId) => {
      if (confirm('이 메모를 삭제하시겠습니까?')) {
        notes.value = notes.value.filter(note => note.id !== noteId);
        saveNotes();
      }
    };

    // 메모 추가 도움말 표시
    const showAddNoteTooltip = () => {
      showAddNoteHelp.value = true;
    };

    // 더블클릭 이벤트 리스너 (메모 추가) - 수정됨
    const handleDoubleClick = (event) => {
      const container = pdfCanvas.value;
      if (!container) return;
      
      const rect = container.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      // 현재 스케일을 고려하여 상대적 좌표로 변환
      const relativeX = x / scale.value;
      const relativeY = y / scale.value;
      
      openAddNoteModal(relativeX, relativeY);
    };

    // 텍스트 색상 업데이트 함수
    const updateTextColor = () => {
      const textLayerDiv = textLayer.value;
      if (!textLayerDiv) return;

      const spans = textLayerDiv.querySelectorAll('span');
      spans.forEach(span => {
        span.style.color = isTransparent.value ? 'transparent' : textColor.value;
      });
    };

    // 투명 모드 토글 함수
    const toggleTransparent = () => {
      isTransparent.value = !isTransparent.value;
      updateTextColor();
    };

    // --- Highlighting methods ---
    const onMouseDown = (e) => {
      const rect = highlightLayer.value.getBoundingClientRect();
      // Removed scrollLeft/scrollTop adjustment
      const scrollLeft = 0;
      const scrollTop = 0;
      startX = e.clientX - rect.left + scrollLeft;
      startY = e.clientY - rect.top + scrollTop;

      isHighlighting.value = true;
      highlightBoxStyle.value = {
        top: `${startY}px`,
        left: `${startX}px`,
        width: '0px',
        height: '0px'
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    };

    const onMouseMove = (e) => {
      const rect = highlightLayer.value.getBoundingClientRect();
      // Removed scrollLeft/scrollTop adjustment
      const scrollLeft = 0;
      const scrollTop = 0;
      const x = e.clientX - rect.left + scrollLeft;
      const y = e.clientY - rect.top + scrollTop;

      const left = Math.min(x, startX);
      const top = Math.min(y, startY);
      const width = Math.abs(x - startX);
      const height = Math.abs(y - startY);

      highlightBoxStyle.value = {
        top: `${top}px`,
        left: `${left}px`,
        width: `${width}px`,
        height: `${height}px`
      };
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);

      const container = highlightLayer.value;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const top = parseFloat(highlightBoxStyle.value.top);
      const left = parseFloat(highlightBoxStyle.value.left);
      const width = parseFloat(highlightBoxStyle.value.width);
      const height = parseFloat(highlightBoxStyle.value.height);

      isHighlighting.value = false;
      highlightBoxStyle.value = {
        top: '0px',
        left: '0px',
        width: '0px',
        height: '0px'
      };

      if (width > 0 && height > 0) {
        const relativeBox = {
          top: top / rect.height,
          left: left / rect.width,
          width: width / rect.width,
          height: height / rect.height
        };
        const page = currentPage.value;
        if (!savedHighlights.value[page]) {
          savedHighlights.value[page] = [];
        }
        savedHighlights.value[page].push(relativeBox);
        console.log('✅ 저장된 박스 좌표:', relativeBox);
      }
    };

    onMounted(() => {
      // PDF.js 라이브러리가 로드됐는지 확인
      if (!window.pdfjsLib) {
        // PDF.js 라이브러리를 동적으로 로드
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js';
        script.onload = () => {
          pdfjsLib = window.pdfjsLib;
          const fileId = route.params.fileId;
          loadPDF(fileId);
        };
        script.onerror = () => {
          alert('PDF.js 라이브러리를 로드할 수 없습니다.');
          loading.value = false;
        };
        document.head.appendChild(script);
      } else {
        pdfjsLib = window.pdfjsLib;
        const fileId = route.params.fileId;
        loadPDF(fileId);
      }

      // 더블클릭 이벤트 리스너 등록
      const pdfContainerEl = pdfContainer.value;
      if (pdfContainerEl) {
        pdfContainerEl.addEventListener('dblclick', handleDoubleClick);
      }

      // Highlight layer ref and event binding
      highlightLayer.value = pdfContainer.value.querySelector('.highlight-layer');
      if (highlightLayer.value) {
        highlightLayer.value.addEventListener('mousedown', onMouseDown);
        updateHighlightLayerSize();
      }
    });

    watch(() => route.params.fileId, (newId) => {
      if (newId && pdfjsLib) {
        loadPDF(newId);
      }
    });

    // Watch for scale changes to update the highlight layer size
    watch(scale, () => {
      updateHighlightLayerSize();
    });
    
    onBeforeUnmount(() => {
      // 메모리 정리
      pdfDoc = null;

      // 이벤트 리스너 제거
      const pdfContainerEl = pdfContainer.value;
      if (pdfContainerEl) {
        pdfContainerEl.removeEventListener('dblclick', handleDoubleClick);
      }
    });


    // 하이라이트 초기화 함수 (현재 페이지만)
    const clearHighlights = () => {
      const page = currentPage.value;
      if (savedHighlights.value[page]) {
        savedHighlights.value[page] = [];
      }
      const fileId = route.params.fileId;
      localStorage.setItem(`pdfHighlights_${fileId}`, JSON.stringify(savedHighlights.value));
      alert(`✅ 현재 페이지의 박스가 삭제되었습니다.`);
    };

    return {
      pdfContainer,
      pdfCanvas,
      textLayer,
      pdfName,
      currentPage,
      totalPages,
      loading,
      showNotePanel,
      showNoteModal,
      showAddNoteHelp,
      currentPageNotes,
      scaledNotes, // 추가된 computed 속성
      noteContent,
      editingNote,
      goBack,
      prevPage,
      nextPage,
      zoomIn,
      zoomOut,
      toggleNotePanel,
      openNote,
      closeNoteModal,
      saveNote,
      deleteNote,
      showAddNoteTooltip,
      // 새로 추가된 속성들
      textColor,
      isTransparent,
      updateTextColor,
      toggleTransparent,
      highlightLayer,
      isHighlighting,
      highlightBoxStyle,
      savedHighlights, // <-- ensure this is returned so it's reactive in template
      currentPageHighlights,
      highlightLayerWidth,
      highlightLayerHeight,
      clearHighlights
    };
  }
};
</script>

<style scoped>
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.pdf-header {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 10;
  gap: 15px;
}

.back-button {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: #333;
  cursor: pointer;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.back-button svg {
  margin-right: 8px;
}

.back-button:hover {
  background-color: #f0f0f0;
}

.pdf-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  text-align: center;
  color: #333;
  padding: 0 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 텍스트 색상 컨트롤 스타일 추가 */

.pdf-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-button {
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #555;
}

.control-button:hover {
  background-color: #f0f0f0;
  color: #333;
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 10px;
}

.page-info {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  min-width: 60px;
  text-align: center;
}

.content-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.pdf-container {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  position: relative;
  padding: 20px;
}

.pdf-page-container {
  position: relative;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  background-color: white;
}

.pdf-canvas {
  position: relative;
  z-index: 1;
}

.textLayer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  opacity: 0.2;
  line-height: 1.0;
  z-index: 2;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
}

.textLayer > span {
  position: absolute;
  white-space: pre;
  cursor: text;
  transform-origin: 0% 0%;
}


.loading-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #666;
}

/* 메모 버튼 스타일 */
.note-button {
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #4d90fe;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-left: 10px;
}

.note-button:hover {
  background-color: #3a78de;
}

/* 메모 패널 스타일 */
.note-panel {
  width: 320px;
  background-color: white;
  position: absolute;
  right: -320px;
  top: 0;
  bottom: 0;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 5;
}

.note-panel.open {
  right: 0;
}

.note-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.note-panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  padding: 4px;
  border-radius: 4px;
}

.close-button:hover {
  background-color: #f0f0f0;
  color: #333;
}

.note-list {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.no-notes {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 20px 0;
  line-height: 1.5;
}

.note-item {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.note-item:hover {
  background-color: #f0f0f0;
}

.note-content {
  font-size: 14px;
  color: #333;
  margin-bottom: 5px;
  line-height: 1.4;
}

.note-actions {
  display: flex;
  justify-content: flex-end;
}

.delete-button {
  background: none;
  border: none;
  color: #ff5252;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.delete-button:hover {
  background-color: #ffebee;
}

.add-note-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: #f1f8ff;
  border: 1px dashed #4d90fe;
  color: #4d90fe;
  width: calc(100% - 30px);
  margin: 15px;
  padding: 10px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.add-note-button:hover {
  background-color: #e3f2fd;
}

/* 메모 마커 스타일 */
.annotation-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
  pointer-events: none;
}

.note-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
  pointer-events: all;
  z-index: 3;
}

.note-marker:hover {
  transform: translate(-50%, -50%) scale(1.1);
}

/* 메모 모달 스타일 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.note-textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

.note-textarea:focus {
  outline: none;
  border-color: #4d90fe;
  box-shadow: 0 0 0 2px rgba(77, 144, 254, 0.2);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  border-top: 1px solid #eee;
}

.cancel-button {
  background-color: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-button:hover {
  background-color: #e0e0e0;
}

.save-button {
  background-color: #4d90fe;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-button:hover {
  background-color: #3a78de;
}

/* 툴팁 스타일 */
.tooltip {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.tooltip-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 20px;
  width: 90%;
  max-width: 400px;
  text-align: center;
}

.tooltip-close {
  background-color: #4d90fe;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 15px;
}

.tooltip-close:hover {
  background-color: #3a78de;
}

.highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  pointer-events: auto; /* changed from none to auto */
}

.highlight-box {
  position: absolute;
  background-color: rgba(135, 206, 250, 0.2);
  border: 1px solid rgba(135, 206, 250, 0.6);
  z-index: 11;
  pointer-events: none;
}

.highlight-box-temp {
  position: absolute;
  border: 2px solid #4d90fe;
  background-color: rgba(77, 144, 254, 0.2);
  z-index: 5;
  pointer-events: auto;
}

</style>