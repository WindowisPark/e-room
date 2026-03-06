<template>
  <div class="student-pdf-container">
    <!-- 파일 관리자 컴포넌트 -->
    <FileManager
      :filteredFolders="filteredFolders"
      :filteredFiles="filteredFiles"
      :allFolders="allFolders"
      :currentPath="currentPath"
      :breadcrumbs="breadcrumbs"
      :viewMode="viewMode"
      :selectMode="selectMode"
      :selectedItems="selectedItems"
      @toggle-view="toggleViewMode"
      @toggle-select="toggleSelectMode"
      @navigate-back="navigateBack"
      @navigate-home="navigateHome"
      @navigate-to-breadcrumb="navigateToBreadcrumb"
      @add-item="handleAddClick"
      @open-folder="openFolder"
      @open-file="openFile"
      @update:selectedItems="selectedItems = $event"
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

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import FileManager from './FileManager.vue';
import CommonModal from './CommonModal.vue';
import IndexedDBService from '@/util/IndexedDBService';

const router = useRouter();
const showAddOptions = ref(false);
const showFolderModal = ref(false);
const showFileUploadModal = ref(false);
const newFolderName = ref('');
const selectedFile = ref(null);
const viewMode = ref('grid');
const selectMode = ref(false);
const selectedItems = ref([]);
const currentPath = ref([]);
const currentFolderId = ref(null);

const selectedItemId = ref(null);
const selectedItemType = ref(null);
const selectedItem = ref(null);

const showRenameModal = ref(false);
const newItemName = ref('');

const showMoveModal = ref(false);
const targetFolderId = ref(null);

const folders = ref([]);
const files = ref([]);

const filteredFolders = computed(() =>
  folders.value.filter(f => f.parentId === currentFolderId.value)
);

const filteredFiles = computed(() =>
  files.value.filter(f => f.parentId === currentFolderId.value)
);

const allFolders = computed(() => folders.value);

const breadcrumbs = computed(() =>
  currentPath.value
    .map(id => {
      const folder = folders.value.find(f => f.id === id);
      return folder ? { id, name: folder.name } : null;
    })
    .filter(Boolean)
);

const handleAddClick = () => { showAddOptions.value = true; };
const handleFileUpload = () => { showAddOptions.value = false; showFileUploadModal.value = true; };
const handleAddFolder = () => { showAddOptions.value = false; showFolderModal.value = true; };
const cancelAddFolder = () => { showFolderModal.value = false; newFolderName.value = ''; };

const createFolder = (folderName) => {
  if (folderName && folderName.trim() !== '') {
    folders.value.push({
      id: 'folder-' + Date.now(),
      name: folderName.trim(),
      parentId: currentFolderId.value
    });
    showFolderModal.value = false;
  }
};

const cancelFileUpload = () => { showFileUploadModal.value = false; selectedFile.value = null; };

const uploadFile = async (file) => {
  if (!file) return;
  try {
    if (file.type !== 'application/pdf') {
      alert('PDF 파일만 업로드할 수 있습니다.');
      return;
    }
    const maxFileSize = 50 * 1024 * 1024;
    if (file.size > maxFileSize) {
      alert(`파일 크기가 너무 큽니다. ${IndexedDBService.formatFileSize(maxFileSize)} 이하의 파일만 업로드할 수 있습니다.`);
      return;
    }

    const newId = 'file-' + Date.now() + '-' + Math.random().toString(36).substring(7);
    console.log('📤 파일 업로드 시작:', file.name);

    const base64Content = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsDataURL(file);
    });

    await IndexedDBService.saveFile({
      id: newId,
      name: file.name,
      content: base64Content,
      type: file.type,
      size: file.size,
      parentId: currentFolderId.value,
      uploadDate: new Date().toISOString()
    });
    console.log('✅ IndexedDB 저장 완료');

    files.value.push({
      id: newId,
      name: file.name,
      parentId: currentFolderId.value,
      size: IndexedDBService.formatFileSize(file.size)
    });
    console.log('✅ 파일 목록 업데이트 완료');
    showFileUploadModal.value = false;

    if (confirm('업로드가 완료되었습니다. 파일을 열어보시겠습니까?')) {
      router.push(`/student/pdf/view/${newId}`);
    }
  } catch (error) {
    console.error('❌ 파일 업로드 오류:', error);
    alert('파일 업로드 중 오류가 발생했습니다: ' + error.message);
  }
};

const toggleViewMode = (mode) => { viewMode.value = mode; };
const toggleSelectMode = () => {
  selectMode.value = !selectMode.value;
  if (!selectMode.value) selectedItems.value = [];
};

const handleRename = (item, type) => {
  selectedItemId.value = item.id;
  selectedItemType.value = type;
  selectedItem.value = item;
  if (type === 'folder') {
    newItemName.value = item.name;
  } else {
    const parts = item.name.split('.');
    parts.pop();
    newItemName.value = parts.join('.');
  }
  showRenameModal.value = true;
};

const cancelRename = () => { showRenameModal.value = false; newItemName.value = ''; };

const confirmRename = async (newName) => {
  if (!newName || !newName.trim()) return;
  try {
    if (selectedItemType.value === 'folder') {
      const idx = folders.value.findIndex(f => f.id === selectedItemId.value);
      if (idx !== -1) folders.value[idx].name = newName.trim();
    } else {
      const idx = files.value.findIndex(f => f.id === selectedItemId.value);
      if (idx !== -1) {
        const parts = files.value[idx].name.split('.');
        const ext = parts.pop();
        files.value[idx].name = `${newName.trim()}.${ext}`;
        try {
          const fileData = await IndexedDBService.getFile(selectedItemId.value);
          if (fileData) {
            fileData.name = files.value[idx].name;
            await IndexedDBService.saveFile(fileData);
          }
        } catch (e) {
          console.error('파일 이름 변경 오류:', e);
        }
      }
    }
    showRenameModal.value = false;
  } catch (error) {
    console.error('이름 변경 오류:', error);
    alert('이름을 변경하는 중 오류가 발생했습니다.');
  }
};

const handleMoveItem = (item, type) => {
  selectedItemId.value = item.id;
  selectedItemType.value = type;
  selectedItem.value = item;
  showMoveModal.value = true;
  targetFolderId.value = null;
};

const cancelMove = () => { showMoveModal.value = false; targetFolderId.value = null; };
const selectTargetFolder = (folderId) => { targetFolderId.value = folderId; };

const confirmMove = async () => {
  try {
    if (selectedItemType.value === 'folder') {
      const idx = folders.value.findIndex(f => f.id === selectedItemId.value);
      if (idx !== -1) folders.value[idx].parentId = targetFolderId.value;
    } else {
      const idx = files.value.findIndex(f => f.id === selectedItemId.value);
      if (idx !== -1) {
        files.value[idx].parentId = targetFolderId.value;
        try {
          const fileData = await IndexedDBService.getFile(selectedItemId.value);
          if (fileData) {
            fileData.parentId = targetFolderId.value;
            await IndexedDBService.saveFile(fileData);
          }
        } catch (e) {
          console.error('파일 이동 오류:', e);
        }
      }
    }
    showMoveModal.value = false;
  } catch (error) {
    console.error('이동 오류:', error);
    alert('항목을 이동하는 중 오류가 발생했습니다.');
  }
};

const handleDelete = async (item, type) => {
  try {
    const msg = type === 'folder' ? '이 폴더와 모든 내용을 삭제하시겠습니까?' : '이 파일을 삭제하시겠습니까?';
    if (!confirm(msg)) return;
    if (type === 'folder') await deleteFolder(item.id);
    else await deleteFile(item.id);
  } catch (error) {
    console.error('삭제 오류:', error);
    alert('항목을 삭제하는 중 오류가 발생했습니다.');
  }
};

const deleteFile = async (fileId) => {
  await IndexedDBService.deleteFile(fileId);
  files.value = files.value.filter(f => f.id !== fileId);
};

const deleteFolder = async (folderId) => {
  const subFolders = folders.value.filter(f => f.parentId === folderId);
  const subFiles = files.value.filter(f => f.parentId === folderId);
  for (const sf of subFolders) await deleteFolder(sf.id);
  for (const sf of subFiles) await deleteFile(sf.id);
  folders.value = folders.value.filter(f => f.id !== folderId);
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

const navigateHome = () => { currentPath.value = []; currentFolderId.value = null; };

const navigateToBreadcrumb = (index) => {
  if (index < currentPath.value.length) {
    currentPath.value = currentPath.value.slice(0, index + 1);
    currentFolderId.value = currentPath.value[index];
  }
};

const openFile = async (fileId) => {
  try {
    const fileData = await IndexedDBService.getFile(fileId);
    if (!fileData) { alert('파일을 찾을 수 없습니다.'); return; }
    sessionStorage.setItem('currentPdfFile', fileId);
    router.push(`/student/pdf/view/${fileId}`);
  } catch (error) {
    console.error('파일 열기 오류:', error);
    alert('파일을 여는 중 오류가 발생했습니다: ' + error);
  }
};

const loadSavedFiles = async () => {
  try {
    console.log('📂 저장된 파일 로드 시작');
    const savedFiles = await IndexedDBService.getAllFiles();
    files.value = savedFiles.map(f => ({
      id: f.id,
      name: f.name,
      parentId: f.parentId || null,
      size: IndexedDBService.formatFileSize(f.size),
      uploadDate: f.uploadDate
    }));
    console.log('✅ 파일 로드 완료:', files.value.length + '개');
  } catch (error) {
    console.error('❌ 파일 로드 오류:', error);
  }
};

onMounted(() => { loadSavedFiles(); });
</script>

<style scoped>
.student-pdf-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
