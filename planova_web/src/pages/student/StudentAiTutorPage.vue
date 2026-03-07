<template>
  <div class="student-ai-tutor-container">
    <!-- 모바일 사이드바 오버레이 -->
    <div v-if="showSidebar" class="sidebar-overlay" @click="showSidebar = false"></div>

    <!-- 사이드바: 대화 목록 -->
    <div class="sidebar" :class="{ open: showSidebar }">
      <div class="search-bar">
        <div class="search-input-wrapper">
          <i class="search-icon fa-solid fa-magnifying-glass"></i>
          <input
            type="text"
            placeholder="대화 검색하기"
            class="search-input"
            v-model="searchQuery"
          />
        </div>
        <button class="new-chat-btn" @click="startNewChat" title="새 대화"><i class="fa-regular fa-pen-to-square"></i></button>
      </div>

      <div class="history-section">
        <div v-for="(chatGroup, timeGroup) in groupedChatHistory" :key="timeGroup" class="history-group">
          <div v-if="chatGroup.length" class="section-title">{{ getTimeGroupLabel(timeGroup) }}</div>
          <div
            v-for="chat in chatGroup"
            :key="chat.id"
            class="menu-item"
            :class="{ active: currentChatId === chat.id, 'menu-open': activeMenuId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <!-- 이름 편집 중 -->
            <input
              v-if="renamingChatId === chat.id"
              class="rename-input"
              v-model="renameValue"
              @click.stop
              @keydown.enter.stop="confirmRename"
              @keydown.esc.stop="cancelRename"
              @blur="confirmRename"
            />
            <span v-else class="item-text">{{ chat.title || '새 대화' }}</span>

            <!-- 더보기 버튼 -->
            <button
              v-if="renamingChatId !== chat.id"
              class="menu-more-btn"
              @click.stop="toggleMenu(chat.id)"
              title="더보기"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
              </svg>
            </button>

            <!-- 드롭다운 메뉴 -->
            <div v-if="activeMenuId === chat.id" class="context-menu" @click.stop>
              <button @click.stop="startRename(chat)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                이름 변경
              </button>
              <button class="danger" @click.stop="deleteChat(chat.id)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
                  <path d="M9 6V4h6v2"/>
                </svg>
                삭제
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 메인 콘텐츠 -->
    <div class="main-content">
      <!-- 모바일 상단 바 -->
      <div class="mobile-topbar">
        <button class="hamburger-btn" @click="showSidebar = !showSidebar">
          <i class="fa-solid fa-bars"></i>
        </button>
        <span class="mobile-title">AI 튜터</span>
      </div>

      <!-- 빈 화면: 로고 + 퀵 액션 -->
      <template v-if="!currentChat">
        <div class="main-background">
          <div class="logo-wrapper">
            <img src="@/assets/images/planova-small-logo.jpg" alt="플래노바" class="background-logo" />
          </div>
        </div>

        <!-- AI 퀵 액션 -->
        <div class="quick-section">
          <div class="quick-label">AI로 빠르게 시작하기</div>
          <div class="quick-actions">
            <div
              v-for="a in aiActions"
              :key="a.text"
              class="quick-action-card"
              @click="startQuickAction(a)"
            >
              <div class="action-icon"><i :class="a.icon"></i></div>
              <div class="action-text">{{ a.text }}</div>
            </div>
          </div>
        </div>

        <!-- 링크 카드 -->
        <div class="quick-section">
          <div class="quick-label">별도 공간에서 작성하기</div>
          <div class="quick-actions">
            <div
              v-for="a in linkActions"
              :key="a.text"
              class="quick-action-card link-card"
              @click="router.push(a.link)"
            >
              <div class="action-icon"><i :class="a.icon"></i></div>
              <div>
                <div class="action-text">{{ a.text }}</div>
                <div class="action-desc">{{ a.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 채팅 화면 -->
      <div v-if="currentChat" class="chat-container">
        <div class="chat-messages" ref="chatMessagesContainer">
          <div
            v-for="(message, index) in currentChat.messages"
            :key="index"
            class="chat-message"
            :class="{
              'user-message': message.role === 'user',
              'ai-message': message.role === 'assistant'
            }"
          >
            <!-- 버블 -->
            <div class="bubble">
              <!-- 스트리밍 중: plain text / 완료 후: 마크다운 -->
              <span
                v-if="message.role === 'assistant' && !message.streaming"
                class="msg-text markdown-body"
                v-html="renderMarkdown(message.content)"
              ></span>
              <span
                v-else-if="message.role === 'assistant' && message.streaming"
                class="msg-text streaming-text"
              >{{ message.content }}</span>
              <span v-else class="msg-text">{{ message.content }}</span>
            </div>

            <!-- 액션 바 (버블 아래, hover 시 노출) -->
            <div v-if="message.role === 'assistant' && !message.streaming" class="msg-actions">
              <button class="msg-action-btn" @click="copyMessage(message.content)" title="복사">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                <span class="btn-label">복사</span>
              </button>
            </div>
            <div v-if="message.role === 'user'" class="msg-actions">
              <button class="msg-action-btn" @click="resendMessage(message.content)" title="재질문">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="1 4 1 10 7 10"/>
                  <path d="M3.51 15a9 9 0 1 0 .49-3.87L1 10"/>
                </svg>
                <span class="btn-label">재질문</span>
              </button>
            </div>
          </div>
          <div v-if="statusMessage" class="status-message">{{ statusMessage }}</div>
          <div v-if="isLoading" class="loading-indicator">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 입력 영역 -->
      <div class="input-section">
        <!-- 선택된 파일 미리보기 -->
        <div v-if="selectedFile" class="selected-file">
          <div class="file-preview">
            <div class="file-icon"><i class="fa-solid fa-file-pdf"></i></div>
            <div class="file-details">
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
            </div>
          </div>
          <button class="remove-file" @click.stop="removeFile">✕</button>
        </div>

        <!-- 입력 바 -->
        <div class="input-bar">
          <button class="attach-btn" @click="selectFile" title="PDF 첨부">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
            <input
              ref="fileInput"
              type="file"
              accept=".pdf"
              hidden
              @change="handleFileSelect"
            />
          </button>

          <textarea
            v-model="userQuestion"
            class="question-input"
            placeholder="질문을 입력하세요..."
            rows="1"
            @keydown.enter.exact.prevent="sendQuestion"
            ref="questionTextarea"
          ></textarea>

          <button
            class="send-button"
            :class="{ active: userQuestion.trim().length > 0 || selectedFile }"
            :disabled="(userQuestion.trim().length === 0 && !selectedFile) || isLoading"
            @click="sendQuestion"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="send-icon">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 대화 삭제 확인 모달 -->
    <div v-if="showDeleteConfirm" class="file-selector-modal" @click.self="showDeleteConfirm = false">
      <div class="modal-content delete-confirm-modal">
        <p>이 대화를 삭제하시겠습니까?</p>
        <p class="delete-warning">삭제된 대화는 복구할 수 없습니다.</p>
        <div class="modal-actions">
          <button @click="confirmDeleteChat">삭제</button>
          <button @click="showDeleteConfirm = false">취소</button>
        </div>
      </div>
    </div>

    <!-- 파일 선택 모달 -->
    <div v-if="showFileSelector" class="file-selector-modal">
      <div class="modal-content">
        <p>{{ pendingFileRequest?.message }}</p>
        <div v-for="file in pendingFileRequest?.available_files" :key="file.path" class="file-item">
          <input type="checkbox" :value="file.path" v-model="selectedFilePaths" />
          <span>{{ file.folder }} / {{ file.name }}</span>
        </div>
        <div class="modal-actions">
          <button @click="submitFileSelection(selectedFilePaths)">선택</button>
          <button v-if="pendingFileRequest?.optional" @click="submitFileSelection([], true)">건너뛰기</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 모듈 레벨 캐시 — 탭 이동 후 재마운트 시에도 유지
const _cache = { sessions: [], lastFetch: 0, messages: {} }
export default {}
</script>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/index.js'
import { marked } from 'marked'

const router = useRouter()
const authStore = useAuthStore()

// 상태
const chatHistory = ref([])
const currentChatId = ref(null)
const currentChat = ref(null)
const isLoading = ref(false)
const searchQuery = ref('')
const selectedFile = ref(null)
const userQuestion = ref('')
const ws = ref(null)
const sessionId = ref(null)
const pingInterval = ref(null)
const pendingFileRequest = ref(null)
const showFileSelector = ref(false)
const statusMessage = ref('')
const selectedFilePaths = ref([])
const fileInput = ref(null)
const chatMessagesContainer = ref(null)
const questionTextarea = ref(null)
const showDeleteConfirm = ref(false)
const deleteChatId = ref(null)
const showSidebar = ref(false)
// 채팅 목록 컨텍스트 메뉴
const activeMenuId = ref(null)
// 이름 변경
const renamingChatId = ref(null)
const renameValue = ref('')

// 퀵 액션
const aiActions = [
  { icon: 'fa-solid fa-book-open', text: '요약하기', prompt: '이 PDF를 요약해주세요.' },
  { icon: 'fa-solid fa-file-pen', text: '시험 문제 생성', prompt: '이 내용으로 시험 문제를 만들어주세요.' },
]
const linkActions = [
  { icon: 'fa-solid fa-id-card', text: '이력서 작성', desc: '학업/취업 이력서 관리', link: '/student/resume' },
  { icon: 'fa-solid fa-pen-nib', text: '자소서 작성', desc: 'AI 초안 생성 및 편집', link: '/student/coverletter' },
]

// 대화 그룹핑
const groupedChatHistory = computed(() => {
  const groups = { today: [], yesterday: [], lastWeek: [], older: [] }
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
  const lastWeek = new Date(today); lastWeek.setDate(today.getDate() - 7)

  ;[...chatHistory.value]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .forEach(chat => {
      const d = new Date(chat.createdAt)
      if (d >= today) groups.today.push(chat)
      else if (d >= yesterday) groups.yesterday.push(chat)
      else if (d >= lastWeek) groups.lastWeek.push(chat)
      else groups.older.push(chat)
    })

  return groups
})

function getTimeGroupLabel(group) {
  return { today: '오늘', yesterday: '어제', lastWeek: '지난 주', older: '이전' }[group] || '대화'
}

function truncateText(text, len) {
  return text.length > len ? text.substring(0, len) + '...' : text
}

function selectFile() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  if (event.target.files.length > 0) {
    const file = event.target.files[0]
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      selectedFile.value = file
    } else {
      alert('PDF 파일만 업로드 가능합니다.')
      event.target.value = ''
    }
  }
}

function removeFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function formatFileSize(size) {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

function startNewChat() {
  clearInterval(pingInterval.value)
  ws.value?.close()
  ws.value = null
  sessionId.value = null

  const newChatId = `chat_${Date.now()}`
  currentChatId.value = newChatId
  currentChat.value = {
    id: newChatId,
    title: '새 대화',
    messages: [],
    createdAt: new Date().toISOString()
  }
  chatHistory.value.push(currentChat.value)
  // connectWebSocket() 제거 — WS는 sendQuestion() 호출 시 연결
}

function startQuickAction(action) {
  startNewChat()
  userQuestion.value = action.prompt
  sendQuestion()
}

async function loadChat(chatId) {
  const chat = chatHistory.value.find(c => c.id === chatId)
  if (!chat) return

  // 캐시 즉시 표시
  if (_cache.messages[chatId]?.length > 0) {
    chat.messages = _cache.messages[chatId]
    currentChatId.value = chatId
    currentChat.value = chat
    scrollToBottom()
    return
  }

  currentChatId.value = chatId
  currentChat.value = chat

  if (chat.messages.length === 0) {
    try {
      const res = await apiClient.get(`/ws/chat/sessions/${chatId}/history`)
      const msgs = res.data.message_history.map(m => ({
        role: m.type === 'HumanMessage' ? 'user' : 'assistant',
        type: 'text',
        content: m.content,
        timestamp: m.timestamp
      }))
      chat.messages = msgs
      _cache.messages[chatId] = msgs  // 캐시 저장
    } catch {}
  }
  scrollToBottom()
}

// ── 컨텍스트 메뉴 ──────────────────────────────────────────────
function toggleMenu(chatId) {
  activeMenuId.value = activeMenuId.value === chatId ? null : chatId
}

function closeMenu() {
  activeMenuId.value = null
}

function startRename(chat) {
  renameValue.value = chat.title || ''
  renamingChatId.value = chat.id
  activeMenuId.value = null
  nextTick(() => {
    const input = document.querySelector('.rename-input')
    input?.focus()
    input?.select()
  })
}

async function confirmRename() {
  const chatId = renamingChatId.value
  const newTitle = renameValue.value.trim()
  renamingChatId.value = null
  if (!chatId || !newTitle) return
  const chat = chatHistory.value.find(c => c.id === chatId)
  if (chat) chat.title = newTitle
  // 캐시 동기화
  const cached = _cache.sessions.find(s => s.id === chatId)
  if (cached) cached.title = newTitle
  try { await apiClient.patch(`/ws/chat/sessions/${chatId}/title`, { title: newTitle }) } catch {}
}

function cancelRename() {
  renamingChatId.value = null
}

function deleteChat(chatId) {
  deleteChatId.value = chatId
  showDeleteConfirm.value = true
  activeMenuId.value = null
}

async function confirmDeleteChat() {
  const chatId = deleteChatId.value
  showDeleteConfirm.value = false
  deleteChatId.value = null
  try { await apiClient.delete(`/ws/chat/sessions/${chatId}`) } catch {}
  chatHistory.value = chatHistory.value.filter(c => c.id !== chatId)
  // 캐시 동기화
  _cache.sessions = _cache.sessions.filter(s => s.id !== chatId)
  delete _cache.messages[chatId]
  if (currentChatId.value === chatId) {
    currentChatId.value = null
    currentChat.value = null
  }
}

async function sendQuestion() {
  if (!userQuestion.value.trim() && !selectedFile.value) return
  if (!currentChat.value) startNewChat()

  const text = userQuestion.value.trim()
  currentChat.value.messages.push({
    role: 'user', type: 'text', content: text, timestamp: new Date().toISOString()
  })
  userQuestion.value = ''
  isLoading.value = true
  scrollToBottom()

  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({ type: 'user_message', data: { message: text } }))
  } else {
    // 기존 세션 ID 전달 — 재방문 후에도 기존 대화 이어가기
    connectWebSocket(currentChatId.value)
    ws.value.onopen = () => {
      clearInterval(pingInterval.value)
      pingInterval.value = setInterval(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          ws.value.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
      ws.value.send(JSON.stringify({ type: 'user_message', data: { message: text } }))
    }
  }
}

function connectWebSocket(resumeSessionId = null) {
  // CONNECTING 상태면 중복 연결 방지
  if (ws.value?.readyState === WebSocket.CONNECTING) return

  const token = authStore.token
  const userId = authStore.userId
  if (!token || !userId) return

  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const wsBase = baseURL.replace(/^http/, 'ws')
  const sessionParam = resumeSessionId?.startsWith('session:')
    ? `&session_id=${encodeURIComponent(resumeSessionId)}`
    : ''
  ws.value = new WebSocket(`${wsBase}/api/v1/ws/chat/${userId}?token=${token}${sessionParam}`)

  ws.value.onmessage = (event) => handleWSMessage(JSON.parse(event.data))
  ws.value.onclose = () => { clearInterval(pingInterval.value); sessionId.value = null }
  ws.value.onerror = () => { isLoading.value = false; statusMessage.value = '' }
}

function handleWSMessage(msg) {
  sessionId.value = msg.session_id || sessionId.value
  switch (msg.type) {
    case 'session_connected':
      if (currentChat.value && currentChat.value.id !== msg.session_id) {
        const oldId = currentChat.value.id
        const idx = chatHistory.value.findIndex(c => c.id === oldId)
        if (idx !== -1) chatHistory.value[idx].id = msg.session_id
        currentChat.value.id = msg.session_id
        currentChatId.value = msg.session_id
      }
      break

    case 'ai_response':
    case 'result':
      currentChat.value.messages.push({
        role: 'assistant', type: 'text',
        content: msg.data.message,
        timestamp: new Date().toISOString()
      })
      isLoading.value = false
      statusMessage.value = ''
      scrollToBottom()
      syncCurrentChatToHistory()
      break

    case 'stream_start':
      isLoading.value = false
      currentChat.value.messages.push({
        role: 'assistant', type: 'text', content: '', streaming: true,
        timestamp: new Date().toISOString()
      })
      scrollToBottom()
      break

    case 'stream_chunk': {
      const last = currentChat.value.messages.at(-1)
      if (last?.streaming) { last.content += msg.data.chunk; scrollToBottom() }
      break
    }

    case 'stream_end': {
      const last = currentChat.value.messages.at(-1)
      if (last?.streaming) { last.streaming = false; last.content = msg.data.message }
      statusMessage.value = ''
      scrollToBottom()
      syncCurrentChatToHistory()
      break
    }

    case 'status_update':
      statusMessage.value = msg.data.message
      break

    case 'file_request':
      pendingFileRequest.value = msg.data
      showFileSelector.value = true
      isLoading.value = false
      break

    case 'error':
      currentChat.value.messages.push({
        role: 'assistant', type: 'error',
        content: msg.data.message,
        timestamp: new Date().toISOString()
      })
      isLoading.value = false
      statusMessage.value = ''
      break
  }
}

function submitFileSelection(selectedPaths, skip = false) {
  showFileSelector.value = false
  pendingFileRequest.value = null
  isLoading.value = true
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'file_selection',
      data: { selected_files: selectedPaths, skip }
    }))
  }
}

async function loadSessions() {
  const userId = authStore.userId
  if (!userId) return

  // 1) 캐시된 데이터 즉시 표시
  if (_cache.sessions.length > 0) {
    chatHistory.value = _cache.sessions.map(s => ({
      ...s,
      messages: _cache.messages[s.id] || []
    }))
    // 30초 이내 갱신이면 API 생략
    if (Date.now() - _cache.lastFetch < 30000) return
  }

  // 2) 백그라운드 API 갱신
  try {
    const res = await apiClient.get(`/ws/chat/sessions/${userId}`)
    const newSessions = res.data.sessions.map(s => ({
      id: s.session_id,
      title: s.title || '새 대화',
      messages: [],
      createdAt: s.created_at
    }))
    _cache.sessions = newSessions
    _cache.lastFetch = Date.now()

    // 현재 활성 메시지 보존
    chatHistory.value = newSessions.map(s => ({
      ...s,
      messages: (s.id === currentChatId.value && currentChat.value?.messages.length > 0)
        ? currentChat.value.messages
        : (_cache.messages[s.id] || [])
    }))

    // 활성 세션이 없으면 오늘 세션 자동 선택
    if (!currentChatId.value && chatHistory.value.length > 0) {
      const today = new Date()
      const todaySession = chatHistory.value.find(s => {
        const d = new Date(s.createdAt)
        return d.getFullYear() === today.getFullYear() &&
               d.getMonth() === today.getMonth() &&
               d.getDate() === today.getDate()
      })
      if (todaySession) await loadChat(todaySession.id)
    }
  } catch {}
}

function syncCurrentChatToHistory() {
  if (!currentChat.value) return
  if (currentChat.value.title === '새 대화' && currentChat.value.messages.length > 0) {
    const firstUser = currentChat.value.messages.find(m => m.role === 'user')
    if (firstUser) currentChat.value.title = truncateText(firstUser.content, 20)
  }
  // 메시지 캐시 업데이트
  if (currentChatId.value) {
    _cache.messages[currentChatId.value] = [...currentChat.value.messages]
  }
}

async function copyMessage(content) {
  try {
    await navigator.clipboard.writeText(content)
    statusMessage.value = '복사되었습니다.'
    setTimeout(() => {
      if (statusMessage.value === '복사되었습니다.') statusMessage.value = ''
    }, 2000)
  } catch {}
}

function resendMessage(content) {
  userQuestion.value = content
  sendQuestion()
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatMessagesContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

onMounted(() => {
  loadSessions()
  document.addEventListener('click', closeMenu)
})
onBeforeUnmount(() => {
  clearInterval(pingInterval.value)
  ws.value?.close()
  document.removeEventListener('click', closeMenu)
})
watch(currentChat, () => { scrollToBottom() })
</script>

<style scoped>
.student-ai-tutor-container {
  display: flex;
  height: 100vh;
  font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
  background-color: #f8f9fa;
  color: #333;
}

/* ── 사이드바 ── */
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #eaeaea;
  padding: 15px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 15px rgba(0,0,0,0.03);
  z-index: 10;
}

.search-bar {
  display: flex;
  margin-bottom: 20px;
  gap: 8px;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  background: #f5f5f7;
  border-radius: 8px;
  padding: 8px 12px;
}

.search-icon { margin-right: 8px; font-size: 14px; }

.search-input {
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  width: 100%;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: #f5f5f7;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.2s;
}
.new-chat-btn:hover { background: #eaeaea; }

.history-section {
  flex: 1;
  overflow-y: auto;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  margin: 15px 5px 10px;
  color: #666;
}

.menu-item {
  position: relative;
  padding: 9px 10px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}
.menu-item:hover { background: #f5f5f7; }
.menu-item.active { background: #fff1e6; color: #F76707; font-weight: 500; }
.menu-item.menu-open { background: #f5f5f7; }

.item-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* 더보기 버튼 */
.menu-more-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  border-radius: 5px;
  color: #aaa;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}
.menu-item:hover .menu-more-btn,
.menu-item.menu-open .menu-more-btn { opacity: 1; }
.menu-more-btn:hover { background: #e8e8e8; color: #555; }
.menu-item.active .menu-more-btn { color: #F76707; }
.menu-item.active .menu-more-btn:hover { background: rgba(247,103,7,0.12); }

/* 이름 변경 인라인 입력 */
.rename-input {
  flex: 1;
  border: none;
  outline: none;
  background: white;
  border-radius: 5px;
  font-size: 14px;
  font-family: inherit;
  padding: 2px 6px;
  box-shadow: 0 0 0 2px #F76707;
  color: #333;
  min-width: 0;
}

/* 드롭다운 메뉴 */
.context-menu {
  position: absolute;
  right: 4px;
  top: calc(100% + 2px);
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.14);
  overflow: hidden;
  z-index: 200;
  min-width: 130px;
  padding: 4px;
}
.context-menu button {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  border-radius: 7px;
  font-size: 13px;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  color: #333;
  transition: background 0.12s;
}
.context-menu button:hover { background: #f5f5f7; }
.context-menu button.danger { color: #e53935; }
.context-menu button.danger:hover { background: #fff5f5; }

/* ── 메인 콘텐츠 ── */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  padding: 30px;
}

.main-background {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  flex-shrink: 0;
}

.background-logo {
  max-width: 400px;
  opacity: 0.2;
}

/* ── 퀵 섹션 ── */
.quick-section { margin-bottom: 24px; }

.quick-label {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  max-width: 700px;
}

.quick-action-card {
  background: white;
  border-radius: 14px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.quick-action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
  background: #fff8f2;
  border-color: rgba(247,103,7,0.2);
}

.link-card { border: 1px solid #eee; }
.link-card:hover { border-color: #F76707; }

.action-icon { font-size: 24px; flex-shrink: 0; color: #F76707; }
.action-text { font-size: 15px; font-weight: 500; }
.action-desc { font-size: 12px; color: #999; margin-top: 2px; }

/* ── 채팅 ── */
.chat-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 15px;
  padding-bottom: 20px;
}

.chat-message {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-message { align-self: flex-end; align-items: flex-end; }
.ai-message  { align-self: flex-start; align-items: flex-start; }

.bubble {
  padding: 12px 16px;
  border-radius: 18px;
  word-break: break-word;
}

.user-message .bubble { background: #F76707; color: white; }
.ai-message  .bubble  { background: #f0f0f0; color: #333; }

/* ── 메시지 액션 바 ── */
.msg-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
  padding: 0 2px;
}
.chat-message:hover .msg-actions {
  opacity: 1;
  pointer-events: auto;
}

.msg-action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  color: #999;
  font-size: 12px;
  font-family: inherit;
  transition: color 0.15s, background 0.15s;
}
.msg-action-btn:hover {
  color: #444;
  background: #f0f0f0;
}
.msg-action-btn svg { flex-shrink: 0; }
.btn-label { font-size: 12px; color: inherit; }

.user-message .msg-action-btn { color: #aaa; }
.user-message .msg-action-btn:hover { color: #555; background: #f0f0f0; }

.loading-indicator { align-self: flex-start; margin-top: 10px; }

.typing-indicator { display: flex; gap: 4px; }
.typing-indicator span {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #ccc;
  animation: bounce 1.3s linear infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

.status-message {
  align-self: flex-start;
  font-size: 13px;
  color: #888;
  padding: 4px 8px;
  font-style: italic;
}

/* ── 입력 영역 ── */
.input-section {
  flex-shrink: 0;
  margin-top: 16px;
}

.selected-file {
  background: #f5f5f7;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-preview { display: flex; align-items: center; gap: 10px; }
.file-icon { font-size: 18px; color: #F76707; }
.file-name { font-size: 13px; font-weight: 500; }
.file-size { font-size: 11px; color: #888; }

.remove-file {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}
.remove-file:hover { color: #F76707; }

.input-bar {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: white;
  border-radius: 16px;
  padding: 12px 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.attach-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #aaa;
  padding: 4px;
  border-radius: 6px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}
.attach-btn:hover { color: #F76707; background: #fff5ee; }

.question-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  font-family: inherit;
  background: transparent;
  max-height: 120px;
  overflow-y: auto;
}

.send-button {
  background: #ddd;
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}
.send-button.active { background: #F76707; }
.send-button:disabled { opacity: 0.5; cursor: not-allowed; }
.send-button:not(:disabled).active:hover {
  background: #e05500;
  transform: translateY(-1px);
}

.send-icon { width: 18px; height: 18px; fill: white; }

/* ── 파일 선택 모달 ── */
.file-selector-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 28px;
  min-width: 360px;
  max-width: 480px;
  max-height: 70vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.modal-content p {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  color: #333;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 14px;
  color: #444;
  border-bottom: 1px solid #f0f0f0;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-actions button {
  padding: 9px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.modal-actions button:first-child { background: #F76707; color: white; }
.modal-actions button:first-child:hover { background: #e05500; }
.modal-actions button:last-child:not(:first-child) { background: #f5f5f7; color: #555; }
.modal-actions button:last-child:not(:first-child):hover { background: #eaeaea; }

.delete-confirm-modal p:first-child {
  font-size: 17px;
  font-weight: 600;
  color: #222;
  margin-bottom: 6px;
}
.delete-warning {
  font-size: 13px !important;
  color: #999 !important;
  font-weight: 400 !important;
  margin-bottom: 20px !important;
}
.delete-confirm-modal .modal-actions button:first-child {
  background: #e53935;
  color: white;
}
.delete-confirm-modal .modal-actions button:first-child:hover { background: #c62828; }

/* ── 마크다운 렌더링 ── */
.msg-text { display: block; }

/* 스트리밍 중 raw text — 불완전한 마크다운 파싱 방지 */
.streaming-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  font-weight: 700;
  margin: 8px 0 4px;
  line-height: 1.4;
}
.markdown-body :deep(h1) { font-size: 1.3em; }
.markdown-body :deep(h2) { font-size: 1.15em; }
.markdown-body :deep(h3) { font-size: 1.05em; }

.markdown-body :deep(p) { margin: 4px 0; }

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.markdown-body :deep(li) { margin: 2px 0; }

.markdown-body :deep(code) {
  background: rgba(0,0,0,0.07);
  border-radius: 4px;
  padding: 1px 5px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: rgba(0,0,0,0.07);
  border-radius: 8px;
  padding: 10px 14px;
  overflow-x: auto;
  margin: 6px 0;
}
.markdown-body :deep(pre) code { background: none; padding: 0; }

.markdown-body :deep(strong) { font-weight: 700; }
.markdown-body :deep(em) { font-style: italic; }

.markdown-body :deep(blockquote) {
  border-left: 3px solid #ccc;
  margin: 6px 0;
  padding-left: 12px;
  color: #555;
}

/* ── 스크롤바 ── */
.history-section::-webkit-scrollbar,
.chat-messages::-webkit-scrollbar { width: 4px; }
.history-section::-webkit-scrollbar-thumb,
.chat-messages::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

/* ── 모바일 ── */
.mobile-topbar {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: -260px;
    top: 0;
    bottom: 0;
    z-index: 200;
    transition: left 0.3s;
    width: 260px;
    padding-top: 60px;
  }

  .sidebar.open {
    left: 0;
  }

  .sidebar-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 199;
  }

  .mobile-topbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid #eee;
    background: white;
    flex-shrink: 0;
  }

  .hamburger-btn {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #555;
    padding: 4px;
  }

  .mobile-title {
    font-size: 15px;
    font-weight: 600;
    color: #333;
  }

  .main-content {
    padding: 0;
  }

  .main-content > .quick-section,
  .main-content > .main-background {
    padding: 16px;
  }
}
</style>
