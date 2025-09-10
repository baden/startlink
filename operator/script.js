let gamepad = null;
let requestAnimationFrameId = null;
// const ws = new WebSocket("ws://localhost:8765");
const ws = new WebSocket("ws://s.navi.cc:8765");

// Змінні для керування частотою відправки
// let lastSendTime = 0;
// const sendInterval = 1000 / 5; // 1000 мс / 5 відправок = 200 мс між відправками

// Функція для оновлення статусу джойстика
function updateGamepadStatus() {
    const statusDiv = document.getElementById('gamepad-status');
    if (gamepad) {
        statusDiv.textContent = `Підключено: ${gamepad.id} (Індекс: ${gamepad.index})`;
        updateAxesDisplay();
        updateButtonsDisplay();

        // Перевірка часу перед відправкою через WebSocket
        const currentTime = Date.now();
        if (ws.readyState === WebSocket.OPEN /*&& (currentTime - lastSendTime > sendInterval)*/) {
            const data = {
                axes: gamepad.axes,
                buttons: gamepad.buttons.map(button => ({ pressed: button.pressed, value: button.value }))
            };
            ws.send(JSON.stringify(data));
            //lastSendTime = currentTime; // Оновлюємо час останньої відправки
        }
    } else {
        statusDiv.textContent = 'Очікування підключення джойстика...';
    }
}

// Функція для оновлення відображення осей
function updateAxesDisplay() {
    if (!gamepad) return;
    for (let i = 0; i < gamepad.axes.length; i++) {
        let axisDiv = document.getElementById(`axis${i}`);
        if (!axisDiv) {
            axisDiv = document.createElement('div');
            axisDiv.id = `axis${i}`;
            axisDiv.className = 'control-item';
            document.getElementById('axes-display').appendChild(axisDiv);
        }
        axisDiv.textContent = `Вісь ${i}: ${gamepad.axes[i].toFixed(4)}`;
    }
}

// Функція для оновлення відображення кнопок
function updateButtonsDisplay() {
    if (!gamepad) return;
    for (let i = 0; i < gamepad.buttons.length; i++) {
        let buttonDiv = document.getElementById(`button${i}`);
        if (!buttonDiv) {
            buttonDiv = document.createElement('div');
            buttonDiv.id = `button${i}`;
            buttonDiv.className = 'control-item';
            document.getElementById('buttons-display').appendChild(buttonDiv);
        }
        buttonDiv.textContent = `Кнопка ${i}: ${gamepad.buttons[i].pressed ? 'Натиснута' : 'Не натиснута'} (Значення: ${gamepad.buttons[i].value.toFixed(4)})`;
    }
}

// Основний цикл для опитування джойстика
function gameLoop() {
    const gamepads = navigator.getGamepads();
    if (gamepads.length > 0) {
        // Ми припускаємо, що нас цікавить перший підключений джойстик
        // Можливо, вам потрібно буде додати логіку для вибору конкретного джойстика за Vendor/Product ID
        gamepad = gamepads[0]; // або шукати по gamepad.id, щоб знайти ваш Radiomaster
    } else {
        gamepad = null;
    }

    updateGamepadStatus();
    requestAnimationFrameId = requestAnimationFrame(gameLoop);
}

// Обробник події підключення джойстика
window.addEventListener("gamepadconnected", (event) => {
    console.log("Gamepad", [event.gamepad]);
    console.log("Gamepad connected at index %d: %s. %d buttons, %d axes.",
        event.gamepad.index, event.gamepad.id,
        event.gamepad.buttons.length, event.gamepad.axes.length);

    // Перевірка на Vendor/Product ID
    // Radiomaster TX12 Joystick: Vendor: 1209 Product: 4f54
    // Деякі браузери можуть надавати ідентифікатор у форматі "Vendor_XXXX_Product_YYYY"
    // або просто текстовий опис. Вам потрібно буде перевірити формат у вашому браузері.
    if (event.gamepad.id.includes("Vendor: 1209 Product: 4f54") || event.gamepad.id.includes("Radiomaster TX12 Joystick")) { // Або інший спосіб перевірки
        gamepad = event.gamepad;
        if (!requestAnimationFrameId) { // Запускаємо цикл, якщо він ще не запущений
            requestAnimationFrameId = requestAnimationFrame(gameLoop);
        }
    } else {
        console.log("Інший джойстик підключено, але не Radiomaster TX12.");
    }
});

// Обробник події відключення джойстика
window.addEventListener("gamepaddisconnected", (event) => {
    console.log("Gamepad disconnected from index %d: %s",
        event.gamepad.index, event.gamepad.id);
    if (gamepad && gamepad.index === event.gamepad.index) {
        gamepad = null;
        cancelAnimationFrame(requestAnimationFrameId);
        requestAnimationFrameId = null;
        updateGamepadStatus();
    }
});

// Початковий запуск перевірки джойстика, якщо він вже підключений при завантаженні сторінки
// Це може бути не потрібно, якщо ви покладаєтеся тільки на gamepadconnected
const initialGamepads = navigator.getGamepads();
if (initialGamepads.length > 0) {
    // Перевірте, чи є серед них ваш Radiomaster
    console.log("gpamepads:", [initialGamepads]);
    for (const gp of initialGamepads) {
        if (gp && (gp.id.includes("Vendor_1209_Product_4f54") || gp.id.includes("RadioMaster TX12 Joystick"))) {
            gamepad = gp;
            break;
        }
    }
    if (gamepad && !requestAnimationFrameId) {
        requestAnimationFrameId = requestAnimationFrame(gameLoop);
    }
} else {
    updateGamepadStatus();
}


ws.onopen = () => {
    console.log("Connected to WebSocket server!");
    // Відправляємо тестове повідомлення
    ws.send(JSON.stringify({ command: "get_status" }));
};

ws.onmessage = (event) => {
    console.log("Received:", event.data);
};

ws.onclose = (event) => {
    console.log("Disconnected:", event.code, event.reason);
};

ws.onerror = (error) => {
    console.error("WebSocket Error:", error);
};

// Щоб закрити з'єднання:
// ws.close();