import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../static',  // 构建输出到上级 static 目录
    emptyOutDir: true,    // 构建前清空目录
  },
})
