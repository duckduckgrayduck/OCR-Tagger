"""
Simple DocumentCloud Add-On that tags documents
with the OCR engine used on said documents.
"""

import sys
import time
from itertools import batched

from documentcloud.addon import SoftTimeOutAddOn
from documentcloud.exceptions import APIError

BATCH_SIZE = 25


class OCRTagger(SoftTimeOutAddOn):
    """Tags documents with OCR engine"""

    OCR_MAPPING = {
        "tess4": "tesseract",
        "tess4_force": "tesseract",
        "textract": "textract",
        "textract_force": "textract",
        "azuredi": "azure",
        "googlecv": "google",
        "doctr": "doctr",
        "None": "None",
    }

    def tag_documents(self, payload, max_retries=5, retry_delay=60):
        """Bulk-tag a batch of documents, retrying on failure.

        `payload` is a list of {"id": ..., "data": {...}} objects (up to 25).
        """
        retries = 0
        while retries < max_retries:
            try:
                print(f"Tagging batch of {len(payload)} documents...")
                self.client.patch("documents/", json=payload)
                print("Finished tagging batch")
                return
            except APIError as exc:
                print(f"Error tagging batch. {exc}. Retrying...")
                retries += 1
                time.sleep(retry_delay)
        # Retries exhausted
        print(f"Failed to tag batch after {max_retries} attempts.")
        self.set_message(
            "Failed to set the OCR tag for some documents. "
            "Email info@documentcloud.org to debug."
        )
        sys.exit(1)

    def get_ocr_value(self, document):
        """Fetch the OCR engine from the document's JSON text."""
        try:
            json_text = document.json_text
            return json_text["pages"][0]["ocr"]
        except (KeyError, IndexError):
            print(f"No OCR value for {document.id}; tagging as None.")
            return "None"
        except APIError as exc:
            print(f"FETCH FAILED for {document.id}: {exc}")
            return None

    def main(self):
        """
        For each document finds the ocr value from the json text and tags.
        Does this in batches to save on API calls.
        """
        self.client.session.headers.update({"User-Agent": "OCR Tagger Add-On"})
        for chunk in batched(self.get_documents(), BATCH_SIZE):
            payload = []
            for document in chunk:
                ocr_value = self.get_ocr_value(document)
                ocr_value_to_tag = self.OCR_MAPPING.get(ocr_value)
                if ocr_value_to_tag is None:
                    print(f"Skipping {document.id}: unmapped OCR value {ocr_value!r}.")
                    continue
                data = dict(document.data or {})
                data["ocr_engine"] = [ocr_value_to_tag]
                payload.append({"id": document.id, "data": data})
            if payload:
                self.tag_documents(payload)


if __name__ == "__main__":
    OCRTagger().main()
