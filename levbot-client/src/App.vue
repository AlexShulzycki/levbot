<script setup lang="ts">
import BlockDisplay from "./components/BlockDisplay.vue";
import {ref} from "vue";
import Block from "./components/Block.ts"
const ws = new WebSocket('ws://localhost:8080');

let blockObjects = ref(new Array<Block>())

ws.onopen = () => {
  console.log('Connected to server');
  ws.send("henlou :DDDDDD")
  // Send the ping!
  ws.send("ping!")
};

ws.onmessage = (event) => {
  console.log(`Message from server: ${event.data}`);
  try{
    const parsed = JSON.parse(event.data).blocks
    for(let i = 0; i < parsed.length; i++) {
      parsed[i] = new Block(parsed[i].blockid, parsed[i].time)
    }
    blockObjects.value.push(...parsed)
  }catch(e){
    console.log("Error parsing to JSON" + e)
  }
};

ws.onclose = () => {
  console.log('Connection closed');
};

</script>

<template>
  <h1> Title text </h1>
  <h3>{{blockObjects[0].id}}</h3>
  <BlockDisplay v-for="x in blockObjects" :model="x" :key="x.id"/>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
