import streamlit as st
import textwrap

from src.chat.chat_service import ask_general_ai


def speak_response(text, voice_name):
    """Browser-based text-to-speech."""

    safe_text = (
        str(text)
        .replace("`", "'")
        .replace("\n", " ")
    )

    if voice_name == "JARVIS":
        rate = 0.92
        pitch = 0.85
    else:
        rate = 1.05
        pitch = 1.08

    html = f"""
    <script>
    const text = {safe_text!r};

    const utterance = new SpeechSynthesisUtterance(text);

    const voices = window.speechSynthesis.getVoices();

    let selectedVoice = null;

    if ("{voice_name}" === "JARVIS") {{

        selectedVoice = voices.find(v =>
            /male|david|mark|daniel|alex/i.test(v.name)
        );

    }} else {{

        selectedVoice = voices.find(v =>
            /female|samantha|zira|karen|zira/i.test(v.name)
        );
    }}

    if (!selectedVoice) {{

        selectedVoice = voices.find(v =>
            /en-IN|ta-IN|en-US|en-GB/i.test(v.lang)
        );
    }}

    if (selectedVoice) {{
        utterance.voice = selectedVoice;
    }}

    utterance.rate = {rate};
    utterance.pitch = {pitch};
    utterance.volume = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    </script>
    """

    st.components.v1.html(
        html,
        height=0
    )


def show_chat_page():
    """Display the general AI chat page."""

    if "general_chat_history" not in st.session_state:
        st.session_state.general_chat_history = []

    if "auto_speak" not in st.session_state:
        st.session_state.auto_speak = True

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        textwrap.dedent(
            """
            <div style="
                text-align:center;
                padding:20px 10px;
            ">
                <h1 style="margin-bottom:5px;">
                    💬 AI Chat
                </h1>

                <p style="color:#9ca3af;">
                    Your General AI Assistant
                </p>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        chat_voice = st.selectbox(
            "🤖 AI Personality",
            ["🦾 JARVIS", "🕷️ EDY"],
            key="general_ai_voice"
        )

    with col2:

        auto_speak = st.toggle(
            "🔊 Auto Voice Reply",
            value=st.session_state.auto_speak
        )

        st.session_state.auto_speak = auto_speak

    if chat_voice == "🦾 JARVIS":
        voice_name = "JARVIS"
        description = "Calm • Intelligent • Professional"
    else:
        voice_name = "EDY"
        description = "Friendly • Energetic • Casual"

    st.caption(
        f"Currently talking with **{voice_name}** — {description}"
    )

    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):
        st.session_state.general_chat_history = []
        st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    if not st.session_state.general_chat_history:

        st.info(
            "👋 Hi! Ask me anything in Tamil, English "
            "or Tanglish. I'm not limited to travel!"
        )

    for index, message in enumerate(
        st.session_state.general_chat_history
    ):

        role = message.get("role")

        if role == "user":

            with st.chat_message("user"):

                st.markdown(
                    message.get("content", "")
                )

        else:

            with st.chat_message("assistant"):

                st.markdown(
                    message.get("content", "")
                )

                if st.button(
                    "🔊 Speak",
                    key=f"general_speak_{index}"
                ):
                    speak_response(
                        message.get("content", ""),
                        message.get(
                            "voice",
                            voice_name
                        )
                    )

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    user_message = st.chat_input(
        "Message AI..."
    )

    if user_message:

        # Show user message
        with st.chat_message("user"):

            st.markdown(user_message)

        st.session_state.general_chat_history.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        # Convert history format
        ai_history = []

        messages = (
            st.session_state.general_chat_history[:-1]
        )

        current_user = None

        for item in messages:

            if item["role"] == "user":

                current_user = item["content"]

            elif (
                item["role"] == "assistant"
                and current_user
            ):

                ai_history.append(
                    {
                        "user": current_user,
                        "assistant": item["content"]
                    }
                )

                current_user = None

        # Generate answer
        with st.chat_message("assistant"):

            with st.spinner(
                f"{voice_name} is thinking..."
            ):

                try:

                    answer = ask_general_ai(
                        user_message=user_message,
                        voice=voice_name,
                        chat_history=ai_history
                    )

                    st.markdown(answer)

                    if st.session_state.auto_speak:

                        speak_response(
                            answer,
                            voice_name
                        )

                    st.session_state.general_chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "voice": voice_name
                        }
                    )

                except Exception as error:

                    error_message = (
                        f"❌ AI Error: {error}"
                    )

                    st.error(error_message)

                    st.session_state.general_chat_history.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                            "voice": voice_name
                        }
                    )
