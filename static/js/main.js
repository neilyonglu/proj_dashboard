document.addEventListener("DOMContentLoaded", () => {
    // 處理時間軸的預設滾動位置
    const container = document.getElementById('timeline-container');
    if (container) {
        container.scrollLeft = 150;
    }

    // 初始化所有可打字篩選的下拉 (combobox)
    document.querySelectorAll('[data-combobox]').forEach(initCombobox);
    setupComboboxFormValidation();
});

// =============================================
// Searchable combobox (打字模糊篩選 + 只能選現有項目)
//
// Expected markup:
//   <div data-combobox data-required>
//     <input type="hidden" name="field" value="...">      ← 實際送出的值
//     <input type="text" class="combo-input" ...>          ← 顯示/搜尋用
//     <ul class="combo-list hidden">
//       <li class="combo-option" data-value="ID" data-label="顯示名稱">顯示名稱 ...</li>
//     </ul>
//   </div>
// =============================================
function initCombobox(root) {
    const hidden = root.querySelector('input[type="hidden"]');
    const input = root.querySelector('.combo-input');
    const list = root.querySelector('.combo-list');
    if (!hidden || !input || !list) return;

    const options = Array.from(list.querySelectorAll('.combo-option'));
    let activeIdx = -1;

    function labelFor(value) {
        const opt = options.find(o => o.dataset.value === value);
        return opt ? opt.dataset.label : '';
    }

    // 確保初始顯示文字與已選值一致
    if (hidden.value) {
        const lbl = labelFor(hidden.value);
        if (lbl) input.value = lbl;
    }

    function openList() {
        list.classList.remove('hidden');
    }
    function closeList() {
        list.classList.add('hidden');
        activeIdx = -1;
        options.forEach(o => o.classList.remove('combo-active'));
    }

    function filter() {
        const q = input.value.trim().toLowerCase();
        let firstVisible = -1;
        options.forEach((o, i) => {
            const hay = o.dataset.label.toLowerCase();
            const match = q === '' || hay.includes(q);
            o.style.display = match ? '' : 'none';
            if (match && firstVisible === -1) firstVisible = i;
        });
        activeIdx = firstVisible;
        highlight();
    }

    function highlight() {
        options.forEach((o, i) => {
            o.classList.toggle('combo-active', i === activeIdx);
        });
        const cur = options[activeIdx];
        if (cur && cur.style.display !== 'none') {
            cur.scrollIntoView({ block: 'nearest' });
        }
    }

    function selectOption(opt) {
        if (!opt) return;
        hidden.value = opt.dataset.value;
        input.value = opt.dataset.label;
        closeList();
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // 失焦時：若輸入文字未對應任何現有項目，還原為上次選取（或清空）
    function reconcile() {
        const exact = options.find(o => o.dataset.label.toLowerCase() === input.value.trim().toLowerCase());
        if (exact) {
            selectOption(exact);
        } else if (hidden.value) {
            input.value = labelFor(hidden.value); // 還原成已選的
        } else {
            input.value = '';
        }
    }

    input.addEventListener('focus', () => { filter(); openList(); });
    input.addEventListener('input', () => { hidden.value = ''; filter(); openList(); });

    input.addEventListener('keydown', (e) => {
        const visible = options.filter(o => o.style.display !== 'none');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            openList();
            if (visible.length) {
                const curPos = visible.indexOf(options[activeIdx]);
                const np = visible[Math.min(visible.length - 1, curPos + 1)] || visible[0];
                activeIdx = options.indexOf(np);
                highlight();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const curPos = visible.indexOf(options[activeIdx]);
            const pp = visible[Math.max(0, curPos - 1)] || visible[0];
            activeIdx = options.indexOf(pp);
            highlight();
        } else if (e.key === 'Enter') {
            if (!list.classList.contains('hidden')) {
                e.preventDefault();
                if (options[activeIdx] && options[activeIdx].style.display !== 'none') {
                    selectOption(options[activeIdx]);
                }
            }
        } else if (e.key === 'Escape') {
            closeList();
        }
    });

    options.forEach(o => {
        // mousedown 先於 blur，避免點選前就被 reconcile 清掉
        o.addEventListener('mousedown', (e) => { e.preventDefault(); selectOption(o); });
    });

    input.addEventListener('blur', () => { setTimeout(() => { closeList(); reconcile(); }, 120); });
}

function setupComboboxFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        if (!form.querySelector('[data-combobox][data-required]')) return;
        form.addEventListener('submit', (e) => {
            let bad = null;
            form.querySelectorAll('[data-combobox][data-required]').forEach(root => {
                const hidden = root.querySelector('input[type="hidden"]');
                if (hidden && !hidden.value && !bad) bad = root;
            });
            if (bad) {
                e.preventDefault();
                const input = bad.querySelector('.combo-input');
                if (input) { input.focus(); }
                alert('請從清單中選擇有效的項目');
            }
        });
    });
}
