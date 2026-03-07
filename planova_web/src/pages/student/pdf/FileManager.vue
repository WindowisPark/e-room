<!-- FileManager.vue - 파일 및 폴더 관리 컴포넌트 -->
<template>
  <div>
    <!-- 페이지 헤더 -->
    <div class="pdf-page-header">
      <div class="pdf-page-title"><i class="fa-solid fa-book-open"></i> 내 PDF 파일</div>
      <div class="pdf-page-desc">학습 자료를 업로드하고 AI로 분석하세요</div>
    </div>

    <!-- 상단 액션 영역 -->
    <div class="top-container">
      <div class="action-icons">
        <button
          class="action-button"
          :class="{ 'active-icon': viewMode === 'list' }"
          @click="$emit('toggle-view', 'list')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="action-icon">
            <line x1="8" y1="6" x2="21" y2="6"></line>
            <line x1="8" y1="12" x2="21" y2="12"></line>
            <line x1="8" y1="18" x2="21" y2="18"></line>
            <line x1="3" y1="6" x2="3.01" y2="6"></line>
            <line x1="3" y1="12" x2="3.01" y2="12"></line>
            <line x1="3" y1="18" x2="3.01" y2="18"></line>
          </svg>
        </button>
        <button
          class="action-button"
          :class="{ 'active-icon': viewMode === 'grid' }"
          @click="$emit('toggle-view', 'grid')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="action-icon">
            <rect x="3" y="3" width="7" height="7" rx="1"></rect>
            <rect x="14" y="3" width="7" height="7" rx="1"></rect>
            <rect x="3" y="14" width="7" height="7" rx="1"></rect>
            <rect x="14" y="14" width="7" height="7" rx="1"></rect>
          </svg>
        </button>
      </div>
    </div>

    <!-- 경로 네비게이션 영역 -->
    <div class="breadcrumb-container" v-if="currentPath.length > 0">
      <button class="back-button" @click="$emit('navigate-back')">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"></path>
          <path d="M12 19l-7-7 7-7"></path>
        </svg>
      </button>
      <div class="breadcrumb-path">
        <span class="breadcrumb-item" @click="$emit('navigate-home')">홈</span>
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.id">
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-item" @click="$emit('navigate-to-breadcrumb', index)">
            {{ crumb.name }}
          </span>
        </template>
      </div>
    </div>

    <!-- 파일/폴더 그리드 영역 -->
    <div class="folder-grid" :class="{ 'list-view': viewMode === 'list' }">
      <div class="folder-item add-folder" @click="$emit('add-item')">
        <div class="add-icon">
          <span class="plus-icon">+</span>
        </div>
        <div class="folder-name">추가</div>
      </div>

      <div
        v-for="folder in filteredFolders"
        :key="folder.id"
        class="folder-item"
        :class="{ 'list-view': viewMode === 'list', 'selected': selectMode && selectedItems.includes(folder.id) }"
        @click="selectMode ? toggleItemSelection(folder.id) : $emit('open-folder', folder.id)"
        @contextmenu.prevent="showContextMenu($event, 'folder', folder)"
      >
        <div class="item-checkbox" v-if="selectMode">
          <input
            type="checkbox"
            :checked="selectedItems.includes(folder.id)"
            @click.stop="toggleItemSelection(folder.id)"
          >
        </div>
        <div class="folder-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFC107" stroke="#FFA000" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="folder-svg">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        <div class="folder-name">{{ folder.name }}</div>
      </div>

      <div
        v-for="file in filteredFiles"
        :key="file.id"
        class="folder-item file-item"
        :class="{ 'list-view': viewMode === 'list', 'selected': selectMode && selectedItems.includes(file.id) }"
        @click="selectMode ? toggleItemSelection(file.id) : $emit('open-file', file.id)"
        @contextmenu.prevent="showContextMenu($event, 'file', file)"
      >
        <div class="item-checkbox" v-if="selectMode">
          <input
            type="checkbox"
            :checked="selectedItems.includes(file.id)"
            @click.stop="toggleItemSelection(file.id)"
          >
        </div>
        <div class="file-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ECEFF1" stroke="#607D8B" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="file-svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <path d="M14 2v6h6"></path>
            <path d="M16 13H8" stroke="red"></path>
            <path d="M16 17H8" stroke="red"></path>
            <path d="M10 9H8" stroke="red"></path>
          </svg>
        </div>
        <div class="folder-name">
          {{ file.name }}
          <div class="file-size" v-if="file.size">{{ file.size }}</div>
        </div>
      </div>
    </div>

    <!-- 컨텍스트 메뉴 -->
    <div v-if="showContextMenuFlag" class="context-menu" :style="contextMenuStyle">
      <div class="context-menu-item" @click="$emit('handle-rename', selectedContextItem, selectedContextType); closeContextMenu()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 20h9"></path>
          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
        </svg>
        <span>이름 변경</span>
      </div>
      <div class="context-menu-item" @click="$emit('handle-move', selectedContextItem, selectedContextType); closeContextMenu()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <line x1="9" y1="15" x2="15" y2="15"></line>
        </svg>
        <span>이동</span>
      </div>
      <div class="context-menu-item delete" @click="$emit('handle-delete', selectedContextItem, selectedContextType); closeContextMenu()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          <line x1="10" y1="11" x2="10" y2="17"></line>
          <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>
        <span>삭제</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FileManager',
  emits: [
    'toggle-view',
    'toggle-select',
    'navigate-back',
    'navigate-home',
    'navigate-to-breadcrumb',
    'add-item',
    'open-folder',
    'open-file',
    'update:selectedItems',
    'handle-rename',
    'handle-move',
    'handle-delete'
  ],
  props: {
    filteredFolders: {
      type: Array,
      required: true
    },
    filteredFiles: {
      type: Array,
      required: true
    },
    allFolders: {
      type: Array,
      default: () => []
    },
    currentPath: {
      type: Array,
      required: true
    },
    breadcrumbs: {
      type: Array,
      required: true
    },
    viewMode: {
      type: String,
      default: 'grid'
    },
    selectMode: {
      type: Boolean,
      default: false
    },
    selectedItems: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      showContextMenuFlag: false,
      contextMenuStyle: { top: '0px', left: '0px' },
      selectedContextType: null,
      selectedContextItem: null
    };
  },
  mounted() {
    document.addEventListener('click', this.closeContextMenu);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeContextMenu);
  },
  methods: {
    toggleItemSelection(itemId) {
      const next = [...this.selectedItems];
      const idx = next.indexOf(itemId);
      if (idx === -1) next.push(itemId);
      else next.splice(idx, 1);
      this.$emit('update:selectedItems', next);
    },
    showContextMenu(event, type, item) {
      this.contextMenuStyle = {
        top: `${event.clientY}px`,
        left: `${event.clientX}px`
      };
      this.selectedContextType = type;
      this.selectedContextItem = item;
      this.showContextMenuFlag = true;
    },
    closeContextMenu() {
      this.showContextMenuFlag = false;
    }
  }
};
</script>

<style scoped>
/* 페이지 헤더 */
.pdf-page-header {
  margin-bottom: 20px;
}

.pdf-page-title {
  font-size: 1.3rem;
  font-weight: 800;
  color: #1a1a1a;
}

.pdf-page-desc {
  font-size: 0.85rem;
  color: #888;
  margin-top: 4px;
}

/* 상단 액션 */
.top-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 15px;
}

.action-icons {
  display: flex;
  gap: 10px;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  width: 40px;
  height: 40px;
}

.action-button:hover {
  background-color: #f0f0f0;
}

.action-button:focus {
  outline: none;
  box-shadow: none;
}

.action-icon {
  width: 24px;
  height: 24px;
  color: #555;
}

.action-button.active-icon .action-icon {
  color: #F76707;
}

/* 브레드크럼 */
.breadcrumb-container {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  background-color: #f8f9ff;
  padding: 8px 12px;
  border-radius: 8px;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 10px;
  color: #555;
  transition: all 0.2s;
}

.back-button:hover {
  background-color: #e9ecef;
  color: #333;
}

.breadcrumb-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.breadcrumb-item {
  font-size: 14px;
  color: #000;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
}

.breadcrumb-item:hover {
  background-color: #e3f2fd;
  text-decoration: underline;
}

.breadcrumb-separator {
  color: #999;
  margin: 0 2px;
}

/* 그리드 / 리스트 */
.folder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.folder-grid.list-view {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.folder-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  width: 100px;
  margin: 0 auto;
  position: relative;
  padding: 8px;
  border-radius: 8px;
}

.folder-item:hover {
  transform: translateY(-3px);
  background-color: #FFF8F2;
}

.folder-item.file-item:hover {
  border-left: 3px solid #F76707;
}

.folder-item.selected {
  background-color: #e3f2fd;
  border: 1px solid #64b5f6;
}

.folder-item.list-view {
  flex-direction: row;
  width: 100%;
  padding: 10px 15px;
  margin: 0;
  justify-content: flex-start;
  align-items: center;
  gap: 15px;
}

.folder-item.list-view:hover {
  transform: none;
  background-color: #FFF8F2;
}

.folder-item.list-view .folder-name {
  text-align: left;
  font-size: 14px;
}

.item-checkbox {
  position: absolute;
  top: 5px;
  left: 5px;
  z-index: 1;
}

.folder-item.list-view .item-checkbox {
  position: static;
  margin-right: 10px;
}

.folder-icon,
.file-icon {
  width: 48px;
  height: 48px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
}

.folder-svg,
.file-svg {
  width: 100%;
  height: 100%;
}

.add-icon {
  width: 40px;
  height: 40px;
  background-color: #F76707;
  color: white;
  border-radius: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 5px;
  margin-bottom: 10px;
}

.plus-icon {
  font-size: 25px;
  font-weight: bold;
  line-height: 1;
}

.folder-name {
  font-size: 15px;
  text-align: center;
  color: #333;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 11px;
  color: #888;
  margin-top: 2px;
}

/* 컨텍스트 메뉴 */
.context-menu {
  position: fixed;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  padding: 5px 0;
  z-index: 1100;
  min-width: 180px;
}

.context-menu-item {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background-color 0.2s;
}

.context-menu-item:hover {
  background-color: #f5f5f5;
}

.context-menu-item svg {
  margin-right: 10px;
  color: #555;
}

.context-menu-item.delete {
  color: #f44336;
}

.context-menu-item.delete svg {
  color: #f44336;
}

@media (max-width: 768px) {
  .folder-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 12px;
  }

  .folder-item {
    width: 80px;
  }
}
</style>
