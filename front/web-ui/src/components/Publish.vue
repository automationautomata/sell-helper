<template>
  <div class="container publish-card">
    <div class="publish-header">
      <h2>📦 Publish New Product</h2>
      <p class="subtitle">Complete your product details</p>
    </div>

    <div v-if="productStore.productName" class="recognized-info">
      <div class="info-badge">
        <span class="badge-icon">✨</span>
        <div class="badge-content">
          <span class="badge-label">Recognized Product:</span>
          <span class="badge-value">{{ productStore.productName }}</span>
        </div>
      </div>
      <div class="info-badge">
        <span class="badge-icon">📂</span>
        <div class="badge-content">
          <span class="badge-label">Category:</span>
          <span class="badge-value">{{ productStore.selectedCategory }}</span>
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3>Product Information</h3>
      <div class="form-group">
        <label for="title">Product Title *</label>
        <input
          id="title"
          v-model="title"
          placeholder="Enter product title"
          maxlength="150"
          required
        />
        <span class="char-count">{{ title.length }}/150</span>
      </div>

      <div class="form-group">
        <label for="description">Description *</label>
        <textarea
          id="description"
          v-model="description"
          placeholder="Describe your product in detail"
          maxlength="2000"
          required
        ></textarea>
        <span class="char-count">{{ description.length }}/2000</span>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="category">Category *</label>
          <input
            id="category"
            v-model="category"
            placeholder="Enter category"
            required
          />
        </div>
        <div class="form-group">
          <label for="quantity">Quantity *</label>
          <input
            id="quantity"
            type="number"
            v-model.number="quantity"
            placeholder="1"
            min="1"
            required
          />
        </div>
      </div>
    </div>

    <div class="form-section">
      <h3>Pricing & Location</h3>
      <div class="form-row">
        <div class="form-group">
          <label for="price">Price *</label>
          <div class="price-input-group">
            <input
              id="price"
              type="number"
              v-model.number="price"
              placeholder="0.00"
              min="0"
              step="0.01"
              required
            />
          </div>
        </div>
        <div class="form-group">
          <label for="currency">Currency *</label>
          <select v-model="currency" id="currency" required>
            <option value="USD">💵 USD - US Dollar</option>
            <option value="EUR">€ EUR - Euro</option>
            <option value="RUB">₽ RUB - Russian Ruble</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label for="country">Country *</label>
        <select v-model="country" id="country" required>
          <option value="US">🇺🇸 United States</option>
          <option value="RU">🇷🇺 Russia</option>
          <option value="DE">🇩🇪 Germany</option>
          <option value="GB">🇬🇧 United Kingdom</option>
          <option value="FR">🇫🇷 France</option>
        </select>
      </div>
    </div>

    <UploadImage ref="uploadComp" />

    <div v-if="aspectKeys.length" class="aspect-section">
      <h3>✨ Product Specifications (Auto-filled)</h3>
      <p class="info-text">Review and update product specifications</p>
      <div class="aspect-grid">
        <div class="aspect-item" v-for="key in aspectKeys" :key="key">
          <label :for="key">{{ formatAspectName(key) }}</label>
          <input
            :id="key"
            type="text"
            v-model="productStore.aspects[key]"
            placeholder="Enter value"
          />
          <span v-if="productStore.aspects[key]" class="value-badge">✓ Filled</span>
        </div>
      </div>
    </div>

    <transition name="slide">
      <div v-if="successMessage" class="success-message">
        ✅ {{ successMessage }}
      </div>
    </transition>

    <div class="form-actions">
      <button
        @click="publish"
        :disabled="!canPublish || publishing"
        class="btn-publish"
      >
        <span v-if="!publishing">🚀 Publish Product</span>
        <span v-else>Publishing...</span>
      </button>
      <button
        @click="goBack"
        class="btn-back"
        :disabled="publishing"
      >
        ⬅️ Go Back
      </button>
    </div>

    <div v-if="errorMessage" class="error-message">
      ❌ {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import useProductStore from "@/storage";
import UploadImage from "@/components/UploadImage.vue";
import api from "@/api";

const router = useRouter();
const productStore = useProductStore();
const uploadComp = ref(null);

const title = ref("");
const category = ref("");
const description = ref("");
const price = ref(null);
const currency = ref("USD");
const country = ref("US");
const quantity = ref(1);
const publishing = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

// Prepopulate category from recognized data
if (productStore.selectedCategory) {
  category.value = productStore.selectedCategory;
}

const aspectKeys = computed(() => Object.keys(productStore.aspects || {}));

const canPublish = computed(() =>
  title.value.trim() &&
  description.value.trim() &&
  category.value.trim() &&
  price.value > 0 &&
  quantity.value > 0 &&
  uploadComp.value?.files?.length > 0
);

const formatAspectName = (key) => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const publish = async () => {
  if (!canPublish.value) return;

  publishing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const item = {
      title: title.value,
      description: description.value,
      category: category.value,
      price: price.value,
      currency: currency.value,
      country: country.value,
      quantity: quantity.value,
      product: productStore.aspects,
      marketplace_aspects: {},
    };

    const formData = new FormData();
    formData.append("item", JSON.stringify(item));
    uploadComp.value.files.forEach(f => formData.append("images", f));

    await api.post("/product/publish", formData);

    successMessage.value = "Product published successfully! 🎉";
    setTimeout(() => {
      productStore.clear();
      router.push("/recognize");
    }, 2000);
  } catch (err) {
    errorMessage.value = "Failed to publish product. Please try again.";
    console.error(err);
  } finally {
    publishing.value = false;
  }
};

const goBack = () => {
  router.push("/recognize");
};
</script>

<style scoped>
.publish-card {
  max-width: 900px;
}

.publish-header {
  text-align: center;
  margin-bottom: 24px;
}

.publish-header h2 {
  margin-bottom: 6px;
  font-size: 1.5rem;
  color: #333;
}

.subtitle {
  color: #777;
  font-size: 0.9rem;
  margin: 0;
}

.recognized-info {
  background: #f0fdf4;
  border: 1px solid #dcfce7;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.info-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  padding: 10px 12px;
  border-radius: 4px;
  border: 1px solid #eee;
  font-size: 0.9rem;
}

.badge-icon {
  font-size: 1.3rem;
}

.badge-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.badge-label {
  font-size: 0.75rem;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
}

.badge-value {
  color: #22c55e;
  font-weight: 600;
  font-size: 0.9rem;
}

.form-section {
  background: #fafafa;
  padding: 18px;
  border-radius: 6px;
  border: 1px solid #eee;
  margin-bottom: 18px;
}

.form-section h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1rem;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.form-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid #ddd;
  font-size: 1rem;
  transition: all 0.2s;
  background-color: #fafafa;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #333;
  background-color: #fff;
}

.char-count {
  font-size: 0.85rem;
  color: #999;
  align-self: flex-end;
}

.price-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-input-group input {
  flex: 1;
}

.aspect-section {
  background: #fafafa;
  padding: 18px;
  border-radius: 6px;
  border: 1px solid #eee;
  margin-bottom: 18px;
}

.aspect-section h3 {
  margin-top: 0;
  margin-bottom: 4px;
  font-size: 1rem;
  color: #333;
}

.aspect-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.aspect-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.aspect-item label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.value-badge {
  font-size: 0.75rem;
  background: #333;
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 500;
  align-self: flex-start;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 24px;
}

.btn-publish {
  background: #333;
  color: white;
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back {
  background: #666;
  color: white;
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-publish:not(:disabled):hover {
  background: #555;
}

.btn-back:not(:disabled):hover {
  background: #777;
}

.btn-publish:disabled,
.btn-back:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 12px 14px;
  color: #dc2626;
  font-weight: 500;
  font-size: 0.9rem;
  margin-top: 16px;
}

.success-message {
  background: #f0fdf4;
  border: 1px solid #dcfce7;
  border-radius: 6px;
  padding: 12px 14px;
  color: #22c55e;
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.info-text {
  color: #777;
  font-size: 0.85rem;
  margin: 0;
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .publish-card {
    max-width: 100%;
  }

  .recognized-info {
    flex-direction: column;
    gap: 10px;
  }

  .form-section {
    padding: 14px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .aspect-grid {
    grid-template-columns: 1fr;
  }

  .form-actions {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .btn-publish,
  .btn-back {
    width: 100%;
  }

  .publish-header h2 {
    font-size: 1.3rem;
  }
}

@media (max-width: 480px) {
  .recognized-info {
    flex-direction: column;
  }

  .info-badge {
    width: 100%;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    grid-template-columns: 1fr;
  }
}
</style>

<style scoped>
.publish-card {
  max-width: 900px;
}

.publish-header {
  text-align: center;
  margin-bottom: 35px;
}

.publish-header h2 {
  margin-bottom: 8px;
}

.subtitle {
  color: #999;
  font-size: 1rem;
  margin: 0;
}

.form-section {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
  padding: 24px;
  border-radius: 16px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  margin-bottom: 24px;
}

.form-section h3 {
  margin-top: 0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
}

.form-group label {
  font-weight: 600;
  color: #555;
  font-size: 0.95rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 14px 16px;
  border-radius: 12px;
  border: 2px solid #e0e0e0;
  font-size: 1rem;
  transition: all 0.3s ease;
  background-color: #fafafa;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #667eea;
  background-color: #fff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.char-count {
  font-size: 0.85rem;
  color: #999;
  align-self: flex-end;
}

.price-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-input-group input {
  flex: 1;
}

.aspect-section {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  padding: 24px;
  border-radius: 16px;
  border-left: 4px solid #667eea;
  margin-bottom: 24px;
}

.aspect-section h3 {
  margin-top: 0;
}

.aspect-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.aspect-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-item label {
  font-weight: 600;
  color: #555;
  font-size: 0.95rem;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 30px;
}

.btn-publish {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  grid-column: 1;
}

.btn-reset {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  grid-column: 2;
}

.btn-publish:not(:disabled):hover,
.btn-reset:not(:disabled):hover {
  transform: translateY(-3px);
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

.success-message {
  background: #d4edda;
  border: 2px solid #28a745;
  border-radius: 12px;
  padding: 16px;
  color: #155724;
  font-weight: 600;
  margin-bottom: 20px;
  animation: slideUp 0.3s ease-out;
}

.info-text {
  color: #666;
  font-size: 0.9rem;
  margin: 8px 0 0 0;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 768px) {
  .publish-card {
    padding: 24px;
  }

  .form-section,
  .aspect-section {
    padding: 16px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .aspect-grid {
    grid-template-columns: 1fr;
  }

  .form-actions {
    grid-template-columns: 1fr;
  }

  .btn-publish,
  .btn-reset {
    grid-column: 1;
  }

  .publish-header h2 {
    font-size: 1.5rem;
  }
}
</style>
