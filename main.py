"""
Simple DocumentCloud Add-On that tags documents
with the OCR engine used on said documents. 
"""
import requests
from documentcloud.addon import AddOn


class OCRTagger(AddOn):
    """Tags documents with OCR engine"""

    def main(self):
        """ For each document finds the ocr value from the json text and tags """
        for document in self.get_documents():
            try:
                json_text_url = f"{document.asset_url}documents/{document.id}/{document.slug}.txt.json"
                response = requests.get(json_text_url, timeout=10)
                json_data = response.json()
                ocr_value = json_data["pages"][0]["ocr"]
            except:
                ocr_value = "None"
            ocr_mapping = {
                "tess4": "tesseract",
                "tess4_force": "tesseract",
                "textract": "textract",
                "textract_force": "textract",
                "azuredi": "azure",
                "googlecv": "google",
                "doctr": "doctr",
                "None": "None",
            }
            document.data["ocr_engine"] = ocr_mapping.get(ocr_value)
            document.put()


if __name__ == "__main__":
    OCRTagger().main()
