/// <reference types="vite/client" />

// theme/index.ts 里 `import './custom.css'` 是副作用导入，TS 默认不认识
// .css 模块（TS2882）。vite/client 带 *.css 的模块声明，引一次就够，
// 不要写成 `declare module '*.css'` 自己造一份。
