<template>
  <div class="login-container">
    <div class="container login-card">
      <div class="login-header">
        <div class="login-icon">🔐</div>
        <h2>Welcome Back</h2>
        <p class="subtitle">Sign in to your account</p>
      </div>

      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            type="email"
            v-model="email"
            placeholder="your@email.com"
            required
            @keyup.enter="login"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            type="password"
            v-model="password"
            placeholder="••••••••"
            required
            @keyup.enter="login"
          />
        </div>

        <transition name="fade">
          <div v-if="error" class="error-box">
            <span class="error-icon">❌</span>
            <span>{{ error }}</span>
          </div>
        </transition>

        <button
          type="submit"
          class="btn-login"
          :disabled="loading || !email || !password"
        >
          <span v-if="!loading">Sign In</span>
          <span v-else class="loading-spinner">Loading...</span>
        </button>
      </form>

      <div class="login-footer">
        <p><router-link to="/registration" class="highlight">Register</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const router = useRouter();

const login = () => {
  if (!email.value || !password.value) return;

  loading.value = true;
  error.value = "";

  api.post("/auth/login", {
    email: email.value,
    password: password.value,
  })
    .then(res => {
      localStorage.setItem("token", res.data.token);
      router.push("/marketplace");
    })
    .catch(() => {
      error.value = "Invalid email or password";
      password.value = "";
    })
    .finally(() => {
      loading.value = false;
    });
};
</script>

<style scoped>
.login-container {
  padding: 20px;
}

.login-card {
  max-width: 420px;
}

.login-icon {
  margin-bottom: 12px;
}

.login-header h2 {
  font-size: 1.6rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.error-icon {
  flex-shrink: 0;
}

.btn-login {
  width: 100%;
  margin-top: 6px;
}

.login-footer {
  text-align: center;
  color: #888;
  font-size: 0.9rem;
}

.login-footer .highlight {
  color: #333;
  font-weight: 500;
  cursor: pointer;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .login-header h2 {
    font-size: 1.3rem;
  }
}
</style>
