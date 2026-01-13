import json
from dataclasses import dataclass
from typing import Literal

from perplexity import Perplexity as PerplexityClient
from perplexity import PerplexityError

from ..domain.entities import IMetadata, Product, ProductStructure
from ..services.ports import SearchEngineError
from ..utils import recognition
from .adapter import ProductAdapter, ProductAdapterError
from .api_clients import barcode


@dataclass
class SearchEngine:
    _SYSTEM_ROLE_CONTENT = "You are a search system"
    _PRODUCT_SEARCH_TEMPLATE = (
        "Provide information about {product} without sourses links"
    )
    _COMMENT_TEXT_TEMPLATE = "Comment: {comment}"

    client: PerplexityClient
    model: str
    barcode_search_token: str

    def by_product_name(
        self,
        metadata_type: type[IMetadata],
        product_name: str,
        comment: str,
        product_structure: ProductStructure,
    ) -> Product:
        prompt = self._product_search_prompt(product_name, comment)

        adapter = ProductAdapter(metadata_type=metadata_type)
        try:
            json_schema = adapter.to_schema(product_structure)
        except ProductAdapterError as e:
            raise SearchEngineError() from e

        content = self._perplexity_request(prompt, json_schema, "json_schema")
        try:
            return adapter.to_product(product_structure, json.loads(content))
        except ProductAdapterError as e:
            raise SearchEngineError("Failed to parse answer") from e

    def barecodes_on_image(self, img_path: str) -> str:
        return recognition.extract_barcodes(img_path)

    def by_barecode(self, barecode):
        try:
            return barcode.search(barecode, self.barcode_search_token)
        except barcode.BarcodeSearchError as e:
            raise SearchEngineError("Failed to find product") from e

    @classmethod
    def _product_search_prompt(cls, product: str, comment: str) -> str:
        template = cls._PRODUCT_SEARCH_TEMPLATE
        mapping = {"product": product}

        if comment:
            mapping.update(comment=comment)
            template = f"{template}\n{cls._COMMENT_TEXT_TEMPLATE}"

        return template.format_map(mapping)

    @classmethod
    def _convert(cls, text: str) -> list[dict[str, str]]:
        """Convert text into OpenAI chat messages format."""
        messages = []

        messages.append({"role": "system", "content": cls._SYSTEM_ROLE_CONTENT})

        if text:
            messages.append(
                {
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                }
            )
        return messages

    def _perplexity_request(
        self,
        text: str,
        response_format: dict | str | None = None,
        response_type: Literal["json_schema", "regex"] | None = None,
    ) -> str:
        messages = self._convert(text)

        response_format_content = None
        if response_format and response_type:
            _name = "regex" if response_type == "regex" else "schema"

            response_format_content = {
                "type": response_type,
                response_type: {_name: response_format},
            }
        elif response_type or response_format:
            raise ValueError(
                "Both response_format and response_type must be provided together"
            )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format=response_format_content,
            )
        except PerplexityError as e:
            raise SearchEngineError() from e

        if response.choices is None or len(response.choices) != 1:
            raise SearchEngineError(f"Invalid perplexity response: {response}")

        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise SearchEngineError("Invalid content type in perplexity answer")

        return content
