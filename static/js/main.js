document.addEventListener("DOMContentLoaded", () => {
    // 處理時間軸的預設滾動位置
    const container = document.getElementById('timeline-container');
    if (container) {
        container.scrollLeft = 150;
    }
});