document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const messageDiv = document.getElementById("uploadMessage");
    const questionForm = document.getElementById("qaForm");
    const answerDiv = document.getElementById("answer");
    let extractedContent = ""; // Variable to store the extracted content from the uploaded file

    // Handle file upload
    uploadForm.addEventListener("submit", async function (e) {
        e.preventDefault(); // Prevent default form submission

        const formData = new FormData(uploadForm);

        try {
            const response = await fetch("/api/upload/", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                // Show success message and store extracted content
                messageDiv.textContent = result.message || "File uploaded successfully!";
                messageDiv.className = "message success";
                extractedContent = result.content; // Save the extracted content
                document.getElementById("qaSection").style.display = "block"; // Show Q&A section
            } else {
                // Show error message
                messageDiv.textContent = result.error || "Error uploading file.";
                messageDiv.className = "message error";
            }
        } catch (error) {
            // Handle network or server errors
            messageDiv.textContent = "Something went wrong. Please try again.";
            messageDiv.className = "message error";
        }

        messageDiv.style.display = "block";
    });

    // Handle Q&A submission
    questionForm.addEventListener("submit", async function (e) {
        e.preventDefault(); // Prevent default form submission

        const question = document.getElementById("question").value;

        try {
            const response = await fetch("/api/question/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    question: question,
                    content: extractedContent, // Include the extracted content
                }),
            });

            const result = await response.json();

            if (response.ok) {
                // Display the answer
                answerDiv.textContent = result.answer || "No answer found.";
            } else {
                // Show error message
                answerDiv.textContent = result.error || "Error processing question.";
            }
        } catch (error) {
            // Handle network or server errors
            answerDiv.textContent = "Something went wrong. Please try again.";
        }

        answerDiv.style.display = "block";
    });
});
