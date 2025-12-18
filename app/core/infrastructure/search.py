import json
from typing import Dict, List, Literal, Optional

from perplexity import Perplexity as PerplexityClient
from perplexity import PerplexityError

from ...config import EbayConfig, PerplexityConfig
from ...external import barcode_search
from ...external.ebay.taxonomy import (
    EbayCategoriesNotFoundError,
    EbayTaxonomyClient,
    EbayTaxonomyClientError,
)
from ...utils import recognition
from ..domain.entities.question import Answer, Question
from ..infrastructure.adapter import QuestionAdapter, QuestionAdapterError
from ..services.ports import CategoriesNotFoundError, SearchEngineError


class PerplexityAndEbaySearch:
    _SYSTEM_ROLE_CONTENT = "You are a search system"
    _PRODUCT_SEARCH_TEMPLATE = (
        "Provide information about {product} without sourses links"
    )
    _COMMENT_TEXT_TEMPLATE = "Comment: {comment}"

    def __init__(
        self,
        perplexity_config: PerplexityConfig,
        perplexity_client: PerplexityClient,
        ebay_config: EbayConfig,
        taxonomy_client: EbayTaxonomyClient,
    ):
        self._perplexity_client = perplexity_client
        self._perplexity_model = perplexity_config.model
        self._ebay_config = ebay_config
        self._taxonomy_api = taxonomy_client

    def by_product_name(
        self,
        product_name: str,
        comment: str,
        qusetion: Question,
    ) -> Answer:
        text = self._product_search_text(product_name, comment)

        adapter = QuestionAdapter()
        try:
            json_schema = adapter.to_schema(qusetion)
        except QuestionAdapterError as e:
            raise SearchEngineError() from e

        content = self._perplexity_request(text, json_schema, "json_schema")
        try:
            return adapter.to_answer(qusetion, json.loads(content))
        except QuestionAdapterError as e:
            raise SearchEngineError("Failed to parse answer") from e

    def barecodes_on_image(self, img_path: str) -> str:
        return recognition.extract_barcodes(img_path)

    def by_barecode(self, barecode):
        try:
            return barcode_search.search(barecode)
        except barcode_search.BarcodeSearchError as e:
            raise SearchEngineError("Failed to find product") from e

    def categories(self, product_name: str) -> list[str]:
        marketplace_id = self._ebay_config.marketplace_id
        tree_id = self._taxonomy_api.get_default_tree_id(marketplace_id)
        try:
            response = self._taxonomy_api.get_category_suggestions(
                tree_id, product_name
            )
            categories = []
            for suggestion in response.category_suggestions:
                categories.append(suggestion.category.category_name)

            return list(categories)

        except EbayTaxonomyClientError as e:
            raise SearchEngineError("Failed to get category suggestions") from e

        except EbayCategoriesNotFoundError as e:
            raise CategoriesNotFoundError() from e

    @classmethod
    def _product_search_text(cls, product: str, comment: str) -> str:
        template = cls._PRODUCT_SEARCH_TEMPLATE
        mapping = {"product": product}

        if comment:
            mapping.update(comment=comment)
            template = f"{template}\n{cls._COMMENT_TEXT_TEMPLATE}"

        return template.format_map(mapping)

    @classmethod
    def _convert(cls, text: str) -> List[Dict[str, str]]:
        """Convert text into OpenAI chat messages format."""
        messages: List[Dict[str, str]] = []

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
        response_format: Optional[Dict | str] = None,
        response_type: Optional[Literal["json_schema", "regex"]] = None,
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
            response = self._perplexity_client.chat.completions.create(
                model=self._perplexity_model,
                messages=messages,
                response_format=response_format_content,
            )
        except PerplexityError as e:
            raise SearchEngineError() from e

        if not response.choices:
            raise SearchEngineError(f"Invalid API Response: {response}")

        if len(response.choices) > 1:
            raise SearchEngineError("Too many perplexity answers")

        if len(response.choices) == 0:
            raise SearchEngineError("Empty perplexity answer")

        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise SearchEngineError("Invalid content type in perplexity answer")

        return content
