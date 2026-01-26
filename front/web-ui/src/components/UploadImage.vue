<template>
  <div class="upload-section">
    <h3>Product Images</h3>
    <p class="info-text">Upload at least one image of your product</p>
    
    <div
      class="upload-container"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      :class="{ dragover: dragOver }"
    >
      <div class="upload-content">
        <div class="upload-icon">🖼️</div>
        <p class="upload-main-text">Drag & drop images here</p>
        <p class="upload-hint">Supported formats: JPG, PNG, GIF (Max 10MB each)</p>
      </div>
    </div>

    <div v-if="previews.length" class="preview-section">
      <div class="preview-header">
        <h4>{{ previews.length }} image{{ previews.length !== 1 ? 's' : '' }} added</h4>
        <button type="button" @click="clearAll" class="btn-clear-all">Clear All</button>
      </div>
      <div class="upload-preview-grid">
        <div v-for="(img, i) in previews" :key="i" class="preview-item">
          <img :src="img" :alt="`Preview ${i + 1}`" />
          <button
            type="button"
            @click="removeImage(i)"
            class="btn-remove"
            title="Remove image"
          >
            ✕
          </button>
          <span class="preview-number">{{ i + 1 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const emit = defineEmits(['file-added']);

const files = ref([]);
const previews = ref([]);
const dragOver = ref(false);

const onDragEnter = () => {
  dragOver.value = true;
};

const onDragOver = (event) => {
  event.dataTransfer.dropEffect = 'copy';
  dragOver.value = true;
};

const onDragLeave = () => {
  dragOver.value = false;
};

const onDrop = (event) => {
  dragOver.value = false;
  event.dataTransfer.dropEffect = 'copy';
  const droppedFiles = event.dataTransfer.files;
  console.log('Files dropped:', droppedFiles);
  handleFiles(droppedFiles);
};

const handleFiles = (selectedFiles) => {
  console.log('handleFiles called with:', selectedFiles);
  for (let f of selectedFiles) {
    console.log('Processing file:', f.name, f.type, f.size);
    if (f.type.startsWith('image/') && f.size <= 10 * 1024 * 1024) {
      files.value.push(f);
      const reader = new FileReader();
      reader.onload = e => {
        console.log('Preview added for:', f.name);
        previews.value.push(e.target.result);
        emit('file-added', { file: f, preview: e.target.result });
      };
      reader.readAsDataURL(f);
    } else {
      console.log('File rejected:', f.name);
    }
  }
  console.log('Total files:', files.value.length);
};

const removeImage = (index) => {
  files.value.splice(index, 1);
  previews.value.splice(index, 1);
};

const clearAll = () => {
  files.value = [];
  previews.value = [];
};

defineExpose({ files, previews });
</script>

<style scoped>
.upload-section {
  background: #fafafa;
  padding: 18px;
  border-radius: 6px;
  border: 1px solid #eee;
  margin-bottom: 18px;
}

.upload-section h3 {
  margin-top: 0;
  margin-bottom: 6px;
  font-size: 1rem;
  color: #333;
}

.upload-container {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
  position: relative;
  overflow: hidden;
}

.upload-container:hover {
  border-color: #999;
  background: #f5f5f5;
}

.upload-container.dragover {
  border-color: #333;
  background: #f0f0f0;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 2.2rem;
  margin-bottom: 12px;
  display: block;
}

.upload-main-text {
  color: #333;
  font-weight: 600;
  font-size: 1rem;
  margin: 8px 0;
}

.upload-sub-text {
  color: #888;
  font-size: 0.9rem;
  margin: 4px 0;
}

.upload-hint {
  color: #aaa;
  font-size: 0.85rem;
  margin: 8px 0 0 0;
}

.preview-section {
  margin-top: 18px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.preview-header h4 {
  color: #333;
  font-size: 0.95rem;
  margin: 0;
  font-weight: 500;
}

.btn-clear-all {
  background: #666;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-clear-all:hover {
  background: #777;
}

.upload-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}

.preview-item {
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  aspect-ratio: 1;
  border: 1px solid #eee;
}

.preview-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-number {
  position: absolute;
  top: 6px;
  left: 6px;
  background: #333;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
}

.btn-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  background: #d32f2f;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
  opacity: 0;
}

.preview-item:hover .btn-remove {
  opacity: 1;
}

.btn-remove:hover {
  background: #b71c1c;
}

.info-text {
  color: #777;
  font-size: 0.85rem;
  margin: 0;
}

@media (max-width: 768px) {
  .upload-section {
    padding: 14px;
  }

  .upload-container {
    padding: 32px 16px;
  }

  .upload-icon {
    font-size: 2rem;
  }

  .upload-main-text {
    font-size: 0.95rem;
  }

  .upload-preview-grid {
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
    gap: 10px;
  }

  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .btn-clear-all {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .upload-container {
    padding: 24px 12px;
  }

  .upload-icon {
    font-size: 1.8rem;
  }

  .upload-main-text {
    font-size: 0.9rem;
  }

  .upload-hint {
    font-size: 0.75rem;
  }

  .upload-preview-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 8px;
  }
}
</style>
