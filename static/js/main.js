
document.addEventListener("DOMContentLoaded", () => {
    const rowInput = document.querySelector('input[name="rows"]');

    if (rowInput) {
        rowInput.addEventListener("change", () => {
            const value = Number(rowInput.value);

            if (!Number.isInteger(value) || value < 20 || value > 1000) {
                rowInput.setCustomValidity(
                    "Please enter a whole number between 20 and 1000."
                );
            } else {
                rowInput.setCustomValidity("");
            }
        });
    }

    const uploadInput = document.querySelector('input[name="file"]');

    if (uploadInput) {
        uploadInput.addEventListener("change", () => {
            const file = uploadInput.files[0];

            if (file && !file.name.toLowerCase().endsWith(".csv")) {
                uploadInput.setCustomValidity("Please select a CSV file.");
            } else {
                uploadInput.setCustomValidity("");
            }
        });
    }
});
