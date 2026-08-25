import streamlit as st


def voice_input_button(
    key="voice_input"
):
    """
    Browser speech recognition.

    Returns spoken text through
    Streamlit session state.
    """

    html = f"""
    <div style="
        text-align:center;
        padding:10px;
    ">
        <button
            id="{key}_button"
            style="
                border:none;
                border-radius:50%;
                width:55px;
                height:55px;
                font-size:24px;
                cursor:pointer;
            "
        >
            🎤
        </button>
    </div>

    <script>

    const button =
        document.getElementById(
            "{key}_button"
        );

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {{

        button.innerHTML = "❌";

    }} else {{

        const recognition =
            new SpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.lang = "en-IN";

        button.onclick = () => {{

            recognition.start();

            button.innerHTML = "🎙️";

        }};

        recognition.onresult = event => {{

            const text =
                event.results[0][0].transcript;

            window.parent.postMessage(
                {{
                    type:
                    "streamlit:setComponentValue",

                    value: text
                }},
                "*"
            );

            button.innerHTML = "🎤";

        }};

        recognition.onerror = () => {{

            button.innerHTML = "🎤";

        }};

    }}

    </script>
    """

    result = st.components.v1.html(
        html,
        height=75
    )

    return result
