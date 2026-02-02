<template>
  <div class="container recognize-card">
    <div class="recognize-header">
      <h2>📸 Identify Your Product</h2>
      <p class="subtitle">Upload an image and AI will recognize your product</p>
    </div>

    <div class="step-container">
      <UploadImage ref="uploadComponent" @file-added="onFileAdded" />

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
import UploadImage from "./UploadImage.vue";

const router = useRouter();
const productStore = useProductStore();

const uploadComponent = ref(null);

const file = ref(null);
const preview = ref(null);

const recognizing = ref(false);
const recognitionError = ref("");
const productName = ref("");
const categories = ref([]);

const showCategoryModal = ref(false);
const selectedCategory = ref("");
const loadingAspects = ref(false);
const aspectsError = ref("");

const marketplace = ref(productStore.marketplace);

const recognizeImage = () => {
  if (!file.value) {
    recognitionError.value = "Please upload an image first";
    return;
  }

  recognizing.value = true;
  recognitionError.value = "";

  const formData = new FormData();
  formData.append("image", file.value);

  api.post(
    `/product/${marketplace.value}/recognize`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  )
    .then(res => {
      productName.value = res.data.product_name;
      categories.value = res.data.categories || [];
      productStore.setProductName(res.data.product_name);

      if (categories.value.length > 0) {
        showCategoryModal.value = true;
      }
    })
    .catch(err => {
      recognitionError.value = "Failed to recognize product. Please try again.";
      console.error(err);
    })
    .finally(() => {
      recognizing.value = false;
    });
};

const selectAndLoadAspects = (category) => {
  if (selectedCategory.value === category) return;
  
  selectedCategory.value = category;
  loadingAspects.value = true;
  aspectsError.value = "";

  api.post(`/product/${marketplace.value}/aspects`, {
    product_name: productName.value,
    category: category,
  })
    .then(res => {
      productStore.setSelectedCategory(category);
      productStore.setAspects(res.data.product.aspects || {});
      
      if (res.data.metadata) {
        productStore.setRecommendations(res.data.metadata);
      }

      showCategoryModal.value = false;
      router.push("/publish");
    })
    .catch(err => {
      aspectsError.value = "Failed to load product aspects. Please try again.";
      selectedCategory.value = "";
      console.error(err);
    })
    .finally(() => {
      loadingAspects.value = false;
    });
};

const closeCategoryModal = () => {
  if (!loadingAspects.value) {
    showCategoryModal.value = false;
    selectedCategory.value = "";
    aspectsError.value = "";
  }
};

const clearPreview = () => {
  file.value = null;
  preview.value = null;
  if (uploadComponent.value) {
    uploadComponent.value.clearAll();
  }
};

const onFileAdded = (data) => {
  file.value = data.file;
  preview.value = data.preview;
  console.log('File added:', data.file.name);
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

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.btn-recognize {
  padding: 10px 16px;
  font-size: 0.95rem;
  background: #333;
  color: white;
}

.btn-recognize:hover:not(:disabled) {
  background: #555;
}

.btn-change {
  padding: 10px 16px;
  font-size: 0.95rem;
  background: #666;
  color: white;
}

.btn-change:hover {
  background: #777;
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

.loading-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 1rem;
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
  .categories-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 10px;
    padding: 16px;
  }

  .button-group {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .categories-grid {
    grid-template-columns: 1fr;
  }
}
</style>
