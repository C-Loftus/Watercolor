document.addEventListener("DOMContentLoaded", () => {
  const copyIcons = document.querySelectorAll(".copy");

  copyIcons.forEach((icon) => {
    icon.addEventListener("click", (event) => {
      const textToCopy = icon.parentElement.innerText;
      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          const tooltip = document.createElement("div");
          tooltip.classList.add("tooltip");
          tooltip.textContent = "Copied to clipboard";

          // Calculate tooltip position
          const iconRect = icon.getBoundingClientRect();
          tooltip.style.top = iconRect.top + "px";
          tooltip.style.left = iconRect.right + "px";

          document.body.appendChild(tooltip);

          setTimeout(() => {
            tooltip.remove();
          }, 1000); // Remove tooltip after 2 seconds
        })
        .catch((err) => {
          console.error("Could not copy text: ", err);
        });
    });
  });
});
