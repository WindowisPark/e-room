<template>
  <FileManager
    :activeTab="activeTab"
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
    @add-item="$emit('add-item')"
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
  name: 'PersonalFileManager',
  components: { FileManager },
  props: {
    activeTab: String,
    currentPath: Array,
    breadcrumbs: Array,
    viewMode: String,
    selectMode: Boolean,
    selectedItems: Array,
  }
};
</script>