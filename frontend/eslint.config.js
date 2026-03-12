import antfu from '@antfu/eslint-config'

export default antfu({
  vue: true,
  typescript: true,
  formatters: true,

  ignores: [
    '*.md',
  ],

  // 自訂規則
  rules: {
    // 允許 console.log
    'no-console': 'off',

    // Vue 相關
    'vue/multi-word-component-names': 'off',

    // TypeScript 相關
    '@typescript-eslint/no-explicit-any': 'warn',
  },
})
