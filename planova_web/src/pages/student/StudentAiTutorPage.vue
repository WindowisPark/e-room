<template>
  <div class="student-ai-tutor-container">
    <div class="sidebar">
      <div class="search-bar">
        <div class="search-input-wrapper">
          <i class="search-icon">🔍</i>
          <input 
            type="text" 
            placeholder="대화 검색하기" 
            class="search-input" 
            v-model="searchQuery"
          />
        </div>
        <button class="new-chat-btn" @click="startNewChat">
          <i class="new-chat-icon">✏️</i>
        </button>
      </div>
      
      <div class="history-section">
        <div v-for="(chatGroup, timeGroup) in groupedChatHistory" :key="timeGroup" class="history-group">
          <div class="section-title">{{ getTimeGroupLabel(timeGroup) }}</div>
          <div 
            v-for="chat in chatGroup" 
            :key="chat.id" 
            class="menu-item"
            :class="{ 'active': currentChatId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <span class="item-text">{{ chat.title || '새 대화' }}</span>
            <div class="item-actions">
              <span class="more-options" @click.stop="deleteChat(chat.id)">• • •</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  
    <div class="main-content">
      <div v-if="!currentChat" class="main-background">
        <div class="logo-wrapper">
          <img src="@/assets/images/planova-small-logo.jpg" alt="배경" class="background-logo" />
        </div>
      </div>

      <div v-if="!currentChat" class="quick-actions">
        <div 
          v-for="action in quickActions" 
          :key="action.text" 
          class="quick-action-card"
          @click="startQuickAction(action)"
        >
          <div class="action-icon">{{ action.icon }}</div>
          <div class="action-text">{{ action.text }}</div>
        </div>
      </div>
      
      <div v-if="currentChat" class="chat-container">
        <div class="chat-inner">
          <!-- 대화가 시작되었지만 메시지가 없을 때도 배경 로고 표시 -->
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
              {{ message.content }}
            </div>
            <div v-if="statusMessage" class="status-message">{{ statusMessage }}</div>
            <div v-if="isLoading" class="loading-indicator">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
  
      <div class="input-section">
        <div class="file-upload-section">    
          <div 
            class="upload-area" 
            @click="selectFile" 
            @dragover.prevent 
            @drop.prevent="handleFileDrop"
          >
            <input 
              ref="fileInput" 
              type="file" 
              class="file-input" 
              @change="handleFileSelect" 
              accept=".pdf" 
              hidden 
            />
          </div>
          
          <div v-if="selectedFile" class="selected-file">
            <div class="file-preview">
              <div class="file-icon">📄</div>
              <div class="file-details">
                <div class="file-name">{{ selectedFile.name }}</div>
                <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
              </div>
            </div>
            <button class="remove-file" @click.stop="removeFile">✕</button>
          </div>
          
          <div class="question-input-area">
            <textarea 
              v-model="userQuestion" 
              class="question-input" 
              placeholder="질문을 입력하세요..."
              :rows="questionRows"
              @input="adjustTextareaHeight"
              @keydown.enter.exact.prevent="sendQuestion"
              ref="questionTextarea"
            ></textarea>
          </div>
          
          <div class="upload-actions">
            <div class="action-buttons">
              <button 
                class="send-button" 
                :class="{ active: userQuestion.trim().length > 0 || selectedFile }" 
                :disabled="(userQuestion.trim().length === 0 && !selectedFile) || isLoading"
                @click="sendQuestion"
              >
                <span class="send-text">보내기</span>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="send-icon">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </div>
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
  import { useAuthStore } from '@/stores/auth'
  import apiClient from '@/api/index.js'

  export default {
    name: 'StudentAiTutorPage',
    data() {
      return {
        // AI 대화 관련 상태
        chatHistory: [],
        currentChatId: null,
        currentChat: null,
        isLoading: false,

        // 검색 및 필터링
        searchQuery: '',

        // 입력 관련 상태
        selectedFile: null,
        userQuestion: '',
        questionRows: 1,
        minRows: 1,
        maxRows: 5,

        // WebSocket 관련 상태
        ws: null,
        sessionId: null,
        pingInterval: null,
        pendingFileRequest: null,
        showFileSelector: false,
        statusMessage: '',
        selectedFilePaths: [],

        // 퀵 액션
        quickActions: [
          { icon: '📚', text: '요약하기' },
          { icon: '📝', text: '시험 문제 생성' },
          { icon: '📄', text: '이력서 피드백' },
          { icon: '✍️', text: '자소서 첨삭' },
        ],
      }
    },
    computed: {
      groupedChatHistory() {
        const groupedChats = {
          today: [],
          yesterday: [],
          lastWeek: [],
          older: []
        };
        
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);
        
        this.chatHistory
          .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
          .forEach(chat => {
            const chatDate = new Date(chat.createdAt);
            
            if (chatDate >= today) {
              groupedChats.today.push(chat);
            } else if (chatDate >= yesterday) {
              groupedChats.yesterday.push(chat);
            } else if (chatDate >= lastWeek) {
              groupedChats.lastWeek.push(chat);
            } else {
              groupedChats.older.push(chat);
            }
          });
        
        return groupedChats;
      }
    },
    methods: {
      getTimeGroupLabel(timeGroup) {
        switch(timeGroup) {
          case 'today': return '오늘';
          case 'yesterday': return '어제';
          case 'lastWeek': return '지난 주';
          case 'older': return '이전';
          default: return '대화';
        }
      },
      
      truncateText(text, length) {
        return text.length > length 
          ? text.substring(0, length) + '...' 
          : text;
      },
      
      selectFile() {
        this.$refs.fileInput.click();
      },
      
      handleFileSelect(event) {
        if (event.target.files.length > 0) {
          const file = event.target.files[0];
          
          if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
            this.selectedFile = file;
          } else {
            alert('PDF 파일만 업로드 가능합니다.');
            this.$refs.fileInput.value = '';
          }
        }
      },
      
      handleFileDrop(event) {
        event.preventDefault();
        if (event.dataTransfer.files.length > 0) {
          const file = event.dataTransfer.files[0];
  
          if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
            this.selectedFile = file;
          } else {
            alert('PDF 파일만 업로드 가능합니다.');
          }
        }
      },
      
      removeFile() {
        this.selectedFile = null;
        this.$refs.fileInput.value = '';
      },
      
      formatFileSize(size) {
        if (size < 1024) {
          return size + ' B';
        } else if (size < 1024 * 1024) {
          return (size / 1024).toFixed(1) + ' KB';
        } else {
          return (size / (1024 * 1024)).toFixed(1) + ' MB';
        }
      },
      
      adjustTextareaHeight() {
        // 자동 높이 조정 비활성화
      },
      
      startNewChat() {
        clearInterval(this.pingInterval)
        if (this.ws) {
          this.ws.close()
          this.ws = null
        }
        this.sessionId = null

        const newChatId = `chat_${Date.now()}`;
        this.currentChatId = newChatId;
        this.currentChat = {
          id: newChatId,
          title: '새 대화',
          messages: [],
          createdAt: new Date().toISOString()
        };
        this.chatHistory.push(this.currentChat);
        this.connectWebSocket();
      },
      
      startQuickAction(action) {
        this.startNewChat();
        this.userQuestion = `${action.text}에 대해 도와주세요.`;
        this.sendQuestion();
      },
      
      async loadChat(chatId) {
        const chat = this.chatHistory.find(c => c.id === chatId)
        if (!chat) return
        if (chat.messages.length === 0) {
          try {
            const res = await apiClient.get(`/ws/chat/sessions/${chatId}/history`)
            chat.messages = res.data.message_history.map(m => ({
              role: m.type === 'HumanMessage' ? 'user' : 'assistant',
              type: 'text',
              content: m.content,
              timestamp: m.timestamp
            }))
          } catch (e) { /* 로드 실패 시 빈 메시지 */ }
        }
        this.currentChatId = chatId
        this.currentChat = chat
        this.scrollToBottom()
      },
      
      // 삭제 기능: 채팅 삭제
      async deleteChat(chatId) {
        if (confirm('이 대화를 삭제하시겠습니까?')) {
          try {
            await apiClient.delete(`/ws/chat/sessions/${chatId}`)
          } catch (e) { /* API 삭제 실패해도 로컬에서는 제거 */ }
          this.chatHistory = this.chatHistory.filter(chat => chat.id !== chatId);
          if (this.currentChatId === chatId) {
            this.currentChatId = null;
            this.currentChat = null;
          }
        }
      },
      
      async sendQuestion() {
        if (!this.userQuestion.trim() && !this.selectedFile) return
        if (!this.currentChat) this.startNewChat()

        const text = this.userQuestion.trim()
        this.currentChat.messages.push({
          role: 'user',
          type: 'text',
          content: text,
          timestamp: new Date().toISOString()
        })
        this.userQuestion = ''
        this.isLoading = true
        this.scrollToBottom()

        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'user_message', data: { message: text } }))
        } else {
          this.connectWebSocket()
          this.ws.onopen = () => {
            this.ws.send(JSON.stringify({ type: 'user_message', data: { message: text } }))
          }
        }
      },
      
      connectWebSocket() {
        const authStore = useAuthStore()
        const token = authStore.token
        const userId = authStore.userId
        if (!token || !userId) return

        const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const wsBase = baseURL.replace(/^http/, 'ws')
        this.ws = new WebSocket(`${wsBase}/api/v1/ws/chat/${userId}?token=${token}`)

        this.ws.onopen = () => {
          this.pingInterval = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify({ type: 'ping' }))
            }
          }, 30000)
        }
        this.ws.onmessage = (event) => this.handleWSMessage(JSON.parse(event.data))
        this.ws.onclose = () => { clearInterval(this.pingInterval); this.sessionId = null }
        this.ws.onerror = () => { this.isLoading = false; this.statusMessage = '' }
      },

      handleWSMessage(msg) {
        this.sessionId = msg.session_id || this.sessionId
        switch (msg.type) {
          case 'session_connected':
            // 백엔드 세션 ID를 로컬 임시 ID에 동기화 (삭제/이력 API 정상화)
            if (this.currentChat && this.currentChat.id !== msg.session_id) {
              const oldId = this.currentChat.id
              const idx = this.chatHistory.findIndex(c => c.id === oldId)
              if (idx !== -1) this.chatHistory[idx].id = msg.session_id
              this.currentChat.id = msg.session_id
              this.currentChatId = msg.session_id
            }
            break
          case 'ai_response':
          case 'result':
            this.currentChat.messages.push({
              role: 'assistant',
              type: 'text',
              content: msg.data.message,
              timestamp: new Date().toISOString()
            })
            this.isLoading = false
            this.statusMessage = ''
            this.scrollToBottom()
            this.syncCurrentChatToHistory()
            break
          case 'status_update':
            this.statusMessage = msg.data.message
            break
          case 'file_request':
            this.pendingFileRequest = msg.data
            this.showFileSelector = true
            this.isLoading = false
            break
          case 'error':
            this.currentChat.messages.push({
              role: 'assistant',
              type: 'error',
              content: msg.data.message,
              timestamp: new Date().toISOString()
            })
            this.isLoading = false
            this.statusMessage = ''
            break
        }
      },

      submitFileSelection(selectedPaths, skip = false) {
        this.showFileSelector = false
        this.pendingFileRequest = null
        this.isLoading = true
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 'file_selection',
            data: { selected_files: selectedPaths, skip }
          }))
        }
      },

      async loadSessions() {
        const authStore = useAuthStore()
        const userId = authStore.userId
        if (!userId) return
        try {
          const res = await apiClient.get(`/ws/chat/sessions/${userId}`)
          this.chatHistory = res.data.sessions.map(s => ({
            id: s.session_id,
            title: s.title || '새 대화',
            messages: [],
            createdAt: s.created_at
          }))
        } catch (e) { /* 실패 시 빈 목록 */ }
      },

      syncCurrentChatToHistory() {
        if (!this.currentChat) return
        if (this.currentChat.title === '새 대화' && this.currentChat.messages.length > 0) {
          const firstUserMsg = this.currentChat.messages.find(m => m.role === 'user')
          if (firstUserMsg) {
            this.currentChat.title = this.truncateText(firstUserMsg.content, 20)
          }
        }
      },

      scrollToBottom() {
        this.$nextTick(() => {
          const container = this.$refs.chatMessagesContainer;
          if (container) {
            container.scrollTop = container.scrollHeight;
          }
        });
      }
    },
    mounted() {
      this.loadSessions()
      // connectWebSocket()은 startNewChat() / sendQuestion()에서 필요 시 호출

      this.$nextTick(() => {
        if (this.$refs.questionTextarea) {
          this.adjustTextareaHeight();
        }
      });
    },
    beforeUnmount() {
      clearInterval(this.pingInterval)
      this.ws?.close()
    },
    watch: {
      currentChat() {
        this.scrollToBottom();
      }
    }
  }
  </script>
  
  <style scoped>
.main-background {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  z-index: 0;
  background-color: #f8f9fa;
  height: 420px;
}
.logo-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}

  .student-ai-tutor-container {
    display: flex;
    height: 100vh;
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background-color: #f8f9fa;
    color: #333;
  }
  
  .sidebar {
    width: 260px;
    background-color: white;
    border-right: 1px solid #eaeaea;
    padding: 15px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.03);
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
    background-color: #f5f5f7;
    border-radius: 8px;
    padding: 8px 12px;
  }
  
  .search-icon {
    margin-right: 8px;
    font-size: 14px;
  }
  
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
    background-color: #f5f5f7;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .new-chat-btn:hover {
    background-color: #eaeaea;
  }
  
  .history-section {
    flex: 1;
    overflow-y: auto;
    margin-bottom: 15px;
  }
  
  .section-title {
    font-size: 13px;
    font-weight: 600;
    margin: 15px 5px 10px;
    color: #666;
  }
  
  .menu-item {
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 14px;
    color: #333;
    cursor: pointer;
    margin-bottom: 2px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s;
  }
  
  .menu-item:hover {
    background-color: #f5f5f7;
  }
  
  .menu-item.active {
    background-color: #fff1e6;
    color: #f1883c;
    font-weight: 500;
  }
  
  .item-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .item-actions {
    display: flex;
    align-items: center;
  }
  
  .more-options {
    color: #999;
    font-size: 12px;
    padding: 0 5px;
  }
  
  /* 메인 콘텐츠 스타일링 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden auto;
  padding: 30px;
}
  
  .greeting-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30px;
  }
  
  .greeting-text h1 {
    font-size: 26px;
    color: #f1883c;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
  }
  
  .wave-emoji {
    display: inline-block;
    margin-left: 8px;
    animation: wave 1.5s infinite;
    transform-origin: 70% 70%;
  }
  
  @keyframes wave {
    0% { transform: rotate(0deg); }
    10% { transform: rotate(14deg); }
    20% { transform: rotate(-8deg); }
    30% { transform: rotate(14deg); }
    40% { transform: rotate(-4deg); }
    50% { transform: rotate(10deg); }
    60% { transform: rotate(0deg); }
    100% { transform: rotate(0deg); }
  }
  
  .greeting-text h2 {
    font-size: 28px;
    color: #f1883c;
    font-weight: 500;
  }
  
  .illustration-img {
    width: 140px;
    height: 140px;
  }
  
  /* 2x2 퀵 액션 버튼 스타일링 */
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr); /* 2x2 그리드 설정 */
    gap: 20px;
    margin-bottom: 40px;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .quick-action-card {
    background-color: white;
    border-radius: 16px;
    padding: 25px;
    display: flex;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transition: all 0.2s;
    cursor: pointer;
    height: 80px;
    width: 400px;
  }
  
  .quick-action-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    background-color: #fff8f2;
    border: 1px solid rgba(241, 136, 60, 0.2);
  }
  
  .action-icon {
    font-size: 36px;
    margin-right: 20px;
  }
  
.action-text {
    font-size: 18px;
    font-weight: 500;
}

  .chat-container {
     flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  }

  .chat-inner {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 100%;
    z-index: 1;
  }

  .chat-background {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f8f9fa;
    z-index: 2;
    pointer-events: none;
    min-height: 300px;
  }

  .chat-messages {
    position: relative;
    z-index: 3;
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
    padding: 12px 16px;
    border-radius: 18px;
    word-break: break-word;
  }
  
  .user-message {
    align-self: flex-end;
    background-color: #f1883c;
    color: white;
  }
  
  .ai-message {
    align-self: flex-start;
    background-color: #f0f0f0;
    color: #333;
  }
  
  .loading-indicator {
    align-self: flex-start;
    margin-top: 10px;
  }
  
  .typing-indicator {
    display: flex;
    gap: 4px;
  }
  
  .typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #ccc;
    display: inline-block;
    animation: bounce 1.3s linear infinite;
  }
  
  .typing-indicator span:nth-child(2) {
    animation-delay: 0.15s;
  }
  
  .typing-indicator span:nth-child(3) {
    animation-delay: 0.3s;
  }
  
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
  }
  
  /* 질문 입력 영역 */
.input-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
  justify-content: flex-end;
  min-height: 100px;
  margin-top: 0;
}
  
  .question-input-area {
    margin: 15px 0;
  }
  
  .question-input {
    width: 100%;
    border: none;
    outline: none;
    resize: vertical;
    font-size: 15px;
    line-height: 1.5;
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    padding: 12px;
    border-radius: 8px;
    transition: all 0.2s;
    background-color: #f9f9f9;
    height: 80px;
  }
  
  .question-input:focus {
    background-color: #f5f5f5;
    box-shadow: 0 0 0 2px rgba(241, 136, 60, 0.2);
  }
  
  /* 파일 업로드 섹션 */
  .file-upload-section {
    background-color: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  }
  
  .upload-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .upload-instructions {
    font-size: 16px;
    color: #333;
    font-weight: 500;
  }
  
  .supported-formats {
    font-size: 12px;
    color: #888;
  }
  
  
  .upload-button {
    background-color: #f5f5f7;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    color: #333;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .upload-button:hover {
    background-color: #eaeaea;
  }
  
  .selected-file {
    background-color: #f5f5f7;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .file-preview {
    display: flex;
    align-items: center;
  }
  
  .file-icon {
    font-size: 20px;
    margin-right: 12px;
  }
  
  .file-name {
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .file-size {
    font-size: 12px;
    color: #888;
  }
  
  .remove-file {
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
  }
  
  .remove-file:hover {
    color: #f1883c;
  }
  
  .upload-actions {
    display: flex;
    justify-content: flex-end;
  }
  
  .action-buttons {
    display: flex;
    gap: 10px;
  }
  
  .send-button {
    display: flex;
    align-items: center;
    background-color: #f1883c;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    opacity: 0.7;
  }
  
  .send-button.active {
    opacity: 1;
  }
  
  .send-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(241, 136, 60, 0.3);
  }
  
  .send-button:disabled {
    background-color: #ddd;
    cursor: not-allowed;
    opacity: 0.7;
    transform: none;
    box-shadow: none;
  }
  
  .send-text {
    margin-right: 8px;
  }
  
  .send-icon {
    width: 16px;
    height: 16px;
    fill: currentColor;
  }
  
  /* 스크롤바 스타일 */
  .history-section::-webkit-scrollbar {
    width: 6px;
  }
  
  .history-section::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .history-section::-webkit-scrollbar-thumb {
    background-color: #ddd;
    border-radius: 3px;
  }
  
  .history-section::-webkit-scrollbar-thumb:hover {
    background-color: #ccc;
  }
  
  .main-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .main-content::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .main-content::-webkit-scrollbar-thumb {
    background-color: #ddd;
    border-radius: 3px;
  }
  
  .main-content::-webkit-scrollbar-thumb:hover {
    background-color: #ccc;
  }
  
  /* 반응형 디자인 */
  @media (max-width: 768px) {
    .student-ai-tutor-container {
      flex-direction: column;
    }
    
    .sidebar {
      width: 100%;
      height: auto;
      max-height: 40vh;
    }
    
    .greeting-header {
      flex-direction: column;
      text-align: center;
    }
    
    .greeting-illustration {
      display: none;
    }
    
    .quick-actions {
      grid-template-columns: repeat(2, 1fr); /* 모바일에서도 2x2 유지 */
      gap: 15px;
      max-width: 100%;
    }
    
    .quick-action-card {
      padding: 18px;
      height: 90px;
      width: auto;
    }
    
    .action-icon {
      font-size: 28px;
    }
    
    .action-text {
      font-size: 16px;
    }
  }

.chat-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  z-index: 0;
  background-color: #f8f9fa;
  min-height: 300px;
}

.background-logo {
    max-width: 500px;
    opacity: 0.2;
}

.status-message {
  align-self: flex-start;
  font-size: 13px;
  color: #888;
  padding: 4px 8px;
  font-style: italic;
}

.file-selector-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
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
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
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

.file-item input[type="checkbox"] {
  cursor: pointer;
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

.modal-actions button:first-child {
  background-color: #f1883c;
  color: white;
}

.modal-actions button:first-child:hover {
  background-color: #e07020;
}

.modal-actions button:last-child:not(:first-child) {
  background-color: #f5f5f7;
  color: #555;
}

.modal-actions button:last-child:not(:first-child):hover {
  background-color: #eaeaea;
}

</style>