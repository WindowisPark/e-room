<!-- CommonModal.vue - 재사용 가능한 모달 컴포넌트 -->
<template>
    <div class="folder-modal" v-if="show">
      <div class="modal-content" :class="modalClass">
        <h3 class="modal-title">{{ title }}</h3>
        
        <!-- 모달 유형별 내용 -->
        <!-- 추가 옵션 선택 모달 -->
        <div v-if="type === 'options'" class="option-buttons">
          <button @click="$emit('file-upload')" class="option-button">
            <div class="option-icon file-option">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="18" x2="12" y2="12"></line>
                <line x1="9" y1="15" x2="15" y2="15"></line>
              </svg>
            </div>
            <div class="option-text">
              <span class="option-title">파일 업로드</span>
              <span class="option-desc">PDF 파일을 업로드합니다</span>
            </div>
          </button>
          <button @click="$emit('folder-create')" class="option-button">
            <div class="option-icon folder-option">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                <line x1="12" y1="11" x2="12" y2="17"></line>
                <line x1="9" y1="14" x2="15" y2="14"></line>
              </svg>
            </div>
            <div class="option-text">
              <span class="option-title">폴더 생성</span>
              <span class="option-desc">새 폴더를 만듭니다</span>
            </div>
          </button>
        </div>
        
        <!-- 폴더 생성 모달 -->
        <div v-if="type === 'folder-create'" class="folder-input-container">
          <div class="folder-icon-preview">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFC107" stroke="#FFA000" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <input 
            type="text" 
            v-model="inputValue" 
            placeholder="폴더 이름을 입력하세요"
            class="folder-input"
            @keyup.enter="$emit('submit', inputValue)"
          />
        </div>
        
        <!-- 파일 업로드 모달 -->
        <div v-if="type === 'file-upload'" class="file-upload-area" :class="{ 'has-file': selectedFile }">
          <label class="file-upload-label">
            <input 
              type="file" 
              class="file-input" 
              accept=".pdf" 
              ref="fileInput"
              @change="onFileSelected"
            />
            <div class="upload-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <div class="upload-text">
              <span class="upload-title">파일을 선택하세요</span>
              <span class="upload-desc">PDF 파일만 가능합니다</span>
            </div>
          </label>
          <div class="selected-file" v-if="selectedFile">
            {{ selectedFile.name }}
          </div>
        </div>
        
        <!-- 이름 변경 모달 -->
        <div v-if="type === 'rename'" class="folder-input-container">
          <div class="folder-icon-preview">
            <svg v-if="itemType === 'folder'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFC107" stroke="#FFA000" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ECEFF1" stroke="#607D8B" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <path d="M14 2v6h6"></path>
            </svg>
          </div>
          <input 
            type="text" 
            v-model="inputValue" 
            placeholder="새 이름을 입력하세요"
            class="folder-input"
            @keyup.enter="$emit('submit', inputValue)"
          />
        </div>
        
        <!-- 이동 모달 -->
        <div v-if="type === 'move'" class="folder-tree-container">
          <div class="folder-tree-item root" @click="$emit('select-target', null)">
            <div class="folder-tree-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </div>
            <div class="folder-tree-name" :class="{ 'selected': targetFolderId === null }">
              홈
            </div>
          </div>
          <div 
            v-for="folder in allFolders" 
            :key="folder.id"
            class="folder-tree-item"
            :style="{ marginLeft: getFolderIndent(folder) + 'px' }"
            @click="$emit('select-target', folder.id)"
          >
            <div class="folder-tree-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFC107" stroke="#FFA000" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" width="18" height="18">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="folder-tree-name" :class="{ 'selected': targetFolderId === folder.id, 'disabled': isInvalidMoveTarget(folder.id) }">
              {{ folder.name }}
            </div>
          </div>
        </div>
        
        <!-- 모달 버튼 영역 -->
        <div class="modal-buttons">
          <button @click="$emit('cancel')" class="cancel-button">취소</button>
          <button 
            @click="$emit('submit', type === 'file-upload' ? selectedFile : inputValue)" 
            class="create-button" 
            :disabled="!isValid"
          >
            <span>{{ actionButtonText }}</span>
          </button>
        </div>
        
        <!-- 닫기 버튼 -->
        <button @click="$emit('cancel')" class="close-modal-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'CommonModal',
    props: {
      show: {
        type: Boolean,
        required: true
      },
      type: {
        type: String,
        required: true,
        validator: (value) => ['options', 'folder-create', 'file-upload', 'rename', 'move'].includes(value)
      },
      title: {
        type: String,
        required: true
      },
      initialValue: {
        type: String,
        default: ''
      },
      itemType: {
        type: String,
        default: 'folder'
      },
      allFolders: {
        type: Array,
        default: () => []
      },
      targetFolderId: {
        type: String,
        default: null
      },
      selectedItemId: {
        type: String,
        default: null
      }
    },
    
    data() {
      return {
        inputValue: this.initialValue,
        selectedFile: null
      };
    },
    
    watch: {
      initialValue(newValue) {
        this.inputValue = newValue;
      },
      show(newValue) {
        if (!newValue) {
          // 모달이 닫힐 때 초기화
          this.selectedFile = null;
          this.inputValue = this.initialValue;
        }
      }
    },
    
    computed: {
      modalClass() {
        return `${this.type}-modal`;
      },
      
      actionButtonText() {
        switch (this.type) {
          case 'folder-create': return '생성';
          case 'file-upload': return '업로드';
          case 'rename': return '변경';
          case 'move': return '이동';
          default: return '확인';
        }
      },
      
      isValid() {
        if (this.type === 'folder-create' || this.type === 'rename') {
          return this.inputValue && this.inputValue.trim() !== '';
        } else if (this.type === 'file-upload') {
          return !!this.selectedFile;
        } else if (this.type === 'move') {
          return this.isValidMoveOperation();
        }
        return true;
      }
    },
    
    methods: {
      onFileSelected(event) {
        const files = event.target.files;
        if (files.length > 0) {
          this.selectedFile = files[0];
        }
      },
      
      getFolderIndent(folder) {
        let level = 0;
        let currentFolder = folder;
        
        while (currentFolder.parentId !== null) {
          level++;
          const parentFolder = this.allFolders.find(f => f.id === currentFolder.parentId);
          if (!parentFolder) break;
          currentFolder = parentFolder;
        }
        
        return level * 20;
      },
      
      isInvalidMoveTarget(targetId) {
        // 자기 자신으로 이동 불가
        if (targetId === this.selectedItemId) return true;
        
        // 폴더의 경우, 자신의 하위 폴더로 이동 불가 (순환 참조 방지)
        if (this.itemType === 'folder') {
          let currentFolderId = targetId;
          while (currentFolderId !== null) {
            const parentFolder = this.allFolders.find(f => f.id === currentFolderId);
            if (!parentFolder) break;
            
            if (parentFolder.parentId === this.selectedItemId) return true;
            currentFolderId = parentFolder.parentId;
          }
        }
        
        return false;
      },
      
      isValidMoveOperation() {
        // 현재 위치와 동일한 위치로 이동하는 경우 비활성화
        const currentItem = this.itemType === 'folder' 
          ? this.allFolders.find(f => f.id === this.selectedItemId)
          : null; // 파일의 경우 부모폴더 정보를 직접 확인해야 함
        
        if (currentItem && currentItem.parentId === this.targetFolderId) return false;
        
        // 순환 참조 검사
        if (this.isInvalidMoveTarget(this.targetFolderId)) return false;
        
        return true;
      }
    }
  };
  </script>
  
  <style scoped>
  .folder-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal-content {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    width: 90%;
    max-width: 400px;
    position: relative;
  }
  
  .modal-title {
    text-align: center;
    font-size: 22px;
    margin-bottom: 25px;
    color: #333;
    font-weight: 600;
  }
  
  .close-modal-button {
    position: absolute;
    top: 15px;
    right: 15px;
    background: none;
    border: none;
    cursor: pointer;
    color: #999;
    padding: 5px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.2s;
  }
  
  .close-modal-button:hover {
    background-color: #f5f5f5;
    color: #333;
  }
  
  .modal-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 20px;
  }
  
  .cancel-button, .create-button {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 15px;
    font-weight: 500;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  
  .cancel-button {
    background-color: #f5f5f5;
    color: #666;
  }
  
  .cancel-button:hover {
    background-color: #e8e8e8;
    color: #333;
  }
  
  .create-button {
    background-color: #4d90fe;
    color: white;
    box-shadow: 0 2px 5px rgba(77, 144, 254, 0.2);
  }
  
  .create-button:hover {
    background-color: #3a7be0;
    box-shadow: 0 4px 8px rgba(77, 144, 254, 0.3);
    transform: translateY(-1px);
  }
  
  .create-button:disabled {
    background-color: #a0c3ff;
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
  }
  
  /* 추가 옵션 선택 모달 스타일 */
  .options-modal {
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  }
  
  .options-title {
    font-size: 22px;
    margin-bottom: 25px;
  }
  
  .option-buttons {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin: 15px 0;
  }
  
  .option-button {
    display: flex;
    align-items: center;
    padding: 16px;
    border: none;
    border-radius: 12px;
    background-color: #ffffff;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
    cursor: pointer;
    font-size: 16px;
    text-align: left;
    transition: all 0.3s ease;
    border: 1px solid #f0f0f0;
  }
  
  .option-button:hover {
    background-color: #f8f9ff;
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
  }
  
  .option-icon {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    margin-right: 16px;
  }
  
  .file-option {
    background-color: #e3f2fd;
    color: #1976d2;
  }
  
  .folder-option {
    background-color: #fff8e1;
    color: #ffb300;
  }
  
  .option-icon svg {
    width: 24px;
    height: 24px;
  }
  
  .option-text {
    display: flex;
    flex-direction: column;
  }
  
  .option-title {
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 4px;
    color: #333;
  }
  
  .option-desc {
    font-size: 13px;
    color: #666;
  }
  
  /* 폴더 생성 및 이름 변경 모달 스타일 */
  .folder-input-container {
    display: flex;
    align-items: center;
    margin: 25px 0 30px;
    background-color: #f8f9ff;
    border-radius: 12px;
    padding: 5px;
    border: 1px solid #e0e0e0;
  }
  
  .folder-icon-preview {
    width: 40px;
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 10px;
  }
  
  .folder-input {
    flex: 1;
    padding: 12px;
    border: none;
    background: transparent;
    font-size: 16px;
    outline: none;
  }
  
  .folder-input::placeholder {
    color: #aaa;
  }
  
  /* 파일 업로드 모달 스타일 */
  .file-upload-area {
    margin: 20px 0 30px;
    border: 2px dashed #ddd;
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    transition: all 0.3s ease;
  }
  
  .file-upload-area:hover {
    border-color: #4d90fe;
    background-color: #f8f9ff;
  }
  
  .file-upload-area.has-file {
    border-color: #4caf50;
    background-color: #f1f8e9;
  }
  
  .file-input {
    display: none;
  }
  
  .file-upload-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .upload-icon {
    width: 60px;
    height: 60px;
    margin-bottom: 15px;
    color: #4d90fe;
  }
  
  .file-upload-area.has-file .upload-icon {
    color: #4caf50;
  }
  
  .upload-text {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .upload-title {
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 6px;
    color: #333;
  }
  
  .upload-desc {
    font-size: 14px;
    color: #666;
  }
  
  .selected-file {
    margin-top: 10px;
    font-size: 14px;
    color: #4caf50;
    font-weight: 500;
    word-break: break-all;
    max-width: 280px;
  }
  
  /* 이동 모달 스타일 */
  .folder-tree-container {
    max-height: 300px;
    overflow-y: auto;
    margin: 20px 0;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px;
    background-color: #f9f9f9;
  }
  
  .folder-tree-item {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
  }
  
  .folder-tree-item:hover {
    background-color: #f0f0f0;
  }
  
  .folder-tree-icon {
    margin-right: 8px;
    display: flex;
    align-items: center;
  }
  
  .folder-tree-name {
    font-size: 14px;
    color: #333;
  }
  
  .folder-tree-name.selected {
    font-weight: 600;
    color: #1976d2;
  }
  
  .folder-tree-name.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .folder-tree-item.root {
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 8px;
    padding-bottom: 10px;
  }
  </style>