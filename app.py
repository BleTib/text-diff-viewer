import streamlit as st
import difflib
import pandas as pd
import os


def format_to_markdown(text):
    return (
        text.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(" ", " &nbsp; ")
        .replace("\n", " &br; ")
    )


def unformat_from_markdown(text):
    return (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
        .replace("&br;", "\n")
    )


def count_chars(word_list):
    plus_minus_count = 0
    for word in word_list:
        word = unformat_from_markdown(word)
        if word.endswith("\n"):
            continue
        elif word.startswith("+"):
            plus_minus_count += len(word[2:])
        elif word.startswith("-"):
            plus_minus_count -= len(word[2:])
    return plus_minus_count


def organize_words(word_list):
    result = []
    current_list = []

    for word in word_list:
        if word.endswith("&br;"):
            if current_list and not current_list[0].endswith("&br;"):
                result.append(current_list)
                current_list = []

            current_list.append(word)

        elif word.startswith("+") or word.startswith("-"):
            if current_list and (
                current_list[0].startswith(" ") or current_list[0].endswith("&br;")
            ):
                result.append(current_list)
                current_list = []

            current_list.append(word)

        elif word.startswith(" "):
            if current_list and (
                not (current_list[0].startswith(" "))
                or current_list[0].endswith("&br;")
            ):
                result.append(current_list)
                current_list = []

            current_list.append(word)

    if current_list:
        result.append(current_list)

    return result


def highlight_differences(original, modified):

    original_words = format_to_markdown(original).split()
    modified_words = format_to_markdown(modified).split()

    diffs = difflib.ndiff(original_words, modified_words)
    diffs = organize_words(diffs)
    highlighted_original = []
    highlighted_modified = []

    for diff in diffs:

        if diff[0].startswith(" "):
            for word in diff:
                highlighted_original.append(word[2:])
                highlighted_modified.append(word[2:])

        else:
            for word in diff:
                if word.startswith("+"):
                    if word[2:] == "&nbsp;":
                        highlighted_modified.append(
                            f'<span style="background-color: #b3ffb3;">{word[2:]}</span>'
                        )
                    else:
                        highlighted_modified.append(
                            f'<span style="color: green;background-color: #b3ffb3;">{word[2:]}</span>'
                        )
                    if word[2:] == "&br;":
                        highlighted_original.append(word[2:])

                elif word.startswith("-"):
                    if word[2:] == "&nbsp;":
                        highlighted_original.append(
                            f'<span style="background-color: #ff9a9a;">{word[2:]}</span>'
                        )
                    else:
                        highlighted_original.append(
                            f'<span style="color: black;background-color: #ff9a9a;">{word[2:]}</span>'
                        )
                    if word[2:] == "&br;":
                        highlighted_modified.append(word[2:])

            charcount = count_chars(diff)
            if charcount > 0:
                highlighted_original.append(
                    f'<span style="background-color: #b3ffb3;">{"".join(["&nbsp;" for _ in range(charcount)])}</span>'
                )
            if charcount < 0:
                highlighted_modified.append(
                    f'<span style="background-color: #ff9a9a;">{"".join(["&nbsp;" for _ in range(-charcount)])}</span>'
                )

    return "".join(highlighted_original), "".join(highlighted_modified)


# --- Streamlit App ---

st.set_page_config(
    page_title="Text Diff Viewer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .monospace-text {
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: keep-all;
        overflow-wrap: break-word;
        max-width: 100%;
        overflow-x: hidden;
    }
    .st-emotion-cache-183lzff p {
        font-family: 'Courier New', Courier, monospace;
    }
    .text-area {
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<center><h1>Text Diff Viewer</h1></center>", unsafe_allow_html=True)
st.markdown(
    "<center><p style='color: gray;'>Compare text side-by-side with word-level highlighting. "
    "Upload your own CSV or use the sample data.</p></center>",
    unsafe_allow_html=True,
)

# --- Data Loading ---

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])

FREE_TEXT_OPTION = "Free text input"
source_options = [FREE_TEXT_OPTION] + csv_files

separator = st.sidebar.text_input("CSV separator", value=";")


@st.cache_data
def load_csv(file, sep):
    return pd.read_csv(file, sep=sep, encoding="utf-8", index_col=0)


# --- Source Selection ---

_, col_source, _ = st.columns([0.3, 0.4, 0.3])
with col_source:
    selected_source = st.selectbox(
        "Data source",
        options=source_options,
        index=0,
    )

use_csv = selected_source != FREE_TEXT_OPTION

if use_csv:
    df = load_csv(os.path.join(DATA_DIR, selected_source), separator)
    column_options = df.columns.tolist()

    # --- Navigation (only for CSV mode) ---

    if "current_index" not in st.session_state:
        st.session_state["current_index"] = 0

    # Clamp index to valid range for current CSV
    if st.session_state["current_index"] >= len(df.index):
        st.session_state["current_index"] = 0

    _, col_prev, col_select, col_next, _ = st.columns([0.35, 0.05, 0.2, 0.05, 0.35])

    with col_prev:
        st.markdown("<div style='height: 26px'></div>", unsafe_allow_html=True)
        if st.button("\u25c0", key="prev_entry", use_container_width=True):
            if st.session_state["current_index"] > 0:
                st.session_state["current_index"] -= 1
                st.rerun()

    with col_select:
        selected_entry = st.selectbox(
            "Entry",
            options=df.index,
            index=st.session_state["current_index"],
            key="entry_selector",
        )
        current_index = list(df.index).index(selected_entry)
        st.session_state["current_index"] = current_index

    with col_next:
        st.markdown("<div style='height: 26px'></div>", unsafe_allow_html=True)
        if st.button("\u25b6", key="next_entry", use_container_width=True):
            if st.session_state["current_index"] < len(df.index) - 1:
                st.session_state["current_index"] += 1
                st.rerun()

    selected_entry = df.index[st.session_state["current_index"]]

# --- Text Areas ---

cols = st.columns(2)

if use_csv:
    with cols[0]:
        col1_selected = st.selectbox(
            "Left column",
            options=column_options,
            index=0,
        )
        initial_text1 = str(df.loc[selected_entry, col1_selected]) if selected_entry is not None else ""
        text1 = st.text_area("Original", value=initial_text1, height=250, key="text1", label_visibility="collapsed")

    with cols[1]:
        col2_selected = st.selectbox(
            "Right column",
            options=column_options,
            index=min(1, len(column_options) - 1),
        )
        initial_text2 = str(df.loc[selected_entry, col2_selected]) if selected_entry is not None else ""
        text2 = st.text_area("Modified", value=initial_text2, height=250, key="text2", label_visibility="collapsed")
else:
    with cols[0]:
        text1 = st.text_area("Original", value="", height=250, key="text1")
    with cols[1]:
        text2 = st.text_area("Modified", value="", height=250, key="text2")

# --- Diff Output ---

st.button("Find difference", use_container_width=True, key="find_diff")

if st.session_state.get("find_diff") or use_csv:
    highlighted_original, highlighted_modified = highlight_differences(text1, text2)

    result_cols = st.columns(2)
    with result_cols[0]:
        st.markdown(
            '<div class="monospace-text">'
            + highlighted_original.replace("&br;", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )
    with result_cols[1]:
        st.markdown(
            '<div class="monospace-text">'
            + highlighted_modified.replace("&br;", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )
