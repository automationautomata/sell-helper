<template>
  <div class="container recognize-card">
    <div class="recognize-header">
      <h2>📸 Identify Your Product</h2>
      <p class="subtitle">Upload an image and AI will recognize your product</p>
    </div>

    <div class="step-container">
      <div
        class="upload-container"
        @click="triggerFile"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
        :class="{ dragover }"
      >
        <input
          type="file"
          ref="fileInput"
          @change="onFileChange"
          accept="image/*"
        />
        <div class="upload-content">
          <div class="upload-icon">📸</div>
          <p class="upload-main-text">Upload a product image</p>
          <p class="upload-sub-text">or drag it here</p>
          <p class="upload-hint">Supported formats: JPG, PNG, GIF (Max 10MB)</p>
        </div>
      </div>

      <div v-if="preview" class="preview-container">
        <div class="preview-wrapper">
          <img :src="preview" alt="Product Preview" class="upload-preview" />
        </div>
        <div class="button-group">
          <button
            type="button"
            @click="recognizeImage"
            :disabled="recognizing"
            class="btn-recognize"
          >
            <span v-if="!recognizing">🔍 Recognize Product</span>
            <span v-else>Analyzing image...</span>
          </button>
          <button
            type="button"
            @click="clearPreview"
            class="btn-change"
          >
            🔄 Change Image
          </button>
        </div>
      </div>

      <div v-if="recognitionError" class="error-message">
        ❌ {{ recognitionError }}
      </div>
    </div>

    <!-- Category Selection Modal -->
    <teleport to="body">
      <transition name="modal">
        <div v-if="showCategoryModal" class="modal-overlay" @click.self="closeCategoryModal">
          <div class="modal-content">
            <div class="modal-header">
              <h3>🏷️ Select Product Category</h3>
              <p class="modal-subtitle">Choose the best category for your product</p>
            </div>

            <div class="categories-grid">
              <div
                v-for="(cat, idx) in categories"
                :key="idx"
                @click="selectAndLoadAspects(cat)"
                :class="['category-card', { selected: selectedCategory === cat, loading: loadingAspects }]"
              >
                <div class="category-icon">📁</div>
                <span class="category-name">{{ cat }}</span>
                <span v-if="selectedCategory === cat && !loadingAspects" class="category-check">✓</span>
                <span v-if="selectedCategory === cat && loadingAspects" class="loading-indicator">⏳</span>
              </div>
            </div>

            <div class="modal-footer">
              <button
                @click="closeCategoryModal"
                class="btn-modal-cancel"
                :disabled="loadingAspects"
              >
                Cancel
              </button>
            </div>

            <div v-if="aspectsError" class="modal-error">
              ❌ {{ aspectsError }}
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";
import useProductStore from "@/storage";

const router = useRouter();
const productStore = useProductStore();

const fileInput = ref(null);
const preview = ref(null);
const file = ref(null);
const dragOver = ref(false);

const recognizing = ref(false);
const recognitionError = ref("");
const productName = ref("");
const categories = ref([]);

const showCategoryModal = ref(false);
const selectedCategory = ref("");
const loadingAspects = ref(false);
const aspectsError = ref("");

const marketplace = ref("ozon");

const triggerFile = () => {
  fileInput.value.click();
};

const onFileChange = (event) => {
  const selected = event.target.files[0];
  if (!selected) return;
  processFile(selected);
};

const onDrop = (event) => {
  dragOver.value = false;
  const selected = event.dataTransfer.files[0];
  if (!selected) return;
  processFile(selected);
};

const processFile = (selectedFile) => {
  if (selectedFile.type.startsWith('image/') && selectedFile.size <= 10 * 1024 * 1024) {
    file.value = selectedFile;
    const reader = new FileReader();
    reader.onload = e => preview.value = e.target.result;
    reader.readAsDataURL(selectedFile);
  }
};

const recognizeImage = async () => {
  if (!file.value) return;

  recognizing.value = true;
  recognitionError.value = "";

  try {
    const formData = new FormData();
    formData.append("image", file.value);

    const res = await api.post(
      `/product/${marketplace.value}/recognize`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );

    productName.value = res.data.product_name;
    categories.value = res.data.categories || [];
    productStore.setProductName(res.data.product_name);

    // Show category modal if multiple categories
    if (categories.value.length > 0) {
      showCategoryModal.value = true;
    }
  } catch (err) {
    recognitionError.value = "Failed to recognize product. Please try again.";
    console.error(err);
  } finally {
    recognizing.value = false;
  }
};

const selectAndLoadAspects = async (cat) => {
  if (selectedCategory.value === cat) return; // Already loading or selected
  
  selectedCategory.value = cat;
  loadingAspects.value = true;
  aspectsError.value = "";

  try {
    const res = await api.post(`/product/${marketplace.value}/aspects`, {
      product_name: productName.value,
      category: cat,
    });

    // Store the aspects
    productStore.setSelectedCategory(cat);
    productStore.setAspects(res.data.product.aspects || {});

    // Close modal and redirect
    showCategoryModal.value = false;
    router.push("/publish");
  } catch (err) {
    aspectsError.value = "Failed to load product aspects. Please try again.";
    selectedCategory.value = "";
    console.error(err);
  } finally {
    loadingAspects.value = false;
  }
};

const closeCategoryModal = () => {
  if (!loadingAspects.value) {
    showCategoryModal.value = false;
    selectedCategory.value = "";
    aspectsError.value = "";
  }
};

const clearPreview = () => {
  preview.value = null;
  file.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};
</script>

<style scoped>
.recognize-card {
  max-width: 700px;
}

.recognize-header {
  text-align: center;
  margin-bottom: 24px;
}

.recognize-header h2 {
  margin-bottom: 6px;
  font-size: 1.5rem;
  color: #333;
}

.subtitle {
  color: #777;
  font-size: 0.9rem;
  margin: 0;
}

.step-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.upload-container input[type="file"] {
  display: none;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  display: block;
}

.upload-main-text {
  color: #333;
  font-weight: 600;
  font-size: 1.1rem;
  margin: 8px 0;
}

.upload-sub-text {
  color: #888;
  font-size: 0.95rem;
  margin: 6px 0;
}

.upload-hint {
  color: #aaa;
  font-size: 0.85rem;
  margin: 8px 0 0 0;
}

.preview-container {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.preview-wrapper {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  max-width: 100%;
}

.upload-preview {
  max-width: 100%;
  max-height: 350px;
  display: block;
  border-radius: 6px;
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.btn-recognize {
  background: #333;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.btn-recognize:hover:not(:disabled) {
  background: #555;
}

.btn-recognize:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-change {
  background: #666;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.btn-change:hover {
  background: #777;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 12px 14px;
  color: #dc2626;
  font-weight: 500;
  font-size: 0.9rem;
}


.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 560px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.modal-header {
  text-align: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  color: #333;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.modal-subtitle {
  color: #777;
  font-size: 0.9rem;
  margin: 0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
  padding: 20px;
}

.category-card {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}

.category-card:hover {
  border-color: #999;
  background: #f5f5f5;
}

.category-card.selected {
  background: #f0f0f0;
  border-color: #333;
}

.category-card.loading {
  cursor: not-allowed;
  opacity: 0.6;
}

.category-icon {
  font-size: 1.8rem;
}

.category-name {
  font-weight: 500;
  color: #333;
  text-align: center;
  font-size: 0.9rem;
}

.category-check {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #333;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
}

.loading-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 1rem;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-modal-cancel {
  background: #eee;
  color: #333;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn-modal-cancel:hover:not(:disabled) {
  background: #ddd;
}

.btn-modal-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 12px 14px;
  color: #dc2626;
  font-weight: 500;
  font-size: 0.9rem;
  margin: 0 20px 16px 20px;
}

.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .recognize-card {
    max-width: 100%;
  }

  .upload-container {
    padding: 32px 16px;
  }

  .upload-icon {
    font-size: 2rem;
  }

  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 10px;
    padding: 16px;
  }

  .button-group {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .modal-content {
    max-height: 90vh;
  }

  .modal-header {
    padding: 16px;
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
    font-size: 1rem;
  }

  .categories-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .button-group {
    gap: 8px;
  }

  .modal-overlay {
    padding: 10px;
  }

  .modal-content {
    border-radius: 6px;
  }
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  display: block;
  animation: bounce 2s ease-in-out infinite;
}

.upload-main-text {
  color: #667eea;
  font-weight: 700;
  font-size: 1.2rem;
  margin: 10px 0;
}

.upload-sub-text {
  color: #999;
  font-size: 1rem;
  margin: 8px 0;
}

.upload-hint {
  color: #aaa;
  font-size: 0.85rem;
  margin: 12px 0 0 0;
}

.preview-container {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.preview-wrapper {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  max-width: 100%;
}

.upload-preview {
  max-width: 100%;
  max-height: 400px;
  display: block;
  border-radius: 12px;
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
}

.btn-recognize {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.btn-recognize:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-recognize:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-change {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.btn-change:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
}

.recognition-result {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 2px solid #28a745;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 30px;
  animation: slideUp 0.5s ease-out;
}

.recognition-result h3 {
  color: #155724;
  margin-top: 0;
  margin-bottom: 15px;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  font-weight: 600;
  color: #155724;
  min-width: 130px;
}

.value {
  color: #155724;
  font-size: 1.05rem;
}

.info-image {
  max-width: 150px;
  max-height: 150px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-selection {
  margin-bottom: 30px;
}

.category-selection h3 {
  margin-top: 0;
  color: #333;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 20px;
}

.category-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
}

.category-card:hover {
  border-color: #667eea;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
}

.category-card.selected {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.category-icon {
  font-size: 2rem;
}

.category-name {
  font-weight: 600;
  color: #333;
  text-align: center;
  font-size: 0.95rem;
}

.category-check {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #667eea;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 30px;
}

.btn-proceed {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  grid-column: 1;
}

.btn-proceed:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-proceed:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-reset {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  grid-column: 2;
}

.btn-reset:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
}

.error-message {
  background: #ffe5e5;
  border: 2px solid #ff6b6b;
  border-radius: 12px;
  padding: 16px;
  color: #c92a2a;
  font-weight: 600;
  margin-top: 20px;
  animation: shake 0.3s ease-in-out;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  animation: slideUp 0.5s ease-out;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 15px;
}

.empty-state h3 {
  color: #333;
  margin-bottom: 10px;
}

.empty-state p {
  color: #999;
  margin-bottom: 25px;
}

.btn-retry {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.btn-retry:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .recognize-card {
    padding: 24px;
  }

  .upload-container {
    padding: 40px 20px;
  }

  .upload-icon {
    font-size: 2.5rem;
  }

  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }

  .button-group {
    grid-template-columns: 1fr;
  }

  .form-actions {
    grid-template-columns: 1fr;
  }

  .btn-proceed,
  .btn-reset {
    grid-column: 1;
  }

  .product-info {
    flex-direction: column;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .upload-container {
    padding: 30px 15px;
  }

  .upload-icon {
    font-size: 2rem;
  }

  .upload-main-text {
    font-size: 1rem;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .button-group {
    gap: 10px;
  }
}
</style>
