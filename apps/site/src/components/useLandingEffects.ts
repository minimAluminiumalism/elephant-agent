import {useEffect} from "react";

export function useLandingEffects() {
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const revealNodes = Array.from(
      document.querySelectorAll<HTMLElement>("[data-reveal]")
    );

    let animationFrameId = 0;
    let revealObserver: IntersectionObserver | undefined;
    let resizeCanvas: (() => void) | undefined;

    if (prefersReducedMotion.matches) {
      revealNodes.forEach((node) => node.classList.add("is-visible"));
    } else {
      revealNodes.forEach((node, index) => {
        const style = node instanceof Element ? (node as HTMLElement | SVGElement).style : null;
        if (style && typeof style.setProperty === "function") {
          style.setProperty("--delay", `${Math.min(index * 55, 320)}ms`);
        }
      });

      revealObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) {
              return;
            }
            entry.target.classList.add("is-visible");
            revealObserver?.unobserve(entry.target);
          });
        },
        {
          threshold: 0.18,
          rootMargin: "0px 0px -10% 0px",
        }
      );

      revealNodes.forEach((node) => revealObserver?.observe(node));
    }

    const canvas = document.getElementById("dither-canvas") as HTMLCanvasElement | null;
    const context = canvas?.getContext("2d");

    if (canvas && context && !prefersReducedMotion.matches) {
      let width = 0;
      let height = 0;
      let time = 0;

      const bayerMatrix = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
      ];

      resizeCanvas = () => {
        width = window.innerWidth;
        height = window.innerHeight;
        const scale = Math.min(window.devicePixelRatio || 1, 1.5);
        canvas.width = Math.floor(width * scale);
        canvas.height = Math.floor(height * scale);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        context.setTransform(scale, 0, 0, scale, 0, 0);
      };

      const thresholdAt = (x: number, y: number) => bayerMatrix[y % 4][x % 4] / 16 - 0.5;

      const draw = () => {
        const gridSize = width > 1200 ? 10 : 8;
        const columns = Math.ceil(width / gridSize);
        const rows = Math.ceil(height / gridSize);

        context.clearRect(0, 0, width, height);
        context.fillStyle = "#0d0d0d";
        context.fillRect(0, 0, width, height);

        for (let row = 0; row < rows; row += 1) {
          for (let column = 0; column < columns; column += 1) {
            const waveA = Math.sin(column * 0.05 + time * 0.55);
            const waveB = Math.cos(row * 0.035 + time * 0.22);
            let intensity = (waveA + waveB + 2) / 4;

            const dx = (column - columns / 2) / (columns / 2);
            const dy = (row - rows / 2) / (rows / 2);
            const radial = Math.sqrt(dx * dx + dy * dy);
            intensity *= 0.16 + radial * 0.9;

            if (intensity + thresholdAt(column, row) > 0.68) {
              context.fillStyle = "rgba(242, 237, 231, 0.18)";
              context.fillRect(column * gridSize, row * gridSize, gridSize - 2, gridSize - 2);
            }
          }
        }

        time += 0.015;
        animationFrameId = window.requestAnimationFrame(draw);
      };

      window.addEventListener("resize", resizeCanvas);
      resizeCanvas();
      draw();
    }

    return () => {
      revealObserver?.disconnect();
      if (resizeCanvas) {
        window.removeEventListener("resize", resizeCanvas);
      }
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
    };
  }, []);
}
