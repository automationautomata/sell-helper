<template>
  <form @submit.prevent="login">
    <input type="email" v-model="email" placeholder="Email" required />
    <input type="password" v-model="password" placeholder="Password" required />
    <button type="submit">Login</button>
    <p v-if="error">{{ error }}</p>
  </form>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api/api";

const email = ref("");
const password = ref("");
const error = ref("");
const router = useRouter();

const login = () => {
  api
    .post("/auth/login", { email: email.value, password: password.value })
    .then((res) => {
      localStorage.setItem("token", res.data.token); // Only essential
      router.push("/recognize");
    })
    .catch(() => {
      error.value = "Invalid email or password";
    });
};
</script>
