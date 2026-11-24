/**
 * Kokogram Web Client Entry Point (HLD §1.7)
 */

import { initAuthView } from './views/auth.js';

document.addEventListener('DOMContentLoaded', () => {
  initAuthView();
});
