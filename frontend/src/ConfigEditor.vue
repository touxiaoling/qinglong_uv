<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { basicSetup, EditorView } from 'codemirror'
import { yaml } from '@codemirror/lang-yaml'
import { StreamLanguage } from '@codemirror/language'
import { toml } from '@codemirror/legacy-modes/mode/toml'

const props = defineProps({ filename: String })
const content = defineModel({ type: String, required: true })
const container = ref()
let editor

onMounted(() => {
  editor = new EditorView({
    parent: container.value,
    doc: content.value,
    extensions: [
      basicSetup,
      props.filename.toLowerCase().endsWith('.toml') ? StreamLanguage.define(toml) : yaml(),
      EditorView.contentAttributes.of({ 'aria-label': props.filename }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) content.value = update.state.doc.toString()
      }),
    ],
  })
})

onBeforeUnmount(() => editor?.destroy())
</script>

<template>
  <div ref="container" class="code-editor"></div>
</template>
