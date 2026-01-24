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
        <p>Don't have an account? <span class="highlight">Contact administrator</span></p>
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

const login = async () => {
  if (!email.value || !password.value) return;

  loading.value = true;
  error.value = "";

  try {
    const res = await api.post("/auth/login", {
      email: email.value,
      password: password.value,
    });
    localStorage.setItem("token", res.data.token);
    router.push("/recognize");
  } catch (err) {
    error.value = "Invalid email or password";
    password.value = "";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background: #f5f5f5;
}

.login-card {
  margin: 0;
  max-width: 420px;
  width: 100%;
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 12px;
}

.login-header h2 {
  margin-bottom: 6px;
  font-size: 1.6rem;
  color: #333;
}

.subtitle {
  color: #777;
  font-size: 0.9rem;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group input:focus {
  border-color: #333;
}

.error-box {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #dc2626;
  font-weight: 500;
  font-size: 0.9rem;
}

.error-icon {
  font-size: 1.1rem;
}

.btn-login {
  width: 100%;
  padding: 12px 16px;
  font-size: 1rem;
  margin-top: 6px;
}

.btn-login:not(:disabled):hover {
  background: #555;
}

.loading-spinner {
  display: inline-block;
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
  .login-card {
    padding: 24px !important;
  }

  .login-icon {
    font-size: 2rem;
  }

  .login-header h2 {
    font-size: 1.3rem;
  }
}
</style>
