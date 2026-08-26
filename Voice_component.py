import json
import streamlit.components.v1 as components


def voice_assistant_component(
    key="tourist_voice_assistant",
    button_text="🎤 Start Speaking",
    language="ta-IN",
    auto_restart=False,
):
    """
    Browser-side voice component.

    Returns the latest recognized text to Streamlit.
    Requires a browser with Web Speech API support.
    """

    config = {
        "key": key,
        "button_text": button_text,
        "language": language,
        "auto_restart": auto_restart,
    }

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
        font-family: Arial, sans-serif;
    }}

    body {{
        margin: 0;
        background: transparent;
        color: #f8fafc;
    }}

    .voice-box {{
        width: 100%;
        padding: 18px;
        border: 1px solid #2c4264;
        border-radius: 18px;
        background: #0f1b2d;
        text-align: center;
    }}

    .orb {{
        width: 58px;
        height: 58px;
        margin: 0 auto 12px;
        border-radius: 50%;
        background: #3b82f6;
        box-shadow: 0 0 20px #3b82f6;
        transition: transform .2s ease;
    }}

    .orb.listening {{
        animation: pulse 1s infinite ease-in-out;
    }}

    @keyframes pulse {{
        0%, 100% {{
            transform: scale(.88);
            opacity: .65;
        }}
        50% {{
            transform: scale(1.18);
            opacity: 1;
        }}
    }}

    button {{
        width: 100%;
        min-height: 48px;
        border-radius: 14px;
        border: 1px solid #3b82f6;
        background: #17243a;
        color: white;
        font-size: 16px;
        font-weight: 700;
        cursor: pointer;
    }}

    button:hover {{
        border-color: #60a5fa;
    }}

    .status {{
        margin-top: 12px;
        color: #cbd5e1;
        font-size: 14px;
    }}

    .transcript {{
        margin-top: 12px;
        min-height: 42px;
        padding: 10px;
        border-radius: 12px;
        background: #111b2e;
        color: #ffffff;
        text-align: left;
        white-space: pre-wrap;
        word-break: break-word;
    }}
</style>
</head>

<body>
<div class="voice-box">
    <div id="orb" class="orb"></div>

    <button id="micBtn">{config["button_text"]}</button>

    <div id="status" class="status">
        Tap the microphone and start speaking
    </div>

    <div id="transcript" class="transcript">
        Your speech will appear here...
    </div>
</div>

<script>
(() => {{
    const CONFIG = {json.dumps(config)};

    const micBtn = document.getElementById("micBtn");
    const status = document.getElementById("status");
    const transcript = document.getElementById("transcript");
    const orb = document.getElementById("orb");

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {{
        status.textContent =
            "Voice recognition is not supported in this browser.";
        micBtn.disabled = true;
        return;
    }}

    const recognition = new SpeechRecognition();

    recognition.lang = CONFIG.language;
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    let listening = false;
    let finalText = "";
    let submitted = false;

    function setListeningUI(active) {{
        listening = active;
        orb.classList.toggle("listening", active);

        micBtn.textContent = active
            ? "⏹ Stop & Send"
            : CONFIG.button_text;

        status.textContent = active
            ? "Listening... speak naturally"
            : "Tap the microphone and start speaking";
    }}

    function sendToStreamlit(text) {{
        if (!text || !text.trim() || submitted) return;

        submitted = true;

        status.textContent = "Sending your message to Tourist AI...";

        const payload = {{
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: {{
                text: text.trim(),
                timestamp: Date.now()
            }}
        }};

        window.parent.postMessage(payload, "*");

        setTimeout(() => {{
            submitted = false;
        }}, 1500);
    }}

    recognition.onstart = () => {{
        finalText = "";
        transcript.textContent = "";
        setListeningUI(true);
    }};

    recognition.onresult = (event) => {{
        let interim = "";

        for (
            let i = event.resultIndex;
            i < event.results.length;
            i++
        ) {{
            const resultText =
                event.results[i][0].transcript;

            if (event.results[i].isFinal) {{
                finalText += resultText + " ";
            }} else {{
                interim += resultText;
            }}
        }}

        transcript.textContent =
            (finalText + interim).trim() ||
            "Listening...";
    }};

    recognition.onerror = (event) => {{
        if (event.error === "not-allowed") {{
            status.textContent =
                "Microphone permission was denied.";
        }} else if (event.error !== "aborted") {{
            status.textContent =
                "Voice error: " + event.error;
        }}
    }};

    recognition.onend = () => {{
        const text = finalText.trim();

        if (listening) {{
            setListeningUI(false);
        }}

        if (text) {{
            sendToStreamlit(text);
        }}
    }};

    micBtn.addEventListener("click", () => {{
        if (!listening) {{
            submitted = false;
            finalText = "";

            try {{
                recognition.start();
            }} catch (e) {{
                recognition.stop();
                setTimeout(() => recognition.start(), 250);
            }}
        }} else {{
            status.textContent = "Processing...";
            recognition.stop();
        }}
    }});

    window.addEventListener("message", (event) => {{
        const data = event.data;

        if (
            data &&
            data.type === "tourist-ai:speak"
        ) {{
            window.speechSynthesis.cancel();

            const utterance =
                new SpeechSynthesisUtterance(
                    data.text || ""
                );

            utterance.lang =
                data.language || "ta-IN";

            utterance.rate =
                data.rate || 1;

            utterance.pitch =
                data.pitch || 1;

            window.speechSynthesis.speak(
                utterance
            );

            utterance.onend = () => {{
                if (CONFIG.auto_restart) {{
                    setTimeout(() => {{
                        try {{
                            recognition.start();
                        }} catch (e) {{}}
                    }}, 500);
                }}
            }};
        }}
    }});

    window.parent.postMessage(
        {{
            isStreamlitMessage: true,
            type: "streamlit:componentReady",
            apiVersion: 1
        }},
        "*"
    );

    window.parent.postMessage(
        {{
            isStreamlitMessage: true,
            type: "streamlit:setFrameHeight",
            height: 250
        }},
        "*"
    );
}})();
</script>
</body>
</html>
"""

    return components.html(
        html,
        height=250,
        key=key,
    )
