# PDF OCRアプリケーション設計書

## 要件定義書

### 目的
PDFファイルをアップロードし、OCR処理を行い、テキストと画像を含むMarkdown形式で結果を表示するWebアプリケーションを開発する。

### 機能要件
1. PDFファイルのアップロード機能
2. アップロードされたPDFファイルのOCR処理機能
3. OCR結果（Markdown形式）の表示機能
4. PDFと OCR結果を横並びに表示する機能
5. OCR結果内の画像を適切に表示する機能

### 非機能要件
1. ユーザーインターフェースはシンプルで使いやすいこと
2. OCR処理中はローディング表示を行うこと
3. OCR結果は白背景で表示すること
4. 画像を含むMarkdownが正しく表示されること

### 制約条件
1. Streamlitを使用して実装すること
2. MistralのOCR APIを使用すること
3. テストコードは当面不要

## 設計書

### 概略設計
本アプリケーションは、Streamlitを使用したWebアプリケーションとして実装する。ユーザーはPDFファイルをアップロードし、「OCR実行」ボタンをクリックすることでOCR処理を開始する。処理中はローディング表示を行い、処理が完了するとPDFと OCR結果を横並びに表示する。

### 機能設計

#### PDFアップロード機能
- Streamlitの`st.file_uploader`を使用してPDFファイルのアップロード機能を実装
- アップロードされたファイルがPDF形式であることを確認

#### OCR処理機能
- MistralのOCR APIを使用してPDFファイルのOCR処理を実行
- 処理中はStreamlitの`st.spinner`を使用してローディング表示を行う
- OCR結果からMarkdownテキストを生成し、画像を適切に置き換える

#### 結果表示機能
- Streamlitの`st.columns`を使用して画面を2分割し、左側にPDF、右側にOCR結果を表示
- PDFの表示には`st.pdf_viewer`を使用
- OCR結果の表示には`st.markdown`を使用し、白背景で表示するためのCSSを適用

### クラス構成

#### `OCRProcessor`クラス
PDFファイルのOCR処理を行うクラス

- メソッド:
  - `process_pdf(pdf_file)`: PDFファイルをOCR処理し、結果を返す
  - `get_markdown_with_images(ocr_response)`: OCR結果からMarkdownテキストを生成し、画像を適切に置き換える

#### `StreamlitApp`クラス
Streamlitアプリケーションのメインクラス

- メソッド:
  - `run()`: アプリケーションを実行
  - `upload_pdf()`: PDFファイルのアップロード機能を提供
  - `display_results(pdf_file, ocr_result)`: PDFとOCR結果を表示