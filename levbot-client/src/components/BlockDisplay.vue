<script setup lang="ts">
import Block from "./Block.ts"
let {model}  = defineProps({"model": Block})
</script>

<template>
  <div class="blockdiv">
    <h5>Block!</h5>
  <h2>Block ID: {{model.id}}</h2>
    <h5>Current time: {{model.time}}</h5>
    <button type="button" @click="model.id ++">Click meeee</button>

  </div>
</template>

<style scoped>
.blockdiv{
  padding: 2em;
}
</style>