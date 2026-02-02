<template>
  <div class="app-wrapper">
    <nav class="navbar">
      <div class="navbar-container">
        <div class="navbar-brand">
          <span class="brand-icon">📦</span>
        </div>
        <div v-if="isLoggedIn" class="navbar-actions">
          <button @click="logout" class="btn-logout">Logout</button>
        </div>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token');
});

const logout = () => {
  localStorage.removeItem('token');
  router.push('/');
};
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f5f5;
}

.navbar {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.brand-icon {
  font-size: 1.6rem;
}

.navbar-brand h1 {
  font-size: 1.3rem;
  color: #333;
  font-weight: 600;
  margin: 0;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  color: #666;
  text-decoration: none;
  font-weight: 500;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.nav-link:hover {
  color: #333;
  background: #eee;
}

.nav-link.active {
  color: #333;
  background: #ddd;
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: #333;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn-logout:hover {
  background: #555;
}

.main-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 2rem 2rem;
}

.app-footer {
  background: #f5f5f5;
  border-top: 1px solid #eee;
  color: #666;
  text-align: center;
  padding: 1.5rem 2rem;
  margin-top: 2rem;
  font-size: 0.9rem;
}

.app-footer p {
  margin: 0;
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0.8rem 1rem;
  }

  .navbar-brand h1 {
    font-size: 1.1rem;
  }

  .navbar-actions {
    gap: 10px;
  }

  .nav-link {
    padding: 0.4rem 0.6rem;
    font-size: 0.85rem;
  }

  .main-content {
    padding: 1.5rem 1rem;
  }

  .app-footer {
    padding: 1rem;
  }
}
</style>
