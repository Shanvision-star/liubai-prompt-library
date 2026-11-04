'use strict';
const feedbackDialog = document.getElementById('feedback-dialog');
const feedbackMenu = document.getElementById('settings-menu');
document.getElementById('feedback-open').addEventListener('click', () => {
  feedbackMenu.open = false;
  feedbackDialog.showModal();
});
document.getElementById('feedback-close').addEventListener('click', () => feedbackDialog.close());
feedbackDialog.addEventListener('close', () => feedbackMenu.querySelector('summary').focus());
