document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const qaForm = document.getElementById("qaForm");
    const uploadMessage = document.getElementById("uploadMessage");
    const answerField = document.getElementById("answer");
    let extractedContent = ""; // Store extracted content from the uploaded file

    /**
     * Displays a message with the given text and type (success or error)
     * @param {string} message - The message to display
     * @param {string} type - The type of message ("success" or "error")
     */
    function displayMessage(message, type) {
        uploadMessage.textContent = message;
        uploadMessage.className = `message ${type}`;
        uploadMessage.style.display = "block";
    }

    /**
     * Handles the file upload process
     */
    uploadForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);

        try {
            const response = await fetch("/api/upload/", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                displayMessage(result.message || "File uploaded successfully!", "success");
                extractedContent = result.content; // Store extracted content for querying
                document.getElementById("qaSection").style.display = "block"; // Show Q&A section
            } else {
                displayMessage(result.error || "Error uploading file.", "error");
            }
        } catch (error) {
            displayMessage("Something went wrong. Please try again.", "error");
        }
    });

    /**
     * Handles the question submission process
     */
    qaForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const question = document.getElementById("question").value;
        answerField.textContent = "Fetching answer..."; // Show loading message

        try {
            const response = await fetch("/api/question/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question: question, content: extractedContent }),
            });

            const result = await response.json();

            if (response.ok) {
                answerField.textContent = result.answer || "No answer found.";
            } else {
                answerField.textContent = result.error || "Error processing question.";
            }
        } catch (error) {
            answerField.textContent = "Something went wrong. Please try again.";
        }
    });
});
