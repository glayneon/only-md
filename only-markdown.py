import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import nest_asyncio
from llama_parse import LlamaParse
from firecrawl import FirecrawlApp

# To do


# Load API Key for firecrawl and llama-parse
def load_api_key():
    load_dotenv(find_dotenv(), override=True)


def file2markdown(org_file, language="en"):
    load_api_key()
    nest_asyncio.apply()
    with st.spinner("Converting is in progress. Please Wait ..."):
        document = LlamaParse(result_type="markdown", language="en").load_data(
            org_file
        )
    st.success("Done!!")

    return document


def url2markdown(url, type="scrape", limits=10):
    load_api_key()

    app = FirecrawlApp()
    with st.spinner(f"Scraping {url} and Converting into Markdown ..."):
        if type.lower() == "scrape":
            document = app.scrape_url(
                url=url,
                params={
                    "formats": [
                        "markdown",
                    ]
                },
            )
            markdowned_docs = document["markdown"]

        elif type.lower() == "crawl":
            document = app.crawl_url(
                url=url,
                params={
                    "limit": limits,
                    "scrapeOptions": {
                        "formats": [
                            "markdown",
                        ]
                    },
                },
                poll_interval=5,
            )
            if document["status"] == "completed":
                markdowned_docs = "/n/n".join(
                    [x["markdown"] for x in document["data"]]
                )

        elif type.lower() == "map":
            document = app.map_url(url=target_url)
            markdowned_docs = "\n".join([i for i in document["links"]])

    return markdowned_docs


# main
if __name__ == "__main__":
    # webapp layout
    st.set_page_config(
        "Only-MarkDown", layout="centered", initial_sidebar_state="expanded"
    )
    # Open YAML config file
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=SafeLoader)

    # Create authenticator object
    with st.sidebar:
        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
            auth_hash=False,
        )

        # Render the login widget
        authenticator.login("sidebar", 5, 5, captcha=False, key="login1")

    # Authenticate users
    if st.session_state["authentication_status"] is False:
        st.error("Username/Password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please Enter your Username and Password")
    elif st.session_state["authentication_status"]:
        with st.sidebar:
            authenticator.logout()
            st.write(f"# Welcome *{st.session_state['name']}*")
            "Only-Markdown 은 업로드한 pdf, ppt, doc 등의 파일을 Markdown 으로 변환합니다."
            "또한 URL 에 web 주소를 입력하면, 입력한 주소의 페이지를 역시 Markdown 으로 변환 합니다."
            "[View the source code](https://glayneon.github.com/only-markdown)"

        # main widget
        st.title("Only-MarkDown :jack_o_lantern:")

        # Converting files into Markdown
        with st.container(border=True):
            uploaded_file = st.file_uploader(
                "Choose a PDF, DOC, PPT file to Convert Markdowned file",
                type=["pdf", "ppt", "pptx", "doc", "docx"],
                help="Limit 100MB per file",
            )

            save_button = st.button("Convert to Markdown", key="save1")

            if save_button and uploaded_file is not None:
                tmp_file = Path("./data") / uploaded_file.name
                tmp_file.write_bytes(uploaded_file.getbuffer())
                if content := file2markdown(tmp_file):
                    st.success(
                        f"Converting {uploaded_file.name} into {uploaded_file.name + '.md'} ..."
                    )
                    # delete tmp_file
                    tmp_file.unlink()

                    new_name = f"{uploaded_file.name.split('.')[0]}.md"
                    with open(new_name, "a") as f:
                        for i in range(0, len(content)):
                            f.write(content[i].text)
                    st.download_button(
                        "Download MD file",
                        data=Path(new_name).read_text(encoding="utf-8"),
                        file_name=new_name,
                        key="downloaded",
                    )
                    if Path(new_name).exists:
                        Path(new_name).unlink()
                else:
                    st.warning("Please Select the file")

        # Converting url pages into Markdown
        with st.form("form1"):
            target_url = st.text_input("Target URL", max_chars=200, key="url1")
            mode = st.radio(
                "Choose what action you want.",
                ["Scrape", "Crawl", "Map"],
                horizontal=True,
            )
            st.form_submit_button("Submit")
            if st.form_submit_button and target_url and mode:
                document = url2markdown(target_url, type=mode)
                if document and st.session_state.url1:
                    with st.expander("Check out - Converted Markdown"):
                        st.text_area("Markdown", value=document, height=500)
                    with st.expander("View of the Markdown"):
                        st.markdown(document)
