import type { GlobalThemeOverrides } from 'naive-ui'

/**
 * Naive UI 主題客製化配置
 * 整合 Tailwind CSS 色彩系統
 */
export const themeOverrides: GlobalThemeOverrides = {
  common: {
    // 主色系 - 藍色
    primaryColor: '#0ea5e9',
    primaryColorHover: '#0284c7',
    primaryColorPressed: '#0369a1',
    primaryColorSuppl: '#38bdf8',

    // 資訊色 - 藍色
    infoColor: '#0ea5e9',
    infoColorHover: '#0284c7',
    infoColorPressed: '#0369a1',
    infoColorSuppl: '#38bdf8',

    // 成功色 - 綠色
    successColor: '#10b981',
    successColorHover: '#059669',
    successColorPressed: '#047857',
    successColorSuppl: '#34d399',

    // 警告色 - 橙色
    warningColor: '#f59e0b',
    warningColorHover: '#d97706',
    warningColorPressed: '#b45309',
    warningColorSuppl: '#fbbf24',

    // 錯誤色 - 紅色
    errorColor: '#ef4444',
    errorColorHover: '#dc2626',
    errorColorPressed: '#b91c1c',
    errorColorSuppl: '#f87171',

    // 文字色
    textColorBase: '#1f2937', // gray-800
    textColor1: '#111827', // gray-900
    textColor2: '#374151', // gray-700
    textColor3: '#6b7280', // gray-500
    textColorDisabled: '#9ca3af', // gray-400

    // 背景色
    bodyColor: '#ffffff',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    tableColor: '#ffffff',

    // 邊框
    borderColor: '#e5e7eb', // gray-200
    dividerColor: '#e5e7eb',

    // 圓角
    borderRadius: '0.5rem', // 8px
    borderRadiusSmall: '0.375rem', // 6px

    // 陰影
    boxShadow1: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    boxShadow2: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    boxShadow3: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  },

  // 按鈕
  Button: {
    borderRadiusMedium: '0.5rem',
    borderRadiusLarge: '0.625rem',
    fontSizeMedium: '0.875rem',
    fontSizeLarge: '1rem',
    heightMedium: '2.5rem',
    heightLarge: '2.75rem',
    paddingMedium: '0 1rem',
    paddingLarge: '0 1.25rem',
  },

  // 卡片
  Card: {
    borderRadius: '0.75rem', // 12px
    paddingMedium: '1.5rem',
    paddingLarge: '2rem',
    titleFontSizeMedium: '1.125rem',
    titleFontSizeLarge: '1.25rem',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  },

  // 輸入框
  Input: {
    borderRadius: '0.5rem',
    heightMedium: '2.5rem',
    heightLarge: '2.75rem',
    paddingMedium: '0 0.75rem',
    paddingLarge: '0 1rem',
    fontSizeMedium: '0.875rem',
    fontSizeLarge: '1rem',
  },

  // 選單
  Menu: {
    borderRadius: '0.5rem',
    itemHeight: '2.75rem',
    itemIconSize: '1.25rem',
    itemTextColor: '#374151',
    itemTextColorHover: '#111827',
    itemTextColorActive: '#0ea5e9',
    itemTextColorActiveHover: '#0284c7',
    itemColorActive: '#eff6ff', // blue-50
    itemColorActiveHover: '#dbeafe', // blue-100
    groupTextColor: '#6b7280',
  },

  // 下拉選單
  Dropdown: {
    borderRadius: '0.625rem',
    padding: '0.5rem',
    optionHeightMedium: '2.5rem',
    optionHeightLarge: '2.75rem',
  },

  // 統計數字
  Statistic: {
    valueFontSizeMedium: '1.875rem',
    valueFontSizeLarge: '2.25rem',
    labelFontSize: '0.875rem',
  },

  // 進度條
  Progress: {
    railHeight: '0.5rem',
    fillBorderRadius: '0.25rem',
  },

  // Layout
  Layout: {
    color: '#f9fafb', // gray-50
    siderColor: '#ffffff',
    headerColor: '#ffffff',
    headerBorderColor: '#e5e7eb',
    siderBorderColor: '#e5e7eb',
  },

  // 訊息提示
  Message: {
    borderRadius: '0.625rem',
    padding: '0.75rem 1rem',
  },

  // 通知
  Notification: {
    borderRadius: '0.75rem',
    padding: '1rem',
  },
}
