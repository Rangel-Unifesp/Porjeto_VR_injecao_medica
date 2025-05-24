const hand = document.querySelector("#hand");
      const syringe = document.querySelector("#syringe");
      let holding = false;

      // WebSocket
      const socket = new WebSocket("ws://localhost:8080");

      socket.onmessage = (event) => {
        const command = event.data.toLowerCase();
        console.log("Comando recebido:", command);

        if (command.includes("mover mão")) {
          // Exemplo: "mover mão 0.1 1.2 -1.5"
          const coords = command.match(/-?\d+(\.\d+)?/g);
          if (coords && coords.length === 3) {
            hand.setAttribute("position", coords.join(" "));
          }
        }

        if (command.includes("pegar seringa") && !holding) {
          holding = true;
          syringe.setAttribute("position", "0 -0.1 0");
          hand.appendChild(syringe);
        }

        if (command.includes("soltar seringa") && holding) {
          holding = false;
          document.querySelector("a-scene").appendChild(syringe);
          syringe.setAttribute("position", "0 1.1 -1.8");
        }

        if (command.includes("injetar")) {
          syringe.setAttribute("animation", {
            property: "position",
            to: "0 -0.2 0",
            dur: 200,
            dir: "alternate",
            loop: 2,
          });
        }
      };