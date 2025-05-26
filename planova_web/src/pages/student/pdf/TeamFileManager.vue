<template>
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
    @update:activeTab="$emit('update:activeTab', $event)"
    @toggle-view="$emit('toggle-view', $event)"
    @toggle-select="$emit('toggle-select')"
    @toggle-options="$emit('toggle-options')"
    @navigate-back="$emit('navigate-back')"
    @navigate-home="$emit('navigate-home')"
    @navigate-to-breadcrumb="$emit('navigate-to-breadcrumb', $event)"
    @add-item="$emit('add-item', selectedTeam)"
    @open-folder="$emit('open-folder', $event)"
    @open-file="$emit('open-file', $event)"
    @update:selectedItems="$emit('update:selectedItems', $event)"
    @handle-rename="$emit('handle-rename', ...arguments)"
    @handle-move="$emit('handle-move', ...arguments)"
    @handle-delete="$emit('handle-delete', ...arguments)"
  />
</template>

<script>
import FileManager from './FileManager.vue';
export default {
  name: 'TeamFileManager',
  components: { FileManager },
  props: {
    activeTab: String,
    teamFolders: Object,
    teamFiles: Object,
    selectedTeam: Number,
    currentPath: Array,
    breadcrumbs: Array,
    viewMode: String,
    selectMode: Boolean,
    selectedItems: Array,
  },
  emits: [
    'update:activeTab',
    'toggle-view',
    'toggle-select',
    'toggle-options',
    'navigate-back',
    'navigate-home',
    'navigate-to-breadcrumb',
    'add-item',
    'open-folder',
    'open-file',
    'update:selectedItems',
    'handle-rename',
    'handle-move',
    'handle-delete',
    'update:selectedTeam'
  ]
};
</script>