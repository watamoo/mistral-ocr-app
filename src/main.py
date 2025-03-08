"""
PDF OCRアプリケーション

PDFファイルをアップロードし、OCR処理を行い、テキストと画像を含むMarkdown形式で結果を表示するWebアプリケーション。
"""

import os
import tempfile
from typing import Dict, List, Optional


import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from dotenv import load_dotenv
from mistralai import DocumentURLChunk
from mistralai.models import OCRResponse
from mistralai import Mistral

# 環境変数の読み込み
load_dotenv()

# Mistral APIキーの取得
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class OCRProcessor:
    """PDFファイルのOCR処理を行うクラス"""

    def __init__(self, api_key: str):
        """
        OCRProcessorクラスの初期化

        Args:
            api_key: Mistral APIキー
        """
        self.client = Mistral(api_key=api_key)

    def process_pdf(self, pdf_file) -> OCRResponse:
        """
        PDFファイルをOCR処理する

        Args:
            pdf_file: アップロードされたPDFファイル

        Returns:
            OCRResponse: OCR処理結果
        """
        # 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # ファイルをアップロード
            uploaded_file = self.client.files.upload(
                file={
                    "file_name": pdf_file.name,
                    "content": open(temp_file_path, "rb").read(),
                },
                purpose="ocr",
            )

            # 署名付きURLを取得
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

            # OCR処理を実行
            pdf_response = self.client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url.url), model="mistral-ocr-latest", include_image_base64=True
            )

            return pdf_response
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @staticmethod
    def replace_images_in_markdown(markdown_str: str, images_dict: Dict[str, str]) -> str:
        """
        Markdown内の画像参照を実際の画像データに置き換える

        Args:
            markdown_str: Markdownテキスト
            images_dict: 画像IDとBase64エンコードされた画像データの辞書

        Returns:
            str: 画像が置き換えられたMarkdownテキスト
        """
        for img_name, base64_str in images_dict.items():
            markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
        return markdown_str

    def get_markdown_with_images(self, ocr_response: OCRResponse) -> str:
        """
        OCR結果からMarkdownテキストを生成し、画像を適切に置き換える

        Args:
            ocr_response: OCR処理結果

        Returns:
            str: 画像が置き換えられたMarkdownテキスト
        """
        markdowns: List[str] = []
        for page in ocr_response.pages:
            image_data = {}
            for img in page.images:
                image_data[img.id] = img.image_base64
            markdowns.append(self.replace_images_in_markdown(page.markdown, image_data))

        return "\n\n".join(markdowns)


class StreamlitApp:
    """Streamlitアプリケーションのメインクラス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        StreamlitAppクラスの初期化

        Args:
            api_key: Mistral APIキー（省略可）
        """
        self.api_key = api_key
        self.ocr_processor = None
        if self.api_key:
            self.ocr_processor = OCRProcessor(api_key=self.api_key)

    def run(self):
        """アプリケーションを実行する"""
        st.set_page_config(
            page_title="PDF OCRアプリ",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("PDF OCRアプリ")
        st.markdown("PDFファイルをアップロードして、OCR処理を行います。")

        # APIキーの設定
        if not self.api_key:
            self.api_key = st.sidebar.text_input("Mistral APIキー", type="password")
            if self.api_key:
                self.ocr_processor = OCRProcessor(api_key=self.api_key)
            else:
                st.sidebar.warning("APIキーを入力してください。")
                st.sidebar.markdown("APIキーは [Mistral Console](https://console.mistral.ai/) で取得できます。")
                return

        # PDFファイルのアップロード
        pdf_file = self.upload_pdf()
        if not pdf_file:
            return

        # OCR処理の実行
        if st.button("OCR実行"):
            with st.spinner("OCR処理中..."):
                try:
                    ocr_result = self.ocr_processor.process_pdf(pdf_file)
                    markdown_text = self.ocr_processor.get_markdown_with_images(ocr_result)
                    self.display_results(pdf_file, markdown_text)
                except Exception as e:
                    st.error(f"OCR処理中にエラーが発生しました: {str(e)}")

    def upload_pdf(self):
        """
        PDFファイルのアップロード機能を提供する

        Returns:
            UploadedFile: アップロードされたPDFファイル（アップロードされていない場合はNone）
        """
        pdf_file = st.file_uploader("PDFファイルをアップロード", type=["pdf"])
        return pdf_file

    def display_results(self, pdf_file, markdown_text: str):
        """
        PDFとOCR結果を表示する

        Args:
            pdf_file: アップロードされたPDFファイル
            markdown_text: OCR結果のMarkdownテキスト
        """
        # 2カラムレイアウトの作成
        col1, col2 = st.columns(2)

        # 左側にPDFを表示
        with col1:
            st.subheader("アップロードされたPDF")

            # PDFをbase64エンコードして表示
            pdf_contents = pdf_file.read()
            pdf_viewer(pdf_contents)

        # 右側にOCR結果を表示
        with col2:
            st.subheader("OCR結果")

            # 白背景で黒文字のMarkdownを表示するためのCSSを適用
            st.markdown(
                """
                <style>
                .ocr-result {
                    background-color: white;
                    color: black;
                    padding: 20px 30px; /* テキストの左右の余白を増やす */
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    overflow: auto; /* 横スクロールも可能に */
                    max-height: 90vh; /* 画面の90%の高さに調整 */
                }
                .ocr-result img {
                    max-width: 50%; /* 画像の幅を縮小 */
                    max-height: 50vh; /* 画像の高さを縮小 */
                    display: block;
                    margin: 10px auto; /* 画像の上下マージンを追加 */
                    object-fit: contain; /* 画像全体が表示されるように */
                }
                .markdown-text {
                    background-color: #f8f9fa;
                    color: #333;
                    padding: 20px;
                    border-radius: 5px;
                    font-family: monospace;
                    white-space: pre-wrap;
                    overflow-x: auto;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # タブを使用してプレビューとマークダウンテキストを切り替える
            preview_tab, markdown_tab = st.tabs(["プレビュー", "マークダウンテキスト"])

            # プレビュータブ
            with preview_tab:
                st.markdown(markdown_text, unsafe_allow_html=True)

            # マークダウンテキストタブ
            with markdown_tab:
                st.code(markdown_text)


def main():
    """アプリケーションのエントリーポイント"""
    app = StreamlitApp(api_key=MISTRAL_API_KEY)
    app.run()


if __name__ == "__main__":
    main()
