<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
const viols = ref<any[]>([])
const unplaced = ref<any[]>([])
const state = ref('')
const error = ref('')
onMounted(async () => {
  try {
    const res = await api('/seating/violations?hall_id=1')
    viols.value = res.violations; unplaced.value = res.unplaced; state.value = res.state
  } catch (e: any) {
    error.value = e?.message || '查询失败'
  }
})
</script>
<template>
  <h1>违规</h1>
  <p class="sub">间距不足或同试卷四邻相邻</p>
  <div v-if="error" class="card" style="border-color:var(--hs-bad);color:var(--hs-bad);font-weight:700">
    {{ error }}
  </div>
  <template v-else>
    <div class="card">
      <span class="badge" :class="state === 'closed' ? 'badge-bad' : 'badge-ok'" style="margin-bottom:0.5rem">
        {{ state === 'closed' ? '封闭场' : '开放场' }}
      </span>
      <table>
        <thead><tr><th>类型</th><th>考生A</th><th>考生B</th><th>说明</th></tr></thead>
        <tbody>
          <tr v-for="(v,i) in viols" :key="i">
            <td>{{ v.kind }}</td><td>{{ v.a_id }}</td><td>{{ v.b_id }}</td><td>{{ v.detail }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!viols.length" class="muted">无违规</p>
    </div>
    <div class="card" v-if="state === 'open' && unplaced.length">
      <h3>未排上</h3>
      <div v-for="u in unplaced" :key="u.id">{{ u.name }}（{{ u.ticket_no }}）</div>
    </div>
    <div class="card" v-if="state === 'closed'">
      <h3>未排上</h3>
      <p class="muted">封闭场 · 未排入口已关闭</p>
    </div>
  </template>
</template>
