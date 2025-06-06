// A-Frame element selectors
const hand = document.querySelector("#hand");
const syringe = document.querySelector("#syringe");
let holding = false; // This variable might still be useful for local state representation

// WebSocket connection
const socket = new WebSocket("ws://localhost:8000/ws");

socket.onopen = () => {
    console.log("WebSocket conectado ao backend.");
    // Example: Send a join message if your backend expects one
    // socket.send(JSON.stringify({ action: "client_join", payload: { clientId: "frontend_user_vr" } }));
};

socket.onmessage = (event) => {
    console.log("Mensagem recebida do backend:", event.data);
    try {
        const message = JSON.parse(event.data);

        // Logic to handle messages from the backend
        if (message.source === "sofa_bridge" && message.data) {
            console.log("Feedback do SOFA:", message.data);
            // Example: Display SOFA message or use force_feedback
            if (message.data.message) {
                console.log("Mensagem do SOFA Bridge:", message.data.message);
            }
            if (message.data.force_feedback !== undefined) {
                console.log("Feedback de força do SOFA:", message.data.force_feedback);
                // Here you could apply some visual or other feedback based on force
            }
            // If SOFA bridge confirms an action, you might update local A-Frame state here
            if (message.action === "pegar_seringa" && message.data.status === "success") {
                console.log("Backend/SOFA confirmou 'pegar_seringa'. Atualizando A-Frame.");
                // Local A-Frame updates (example)
                holding = true;
                syringe.setAttribute("position", "0 -0.1 0"); // Position relative to hand
                if (hand) hand.appendChild(syringe); // Ensure hand is found
                else console.error("Elemento #hand não encontrado no A-Frame.");
            } else if (message.action === "soltar_seringa" && message.data.status === "success") {
                 console.log("Backend/SOFA confirmou 'soltar_seringa'. Atualizando A-Frame.");
                 holding = false;
                 // Append to scene and set world position
                 const scene = document.querySelector("a-scene");
                 if (scene) scene.appendChild(syringe); else console.error("Elemento a-scene não encontrado.");
                 // Use position from backend if provided, otherwise a default
                 const pos = message.data.position || { x: 0, y: 1.1, z: -1.8 };
                 syringe.setAttribute("position", `${pos.x} ${pos.y} ${pos.z}`);
            }


        } else if (message.source === "esp32_status" && message.data) {
            console.log("Status do ESP32:", message.data);
            // Example: Update UI with ESP32's FSR value or motor status
            // document.getElementById("fsr-value-display").textContent = message.data.fsr_value;
        } else if (message.source === "backend" && message.message) {
            console.log("Mensagem do Backend:", message.message);
        }

    } catch (e) {
        console.error("Erro ao parsear JSON do backend:", e, "Dados recebidos:", event.data);
    }
};

socket.onclose = (event) => {
    console.log("WebSocket desconectado do backend.", event.reason, `Code: ${event.code}`);
};

socket.onerror = (error) => {
    console.error("Erro no WebSocket:", error);
};

// ------------- Functions to Send JSON Commands -------------

function sendMoveHandCommand(position) { // position e.g., {x: 0.1, y: 1.2, z: -1.5}
    if (socket.readyState === WebSocket.OPEN) {
        const command = { action: "mover_mao", payload: { position: position } };
        socket.send(JSON.stringify(command));
        console.log("Comando 'mover_mao' enviado:", command);
        // Local A-Frame update (optimistic update)
        if (hand) hand.setAttribute("position", `${position.x} ${position.y} ${position.z}`);
        else console.error("Elemento #hand não encontrado para mover.");

    } else {
        console.error("WebSocket não está aberto. Não foi possível enviar 'mover_mao'.");
    }
}

function sendPegarSeringaCommand() {
    if (socket.readyState === WebSocket.OPEN) {
        // Payload can include current hand position or other relevant info
        const handPosition = hand ? hand.getAttribute("position") : null;
        const command = { action: "pegar_seringa", payload: { hand_id: "#hand", syringe_id: "#syringe", hand_pos: handPosition } };
        socket.send(JSON.stringify(command));
        console.log("Comando 'pegar_seringa' enviado.", command);
        // OPTIONAL: Optimistic local update (A-Frame manipulation)
        // Or wait for backend confirmation message (see in socket.onmessage)
        // holding = true;
        // syringe.setAttribute("position", "0 -0.1 0"); // Relative to hand
        // if(hand) hand.appendChild(syringe); else console.error("Elemento #hand não encontrado.");
    } else {
        console.error("WebSocket não está aberto. Não foi possível enviar 'pegar_seringa'.");
    }
}

function sendSoltarSeringaCommand(position) { // position of the syringe when released (world coords)
     if (socket.readyState === WebSocket.OPEN) {
        const command = { action: "soltar_seringa", payload: { syringe_id: "#syringe", position: position } };
        socket.send(JSON.stringify(command));
        console.log("Comando 'soltar_seringa' enviado.", command);
        // OPTIONAL: Optimistic local update
        // Or wait for backend confirmation
        // holding = false;
        // const scene = document.querySelector("a-scene");
        // if(scene) scene.appendChild(syringe); else console.error("Elemento a-scene não encontrado.");
        // syringe.setAttribute("position", `${position.x} ${position.y} ${position.z}`);
    } else {
        console.error("WebSocket não está aberto. Não foi possível enviar 'soltar_seringa'.");
    }
}

function sendInjetarCommand(depth, speed) {
    if (socket.readyState === WebSocket.OPEN) {
        const command = { action: "injetar", payload: { depth: depth, speed: speed } };
        socket.send(JSON.stringify(command));
        console.log("Comando 'injetar' enviado:", command);
        // Local animation for syringe plunger might still be relevant,
        // or it could be driven by fine-grained feedback from SOFA via backend.
        // Example: Simulating plunger animation locally
        /*
        if (syringe && holding) {
            syringe.setAttribute("animation", {
                property: "components.cylinder.height", // Assuming cylinder is main body
                to: 0.25, // Shorter height
                dur: 500,
                dir: "alternate",
                loop: 1
            });
        }
        */
    } else {
        console.error("WebSocket não está aberto. Não foi possível enviar 'injetar'.");
    }
}

// Example test calls (uncomment in browser console or integrate with UI events)
/*
setTimeout(() => {
    console.log("Enviando comandos de teste...");
    sendMoveHandCommand({x: 0.1, y: 1.5, z: -0.7});
}, 3000);

setTimeout(() => {
    sendPegarSeringaCommand();
    // Manually update A-Frame for testing pegar_seringa if not handled by backend confirmation yet
    // holding = true;
    // syringe.setAttribute("position", "0 -0.1 0");
    // if(hand) hand.appendChild(syringe);
}, 5000);

setTimeout(() => {
    sendInjetarCommand(10, 2); // depth 10, speed 2
}, 7000);

setTimeout(() => {
    // Manually update A-Frame for testing soltar_seringa
    // const scene = document.querySelector("a-scene");
    // if(scene) scene.appendChild(syringe);
    sendSoltarSeringaCommand({x: 0.2, y: 1.0, z: -1.0});
}, 9000);
*/

// The original logic for A-Frame manipulation based on simple string commands from the backend
// has been replaced by the new socket.onmessage handler which parses JSON.
// Frontend A-Frame updates should ideally be triggered by these parsed JSON messages
// (e.g., confirmation of an action from the backend, or new state data from SOFA/ESP32).
// For some actions (like moving the hand locally), optimistic updates can still be done
// right after sending the command, as shown in sendMoveHandCommand.
console.log("simulacao.js carregado e pronto.");
