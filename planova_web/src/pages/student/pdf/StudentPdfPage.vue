<template>
  <div class="student-pdf-container">
    <!-- 파일 관리자 컴포넌트 -->
    <FileManager
      :activeTab="activeTab"
      :teamFolders="teamFolders"
      :teamFiles="teamFiles"
      :selectedTeam="selectedTeam"
      :currentPath="currentPath"
      :breadcrumbs="breadcrumbs"
      :viewMode="viewMode"
      :selectMode="selectMode"
      :selectedItems="selectedItems"
      @update:activeTab="activeTab = $event"
      @toggle-view="toggleViewMode"
      @toggle-select="toggleSelectMode"
      @toggle-options="toggleOptionsMenu"
      @navigate-back="navigateBack"
      @navigate-home="navigateHome"
      @navigate-to-breadcrumb="navigateToBreadcrumb"
      @add-item="handleAddClick"
      @open-folder="openFolder"
      @open-file="openFile"
      @update:selectedItems="selectedItems = $event"
      @update:selectedTeam="selectedTeam = $event"
      @handle-rename="handleRename"
      @handle-move="handleMoveItem"
      @handle-delete="handleDelete"
    />
    
    <!-- 공통 모달 컴포넌트들 -->
    <CommonModal
      v-if="showAddOptions"
      show
      type="options"
      title="추가하기"
      @cancel="showAddOptions = false"
      @file-upload="handleFileUpload"
      @folder-create="handleAddFolder"
    />
    
    <CommonModal
      v-if="showFolderModal"
      show
      type="folder-create"
      title="새 폴더 만들기"
      :initialValue="newFolderName"
      @cancel="cancelAddFolder"
      @submit="createFolder"
    />
    
    <CommonModal
      v-if="showFileUploadModal"
      show
      type="file-upload"
      title="파일 업로드"
      @cancel="cancelFileUpload"
      @submit="uploadFile"
    />
    
    <CommonModal
      v-if="showRenameModal"
      show
      type="rename"
      title="이름 변경"
      :initialValue="newItemName"
      :itemType="selectedItemType"
      @cancel="cancelRename"
      @submit="confirmRename"
    />
    
    <CommonModal
      v-if="showMoveModal"
      show
      type="move"
      :title="selectedItemType === 'folder' ? '폴더 이동' : '파일 이동'"
      :allFolders="allFolders"
      :targetFolderId="targetFolderId"
      :selectedItemId="selectedItemId"
      :itemType="selectedItemType"
      @cancel="cancelMove"
      @submit="confirmMove"
      @select-target="selectTargetFolder"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import FileManager from './FileManager.vue';
import CommonModal from './CommonModal.vue';
import IndexedDBService from '@/util/IndexedDBService';

export default {
  name: 'StudentPdfPage',
  components: {
    FileManager,
    CommonModal
  },
  
  setup() {
    const router = useRouter();
    const route = useRoute();
    const activeTab = ref(route.query.tab === 'team' ? 'team' : 'personal');
    const showAddOptions = ref(false);
    const showFolderModal = ref(false);
    const showFileUploadModal = ref(false);
    const showOptionsMenu = ref(false);
    const newFolderName = ref('');
    const selectedFile = ref(null);
    const fileInput = ref(null);
    const viewMode = ref('grid');
    const selectMode = ref(false);
    const selectedItems = ref([]);
    const currentPath = ref([]);
    const currentFolderId = ref(null);
    
    // 컨텍스트 메뉴 관련 변수
    const selectedItemId = ref(null);
    const selectedItemType = ref(null);
    const selectedItem = ref(null);

    // 이름 변경 관련 변수
    const showRenameModal = ref(false);
    const newItemName = ref('');

    // 이동 관련 변수
    const showMoveModal = ref(false);
    const targetFolderId = ref(null);
    
    const folders = ref([
      { id: 'mocktest', name: '기출문제', type: 'personal', parentId: null },
       { id: 'question', name: '생성문제', type: 'personal', parentId: null },
      { id: 'file', name: '요약파일', type: 'personal', parentId: null },
      { id: 'math', name: '수학', type: 'personal', parentId: 'question' },
      { id: 'english', name: '영어', type: 'personal', parentId: 'file' },
    ]);
    
    const files = ref([
      { id: 'file-3', name: '수학 기본 개념.pdf', type: 'personal', parentId: 'math' },
      { id: 'file-4', name: '영어 단어장.pdf', type: 'personal', parentId: 'english' },
      { id: 'file-5', name: '미적분 문제집.pdf', type: 'personal', parentId: 'advanced-math' }
    ]);

    const filteredFolders = computed(() => {
      return folders.value.filter(folder => 
        folder.type === activeTab.value && 
        folder.parentId === currentFolderId.value
      );
    });
    
    const selectedTeam = ref(1);
    
    const teamFolders = computed(() => {
      return {
        1: folders.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 1),
        2: folders.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 2),
        3: folders.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 3)
      };
    });
    
    const teamFiles = computed(() => {
      return {
        1: files.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 1),
        2: files.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 2),
        3: files.value.filter(f => f.type === activeTab.value && f.parentId === currentFolderId.value && f.team === 3)
      };
    });
    
    const filteredFiles = computed(() => {
      return files.value.filter(file => 
        file.type === activeTab.value && 
        file.parentId === currentFolderId.value
      );
    });
    
    // 모든 폴더 (트리 뷰용)
    const allFolders = computed(() => {
      return folders.value.filter(folder => folder.type === activeTab.value);
    });
    
    const breadcrumbs = computed(() => {
      return currentPath.value.map(id => {
        const folder = folders.value.find(f => f.id === id);
        return folder ? { id, name: folder.name } : null;
      }).filter(Boolean);
    });

    // 기능 함수들
    const handleAddClick = () => {
      showAddOptions.value = true;
    };
    
    const handleFileUpload = () => {
      showAddOptions.value = false;
      showFileUploadModal.value = true;
    };

    const handleAddFolder = () => {
      showAddOptions.value = false;
      showFolderModal.value = true;
    };

    const cancelAddFolder = () => {
      showFolderModal.value = false;
      newFolderName.value = '';
    };

    const createFolder = (folderName) => {
      if (folderName && folderName.trim() !== '') {
        const newId = 'folder-' + Date.now();
        folders.value.push({
          id: newId,
          name: folderName.trim(),
          type: activeTab.value,
          parentId: currentFolderId.value,
          team: selectedTeam.value
        });
        showFolderModal.value = false;
      }
    };
    
    const cancelFileUpload = () => {
      showFileUploadModal.value = false;
      selectedFile.value = null;
    };
    
    // 개선된 파일 업로드 함수
    const uploadFile = async (file) => {
      if (!file) return;
      
      try {
        // 파일 타입 검증
        if (file.type !== 'application/pdf') {
          alert('PDF 파일만 업로드할 수 있습니다.');
          return;
        }
        
        // 파일 크기 검증 (50MB 제한)
        const maxFileSize = 50 * 1024 * 1024;
        if (file.size > maxFileSize) {
          alert(`파일 크기가 너무 큽니다. ${IndexedDBService.formatFileSize(maxFileSize)} 이하의 파일만 업로드할 수 있습니다.`);
          return;
        }
        
        const newId = 'file-' + Date.now() + '-' + Math.random().toString(36).substring(7);
        
        console.log('📤 파일 업로드 시작:', file.name);
        
        // FileReader로 파일을 Base64로 변환
        const base64Content = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          
          reader.onload = (event) => {
            resolve(event.target.result);
          };
          
          reader.onerror = (error) => {
            reject(error);
          };
          
          reader.readAsDataURL(file);
        });
        
        // IndexedDB에 저장할 파일 정보
        const fileInfo = {
          id: newId,
          name: file.name,
          content: base64Content,
          type: file.type,
          size: file.size,
          parentId: currentFolderId.value,
          uploadDate: new Date().toISOString(),
          // 탭 정보 추가
          activeTab: activeTab.value,
          team: activeTab.value === 'team' ? selectedTeam.value : null
        };
        
        // IndexedDB에 파일 저장 - 올바른 메서드명 사용
        await IndexedDBService.saveFile(fileInfo);
        console.log('✅ IndexedDB 저장 완료');
        
        // 메모리의 파일 목록에 추가
        files.value.push({
          id: newId,
          name: file.name,
          type: activeTab.value,
          parentId: currentFolderId.value,
          size: IndexedDBService.formatFileSize(file.size),
          team: activeTab.value === 'team' ? selectedTeam.value : null
        });
        
        console.log('✅ 파일 목록 업데이트 완료');
        showFileUploadModal.value = false;
        
        // 업로드 완료 후 해당 파일로 이동 (선택사항)
        if (confirm('업로드가 완료되었습니다. 파일을 열어보시겠습니까?')) {
          router.push(`/student/pdf/view/${newId}`);
        }
        
      } catch (error) {
        console.error('❌ 파일 업로드 오류:', error);
        alert('파일 업로드 중 오류가 발생했습니다: ' + error.message);
      }
    };

    const toggleViewMode = (mode) => {
      viewMode.value = mode;
    };
    
    const toggleSelectMode = () => {
      selectMode.value = !selectMode.value;
      if (!selectMode.value) {
        selectedItems.value = [];
      }
    };
    
    const toggleOptionsMenu = () => {
      showOptionsMenu.value = !showOptionsMenu.value;
    };
    
    // 이름 변경 모달 열기
    const handleRename = (item, type) => {
      selectedItemId.value = item.id;
      selectedItemType.value = type;
      selectedItem.value = item;
      
      if (type === 'folder') {
        newItemName.value = item.name;
      } else {
        // 확장자 제외한 파일명만 편집
        const nameParts = item.name.split('.');
        const extension = nameParts.pop();
        newItemName.value = nameParts.join('.');
      }
      
      showRenameModal.value = true;
    };
    
    // 이름 변경 취소
    const cancelRename = () => {
      showRenameModal.value = false;
      newItemName.value = '';
    };
    
    // 이름 변경 확인
    const confirmRename = async (newName) => {
      if (!newName || !newName.trim()) return;
      
      try {
        if (selectedItemType.value === 'folder') {
          // 폴더 이름 변경
          const folderIndex = folders.value.findIndex(f => f.id === selectedItemId.value);
          if (folderIndex !== -1) {
            folders.value[folderIndex].name = newName.trim();
          }
        } else {
          // 파일 이름 변경
          const fileIndex = files.value.findIndex(f => f.id === selectedItemId.value);
          if (fileIndex !== -1) {
            // 확장자 유지
            const nameParts = files.value[fileIndex].name.split('.');
            const extension = nameParts.pop();
            files.value[fileIndex].name = `${newName.trim()}.${extension}`;
            
            // IndexedDB에서 파일 데이터 업데이트
            try {
              const fileData = await IndexedDBService.getFile(selectedItemId.value);
              if (fileData) {
                fileData.name = files.value[fileIndex].name;
                await IndexedDBService.saveFile(fileData);
              }
            } catch (error) {
              console.error('파일 이름 변경 오류:', error);
            }
          }
        }
        
        showRenameModal.value = false;
      } catch (error) {
        console.error('이름 변경 오류:', error);
        alert('이름을 변경하는 중 오류가 발생했습니다.');
      }
    };
    
    // 항목 이동 모달 열기
    const handleMoveItem = (item, type) => {
      selectedItemId.value = item.id;
      selectedItemType.value = type;
      selectedItem.value = item;
      showMoveModal.value = true;
      targetFolderId.value = null; // 기본값: 루트 폴더
    };
    
    // 이동 취소
    const cancelMove = () => {
      showMoveModal.value = false;
      targetFolderId.value = null;
    };
    
    // 대상 폴더 선택
    const selectTargetFolder = (folderId) => {
      targetFolderId.value = folderId;
    };
    
    // 이동 확인
    const confirmMove = async () => {
      try {
        if (selectedItemType.value === 'folder') {
          // 폴더 이동
          const folderIndex = folders.value.findIndex(f => f.id === selectedItemId.value);
          if (folderIndex !== -1) {
            folders.value[folderIndex].parentId = targetFolderId.value;
          }
        } else {
          // 파일 이동
          const fileIndex = files.value.findIndex(f => f.id === selectedItemId.value);
          if (fileIndex !== -1) {
            files.value[fileIndex].parentId = targetFolderId.value;
            
            // IndexedDB에서 파일 데이터 업데이트
            try {
              const fileData = await IndexedDBService.getFile(selectedItemId.value);
              if (fileData) {
                fileData.parentId = targetFolderId.value;
                await IndexedDBService.saveFile(fileData);
              }
            } catch (error) {
              console.error('파일 이동 오류:', error);
            }
          }
        }
        
        showMoveModal.value = false;
      } catch (error) {
        console.error('이동 오류:', error);
        alert('항목을 이동하는 중 오류가 발생했습니다.');
      }
    };
    
    // 항목 삭제
    const handleDelete = async (item, type) => {
      try {
        const confirmMessage = type === 'folder'
          ? '이 폴더와 모든 내용을 삭제하시겠습니까?'
          : '이 파일을 삭제하시겠습니까?';
          
        if (!confirm(confirmMessage)) return;
        
        if (type === 'folder') {
          // 폴더 삭제 시 하위 항목도 모두 삭제
          await deleteFolder(item.id);
        } else {
          // 파일 삭제
          await deleteFile(item.id);
        }
      } catch (error) {
        console.error('삭제 오류:', error);
        alert('항목을 삭제하는 중 오류가 발생했습니다.');
      }
    };
    
    // 파일 삭제 함수
    const deleteFile = async (fileId) => {
      try {
        // IndexedDB에서 파일 데이터 삭제
        await IndexedDBService.deleteFile(fileId);
        
        // 파일 목록에서 제거
        files.value = files.value.filter(file => file.id !== fileId);
      } catch (error) {
        console.error('파일 삭제 오류:', error);
        throw error;
      }
    };
    
    // 폴더 삭제 함수 (재귀적으로 하위 항목 삭제)
    const deleteFolder = async (folderId) => {
      try {
        // 하위 폴더 찾기
        const subFolders = folders.value.filter(folder => folder.parentId === folderId);
        
        // 하위 파일 찾기
        const subFiles = files.value.filter(file => file.parentId === folderId);
        
        // 하위 폴더 먼저 삭제 (재귀 호출)
        for (const subFolder of subFolders) {
          await deleteFolder(subFolder.id);
        }
        
        // 하위 파일 삭제
        for (const subFile of subFiles) {
          await deleteFile(subFile.id);
        }
        
        // 마지막으로 폴더 자체 삭제
        folders.value = folders.value.filter(folder => folder.id !== folderId);
      } catch (error) {
        console.error('폴더 삭제 오류:', error);
        throw error;
      }
    };
    
    const openFolder = (folderId) => {
      currentPath.value.push(folderId);
      currentFolderId.value = folderId;
    };
    
    const navigateBack = () => {
      if (currentPath.value.length > 0) {
        currentPath.value.pop();
        currentFolderId.value = currentPath.value.length > 0 
          ? currentPath.value[currentPath.value.length - 1] 
          : null;
      }
    };
    
    const navigateHome = () => {
      currentPath.value = [];
      currentFolderId.value = null;
    };
    
    const navigateToBreadcrumb = (index) => {
      if (index < currentPath.value.length) {
        currentPath.value = currentPath.value.slice(0, index + 1);
        currentFolderId.value = currentPath.value[index];
      }
    };
    
    const openFile = async (fileId) => {
      try {
        // IndexedDB에서 파일 데이터 가져오기
        const fileData = await IndexedDBService.getFile(fileId);
        if (!fileData) {
          alert('파일을 찾을 수 없습니다.');
          return;
        }
        
        // 필요한 경우 여기서 fileData를 세션 스토리지에 임시 저장할 수 있음
        // 뷰어 페이지에서 접근할 수 있도록
        sessionStorage.setItem('currentPdfFile', fileId);
        
        // PDF 뷰어 페이지로 이동
        router.push(`/student/pdf/view/${fileId}`);
      } catch (error) {
        console.error('파일 열기 오류:', error);
        alert('파일을 여는 중 오류가 발생했습니다: ' + error);
      }
    };
    
    // 저장된 파일 로드 함수
    const loadSavedFiles = async () => {
      try {
        console.log('📂 저장된 파일 로드 시작');
        const savedFiles = await IndexedDBService.getAllFiles();
        
        // 기존 파일 목록 초기화
        files.value = [];
        
        // 저장된 파일을 current activeTab과 팀에 맞게 필터링하여 추가
        savedFiles.forEach(savedFile => {
          // activeTab 정보가 없는 경우 personal로 기본 설정
          const fileTab = savedFile.activeTab || 'personal';
          const fileTeam = savedFile.team || null;
          
          files.value.push({
            id: savedFile.id,
            name: savedFile.name,
            type: fileTab,
            parentId: savedFile.parentId || null,
            size: IndexedDBService.formatFileSize(savedFile.size),
            team: fileTeam,
            uploadDate: savedFile.uploadDate
          });
        });
        
        console.log('✅ 파일 로드 완료:', files.value.length + '개');
      } catch (error) {
        console.error('❌ 파일 로드 오류:', error);
      }
    };
    
    // 컴포넌트 마운트 시 저장된 파일 로드
    onMounted(() => {
      loadSavedFiles();
    });
    
    // 탭 변경 시 파일 목록 새로고침
    watch(activeTab, () => {
      loadSavedFiles();
    });

    return {
      activeTab,
      folders,
      files,
      filteredFolders,
      filteredFiles,
      teamFolders,
      teamFiles,
      selectedTeam,
      allFolders,
      currentFolderId,
      currentPath,
      breadcrumbs,
      viewMode,
      selectMode,
      selectedItems,
      
      // 모달 관련 상태
      showAddOptions,
      showFolderModal,
      showFileUploadModal,
      showRenameModal,
      showMoveModal,
      
      // 기타 상태 변수
      newFolderName,
      selectedItemId,
      selectedItemType,
      selectedItem,
      newItemName,
      targetFolderId,
      
      // 기능 함수들
      handleAddClick,
      handleFileUpload,
      handleAddFolder,
      cancelAddFolder,
      createFolder,
      cancelFileUpload,
      uploadFile,
      toggleViewMode,
      toggleSelectMode,
      toggleOptionsMenu,
      handleRename,
      cancelRename,
      confirmRename,
      handleMoveItem,
      cancelMove,
      selectTargetFolder,
      confirmMove,
      handleDelete,
      openFolder,
      navigateBack,
      navigateHome,
      navigateToBreadcrumb,
      openFile
    };
  }
};
</script>

<style scoped>
.student-pdf-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>