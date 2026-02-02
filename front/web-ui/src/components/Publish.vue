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
      <div class="info-badge">
        <span class="badge-icon">🏪</span>
        <div class="badge-content">
          <span class="badge-label">Marketplace:</span>
          <span class="badge-value">{{ productStore.marketplace }}</span>
        </div>
      </div>
    </div>

    <Recommendations />

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

    <Aspects />

    <AccountSettings v-model="showSettings" />

    <transition name="slide">
      <div v-if="successMessage" class="success-message">
        ✅ {{ successMessage }}
      </div>
    </transition>
    <button
      @click="publish"
      :disabled="!canPublish || publishing"
      class="btn"
    >
      <span v-if="!publishing">🚀 Publish Product</span>
      <span v-else>Publishing...</span>
    </button>
    
    <div class="action-buttons">
      <button 
        @click="showSettings = true" 
        :disabled="isSettingsDisabled()"
        class="btn-settings"
      >
        ⚙️ Settings
      </button>

      <button
        @click="goBack"
        class="btn"
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
import Recommendations from "@/components/Recommendations.vue";
import Aspects from "@/components/Aspects.vue";
import api from "@/api";
import AccountSettings from '@/components/AccountSettings.vue';

const router = useRouter();
const productStore = useProductStore();
const uploadComp = ref(null);
const showSettings = ref(false);

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

if (productStore.selectedCategory) {
  category.value = productStore.selectedCategory;
}

// const aspectKeys = computed(() => Object.keys(productStore.aspects || {}));

const canPublish = computed(() =>
  title.value.trim() &&
  description.value.trim() &&
  category.value.trim() &&
  price.value > 0 &&
  quantity.value > 0 &&
  uploadComp.value?.files?.length > 0
);
const isSettingsDisabled = () => productStore.selectedMarketplace;

const publish = () => {
  if (!canPublish.value) return;

  publishing.value = true;
  errorMessage.value = "";
  successMessage.value = "";

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

  api.post("/product/publish", formData)
    .then(() => {
      successMessage.value = "Product published successfully! 🎉";
      setTimeout(() => {
        productStore.clear();
        router.push("/recognize");
      }, 2000);
    })
    .catch(err => {
      errorMessage.value = "Failed to publish product. Please try again.";
      console.error(err);
    })
    .finally(() => {
      publishing.value = false;
    });
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

.btn {
  background: #666;
}

.btn:hover:not(:disabled) {
  background: #777;
}

.btn-settings:hover:not(:disabled) {
  background: #777;
}

.btn-settings:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
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
    gap: 15px;
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
