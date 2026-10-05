<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
const rows = ref<any[]>([])
async function load() { rows.value = await api('/candidates') }
async function toggleKey(r: any) {
  await api(`/candidates/${r.id}`, { method: 'PATCH', body: JSON.stringify({ is_key: !r.is_key }) })
  await load()
}
onMounted(load)
</script>
<template>
  <h1>考生名册</h1>
  <p class="sub">夹板名册样式 · 标一名关键考生场次即封闭，全部取消则开放</p>
  <div class="hs-clipboard" style="max-width:480px">
    <h2>考生名册 · Clipboard</h2>
    <div v-for="r in rows" :key="r.id ?? JSON.stringify(r)" class="hs-roster-row">
      <div>
        <div>
          {{ r.name }}
          <span v-if="r.is_key" class="badge badge-bad">关键</span>
        </div>
        <div class="hs-ticket">{{ r.ticket_no }}</div>
      </div>
      <div style="display:flex;align-items:center;gap:0.5rem">
        <span>卷{{ r.paper_id }} · 室{{ r.hall_id }}</span>
        <button class="btn" style="padding:0.15rem 0.5rem;font-size:0.72rem" @click="toggleKey(r)">
          {{ r.is_key ? '取消关键' : '标为关键' }}
        </button>
      </div>
    </div>
  </div>
</template>
