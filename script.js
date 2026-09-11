const questions = [
    "Tell us about yourself and your technical background.",
    "What is the difference between a process and a thread?",
    "Explain Object-Oriented Programming.",
    "What is a database and why is it used?",
    "What is the difference between HTTP and HTTPS?"
];

let currentQuestion = 0;
let time = 60;

let timerInterval = null;
let mediaRecorder = null;
let audioChunks = [];

const questionElement = document.getElementById("question");
const questionNumberElement = document.getElementById("questionNumber");
const timerElement = document.getElementById("timer");

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const nextBtn = document.getElementById("nextBtn");

const recordingStatus = document.getElementById("recordingStatus");
const audioPlayer = document.getElementById("audioPlayer");


// ---------------- TIMER ----------------

function startTimer() {

    clearInterval(timerInterval);

    time = 60;
    timerElement.textContent = time;

    timerInterval = setInterval(() => {

        time--;

        timerElement.textContent = time;

        if (time <= 0) {

            clearInterval(timerInterval);

            recordingStatus.textContent =
                "Time is over. Please stop your recording.";

        }

    }, 1000);
}


// ---------------- START RECORDING ----------------

startBtn.addEventListener("click", async () => {

    try {

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];

        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {

            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }

        };

        mediaRecorder.onstop = () => {

            const audioBlob = new Blob(
                audioChunks,
                { type: "audio/webm" }
            );

            const audioURL = URL.createObjectURL(audioBlob);

            audioPlayer.src = audioURL;

            recordingStatus.textContent =
                "Recording completed. You can play your answer below.";

            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();

        startBtn.disabled = true;
        stopBtn.disabled = false;

        recordingStatus.textContent =
            "🔴 Recording... Please answer the question.";

        startTimer();

    } catch (error) {

        alert(
            "Microphone permission is required to record your answer."
        );

        console.error(error);
    }

});


// ---------------- STOP RECORDING ----------------

stopBtn.addEventListener("click", () => {

    if (mediaRecorder && mediaRecorder.state !== "inactive") {

        mediaRecorder.stop();

        clearInterval(timerInterval);

        startBtn.disabled = false;
        stopBtn.disabled = true;

    }

});


// ---------------- NEXT QUESTION ----------------

nextBtn.addEventListener("click", () => {

    // Stop recording if it is active
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }

    clearInterval(timerInterval);

    // Check if this was the last question
    if (currentQuestion === questions.length - 1) {

        // Demo evaluation data
        const result = {
            overall: 82,
            technical: 85,
            communication: 80,
            problemSolving: 82
        };

        // Save result in browser
        localStorage.setItem(
            "hireiqResult",
            JSON.stringify(result)
        );

        // Open result page
        window.location.href = "result.html";

        return;
    }

    // Move to next question
    currentQuestion++;

    questionElement.textContent =
        questions[currentQuestion];

    questionNumberElement.textContent =
        currentQuestion + 1;

    time = 60;

    timerElement.textContent = time;

    audioPlayer.removeAttribute("src");

    recordingStatus.textContent =
        'Click "Start Recording" to answer.';

    startBtn.disabled = false;
    stopBtn.disabled = true;
});